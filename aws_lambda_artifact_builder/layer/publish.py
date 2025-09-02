# -*- coding: utf-8 -*-

"""
Lambda layer publication implementation - Step 4 of the layer creation workflow.

This module handles the publication phase of AWS Lambda layer deployment, taking
the uploaded layer zip file from S3 and creating versioned Lambda layer resources.
It represents the fourth and final step in the complete layer workflow:

1. **Build**: Install dependencies using pip/Poetry/UV builders
2. **Package**: Structure and compress dependencies into zip file  
3. **Upload**: Deploy zip file to S3 storage
4. **Publish**: Create versioned Lambda layer from S3 artifact (this module)

**Public API Functions:**
    - :func:`publish_layer_version`: Intelligent layer publishing with change detection

**Key Features:**
    - **Change Detection**: Compares dependency manifests to avoid unnecessary publications
    - **Version Management**: Automatically increments layer versions
    - **Manifest Backup**: Stores dependency manifests for reproducibility
    - **S3 Integration**: Uses existing S3 artifacts for layer creation

**Publication Process:**
    The module implements smart publishing that only creates new layer versions when
    dependencies have actually changed, determined by comparing local dependency
    manifests against stored versions from previous publications.
"""

import typing as T
import dataclasses
from pathlib import Path
from functools import cached_property

from func_args.api import BaseFrozenModel, REQ

from ..typehint import T_PRINTER
from ..constants import S3MetadataKeyEnum, LayerBuildToolEnum
from ..imports import S3Path, simple_aws_lambda

from .common import LayerManifestManager


if T.TYPE_CHECKING:  # pragma: no cover
    from mypy_boto3_s3 import S3Client
    from mypy_boto3_lambda import LambdaClient


@dataclasses.dataclass(frozen=True)
class LambdaLayerVersionPublisher(LayerManifestManager):
    """
    Command class for intelligent Lambda layer version publishing (Internal API).

    This class implements the layer publication workflow with dependency change detection,
    ensuring new layer versions are only created when dependencies have actually changed.
    It follows the Command Pattern established by other builder classes.

    **Not for direct use**: This is an internal command class. Use the public function
    :func:`publish_layer_version` instead.

    **Key Responsibilities:**

    - **Change Detection**: Compare local manifests with previously published versions
    - **Layer Publication**: Create new Lambda layer versions from S3 artifacts
    - **Manifest Storage**: Backup dependency manifests for future comparisons
    - **Version Management**: Handle layer version incrementation automatically

    **Publication Logic:**

    The publisher only creates new layer versions when the dependency manifest has
    changed since the last publication. This prevents unnecessary version proliferation
    and ensures layer versions represent meaningful dependency updates.
    """

    layer_name: str = dataclasses.field(default=REQ)
    lambda_client: "LambdaClient" = dataclasses.field(default=REQ)

    def is_layer_zip_exists(self) -> bool:
        """
        Check if the layer zip file exists in S3 temporary storage.
        
        Verifies that the layer.zip file was successfully uploaded to S3 during
        the upload phase and is available for Lambda layer creation. This is a
        prerequisite validation before attempting to publish a new layer version.
        
        **Common Failure Scenarios:**
        
        - **Upload Step Skipped**: The upload phase was not executed
        - **Upload Failed**: Network issues or S3 permissions prevented successful upload
        - **File Deleted**: The temporary zip file was manually removed from S3
        - **Wrong S3 Path**: Misconfigured S3 directory structure
        
        :return: True if layer.zip exists in S3, False otherwise
        """
        s3path = self.s3_layout.s3path_temp_layer_zip
        return s3path.exists(bsm=self.s3_client)

    def is_layer_zip_consistent(self) -> bool:
        """
        Validate that the uploaded layer.zip matches the current local manifest.
        
        Compares the manifest MD5 hash stored in the S3 layer.zip metadata
        with the MD5 hash of the current local manifest file. This ensures that
        the uploaded layer artifact corresponds to the current dependency state
        before creating a new layer version.
        
        **Consistency Issues That Can Occur:**
        
        - **Manifest Modified**: Local manifest file was changed after upload
        - **Wrong Upload**: A different project's layer.zip was uploaded
        - **Missing Metadata**: Upload process failed to store manifest MD5
        - **Stale Upload**: Old layer.zip from previous dependency state
        
        **Why This Check Matters:**
        
        Without this validation, you might publish a layer version that doesn't
        match your current dependencies, leading to runtime errors or unexpected
        behavior in Lambda functions that use the layer.
        
        :return: True if uploaded layer.zip matches current manifest, False otherwise
        """
        s3path = self.s3_layout.s3path_temp_layer_zip
        s3path.head_object(bsm=self.s3_client)
        manifest_md5 = s3path.metadata.get(
            S3MetadataKeyEnum.manifest_md5.value, "__invalid__"
        )
        return manifest_md5 == self.manifest_md5

    @cached_property
    def latest_layer_version(self) -> T.Union["simple_aws_lambda.LayerVersion", None]:
        return simple_aws_lambda.get_latest_layer_version(
            lambda_client=self.lambda_client,
            layer_name=self.layer_name,
        )

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

        This method creates a new versioned Lambda layer by referencing the layer zip
        file that was previously uploaded to S3 during the upload phase. AWS Lambda
        automatically assigns the next sequential version number.

        **Layer Creation Process:**

        1. **S3 Reference**: Points Lambda service to the uploaded zip file in S3
        2. **Version Creation**: Lambda automatically increments version number
        3. **ARN Generation**: Returns the full ARN of the newly created layer version

        :param publish_layer_version_kwargs: Optional additional arguments to pass to
            the Lambda publish_layer_version API call (e.g., Description, CompatibleRuntimes)
        :return: Tuple of (layer_version_number, layer_version_arn)
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
        Upload the dependency manifest file to S3 for the specified layer version.

        This method stores the local dependency manifest (source of truth) alongside
        the published layer version for future change detection and reproducibility.
        The stored manifest enables the system to determine if dependencies have
        changed in subsequent publication attempts.

        **Storage Strategy:**

        - **Version-Specific**: Each layer version gets its own manifest backup
        - **Content Integrity**: Uses write_bytes() to ensure proper eTag generation
        - **Plain Text**: Stored as text/plain for easy inspection and comparison

        .. important::

            Uses write_bytes() instead of upload_file() to ensure that the eTag
            is the MD5 hash of the file content, which is important for content
            integrity verification.

        :param version: The layer version number to associate the manifest with
        :return: S3Path where the manifest was stored
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
    """
    Data class representing a completed layer deployment (Public API).

    This immutable data class encapsulates all the key information about a
    successfully published Lambda layer version, providing a complete record
    of the deployment for downstream operations.

    **Usage:**

    The LayerDeployment is returned by :func:`publish_layer_version` when a new
    layer version is successfully created. It contains all the identifiers and
    references needed to work with the published layer.

    **Attributes:**

    - **layer_name**: The name of the Lambda layer
    - **layer_version**: The version number assigned by AWS Lambda
    - **layer_version_arn**: The full ARN of the published layer version
    - **s3path_manifest**: S3 location of the stored dependency manifest
    """

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
    """
    Intelligently publish a new Lambda layer version with dependency change detection (Public API).

    This function implements smart layer publishing that only creates new layer versions
    when dependencies have actually changed since the last publication. It compares the
    current dependency manifest against the stored version from the latest published layer
    to determine if a new version is needed.

    **Smart Publication Logic:**

    1. **Change Detection**: Compare local manifest with latest published version
    2. **Conditional Publishing**: Only publish if dependencies have changed
    3. **Version Creation**: Use existing S3 zip file to create Lambda layer version
    4. **Manifest Backup**: Store dependency manifest for future comparisons

    **Publication Process:**

    - **Dependencies Changed**: Creates new layer version and returns LayerDeployment
    - **No Changes Detected**: Skips publication and returns None
    - **First Publication**: Always publishes (no previous version to compare)

    **Requirements:**

    - Layer zip file must already exist in S3 (from upload step)
    - Local dependency manifest must be available for comparison
    - AWS credentials must have Lambda layer publication permissions

    :param s3_client: Configured boto3 S3 client with appropriate permissions
    :param lambda_client: Configured boto3 Lambda client with layer permissions
    :param path_pyproject_toml: Path to pyproject.toml file (determines project root)
    :param s3dir_lambda: S3 directory where Lambda artifacts are stored
    :param layer_build_tool: Build tool used to create dependencies (pip/poetry/uv)
    :param layer_name: Name of the Lambda layer to create/update
    :param publish_layer_version_kwargs: Optional additional arguments for Lambda API
    :param verbose: If True, shows detailed publication progress
    :param printer: Function to handle progress messages, defaults to print

    :return: LayerDeployment object if new version was published, None if skipped
    """
    # Display publication initiation message
    printer("--- Publish Lambda Layer Version ---")
    # Initialize the layer publisher command with all required configuration
    # This sets up the path layouts, S3 structures, and AWS clients needed
    # for the publication workflow
    publisher = LambdaLayerVersionPublisher(
        path_pyproject_toml=path_pyproject_toml,
        s3dir_lambda=s3dir_lambda,
        layer_name=layer_name,
        layer_build_tool=layer_build_tool,
        s3_client=s3_client,
        lambda_client=lambda_client,
        printer=printer,
    )

    # CRITICAL: Validate that layer.zip exists in S3 before attempting publication
    # This prevents "NoSuchKey" errors during Lambda layer creation
    # Common causes: upload step was skipped, S3 upload failed, or file was manually deleted
    if publisher.is_layer_zip_exists() is False:
        s3path = publisher.s3_layout.s3path_temp_layer_zip
        raise FileNotFoundError(
            f"Layer zip file {s3path.uri} does not exist! "
            f"Please run the upload step first to create the layer.zip in S3."
        )
    
    # CRITICAL: Validate that the uploaded layer.zip matches current local manifest
    # This prevents publishing a layer with wrong dependencies that could cause runtime errors
    # Common causes: manifest was modified after upload, wrong layer.zip was uploaded,
    # or upload metadata is missing/corrupted
    if publisher.is_layer_zip_consistent() is False:
        path = publisher.path_manifest
        s3path = publisher.s3_layout.s3path_temp_layer_zip
        raise ValueError(
            f"Layer zip file {s3path.uri} is inconsistent with current manifest {path}! "
            f"The uploaded layer.zip corresponds to a different dependency state. "
            f"Please re-run the upload step to sync the layer.zip with current dependencies."
        )

    # Check if the local dependency manifest has changed since the last publication
    # This is the core intelligence that prevents unnecessary layer version creation
    has_changed = publisher.has_dependency_manifest_changed()
    if not has_changed:
        # Dependencies are identical to the last published version
        # Skip publication to avoid creating redundant layer versions
        if verbose:
            printer("Dependencies unchanged since last publication - skipping")
        return None
    # Dependencies have changed - proceed with publishing new layer version
    # This creates the actual Lambda layer version using the S3 zip file
    layer_version, layer_version_arn = publisher.publish_layer_version(
        publish_layer_version_kwargs=publish_layer_version_kwargs,
    )

    # Display the newly created layer version information
    if verbose:
        printer(f"Successfully published layer version: {layer_version}")
        printer(f"Layer version ARN: {layer_version_arn}")
    # Store the dependency manifest alongside the published layer version
    # This backup enables future change detection for subsequent publications
    s3path_manifest = publisher.upload_dependency_manifest(
        version=layer_version,
    )

    # Display manifest storage information for verification and debugging
    if verbose:
        printer(f"Manifest stored at: {s3path_manifest.uri}")
        printer(f"Console URL: {s3path_manifest.console_url}")
    # Create and return a complete deployment record with all key information
    # This provides downstream processes with everything needed to reference the layer
    layer_deployment = LayerDeployment(
        layer_name=layer_name,
        layer_version=layer_version,
        layer_version_arn=layer_version_arn,
        s3path_manifest=s3path_manifest,
    )
    return layer_deployment
