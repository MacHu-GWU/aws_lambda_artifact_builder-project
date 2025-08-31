# -*- coding: utf-8 -*-

"""

"""

from aws_lambda_artifact_builder.layer import (
    build_layer_artifacts_using_poetry,
)

from pathlib import Path
from s3pathlib import S3Path
from boto_session_manager import BotoSesManager

# ------------------------------------------------------------------------------
# Step 1: Build source artifacts using pip
# ------------------------------------------------------------------------------
# Define paths for the build process
dir_home = Path.home()
dir_here = Path(__file__).absolute().parent  # Current project directory
path_bin_poetry = dir_home / ".pyenv" / "shims" / "poetry"
path_pyproject_toml = dir_here / "pyproject.toml"  # Project configuration file
dir_lambda_layer_build = (
    dir_here / "build" / "lambda" / "layer" / "build"
)  # Target build directory

# This installs the current package into the build directory without dependencies
build_layer_artifacts_using_poetry(
    path_bin_poetry=path_bin_poetry,
    path_pyproject_toml=path_pyproject_toml,
    dir_lambda_layer_build=dir_lambda_layer_build,
    verbose=True,  # Show detailed output
    skip_prompt=True,  # Automatically clean existing build directory
)
