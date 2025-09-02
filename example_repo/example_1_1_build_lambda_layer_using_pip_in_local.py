# -*- coding: utf-8 -*-

from settings import teardown_aws_lambda_artifact_builder, settings
import aws_lambda_artifact_builder.api as aws_lambda_artifact_builder

with aws_lambda_artifact_builder.DateTimeTimer(title="Total build time"):
    builder = aws_lambda_artifact_builder.PipBasedLambdaLayerLocalBuilder(
        path_bin_pip=settings.path_bin_pip,
        path_pyproject_toml=settings.path_pyproject_toml,
        credentials=settings.credentials,
        skip_prompt=True,
    )
    builder.run()

teardown_aws_lambda_artifact_builder()
