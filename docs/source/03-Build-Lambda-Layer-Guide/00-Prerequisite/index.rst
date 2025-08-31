Prerequisites
==============================================================================
To use the AWS Lambda Artifact Builder Library for building Lambda layers, we require the following setup:


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


