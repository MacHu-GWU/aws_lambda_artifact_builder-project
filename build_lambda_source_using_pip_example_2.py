# -*- coding: utf-8 -*-

"""
All-in-one Lambda source artifacts builder example.

This script demonstrates the simplified approach using the `build_package_upload_source_artifacts`
function that combines all three steps from example_1.py into a single function call:

1. Build source artifacts using pip from pyproject.toml
2. Create a compressed zip file of the built artifacts  
3. Upload the zip to S3 with proper versioning and metadata

**Key Differences from Example 1:**
- Uses single function instead of three separate function calls
- Automatically extracts version from pyproject.toml (assumes semantic versioning)
- Assumes standardized folder structure for Lambda build directories
- Less control over individual steps but simpler to use

**Requirements:**
- Must use pyproject.toml (not setup.py)
- Must have semantic version defined in pyproject.toml under [project].version
- Assumes conventional build folder structure: build/lambda/source/build/
"""

from aws_lambda_artifact_builder.source import build_package_upload_source_artifacts

from pathlib import Path
from s3pathlib import S3Path
from boto_session_manager import BotoSesManager

# Define project paths and AWS configuration
dir_here = Path(__file__).absolute().parent  # Current script directory
dir_project_root = dir_here  # Project root directory (contains pyproject.toml)

# Initialize AWS session using boto session manager
bsm = BotoSesManager(profile_name="bmt_app_dev_us_east_1")

# Construct S3 bucket name following naming convention
bucket = f"{bsm.aws_account_alias}-{bsm.aws_region}-artifacts"

# Define S3 directory structure for Lambda artifacts
s3dir_lambda = S3Path(f"s3://{bucket}/projects/aws_lambda_artifact_builder/lambda/")

# All-in-one function: Build → Package → Upload
# This function automatically:
# 1. Installs package from pyproject.toml using pip (no dependencies)
# 2. Creates compressed zip archive with maximum compression
# 3. Extracts version from pyproject.toml [project].version
# 4. Uploads to S3 with SHA256 metadata and versioning
result = build_package_upload_source_artifacts(
    s3_client=bsm.s3_client,
    dir_project_root=dir_project_root,  # Directory containing pyproject.toml
    s3dir_lambda=s3dir_lambda,  # Base S3 directory for Lambda artifacts
    verbose=True,  # Show detailed progress for all steps
    skip_prompt=True,  # Automatically clean existing build directory
)

print("\n✅ Lambda source artifacts successfully built and uploaded (all-in-one)!")
print(f"🔐 SHA256: {result.source_sha256}")
print(f"📍 S3 Location: {result.s3path_source_zip.uri}")
print(f"🌐 AWS Console: {result.s3path_source_zip.console_url}")
print(f"📂 Build assumes structure: {dir_project_root}/build/lambda/source/build/")
