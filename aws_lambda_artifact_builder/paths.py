# -*- coding: utf-8 -*-

from pathlib import Path

dir_here = Path(__file__).absolute().parent
dir_package = dir_here
PACKAGE_NAME = dir_package.name

dir_project_root = dir_package.parent

# ------------------------------------------------------------------------------
# Virtual Environment Related
# ------------------------------------------------------------------------------
dir_venv = dir_project_root / ".venv"
dir_venv_bin = dir_venv / "bin"

# virtualenv executable paths
bin_pytest = dir_venv_bin / "pytest"

# ------------------------------------------------------------------------------
# Test Related
# ------------------------------------------------------------------------------
dir_htmlcov = dir_project_root / "htmlcov"
path_cov_index_html = dir_htmlcov / "index.html"
dir_unit_test = dir_project_root / "tests"
dir_int_test = dir_project_root / "tests_int"
dir_load_test = dir_project_root / "tests_load"

# ------------------------------------------------------------------------------
# Doc Related
# ------------------------------------------------------------------------------
dir_docs_source = dir_project_root / "docs" / "source"
dir_docs_build_html = dir_project_root / "docs" / "build" / "html"

# ------------------------------------------------------------------------------
# Lambda Related
# ------------------------------------------------------------------------------
_dir_layer = dir_package / "layer"

# The following scripts will be copied to the temporary build directory
# and mount the project root directory to the container,
# so that the script can be executed in the container environment.
_basename = "_build_lambda_layer_using_pip_in_container.py"
path_build_lambda_layer_using_pip_in_container_script = _dir_layer / _basename
"""
The purposely designed Python shell script to build the Lambda layer artifacts
using pip in a container environment.
"""

_basename = "_build_lambda_layer_using_poetry_in_container.py"
path_build_lambda_layer_using_poetry_in_container_script = _dir_layer / _basename
"""
The purposely designed Python shell script to build the Lambda layer artifacts
using poetry in a container environment. 
"""

_basename = "_build_lambda_layer_using_uv_in_container.py"
path_build_lambda_layer_using_uv_in_container_script = _dir_layer / _basename
"""
The purposely designed Python shell script to build the Lambda layer artifacts
using uv in a container environment. 
"""
