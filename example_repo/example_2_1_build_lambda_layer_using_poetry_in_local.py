# -*- coding: utf-8 -*-

from settings import teardown_aws_lambda_artifact_builder, settings
import aws_lambda_artifact_builder.api as aws_lambda_artifact_builder

with aws_lambda_artifact_builder.DateTimeTimer(title="Total build time"):
    builder = aws_lambda_artifact_builder.PoetryBasedLambdaLayerLocalBuilder(
        path_bin_poetry=settings.path_bin_poetry,
        path_pyproject_toml=settings.path_pyproject_toml,
        credentials=settings.credentials,
        skip_prompt=True,
    )

    # Run the workflow in one line
    builder.run()

    # or run step by step
    # builder.step_1_preflight_check()
    # builder.step_2_prepare_environment()
    # builder.step_3_execute_build()
    # builder.step_4_finalize_artifacts()

teardown_aws_lambda_artifact_builder()
