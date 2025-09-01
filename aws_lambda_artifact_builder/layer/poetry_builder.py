# -*- coding: utf-8 -*-

"""

"""

import os
import subprocess
import dataclasses
from pathlib import Path

from func_args.api import REQ
from ..vendor.better_pathlib import temp_cwd

from ..typehint import T_PRINTER
from ..paths import path_build_lambda_layer_using_poetry_in_container_script

from .common import (
    Credentials,
    BasedLambdaLayerLocalBuilder,
    BasedLambdaLayerContainerBuilder,
)


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

    def _poetry_login(self, credentials: Credentials):
        self.printer("Setting up Poetry credentials ...")
        # poetry use environment variables to get the private repository
        # Http basic auth credentials.
        # See: https://python-poetry.org/docs/repositories/#configuring-credentials
        source_name = credentials.index_name.replace("-", "_").upper()
        key = f"POETRY_HTTP_BASIC_{source_name}_USERNAME"
        os.environ[key] = "aws"
        self.printer(f"Set environment variable {key}")
        key = f"POETRY_HTTP_BASIC_{source_name}_PASSWORD"
        os.environ[key] = credentials.password
        self.printer(f"Set environment variable {key}")

    def step_04_run_poetry_install(
        self,
        credentials: Credentials | None = None,
    ):
        path_bin_poetry = self.path_bin_poetry
        dir_repo = self.path_layout.dir_repo
        with temp_cwd(dir_repo):
            self.printer("Run 'poetry config virtualenvs.in-project true'")
            args = [
                f"{path_bin_poetry}",
                "config",
                "virtualenvs.in-project",
                "true",
            ]
            subprocess.run(args, cwd=dir_repo, check=True)
            if credentials is not None:
                self._poetry_login(credentials)

            self.printer("Run 'poetry install --no-root'")
            args = [
                f"{path_bin_poetry}",
                "install",
                "--no-root",
            ]
            subprocess.run(args, cwd=dir_repo, check=True)


def build_layer_artifacts_using_poetry_in_local(
    path_bin_poetry: Path,
    path_pyproject_toml: Path,
    credentials: Credentials | None = None,
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
    builder.step_04_run_poetry_install(credentials=credentials)


@dataclasses.dataclass(frozen=True)
class PoetryBasedLambdaLayerContainerBuilder(
    BasedLambdaLayerContainerBuilder,
):

    def step_01_copy_build_script(self):
        self.path_layout.copy_build_script(
            p_src=path_build_lambda_layer_using_poetry_in_container_script,
            printer=self.printer,
        )


def build_layer_artifacts_using_poetry_in_container(
    path_pyproject_toml: Path,
    py_ver_major: int,
    py_ver_minor: int,
    is_arm: bool,
    credentials: Credentials | None = None,
    printer: T_PRINTER = print,
):
    builder = PoetryBasedLambdaLayerContainerBuilder(
        path_pyproject_toml=path_pyproject_toml,
        py_ver_major=py_ver_major,
        py_ver_minor=py_ver_minor,
        is_arm=is_arm,
        credentials=credentials,
        printer=printer,
    )

    builder.step_01_copy_build_script()
    builder.step_02_setup_private_repository_credential()
    builder.step_03_docker_run()
