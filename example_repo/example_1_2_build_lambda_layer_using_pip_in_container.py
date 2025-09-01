# -*- coding: utf-8 -*-

"""

"""

from pathlib import Path
from datetime import datetime

import aws_lambda_artifact_builder.api as aws_lambda_artifact_builder

from settings import credentials

# Current project directory
dir_here = Path(__file__).absolute().parent
# pip executable in the virtual environment
path_bin_pip = dir_here / ".venv" / "bin" / "pip"
# Python project configuration file
path_pyproject_toml = dir_here / "pyproject.toml"

# Build the lambda layer artifacts
st = datetime.now()
aws_lambda_artifact_builder.build_layer_artifacts_using_pip_in_container(
    path_pyproject_toml=path_pyproject_toml,
    py_ver_major=3,
    py_ver_minor=11,
    credentials=credentials,
    is_arm=False,
)
elapsed = (datetime.now() - st).total_seconds()
print(f"Total elapsed: {elapsed:.2f} seconds")
