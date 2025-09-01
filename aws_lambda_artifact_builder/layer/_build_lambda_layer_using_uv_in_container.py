# -*- coding: utf-8 -*-

"""
Build lambda layer and create a zip file.

**IMPORTANT**

THIS SHELL SCRIPT HAS TO BE EXECUTED IN THE CONTAINER, NOT IN THE HOST MACHINE.
"""

import sys
import subprocess
from pathlib import Path
from datetime import datetime

print("--- Verify the current runtime ...")
dir_here = Path(__file__).absolute().parent
print(f"Current directory is {dir_here}")
if str(dir_here) != "/var/task":
    raise EnvironmentError(
        "This script has to be executed in the container, not in the host machine"
    )
else:
    print("Current directory is /var/task, we are in the container OK.")

dir_bin = Path(sys.executable).parent
path_bin_pip = dir_bin / "pip"
path_bin_uv = Path("/root/.local/bin/uv")

print("--- install uv ...")
args = "curl -LsSf https://astral.sh/uv/install.sh | sh"
st = datetime.now()
subprocess.run(args, shell=True, check=True)
elapsed = (datetime.now() - st).total_seconds()
print(f"install uv elapsed: {elapsed:.2f} seconds")

print("--- Pip install aws_lambda_artifact_builder ...")
st = datetime.now()

# --- Dev code ---
# This code block is used to install aws_lambda_artifact_builder
# during local deployment and testing, we use this command to simulate
# "pip install aws_lambda_artifact_builder"
path_req = dir_here / "requirements-aws-lambda-artifact-builder.txt"
args = [f"{path_bin_pip}", "install", "-r", f"{path_req}"]
subprocess.run(args, check=True)
# --- End dev code ---
# --- Production code ---
# args = [f"{path_bin_pip}", "install", "aws_lambda_artifact_builder>=0.1.1,<1.0.0"]
# subprocess.run(args, check=True)
# --- End production code ---

elapsed = (datetime.now() - st).total_seconds()
print(f"pip install aws_lambda_artifact_builder elapsed: {elapsed:.2f} seconds")

from aws_lambda_artifact_builder.api import (
    Credentials,
    build_layer_artifacts_using_uv_in_local,
)

# This path has to match the path defined in
# :meth:`aws_lambda_artifact_builder.layer.common.LayerPathLayout.path_private_repository_credentials_in_container`
path_credentials = dir_here / "build" / "lambda" / "private-repository-credentials.json"

if path_credentials.exists():
    credentials = Credentials.load(path=path_credentials)
else:
    credentials = None

build_layer_artifacts_using_uv_in_local(
    path_bin_uv=path_bin_uv,
    path_pyproject_toml=dir_here / "pyproject.toml",
    credentials=credentials,
    skip_prompt=True,
)
