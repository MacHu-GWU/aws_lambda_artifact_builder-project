# -*- coding: utf-8 -*-

from aws_lambda_artifact_builder import api


def test():
    _ = api


if __name__ == "__main__":
    from aws_lambda_artifact_builder.tests import run_cov_test

    run_cov_test(
        __file__,
        "aws_lambda_artifact_builder.api",
        preview=False,
    )
