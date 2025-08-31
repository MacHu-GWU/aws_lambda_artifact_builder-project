# -*- coding: utf-8 -*-

"""

"""

import typing as T
import shutil
import subprocess
import dataclasses
from pathlib import Path
from functools import cached_property

from func_args.api import BaseFrozenModel, REQ, OPT

from ..typehint import T_PRINTER
from ..constants import ZFILL
from ..imports import S3Path
from ..paths import (
    path_build_lambda_layer_using_poetry_in_container_script,
)
from ..utils import clean_build_directory


@dataclasses.dataclass(frozen=True)
class LayerPathLayout(BaseFrozenModel):
    """
    Local directory layout manager for Lambda layer build artifacts.

    假设你的 Git 仓库的目录位于 ``${dir_project_root}/`` 下,
    我们用 ``${dir_project_root}`` 来表示这个路径. 那么跟 Lambda layer 相关的路径如下:

    - ``${dir_project_root}``
        :meth:`dir_project_root`, git 仓库根目录.
    - ``${dir_project_root}/pyproject.toml``
        :attr:`path_pyproject_toml`, pyproject.toml 文件路径.
    - ``${dir_project_root}/build/lambda/layer``
        :meth:`dir_build_lambda_layer`, 构建 Lambda layer 的临时目录,
        每次构建前会被清空.
    - ``${dir_project_root}/build/lambda/layer/layer.zip``
        :meth:`path_build_lambda_layer_zip`, 最终用于部署的 Lambda layer zip 文件路径.
    - ``${dir_project_root}/build/lambda/layer/repo``
        :meth:`dir_repo`, 为了不影响仓库中原有的文件, 我们在这里创建一个临时的,
        结构类似于 dir_project_root 的目录, 并把一些重要文件拷贝进去, 例如 pyproject.toml
        如果需要临时构建虚拟环境, 也会在这里创建.
    - ``${dir_project_root}/build/lambda/layer/artifacts``
        :meth:`dir_artifacts`, 用于存放所有需要打包进 layer.zip 的文件
    - ``${dir_project_root}/build/lambda/layer/artifacts/python``
        :meth:`dir_python`, AWS Lambda 要求的 ``python`` 子目录.
    """

    path_pyproject_toml: Path = dataclasses.field()

    @property
    def dir_project_root(self) -> Path:
        """
        Project root directory, usually the Git repository root.
        """
        return self.path_pyproject_toml.parent

    @property
    def dir_build_lambda_layer(self) -> Path:
        """
        The build directory for Lambda layer build.
        """
        return self.dir_project_root / "build" / "lambda" / "layer"

    @property
    def path_build_lambda_layer_zip(self) -> Path:
        """
        The output zip file path for the built Lambda layer.
        """
        return self.dir_build_lambda_layer / "layer.zip"

    @property
    def dir_repo(self) -> Path:
        """
        A temporary copy of the project repository for building the layer.
        """
        return self.dir_build_lambda_layer / "repo"

    @property
    def path_tmp_pyproject_toml(self) -> Path:
        """
        A temporary copy of pyproject.toml for building the layer.
        """
        return self.dir_repo / self.path_pyproject_toml.name

    @property
    def path_build_lambda_layer_in_container_script_in_local(self) -> Path:
        return self.dir_repo / "build_lambda_layer_in_container.py"

    @property
    def path_build_lambda_layer_in_container_script_in_container(self) -> str:
        p = self.path_build_lambda_layer_in_container_script_in_local
        dir = self.dir_project_root
        relpath = p.relative_to(dir)
        parts = ["var", "task"]
        parts.extend(relpath.parts)
        path = "/" + "/".join(parts)
        return path

    @property
    def path_requirements_txt(self) -> Path:
        """
        The generated requirements.txt file path.
        """
        return self.dir_project_root / "requirements.txt"

    @property
    def path_poetry_lock(self) -> Path:
        """
        The original poetry.lock file path.
        """
        return self.dir_project_root / "poetry.lock"

    @property
    def path_tmp_poetry_lock(self) -> Path:
        """
        A temporary copy of poetry.lock for building the layer.
        """
        return self.dir_repo / "poetry.lock"

    @property
    def path_uv_lock(self) -> Path:
        """
        The original uv.lock file path.
        """
        return self.dir_project_root / "uv.lock"

    @property
    def path_tmp_uv_lock(self) -> Path:
        """
        A temporary copy of uv.lock for building the layer.
        """
        return self.dir_repo / "uv.lock"

    @property
    def dir_artifacts(self) -> Path:
        """
        The directory to store all files to be included in the layer.zip.
        """
        return self.dir_build_lambda_layer / "artifacts"

    @property
    def dir_python(self) -> Path:
        """
        The AWS Lambda required ``python`` subdirectory.

        Ref:

        - https://docs.aws.amazon.com/lambda/latest/dg/python-layers.html
        """
        return self.dir_artifacts / "python"

    def clean(self, skip_prompt: bool = False):
        """
        Clean existing build directory to ensure fresh installation.
        """
        clean_build_directory(
            dir_build=self.dir_build_lambda_layer,
            folder_alias="lambda layer build folder",
            skip_prompt=skip_prompt,
        )

    def mkdirs(self):
        """
        Make sure all necessary directories exist.
        """
        self.dir_repo.mkdir(parents=True, exist_ok=True)
        self.dir_python.mkdir(parents=True, exist_ok=True)

    def copy_file(
        self,
        p_src: Path,
        p_dst: Path,
        printer: T_PRINTER = print,
    ):
        printer(f"Copy {p_src} to {p_dst}")
        shutil.copy(p_src, p_dst)

    def copy_build_script(self, p_src: Path, printer: T_PRINTER = print):
        self.copy_file(
            p_src=p_src,
            p_dst=self.path_build_lambda_layer_in_container_script_in_local,
            printer=printer,
        )

    def copy_pyproject_toml(self, printer: T_PRINTER = print):
        self.copy_file(
            p_src=self.path_pyproject_toml,
            p_dst=self.path_tmp_pyproject_toml,
            printer=printer,
        )

    def copy_poetry_lock(self, printer: T_PRINTER = print):
        self.copy_file(
            p_src=self.path_poetry_lock,
            p_dst=self.path_tmp_poetry_lock,
            printer=printer,
        )

    def copy_uv_lock(self, printer: T_PRINTER = print):
        self.copy_file(
            p_src=self.path_uv_lock,
            p_dst=self.path_tmp_uv_lock,
            printer=printer,
        )


@dataclasses.dataclass
class LayerS3Layout:
    """
    S3 directory layout manager for Lambda layer artifacts.

    Example::

        # if
        s3dir_lambda = "s3://my-bucket/my-app/lambda/"

        # :meth:`s3path_temp_layer_zip`
        s3://my-bucket/my-app/lambda/layer/layer.zip

        # :meth:`get_s3path_layer_requirements_txt`
        s3://my-bucket/my-app/lambda/layer/000001/requirements.txt

        # :meth:`s3path_last_requirements_txt`
        s3://my-bucket/my-app/lambda/layer/last-requirements.txt
    """

    s3dir_lambda: "S3Path" = dataclasses.field()

    @property
    def s3path_temp_layer_zip(self) -> "S3Path":
        """
        Layer artifacts are uploaded to this temporary location for
        ``publish_layer_version`` API call.

        .. note::

            Since AWS stores Lambda layer for you, there's no need to maintain
            keep historical versions of the layer zip in S3.

        :returns: S3Path to the last requirements.txt file
        """
        return self.s3dir_lambda.joinpath("layer", "last-requirements.txt")

    def get_s3path_layer_requirements_txt(
        self,
        layer_version: int,
    ) -> "S3Path":
        """
        Generate S3 Path for a specific version of the ``requirements.txt`` file.

        :param layer_version: Layer version number

        :return: S3Path object pointing to the versioned requirements.txt file
        """
        return self.s3dir_lambda.joinpath(
            "layer",
            str(layer_version).zfill(ZFILL),
            "requirements.txt",
        )

    @property
    def s3path_last_requirements_txt(self) -> "S3Path":
        """
        The last requirements.txt file for the published layer version.

        This file is used to compare with the local requirements.txt to determine
        whether a new layer version needs to be published.

        :returns: S3Path to the last requirements.txt file
        """
        return self.s3dir_lambda.joinpath("layer", "last-requirements.txt")


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

    def step_02_setup_build_dir(self, skip_prompt: bool = False):
        """
        Clean existing build directory to ensure fresh installation.
        """
        dir = self.path_layout.dir_build_lambda_layer
        self.printer(f"--- Clean existing build directory: {dir}")
        self.path_layout.clean(skip_prompt=skip_prompt)
        self.path_layout.mkdirs()


@dataclasses.dataclass(frozen=True)
class BasedLambdaLayerContainerBuilder(BaseFrozenModel):
    """
    Command pattern for building Lambda layers using Docker containers.

    This class encapsulates all the configuration and logic needed to build
    Lambda layers in Docker containers using AWS SAM build images.
    Designed for extensibility through subclassing.
    """

    path_pyproject_toml: Path = dataclasses.field(default=REQ)
    py_ver_major: int = dataclasses.field(default=REQ)
    py_ver_minor: int = dataclasses.field(default=REQ)
    is_arm: bool = dataclasses.field(default=REQ)
    printer: T_PRINTER = dataclasses.field(default=print)

    @cached_property
    def path_layout(self) -> LayerPathLayout:
        return LayerPathLayout(
            path_pyproject_toml=self.path_pyproject_toml,
        )

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
    def path_build_lambda_layer_in_container_script_in_container(self) -> str:
        """
        Python script that builds AWS Lambda layers inside Docker containers,
        orchestrating dependencies installations and layer artifact creation
        as an automated build process.
        """
        return f"/var/task/{path_build_lambda_layer_in_container_script.name}"

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
            f"type=bind,source={self.path_layout.dir_project_root},target=/var/task",
            self.image_uri,
            "python",
            # Use unbuffered output to ensure real-time logging
            "-u",
            self.path_layout.path_build_lambda_layer_in_container_script_in_container,
        ]

    def step_01_copy_build_script(self):
        self.path_layout.copy_build_script(
            p_src=path_build_lambda_layer_using_poetry_in_container_script,
            printer=self.printer,
        )

    def step_02_setup_private_repository_credential(self):
        pass

    def step_03_docker_run(self):
        subprocess.run(self.args)
