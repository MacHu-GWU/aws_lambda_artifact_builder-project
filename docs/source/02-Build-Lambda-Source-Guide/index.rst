.. _Build-Lambda-Source-Guide:

Build Lambda Source Guide
==============================================================================
Build and deploy AWS Lambda source artifacts using proper Python packaging with pip install.


Overview
------------------------------------------------------------------------------
Lambda source artifacts contain your application code (not dependencies) packaged as a proper Python package. This ensures correct module discovery and import resolution within the Lambda runtime environment.

**Key Concept: pip install Approach**

We use ``pip install`` to build source artifacts because:

- **Proper Module Paths**: Ensures Python modules are discoverable within Lambda runtime
- **Package Metadata**: Correctly configures entry points and package information
- **Import Resolution**: Guarantees imports work as expected (unlike simple file copying)

**Critical Requirement: Embedded Entry Point**

Your Lambda entry point (``lambda_function.py`` containing ``lambda_handler``) **must be inside your Python package**, not a separate external file. This is essential because:

- Lambda needs to import your handler from the installed package
- External files outside the package structure are not importable
- Proper packaging ensures the handler is discoverable at runtime


Example Package Structure
------------------------------------------------------------------------------
Your project should look like this:

.. code-block::

    my-lambda-project/
    ├── pyproject.toml
    ├── my_lambda_app/
    │   ├── __init__.py
    │   ├── lambda_function.py  # ← Must be inside the package
    │   └── business_logic.py
    └── .venv/

**Correct pyproject.toml Configuration:**

.. code-block:: toml

    [project]
    name = "my-lambda-app"
    version = "0.1.1"

    [tool.setuptools.packages.find]
    where = ["."]
    include = ["my_lambda_app*"]

**Lambda Handler Inside Package:**

.. code-block:: python

    # my_lambda_app/lambda_function.py
    def lambda_handler(event, context):
        """AWS Lambda entry point - MUST be inside the package"""
        return {'statusCode': 200, 'body': 'Hello from Lambda!'}


S3 Storage Organization
------------------------------------------------------------------------------
Lambda source artifacts are organized using :class:`~aws_lambda_artifact_builder.source.SourceS3Layout` with semantic versioning:

.. code-block::

    s3://bucket/lambda/
    └── source/
        ├── 0.1.1/
        │   └── source.zip
        ├── 0.1.2/
        │   └── source.zip
        └── 0.2.0/
            └── source.zip

**S3 Layout Benefits:**

- **Semantic Versioning**: Clear version management with ``major.minor.patch``
- **Immutable Artifacts**: Each version stored separately, never overwritten
- **Easy Rollbacks**: Previous versions remain available
- **Integrity Verification**: SHA256 hashes stored in S3 metadata


Usage Examples
------------------------------------------------------------------------------
See complete working examples:

**Step-by-Step Approach:**
  `example_1_build_lambda_source_using_pip_step_by_step.py <https://github.com/MacHu-GWU/aws_lambda_artifact_builder-project/blob/main/example_1_build_lambda_source_using_pip_step_by_step.py>`_

  - Individual control over build, package, and upload steps
  - Works with both ``setup.py`` and ``pyproject.toml``
  - Full customization of metadata and S3 tags

**All-in-One Approach:**
  `example_2_build_lambda_source_using_pip_all_in_one.py <https://github.com/MacHu-GWU/aws_lambda_artifact_builder-project/blob/main/example_2_build_lambda_source_using_pip_all_in_one.py>`_

  - Single function call for complete workflow
  - Automatically extracts version from ``pyproject.toml``
  - Assumes conventional build directory structure


3-Step Workflow
------------------------------------------------------------------------------
The Lambda source build process follows three steps:

**1. Build with pip install**

.. code-block:: python

    build_source_artifacts_using_pip(
        path_bin_pip=Path(".venv/bin/pip"),
        path_setup_py_or_pyproject_toml=Path("pyproject.toml"),
        dir_lambda_source_build=Path("build/lambda/source/build"),
        skip_prompt=True,  # Clean existing build automatically
    )

**Key Features:**

- Uses ``pip install --no-dependencies --target`` for clean installation
- Installs only your code (dependencies come from Lambda layers)
- Ensures proper Python package structure

**2. Create Compressed Archive**

.. code-block:: python

    source_sha256 = create_source_zip(
        dir_lambda_source_build=Path("build/lambda/source/build"),
        path_source_zip=Path("build/lambda/source/source.zip"),
    )

**Key Features:**

- Maximum compression (zip level -9) for smallest file size
- Returns SHA256 hash for integrity verification
- Creates deployment-ready zip archive

**3. Upload to S3 with Versioning**

.. code-block:: python

    s3path = upload_source_artifacts(
        s3_client=s3_client,
        source_version="0.1.1",
        source_sha256=source_sha256,
        path_source_zip=Path("source.zip"),
        s3dir_lambda=S3Path("s3://bucket/lambda/"),
    )

**Key Features:**

- Semantic versioning with dedicated S3 directories  
- SHA256 metadata attached to S3 objects
- AWS Console URLs for easy verification


Common Issues
------------------------------------------------------------------------------
**Entry Point Not Found**

.. code-block:: text

    ImportError: cannot import name 'lambda_handler'

**Solution**: Ensure ``lambda_function.py`` is inside your package, not in project root.

**Package Installation Failed**

.. code-block:: text

    ERROR: Could not find a version that satisfies the requirement ./

**Solution**: Verify your ``pyproject.toml`` is properly configured and your package is installable with ``pip install -e .``


Integration with Lambda Layers
------------------------------------------------------------------------------
Lambda source artifacts work best with Lambda layers:

- **Lambda Source**: Your application code (this guide)
- **Lambda Layer**: Dependencies (see :ref:`Build-Lambda-Layer-Guide`)
- **Lambda Function**: References both source S3 location and layer ARN
