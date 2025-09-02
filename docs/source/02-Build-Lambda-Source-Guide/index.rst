Build Lambda Source Guide
==============================================================================
Build, package, and deploy AWS Lambda source artifacts with proper packaging, versioning, and S3 storage.


Overview
------------------------------------------------------------------------------
The Lambda Source Guide covers building deployment packages for your Lambda functions using proper Python packaging. Unlike Lambda layers that contain dependencies, Lambda source artifacts contain your application code installed as a Python package, ensuring proper module discovery and import resolution.

**What Lambda Source Artifacts Are:**

Lambda source artifacts are deployment packages that contain your application code installed via pip. This approach ensures that:

- Python modules are properly discoverable within the Lambda runtime
- Package metadata and entry points are correctly configured
- Import paths work as expected in the Lambda execution environment

**Key Assumptions:**

- **Pip-based packaging**: Uses ``pip install`` to build source artifacts ensuring proper Python package installation
- **Embedded entry point**: Lambda entry point (``lambda_function.py`` with ``lambda_handler``) is included within your package structure, not as a separate file
- **No dependencies**: Source artifacts contain only your code; dependencies should be provided via Lambda layers

**3-Step Workflow:**

1. **Build**: Install your package using pip without dependencies
2. **Package**: Create compressed zip archive with maximum compression
3. **Upload**: Deploy to S3 with semantic versioning and integrity metadata


S3 Storage Structure
------------------------------------------------------------------------------
Lambda source artifacts are organized in S3 using semantic versioning:

**Directory Layout:**

.. code-block::

    s3://bucket/lambda/
    └── source/
        ├── 0.1.1/
        │   └── source.zip
        ├── 0.1.2/
        │   └── source.zip
        ├── 0.1.3/
        │   └── source.zip
        └── ...

**Benefits:**

- **Semantic Versioning**: Clear version management with ``major.minor.patch`` format
- **Immutable Artifacts**: Each version is stored separately and never overwritten
- **Integrity Verification**: SHA256 hashes stored in S3 metadata
- **Easy Rollbacks**: Previous versions remain available for quick deployment rollbacks


Basic Usage - Step by Step
------------------------------------------------------------------------------
Build Lambda source artifacts through three individual steps:

.. code-block:: python

    from pathlib import Path
    from s3pathlib import S3Path
    from boto_session_manager import BotoSesManager
    from aws_lambda_artifact_builder.api import (
        build_source_artifacts_using_pip,
        create_source_zip, 
        upload_source_artifacts,
    )

    # Project configuration
    project_root = Path.cwd()
    build_dir = project_root / "build" / "lambda" / "source" / "build"
    zip_path = project_root / "build" / "lambda" / "source" / "source.zip"

    # AWS configuration  
    bsm = BotoSesManager(profile_name="your-profile")
    s3dir_lambda = S3Path("s3://your-bucket/lambda/").to_dir()

    # Step 1: Build source artifacts using pip
    build_source_artifacts_using_pip(
        path_bin_pip=project_root / ".venv" / "bin" / "pip",
        path_setup_py_or_pyproject_toml=project_root / "pyproject.toml", 
        dir_lambda_source_build=build_dir,
        verbose=True,
        skip_prompt=True,
    )

    # Step 2: Create compressed zip archive
    source_sha256 = create_source_zip(
        dir_lambda_source_build=build_dir,
        path_source_zip=zip_path,
        verbose=True,
    )

    # Step 3: Upload to S3 with versioning
    upload_source_artifacts(
        s3_client=bsm.s3_client,
        source_version="0.1.1",
        source_sha256=source_sha256,
        path_source_zip=zip_path,
        s3dir_lambda=s3dir_lambda,
        verbose=True,
    )


Basic Usage - All-in-One
-------------------------
Use the simplified approach with automatic version extraction:

.. code-block:: python

    from pathlib import Path
    from s3pathlib import S3Path
    from boto_session_manager import BotoSesManager
    from aws_lambda_artifact_builder.source import build_package_upload_source_artifacts

    # Project and AWS configuration
    project_root = Path.cwd()
    bsm = BotoSesManager(profile_name="your-profile")
    s3dir_lambda = S3Path("s3://your-bucket/lambda/").to_dir()

    # All-in-one: Build → Package → Upload
    result = build_package_upload_source_artifacts(
        s3_client=bsm.s3_client,
        dir_project_root=project_root,
        s3dir_lambda=s3dir_lambda,
        verbose=True,
        skip_prompt=True,
    )

    print(f"✅ Version uploaded: {result.s3path_source_zip.uri}")
    print(f"🔐 SHA256: {result.source_sha256}")

**Requirements for All-in-One Approach:**

- Must use ``pyproject.toml`` (not ``setup.py``)
- Must have semantic version in ``[project].version``
- Assumes conventional build structure: ``build/lambda/source/build/``

Step 1: Build Source Artifacts
-------------------------------

Install your Python package as Lambda source artifacts using pip:

**Why pip install?**

Using ``pip install`` ensures:

- Proper Python package installation with correct module paths
- Entry points and package metadata are correctly configured  
- All modules are discoverable within the Lambda execution environment
- Import resolution works as expected (unlike simple file copying)

**Function Reference:**

.. code-block:: python

    build_source_artifacts_using_pip(
        path_bin_pip=Path(".venv/bin/pip"),              # Pip executable path
        path_setup_py_or_pyproject_toml=Path("pyproject.toml"),  # Package definition
        dir_lambda_source_build=Path("build/lambda/source/build"),  # Target directory
        verbose=True,                                    # Show detailed output
        skip_prompt=True,                               # Auto-clean existing build
        printer=print,                                  # Custom output function
    )

**Key Features:**

- **No Dependencies**: Uses ``--no-dependencies`` to exclude external packages
- **Target Installation**: Uses ``--target`` to install directly to build directory  
- **Clean Build**: Automatically cleans existing build directory for fresh installation
- **Workspace Context**: Runs pip install from package directory for proper context

Step 2: Package Source Artifacts  
---------------------------------

Create a compressed zip archive from the built source artifacts:

**Function Reference:**

.. code-block:: python

    source_sha256 = create_source_zip(
        dir_lambda_source_build=Path("build/lambda/source/build"),  # Built artifacts
        path_source_zip=Path("build/lambda/source/source.zip"),     # Output zip
        verbose=True,                                               # Show progress
        printer=print,                                              # Custom output
    )

**Key Features:**

- **Maximum Compression**: Uses zip level -9 for smallest possible file size
- **Integrity Verification**: Returns SHA256 hash of source directory
- **Root Structure**: Creates zip with all files in the root (no nested directories)
- **Complete Package**: Includes all installed package files and metadata

**Important Assumption:**

The Lambda entry point (``lambda_function.py`` with ``lambda_handler``) must be included within your installed package structure, not as a separate external file. Configure this in your ``pyproject.toml``:

.. code-block:: toml

    [project]
    name = "my-lambda-app"
    version = "0.1.1"

    [tool.setuptools.packages.find]
    where = ["."]
    include = ["my_lambda_app*"]

    # Ensure your package includes lambda_function.py
    [tool.setuptools.package-data]
    "my_lambda_app" = ["lambda_function.py"]

Step 3: Upload Source Artifacts
--------------------------------

Upload the packaged source artifacts to S3 with versioning and metadata:

**Function Reference:**

.. code-block:: python

    s3path_source_zip = upload_source_artifacts(
        s3_client=bsm.s3_client,                        # Boto3 S3 client
        source_version="0.1.1",                         # Semantic version
        source_sha256=source_sha256,                    # SHA256 hash from Step 2
        path_source_zip=Path("source.zip"),             # Local zip file
        s3dir_lambda=S3Path("s3://bucket/lambda/"),     # Base S3 directory
        metadata={"author": "developer"},               # Optional custom metadata
        tags={"environment": "prod"},                   # Optional S3 tags
        verbose=True,                                   # Show upload progress
        printer=print,                                  # Custom output function
    )

**Key Features:**

- **Semantic Versioning**: Each version gets its own S3 directory
- **Integrity Metadata**: SHA256 hash automatically added to S3 object metadata  
- **Custom Metadata**: Support for additional S3 object metadata
- **S3 Tags**: Optional tagging for resource management
- **Console URLs**: Provides AWS Console links for browser verification
- **Overwrite Protection**: Allows overwriting existing versions if needed

**Upload Output:**

.. code-block:: text

    --- Uploading Lambda source artifacts to S3 ...
    source_version = '0.1.1'
    source_sha256 = 'abc123...'
    Uploading Lambda source artifact to s3://bucket/lambda/source/0.1.1/source.zip
    preview at https://s3.console.aws.amazon.com/s3/object/bucket?prefix=lambda/source/0.1.1/source.zip

Complete Example
----------------

Here's a comprehensive example showing both approaches:

.. code-block:: python

    from pathlib import Path
    from s3pathlib import S3Path
    from boto_session_manager import BotoSesManager
    from aws_lambda_artifact_builder.source import (
        build_source_artifacts_using_pip,
        create_source_zip,
        upload_source_artifacts,
        build_package_upload_source_artifacts,
    )

    # Project setup
    project_root = Path.cwd()
    
    # AWS setup
    bsm = BotoSesManager(profile_name="your-profile")
    bucket = f"{bsm.aws_account_alias}-{bsm.aws_region}-artifacts"
    s3dir_lambda = S3Path(f"s3://{bucket}/lambda/").to_dir()

    print("🚀 Approach 1: Step-by-step with full control")
    
    # Define build paths
    build_dir = project_root / "build" / "lambda" / "source" / "build"
    zip_path = project_root / "build" / "lambda" / "source" / "source.zip"
    
    # Step 1: Build
    print("🔨 Building source artifacts...")
    build_source_artifacts_using_pip(
        path_bin_pip=project_root / ".venv" / "bin" / "pip",
        path_setup_py_or_pyproject_toml=project_root / "pyproject.toml",
        dir_lambda_source_build=build_dir,
        verbose=True,
        skip_prompt=True,
    )
    
    # Step 2: Package  
    print("📦 Creating zip archive...")
    source_sha256 = create_source_zip(
        dir_lambda_source_build=build_dir,
        path_source_zip=zip_path,
        verbose=True,
    )
    
    # Step 3: Upload
    print("⬆️ Uploading to S3...")
    s3path = upload_source_artifacts(
        s3_client=bsm.s3_client,
        source_version="0.1.1",
        source_sha256=source_sha256,
        path_source_zip=zip_path,
        s3dir_lambda=s3dir_lambda,
        metadata={"build_type": "manual", "author": "developer"},
        tags={"environment": "production", "team": "backend"},
        verbose=True,
    )
    
    print(f"✅ Step-by-step upload complete: {s3path.uri}")
    print(f"🔐 SHA256: {source_sha256}")

    print("\n🚀 Approach 2: All-in-one with automatic versioning")
    
    # All-in-one approach (extracts version from pyproject.toml)
    result = build_package_upload_source_artifacts(
        s3_client=bsm.s3_client,
        dir_project_root=project_root,
        s3dir_lambda=s3dir_lambda,
        verbose=True,
        skip_prompt=True,
    )
    
    print(f"✅ All-in-one upload complete: {result.s3path_source_zip.uri}")
    print(f"🔐 SHA256: {result.source_sha256}")
    print(f"🌐 Console: {result.s3path_source_zip.console_url}")

AWS Configuration
-----------------

**Required S3 Permissions:**

.. code-block:: json

    {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "s3:PutObject",
                    "s3:PutObjectAcl",
                    "s3:GetObject"
                ],
                "Resource": "arn:aws:s3:::your-bucket/lambda/source/*"
            }
        ]
    }

**S3 Bucket Setup:**

Ensure your S3 bucket exists and is properly configured:

.. code-block:: bash

    # Create bucket (if needed)
    aws s3 mb s3://your-lambda-artifacts-bucket

    # Verify access
    aws s3 ls s3://your-lambda-artifacts-bucket/lambda/source/

Project Structure Requirements
------------------------------

**For step-by-step approach:**

Your project can use either ``setup.py`` or ``pyproject.toml``:

.. code-block::

    my-lambda-project/
    ├── pyproject.toml (or setup.py)
    ├── .venv/
    │   └── bin/
    │       └── pip
    ├── my_lambda_app/
    │   ├── __init__.py
    │   ├── lambda_function.py  # Must be in package
    │   └── handlers.py
    └── build/  # Created during build
        └── lambda/
            └── source/
                ├── build/      # pip install target
                └── source.zip  # Final artifact

**For all-in-one approach:**

Must use ``pyproject.toml`` with version specified:

.. code-block:: toml

    [project]
    name = "my-lambda-app"
    version = "0.1.1"  # Required for automatic versioning
    description = "My AWS Lambda application"

    [tool.setuptools.packages.find]
    where = ["."]
    include = ["my_lambda_app*"]

**Lambda Entry Point Setup:**

Ensure your ``lambda_function.py`` is included in your package:

.. code-block:: python

    # my_lambda_app/lambda_function.py
    def lambda_handler(event, context):
        """AWS Lambda entry point"""
        return {
            'statusCode': 200,
            'body': 'Hello from Lambda!'
        }

Error Handling
--------------

**Common Issues:**

**Missing Virtual Environment:**

.. code-block:: text

    FileNotFoundError: .venv/bin/pip not found

**Solution**: Create and activate a virtual environment:

.. code-block:: bash

    python -m venv .venv
    source .venv/bin/activate
    pip install -e .

**Package Not Found:**

.. code-block:: text

    ERROR: Could not find a version that satisfies the requirement ./

**Solutions**:
- Ensure ``pyproject.toml`` or ``setup.py`` exists and is properly configured
- Verify package name and structure are correct
- Check that your package is installable: ``pip install -e .``

**Entry Point Missing:**

.. code-block:: text

    ImportError: cannot import name 'lambda_handler'

**Solution**: Ensure ``lambda_function.py`` is included in your package structure and properly configured in packaging files.

**S3 Upload Failed:**

.. code-block:: text

    botocore.exceptions.NoCredentialsError: Unable to locate credentials

**Solutions**:
- Configure AWS credentials: ``aws configure``
- Verify S3 bucket exists and permissions are correct
- Check AWS profile name matches your boto session manager configuration

Integration with Lambda Layers
-------------------------------

Lambda source artifacts work best when combined with Lambda layers:

**Architecture:**

- **Lambda Layer**: Contains dependencies (from Layer Guide)
- **Lambda Source**: Contains your application code (this guide)
- **Lambda Function**: References both layer ARN and source artifact

**Deployment Pattern:**

.. code-block:: python

    # 1. Create Lambda layer with dependencies (see Layer Guide)
    layer_arn = "arn:aws:lambda:region:account:layer:my-deps:1"
    
    # 2. Build and upload source artifacts (this guide)  
    result = build_package_upload_source_artifacts(...)
    
    # 3. Create/update Lambda function
    lambda_client.create_function(
        FunctionName='my-lambda',
        Runtime='python3.9',
        Role=role_arn,
        Handler='my_lambda_app.lambda_function.lambda_handler',
        Code={'S3Bucket': bucket, 'S3Key': 'lambda/source/0.1.1/source.zip'},
        Layers=[layer_arn],  # Dependencies from layer
    )

Next Steps
----------

After building and uploading source artifacts:

**Deploy to Lambda:**

.. code-block:: python

    # Update Lambda function with new source version
    lambda_client.update_function_code(
        FunctionName='my-lambda',
        S3Bucket=s3path_source_zip.bucket,
        S3Key=s3path_source_zip.key,
    )

**Version Management:**

.. code-block:: bash

    # List all source versions
    aws s3 ls s3://bucket/lambda/source/ --recursive

    # Download specific version for inspection
    aws s3 cp s3://bucket/lambda/source/0.1.1/source.zip ./source-0.1.1.zip

**CI/CD Integration:**

The deterministic SHA256 hashing makes this workflow ideal for automated deployment pipelines where source artifacts are built and uploaded as part of continuous integration.

API Reference
-------------

.. autofunction:: aws_lambda_artifact_builder.source.build_source_artifacts_using_pip

.. autofunction:: aws_lambda_artifact_builder.source.create_source_zip

.. autofunction:: aws_lambda_artifact_builder.source.upload_source_artifacts

.. autofunction:: aws_lambda_artifact_builder.source.build_package_upload_source_artifacts

.. autoclass:: aws_lambda_artifact_builder.source.SourceS3Layout
   :members:
   :show-inheritance:

.. autoclass:: aws_lambda_artifact_builder.source.BuildSourceArtifactsResult
   :members:
   :show-inheritance:
