# -*- coding: utf-8 -*-

from pathlib import Path
from datetime import datetime

from settings import credentials
import aws_lambda_artifact_builder.api as aws_lambda_artifact_builder

# Current project directory
dir_here = Path(__file__).absolute().parent
# poetry executable in the virtual environment
path_bin_poetry = dir_here / ".venv" / "bin" / "poetry"
# Python project configuration file
path_pyproject_toml = dir_here / "pyproject.toml"

# Build the lambda layer artifacts
st = datetime.now()
aws_lambda_artifact_builder.build_layer_artifacts_using_poetry_in_local(
    path_bin_poetry=path_bin_poetry,
    path_pyproject_toml=path_pyproject_toml,
    credentials=credentials,
    # credentials=None, # Use this if you don't need to access a private repository
    skip_prompt=True,
)
elapsed = (datetime.now() - st).total_seconds()
print(f"Total elapsed: {elapsed:.2f} seconds")
