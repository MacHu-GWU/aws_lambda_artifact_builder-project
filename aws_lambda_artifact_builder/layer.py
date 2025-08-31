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

from func_args.api import OPT, BaseFrozenModel
from s3pathlib import S3Path


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


@dataclasses.dataclass(frozen=True)
class LayerPathLayout(BaseFrozenModel):
    """

    Example::

        # :meth:`dir_project_root`
        ${HOME}/GitHub/my_app-project/pyproject.toml

        # :meth:`dir_build_lambda_layer`
        ${HOME}/GitHub/my_app-project/build/lambda/layer

        # :meth:`path_build_lambda_layer_zip`
        ${HOME}/GitHub/my_app-project/build/lambda/layer/layer.zip

        # :meth:`dir_tmp`
        ${HOME}/GitHub/my_app-project/build/lambda/layer/tmp

        # :meth:`dir_tmp_python`
        ${HOME}/GitHub/my_app-project/build/lambda/layer/python
    """

    path_pyproject_toml: Path = dataclasses.field()

    @property
    def dir_project_root(self) -> Path:
        """ """
        return self.path_pyproject_toml.parent

    @property
    def dir_build_lambda_layer(self) -> Path:
        """ """
        return self.dir_project_root / "build" / "lambda" / "layer"

    @property
    def path_build_lambda_layer_zip(self) -> Path:
        """ """
        return self.dir_build_lambda_layer / "layer.zip"

    @property
    def dir_tmp(self) -> Path:
        """ """
        return self.dir_build_lambda_layer / "tmp"

    @property
    def dir_tmp_python(self):
        """
        Ref:

        - https://docs.aws.amazon.com/lambda/latest/dg/python-layers.html
        """
        return self.dir_build_lambda_layer


@dataclasses.dataclass
class LayerS3Layout:
    """
    S3 directory layout manager for Lambda layer artifacts.
    """

    s3dir_lambda: S3Path = dataclasses.field()

    @property
    def s3path_temp_layer_zip(self) -> S3Path:
        """
        Layer artifacts are uploaded to this temporary location for
        ``publish_layer_version`` API call.

        Example: ``${s3dir_lambda}/layer/layer.zip``

        .. note::

            Since AWS stores Lambda layer for you, there's no need to maintain
            keep historical versions of the layer zip in S3.

        :returns: S3Path to the last requirements.txt file
        """
        return self.s3dir_lambda.joinpath("layer", "last-requirements.txt")

    def get_s3path_layer_requirements_txt(
        self,
        layer_version: int,
    ) -> S3Path:
        """
        Generate S3 Path for a specific version of the requirements.txt file.

        Example: ``${s3dir_lambda}/layer/${layer_version}/requirements.txt``

        :param layer_version: Layer version number

        :return: S3Path object pointing to the versioned requirements.txt file
        """
        return self.s3dir_lambda.joinpath(
            "layer",
            str(layer_version).zfill(ZFILL),
            "requirements.txt",
        )

    @property
    def s3path_last_requirements_txt(self) -> S3Path:
        """
        The last requirements.txt file for the published layer version.

        Example: ``${s3dir_lambda}/layer/last-requirements.txt``

        This file is used to compare with the local requirements.txt to determine
        whether a new layer version needs to be published.

        :returns: S3Path to the last requirements.txt file
        """
        return self.s3dir_lambda.joinpath("layer", "last-requirements.txt")


@dataclasses.dataclass(frozen=True)
class PoetryBasedLambdaLayerLocalBuilder(BaseFrozenModel):
    """
    Only build this locally, without Docker container.
    """

    path_bin_poetry: Path = dataclasses.field()
    path_pyproject_toml: Path = dataclasses.field()
    printer: T_PRINTER = dataclasses.field(default=print)

    @cached_property
    def path_layout(self) -> LayerPathLayout:
        return LayerPathLayout(
            path_pyproject_toml=self.path_pyproject_toml,
        )

    def s01_print_info(self):
        self.printer(f"--- Building Lambda source artifacts using pip ...")
        self.printer(f"path_bin_poetry = {self.path_bin_poetry!s}")
        self.printer(f"path_pyproject_toml = {self.path_pyproject_toml!s}")
        self.printer(
            f"dir_build_lambda_layer = {self.path_layout.dir_build_lambda_layer}"
        )

    def s02_clean_build_directory(self, skip_prompt: bool = False):
        """
        Clean existing build directory to ensure fresh installation
        """
        dir = self.path_layout.dir_build_lambda_layer
        self.printer(f"Clean existing build directory: {dir}")
        clean_build_directory(
            dir_build=dir,
            folder_alias="lambda layer build folder",
            skip_prompt=skip_prompt,
        )

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

    def s04_run_poetry_install(self):
        path_bin_poetry = self.path_bin_poetry
        dir_tmp = self.path_layout.dir_tmp
        with temp_cwd(dir_tmp):
            args = [
                f"{path_bin_poetry}",
                "config",
                "virtualenvs.in-project",
                "true",
            ]
            subprocess.run(args, cwd=dir_tmp, check=True)

            args = [
                f"{path_bin_poetry}",
                "install",
                "--no-root",
            ]
            subprocess.run(args, cwd=dir_tmp, check=True)


def build_layer_artifacts_using_poetry_in_local(
    path_bin_poetry: Path,
    path_pyproject_toml: Path,
    verbose: bool = True,
    skip_prompt: bool = False,
    printer: T_PRINTER = print,
):
    """
    :return: the layer content sha256, it is sha256 of the requirements.txt file
    """
    builder = PoetryBasedLambdaLayerLocalBuilder(
        path_bin_poetry=path_bin_poetry,
        path_pyproject_toml=path_pyproject_toml,
        printer=printer,
    )
    if verbose:
        builder.s01_print_info()
    builder.s02_clean_build_directory(skip_prompt=skip_prompt)
    builder.s03_prepare_poetry_stuff()
    builder.s04_run_poetry_install()
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
