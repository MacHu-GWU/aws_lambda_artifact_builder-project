# -*- coding: utf-8 -*-

from settings import teardown_aws_lambda_artifact_builder, settings
import aws_lambda_artifact_builder.api as aws_lambda_artifact_builder

with aws_lambda_artifact_builder.DateTimeTimer(title="Total build time"):
    builder = aws_lambda_artifact_builder.PipBasedLambdaLayerContainerBuilder(
        path_pyproject_toml=settings.path_pyproject_toml,
        py_ver_major=settings.py_ver_major,
        py_ver_minor=settings.py_ver_minor,
        credentials=settings.credentials,
        is_arm=False,
    )
    builder.run()

teardown_aws_lambda_artifact_builder()
