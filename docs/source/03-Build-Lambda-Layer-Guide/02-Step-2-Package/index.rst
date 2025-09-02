Step 2: Package Dependencies into Lambda Layer
==============================================================================
Transform your built dependencies into a properly structured, optimized zip file ready for AWS Lambda deployment.


Overview
------------------------------------------------------------------------------
The packaging step transforms the dependencies installed during Step 1 into a Lambda-compatible zip file. This process standardizes the directory structure regardless of which build tool (pip, Poetry, or UV) was used, and optimizes the layer size by excluding unnecessary packages.

**What This Step Does:**

- Standardizes directory structure to Lambda's required ``python/`` layout
- Creates compressed zip file with maximum compression (-9)  
- Excludes AWS runtime-provided packages (boto3, botocore) to reduce size
- Excludes development tools (pytest, setuptools) not needed at runtime
- Produces deployment-ready ``build/lambda/layer/layer.zip`` artifact


Directory Structure Transformation
------------------------------------------------------------------------------
Different build tools install packages to different locations, but Lambda layers require a standardized structure. The packaging step handles this transformation:

**Build Tool-Specific Handling:**

.. list-table::
   :header-rows: 1

   * - Build Tool
     - Source Location  
     - Target Location
     - Action Required
   * - pip
     - ``build/lambda/layer/artifacts/python/``
     - ``build/lambda/layer/artifacts/python/``
     - None (already correct)
   * - Poetry
     - ``build/lambda/layer/repo/.venv/lib/python3.x/site-packages/``
     - ``build/lambda/layer/artifacts/python/``
     - Move packages
   * - UV  
     - ``build/lambda/layer/repo/.venv/lib/python3.x/site-packages/``
     - ``build/lambda/layer/artifacts/python/``
     - Move packages


Basic Usage
------------------------------------------------------------------------------
Create a :class:`~aws_lambda_artifact_builder.layer.package.LambdaLayerZipper` instance and call its ``run()`` method:

.. code-block:: python

    from aws_lambda_artifact_builder.api import LambdaLayerZipper, LayerBuildToolEnum
    from pathlib import Path

    zipper = LambdaLayerZipper(
        path_pyproject_toml=Path("pyproject.toml"),
        build_tool=LayerBuildToolEnum.uv,  # or poetry, pip
    )
    zipper.run()

This creates ``build/lambda/layer/layer.zip`` in your project root.


Package Exclusions
------------------------------------------------------------------------------
By default, the packager excludes packages that are either provided by AWS Lambda runtime or not needed at runtime:

**Default Exclusions:**

- **AWS Runtime Provided**: ``boto3``, ``botocore``, ``s3transfer``, ``urllib3``
- **Build Tools**: ``setuptools``, ``pip``, ``wheel``, ``twine``
- **Development Tools**: ``pytest``, ``_pytest``

**Custom Exclusions:**

You can specify additional packages to exclude:

.. code-block:: python

    zipper = LambdaLayerZipper(
        path_pyproject_toml=Path("pyproject.toml"),
        build_tool=LayerBuildToolEnum.uv,
        ignore_package_list=[
            "boto3",      # Default exclusions
            "pytest",     # Default exclusions  
            "mypy",       # Custom exclusion
            "black",      # Custom exclusion
        ]
    )

**Override Default Exclusions:**

To use only your custom exclusions (not the defaults):

.. code-block:: python

    zipper = LambdaLayerZipper(
        path_pyproject_toml=Path("pyproject.toml"),
        build_tool=LayerBuildToolEnum.poetry,
        ignore_package_list=["mypy", "black"],  # Only these will be excluded
    )


Configuration Options
------------------------------------------------------------------------------
The :class:`~aws_lambda_artifact_builder.layer.package.LambdaLayerZipper` class supports several configuration options:

.. code-block:: python

    zipper = LambdaLayerZipper(
        path_pyproject_toml=Path("pyproject.toml"),     # Required: Project root
        build_tool=LayerBuildToolEnum.poetry,           # Required: Build tool used
        ignore_package_list=["mypy", "black"],          # Optional: Custom exclusions
        verbose=True,                                   # Optional: Show zip progress
    )

Parameters:

- ``path_pyproject_toml``: Path to your project's ``pyproject.toml`` file
- ``build_tool``: Which build tool was used in Step 1 (:class:`~aws_lambda_artifact_builder.constants.LayerBuildToolEnum`)
- ``ignore_package_list``: Additional packages to exclude (None uses defaults)
- ``verbose``: Whether to show detailed zip creation progress (default: True)


Complete Example
------------------------------------------------------------------------------
Here's a complete example showing the packaging step in context:

.. code-block:: python

    from pathlib import Path
    from aws_lambda_artifact_builder.api import LambdaLayerZipper, LayerBuildToolEnum

    # Define project paths
    project_root = Path.cwd()
    pyproject_path = project_root / "pyproject.toml"

    # Configure the zipper
    zipper = LambdaLayerZipper(
        path_pyproject_toml=pyproject_path,
        build_tool=LayerBuildToolEnum.uv,
        ignore_package_list=[
            # Include defaults plus custom exclusions
            "boto3", "botocore", "pytest",  # Defaults
            "mypy", "black", "ruff",        # Custom dev tools
        ],
        verbose=True,
    )

    # Package the dependencies
    print("Packaging dependencies into layer zip...")
    zipper.run()
    print("✅ Layer package created: build/lambda/layer/layer.zip")


Output Artifact
------------------------------------------------------------------------------
The packaging step produces a single artifact:

``build/lambda/layer/layer.zip``
  Compressed layer archive containing the ``python/`` directory with all dependencies.
  This file is ready for upload to S3 and Lambda layer publication.

**Zip File Contents:**

.. code-block::

    layer.zip
    └── python/
        ├── package1/
        │   ├── __init__.py
        │   └── module.py
        ├── package2/
        │   └── ...
        └── package1-1.0.0.dist-info/
            └── ...


Optimization Features
------------------------------------------------------------------------------
The packaging process includes several optimizations:

**Maximum Compression:**
  Uses zip compression level -9 for smallest possible file size.

**Selective Exclusions:**
  Removes packages using glob patterns (``python/package_name*``) to catch all related files.

**Runtime Optimization:**
  Excludes packages provided by Lambda runtime to avoid version conflicts and reduce cold start time.

**Development Tool Removal:**
  Strips testing frameworks and build tools that add unnecessary weight.


Integration with Build Step
------------------------------------------------------------------------------
The packaging step automatically detects which build tool was used and handles the appropriate directory transformations. Ensure you specify the same ``build_tool`` that was used in Step 1:

.. code-block:: python

    # If you built with Poetry in Step 1
    builder = LambdaLayerBuilder(build_tool=LayerBuildToolEnum.poetry, ...)
    builder.run()

    # Use the same build_tool in Step 2
    zipper = LambdaLayerZipper(build_tool=LayerBuildToolEnum.poetry, ...)
    zipper.run()
