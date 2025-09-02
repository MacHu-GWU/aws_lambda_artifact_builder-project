
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

A simple tool that automates the process of building and deploying AWS Lambda `source <https://docs.aws.amazon.com/lambda/latest/dg/python-package.html>`_ and `layer <https://docs.aws.amazon.com/lambda/latest/dg/chapter-layers.html>`_ artifacts. It supports the following build tools:

- `pip <https://pip.pypa.io/>`_
- `poetry <https://python-poetry.org/>`_
- `uv <https://docs.astral.sh/uv/>`_

.. _install:

Install
------------------------------------------------------------------------------

``aws_lambda_artifact_builder`` is released on PyPI, so all you need is to:

.. code-block:: console

    $ pip install aws-lambda-artifact-builder

To upgrade to latest version:

.. code-block:: console

    $ pip install --upgrade aws-lambda-artifact-builder
