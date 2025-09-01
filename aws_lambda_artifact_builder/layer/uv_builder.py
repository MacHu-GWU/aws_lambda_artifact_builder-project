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
from ..paths import path_build_lambda_layer_using_uv_in_container_script

from .common import (
    Credentials,
    BasedLambdaLayerLocalBuilder,
    BasedLambdaLayerContainerBuilder,
)


@dataclasses.dataclass(frozen=True)
class UVBasedLambdaLayerLocalBuilder(
    BasedLambdaLayerLocalBuilder,
):
    """
    Only build this locally, without Docker container.
    """

    path_bin_uv: Path = dataclasses.field(default=REQ)
    _tool: str = dataclasses.field(default="uv")

    def step_01_print_info(self):
        super().step_01_print_info()
        self.printer(f"path_bin_uv = {self.path_bin_uv}")

    def step_03_prepare_uv_stuff(self):
        self.path_layout.copy_pyproject_toml(printer=self.printer)
        self.path_layout.copy_uv_lock(printer=self.printer)

    def _uv_login(self, credentials: Credentials):
        self.printer("Setting up uv credentials ...")
        # uv use environment variables to get the private repository
        # Http basic auth credentials.
        # See: https://docs.astral.sh/uv/reference/environment/#uv_index_url
        source_name = credentials.index_name.replace("-", "_").upper()
        key = f"UV_INDEX_{source_name}_USERNAME"
        os.environ[key] = "aws"
        self.printer(f"Set environment variable {key}")
        key = f"UV_INDEX_{source_name}_PASSWORD"
        os.environ[key] = credentials.password
        self.printer(f"Set environment variable {key}")

    def step_04_run_uv_sync(
        self,
        credentials: Credentials | None = None,
    ):
        path_bin_uv = self.path_bin_uv
        dir_repo = self.path_layout.dir_repo
        with temp_cwd(dir_repo):
            if credentials is not None:
                self._uv_login(credentials)

            self.printer("Run 'uv sync' ...")
            args = [
                f"{path_bin_uv}",
                "sync",
                "--frozen",
                "--no-dev",
                "--no-install-project",
            ]
            subprocess.run(args, cwd=dir_repo, check=True)


def build_layer_artifacts_using_uv_in_local(
    path_bin_uv: Path,
    path_pyproject_toml: Path,
    credentials: Credentials | None = None,
    skip_prompt: bool = False,
    printer: T_PRINTER = print,
):
    """ """
    builder = UVBasedLambdaLayerLocalBuilder(
        path_bin_uv=path_bin_uv,
        path_pyproject_toml=path_pyproject_toml,
        printer=printer,
    )
    builder.step_01_print_info()
    builder.step_02_setup_build_dir(skip_prompt=skip_prompt)
    builder.step_03_prepare_uv_stuff()
    builder.step_04_run_uv_sync(credentials=credentials)


@dataclasses.dataclass(frozen=True)
class UVBasedLambdaLayerContainerBuilder(
    BasedLambdaLayerContainerBuilder,
):

    def step_01_copy_build_script(self):
        self.path_layout.copy_build_script(
            p_src=path_build_lambda_layer_using_uv_in_container_script,
            printer=self.printer,
        )


def build_layer_artifacts_using_uv_in_container(
    path_pyproject_toml: Path,
    py_ver_major: int,
    py_ver_minor: int,
    is_arm: bool,
    credentials: Credentials | None = None,
    printer: T_PRINTER = print,
):
    builder = UVBasedLambdaLayerContainerBuilder(
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
