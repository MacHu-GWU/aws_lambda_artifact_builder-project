# -*- coding: utf-8 -*-

"""
Poetry-based Lambda layer builder implementation.

This module provides Lambda layer creation using Poetry's dependency management,
supporting both local and containerized builds. Poetry offers reproducible builds
through lock files and sophisticated dependency resolution.

**Public API Functions:**
    - :func:`build_layer_artifacts_using_poetry_in_local`: Local Poetry-based builds
    - :func:`build_layer_artifacts_using_poetry_in_container`: Containerized Poetry-based builds

**Private Repository Support:**
    Both functions support private PyPI repositories through environment variable-based
    authentication as documented in Poetry's credential configuration.
"""

import os
import subprocess
import dataclasses
from pathlib import Path

from func_args.api import REQ
from ..vendor.better_pathlib import temp_cwd

from ..typehint import T_PRINTER
from ..paths import path_build_lambda_layer_using_poetry_in_container_script

from .common import (
    Credentials,
    BasedLambdaLayerLocalBuilder,
    BasedLambdaLayerContainerBuilder,
)


@dataclasses.dataclass(frozen=True)
class PoetryBasedLambdaLayerLocalBuilder(
    BasedLambdaLayerLocalBuilder,
):
    """
    Command class for local Poetry-based Lambda layer builds (Internal API).
    
    This class implements Poetry-specific build workflow using virtual environments
    and lock file-based dependency resolution.
    
    **Not for direct use**: Use :func:`build_layer_artifacts_using_poetry_in_local` instead.
    
    **Key Features:**

    - Lock file-based reproducible builds
    - Environment variable authentication (POETRY_HTTP_BASIC_*)
    - In-project virtual environment setup
    - No root package installation (--no-root)
    """

    path_bin_poetry: Path = dataclasses.field(default=REQ)
    _tool: str = dataclasses.field(default="poetry")

    def step_01_print_info(self):
        """
        Display Poetry-specific build information.
        """
        super().step_01_print_info()
        self.printer(f"path_bin_poetry = {self.path_bin_poetry}")

    def step_03_prepare_poetry_stuff(self):
        """
        Copy Poetry project files to build directory.
        
        Copies pyproject.toml and poetry.lock to ensure reproducible builds
        with exact dependency versions as resolved in development.
        """
        self.path_layout.copy_pyproject_toml(printer=self.printer)
        self.path_layout.copy_poetry_lock(printer=self.printer)

    def _poetry_login(self, credentials: Credentials):
        """
        Configure Poetry authentication via environment variables.
        
        Poetry uses POETRY_HTTP_BASIC_{SOURCE}_USERNAME/PASSWORD environment
        variables for private repository authentication, following Poetry's
        documented credential configuration pattern.
        
        :param credentials: Private repository authentication credentials
        """
        self.printer("Setting up Poetry credentials ...")
        # poetry use environment variables to get the private repository
        # Http basic auth credentials.
        # See: https://python-poetry.org/docs/repositories/#configuring-credentials
        source_name = credentials.index_name.replace("-", "_").upper()
        key = f"POETRY_HTTP_BASIC_{source_name}_USERNAME"
        os.environ[key] = "aws"
        self.printer(f"Set environment variable {key}")
        key = f"POETRY_HTTP_BASIC_{source_name}_PASSWORD"
        os.environ[key] = credentials.password
        self.printer(f"Set environment variable {key}")

    def step_04_run_poetry_install(
        self,
        credentials: Credentials | None = None,
    ):
        """
        Execute Poetry installation with lock file constraints.
        
        Runs Poetry install with --no-root to exclude the project package itself,
        installing only dependencies into an in-project virtual environment.
        
        :param credentials: Optional private repository authentication
        """
        path_bin_poetry = self.path_bin_poetry
        dir_repo = self.path_layout.dir_repo
        with temp_cwd(dir_repo):
            self.printer("Run 'poetry config virtualenvs.in-project true'")
            args = [
                f"{path_bin_poetry}",
                "config",
                "virtualenvs.in-project",
                "true",
            ]
            subprocess.run(args, cwd=dir_repo, check=True)
            if credentials is not None:
                self._poetry_login(credentials)

            self.printer("Run 'poetry install --no-root'")
            args = [
                f"{path_bin_poetry}",
                "install",
                "--no-root",
            ]
            subprocess.run(args, cwd=dir_repo, check=True)


def build_layer_artifacts_using_poetry_in_local(
    path_bin_poetry: Path,
    path_pyproject_toml: Path,
    credentials: Credentials | None = None,
    skip_prompt: bool = False,
    printer: T_PRINTER = print,
):
    """
    Build Lambda layer artifacts using Poetry on the local machine (Public API).
    
    Creates Lambda layer artifacts using Poetry's dependency management and lock files
    for reproducible builds. Poetry provides more sophisticated dependency resolution
    than pip and ensures consistent builds across environments.
    
    **Requirements:**

    - Must have pyproject.toml and poetry.lock files in project root
    - Poetry executable must be accessible
    
    :param path_bin_poetry: Path to Poetry executable
    :param path_pyproject_toml: Path to pyproject.toml file (determines project root)
    :param credentials: Optional private repository authentication credentials
    :param skip_prompt: If True, automatically clean existing build directory
    :param printer: Function to handle progress messages, defaults to print
    """
    builder = PoetryBasedLambdaLayerLocalBuilder(
        path_bin_poetry=path_bin_poetry,
        path_pyproject_toml=path_pyproject_toml,
        printer=printer,
    )
    builder.step_01_print_info()
    builder.step_02_setup_build_dir(skip_prompt=skip_prompt)
    builder.step_03_prepare_poetry_stuff()
    builder.step_04_run_poetry_install(credentials=credentials)


@dataclasses.dataclass(frozen=True)
class PoetryBasedLambdaLayerContainerBuilder(
    BasedLambdaLayerContainerBuilder,
):
    """
    Command class for containerized Poetry-based Lambda layer builds (Internal API).
    
    Orchestrates Docker container builds using Poetry within AWS SAM build images.
    
    **Not for direct use**: Use :func:`build_layer_artifacts_using_poetry_in_container` instead.
    """

    def step_01_copy_build_script(self):
        """
        Copy the Poetry-specific container build script to the project directory.
        
        The build script handles Poetry installation and dependency resolution
        within the Docker container environment.
        """
        self.path_layout.copy_build_script(
            p_src=path_build_lambda_layer_using_poetry_in_container_script,
            printer=self.printer,
        )


def build_layer_artifacts_using_poetry_in_container(
    path_pyproject_toml: Path,
    py_ver_major: int,
    py_ver_minor: int,
    is_arm: bool,
    credentials: Credentials | None = None,
    printer: T_PRINTER = print,
):
    """
    Build Lambda layer artifacts using Poetry in a Docker container (Public API).
    
    Creates Lambda layer artifacts by running Poetry inside an AWS SAM build container,
    ensuring runtime compatibility and reproducible builds through lock files.
    
    **Requirements:**
    - Docker must be installed and running
    - Must have pyproject.toml and poetry.lock files in project root
    
    :param path_pyproject_toml: Path to pyproject.toml file (determines project root)
    :param py_ver_major: Python major version (e.g., 3)
    :param py_ver_minor: Python minor version (e.g., 11)
    :param is_arm: If True, build for ARM64; if False, build for x86_64
    :param credentials: Optional private repository authentication credentials
    :param printer: Function to handle progress messages, defaults to print
    """
    builder = PoetryBasedLambdaLayerContainerBuilder(
        path_pyproject_toml=path_pyproject_toml,
        py_ver_major=py_ver_major,
        py_ver_minor=py_ver_minor,
        is_arm=is_arm,
        credentials=credentials,
        printer=printer,
    )

    builder.step_01_copy_build_script()
    builder.step_02_setup_private_repository_credential()
    builder.step_03_docker_run()
