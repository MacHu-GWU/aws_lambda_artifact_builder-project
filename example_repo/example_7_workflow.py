# -*- coding: utf-8 -*-

from settings import teardown_aws_lambda_artifact_builder, settings
import aws_lambda_artifact_builder.api as aws_lambda_artifact_builder

LayerBuildToolEnum = aws_lambda_artifact_builder.LayerBuildToolEnum
workflow = aws_lambda_artifact_builder.LambdaLayerBuildPackageUploadAndPublishWorkflow(
    layer_name=settings.layer_name,
    py_ver_major=settings.py_ver_major,
    py_ver_minor=settings.py_ver_minor,
    credentials=settings.credentials,
    is_arm=settings.is_arm,
    path_pyproject_toml=settings.path_pyproject_toml,
    s3dir_lambda=settings.s3dir_lambda,
    s3_client=settings.bsm.s3_client,
    lambda_client=settings.bsm.lambda_client,
    # layer_build_tool=LayerBuildToolEnum.pip,
    # layer_build_tool=LayerBuildToolEnum.poetry,
    layer_build_tool=LayerBuildToolEnum.uv,
    ignore_package_list=None,
    publish_layer_version_kwargs=None,
    verbose=True,
)

# Run the workflow in one line
workflow.run()

# Or run step by step
# workflow.step_1_build()
# workflow.step_2_package()
# workflow.step_3_upload()
# workflow.step_4_publish()

teardown_aws_lambda_artifact_builder()
