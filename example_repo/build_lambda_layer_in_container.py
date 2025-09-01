# -*- coding: utf-8 -*-

"""
Build AWS Lambda layer and create a zip file.

**IMPORTANT**

THIS SHELL SCRIPT HAS TO BE EXECUTED IN THE CONTAINER, NOT IN THE HOST MACHINE.
"""

import sys
import json
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

print("--- Pip install aws_lambda_artifact_builder ...")
st = datetime.now()
path_req = dir_here / "requirements-aws-lambda-artifact-builder.txt"
args = [f"{path_bin_pip}", "install", "-r", f"{path_req}"]
subprocess.run(args, check=True)
# args = [f"{path_bin_pip}", "install", "aws_lambda_artifact_builder>=0.1.1,<1.0.0"]
# subprocess.run(args, check=True)
elapsed = (datetime.now() - st).total_seconds()
print(f"pip install aws_lambda_artifact_builder elapsed: {elapsed:.2f} seconds")

from aws_lambda_artifact_builder.api import (
    Credentials,
    build_layer_artifacts_using_pip_in_local,
)

path_credentials = (
    dir_here
    / "build"
    / "lambda"
    / "layer"
    / "repo"
    / "private-repository-credentials.json"
)

if path_credentials.exists():
    credentials = Credentials.load(path=path_credentials)
else:
    credentials = None

build_layer_artifacts_using_pip_in_local(
    path_bin_pip=path_bin_pip,
    path_pyproject_toml=dir_here / "pyproject.toml",
    credentials=credentials,
    skip_prompt=True,
)
