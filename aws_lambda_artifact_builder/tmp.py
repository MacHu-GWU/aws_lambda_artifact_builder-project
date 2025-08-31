# -*- coding: utf-8 -*-

"""
This module implements the automation to manage AWS lambda artifacts, versions, etc ...
"""

import typing as T
import subprocess
from pathlib import Path

import aws_lambda_layer.api as aws_lambda_layer
import aws_console_url.api as aws_console_url
from ..vendor.emoji import Emoji
from ..vendor.hashes import hashes

from ..logger import logger


if T.TYPE_CHECKING:  # pragma: no cover
    import pyproject_ops.api as pyops
    from boto_session_manager import BotoSesManager
    from s3pathlib import S3Path


def build_lambda_source(
    pyproject_ops: "pyops.PyProjectOps",
    verbose: bool = True,
) -> T.Tuple[str, Path]:  # pragma: no cover
    """
    Wrapper of ``aws_lambda_layer.api.build_source_artifacts``.

    Build lambda source artifacts locally and return source code sha256 and zip file path.
    It will NOT upload the artifacts to S3.

    :param pyproject_ops: ``PyProjectOps`` object.

    :return: tuple of two items: (source code sha256, zip file path)
    """
    path_lambda_function = pyproject_ops.dir_lambda_app.joinpath("lambda_function.py")
    source_sha256, path_source_zip = aws_lambda_layer.build_source_artifacts(
        path_setup_py_or_pyproject_toml=pyproject_ops.path_pyproject_toml,
        package_name=pyproject_ops.package_name,
        path_lambda_function=path_lambda_function,
        dir_build=pyproject_ops.dir_build_lambda,
        use_pathlib=True,
        verbose=verbose,
    )
    return source_sha256, path_source_zip


def deploy_layer(
    bsm_devops: "BotoSesManager",
    pyproject_ops: "pyops.PyProjectOps",
    layer_name: str,
    s3dir_lambda: "S3Path",
    tags: T.Dict[str, str],
) -> T.Optional[aws_lambda_layer.LayerDeployment]:  # pragma: no cover
    """
    Build layer locally, and upload layer artifacts to S3, then publish lambda layer.

    This function doesn't have any logging, it can make the final function shorter.

    :param bsm_devops: the devops AWS Account ``BotoSesManager`` object.
    :param pyproject_ops: ``PyProjectOps`` object.
    :param layer_name: Lambda layer name.
    :param s3dir_lambda: the S3 folder to store all lambda layer version artifacts.
    :param tags: optional AWS resource tags.
    """
    return aws_lambda_layer.deploy_layer(
        bsm=bsm_devops,
        layer_name=layer_name,
        python_versions=[
            f"python{pyproject_ops.python_version}",
        ],
        path_requirements=pyproject_ops.path_requirements,
        dir_build=pyproject_ops.dir_build_lambda,
        s3dir_lambda=s3dir_lambda,
        bin_pip=pyproject_ops.path_venv_bin_pip,
        quiet=True,
        tags=tags,
    )


def deploy_layer_using_docker(
    bsm_devops: "BotoSesManager",
    pyproject_ops: "pyops.PyProjectOps",
    layer_name: str,
    s3dir_lambda: "S3Path",
    tags: T.Dict[str, str],
    is_arm: bool,
): # pragma: no cover
    """
    Build layer locally using docker, and upload layer artifacts to S3, then publish lambda layer.

    :param bsm_devops: the devops AWS Account ``BotoSesManager`` object.
    :param pyproject_ops: ``PyProjectOps`` object.
    :param layer_name: Lambda layer name.
    :param s3dir_lambda: the S3 folder to store all lambda layer version artifacts.
    :param tags: optional AWS resource tags.
    :param is_arm: is True, then build for ARM architecture, otherwise build for x86_64.
    """
    latest_layer_version = aws_lambda_layer.get_latest_layer_version(
        bsm=bsm_devops, layer_name=layer_name
    )

    if aws_lambda_layer.is_current_layer_the_same_as_latest_one(
        bsm=bsm_devops,
        latest_layer_version=latest_layer_version,
        path_requirements=pyproject_ops.path_requirements,
        s3dir_lambda=s3dir_lambda,
    ):
        return None

    python_version = pyproject_ops.python_version
    container_name = "lbd_layer_build"
    if is_arm:
        image_uri = f"public.ecr.aws/sam/build-python{python_version}:latest-arm64"
        platform = "linux/arm64"
    else:
        image_uri = f"public.ecr.aws/sam/build-python{python_version}:latest-x86_64"
        platform = "linux/amd64"

    dir_here = Path(__file__).absolute().parent
    path_build_layer_in_container_py_source = dir_here / "_build_layer_in_container.py"
    path_build_layer_in_container_py_temp = pyproject_ops.dir_project_root.joinpath(
        path_build_layer_in_container_py_source.name
    )
    path_build_layer_in_container_py_temp.write_text(
        path_build_layer_in_container_py_source.read_text()
    )
    args = [
        "docker",
        "run",
        "--rm",
        "--name",
        container_name,
        "--platform",
        platform,
        "--mount",
        f"type=bind,source={pyproject_ops.dir_project_root},target=/var/task",
        image_uri,
        "python",
        path_build_layer_in_container_py_source.name,
    ]
    subprocess.run(args)
    path_build_layer_in_container_py_temp.remove_if_exists()

    layer_sha256 = hashes.of_bytes(pyproject_ops.path_requirements.read_bytes())

    (
        s3path_tmp_layer_zip,
        s3path_tmp_layer_requirements_txt,
    ) = aws_lambda_layer.upload_layer_artifacts(
        bsm=bsm_devops,
        path_requirements=pyproject_ops.path_requirements,
        layer_sha256=layer_sha256,
        dir_build=pyproject_ops.dir_build_lambda,
        s3dir_lambda=s3dir_lambda,
        tags=tags,
    )

    (
        layer_version,
        layer_version_arn,
        s3path_layer_zip,
        s3path_layer_requirements_txt,
    ) = aws_lambda_layer.publish_layer(
        bsm=bsm_devops,
        layer_name=layer_name,
        python_versions=[
            f"python{pyproject_ops.python_version}",
        ],
        dir_build=pyproject_ops.dir_build_lambda,
        s3dir_lambda=s3dir_lambda,
    )

    return aws_lambda_layer.LayerDeployment(
        layer_sha256=layer_sha256,
        layer_name=layer_name,
        layer_version=layer_version,
        layer_version_arn=layer_version_arn,
        s3path_layer_zip=s3path_layer_zip,
        s3path_layer_requirements_txt=s3path_layer_requirements_txt,
    )


def grant_layer_permission(
    bsm_devops: "BotoSesManager",
    workload_bsm_list: T.List["BotoSesManager"],
    layer_deployment: aws_lambda_layer.LayerDeployment,
) -> T.List[str]:  # pragma: no cover
    """
    Grant cross account Lambda layer permission.

    :param bsm_devops: the devops AWS Account ``BotoSesManager`` object.
    :param workload_bsm_list: list of all workload AWS Accounts ``BotoSesManager`` objects.
    :param layer_deployment: the lambda layer deployment object.
    """
    principal_list = list()
    for bsm_workload in workload_bsm_list:
        if (bsm_devops.aws_account_id == bsm_workload.aws_account_id) and (
            bsm_devops.aws_region == bsm_workload.aws_region
        ):
            continue
        aws_lambda_layer.grant_layer_permission(
            bsm=bsm_devops,
            layer_name=layer_deployment.layer_name,
            version_number=layer_deployment.layer_version,
            principal=bsm_workload.aws_account_id,
        )
        principal_list.append(bsm_workload.aws_account_id)
    return principal_list


def explain_layer_deployment(
    bsm_devops: "BotoSesManager",
    layer_deployment: T.Optional[aws_lambda_layer.LayerDeployment],
):  # pragma: no cover
    """
    Print helpful information about the layer deployment.

    :param bsm_devops: the devops AWS Account ``BotoSesManager`` object.
    :param layer_deployment: the lambda layer deployment object.
    """
    if layer_deployment is None:
        logger.info(
            f"{Emoji.red_circle} don't publish layer, "
            f"the current requirements.txt is the same as the one "
            f"of the latest lambda layer."
        )
    else:
        aws_console = aws_console_url.AWSConsole.from_bsm(bsm=bsm_devops)
        logger.info(f"published a new layer version: {layer_deployment.layer_version}")
        logger.info(f"published layer arn: {layer_deployment.layer_version_arn}")
        layer_console_url = aws_console.awslambda.filter_layers(
            layer_deployment.layer_name
        )
        logger.info(f"preview deployed layer at {layer_console_url}")
        console_url = layer_deployment.s3path_layer_zip.console_url
        logger.info(f"preview layer.zip at {console_url}")
        console_url = layer_deployment.s3path_layer_requirements_txt.console_url
        logger.info(f"preview requirements.txt at {console_url}")
