.. image:: https://readthedocs.org/projects/aws-lambda-artifact-builder/badge/?version=latest
    :target: https://aws-lambda-artifact-builder.readthedocs.io/en/latest/
    :alt: Documentation Status

.. image:: https://github.com/MacHu-GWU/aws_lambda_artifact_builder-project/actions/workflows/main.yml/badge.svg
    :target: https://github.com/MacHu-GWU/aws_lambda_artifact_builder-project/actions?query=workflow:CI

.. .. image:: https://codecov.io/gh/MacHu-GWU/aws_lambda_artifact_builder-project/branch/main/graph/badge.svg
    :target: https://codecov.io/gh/MacHu-GWU/aws_lambda_artifact_builder-project

.. image:: https://img.shields.io/pypi/v/aws-lambda-artifact-builder.svg
    :target: https://pypi.python.org/pypi/aws-lambda-artifact-builder

.. image:: https://img.shields.io/pypi/l/aws-lambda-artifact-builder.svg
    :target: https://pypi.python.org/pypi/aws-lambda-artifact-builder

.. image:: https://img.shields.io/pypi/pyversions/aws-lambda-artifact-builder.svg
    :target: https://pypi.python.org/pypi/aws-lambda-artifact-builder

.. image:: https://img.shields.io/badge/✍️_Release_History!--None.svg?style=social&logo=github
    :target: https://github.com/MacHu-GWU/aws_lambda_artifact_builder-project/blob/main/release-history.rst

.. image:: https://img.shields.io/badge/⭐_Star_me_on_GitHub!--None.svg?style=social&logo=github
    :target: https://github.com/MacHu-GWU/aws_lambda_artifact_builder-project

------

.. image:: https://img.shields.io/badge/Link-API-blue.svg
    :target: https://aws-lambda-artifact-builder.readthedocs.io/en/latest/py-modindex.html

.. image:: https://img.shields.io/badge/Link-Install-blue.svg
    :target: `install`_

.. image:: https://img.shields.io/badge/Link-GitHub-blue.svg
    :target: https://github.com/MacHu-GWU/aws_lambda_artifact_builder-project

.. image:: https://img.shields.io/badge/Link-Submit_Issue-blue.svg
    :target: https://github.com/MacHu-GWU/aws_lambda_artifact_builder-project/issues

.. image:: https://img.shields.io/badge/Link-Request_Feature-blue.svg
    :target: https://github.com/MacHu-GWU/aws_lambda_artifact_builder-project/issues

.. image:: https://img.shields.io/badge/Link-Download-blue.svg
    :target: https://pypi.org/pypi/aws-lambda-artifact-builder#files


Welcome to ``aws_lambda_artifact_builder`` Documentation
==============================================================================
.. image:: https://aws-lambda-artifact-builder.readthedocs.io/en/latest/_static/aws_lambda_artifact_builder-logo.png
    :target: https://aws-lambda-artifact-builder.readthedocs.io/en/latest/

AWS Lambda Artifact Builder is a comprehensive Python library that solves the deployment challenges every team faces when building Lambda applications. It provides battle-tested solutions for both Lambda Layer creation and deployment package building across pip, Poetry, and UV dependency managers.

**Key Features:**

- **Multi-Tool Support**: Seamless integration with pip, Poetry, and UV dependency managers
- **Cross-Platform Builds**: Container-based builds ensuring Linux compatibility from any development platform
- **Private Repository Support**: Built-in AWS CodeArtifact and private PyPI server integration
- **Command Pattern Architecture**: Granular control with simple ``builder.run()`` interface
- **Enterprise Ready**: Intelligent change detection, automated cleanup, cross-account layer sharing
- **Complete Workflow**: End-to-end automation from dependency installation to AWS deployment

**The Problems It Solves:**

- Platform compatibility issues (Windows/macOS → Linux Lambda runtime)
- Dependency separation complexity (stable layers vs changing application code)
- Build reproducibility across development, CI, and production environments
- Private repository authentication and credential management
- Storage optimization and version management
- Enterprise deployment workflows

Usage Examples
------------------------------------------------------------------------------
**Lambda Source Artifacts (Deployment Packages):**

Build application code packages for Lambda function deployment:

- `example_1_build_lambda_source_using_pip_step_by_step.py <https://github.com/MacHu-GWU/aws_lambda_artifact_builder-project/blob/main/example_1_build_lambda_source_using_pip_step_by_step.py>`_: Step-by-step source building with pip
- `example_2_build_lambda_source_using_pip_all_in_one.py <https://github.com/MacHu-GWU/aws_lambda_artifact_builder-project/blob/main/example_2_build_lambda_source_using_pip_all_in_one.py>`_: All-in-one source building workflow

**Lambda Layer Artifacts:**

Build dependency layers for Lambda functions using different build tools:

**Common Setup:**

- `settings.py <https://github.com/MacHu-GWU/aws_lambda_artifact_builder-project/blob/main/example_repo/settings.py>`_: Shared configuration for all layer examples

**Pip Builder Examples:**

- `example_1_1_build_lambda_layer_using_pip_in_local.py <https://github.com/MacHu-GWU/aws_lambda_artifact_builder-project/blob/main/example_repo/example_1_1_build_lambda_layer_using_pip_in_local.py>`_: Local pip-based layer building
- `example_1_2_build_lambda_layer_using_pip_in_container.py <https://github.com/MacHu-GWU/aws_lambda_artifact_builder-project/blob/main/example_repo/example_1_2_build_lambda_layer_using_pip_in_container.py>`_: Container-based pip layer building

**Poetry Builder Examples:**

- `example_2_1_build_lambda_layer_using_poetry_in_local.py <https://github.com/MacHu-GWU/aws_lambda_artifact_builder-project/blob/main/example_repo/example_2_1_build_lambda_layer_using_poetry_in_local.py>`_: Local Poetry-based layer building
- `example_2_2_build_lambda_layer_using_poetry_in_container.py <https://github.com/MacHu-GWU/aws_lambda_artifact_builder-project/blob/main/example_repo/example_2_2_build_lambda_layer_using_poetry_in_container.py>`_: Container-based Poetry layer building

**UV Builder Examples:**

- `example_3_1_build_lambda_layer_using_uv_in_local.py <https://github.com/MacHu-GWU/aws_lambda_artifact_builder-project/blob/main/example_repo/example_3_1_build_lambda_layer_using_uv_in_local.py>`_: Local UV-based layer building
- `example_3_2_build_lambda_layer_using_uv_in_container.py <https://github.com/MacHu-GWU/aws_lambda_artifact_builder-project/blob/main/example_repo/example_3_2_build_lambda_layer_using_uv_in_container.py>`_: Container-based UV layer building

**Advanced Workflow Examples:**

- `example_4_package.py <https://github.com/MacHu-GWU/aws_lambda_artifact_builder-project/blob/main/example_repo/example_4_package.py>`_: Layer packaging with optimization and exclusions
- `example_5_upload.py <https://github.com/MacHu-GWU/aws_lambda_artifact_builder-project/blob/main/example_repo/example_5_upload.py>`_: S3 upload with organized artifact storage  
- `example_6_publish.py <https://github.com/MacHu-GWU/aws_lambda_artifact_builder-project/blob/main/example_repo/example_6_publish.py>`_: Lambda layer version publishing with change detection
- `example_7_workflow.py <https://github.com/MacHu-GWU/aws_lambda_artifact_builder-project/blob/main/example_repo/example_7_workflow.py>`_: **Complete end-to-end workflow** (Build → Package → Upload → Publish)


.. _install:

Install
------------------------------------------------------------------------------

``aws_lambda_artifact_builder`` is released on PyPI, so all you need is to:

.. code-block:: console

    $ pip install aws-lambda-artifact-builder

To upgrade to latest version:

.. code-block:: console

    $ pip install --upgrade aws-lambda-artifact-builder