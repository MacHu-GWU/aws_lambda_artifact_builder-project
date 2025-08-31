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
args = [f"{path_bin_pip}", "install", "soft-deps>=0.1.1,<1.0.0"]
subprocess.run(args, check=True)
args = [f"{path_bin_pip}", "install", "func_args>=1.0.1,<2.0.0"]
subprocess.run(args, check=True)
# args = [f"{path_bin_pip}", "install", "-q", "-r", "requirements.txt"]
# subprocess.run(args, check=True)
elapsed = (datetime.now() - st).total_seconds()
print(f"pip install aws_lambda_artifact_builder elapsed: {elapsed:.2f} seconds")

from aws_lambda_artifact_builder.layer.pip_builder import (
    build_layer_artifacts_using_pip_in_local,
)

build_layer_artifacts_using_pip_in_local(
    path_bin_pip=path_bin_pip,
    path_pyproject_toml=dir_here / "pyproject.toml",
    skip_prompt=True,
)
# dir_root = dir_here
#
# path_pypi_index_url = dir_here / "pypi_index_url.txt"
# if path_pypi_index_url.exists():
#     pypi_index_url = path_pypi_index_url.read_text().strip()
#     extra_args = ["--index-url", pypi_index_url]
# else:
#     extra_args = None
# layer_sha256 = aws_lambda_layer.build_layer_artifacts(
#     path_requirements=dir_root / "requirements.txt",
#     dir_build=dir_root / "build" / "lambda",
#     bin_pip="/var/lang/bin/pip",
#     quiet=False,
#     extra_args=extra_args,
# )
