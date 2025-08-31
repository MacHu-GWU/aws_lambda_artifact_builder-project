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
from ..paths import path_build_lambda_layer_using_pip_in_container_script

from .common import BasedLambdaLayerLocalBuilder, BasedLambdaLayerContainerBuilder


@dataclasses.dataclass(frozen=True)
class PipBasedLambdaLayerLocalBuilder(
    BasedLambdaLayerLocalBuilder,
):
    """
    Only build this locally, without Docker container.
    """

    path_bin_pip: Path = dataclasses.field(default=REQ)
    _tool: str = dataclasses.field(default="poetry")

    def step_01_print_info(self):
        super().step_01_print_info()
        self.printer(f"path_bin_pip = {self.path_bin_pip}")

    def step_03_run_pip_install(self):
        path_bin_pip = self.path_bin_pip
        dir_repo = self.path_layout.dir_repo
        with temp_cwd(dir_repo):
            args = [
                f"{path_bin_pip}",
                "install",
                "-r",
                f"{self.path_layout.path_requirements_txt}",
                "-t",
                f"{self.path_layout.dir_python}",
            ]
            subprocess.run(args, cwd=dir_repo, check=True)


def build_layer_artifacts_using_pip_in_local(
    path_bin_pip: Path,
    path_pyproject_toml: Path,
    skip_prompt: bool = False,
    printer: T_PRINTER = print,
):
    """ """
    builder = PipBasedLambdaLayerLocalBuilder(
        path_bin_pip=path_bin_pip,
        path_pyproject_toml=path_pyproject_toml,
        printer=printer,
    )
    builder.step_01_print_info()
    builder.step_02_setup_build_dir(skip_prompt=skip_prompt)
    builder.step_03_run_pip_install()


@dataclasses.dataclass(frozen=True)
class PipBasedLambdaLayerContainerBuilder(
    BasedLambdaLayerContainerBuilder,
):
    def step_01_copy_build_script(self):
        self.path_layout.copy_build_script(
            p_src=path_build_lambda_layer_using_pip_in_container_script,
            printer=self.printer,
        )


def build_layer_artifacts_using_pip_in_container(
    path_pyproject_toml: Path,
    py_ver_major: int,
    py_ver_minor: int,
    is_arm: bool,
    printer: T_PRINTER = print,
):
    builder = PipBasedLambdaLayerContainerBuilder(
        path_pyproject_toml=path_pyproject_toml,
        py_ver_major=py_ver_major,
        py_ver_minor=py_ver_minor,
        is_arm=is_arm,
        printer=printer,
    )

    builder.step_01_copy_build_script()
    builder.step_02_setup_private_repository_credential()
    builder.step_03_docker_run()
