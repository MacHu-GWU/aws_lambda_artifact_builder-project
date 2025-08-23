# -*- coding: utf-8 -*-

"""

"""

from aws_lambda_artifact_builder.source import build_package_upload_source_artifacts

from pathlib import Path
from s3pathlib import S3Path
from boto_session_manager import BotoSesManager

dir_here = Path(__file__).absolute().parent
dir_project_root = dir_here / "pyproject.toml"
bsm = BotoSesManager(profile_name="bmt_app_dev_us_east_1")
bucket = f"{bsm.aws_account_alias}-{bsm.aws_region}-artifacts"
s3dir_lambda = S3Path(f"s3://{bucket}/projects/aws_lambda_artifact_builder/lambda/")

build_package_upload_source_artifacts(
    s3_client=bsm.s3_client,
    dir_project_root=dir_here,
    s3dir_lambda=s3dir_lambda,
    verbose=True,
    skip_prompt=True,
)
