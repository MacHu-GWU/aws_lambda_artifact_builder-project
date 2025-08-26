# -*- coding: utf-8 -*-

import typing as T
import glob
import subprocess
import dataclasses
from pathlib import Path

from func_args.api import OPT
from s3pathlib import S3Path

from .vendor.better_pathlib import temp_cwd
from .vendor.hashes import hashes

from .constants import ZFILL, S3MetadataKeyEnum
from .utils import (
    clean_build_directory,
)

if T.TYPE_CHECKING:  # pragma: no cover
    from mypy_boto3_s3.client import S3Client


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
