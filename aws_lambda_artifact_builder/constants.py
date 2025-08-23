# -*- coding: utf-8 -*-

import enum


class S3MetadataKeyEnum(str, enum.Enum):
    """
    S3 Metadata Key Enum
    """

    source_sha256 = "source_sha256"
