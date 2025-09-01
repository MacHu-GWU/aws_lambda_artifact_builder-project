# -*- coding: utf-8 -*-

"""
Lambda layer packaging implementation - Step 2 of the layer creation workflow.

This module handles the packaging phase of AWS Lambda layer creation, transforming
the built dependencies into a properly structured zip file ready for deployment.
"""

from pathlib import Path
import glob
import shutil
import subprocess

from .common import LayerPathLayout
from ..vendor.better_pathlib import temp_cwd


def move_to_dir_python(
    dir_site_packages: Path,
    path_pyproject_toml: Path,
):
    """
    Restructure installed packages into AWS Lambda layer format.
    
    This function moves packages from a standard Python site-packages directory
    into the AWS Lambda layer's required ``python/`` directory structure. This
    transformation is necessary because different build tools (pip, Poetry, UV)
    install packages to different locations, but Lambda layers must follow a
    standardized directory layout.
    
    **Directory Transformation:**
    
    - **Source**: ``build/lambda/layer/repo/.venv/lib/python3.x/site-packages/``
    - **Target**: ``build/lambda/layer/artifacts/python/``
    
    The function handles the move operation safely by removing any existing
    target directory before moving to prevent conflicts and ensure clean packaging.
    
    :param dir_site_packages: Path to the source site-packages directory from build process
    :param path_pyproject_toml: Path to pyproject.toml file (determines project root and layout)
    
    :raises FileNotFoundError: If the source site-packages directory doesn't exist
    """
    layout = LayerPathLayout(path_pyproject_toml=path_pyproject_toml)
    dir_python = layout.dir_python
    if dir_site_packages.exists():
        # Move the content of dir_site_packages to dir_python
        if dir_site_packages != dir_python:
            if dir_python.exists():
                shutil.rmtree(dir_python)
            shutil.move(dir_site_packages, dir_python)
        # otherwise, dir_site_packages is the same as dir_python, do nothing
    else:
        raise FileNotFoundError(f"dir_site_packages {dir_site_packages} not found")

default_ignore_package_list = [
    "boto3",
    "botocore", 
    "s3transfer",
    "urllib3",
    "setuptools",
    "pip",
    "wheel",
    "twine",
    "_pytest",
    "pytest",
]
"""
Default packages to exclude from Lambda layer zip files.
These packages are commonly excluded because they are either:

- **AWS Runtime Provided**: boto3, botocore, s3transfer, urllib3 are pre-installed in Lambda
- **Build Tools**: setuptools, pip, wheel, twine are not needed at runtime
- **Development Tools**: pytest, _pytest are testing frameworks not needed in production

Excluding these packages reduces layer size and avoids version conflicts with
the Lambda runtime environment. Custom ignore lists can override this default.
"""


def create_layer_zip_file(
    path_pyproject_toml: Path,
    ignore_package_list: list[str] | None = None,
    verbose: bool = True,
):
    """
    Create optimized zip file for AWS Lambda layer deployment (Public API).
    
    This function creates the final deployable artifact by compressing the layer's
    ``python/`` directory into a zip file with selective package exclusions. The
    resulting zip file is ready for upload to S3 and Lambda layer publication.
    
    **Compression and Optimization**
    
    - **Compression Level**: Uses maximum compression (-9) to minimize layer size
    - **Package Exclusions**: Removes AWS runtime-provided and development packages
    - **Directory Structure**: Preserves Lambda-required ``python/`` directory layout
    - **Recursive Packaging**: Includes all subdirectories and maintains file permissions
    
    **Default Exclusions:**
    
    The function automatically excludes common packages that are either provided
    by the AWS Lambda runtime (boto3, botocore) or not needed at runtime (pytest,
    setuptools). This reduces layer size and prevents version conflicts.
    
    **Output Location:**
    
    Creates ``build/lambda/layer/layer.zip`` in the project root, following the
    standard layer artifact naming convention established by the LayerPathLayout.
    
    :param path_pyproject_toml: Path to pyproject.toml file (determines project root and output location)
    :param ignore_package_list: Optional list of additional packages to exclude from zip.
        If None, uses :data:`default_ignore_package_list`. Package names support glob patterns.
    :param verbose: If True, shows detailed zip creation progress; if False, runs silently
    """
    layer_path_layout = LayerPathLayout(
        path_pyproject_toml=path_pyproject_toml,
    )
    if ignore_package_list is None:
        ignore_package_list = list(default_ignore_package_list)

    args = [
        "zip",
        f"{layer_path_layout.path_build_lambda_layer_zip}",
        "-r",
        "-9",
    ]
    if verbose is False:
        args.append("-q")

    # Change to artifacts directory to ensure proper relative path structure in zip
    # The zip file must contain 'python/' as the root directory, not the full path
    # from the host system, so we execute zip from within the artifacts directory
    with temp_cwd(layer_path_layout.dir_artifacts):
        # Add all files and directories from the artifacts directory
        # This typically includes the 'python/' directory containing all packages
        args.extend(glob.glob("*"))
        
        # Apply package exclusions using zip's -x flag for selective filtering
        # Each exclusion pattern targets packages within the python/ directory
        if ignore_package_list:
            args.append("-x")  # Enable exclusion mode
            for package in ignore_package_list:
                # Exclude package directories and all their contents using glob patterns
                args.append(f"python/{package}*")
        # Execute zip command with all configured arguments
        # The resulting layer.zip will be created in the project's build directory
        subprocess.run(args, check=True)
