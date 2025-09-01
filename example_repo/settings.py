# -*- coding: utf-8 -*-

from pathlib import Path
from pywf_internal_proprietary.api import PyWf
from aws_lambda_artifact_builder.api import Credentials

dir_here = Path(__file__).absolute().parent
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

# ------------------------------------------------------------------------------
# Code below is for testing and debugging only
# ------------------------------------------------------------------------------
import shutil

package_name = "aws_lambda_artifact_builder"
dir_src = dir_here.parent / package_name
dir_dst = dir_here / package_name
shutil.rmtree(dir_dst, ignore_errors=True)
shutil.copytree(dir_src, dir_dst)
