# -*- coding: utf-8 -*-

"""

"""

from pathlib import Path
from datetime import datetime

from settings import credentials
import aws_lambda_artifact_builder.api as aws_lambda_artifact_builder

# Current project directory
dir_here = Path(__file__).absolute().parent
# Python project configuration file
path_pyproject_toml = dir_here / "pyproject.toml"

# Build the lambda layer artifacts
st = datetime.now()
aws_lambda_artifact_builder.build_layer_artifacts_using_uv_in_container(
    path_pyproject_toml=path_pyproject_toml,
    py_ver_major=3,
    py_ver_minor=11,
    credentials=credentials,
    is_arm=False,
)
elapsed = (datetime.now() - st).total_seconds()
print(f"Total elapsed: {elapsed:.2f} seconds")
