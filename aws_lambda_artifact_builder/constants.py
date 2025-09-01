# -*- coding: utf-8 -*-

import enum


ZFILL = 6


class S3MetadataKeyEnum(str, enum.Enum):
    """
    S3 Metadata Key Enum
    """

    source_sha256 = "source_sha256"


class LayerBuildToolEnum(str, enum.Enum):
    """
    Layer Build Tool Enum
    """

    pip = "pip"
    poetry = "poetry"
    uv = "uv"
