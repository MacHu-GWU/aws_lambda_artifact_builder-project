# -*- coding: utf-8 -*-

"""
"""

import typing as T
import dataclasses
from pathlib import Path
from functools import cached_property

from func_args.api import BaseFrozenModel, REQ

from ..constants import S3MetadataKeyEnum, LayerBuildToolEnum
from ..imports import S3Path, simple_aws_lambda

from .foundation import BaseLogger
from .package import LambdaLayerZipper
from .upload import upload_layer_zip_to_s3
from .publish import LambdaLayerVersionPublisher


if T.TYPE_CHECKING:  # pragma: no cover
    from mypy_boto3_s3 import S3Client
    from mypy_boto3_lambda import LambdaClient


@dataclasses.dataclass(frozen=True)
class BuildPackageUploadAndPublishWorkflow(BaseLogger):
    """ """

    layer_name: str = dataclasses.field(default=REQ)
    path_pyproject_toml: Path = dataclasses.field(default=REQ)
    s3dir_lambda: "S3Path" = dataclasses.field(default=REQ)
    s3_client: "S3Client" = dataclasses.field(default=REQ)
    lambda_client: "LambdaClient" = dataclasses.field(default=REQ)
    layer_build_tool: LayerBuildToolEnum = dataclasses.field(default=REQ)
    ignore_package_list: list[str] | None = dataclasses.field(default=None)
    publish_layer_version_kwargs: dict[str, T.Any] | None = dataclasses.field(
        default=None
    )

    def run(self):
        self.package()
        self.upload()
        self.publish()

    def package(self):
        zipper = LambdaLayerZipper(
            path_pyproject_toml=self.path_pyproject_toml,
            layer_build_tool=self.layer_build_tool,
            ignore_package_list=self.ignore_package_list,
            verbose=self.verbose,
        )
        return zipper.run()

    def upload(self):
        return upload_layer_zip_to_s3(
            s3_client=self.s3_client,
            path_pyproject_toml=self.path_pyproject_toml,
            s3dir_lambda=self.s3dir_lambda,
            layer_build_tool=self.layer_build_tool,
            verbose=self.verbose,
            printer=self.printer,
        )

    def publish(self):
        publisher = LambdaLayerVersionPublisher(
            layer_name=self.layer_name,
            path_pyproject_toml=self.path_pyproject_toml,
            s3dir_lambda=self.s3dir_lambda,
            layer_build_tool=self.layer_build_tool,
            s3_client=self.s3_client,
            lambda_client=self.lambda_client,
            publish_layer_version_kwargs=self.publish_layer_version_kwargs,
            verbose=self.verbose,
            printer=self.printer,
        )
        return publisher.run()
