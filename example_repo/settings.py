# -*- coding: utf-8 -*-

import sys
from pathlib import Path
from s3pathlib import S3Path
from boto_session_manager import BotoSesManager

dir_here = Path(__file__).absolute().parent

py_ver_major = sys.version_info.major
py_ver_minor = sys.version_info.minor

bsm = BotoSesManager(profile_name="esc_app_dev_us_east_1")
bucket = f"{bsm.aws_account_alias}-{bsm.aws_region}-artifacts"
prefix = "projects/aws_lambda_artifact_builder/example_repo/my_app/lambda/"
s3dir_lambda = S3Path(f"s3://{bucket}/{prefix}").to_dir()
layer_name = "aws_lambda_artifact_builder_my_app"

# ------------------------------------------------------------------------------
# Code below is for testing and debugging only
# It copy aws_lambda_artifact_builder source code to the current directory
# to simulate the "pip install aws_lambda_artifact_builder" command
# ------------------------------------------------------------------------------
import shutil

package_name = "aws_lambda_artifact_builder"
dir_src = dir_here.parent / package_name
dir_dst = dir_here / package_name
shutil.rmtree(dir_dst, ignore_errors=True)
shutil.copytree(dir_src, dir_dst)

# ------------------------------------------------------------------------------
# Get necessary settings
# ------------------------------------------------------------------------------
from pywf_internal_proprietary.api import PyWf
from aws_lambda_artifact_builder.api import Credentials

path_pyproject_toml = dir_here.joinpath("pyproject.toml")
pywf = PyWf.from_pyproject_toml(path_pyproject_toml)

index_name = "esc"
index_url = pywf.get_codeartifact_repository_endpoint()
username = "aws"
password = pywf.get_codeartifact_authorization_token()
credentials = Credentials(
    index_name=index_name,
    index_url=index_url,
    username=username,
    password=password,
)
