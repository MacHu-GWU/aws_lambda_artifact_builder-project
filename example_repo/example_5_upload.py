# -*- coding: utf-8 -*-

from pathlib import Path
from settings import bsm, s3dir_lambda
from aws_lambda_artifact_builder.constants import LayerBuildToolEnum
from aws_lambda_artifact_builder.layer.upload import upload_layer_zip_to_s3

dir_here = Path(__file__).absolute().parent
path_pyproject_toml = dir_here.joinpath("pyproject.toml")

upload_layer_zip_to_s3(
    s3_client=bsm.s3_client,
    path_pyproject_toml=path_pyproject_toml,
    s3dir_lambda=s3dir_lambda,
    layer_build_tool=LayerBuildToolEnum.uv,
    verbose=True,
)
