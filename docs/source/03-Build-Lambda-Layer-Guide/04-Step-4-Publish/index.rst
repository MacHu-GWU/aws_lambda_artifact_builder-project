Step 4: Publish Versioned Lambda Layer
==============================================================================
Create versioned AWS Lambda layers with intelligent change detection, ensuring new layer versions are only published when dependencies have actually changed.


Overview
------------------------------------------------------------------------------
The publish step is the final phase of the layer creation workflow, transforming your uploaded S3 artifacts into versioned AWS Lambda layers. This step features intelligent change detection that compares dependency manifests to avoid creating unnecessary layer versions when dependencies haven't changed.

**What This Step Does:**

- Creates new Lambda layer versions from uploaded S3 artifacts
- Performs intelligent change detection using dependency manifest comparison
- Validates upload consistency and build environment before publishing
- Stores versioned manifest backups for future change detection
- Returns deployment information for integration with other systems
- Automatically increments layer version numbers


Publication Workflow
------------------------------------------------------------------------------
The publish step follows a systematic 2-phase workflow with comprehensive validation:

**Phase 1: Preflight Checks**

1. **Layer Zip Validation**: Verify the layer.zip file exists in S3 temp storage
2. **Consistency Check**: Ensure uploaded zip matches current local manifest  
3. **Change Detection**: Compare local manifest with latest published version

**Phase 2: Publication**

1. **Layer Version Creation**: Publish new Lambda layer version via AWS API
2. **Manifest Backup**: Store dependency manifest for future change detection

This workflow ensures that layers are only published when necessary and that all artifacts are consistent.


Basic Usage
------------------------------------------------------------------------------
Use the :class:`~aws_lambda_artifact_builder.layer.publish.LambdaLayerVersionPublisher` class to publish your layer:

.. code-block:: python

    from aws_lambda_artifact_builder.api import LambdaLayerVersionPublisher, LayerBuildToolEnum
    from pathlib import Path
    from boto_session_manager import BotoSesManager
    from s3pathlib import S3Path

    # Configure AWS clients and paths
    bsm = BotoSesManager(profile_name="your-profile")
    s3dir_lambda = S3Path("s3://your-bucket/lambda/layers/").to_dir()

    # Create and run the publisher
    publisher = LambdaLayerVersionPublisher(
        s3_client=bsm.s3_client,
        lambda_client=bsm.lambda_client,
        path_pyproject_toml=Path("pyproject.toml"),
        s3dir_lambda=s3dir_lambda,
        layer_build_tool=LayerBuildToolEnum.uv,
        layer_name="my-lambda-layer",
        verbose=True,
    )
    
    layer_deployment = publisher.run()
    print(f"✅ Published layer version {layer_deployment.layer_version}")


Intelligent Change Detection
------------------------------------------------------------------------------
The publish step's key feature is intelligent change detection that prevents unnecessary layer version creation:

**How Change Detection Works:**

1. **Manifest Comparison**: Compares current local dependency manifest with the manifest from the latest published layer version
2. **Deterministic Requirements**: Assumes manifests contain exact versions and hashes (not loose constraints)
3. **Skip Publication**: If manifests are identical, publication is skipped with an explanatory message
4. **Proceed with Changes**: If manifests differ, a new layer version is created

**Deterministic vs Non-Deterministic Manifests:**

.. code-block:: text

    # ✅ Good (Deterministic) - Enables change detection
    requests==2.31.0 \
        --hash=sha256:58cd2187c01e70e6e26505bca751777aa9f2ee0b7f4300988b709f44e013003f
    urllib3==2.0.4 \
        --hash=sha256:8d22f86aae8ef5e410d4f539fde9ce6b2c87b6b0c22d2e8ffeef5d49efcaee4c

    # ❌ Bad (Non-Deterministic) - Cannot reliably detect changes  
    requests  # No version pinning
    urllib3>=1.0  # Loose constraint

**Change Detection Scenarios:**

- **First Publication**: No previous layer exists → Publishes new version
- **Dependencies Changed**: Manifest content differs → Publishes new version  
- **No Changes**: Manifest content identical → Skips publication
- **Missing Manifest**: Previous manifest not found → Publishes new version


Publication Output
------------------------------------------------------------------------------
During publishing, the system provides detailed progress information:

.. code-block:: text

    --- Start publish Lambda layer workflow
    --- Step 1 - Flight Check
    --- Step 1.1 - Verify layer.zip exists in S3 at s3://bucket/lambda/layers/temp/layer-20241201123045.zip...
    ✅ Layer zip file found in S3.
    --- Step 1.2 - Validate layer.zip consistency with manifest
    ✅ Layer zip file is consistent with current manifest.
    --- Step 1.3 - Check if dependencies have changed since last publication
    ✅ Dependencies have changed - proceeding with publishing.
    --- Step 2 - Publish Lambda Layer Version
    --- Step 2.1 - Publish new Lambda layer version via API
    Successfully published layer version: 3
    Layer version ARN: arn:aws:lambda:us-east-1:123456789012:layer:my-layer:3
    --- Step 2.2 - Upload dependency manifest to S3
    Manifest stored at: s3://bucket/lambda/layers/published/manifest-v3.txt
    Console URL: https://s3.console.aws.amazon.com/s3/object/bucket?prefix=lambda/layers/published/manifest-v3.txt


LayerDeployment Response
------------------------------------------------------------------------------
The ``run()`` method returns a :class:`~aws_lambda_artifact_builder.layer.publish.LayerDeployment` object containing deployment details:

.. code-block:: python

    layer_deployment = publisher.run()
    
    # Access deployment information
    print(f"Layer Name: {layer_deployment.layer_name}")
    print(f"Version: {layer_deployment.layer_version}")  
    print(f"ARN: {layer_deployment.layer_version_arn}")
    print(f"Manifest: {layer_deployment.s3path_manifest.uri}")

    # Use in Lambda function configuration
    lambda_client.update_function_configuration(
        FunctionName="my-function",
        Layers=[layer_deployment.layer_version_arn]
    )


Error Handling
------------------------------------------------------------------------------
The publish step includes comprehensive error handling for common issues:

**Missing Layer Zip:**

.. code-block:: text

    FileNotFoundError: Layer zip file s3://bucket/layers/temp/layer.zip does not exist!
    Please run the upload step first to create the layer.zip in S3.

**Solution**: Run Step 3 (Upload) to upload the layer zip file to S3.

**Inconsistent Upload:**

.. code-block:: text

    ValueError: Layer zip file s3://bucket/layers/temp/layer.zip is inconsistent with current manifest!
    The uploaded layer.zip corresponds to a different dependency state.

**Solutions**:
- Re-run Step 3 (Upload) to sync the layer.zip with current dependencies
- Or re-run Step 2 (Package) if local zip file is outdated

**No Changes Detected:**

.. code-block:: text

    ValueError: Dependencies unchanged since last publication - skipping

**This is expected behavior**: The system detected that dependencies haven't changed since the last published version, so no new layer version is needed.

**AWS Permission Denied:**

.. code-block:: text

    botocore.exceptions.ClientError: User is not authorized to perform: lambda:PublishLayerVersion

**Solution**: Ensure your AWS credentials have the required Lambda permissions.
