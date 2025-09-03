# -*- coding: utf-8 -*-

"""
All-in-one Lambda layer workflow - Build, Package, Upload, and Publish in one place.

This module provides a unified workflow class that combines all four steps of Lambda layer creation:

1. **Build**: Install dependencies using containerized build tools
2. **Package**: Create optimized zip archives  
3. **Upload**: Deploy artifacts to S3 storage
4. **Publish**: Create versioned Lambda layers with intelligent change detection
"""

import typing as T
import dataclasses
from pathlib import Path

from func_args.api import REQ

from ..constants import LayerBuildToolEnum
from ..imports import S3Path

from .foundation import BaseLogger, Credentials
from .pip_builder import PipBasedLambdaLayerContainerBuilder
from .poetry_builder import PoetryBasedLambdaLayerContainerBuilder
from .uv_builder import UVBasedLambdaLayerContainerBuilder
from .package import LambdaLayerZipper
from .upload import upload_layer_zip_to_s3
from .publish import LambdaLayerVersionPublisher


if T.TYPE_CHECKING:  # pragma: no cover
    from mypy_boto3_s3 import S3Client
    from mypy_boto3_lambda import LambdaClient


@dataclasses.dataclass(frozen=True)
class LambdaLayerBuildPackageUploadAndPublishWorkflow(BaseLogger):
    """
    All-in-one workflow for Lambda layer creation and deployment.
    
    This class orchestrates the complete Lambda layer lifecycle in a single interface,
    combining build, package, upload, and publish operations. It provides both unified
    execution via :meth:`run()` and granular control through individual step methods.

    **Workflow Steps:**

    1. :meth:`step_1_build()` - Uses container-based builders from :mod:`~aws_lambda_artifact_builder.layer.build`
    2. :meth:`step_2_package()` - Creates optimized zip using :class:`~aws_lambda_artifact_builder.layer.package.LambdaLayerZipper`
    3. :meth:`step_3_upload()` - Deploys to S3 via :func:`~aws_lambda_artifact_builder.layer.upload.upload_layer_zip_to_s3`
    4. :meth:`step_4_publish()` - Creates layer versions with :class:`~aws_lambda_artifact_builder.layer.publish.LambdaLayerVersionPublisher`

    **Multi-Tool Support:**

    The workflow automatically selects the appropriate builder based on ``layer_build_tool``:

    - :class:`~aws_lambda_artifact_builder.layer.build.PipBasedLambdaLayerContainerBuilder` for pip
    - :class:`~aws_lambda_artifact_builder.layer.build.PoetryBasedLambdaLayerContainerBuilder` for Poetry  
    - :class:`~aws_lambda_artifact_builder.layer.build.UVBasedLambdaLayerContainerBuilder` for UV

    **Usage Example:**

    .. code-block:: python

        workflow = BuildPackageUploadAndPublishWorkflow(
            layer_name="my-python-deps",
            py_ver_major=3, py_ver_minor=11,
            path_pyproject_toml=Path("pyproject.toml"),
            s3dir_lambda=S3Path("s3://bucket/lambda/"),
            s3_client=s3_client,
            lambda_client=lambda_client, 
            layer_build_tool=LayerBuildToolEnum.uv,
        )
        
        # Execute complete workflow
        workflow.run()
        
        # Or execute individual steps
        workflow.build()
        workflow.package() 
        workflow.upload()
        workflow.publish()

    :param layer_name: Name for the Lambda layer
    :param py_ver_major: Python major version (e.g., 3)
    :param py_ver_minor: Python minor version (e.g., 11)
    :param credentials: Optional private repository credentials
    :param is_arm: Whether to build for ARM64 architecture (default: False)
    :param path_pyproject_toml: Path to project's pyproject.toml file
    :param s3dir_lambda: S3 directory for Lambda artifacts
    :param s3_client: Boto3 S3 client for uploads
    :param lambda_client: Boto3 Lambda client for layer publishing
    :param layer_build_tool: Build tool to use (pip/poetry/uv)
    :param ignore_package_list: Packages to exclude from layer zip
    :param publish_layer_version_kwargs: Additional Lambda API parameters
    """
    layer_name: str = dataclasses.field(default=REQ)
    py_ver_major: int = dataclasses.field(default=REQ)
    py_ver_minor: int = dataclasses.field(default=REQ)
    credentials: Credentials | None = dataclasses.field(default=None)
    is_arm: bool = dataclasses.field(default=False)
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
        self.step_1_build()
        self.step_2_package()
        self.step_3_upload()
        self.step_4_publish()

    def step_1_build(self):
        if self.layer_build_tool == LayerBuildToolEnum.pip:
            builder = PipBasedLambdaLayerContainerBuilder(
                path_pyproject_toml=self.path_pyproject_toml,
                py_ver_major=self.py_ver_major,
                py_ver_minor=self.py_ver_minor,
                credentials=self.credentials,
                is_arm=self.is_arm,
                verbose=self.verbose,
                printer=self.printer,
            )
        elif self.layer_build_tool == LayerBuildToolEnum.poetry:
            builder = PoetryBasedLambdaLayerContainerBuilder(
                path_pyproject_toml=self.path_pyproject_toml,
                py_ver_major=self.py_ver_major,
                py_ver_minor=self.py_ver_minor,
                credentials=self.credentials,
                is_arm=self.is_arm,
                verbose=self.verbose,
                printer=self.printer,
            )
        elif self.layer_build_tool == LayerBuildToolEnum.uv:
            builder = UVBasedLambdaLayerContainerBuilder(
                path_pyproject_toml=self.path_pyproject_toml,
                py_ver_major=self.py_ver_major,
                py_ver_minor=self.py_ver_minor,
                credentials=self.credentials,
                is_arm=self.is_arm,
                verbose=self.verbose,
                printer=self.printer,
            )
        else: # pragma: no cover
            raise ValueError(f"Unsupported layer_build_tool: {self.layer_build_tool}")
        builder.run()

    def step_2_package(self):
        zipper = LambdaLayerZipper(
            path_pyproject_toml=self.path_pyproject_toml,
            layer_build_tool=self.layer_build_tool,
            ignore_package_list=self.ignore_package_list,
            verbose=self.verbose,
        )
        return zipper.run()

    def step_3_upload(self):
        return upload_layer_zip_to_s3(
            s3_client=self.s3_client,
            path_pyproject_toml=self.path_pyproject_toml,
            s3dir_lambda=self.s3dir_lambda,
            layer_build_tool=self.layer_build_tool,
            verbose=self.verbose,
            printer=self.printer,
        )

    def step_4_publish(self):
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
