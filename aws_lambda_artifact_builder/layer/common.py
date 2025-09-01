# -*- coding: utf-8 -*-

"""
Common infrastructure for Lambda layer builders using the Command Pattern.

This module provides the foundational classes and utilities that support multiple
build strategies (pip, poetry, uv) through a consistent command pattern architecture.
The design separates public API functions from internal command classes to balance
ease of use with code maintainability.

Architecture Overview:

- **Public Functions**: Simple API for end users
    (e.g., build_layer_artifacts_using_pip_in_local, build_layer_artifacts_using_pip_in_container)
- **Command Classes**: Internal implementation for better code organization and testability
- **Local Builders**: Direct dependency installation on the host machine
- **Container Builders**: Dockerized builds for AWS Lambda runtime compatibility
"""

import typing as T
import json
import shutil
import subprocess
import dataclasses
from pathlib import Path
from functools import cached_property

from func_args.api import BaseFrozenModel, REQ

from ..typehint import T_PRINTER
from ..constants import ZFILL
from ..imports import S3Path
from ..utils import clean_build_directory


@dataclasses.dataclass(frozen=True)
class Credentials:
    """
    Private repository credentials for accessing authenticated package indexes.

    Used to configure pip, poetry, and uv to authenticate with private PyPI servers
    or corporate package repositories during layer builds.
    """

    index_name: str = dataclasses.field()
    index_url: str = dataclasses.field()
    username: str = dataclasses.field()
    password: str = dataclasses.field()

    @property
    def normalized_index_url(self) -> str:
        index_url = self.index_url
        if index_url.startswith("https://"):
            index_url = index_url[len("https://") :]
        if index_url.endswith("/"):
            index_url = index_url[:-1]
        if index_url.endswith("/simple"):
            index_url = index_url[: -len("/simple")]
        return index_url

    @property
    def pip_extra_index_url(self) -> str:
        """
        Generate pip-compatible URL with embedded authentication.

        :return: URL in format https://username:password@hostname/simple/
        """
        return f"https://{self.username}:{self.password}@{self.normalized_index_url}/simple/"

    def dump(self, path: Path):
        """
        Save credentials to a JSON file.

        :param path: Path to the output JSON file
        """
        data = dataclasses.asdict(self)
        path.write_text(json.dumps(data, indent=4), encoding="utf-8")

    @classmethod
    def load(cls, path: Path):
        return cls(**json.loads(path.read_text(encoding="utf-8")))


@dataclasses.dataclass(frozen=True)
class LayerPathLayout(BaseFrozenModel):
    """
    Local directory layout manager for Lambda layer build artifacts.

    Assuming your Git repository is located at ``${dir_project_root}/``,
    we use ``${dir_project_root}`` to represent this path. The Lambda layer-related paths are as follows:

    - ``${dir_project_root}``
        :meth:`dir_project_root`, Git repository root directory.
    - ``${dir_project_root}/pyproject.toml``
        :attr:`path_pyproject_toml`, pyproject.toml file path.
    - ``${dir_project_root}/build/lambda/layer``
        :meth:`dir_build_lambda_layer`, temporary directory for building Lambda layer,
        cleared before each build.
    - ``${dir_project_root}/build/lambda/layer/layer.zip``
        :meth:`path_build_lambda_layer_zip`, final Lambda layer zip file path for deployment.
    - ``${dir_project_root}/build/lambda/layer/repo``
        :meth:`dir_repo`, to avoid affecting original files in the repository, we create a temporary
        directory here with a structure similar to dir_project_root, copying important files like pyproject.toml.
        If temporary virtual environments need to be built, they will also be created here.
    - ``${dir_project_root}/build/lambda/layer/artifacts``
        :meth:`dir_artifacts`, directory for storing all files to be packaged into layer.zip
    - ``${dir_project_root}/build/lambda/layer/artifacts/python``
        :meth:`dir_python`, AWS Lambda required ``python`` subdirectory.
    """

    path_pyproject_toml: Path = dataclasses.field()

    @property
    def dir_project_root(self) -> Path:
        """
        Project root directory, usually the Git repository root.
        """
        return self.path_pyproject_toml.parent

    def get_path_in_container(self, path_in_local: Path) -> str:
        """
        Convert local filesystem path to corresponding Docker container path.

        Docker containers mount the project root to /var/task, so this method
        translates local paths to their container equivalents for script execution.

        :param path_in_local: Local filesystem path relative to project root
        :return: Corresponding path inside Docker container
        """
        relpath = path_in_local.relative_to(self.dir_project_root)
        parts = ["var", "task"]
        parts.extend(relpath.parts)
        path = "/" + "/".join(parts)
        return path

    @property
    def dir_build_lambda_layer(self) -> Path:
        """
        The build directory for Lambda layer build.
        """
        return self.dir_project_root / "build" / "lambda" / "layer"

    @property
    def path_build_lambda_layer_zip(self) -> Path:
        """
        The output zip file path for the built Lambda layer.
        """
        return self.dir_build_lambda_layer / "layer.zip"

    @property
    def dir_repo(self) -> Path:
        """
        A temporary copy of the project repository for building the layer.
        """
        return self.dir_build_lambda_layer / "repo"

    @property
    def path_tmp_pyproject_toml(self) -> Path:
        """
        A temporary copy of pyproject.toml for building the layer.
        """
        return self.dir_repo / self.path_pyproject_toml.name

    @property
    def path_build_lambda_layer_in_container_script_in_local(self) -> Path:
        """
        Local path where the containerized build script is copied.

        This script contains the build logic that will be executed inside
        the Docker container to install dependencies.
        """
        return self.dir_project_root / "build_lambda_layer_in_container.py"
        # return self.dir_repo / "build_lambda_layer_in_container.py"

    @property
    def path_build_lambda_layer_in_container_script_in_container(self) -> str:
        """
        Container path where the build script can be executed.

        :return: Path string for use in Docker run commands
        """
        p = self.path_build_lambda_layer_in_container_script_in_local
        return self.get_path_in_container(p)

    @property
    def path_requirements_txt(self) -> Path:
        """
        The generated requirements.txt file path.
        """
        return self.dir_project_root / "requirements.txt"

    @property
    def path_poetry_lock(self) -> Path:
        """
        The original poetry.lock file path.
        """
        return self.dir_project_root / "poetry.lock"

    @property
    def path_tmp_poetry_lock(self) -> Path:
        """
        A temporary copy of poetry.lock for building the layer.
        """
        return self.dir_repo / "poetry.lock"

    @property
    def path_uv_lock(self) -> Path:
        """
        The original uv.lock file path.
        """
        return self.dir_project_root / "uv.lock"

    @property
    def path_tmp_uv_lock(self) -> Path:
        """
        A temporary copy of uv.lock for building the layer.
        """
        return self.dir_repo / "uv.lock"

    @property
    def path_private_repository_credentials_in_local(self) -> Path:
        """
        The private repository credentials file path.
        """
        return self.dir_repo / "private-repository-credentials.json"

    @property
    def path_private_repository_credentials_in_container(self) -> str:
        """
        The private repository credentials file path inside the container.
        """
        p = self.path_private_repository_credentials_in_local
        return self.get_path_in_container(p)

    @property
    def dir_artifacts(self) -> Path:
        """
        The directory to store all files to be included in the layer.zip.
        """
        return self.dir_build_lambda_layer / "artifacts"

    @property
    def dir_python(self) -> Path:
        """
        The AWS Lambda required ``python`` subdirectory.

        Ref:

        - https://docs.aws.amazon.com/lambda/latest/dg/python-layers.html
        """
        return self.dir_artifacts / "python"

    def clean(self, skip_prompt: bool = False):
        """
        Clean existing build directory to ensure fresh installation.

        Removes all artifacts from previous builds to prevent conflicts
        and ensure reproducible layer creation.

        :param skip_prompt: If True, skip user confirmation for directory removal
        """
        clean_build_directory(
            dir_build=self.dir_build_lambda_layer,
            folder_alias="lambda layer build folder",
            skip_prompt=skip_prompt,
        )

    def mkdirs(self):
        """
        Create all necessary directories for the build process.

        Ensures the directory structure is ready for dependency installation
        and layer artifact creation.
        """
        self.dir_repo.mkdir(parents=True, exist_ok=True)
        self.dir_python.mkdir(parents=True, exist_ok=True)

    def copy_file(
        self,
        p_src: Path,
        p_dst: Path,
        printer: T_PRINTER = print,
    ):
        """
        Copy a file with logging support.

        :param p_src: Source file path
        :param p_dst: Destination file path
        :param printer: Function to handle log messages
        """
        printer(f"Copy {p_src} to {p_dst}")
        shutil.copy(p_src, p_dst)

    def copy_build_script(self, p_src: Path, printer: T_PRINTER = print):
        """
        Copy containerized build script to the project directory.

        The build script contains tool-specific logic (pip/poetry/uv) that will
        be executed inside the Docker container.

        :param p_src: Path to the tool-specific build script
        :param printer: Function to handle log messages
        """
        self.copy_file(
            p_src=p_src,
            p_dst=self.path_build_lambda_layer_in_container_script_in_local,
            printer=printer,
        )

    def copy_pyproject_toml(self, printer: T_PRINTER = print):
        """
        Copy pyproject.toml to the isolated build directory.

        Creates a clean copy for dependency resolution without affecting
        the original project configuration.

        :param printer: Function to handle log messages
        """
        self.copy_file(
            p_src=self.path_pyproject_toml,
            p_dst=self.path_tmp_pyproject_toml,
            printer=printer,
        )

    def copy_poetry_lock(self, printer: T_PRINTER = print):
        """
        Copy poetry.lock to the isolated build directory.

        Ensures dependency versions remain consistent by using the locked
        dependency resolution from the original project.

        :param printer: Function to handle log messages
        """
        self.copy_file(
            p_src=self.path_poetry_lock,
            p_dst=self.path_tmp_poetry_lock,
            printer=printer,
        )

    def copy_uv_lock(self, printer: T_PRINTER = print):
        """
        Copy uv.lock to the isolated build directory.

        Maintains reproducible builds by preserving the exact dependency
        versions resolved by uv.

        :param printer: Function to handle log messages
        """
        self.copy_file(
            p_src=self.path_uv_lock,
            p_dst=self.path_tmp_uv_lock,
            printer=printer,
        )


@dataclasses.dataclass
class LayerS3Layout:
    """
    S3 directory layout manager for Lambda layer artifacts and versioning.

    This class provides a structured approach to organizing Lambda layer artifacts
    in S3 with proper versioning support. It manages both temporary upload locations
    and permanent versioned storage for requirements tracking and layer management.

    Assuming ``s3dir_lambda`` is ``s3://bucket/path/lambda``, the relevant paths are::

    - ``${s3dir_lambda}/layer/layer.zip``
        :meth:`s3path_temp_layer_zip`, Temporary upload location for layer zip file.
    - ``${s3dir_lambda}/layer/000001/requirements.txt``
        :meth:`get_s3path_layer_requirements_txt`, Versioned requirements file for layer version 1.
    - ``${s3dir_lambda}/layer/000002/requirements.txt``
        :meth:`get_s3path_layer_requirements_txt`, Versioned requirements file for layer version 2.
    - ``${s3dir_lambda}/layer/last-requirements.txt``
        :meth:`s3path_last_requirements_txt`, Requirements file from the most recently published layer version.
    """

    s3dir_lambda: "S3Path" = dataclasses.field()

    @property
    def s3path_temp_layer_zip(self) -> "S3Path":
        """
        Temporary S3 location for layer zip uploads before AWS Lambda layer publishing.

        This is a staging location used during the layer publishing process. AWS Lambda
        reads the zip from this location and stores it internally, so we don't need to
        maintain historical versions in S3.

        .. note::

            Since AWS manages layer storage internally, there's no need to maintain
            historical versions of the layer zip in S3.

        :return: S3Path to the temporary layer.zip file
        """
        return self.s3dir_lambda.joinpath("layer", "layer.zip")

    def get_s3path_layer_requirements_txt(
        self,
        layer_version: int,
    ) -> "S3Path":
        """
        Generate S3 path for a specific layer version's requirements.txt file.

        Each layer version gets its own directory with zero-padded numbering
        to maintain proper lexicographic ordering in S3.

        :param layer_version: Layer version number (e.g., 1, 2, 3...)
        :return: S3Path object pointing to the versioned requirements.txt file
                 (e.g., s3://bucket/path/lambda/layer/000001/requirements.txt)
        """
        return self.s3dir_lambda.joinpath(
            "layer",
            str(layer_version).zfill(ZFILL),
            "requirements.txt",
        )

    def get_s3path_layer_poetry_lock(
        self,
        layer_version: int,
    ) -> "S3Path":
        """
        Generate S3 path for a specific layer version's poetry.lock file.

        Each layer version gets its own directory with zero-padded numbering
        to maintain proper lexicographic ordering in S3.

        :param layer_version: Layer version number (e.g., 1, 2, 3...)
        :return: S3Path object pointing to the versioned poetry.lock file
                 (e.g., s3://bucket/path/lambda/layer/000001/poetry.lock)
        """
        return self.s3dir_lambda.joinpath(
            "layer",
            str(layer_version).zfill(ZFILL),
            "poetry.lock",
        )

    def get_s3path_layer_uv_lock(
        self,
        layer_version: int,
    ) -> "S3Path":
        """
        Generate S3 path for a specific layer version's uv.lock file.

        Each layer version gets its own directory with zero-padded numbering
        to maintain proper lexicographic ordering in S3.

        :param layer_version: Layer version number (e.g., 1, 2, 3...)
        :return: S3Path object pointing to the versioned uv.lock file
                 (e.g., s3://bucket/path/lambda/layer/000001/uv.lock)
        """
        return self.s3dir_lambda.joinpath(
            "layer",
            str(layer_version).zfill(ZFILL),
            "uv.lock",
        )

    @property
    def s3path_last_requirements_txt(self) -> "S3Path":
        """
        S3 path to the most recently published layer's requirements.txt file.

        This file serves as a reference point for dependency change detection.
        The build system compares the local requirements.txt with this file to
        determine whether a new layer version needs to be published.

        **Change Detection Logic**: If local requirements differ from this file,
        a new layer version is automatically created and published.

        :return: S3Path to the last-requirements.txt file
        """
        return self.s3dir_lambda.joinpath("layer", "last-requirements.txt")

    @property
    def s3path_last_poetry_lock(self) -> "S3Path":
        """
        S3 path to the most recently published layer's poetry.lock file.

        This file serves as a reference point for dependency change detection.
        The build system compares the local poetry.lock with this file to
        determine whether a new layer version needs to be published.

        **Change Detection Logic**: If local poetry.lock differs from this file,
        a new layer version is automatically created and published.

        :return: S3Path to the last-requirements.txt file
        """
        return self.s3dir_lambda.joinpath("layer", "last-poetry.lock")

    @property
    def s3path_last_uv_lock(self) -> "S3Path":
        """
        S3 path to the most recently published layer's uv.lock file.

        This file serves as a reference point for dependency change detection.
        The build system compares the local uv.lock with this file to
        determine whether a new layer version needs to be published.

        **Change Detection Logic**: If local uv.lock differs from this file,
        a new layer version is automatically created and published.

        :return: S3Path to the last-requirements.txt file
        """
        return self.s3dir_lambda.joinpath("layer", "last-uv.lock")


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
    """

    path_pyproject_toml: Path = dataclasses.field(default=REQ)
    printer: T_PRINTER = dataclasses.field(default=print)
    _tool: str = dataclasses.field(default=REQ)

    @cached_property
    def path_layout(self) -> LayerPathLayout:
        """
        :return: :class:`LayerPathLayout` object for managing build paths.
        """
        return LayerPathLayout(
            path_pyproject_toml=self.path_pyproject_toml,
        )

    def read_credentials(self):
        pass

    def step_01_print_info(self):
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

    def step_02_setup_build_dir(self, skip_prompt: bool = False):
        """
        Prepare the build environment by cleaning and creating directories.

        Ensures a clean slate for layer creation by removing previous artifacts
        and establishing the required directory structure.

        :param skip_prompt: If True, automatically remove existing build directory
        """
        dir = self.path_layout.dir_build_lambda_layer
        self.printer(f"--- Clean existing build directory: {dir}")
        self.path_layout.clean(skip_prompt=skip_prompt)
        self.path_layout.mkdirs()


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
    credentials: T.Optional[Credentials] = dataclasses.field(default=None)
    printer: T_PRINTER = dataclasses.field(default=print)

    @cached_property
    def path_layout(self) -> LayerPathLayout:
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
    def args(self) -> list[str]:
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

    def step_02_setup_private_repository_credential(self):
        """
        Configure private repository authentication (optional).

        Subclasses can override this method to set up credentials for
        accessing private PyPI servers or corporate package repositories.
        """
        if isinstance(self.credentials, Credentials) is False:
            return
        p = self.path_layout.path_private_repository_credentials_in_local
        self.credentials.dump(path=p)

    def step_03_docker_run(self):
        """
        Execute the Docker container build process.

        Runs the configured Docker command to build the Lambda layer
        inside the container environment.
        """
        subprocess.run(self.args)
