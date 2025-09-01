# -*- coding: utf-8 -*-

"""
UV-based Lambda layer builder implementation.

This module provides Lambda layer creation using UV's ultra-fast dependency management,
supporting both local and containerized builds. UV offers the fastest dependency
resolution and installation while maintaining compatibility with pip and Poetry workflows.

**Public API Functions:**
    - :func:`build_layer_artifacts_using_uv_in_local`: Local UV-based builds
    - :func:`build_layer_artifacts_using_uv_in_container`: Containerized UV-based builds

**Private Repository Support:**
    Both functions support private PyPI repositories through environment variable-based
    authentication as documented in UV's credential configuration.
"""

import os
import subprocess
import dataclasses
from pathlib import Path

from func_args.api import REQ
from ..vendor.better_pathlib import temp_cwd

from ..typehint import T_PRINTER
from ..paths import path_build_lambda_layer_using_uv_in_container_script

from .common import (
    Credentials,
    BasedLambdaLayerLocalBuilder,
    BasedLambdaLayerContainerBuilder,
)


@dataclasses.dataclass(frozen=True)
class UVBasedLambdaLayerLocalBuilder(
    BasedLambdaLayerLocalBuilder,
):
    """
    Command class for local UV-based Lambda layer builds (Internal API).
    
    This class implements UV-specific build workflow using lock files and
    UV's high-performance dependency resolution.
    
    **Not for direct use**: Use :func:`build_layer_artifacts_using_uv_in_local` instead.
    
    **Key Features:**

    - Frozen lock file installation (--frozen)
    - Environment variable authentication (UV_INDEX_*)
    - Development dependency exclusion (--no-dev)
    - Copy-based linking for Lambda compatibility (--link-mode=copy)
    """

    path_bin_uv: Path = dataclasses.field(default=REQ)
    _tool: str = dataclasses.field(default="uv")

    def step_01_print_info(self):
        super().step_01_print_info()
        self.printer(f"path_bin_uv = {self.path_bin_uv}")

    def step_03_prepare_uv_stuff(self):
        """
        Copy UV project files to build directory.
        
        Copies pyproject.toml and uv.lock to ensure reproducible builds
        with exact dependency versions as resolved by UV.
        """
        self.path_layout.copy_pyproject_toml(printer=self.printer)
        self.path_layout.copy_uv_lock(printer=self.printer)

    def _uv_login(self, credentials: Credentials):
        """
        Configure UV authentication via environment variables.
        
        UV uses UV_INDEX_{SOURCE}_USERNAME/PASSWORD environment variables
        for private repository authentication, following UV's documented
        credential configuration pattern.
        
        :param credentials: Private repository authentication credentials
        """
        self.printer("Setting up uv credentials ...")
        # uv use environment variables to get the private repository
        # Http basic auth credentials.
        # See: https://docs.astral.sh/uv/reference/environment/#uv_index_url
        source_name = credentials.index_name.replace("-", "_").upper()
        key = f"UV_INDEX_{source_name}_USERNAME"
        os.environ[key] = "aws"
        self.printer(f"Set environment variable {key}")
        key = f"UV_INDEX_{source_name}_PASSWORD"
        os.environ[key] = credentials.password
        self.printer(f"Set environment variable {key}")

    def step_04_run_uv_sync(
        self,
        credentials: Credentials | None = None,
    ):
        """
        Execute UV sync with lock file constraints.
        
        Runs UV sync with --frozen to prevent lock file updates, --no-dev to exclude
        development dependencies, and --no-install-project to exclude the project itself.
        Uses --link-mode=copy for Lambda layer compatibility.
        
        :param credentials: Optional private repository authentication
        """
        path_bin_uv = self.path_bin_uv
        dir_repo = self.path_layout.dir_repo
        with temp_cwd(dir_repo):
            if credentials is not None:
                self._uv_login(credentials)

            self.printer("Run 'uv sync' ...")
            args = [
                f"{path_bin_uv}",
                "sync",
                "--frozen",
                "--no-dev",
                "--no-install-project",
                "--link-mode=copy",
            ]
            subprocess.run(args, cwd=dir_repo, check=True)


def build_layer_artifacts_using_uv_in_local(
    path_bin_uv: Path,
    path_pyproject_toml: Path,
    credentials: Credentials | None = None,
    skip_prompt: bool = False,
    printer: T_PRINTER = print,
):
    """
    Build Lambda layer artifacts using UV on the local machine (Public API).
    
    Creates Lambda layer artifacts using UV's ultra-fast dependency management
    and lock files. UV provides the fastest dependency resolution while maintaining
    compatibility with standard Python packaging workflows.
    
    **Requirements:**
    - Must have pyproject.toml and uv.lock files in project root
    - UV executable must be accessible
    
    :param path_bin_uv: Path to UV executable
    :param path_pyproject_toml: Path to pyproject.toml file (determines project root)
    :param credentials: Optional private repository authentication credentials
    :param skip_prompt: If True, automatically clean existing build directory
    :param printer: Function to handle progress messages, defaults to print
    """
    builder = UVBasedLambdaLayerLocalBuilder(
        path_bin_uv=path_bin_uv,
        path_pyproject_toml=path_pyproject_toml,
        printer=printer,
    )
    builder.step_01_print_info()
    builder.step_02_setup_build_dir(skip_prompt=skip_prompt)
    builder.step_03_prepare_uv_stuff()
    builder.step_04_run_uv_sync(credentials=credentials)


@dataclasses.dataclass(frozen=True)
class UVBasedLambdaLayerContainerBuilder(
    BasedLambdaLayerContainerBuilder,
):
    """
    Command class for containerized UV-based Lambda layer builds (Internal API).
    
    Orchestrates Docker container builds using UV within AWS SAM build images.
    
    **Not for direct use**: Use :func:`build_layer_artifacts_using_uv_in_container` instead.
    """

    def step_01_copy_build_script(
        self,
        path_script: Path = path_build_lambda_layer_using_uv_in_container_script,
    ):
        """
        Copy the UV-specific container build script to the project directory.
        
        The build script handles UV installation and dependency synchronization
        within the Docker container environment.
        """
        self.path_layout.copy_build_script(
            p_src=path_script,
            printer=self.printer,
        )


def build_layer_artifacts_using_uv_in_container(
    path_pyproject_toml: Path,
    py_ver_major: int,
    py_ver_minor: int,
    is_arm: bool,
    credentials: Credentials | None = None,
    printer: T_PRINTER = print,
):
    """
    Build Lambda layer artifacts using UV in a Docker container (Public API).
    
    Creates Lambda layer artifacts by running UV inside an AWS SAM build container,
    combining UV's speed with runtime compatibility and reproducible builds through lock files.
    
    **Requirements:**
    - Docker must be installed and running
    - Must have pyproject.toml and uv.lock files in project root
    
    :param path_pyproject_toml: Path to pyproject.toml file (determines project root)
    :param py_ver_major: Python major version (e.g., 3)
    :param py_ver_minor: Python minor version (e.g., 11)
    :param is_arm: If True, build for ARM64; if False, build for x86_64
    :param credentials: Optional private repository authentication credentials
    :param printer: Function to handle progress messages, defaults to print
    """
    builder = UVBasedLambdaLayerContainerBuilder(
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
