# -*- coding: utf-8 -*-

"""
UV-based Lambda layer builder implementation.

This module provides Lambda layer creation using UV's ultra-fast dependency management,
supporting both local and containerized builds. UV offers the fastest dependency
resolution and installation while maintaining compatibility with pip and Poetry workflows.

**Command Pattern Classes:**

- :class:`UvBasedLambdaLayerLocalBuilder`: Local uv-based builds
- :class:`UvBasedLambdaLayerContainerBuilder`: Containerized uv-based builds
"""

import subprocess
import dataclasses
from pathlib import Path

from func_args.api import REQ
from ..vendor.better_pathlib import temp_cwd

from ..constants import LayerBuildToolEnum
from ..paths import path_build_lambda_layer_using_uv_in_container_script

from .builder import (
    BasedLambdaLayerLocalBuilder,
    BasedLambdaLayerContainerBuilder,
)


@dataclasses.dataclass(frozen=True)
class UVBasedLambdaLayerLocalBuilder(
    BasedLambdaLayerLocalBuilder,
):
    """
    This class implements UV-specific build workflow using lock files and
    UV's high-performance dependency resolution.

    **Key Features:**

    - Frozen lock file installation (--frozen)
    - Environment variable authentication (UV_INDEX_*)
    - Development dependency exclusion (--no-dev)
    - Copy-based linking for Lambda compatibility (--link-mode=copy)

    .. seealso::

        :class:`~aws_lambda_artifact_builder.layer.builder.BasedLambdaLayerLocalBuilder`
    """

    path_bin_uv: Path = dataclasses.field(default=REQ)
    _build_tool: str = dataclasses.field(default=LayerBuildToolEnum.uv)

    def step_1_1_print_info(self):
        """
        Display uv-specific build information.
        """
        super().step_1_1_print_info()
        self.log(f"path_bin_uv = {self.path_bin_uv}")

    def step_2_prepare_environment(self):
        super().step_2_prepare_environment()
        self.step_2_2_prepare_uv_stuff()

    def step_2_2_prepare_uv_stuff(self):
        """
        Copy UV project files to build directory.

        Copies pyproject.toml and uv.lock to ensure reproducible builds
        with exact dependency versions as resolved by UV.
        """
        self.log("--- Step 2.2 - Prepare UV stuff")
        self.path_layout.copy_pyproject_toml(printer=self.log)
        self.path_layout.copy_uv_lock(printer=self.log)

    def step_3_execute_build(self):
        """
        Perform Poetry-based Lambda layer build step.
        """
        super().step_3_execute_build()
        self.step_3_1_uv_login()
        self.step_3_2_run_uv_sync()

    def step_3_1_uv_login(self):
        """
        Configure UV authentication via environment variables.
        """
        self.log("--- Step 3.1 - Setting up UV credentials")
        if self.credentials is not None:
            key_user, key_pass = self.credentials.uv_login()
            self.log(f"Set environment variable {key_user}")
            self.log(f"Set environment variable {key_pass}")
        else:
            self.log("No UV credentials provided, skipping UV login step")

    def step_3_2_run_uv_sync(self):
        """
        Execute UV sync with lock file constraints.

        Runs UV sync with --frozen to prevent lock file updates, --no-dev to exclude
        development dependencies, and --no-install-project to exclude the project itself.
        Uses --link-mode=copy for Lambda layer compatibility.
        """
        self.log("--- Step 3.2 - Run 'uv sync'")
        path_bin_uv = self.path_bin_uv
        dir_repo = self.path_layout.dir_repo
        with temp_cwd(dir_repo):
            args = [
                f"{path_bin_uv}",
                "sync",
                "--frozen",
                "--no-dev",
                "--no-install-project",
                "--link-mode=copy",
            ]
            subprocess.run(args, cwd=dir_repo, check=True)


@dataclasses.dataclass(frozen=True)
class UVBasedLambdaLayerContainerBuilder(
    BasedLambdaLayerContainerBuilder,
):
    """
    Command class for containerized UV-based Lambda layer builds.

    .. seealso::

        :class:`~aws_lambda_artifact_builder.layer.builder.BasedLambdaLayerContainerBuilder`
    """

    path_script: Path = dataclasses.field(
        default=path_build_lambda_layer_using_uv_in_container_script
    )

    def step_1_preflight_check(self):
        super().step_1_preflight_check()
        if self.path_layout.path_uv_lock.exists() is False:
            raise FileNotFoundError(
                f"UV lock file not found: {self.path_layout.path_uv_lock},"
                f"cannot proceed with uv-based build."
                f"Please run 'uv lock' to generate the lock file."
            )
