# -*- coding: utf-8 -*-

from datetime import datetime
from pathlib import Path

import aws_lambda_artifact_builder.api as aws_lambda_artifact_builder

from settings import index_name, index_url, username, password

# Current project directory
dir_here = Path(__file__).absolute().parent
# pip executable in the virtual environment
path_bin_pip = dir_here / ".venv" / "bin" / "pip"
# Python project configuration file
path_pyproject_toml = dir_here / "pyproject.toml"
# Private PyPI repository credentials
credentials = aws_lambda_artifact_builder.Credentials(
    index_name=index_name,
    index_url=index_url,
    username=username,
    password=password,
)

# Build the lambda layer artifacts
st = datetime.now()
aws_lambda_artifact_builder.build_layer_artifacts_using_pip_in_local(
    path_bin_pip=path_bin_pip,
    path_pyproject_toml=path_pyproject_toml,
    credentials=credentials,
    skip_prompt=True,
)
elapsed = (datetime.now() - st).total_seconds()
print(f"Total elapsed: {elapsed:.2f} seconds")
