# -*- coding: utf-8 -*-

"""
Example script demonstrating how to build, package, and upload Lambda source artifacts.

This script shows the complete workflow:

1. Build source artifacts using pip from the current project
2. Create a compressed zip file of the built artifacts
3. Upload the zip to S3 with proper versioning and metadata
"""

from aws_lambda_artifact_builder.api import (
    build_source_artifacts_using_pip,
    create_source_zip,
    upload_source_artifacts,
)

from pathlib import Path
from s3pathlib import S3Path
from boto_session_manager import BotoSesManager

# ------------------------------------------------------------------------------
# Step 1: Build source artifacts using pip
# ------------------------------------------------------------------------------
# Define paths for the build process
dir_here = Path(__file__).absolute().parent  # Current project directory
path_bin_pip = dir_here / ".venv" / "bin" / "pip"  # Virtual environment pip executable
path_setup_py_or_pyproject_toml = (
    dir_here / "pyproject.toml"
)  # Project configuration file
dir_lambda_source_build = (
    dir_here / "build" / "lambda" / "source" / "build"
)  # Target build directory

# This installs the current package into the build directory without dependencies
build_source_artifacts_using_pip(
    path_bin_pip=path_bin_pip,
    path_setup_py_or_pyproject_toml=path_setup_py_or_pyproject_toml,
    dir_lambda_source_build=dir_lambda_source_build,
    verbose=True,  # Show detailed output
    skip_prompt=True,  # Automatically clean existing build directory
)

# ------------------------------------------------------------------------------
# Step 2: Create compressed zip archive of the built source
# ------------------------------------------------------------------------------
path_source_zip = (
    dir_here / "build" / "lambda" / "source" / "source.zip"
)  # Output zip file path
source_sha256 = create_source_zip(
    dir_lambda_source_build=dir_lambda_source_build,
    path_source_zip=path_source_zip,
    verbose=True,  # Show compression progress
)  # Returns SHA256 hash for integrity verification

# ------------------------------------------------------------------------------
# Step 3: Upload the zip file to S3 with versioning
# ------------------------------------------------------------------------------
# Initialize AWS session using boto session manager
bsm = BotoSesManager(profile_name="bmt_app_dev_us_east_1")

# Construct S3 bucket name following naming convention
bucket = f"{bsm.aws_account_alias}-{bsm.aws_region}-artifacts"

# Define S3 directory structure for Lambda artifacts
s3dir_lambda = S3Path(f"s3://{bucket}/projects/aws_lambda_artifact_builder/lambda/")

# Upload with semantic versioning and metadata
source_version = "0.1.1"
upload_source_artifacts(
    s3_client=bsm.s3_client,
    source_version=source_version,  # Semantic version for this release
    source_sha256=source_sha256,  # Hash from previous step for integrity verification
    path_source_zip=path_source_zip,
    s3dir_lambda=s3dir_lambda,
    verbose=True,  # Show upload progress and S3 URLs
)

print("✅ Lambda source artifacts successfully built and uploaded!")
print(f"📋 Version: 0.1.1")
print(f"🔐 SHA256: {source_sha256}")
print(f"📦 Local Zip File: {path_source_zip}")
print(f"📍 S3 Location: {s3dir_lambda.uri}source/0.1.1/source.zip")
