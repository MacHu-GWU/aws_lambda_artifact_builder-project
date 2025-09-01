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
The library provides two complementary approaches to building Lambda layers, each designed to address different development environments and runtime compatibility needs.

The core challenge in Lambda layer creation is ensuring that dependencies built on your development machine will work correctly in the AWS Lambda runtime environment. Since most developers work on macOS or Windows laptops while Lambda runs on Linux, we need strategies to bridge this compatibility gap.

**The Local Builder Approach**

The :class:`~aws_lambda_artifact_builder.layer.common.BasedLambdaLayerLocalBuilder` assumes your host environment is already compatible with AWS Lambda runtime - essentially, you're working on a Linux system or one that closely matches Lambda's environment. This approach installs dependencies directly using your local tools like pip, poetry, or uv, then packages them into the layer structure.

The trade-off is speed and simplicity for compatibility assurance. If you're on the right platform, local builds are significantly faster since there's no Docker overhead involved.

**The Container Builder Solution**

The :class:`~aws_lambda_artifact_builder.layer.common.BasedLambdaLayerContainerBuilder` addresses the reality that most developers don't work on Linux. Instead of trying to make your Mac or Windows machine compatible with Lambda, it brings Lambda's environment to you through Docker containers.

Container builders execute the build process inside official AWS SAM build images that precisely match the Lambda runtime environment. This approach guarantees that what you build locally will work identically when deployed to Lambda, regardless of your host operating system or architecture.

**How Container Builders Work**

Rather than duplicating all the build logic, container builders wrap the existing local builder logic. The process works by packaging the local build steps into Python scripts, then executing those scripts inside the appropriate Docker container. Meanwhile, the container builder handles the orchestration:

- Mounting your project files and credentials into the container
- Configuring the container environment for authentication  
- Managing the Docker lifecycle and volume mappings

**The Design Benefits**

This separation creates a clean architectural boundary that makes the entire system more maintainable. The core build logic lives in local builders where it's easy to test and debug directly on Linux machines. The container builders are essentially thin wrappers that handle Docker orchestration without duplicating business logic.

This design means that when you need to add support for a new dependency management tool, you primarily focus on the local builder implementation. The container wrapper comes almost for free, inheriting all the functionality while adding cross-platform compatibility.


.. _lambda-layer-local-builder:

Lambda Layer Local Builder
------------------------------------------------------------------------------
