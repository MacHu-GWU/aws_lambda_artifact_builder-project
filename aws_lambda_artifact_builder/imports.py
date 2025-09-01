# -*- coding: utf-8 -*-

from soft_deps.api import MissingDependency

try:
    from s3pathlib import S3Path
except ImportError as e:
    S3Path = MissingDependency("s3pathlib")

try:
    import simple_aws_lambda.api as simple_aws_lambda
except ImportError as e:
    simple_aws_lambda = MissingDependency("simple_aws_lambda")
