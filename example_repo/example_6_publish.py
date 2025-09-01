# -*- coding: utf-8 -*-

from pathlib import Path
from settings import bsm, s3dir_lambda, layer_name
from aws_lambda_artifact_builder.constants import LayerBuildToolEnum
from aws_lambda_artifact_builder.layer.publish import publish_layer_version

dir_here = Path(__file__).absolute().parent
path_pyproject_toml = dir_here.joinpath("pyproject.toml")

publish_layer_version(
    s3_client=bsm.s3_client,
    lambda_client=bsm.lambda_client,
    path_pyproject_toml=path_pyproject_toml,
    s3dir_lambda=s3dir_lambda,
    layer_build_tool=LayerBuildToolEnum.uv,
    layer_name=layer_name,
)
