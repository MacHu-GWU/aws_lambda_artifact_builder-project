# -*- coding: utf-8 -*-

import hashlib
import dataclasses
import subprocess
from pathlib import Path
from functools import cached_property

from func_args.api import BaseFrozenModel, REQ

from ..typehint import T_PRINTER
from ..constants import LayerBuildToolEnum

from .foundation import Credentials, LayerPathLayout


@dataclasses.dataclass(frozen=True)
class BasedLambdaLayerLocalBuilder(BaseFrozenModel):
    """
    Base command class for local Lambda layer builds.

    This abstract base implements the common workflow for building Lambda layers
    directly on the host machine using local dependency management tools (pip, poetry, uv).
    Subclasses implement tool-specific installation logic while sharing common
    infrastructure like directory setup and path management.

    **Command Pattern**: Each builder encapsulates a complete build workflow as a series
    of discrete steps that can be executed, tested, and extended independently.

    **Usage**: Not used directly - subclassed by tool-specific builders like
    PipBasedLambdaLayerLocalBuilder, PoetryBasedLambdaLayerLocalBuilder, etc.

    .. seealso::

        :ref:`lambda-layer-local-builder`
    """

    path_pyproject_toml: Path = dataclasses.field(default=REQ)
    credentials: Credentials | None = dataclasses.field(default=None)
    skip_prompt: bool = dataclasses.field(default=False)
    printer: T_PRINTER = dataclasses.field(default=print)

    _tool: LayerBuildToolEnum = dataclasses.field(default=REQ)

    @cached_property
    def path_layout(self) -> LayerPathLayout:
        """
        :class:`LayerPathLayout` object for managing build paths.
        """
        return LayerPathLayout(
            path_pyproject_toml=self.path_pyproject_toml,
        )

    def run(self):
        """
        Execute the complete build workflow in defined steps.
        """
        self.step_1_preflight_check()
        self.step_2_prepare_environment()
        self.step_3_execute_build()
        self.step_4_finalize_artifacts()

    def step_1_preflight_check(self):
        """
        Perform read-only validation of build environment and project configuration.
        """
        self.step_1_1_print_info()

    def step_2_prepare_environment(self):
        """
        Set up necessary prerequisites for the build process.
        """
        self.step_2_1_setup_build_dir()

    def step_3_execute_build(self):
        """
        Execute dependency manager-specific installation commands (pip/poetry/uv).
        """
        raise NotImplementedError

    def step_4_finalize_artifacts(self):
        """
        Transform build output into Lambda layer's required python/ directory structure.
        """

    # --- step_1_preflight_check sub-steps
    def step_1_1_print_info(self):
        """
        Display build configuration and paths.

        Provides visibility into the build process by showing which tool
        is being used and where artifacts will be created.
        """
        self.printer(f"--- Build Lambda layer artifacts using {self._tool} ...")
        p = self.path_pyproject_toml
        self.printer(f"path_pyproject_toml = {p}")
        p = self.path_layout.dir_build_lambda_layer
        self.printer(f"dir_build_lambda_layer = {p}")

    # --- step_2_prepare_environment sub-steps
    def step_2_1_setup_build_dir(self):
        """
        Prepare the build environment by cleaning and creating directories.

        Ensures a clean slate for layer creation by removing previous artifacts
        and establishing the required directory structure.

        :param skip_prompt: If True, automatically remove existing build directory
        """
        dir = self.path_layout.dir_build_lambda_layer
        self.printer(f"--- Clean existing build directory: {dir}")
        self.path_layout.clean(skip_prompt=self.skip_prompt)
        self.path_layout.mkdirs()

    # --- step_3_execute_build sub-steps
    # --- step_4_finalize_artifacts sub-steps


@dataclasses.dataclass(frozen=True)
class BasedLambdaLayerContainerBuilder(BaseFrozenModel):
    """
    Base command class for containerized Lambda layer builds.

    This abstract base provides Docker container orchestration for building Lambda layers
    using AWS SAM build images that match the Lambda runtime environment. It handles
    container configuration, volume mounting, and script execution while delegating
    tool-specific build logic to copied scripts that run inside the container.

    **Architecture Benefits**:
    - **Runtime Compatibility**: Uses official AWS Lambda container images
    - **Isolation**: Builds don't affect the host environment
    - **Reproducibility**: Consistent results across different development machines
    - **Platform Support**: Handles both x86_64 and ARM64 architectures

    **Command Pattern**: Encapsulates the complete containerized build workflow,
    making it easy to test, extend, and maintain tool-specific build strategies.

    **Usage**: Subclassed by tool-specific container builders that provide
    the appropriate build scripts for execution inside the container.
    """

    path_pyproject_toml: Path = dataclasses.field(default=REQ)
    py_ver_major: int = dataclasses.field(default=REQ)
    py_ver_minor: int = dataclasses.field(default=REQ)
    is_arm: bool = dataclasses.field(default=REQ)
    path_script: Path = dataclasses.field(default=REQ)
    credentials: Credentials | None = dataclasses.field(default=None)
    printer: T_PRINTER = dataclasses.field(default=print)

    @cached_property
    def path_layout(self) -> LayerPathLayout:
        """
        :class:`LayerPathLayout` object for managing build paths.
        """
        return LayerPathLayout(
            path_pyproject_toml=self.path_pyproject_toml,
        )

    @property
    def image_tag(self) -> str:
        """
        Docker image tag based on target architecture.

        :return: Architecture-specific tag for AWS SAM build images
        """
        if self.is_arm:
            return "latest-arm64"
        else:
            return "latest-x86_64"

    @property
    def image_uri(self) -> str:
        """
        Full Docker image URI for AWS SAM build container.

        Uses official AWS SAM images that match the Lambda runtime environment
        to ensure compatibility between local builds and deployed functions.

        :return: Complete Docker image URI from AWS public ECR
        """
        return (
            f"public.ecr.aws/sam"
            f"/build-python{self.py_ver_major}.{self.py_ver_minor}"
            f":{self.image_tag}"
        )

    @property
    def platform(self) -> str:
        """
        Docker platform specification for target architecture.

        :return: Platform string for docker run --platform argument
        """
        if self.is_arm:
            return "linux/arm64"
        else:
            return "linux/amd64"

    @property
    def container_name(self) -> str:
        """
        Unique container name for the build process.

        Includes Python version and architecture to avoid conflicts when
        running multiple builds concurrently.

        :return: Descriptive container name for docker run --name argument
        """
        suffix = "arm64" if self.is_arm else "amd64"
        return (
            f"lambda_layer_builder"
            f"-python{self.py_ver_major}{self.py_ver_minor}"
            f"-{suffix}"
        )

    @property
    def docker_run_args(self) -> list[str]:
        """
        Complete Docker run command arguments.

        Constructs the full command for executing the build script inside
        a Docker container with proper volume mounting and platform specification.

        :return: List of command arguments for subprocess execution
        """
        return [
            "docker",
            "run",
            "--rm",  # Auto-remove container when done
            "--name",
            self.container_name,
            "--platform",
            self.platform,
            "--mount",
            f"type=bind,source={self.path_layout.dir_project_root},target=/var/task",
            self.image_uri,
            "python",
            "-u",  # Unbuffered output for real-time logging
            self.path_layout.path_build_lambda_layer_in_container_script_in_container,
        ]

    def run(self):
        """
        Execute the complete containerized build workflow in defined steps.
        """
        self.step_1_preflight_check()
        self.step_2_prepare_environment()
        self.step_3_execute_build()
        self.step_4_finalize_artifacts()

    def step_1_preflight_check(self):
        """
        Validate Docker environment and container build prerequisites.
        """

    def step_2_prepare_environment(self):
        """
        Set up container build prerequisites including scripts and credentials.
        """
        self.step_2_1_copy_build_script()
        self.step_2_2_setup_private_repository_credential()

    def step_3_execute_build(self):
        """
        Run Docker container with AWS SAM build image for dependency installation.
        """
        self.step_3_1_docker_run()

    def step_4_finalize_artifacts(self):
        """
        Clean up temporary files and validate container build results.
        """

    # --- step_1_preflight_check sub-steps
    # --- step_2_prepare_environment sub-steps
    def step_2_1_copy_build_script(self):
        """
        Copy the tool-specific container build script to the project directory.

        Subclasses must implement this method to provide the appropriate
        build script that will be executed inside the Docker container.
        """
        self.path_layout.copy_build_script(
            p_src=self.path_script,
            printer=self.printer,
        )

    def step_2_2_setup_private_repository_credential(self):
        """
        Configure private repository authentication (optional).

        Subclasses can override this method to set up credentials for
        accessing private PyPI servers or corporate package repositories.
        """
        if isinstance(self.credentials, Credentials) is False:
            return
        p = self.path_layout.path_private_repository_credentials_in_local
        self.printer(f"Dump private repository credentials to {p}")
        self.credentials.dump(path=p)

    # --- step_3_execute_build sub-steps
    def step_3_1_docker_run(self):
        """
        Execute the Docker container build process.

        Runs the configured Docker command to build the Lambda layer
        inside the container environment.
        """
        subprocess.run(self.docker_run_args)

    # --- step_4_finalize_artifacts sub-steps
