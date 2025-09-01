# -*- coding: utf-8 -*-

"""
Container-based Lambda layer build script for pip dependency management.

**Container Orchestration Overview**

This script is designed to execute inside AWS SAM build containers as part of the
:class:`~aws_lambda_artifact_builder.layer.pip_builder.PipBasedLambdaLayerContainerBuilder` workflow.
It bridges the gap between host system and container environment by replicating local build logic
inside a Docker container that matches AWS Lambda's exact runtime environment.

**Execution Flow**

1. **Script Preparation**: The container builder copies this script via
   :meth:`~aws_lambda_artifact_builder.layer.pip_builder.PipBasedLambdaLayerContainerBuilder.step_01_copy_build_script`
2. **Credential Setup**: Authentication tokens are serialized and mounted via
   :meth:`~aws_lambda_artifact_builder.layer.common.BasedLambdaLayerContainerBuilder.step_02_setup_private_repository_credential`
3. **Container Execution**: Docker runs this script inside the container via
   :meth:`~aws_lambda_artifact_builder.layer.common.BasedLambdaLayerContainerBuilder.step_03_docker_run`
4. **Local Build Execution**: This script calls
   :func:`~aws_lambda_artifact_builder.layer.pip_builder.build_layer_artifacts_using_pip_in_local`
   inside the container environment

**Container Environment**

- **Working Directory**: ``/var/task`` (mounted from host project root)
- **Python Environment**: Matches AWS Lambda runtime exactly
- **Authentication**: Credentials loaded from mounted JSON file
- **Isolation**: No interference with host development environment

**Architecture Benefits**

This approach allows the pip-specific build logic to remain in the local builder classes
where it's easily testable and debuggable, while the container orchestration handles
Docker lifecycle management without duplicating business logic.

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

# Verify container execution environment
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

# Locate pip executable within the container's Python environment
# The container uses the same Python version as the target Lambda runtime
dir_bin = Path(sys.executable).parent
path_bin_pip = dir_bin / "pip"

# Install aws_lambda_artifact_builder within the container
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

# Import the local builder functions that contain the actual pip installation logic
# These are the same functions used for local builds, ensuring consistency between
# local and container-based builds
from aws_lambda_artifact_builder.api import (
    Credentials,
    build_layer_artifacts_using_pip_in_local,
)

# Load private repository credentials if available
# The container builder serializes credentials to a JSON file and mounts it into the container
# This path must match the path defined in
# :meth:`~aws_lambda_artifact_builder.layer.common.LayerPathLayout.path_private_repository_credentials_in_container`
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
#
# This delegates to :func:`~aws_lambda_artifact_builder.layer.pip_builder.build_layer_artifacts_using_pip_in_local`
# which orchestrates the :class:`~aws_lambda_artifact_builder.layer.pip_builder.PipBasedLambdaLayerLocalBuilder`
# command execution workflow
print("--- Starting pip-based layer build inside container ...")
build_layer_artifacts_using_pip_in_local(
    path_bin_pip=path_bin_pip,  # Container's pip executable
    path_pyproject_toml=dir_here / "pyproject.toml",  # Mounted project configuration
    credentials=credentials,  # Loaded from mounted credentials file
    skip_prompt=True,  # Automatic execution without user interaction
)
print("--- Container-based layer build completed successfully!")

# The resulting layer.zip file will be available on the host machine at:
# {project_root}/build/lambda/layer/layer.zip
# because the container's /var/task directory is mounted from the host project root
