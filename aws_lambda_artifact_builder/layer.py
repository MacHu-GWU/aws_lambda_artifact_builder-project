# -*- coding: utf-8 -*-

"""
S3 Storage Structure::

    s3://bucket/${s3dir_lambda}/layer/000001/requirements.txt
    s3://bucket/${s3dir_lambda}/layer/000002/requirements.txt
    s3://bucket/${s3dir_lambda}/layer/000003/requirements.txt
    s3://bucket/${s3dir_lambda}/layer/last-requirements.txt
    s3://bucket/${s3dir_lambda}/layer/layer.zip
"""
import typing as T
import glob
import os
import shutil
import subprocess
import dataclasses
from pathlib import Path
from functools import cached_property

from func_args.api import REQ, OPT, BaseFrozenModel

from .imports import S3Path

from .vendor.better_pathlib import temp_cwd
from .vendor.hashes import hashes

from .constants import ZFILL, S3MetadataKeyEnum
from .typehint import T_PRINTER
from .utils import (
    clean_build_directory,
)
from .paths import path_build_lambda_layer_in_container_script

if T.TYPE_CHECKING:  # pragma: no cover
    from mypy_boto3_s3.client import S3Client
    from mypy_boto3_codeartifact.client import CodeArtifactClient





@dataclasses.dataclass(frozen=True)
class BasedLambdaLayerLocalBuilder(BaseFrozenModel):
    """ """

    path_pyproject_toml: Path = dataclasses.field(default=REQ)
    printer: T_PRINTER = dataclasses.field(default=print)
    _tool: str = dataclasses.field(default=REQ)

    @cached_property
    def path_layout(self) -> LayerPathLayout:
        return LayerPathLayout(
            path_pyproject_toml=self.path_pyproject_toml,
        )

    def step_01_print_info(self):
        """
        Print build information.
        """
        self.printer(f"--- Build Lambda layer artifacts using {self._tool} ...")

        p = self.path_pyproject_toml
        self.printer(f"path_pyproject_toml = {p}")

        p = self.path_layout.dir_build_lambda_layer
        self.printer(f"dir_build_lambda_layer = {p}")

    def step_02_clean_build_dir(self, skip_prompt: bool = False):
        """
        Clean existing build directory to ensure fresh installation.
        """
        dir = self.path_layout.dir_build_lambda_layer
        self.printer(f"--- Clean existing build directory: {dir}")
        clean_build_directory(
            dir_build=dir,
            folder_alias="lambda layer build folder",
            skip_prompt=skip_prompt,
        )



    # build_context = BuildContext.new(dir_build=dir_build)
    # path_requirements = Path(path_requirements).absolute()
    # bin_pip = Path(bin_pip).absolute()
    #
    # # remove existing artifacts and temp folder
    # build_context.path_layer_zip.unlink(missing_ok=True)
    # shutil.rmtree(build_context.dir_python, ignore_errors=True)
    #
    # # initialize the build/lambda folder
    # build_context.dir_build.mkdir(parents=True, exist_ok=True)
    #
    # # do "pip install -r requirements.txt -t ./build/lambda/python"
    # args = [
    #     f"{bin_pip}",
    #     "install",
    #     "-r",
    #     f"{path_requirements}",
    #     "-t",
    #     f"{build_context.dir_python}",
    # ]
    # if quiet:
    #     args.append("--disable-pip-version-check")
    #     args.append("--quiet")
    # if extra_args is not None:
    #     args.extend(extra_args)
    # subprocess.run(args, check=True)
    #
    # # zip the layer file
    # # some packages are pre-installed in AWS Lambda runtime, so we don't need to
    # # add them to the layer
    # if ignore_package_list is None:
    #     ignore_package_list = [
    #         "boto3",
    #         "botocore",
    #         "s3transfer",
    #         "urllib3",
    #         "setuptools",
    #         "pip",
    #         "wheel",
    #         "twine",
    #         "_pytest",
    #         "pytest",
    #     ]
    # args = [
    #     "zip",
    #     f"{build_context.path_layer_zip}",
    #     "-r",
    #     "-9",
    # ]
    # if quiet:
    #     args.append("-q")
    # # the glob command and zip command depends on the current working directory
    # with temp_cwd(build_context.dir_build):
    #     args.extend(glob.glob("*"))
    #     if ignore_package_list:
    #         args.append("-x")
    #         for package in ignore_package_list:
    #             args.append(f"python/{package}*")
    #     subprocess.run(args, check=True)


# POETRY_VIRTUALENVS_PATH


@dataclasses.dataclass(frozen=True)
class PipBasedLambdaLayerLocalBuilder(
    BasedLambdaLayerLocalBuilder,
):
    """
    Only build this locally, without Docker container.
    """

    path_bin_pip: Path = dataclasses.field(default=REQ)
    _tool: str = dataclasses.field(default="pip")

    def s01_print_info(self):
        super().step_01_print_info()
        self.printer(f"path_bin_pip = {self.path_bin_pip}")

    def s03_prepare_poetry_stuff(self):
        dir_tmp = self.path_layout.dir_tmp
        self.printer("Create temporary directory for poetry install ...")
        dir_tmp.mkdir(parents=True, exist_ok=True)

        path_pyproject_toml = self.path_pyproject_toml
        path_pyproject_toml_tmp = dir_tmp.joinpath(path_pyproject_toml.name)
        self.printer(f"Copy {path_pyproject_toml} to {path_pyproject_toml_tmp}")
        shutil.copy(path_pyproject_toml, path_pyproject_toml_tmp)

        path_poetry_lock = self.path_pyproject_toml.parent / "poetry.lock"
        path_poetry_lock_tmp = dir_tmp.joinpath(path_poetry_lock.name)
        self.printer(f"Copy {path_poetry_lock} to {path_poetry_lock_tmp}")
        shutil.copy(path_poetry_lock, path_poetry_lock_tmp)

    def step_04_run_pip_install(self):
        path_bin_pip = self.path_bin_pip
        # with temp_cwd(dir_tmp):
        #     args = [
        #         f"{path_bin_poetry}",
        #         "config",
        #         "virtualenvs.in-project",
        #         "true",
        #     ]
        #     subprocess.run(args, cwd=dir_tmp, check=True)
        #
        #     args = [
        #         f"{path_bin_poetry}",
        #         "install",
        #         "--no-dev",
        #         "--no-root",
        #     ]
        #     subprocess.run(args, cwd=dir_tmp, check=True)


def build_layer_artifacts_using_pip_in_local(
    path_bin_pip: Path,
    path_pyproject_toml: Path,
    skip_prompt: bool = False,
    printer: T_PRINTER = print,
):
    """
    :return: the layer content sha256, it is sha256 of the requirements.txt file
    """
    builder = PipBasedLambdaLayerLocalBuilder(
        path_bin_pip=path_bin_pip,
        path_pyproject_toml=path_pyproject_toml,
        printer=printer,
    )
    builder.step_01_print_info()
    builder.step_02_clean_build_dir(skip_prompt=skip_prompt)
    builder.step_04_run_pip_install()

@dataclasses.dataclass(frozen=True)
class PoetryBasedLambdaLayerContainerBuilder(BaseFrozenModel):
    """
    Command pattern for building Lambda layers using Docker containers.

    This class encapsulates all the configuration and logic needed to build
    Lambda layers in Docker containers using AWS SAM build images.
    Designed for extensibility through subclassing.
    """

    path_pyproject_toml: Path = dataclasses.field(default=OPT)
    py_ver_major: int = dataclasses.field(default=OPT)
    py_ver_minor: int = dataclasses.field(default=OPT)
    is_arm: bool = dataclasses.field(default=OPT)

    @property
    def dir_project_root(self) -> Path:
        return self.path_pyproject_toml.parent

    @property
    def dir_lambda_layer_build(self) -> Path:
        return self.dir_project_root / "build" / "lambda" / "layer"

    @property
    def image_tag(self) -> str:
        if self.is_arm:
            return "latest-arm64"
        else:
            return "latest-x86_64"

    @property
    def image_uri(self) -> str:
        return (
            f"public.ecr.aws/sam"
            f"/build-python{self.py_ver_major}.{self.py_ver_minor}"
            f":{self.image_tag}"
        )

    @property
    def platform(self) -> str:
        if self.is_arm:
            return "linux/arm64"
        else:
            return "linux/amd64"

    @property
    def container_name(self) -> str:
        suffix = "arm64" if self.is_arm else "amd64"
        return (
            f"lambda_layer_builder"
            f"-python{self.py_ver_major}{self.py_ver_minor}"
            f"-{suffix}"
        )

    @property
    def path_build_lambda_layer_in_container_script_in_local(self) -> Path:
        return self.dir_project_root / path_build_lambda_layer_in_container_script.name

    @property
    def path_build_lambda_layer_in_container_script_in_container(self) -> str:
        """
        Python script that builds AWS Lambda layers inside Docker containers,
        orchestrating dependencies installations and layer artifact creation
        as an automated build process.
        """
        return f"/var/task/{path_build_lambda_layer_in_container_script.name}"

    def s01_copy(self):
        p_dst = self.path_build_lambda_layer_in_container_script_in_local
        p_dst.unlink(missing_ok=True)

        p_src = path_build_lambda_layer_in_container_script
        shutil.copy(p_src, p_dst)

    def s02_setup_private_repo_credential(self):
        pass

    def s03_run_docker(self):
        subprocess.run(self.args)

    @property
    def args(self) -> list[str]:
        return [
            "docker",
            "run",
            "--rm",
            "--name",
            self.container_name,
            "--platform",
            self.platform,
            "--mount",
            f"type=bind,source={self.dir_project_root},target=/var/task",
            self.image_uri,
            "python",
            # Use unbuffered output to ensure real-time logging
            "-u",
            self.path_build_lambda_layer_in_container_script_in_container,
        ]


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
    )
    builder.s01_copy()
    builder.s02_setup_private_repo_credential()
    builder.s03_run_docker()


