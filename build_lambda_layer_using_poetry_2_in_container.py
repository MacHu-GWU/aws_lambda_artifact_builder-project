# -*- coding: utf-8 -*-

"""

"""

from datetime import datetime
from aws_lambda_artifact_builder.layer.poetry_builder import (
    build_layer_artifacts_using_poetry_in_container,
)

from pathlib import Path
from s3pathlib import S3Path
from boto_session_manager import BotoSesManager

dir_here = Path(__file__).absolute().parent  # Current project directory
path_pyproject_toml = dir_here / "pyproject.toml"  # Project configuration file
# This installs the current package into the build directory without dependencies
st = datetime.now()
build_layer_artifacts_using_poetry_in_container(
    path_pyproject_toml=path_pyproject_toml,
    py_ver_major=3,
    py_ver_minor=11,
    is_arm=False,
)
elapsed = (datetime.now() - st).total_seconds()
print(f"Total elapsed: {elapsed:.2f} seconds")