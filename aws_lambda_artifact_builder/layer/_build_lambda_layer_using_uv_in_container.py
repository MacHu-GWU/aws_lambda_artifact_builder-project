# -*- coding: utf-8 -*-

"""
Container-based Lambda layer build script for uv dependency management.

This script follows the same container orchestration pattern as the pip variant.
For detailed documentation on the container build architecture, execution flow,
and integration with the builder classes, see:

**Execution Flow**

1. Install ``uv`` cli inside the container
2. Install ``aws_lambda_artifact_builder`` library inside the container
3. Use the ``Builder`` class to execute the build logic.

**EXECUTION SAFETY**

THIS SCRIPT HAS TO BE EXECUTED IN THE CONTAINER, NOT ON THE HOST MACHINE.

The script validates its execution environment by checking that it's running from
``/var/task``, which is where the Docker container mounts the host project directory.
This prevents accidental execution on the host system where paths and environment
would be incorrect.
"""

import sys
import subprocess
from pathlib import Path
from datetime import datetime

def main():
    # --------------------------------------------------------------------------
    # 1. Verify container execution environment
    # --------------------------------------------------------------------------
    # The Docker container mounts the host project root to /var/task, so this script
    # must be executing from that exact location to ensure proper path resolution
    print("--- Verify the current runtime ...")
    dir_here = Path(__file__).absolute().parent
    print(f"Current directory is {dir_here}")
    if str(dir_here) != "/var/task":
        raise EnvironmentError(
            "This script has to be executed in the container, not in the host machine"
        )
    else:
        print("Current directory is /var/task, we are in the container OK.")

    # --------------------------------------------------------------------------
    # 2. Install uv within the container
    # --------------------------------------------------------------------------
    print("--- install uv ...")
    args = "curl -LsSf https://astral.sh/uv/install.sh | sh"
    st = datetime.now()
    subprocess.run(args, shell=True, check=True)
    elapsed = (datetime.now() - st).total_seconds()
    print(f"install uv elapsed: {elapsed:.2f} seconds")

    # --------------------------------------------------------------------------
    # 3. Install aws_lambda_artifact_builder within the container
    # --------------------------------------------------------------------------
    # Locate pip executable within the container's Python environment
    # The container uses the same Python version as the target Lambda runtime
    dir_bin = Path(sys.executable).parent
    path_bin_pip = dir_bin / "pip"
    path_bin_uv = Path("/root/.local/bin/uv")

    print("--- Pip install aws_lambda_artifact_builder ...")
    st = datetime.now()

    # --- Dev code ---
    # TODO comment this out in production
    # This code block is used to install aws_lambda_artifact_builder
    # during local deployment and testing, we use this command to simulate
    # "pip install aws_lambda_artifact_builder"
    # path_req = dir_here / "requirements-aws-lambda-artifact-builder.txt"
    # args = [f"{path_bin_pip}", "install", "-r", f"{path_req}"]
    # subprocess.run(args, check=True)
    # --- End dev code ---
    # --- Production code ---
    # TODO uncomment this in production
    args = [f"{path_bin_pip}", "install", "aws_lambda_artifact_builder>=0.1.3,<1.0.0"]
    subprocess.run(args, check=True)
    # --- End production code ---

    elapsed = (datetime.now() - st).total_seconds()
    print(f"pip install aws_lambda_artifact_builder elapsed: {elapsed:.2f} seconds")

    # --------------------------------------------------------------------------
    # 4. Use the local builder logic inside the container
    # --------------------------------------------------------------------------
    # Import the local builder functions that contain the actual poetry installation logic
    # These are the same functions used for local builds, ensuring consistency between
    # local and container-based builds
    from aws_lambda_artifact_builder.api import (
        Credentials,
        UVBasedLambdaLayerLocalBuilder,
    )

    # This path has to match the path defined in
    # :meth:`aws_lambda_artifact_builder.layer.common.LayerPathLayout.path_private_repository_credentials_in_container`
    path_credentials = dir_here / "build" / "lambda" / "private-repository-credentials.json"

    if path_credentials.exists():
        # Deserialize credentials using the same Credentials class used on the host
        # This ensures authentication works identically in both environments
        credentials = Credentials.load(path=path_credentials)
        print(f"Loaded credentials for private repository: {credentials.index_name}")
    else:
        # No private repository access needed - use public PyPI only
        credentials = None
        print("No private repository credentials found, using public PyPI only")

    # Execute the same local builder logic that would run on the host machine
    # The key difference is that this runs inside a Linux container that exactly matches
    # the AWS Lambda runtime environment, ensuring binary compatibility

    # command execution workflow
    print("--- Starting uv-based layer build inside container ...")
    builder = UVBasedLambdaLayerLocalBuilder(
        path_bin_uv=path_bin_uv,
        path_pyproject_toml=dir_here / "pyproject.toml",
        credentials=credentials,
        skip_prompt=True,
    )
    builder.run()
    print("Container-based layer build completed successfully!")

if __name__ == "__main__":
    main()
