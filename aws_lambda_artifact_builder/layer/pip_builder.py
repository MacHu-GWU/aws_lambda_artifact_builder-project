# -*- coding: utf-8 -*-

"""
Pip-based Lambda layer builder implementation.

This module provides Lambda layer creation using pip's ``--target`` installation method,
supporting both local and containerized builds. It offers the simplest approach to layer
creation since pip is universally available with Python installations.

**Command Pattern Classes:**

- :class:`PipBasedLambdaLayerLocalBuilder`: Local pip-based builds
- :class:`PipBasedLambdaLayerContainerBuilder`: Containerized pip-based builds
"""

import subprocess
import dataclasses
from pathlib import Path

from func_args.api import REQ
from ..vendor.better_pathlib import temp_cwd

from ..constants import LayerBuildToolEnum
from ..paths import path_build_lambda_layer_using_pip_in_container_script

from .builder import (
    BasedLambdaLayerLocalBuilder,
    BasedLambdaLayerContainerBuilder,
)


@dataclasses.dataclass(frozen=True)
class PipBasedLambdaLayerLocalBuilder(
    BasedLambdaLayerLocalBuilder,
):
    """
    Command class for local pip-based Lambda layer builds (Internal API).

    .. seealso::

        :class:`~aws_lambda_artifact_builder.layer.builder.BasedLambdaLayerLocalBuilder`
    """

    path_bin_pip: Path = dataclasses.field(default=REQ)
    _build_tool: str = dataclasses.field(default=LayerBuildToolEnum.pip)

    def step_1_1_print_info(self):
        """
        Display pip-specific build information.
        """
        super().step_1_1_print_info()
        self.printer(f"path_bin_pip = {self.path_bin_pip}")

    def step_3_execute_build(self):
        """
        Perform pip-based Lambda layer build step.
        """
        self.step_3_1_run_pip_install()

    def step_3_1_run_pip_install(self):
        """
        Execute pip install with --target flag and optional private repository authentication.

        Installs from requirements.txt directly into Lambda's python/ directory.
        Supports private repositories via --index-url with embedded credentials.
        """
        path_bin_pip = self.path_bin_pip
        dir_repo = self.path_layout.dir_repo
        with temp_cwd(dir_repo):
            args = [
                f"{path_bin_pip}",
                "install",
                "-r",
                f"{self.path_layout.path_requirements_txt}",
                "-t",  # Target directory for package installation
                f"{self.path_layout.dir_python}",  # AWS Lambda python/ directory
            ]
            # Add private repository authentication if provided
            if self.credentials is not None:
                more_args = self.credentials.additional_pip_install_args_index_url
                args.extend(more_args)
            subprocess.run(args, cwd=dir_repo, check=True)


@dataclasses.dataclass(frozen=True)
class PipBasedLambdaLayerContainerBuilder(
    BasedLambdaLayerContainerBuilder,
):
    """
    Command class for containerized pip-based Lambda layer builds.

    .. seealso::

        :class:`~aws_lambda_artifact_builder.layer.builder.BasedLambdaLayerContainerBuilder`
    """

    path_script: Path = dataclasses.field(
        default=path_build_lambda_layer_using_pip_in_container_script
    )
