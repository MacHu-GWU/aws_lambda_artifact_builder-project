# -*- coding: utf-8 -*-

"""
Container-based Lambda layer build script for pip dependency management.

This script is designed to execute inside AWS SAM build containers as part of the
:class:`~aws_lambda_artifact_builder.layer.pip_builder.PipBasedLambdaLayerContainerBuilder` workflow.
It bridges the gap between host system and container environment by replicating local build logic
inside a Docker container that matches AWS Lambda's exact runtime environment.

**Execution Flow**

1. Install ``aws_lambda_artifact_builder`` library inside the container
2. Use the ``Builder`` class to execute the build logic.

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


# ------------------------------------------------------------------------------
# 1. Verify container execution environment
# ------------------------------------------------------------------------------
def main():
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
    # 2. Install aws_lambda_artifact_builder within the container
    # --------------------------------------------------------------------------
    # Locate pip executable within the container's Python environment
    # The container uses the same Python version as the target Lambda runtime
    dir_bin = Path(sys.executable).parent
    path_bin_pip = dir_bin / "pip"

    # This ensures the local builder functions are available inside the container environment
    # Note: In production, this would install from PyPI; in development, uses local requirements
    print("--- Pip install aws_lambda_artifact_builder ...")
    st = datetime.now()

    # --- Dev code ---
    # TODO comment this out in production
    # This code block is used to install aws_lambda_artifact_builder
    # during local deployment and testing, we use this command to simulate
    # "pip install aws_lambda_artifact_builder"
    path_req = dir_here / "requirements-aws-lambda-artifact-builder.txt"
    args = [f"{path_bin_pip}", "install", "-r", f"{path_req}"]
    subprocess.run(args, check=True)
    # --- End dev code ---
    # --- Production code ---
    # TODO uncomment this in production
    # args = [f"{path_bin_pip}", "install", "aws_lambda_artifact_builder>=0.1.1,<1.0.0"]
    # subprocess.run(args, check=True)
    # --- End production code ---

    elapsed = (datetime.now() - st).total_seconds()
    print(f"pip install aws_lambda_artifact_builder elapsed: {elapsed:.2f} seconds")

    # --------------------------------------------------------------------------
    # 3. Use the local builder logic inside the container
    # --------------------------------------------------------------------------
    # Import the local builder functions that contain the actual pip installation logic
    # These are the same functions used for local builds, ensuring consistency between
    # local and container-based builds
    from aws_lambda_artifact_builder.api import (
        Credentials,
        PipBasedLambdaLayerLocalBuilder,
    )

    # Load private repository credentials if available
    # The container builder serializes credentials to a JSON file and mounts it into the container
    # This path must match the path defined in
    # :meth:`~aws_lambda_artifact_builder.layer.common.LayerPathLayout.path_private_repository_credentials_in_container`
    path_credentials = (
        dir_here / "build" / "lambda" / "private-repository-credentials.json"
    )

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
    print("--- Starting pip-based layer build inside container ...")
    builder = PipBasedLambdaLayerLocalBuilder(
        path_bin_pip=path_bin_pip,  # Container's pip executable
        path_pyproject_toml=dir_here
        / "pyproject.toml",  # Mounted project configuration
        credentials=credentials,  # Loaded from mounted credentials file
        skip_prompt=True,  # Automatic execution without user interaction
    )
    builder.run()
    print("--- Container-based layer build completed successfully!")

    # The resulting layer.zip file will be available on the host machine at:
    # {project_root}/build/lambda/layer/layer.zip
    # because the container's /var/task directory is mounted from the host project root


if __name__ == "__main__":
    main()
