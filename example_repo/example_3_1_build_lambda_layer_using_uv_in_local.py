# -*- coding: utf-8 -*-

from pathlib import Path

from settings import credentials, teardown_aws_lambda_artifact_builder
import aws_lambda_artifact_builder.api as aws_lambda_artifact_builder

# Current project directory
dir_here = Path(__file__).absolute().parent
# uv executable in the virtual environment
path_bin_uv = Path("uv")
# Python project configuration file
path_pyproject_toml = dir_here / "pyproject.toml"
# Disable Credentials if you don't need to access a private repository
# credentials = None

# Build the lambda layer artifacts
with aws_lambda_artifact_builder.DateTimeTimer(title="Total build time"):
    builder = aws_lambda_artifact_builder.UVBasedLambdaLayerLocalBuilder(
        path_bin_uv=path_bin_uv,
        path_pyproject_toml=path_pyproject_toml,
        credentials=credentials,
        skip_prompt=True,
    )
    builder.run()

teardown_aws_lambda_artifact_builder()
