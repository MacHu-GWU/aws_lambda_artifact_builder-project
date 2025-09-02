# -*- coding: utf-8 -*-

from settings import teardown_aws_lambda_artifact_builder, settings
import aws_lambda_artifact_builder.api as aws_lambda_artifact_builder

LayerBuildToolEnum = aws_lambda_artifact_builder.LayerBuildToolEnum

zipper = aws_lambda_artifact_builder.LambdaLayerZipper(
    path_pyproject_toml=settings.path_pyproject_toml,
    # build_tool=LayerBuildToolEnum.pip,
    # build_tool=LayerBuildToolEnum.poetry,
    build_tool=LayerBuildToolEnum.uv,
)
zipper.run()

teardown_aws_lambda_artifact_builder()
