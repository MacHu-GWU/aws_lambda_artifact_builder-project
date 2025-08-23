# -*- coding: utf-8 -*-

"""
This module implements the automation of AWS Lambda deployment package building.
It stores the source artifacts in an S3 bucket with the following structure::

    s3://bucket/${s3dir_lambda}/source/0.1.1/source.zip
    s3://bucket/${s3dir_lambda}/source/0.1.2/source.zip
    s3://bucket/${s3dir_lambda}/source/0.1.3/source.zip

The pattern in this module is inspired by this
`blog post <https://sanhehu.atlassian.net/wiki/spaces/LEARNAWS/pages/556793859/AWS+Lambda+Python+Package+Deployment+Ultimate+Guide>`_
"""

import typing as T
import glob
import shutil
import subprocess
import dataclasses
from pathlib import Path
from urllib.parse import urlencode

from func_args.api import OPT, remove_optional
from s3pathlib import S3Path

from .vendor.better_pathlib import temp_cwd
from .vendor.hashes import hashes

from .constants import S3MetadataKeyEnum
from .utils import (
    ensure_exact_one_true,
    write_bytes,
    copy_source_for_lambda_deployment,
    clean_build_directory,
)

if T.TYPE_CHECKING:  # pragma: no cover
    from mypy_boto3_s3.client import S3Client
    from mypy_boto3_lambda.client import LambdaClient


def build_source_artifacts_using_pip(
    path_bin_pip: Path,
    path_setup_py_or_pyproject_toml: Path,
    dir_lambda_source_build: Path,
    verbose: bool = True,
    skip_prompt: bool = False,
    printer: T.Callable[[str], None] = print,
):
    """
    Build the Lambda source artifacts using pip.

    :param path_bin_pip: example ``/path/to/.venv/bin/pip``
    :param path_setup_py_or_pyproject_toml: example: ``/path/to/setup.py`` or ``/path/to/pyproject.toml``
    :param dir_lambda_source_build: example: ``/path/to/build/lambda/source/build``
    :param verbose: whether you want to suppress the output of cli commands
    :param skip_prompt: whether you want to skip the prompt before removing existing build folder
    :param printer: a callable to print messages, default to built-in print function
    """
    if verbose:
        printer(f"--- Building Lambda source artifacts using pip ...")
        printer(f"{path_bin_pip = !s}")
        printer(f"{path_setup_py_or_pyproject_toml = !s}")
        printer(f"{dir_lambda_source_build = !s}")
    clean_build_directory(
        dir_build=dir_lambda_source_build,
        folder_alias="lambda source build folder",
        skip_prompt=skip_prompt,
    )
    dir_workspace = path_setup_py_or_pyproject_toml.parent
    with temp_cwd(dir_workspace):
        args = [
            f"{path_bin_pip}",
            "install",
            f"{dir_workspace}",
            "--no-dependencies",
            f"--target={dir_lambda_source_build}",
        ]
        if verbose is False:
            args.append("--disable-pip-version-check")
            args.append("--quiet")
        subprocess.run(args, check=True)


def create_source_zip(
    dir_lambda_source_build: Path,
    path_source_zip: Path,
    verbose: bool = True,
    printer: T.Callable[[str], None] = print,
) -> str:
    """
    Create a zip archive of the Lambda source build directory and return its sha256 hash.
    """
    if verbose:
        printer(f"--- Creating Lambda source zip file ...")
        printer(f"{dir_lambda_source_build = !s}")
        printer(f"{path_source_zip = !s}")
    args = [
        "zip",
        f"{path_source_zip}",
        "-r",
        "-9",
    ]
    if verbose is False:
        args.append("-q")

    # Has to cd to the lambda source build dir to run the glob command
    with temp_cwd(dir_lambda_source_build):
        args.extend(glob.glob("*"))
        subprocess.run(args, check=True)

    source_sha256 = hashes.of_paths([dir_lambda_source_build])
    printer(f"{source_sha256 = }")
    return source_sha256


@dataclasses.dataclass
class SourceS3Layout:
    """
    AWS S3 layout configuration for storing Lambda source artifacts.

    :param s3dir_lambda: Example: ``s3://bucket/path/to/lambda/``

    Layout::

        ${s3dir_lambda}/source/0.1.1/source.zip
        ${s3dir_lambda}/source/0.1.2/source.zip
        ...
    """

    s3dir_lambda: S3Path = dataclasses.field()

    def get_s3path_source_zip(self, source_version: str) -> S3Path:
        """
        Lambda Function source code semantic version, example: ``"0.1.1"``.
        """
        return self.s3dir_lambda.joinpath(source_version, "source.zip")


def upload_source_artifacts(
    s3_client: "S3Client",
    source_version: str,
    source_sha256: str,
    path_source_zip: Path,
    s3dir_lambda: S3Path,
    metadata: dict[str, str] | None = OPT,
    tags: dict[str, str] | None = OPT,
    verbose: bool = True,
    printer: T.Callable[[str], None] = print,
) -> S3Path:
    """
    Upload the recently built Lambda source artifact from ``${dir_build}/source.zip``
    to S3 folder.

    :param bsm: boto session manager object
    :param source_version: lambda source code semantic version, example: ``"0.1.1"``
    :param source_sha256: sha256 hash of the source artifacts
    :param dir_build: example: ``/path/to/build/lambda``
    :param s3dir_lambda: example: ``s3://bucket/path/to/lambda/``
    :param metadata: S3 object metadata
    :param tags: S3 object tags

    :return: the S3 path of the uploaded ``source.zip`` file
    """
    if verbose:
        printer(f"--- Uploading Lambda source artifacts to S3 ...")
        printer(f"{source_version = }")
        printer(f"{source_sha256 = }")
        printer(f"{path_source_zip = !s}")
        printer(f"{s3dir_lambda.uri =}")
    source_s3_layout = SourceS3Layout(
        s3dir_lambda=s3dir_lambda,
    )
    s3path_source_zip = source_s3_layout.get_s3path_source_zip(
        source_version=source_version
    )
    if verbose:
        uri = s3path_source_zip.uri
        printer(f"Uploading Lambda source artifact to {uri}")
        url = s3path_source_zip.console_url
        printer(f"preview at {url}")
    extra_args = {"ContentType": "application/zip"}
    metadata_arg = {
        S3MetadataKeyEnum.source_sha256: source_sha256,
    }
    if isinstance(metadata, dict):
        metadata_arg.update(metadata)
    extra_args["Metadata"] = metadata_arg
    if isinstance(tags, dict):
        extra_args["Tagging"] = urlencode(tags)
    s3path_source_zip.upload_file(
        path=path_source_zip,
        overwrite=True,
        extra_args=extra_args,
        bsm=s3_client,
    )
    return s3path_source_zip
