Build Lambda Layer Overview
==============================================================================


Project Configuration
------------------------------------------------------------------------------
You must use a ``pyproject.toml`` file as your project configuration to declare dependencies. This file should be compatible with one of the following dependency management tools:

- `pip <https://pip.pypa.io/>`_: Standard Python package installer
- `poetry <https://python-poetry.org/>`_: Modern dependency management and packaging tool
- `uv <https://docs.astral.sh/uv/>`_: Fast Python package resolver and installer

The automation provided by this library is built on top of these tools and leverages their existing functionality.

**Reference Documentation**

- `pyproject.toml Python Official Guide <https://packaging.python.org/en/latest/guides/writing-pyproject-toml/>`_
- `pyproject.toml with pip Guide <https://pip.pypa.io/en/latest/reference/build-system/pyproject-toml/>`_
- `pyproject.toml with poetry Guide <https://python-poetry.org/docs/pyproject/>`_
- `pyproject.toml with uv Guide <https://docs.astral.sh/uv/concepts/projects/config/>`_


Local Path Layout
------------------------------------------------------------------------------
The AWS Lambda Artifact Builder Library follows a standardized directory structure for organizing Lambda layer build artifacts. This :class:`~aws_lambda_artifact_builder.layer.common.LayerPathLayout` ensures consistent builds across different projects and deployment environments.

**Directory Structure Overview**

Assuming your Git repository root is located at ``${dir_project_root}/``, the Lambda layer-related paths are organized as follows:

.. code-block:: text

    ${dir_project_root}/                           # Project root directory
    ├── pyproject.toml                             # Project configuration file
    ├── poetry.lock                                # Poetry lock file (if using Poetry)
    ├── uv.lock                                    # UV lock file (if using UV)
    ├── requirements.txt                           # Generated requirements file
    └── build/lambda/layer/                        # Lambda layer build directory
        ├── layer.zip                              # Final Lambda layer zip file
        ├── repo/                                  # Temporary repository copy
        │   ├── pyproject.toml                     # Copied project configuration
        │   ├── poetry.lock                        # Copied lock file (Poetry)
        │   └── uv.lock                            # Copied lock file (UV)
        └── artifacts/                             # Layer packaging directory
            └── python/                            # AWS Lambda required subdirectory

**Path Descriptions**

- **Project Root** (``${dir_project_root}/``)
    The main directory containing your project files and Git repository.

- **Configuration Files**
    - ``pyproject.toml``: Primary project configuration defining dependencies
    - ``poetry.lock`` / ``uv.lock``: Lock files ensuring reproducible builds
    - ``requirements.txt``: Generated requirements file for pip-based builds

- **Build Directory** (``build/lambda/layer/``)
    Temporary build workspace that gets cleaned before each build:
    
    - ``layer.zip``: The final packaged Lambda layer ready for deployment
    - ``repo/``: Isolated copy of project files to prevent conflicts with your working directory
    - ``artifacts/``: Staging area containing all files to be included in the layer
    - ``artifacts/python/``: AWS Lambda's required subdirectory where all Python packages are installed

**Important Notes**

- The ``build/`` directory is temporary and safe to delete
- The ``artifacts/python/`` structure is required by AWS Lambda for Python layers
- Lock files are copied to the ``repo/`` directory to ensure dependency versions remain consistent during containerized builds
- This layout supports both local and Docker-based build processes


.. _local-builder-and-container-builder:

Local Builder and Container Builder
------------------------------------------------------------------------------
The library provides two approaches for building Lambda layers:

- **Local Builders** (:class:`~aws_lambda_artifact_builder.layer.common.BasedLambdaLayerLocalBuilder`): Fast builds directly on your machine, ideal for Linux environments
- **Container Builders** (:class:`~aws_lambda_artifact_builder.layer.common.BasedLambdaLayerContainerBuilder`): Docker-based builds ensuring AWS Lambda runtime compatibility across platforms

Container builders execute local builder logic inside AWS SAM build images, guaranteeing platform compatibility without duplicating build code.


.. _lambda-layer-local-builder:

Lambda Layer Local Builder
------------------------------------------------------------------------------
Local builders follow a standard three-step workflow implemented by :class:`~aws_lambda_artifact_builder.layer.common.BasedLambdaLayerLocalBuilder`:

1. **Build Information**: :meth:`~aws_lambda_artifact_builder.layer.common.BasedLambdaLayerLocalBuilder.step_01_print_info`
2. **Environment Setup**: :meth:`~aws_lambda_artifact_builder.layer.common.BasedLambdaLayerLocalBuilder.step_02_setup_build_dir`
3. **Tool-Specific Installation**: Implemented by subclasses

**Implementation Example**

See :class:`~aws_lambda_artifact_builder.layer.poetry_builder.PoetryBasedLambdaLayerLocalBuilder` which demonstrates:

- :meth:`~aws_lambda_artifact_builder.layer.poetry_builder.PoetryBasedLambdaLayerLocalBuilder.step_03_prepare_poetry_stuff`
- :meth:`~aws_lambda_artifact_builder.layer.poetry_builder.PoetryBasedLambdaLayerLocalBuilder.step_04_run_poetry_install`

**Public API**

Use high-level functions like :func:`~aws_lambda_artifact_builder.layer.poetry_builder.build_layer_artifacts_using_poetry_in_local` instead of command classes directly.


.. _lambda-layer-container-builder:

Lambda Layer Container Builder
------------------------------------------------------------------------------
Container builders execute local builder logic inside Docker containers to ensure Lambda runtime compatibility across platforms.

**Three-Step Process**

:class:`~aws_lambda_artifact_builder.layer.common.BasedLambdaLayerContainerBuilder` orchestrates:

1. **Script Setup**: :meth:`~aws_lambda_artifact_builder.layer.common.BasedLambdaLayerContainerBuilder.step_01_copy_build_script`
2. **Credential Management**: :meth:`~aws_lambda_artifact_builder.layer.common.BasedLambdaLayerContainerBuilder.step_02_setup_private_repository_credential`
3. **Docker Execution**: :meth:`~aws_lambda_artifact_builder.layer.common.BasedLambdaLayerContainerBuilder.step_03_docker_run`

**Container Script Example**

The build script `_build_lambda_layer_using_poetry_in_container.py <https://github.com/MacHu-GWU/aws_lambda_artifact_builder-project/blob/main/aws_lambda_artifact_builder/layer/_build_lambda_layer_using_poetry_in_container.py>`_ demonstrates containerized execution:

- Environment validation (ensures ``/var/task`` location)
- Tool installation within container
- Credential loading via :meth:`~aws_lambda_artifact_builder.layer.common.Credentials.load`
- Local builder execution

**Public API**

Use functions like :func:`~aws_lambda_artifact_builder.layer.poetry_builder.build_layer_artifacts_using_poetry_in_container` for containerized builds.
