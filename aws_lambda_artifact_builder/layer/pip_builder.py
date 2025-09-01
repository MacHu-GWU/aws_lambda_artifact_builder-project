# -*- coding: utf-8 -*-

"""
Pip-based Lambda layer builder implementation.

This module provides Lambda layer creation using pip's ``--target`` installation method,
supporting both local and containerized builds. It offers the simplest approach to layer
creation since pip is universally available with Python installations.

**Public API Functions:**
    - :func:`build_layer_artifacts_using_pip_in_local`: Local pip-based builds
    - :func:`build_layer_artifacts_using_pip_in_container`: Containerized pip-based builds

**Private Repository Support:**
    Both functions support private PyPI repositories through the :class:`Credentials` parameter,
    which handles authentication for corporate package repositories and AWS CodeArtifact.
"""

import subprocess
import dataclasses
from pathlib import Path

from func_args.api import REQ
from ..vendor.better_pathlib import temp_cwd

from ..typehint import T_PRINTER
from ..paths import path_build_lambda_layer_using_pip_in_container_script

from .common import (
    Credentials,
    BasedLambdaLayerLocalBuilder,
    BasedLambdaLayerContainerBuilder,
)


@dataclasses.dataclass(frozen=True)
class PipBasedLambdaLayerLocalBuilder(
    BasedLambdaLayerLocalBuilder,
):
    """
    Command class for local pip-based Lambda layer builds (Internal API).
    
    This class implements the pip-specific build workflow for creating Lambda layers
    directly on the host machine. It extends the base local builder with pip-specific
    logic including credential handling for private repositories.
    
    **Not for direct use**: This is an internal command class. Use the public function
    :func:`build_layer_artifacts_using_pip_in_local` instead.
    
    **Key Features:**
    - Direct pip installation using ``--target`` flag
    - Private repository authentication via ``--index-url``
    - Pre-resolved requirements.txt processing
    - No Docker overhead for faster builds
    """

    path_bin_pip: Path = dataclasses.field(default=REQ)
    _tool: str = dataclasses.field(default="poetry")

    def step_01_print_info(self):
        """
        Display pip-specific build configuration.
        
        Extends the base info display with pip executable path information
        to provide visibility into which pip binary will be used for the build.
        """
        super().step_01_print_info()
        self.printer(f"path_bin_pip = {self.path_bin_pip}")

    def step_03_run_pip_install(
        self,
        credentials: Credentials | None = None,
    ):
        """
        Execute pip install with optional private repository authentication.
        
        Installs packages from requirements.txt directly into the Lambda layer's
        python directory using pip's ``--target`` flag. Supports private repository
        access through credential-based ``--index-url`` configuration.
        
        **Authentication Flow:**
        - If credentials provided: Uses ``--index-url`` with embedded authentication
        - If no credentials: Uses default PyPI and any configured pip indexes
        - Credentials format: ``https://username:token@hostname/simple/``
        
        **Command Example:**
        ``pip install -r requirements.txt -t artifacts/python --index-url https://user:pass@repo/simple/``
        
        :param credentials: Optional private repository authentication
        """
        path_bin_pip = self.path_bin_pip
        dir_repo = self.path_layout.dir_repo
        with temp_cwd(dir_repo):
            args = [
                f"{path_bin_pip}",
                "install",
                "-r",
                f"{self.path_layout.path_requirements_txt}",
                "-t",  # Target directory for package installation
                f"{self.path_layout.dir_python}",  # AWS Lambda python/ directory
            ]
            # Add private repository authentication if provided
            if credentials is not None:
                args.extend(
                    [
                        "--index-url",  # Override default PyPI with authenticated URL
                        credentials.pip_extra_index_url,  # Includes embedded credentials
                    ]
                )
            subprocess.run(args, cwd=dir_repo, check=True)


def build_layer_artifacts_using_pip_in_local(
    path_bin_pip: Path,
    path_pyproject_toml: Path,
    credentials: Credentials | None = None,
    skip_prompt: bool = False,
    printer: T_PRINTER = print,
):
    """
    Build Lambda layer artifacts using pip on the local machine (Public API).
    
    This function creates Lambda layer artifacts by installing dependencies directly
    on the host machine using pip's ``--target`` installation method. Best suited for
    development workflows on Linux hosts or when build speed is prioritized.
    
    **Process Flow:**
    1. Clean and prepare build directories
    2. Install packages from requirements.txt using pip --target
    3. Create AWS Lambda compatible directory structure (artifacts/python/)
    
    **Private Repository Support:**
    Supports authentication with private PyPI servers, corporate repositories,
    and AWS CodeArtifact through the credentials parameter.
    
    **Requirements:**
    - Must have requirements.txt file in project root
    - pip executable must be accessible (typically from virtual environment)
    - For best results, use pre-resolved requirements from Poetry/UV
    
    :param path_bin_pip: Path to pip executable, e.g., ``.venv/bin/pip``
    :param path_pyproject_toml: Path to pyproject.toml file (determines project root)
    :param credentials: Optional private repository authentication credentials
    :param skip_prompt: If True, automatically clean existing build directory
    :param printer: Function to handle progress messages, defaults to print
    
    **Example:**
    
    .. code-block:: python
    
        from pathlib import Path
        from aws_lambda_artifact_builder import build_layer_artifacts_using_pip_in_local
        
        build_layer_artifacts_using_pip_in_local(
            path_bin_pip=Path(".venv/bin/pip"),
            path_pyproject_toml=Path("pyproject.toml"),
            skip_prompt=True,
        )
    """
    builder = PipBasedLambdaLayerLocalBuilder(
        path_bin_pip=path_bin_pip,
        path_pyproject_toml=path_pyproject_toml,
        printer=printer,
    )
    builder.step_01_print_info()
    builder.step_02_setup_build_dir(skip_prompt=skip_prompt)
    builder.step_03_run_pip_install(credentials=credentials)


@dataclasses.dataclass(frozen=True)
class PipBasedLambdaLayerContainerBuilder(
    BasedLambdaLayerContainerBuilder,
):
    """
    Command class for containerized pip-based Lambda layer builds (Internal API).
    
    This class orchestrates Docker container-based builds using AWS SAM build images
    that match the Lambda runtime environment. It handles container setup, volume
    mounting, and script execution for pip-based dependency installation.
    
    **Not for direct use**: This is an internal command class. Use the public function
    :func:`build_layer_artifacts_using_pip_in_container` instead.
    
    **Container Process:**
    1. Copy pip-specific build script to project directory
    2. Set up private repository credentials (if provided)
    3. Execute Docker run with AWS SAM build image
    4. Script runs inside container using container's pip
    
    **Runtime Compatibility:**
    Uses official AWS Lambda container images to ensure the built layer
    works identically in the deployed Lambda environment.
    """
    
    def step_01_copy_build_script(self):
        """
        Copy the pip-specific container build script to the project directory.
        
        The build script contains pip installation logic that will be executed
        inside the Docker container. This script handles pip install commands
        with proper targeting and credential management within the container environment.
        """
        self.path_layout.copy_build_script(
            p_src=path_build_lambda_layer_using_pip_in_container_script,
            printer=self.printer,
        )


def build_layer_artifacts_using_pip_in_container(
    path_pyproject_toml: Path,
    py_ver_major: int,
    py_ver_minor: int,
    is_arm: bool,
    credentials: Credentials | None = None,
    printer: T_PRINTER = print,
):
    """
    Build Lambda layer artifacts using pip in a Docker container (Public API).
    
    This function creates Lambda layer artifacts by running pip inside an AWS SAM
    build container that matches the Lambda runtime environment. This ensures maximum
    compatibility between the built layer and the deployed Lambda function.
    
    **Container Benefits:**
    - **Runtime Compatibility**: Uses official AWS Lambda container images
    - **Platform Independence**: Works consistently across macOS, Windows, Linux
    - **Isolation**: Doesn't affect host Python environment
    - **Architecture Support**: Handles both x86_64 and ARM64 builds
    
    **Process Flow:**
    1. Copy pip build script to project directory
    2. Configure private repository credentials (if provided)
    3. Run Docker container with volume mounting
    4. Container executes pip install inside Lambda-compatible environment
    
    **Private Repository Support:**
    Credentials are written to a JSON file and made available inside the container
    for authentication with private PyPI servers and AWS CodeArtifact.
    
    **Requirements:**
    - Docker must be installed and running
    - Must have requirements.txt file in project root
    - Network access to pull AWS SAM build images
    
    :param path_pyproject_toml: Path to pyproject.toml file (determines project root)
    :param py_ver_major: Python major version (e.g., 3)
    :param py_ver_minor: Python minor version (e.g., 11)
    :param is_arm: If True, build for ARM64; if False, build for x86_64
    :param credentials: Optional private repository authentication credentials
    :param printer: Function to handle progress messages, defaults to print
    
    **Example:**
    
    .. code-block:: python
    
        from pathlib import Path
        from aws_lambda_artifact_builder import build_layer_artifacts_using_pip_in_container
        
        build_layer_artifacts_using_pip_in_container(
            path_pyproject_toml=Path("pyproject.toml"),
            py_ver_major=3,
            py_ver_minor=11,
            is_arm=False,  # Use True for ARM64 Lambda functions
        )
    """
    builder = PipBasedLambdaLayerContainerBuilder(
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
