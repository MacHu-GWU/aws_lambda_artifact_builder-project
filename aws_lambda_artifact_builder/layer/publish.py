# -*- coding: utf-8 -*-

import typing as T
import dataclasses
from pathlib import Path
from functools import cached_property

from func_args.api import BaseFrozenModel, REQ

from ..typehint import T_PRINTER
from ..constants import LayerBuildToolEnum
from ..imports import S3Path, simple_aws_lambda

from .common import LayerPathLayout, LayerS3Layout


if T.TYPE_CHECKING:  # pragma: no cover
    from mypy_boto3_s3 import S3Client
    from mypy_boto3_lambda import LambdaClient


@dataclasses.dataclass(frozen=True)
class LambdaLayerVersionPublisher(BaseFrozenModel):
    path_pyproject_toml: Path = dataclasses.field(default=REQ)
    s3dir_lambda: "S3Path" = dataclasses.field(default=REQ)
    layer_name: str = dataclasses.field(default=REQ)
    layer_build_tool: LayerBuildToolEnum = dataclasses.field(default=REQ)
    s3_client: "S3Client" = dataclasses.field(default=REQ)
    lambda_client: "LambdaClient" = dataclasses.field(default=REQ)
    printer: T_PRINTER = dataclasses.field(default=print)

    @cached_property
    def path_layout(self) -> LayerPathLayout:
        return LayerPathLayout(
            path_pyproject_toml=self.path_pyproject_toml,
        )

    @cached_property
    def s3_layout(self) -> LayerS3Layout:
        return LayerS3Layout(
            s3dir_lambda=self.s3dir_lambda,
        )

    @cached_property
    def latest_layer_version(self) -> T.Union["simple_aws_lambda.LayerVersion", None]:
        return simple_aws_lambda.get_latest_layer_version(
            lambda_client=self.lambda_client,
            layer_name=self.layer_name,
        )

    @cached_property
    def path_manifest(self) -> Path:
        """
        Get the dependency manifest file path.
        """
        return self.path_layout.get_path_manifest(tool=self.layer_build_tool)

    def get_versioned_manifest(self, version: int) -> "S3Path":
        """
        Get the S3 path of the dependency manifest file for a specific layer version.
        """
        s3dir = self.s3_layout.get_s3dir_layer_version(layer_version=version)
        s3path = s3dir.joinpath(self.path_manifest.name)
        return s3path

    def has_dependency_manifest_changed(self) -> bool:
        """
        Detect if the local dependency manifest has changed from the last published layer.
        
        This method compares the current local dependency manifest (source of truth)
        against the manifest stored with the latest published layer version. If they
        are different, it indicates that dependencies have been updated and a new
        layer version should be published.
        
        **Manifest Comparison Process:**
        
        1. **Retrieve Latest Version**: Get the most recent published layer version
        2. **Locate Stored Manifest**: Find the manifest file stored with that version
        3. **Content Comparison**: Compare local manifest content with stored version
        4. **Change Detection**: Return True if contents differ (change detected)
        
        **Deterministic Requirement:**
        
        The comparison assumes that dependency manifests are deterministic and
        reproducible. This means the manifest should contain exact versions and
        hashes, not loose version constraints.
        
        **Good (Deterministic):**
        
        .. code-block:: text
        
            atomicwrites==1.4.1 ; python_version >= "3.9.dev0" and python_version < "3.10.dev0" \
            --hash=sha256:81b2c9071a49367a7f770170e5eec8cb66567cfbbc8c73d20ce5ca4a8d71cf11
        
        **Bad (Non-deterministic):**
        
        .. code-block:: text
        
            atomicwrites  # Version not pinned
        
        **Return Logic:**
        
        - **True**: Dependencies have changed, new layer version needed
        - **False**: Dependencies unchanged, can skip layer publication
        - **True**: No previous layer exists (first publication)
        - **True**: Previous manifest file not found (missing backup)
        
        :return: True if local manifest differs from latest published version,
                False if they are identical (no changes detected)
        """
        # Check if any layer version has been published previously
        # If no layer exists, we need to publish (dependencies have "changed" from nothing)
        latest_layer_version = self.latest_layer_version
        if latest_layer_version is None:
            return True  # No previous version exists, treat as changed

        # Get local manifest file and construct S3 path for the stored version
        path_manifest = self.path_manifest
        s3path_manifest = self.get_versioned_manifest(
            version=latest_layer_version.version
        )

        # If the stored manifest file doesn't exist, treat as changed
        # This handles cases where the backup wasn't created or was deleted
        if s3path_manifest.exists(bsm=self.s3_client) is False:
            return True  # No stored manifest found, treat as changed

        # Compare local manifest content with stored version
        # Read both files as text and perform exact content comparison
        local_manifest_content = path_manifest.read_text()
        stored_manifest_content = s3path_manifest.read_text(bsm=self.s3_client)

        # Return True if contents differ (change detected), False if identical
        return local_manifest_content != stored_manifest_content

    def publish_layer_version(
        self,
        publish_layer_version_kwargs: dict[str, T.Any] | None = None,
    ) -> tuple[int, str]:
        """
        Publish a new Lambda layer version using the zip file stored in S3.
        """
        if publish_layer_version_kwargs is None:
            publish_layer_version_kwargs = {}
        s3path = self.s3_layout.s3path_temp_layer_zip
        response = self.lambda_client.publish_layer_version(
            LayerName=self.layer_name,
            Content={
                "S3Bucket": s3path.bucket,
                "S3Key": s3path.key,
            },
            **publish_layer_version_kwargs,
        )
        layer_version_arn = response["LayerVersionArn"]
        layer_version = int(layer_version_arn.split(":")[-1])
        return layer_version, layer_version_arn

    def upload_dependency_manifest(
        self,
        version: int,
    ) -> "S3Path":
        """

        .. important::

            We have to use put_object() instead of upload_file() to ensure that
            the eTag is the MD5 hash of the file content.
        """
        path = self.path_manifest
        s3path_manifest = self.get_versioned_manifest(version=version)
        s3path_manifest.write_bytes(
            path.read_bytes(),
            content_type="text/plain",
            bsm=self.s3_client,
        )
        return s3path_manifest


@dataclasses.dataclass(frozen=True)
class LayerDeployment(BaseFrozenModel):
    layer_name: str = dataclasses.field(default=REQ)
    layer_version: int = dataclasses.field(default=REQ)
    layer_version_arn: str = dataclasses.field(default=REQ)
    s3path_manifest: "S3Path" = dataclasses.field(default=REQ)


def publish_layer_version(
    s3_client: "S3Client",
    lambda_client: "LambdaClient",
    path_pyproject_toml: Path,
    s3dir_lambda: "S3Path",
    layer_build_tool: LayerBuildToolEnum,
    layer_name: str,
    publish_layer_version_kwargs: dict[str, T.Any] | None = None,
    verbose: bool = True,
    printer: T_PRINTER = print,
) -> LayerDeployment | None:
    printer("--- Publish Lambda Layer Version ---")
    publisher = LambdaLayerVersionPublisher(
        path_pyproject_toml=path_pyproject_toml,
        s3dir_lambda=s3dir_lambda,
        layer_name=layer_name,
        layer_build_tool=layer_build_tool,
        s3_client=s3_client,
        lambda_client=lambda_client,
        printer=printer,
    )

    flag = publisher.has_dependency_manifest_changed()
    if flag is False:
        if verbose:
            printer(f"dependency not changed, do nothing")
        return None
    layer_version, layer_version_arn = publisher.publish_layer_version(
        publish_layer_version_kwargs=publish_layer_version_kwargs,
    )
    if verbose:
        printer(f"{layer_version = }")
        printer(f"{layer_version_arn = }")
    s3path_manifest = publisher.upload_dependency_manifest(
        version=layer_version,
    )
    if verbose:
        printer(f"{s3path_manifest.uri = }")
        printer(f"{s3path_manifest.console_url = }")
    layer_deployment = LayerDeployment(
        layer_name=layer_name,
        layer_version=layer_version,
        layer_version_arn=layer_version_arn,
        s3path_manifest=s3path_manifest,
    )
    return layer_deployment
