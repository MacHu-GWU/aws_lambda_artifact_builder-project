# -*- coding: utf-8 -*-

from pathlib import Path
from settings import py_ver_major, py_ver_minor
from aws_lambda_artifact_builder.layer.package import (
    move_to_dir_python,
    create_layer_zip_file,
)

# Current project directory
dir_here = Path(__file__).absolute().parent
dir_site_packages = (
    dir_here
    / "build"
    / "lambda"
    / "layer"
    / "repo"
    / ".venv"
    / "lib"
    / f"python{py_ver_major}.{py_ver_minor}"
    / "site-packages"
)
path_pyproject_toml = dir_here.joinpath("pyproject.toml")
move_to_dir_python(
    dir_site_packages=dir_site_packages,
    path_pyproject_toml=path_pyproject_toml,
)
create_layer_zip_file(
    path_pyproject_toml=path_pyproject_toml,
)
