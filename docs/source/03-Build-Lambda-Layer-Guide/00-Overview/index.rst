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
The :class:`~aws_lambda_artifact_builder.layer.common.BasedLambdaLayerLocalBuilder` serves as the foundation for all tool-specific local build implementations. Rather than forcing each dependency management tool to reinvent the wheel, this base class captures the common workflow that every layer build process follows.

Every local builder executes a consistent three-step dance, regardless of whether you're using pip, poetry, or uv. The process begins by displaying build information to give you visibility into what's happening - showing the build directory location, tool versions, and configuration paths. This transparency helps debug issues when builds don't work as expected.

The second step involves setting up a pristine build environment. The builder creates a clean, temporary workspace that's isolated from your main project directory. This isolation prevents conflicts with your working files and ensures reproducible builds by starting with a known clean state every time.

Finally, the actual dependency installation happens using the specific tool's commands and conventions. This is where pip builders differ from poetry builders, and where uv builders have their own unique approach. The base class provides the framework, while each tool-specific subclass implements its particular installation strategy.

**The Three-Step Workflow:**

- **Build Information**: Display paths, versions, and configuration details
- **Environment Setup**: Create clean, isolated temporary build directories  
- **Dependency Installation**: Execute tool-specific commands to install packages

The beauty of this design is that you don't interact with these command classes directly. Instead, the library provides simple public API functions that hide all the complexity behind clean, minimal interfaces. These functions typically only require a few essential parameters - the path to your pip executable, your project configuration file, and perhaps some optional settings.

A typical example would be :func:`~aws_lambda_artifact_builder.layer.pip_builder.build_layer_artifacts_using_pip_in_local`, which handles all the orchestration while presenting a straightforward function call interface.


.. _lambda-layer-container-builder:

Lambda Layer Container Builder
------------------------------------------------------------------------------
