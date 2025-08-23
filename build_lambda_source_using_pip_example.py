# -*- coding: utf-8 -*-

from aws_lambda_artifact_builder.source import (
    build_source_artifacts_using_pip,
    create_source_zip,
    upload_source_artifacts,
)

from pathlib import Path
from s3pathlib import S3Path
from boto_session_manager import BotoSesManager

dir_here = Path(__file__).absolute().parent
path_bin_pip = dir_here / ".venv" / "bin" / "pip"
path_setup_py_or_pyproject_toml = dir_here / "pyproject.toml"
dir_lambda_source_build = dir_here / "build" / "lambda" / "source" / "build"

build_source_artifacts_using_pip(
    path_bin_pip=path_bin_pip,
    path_setup_py_or_pyproject_toml=path_setup_py_or_pyproject_toml,
    dir_lambda_source_build=dir_lambda_source_build,
    verbose=True,
    skip_prompt=True,
)

path_source_zip = dir_here / "build" / "lambda" / "source" / "source.zip"
source_sha256 = create_source_zip(
    dir_lambda_source_build=dir_lambda_source_build,
    path_source_zip=path_source_zip,
    verbose=True,
)

bsm = BotoSesManager(profile_name="bmt_app_dev_us_east_1")
bucket = f"{bsm.aws_account_alias}-{bsm.aws_region}-artifacts"
s3dir_lambda = S3Path(f"s3://{bucket}/projects/aws_lambda_artifact_builder/lambda/")
upload_source_artifacts(
    s3_client=bsm.s3_client,
    source_version="0.1.1",
    source_sha256=source_sha256,
    path_source_zip=path_source_zip,
    s3dir_lambda=s3dir_lambda,
    verbose=True,
)
