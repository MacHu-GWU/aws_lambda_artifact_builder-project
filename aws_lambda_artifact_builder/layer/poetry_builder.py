# -*- coding: utf-8 -*-

import typing as T
import shutil
import subprocess
import dataclasses
from pathlib import Path
from functools import cached_property

from func_args.api import REQ
from ..vendor.better_pathlib import temp_cwd

from ..typehint import T_PRINTER
from ..paths import path_build_lambda_layer_using_poetry_in_container_script

from .common import BasedLambdaLayerLocalBuilder, BasedLambdaLayerContainerBuilder


@dataclasses.dataclass(frozen=True)
class PoetryBasedLambdaLayerLocalBuilder(
    BasedLambdaLayerLocalBuilder,
):
    """
    Only build this locally, without Docker container.
    """

    path_bin_poetry: Path = dataclasses.field(default=REQ)
    _tool: str = dataclasses.field(default="poetry")

    def step_01_print_info(self):
        super().step_01_print_info()
        self.printer(f"path_bin_poetry = {self.path_bin_poetry}")

    def step_03_prepare_poetry_stuff(self):
        self.path_layout.copy_pyproject_toml(printer=self.printer)
        self.path_layout.copy_poetry_lock(printer=self.printer)

    def step_04_run_poetry_install(self):
        path_bin_poetry = self.path_bin_poetry
        dir_repo = self.path_layout.dir_repo
        with temp_cwd(dir_repo):
            args = [
                f"{path_bin_poetry}",
                "config",
                "virtualenvs.in-project",
                "true",
            ]
            subprocess.run(args, cwd=dir_repo, check=True)

            args = [
                f"{path_bin_poetry}",
                "install",
                "--no-root",
            ]
            subprocess.run(args, cwd=dir_repo, check=True)


def build_layer_artifacts_using_poetry_in_local(
    path_bin_poetry: Path,
    path_pyproject_toml: Path,
    skip_prompt: bool = False,
    printer: T_PRINTER = print,
):
    """ """
    builder = PoetryBasedLambdaLayerLocalBuilder(
        path_bin_poetry=path_bin_poetry,
        path_pyproject_toml=path_pyproject_toml,
        printer=printer,
    )
    builder.step_01_print_info()
    builder.step_02_setup_build_dir(skip_prompt=skip_prompt)
    builder.step_03_prepare_poetry_stuff()
    builder.step_04_run_poetry_install()


@dataclasses.dataclass(frozen=True)
class PoetryBasedLambdaLayerContainerBuilder(
    BasedLambdaLayerContainerBuilder,
):
    pass


def build_layer_artifacts_using_poetry_in_container(
    path_pyproject_toml: Path,
    py_ver_major: int,
    py_ver_minor: int,
    is_arm: bool,
    printer: T_PRINTER = print,
):
    builder = PoetryBasedLambdaLayerContainerBuilder(
        path_pyproject_toml=path_pyproject_toml,
        py_ver_major=py_ver_major,
        py_ver_minor=py_ver_minor,
        is_arm=is_arm,
        printer=printer,
    )
    builder.step_01_copy_build_script()
    builder.step_02_setup_private_repository_credential()
    builder.step_03_docker_run()
