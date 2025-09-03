# -*- coding: utf-8 -*-

"""
Integration test settings.

.. note::

    This module uses lazy loading pattern.
"""

import dataclasses
from pathlib import Path
from functools import cached_property
from s3pathlib import S3Path
from boto_session_manager import BotoSesManager
from pywf_internal_proprietary.api import PyWf

dir_here = Path(__file__).absolute().parent

# ------------------------------------------------------------------------------
# This code block is for testing and debugging only
# It copy aws_lambda_artifact_builder source code to the current directory
# to simulate the "pip install aws_lambda_artifact_builder" command
# ------------------------------------------------------------------------------
import shutil

package_name = "aws_lambda_artifact_builder"
dir_src = dir_here.parent / package_name
dir_dst = dir_here / package_name
if dir_dst.exists():
    shutil.rmtree(dir_dst)
shutil.copytree(dir_src, dir_dst)


def teardown_aws_lambda_artifact_builder():
    if dir_dst.exists():
        shutil.rmtree(dir_dst)


# ------------------------------------------------------------------------------
# End of code block for testing and debugging only
# ------------------------------------------------------------------------------
from aws_lambda_artifact_builder.api import Credentials


@dataclasses.dataclass
class Settings:
    layer_name: str = dataclasses.field()
    py_ver_major: int = dataclasses.field()
    py_ver_minor: int = dataclasses.field()
    is_arm: bool = dataclasses.field()
    aws_profile: str = dataclasses.field()
    aws_region: str = dataclasses.field()
    private_index_name: str | None = dataclasses.field(default=None)

    @property
    def path_pyproject_toml(self) -> Path:
        return dir_here.joinpath("pyproject.toml")

    @property
    def path_bin_pip(self) -> Path:
        return dir_here / ".venv" / "bin" / "pip"

    @property
    def path_bin_poetry(self) -> Path:
        return Path("poetry")

    @property
    def path_bin_uv(self) -> Path:
        return Path("uv")

    @cached_property
    def bsm(self):
        return BotoSesManager(profile_name="esc_app_dev_us_east_1")

    @property
    def s3_bucket(self) -> str:
        return f"{self.bsm.aws_account_alias}-{self.bsm.aws_region}-artifacts"

    @property
    def s3dir_lambda(self) -> S3Path:
        prefix = "projects/aws_lambda_artifact_builder/example_repo/my_app/lambda/"
        return S3Path(f"s3://{self.s3_bucket}/{prefix}").to_dir()

    @cached_property
    def pywf(self) -> PyWf:
        return PyWf.from_pyproject_toml(self.path_pyproject_toml)

    @cached_property
    def credentials(self) -> Credentials | None:
        if self.private_index_name is None:
            return None
        index_url = self.pywf.get_codeartifact_repository_endpoint()
        username = "aws"
        password = self.pywf.get_codeartifact_authorization_token()
        credentials = Credentials(
            index_name=self.private_index_name,
            index_url=index_url,
            username=username,
            password=password,
        )
        return credentials


settings = Settings(
    layer_name="aws_lambda_artifact_builder_my_app",
    py_ver_major=3,
    py_ver_minor=11,
    is_arm=False,
    aws_profile="esc_app_dev_us_east_1",
    aws_region="us-east-1",
    private_index_name="esc",
    # Disable Credentials if you don't need to access a private repository
    # private_index_name=None,
)
