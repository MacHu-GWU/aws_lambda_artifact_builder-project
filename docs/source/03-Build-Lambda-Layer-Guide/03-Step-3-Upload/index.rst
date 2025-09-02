Step 3: Upload Layer Zip to S3 Storage
==============================================================================
Upload your packaged Lambda layer zip file to S3 storage, making it accessible for AWS Lambda layer creation and deployment.


Overview
------------------------------------------------------------------------------
The upload step transfers the packaged layer zip file from your local build directory to S3 storage using an organized directory structure. This step makes your layer artifact available to AWS Lambda for layer creation while providing metadata for intelligent change detection.

**What This Step Does:**

- Uploads ``build/lambda/layer/layer.zip`` to organized S3 location
- Stores layer in temporary S3 path with timestamp-based naming
- Attaches manifest metadata for change detection and validation
- Provides AWS Console URLs for browser-based verification
- Prepares artifact for Lambda layer publication in Step 4


S3 Path Organization
------------------------------------------------------------------------------
The upload process uses a structured S3 path layout managed by :class:`~aws_lambda_artifact_builder.layer.foundation.LayerS3Layout`:

**S3 Directory Structure:**

.. code-block::

    s3://your-bucket/lambda/
    └── layer/
        ├── layer.zip                    # Temporary layer upload
        ├── 000001/                      # Version-specific manifests
        │   ├── requirements.txt         # pip manifest backup
        │   ├── poetry.lock              # Poetry manifest backup
        │   └── uv.lock                  # UV manifest backup
        ├── 000002/
        │   └── ...
        ├── last-requirements.txt        # Latest pip manifest reference
        ├── last-poetry.lock             # Latest Poetry manifest reference
        └── last-uv.lock                 # Latest UV manifest reference

**Path Components:**

- **Base Directory**: ``s3://bucket/lambda/`` (from ``s3dir_lambda`` parameter)
- **Temporary Layer**: ``layer/layer.zip`` for upload staging
- **Versioned Manifests**: ``layer/000001/`` directories with zero-padded version numbers  
- **Latest References**: ``layer/last-*.txt`` files for change detection in Step 4


Basic Usage
------------------------------------------------------------------------------
Use the :func:`~aws_lambda_artifact_builder.layer.upload.upload_layer_zip_to_s3` function to upload your layer:

.. code-block:: python

    from aws_lambda_artifact_builder.api import upload_layer_zip_to_s3, LayerBuildToolEnum
    from pathlib import Path
    from boto_session_manager import BotoSesManager
    from s3pathlib import S3Path

    # Configure AWS client and S3 paths
    bsm = BotoSesManager(profile_name="your-profile")
    s3dir_lambda = S3Path("s3://your-bucket/lambda/layers/").to_dir()

    # Upload the layer zip file
    upload_layer_zip_to_s3(
        s3_client=bsm.s3_client,
        path_pyproject_toml=Path("pyproject.toml"),
        s3dir_lambda=s3dir_lambda,
        layer_build_tool=LayerBuildToolEnum.uv,  # Match your build tool
        verbose=True,
    )

This uploads your layer and displays the S3 location and AWS Console URL.
