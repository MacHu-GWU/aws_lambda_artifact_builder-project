.. _release_history:

Release and Version History
==============================================================================


x.y.z (Backlog)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**Features and Improvements**

**Minor Improvements**

**Bugfixes**

**Miscellaneous**


0.1.5 (2025-09-04)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**Bugfixes**

- Fix manifest check logic in ``LambdaLayerVersionPublisher`` to treat missing manifest as changed. The fix in 0.1.4 was incorrect.


0.1.4 (2025-09-04)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**Bugfixes**

- Fix manifest check logic in ``LambdaLayerVersionPublisher`` to treat missing manifest as changed, ensuring correct layer publishing behavior (this fix implementation is wrong)
- Add preflight checks for required build files (requirements.txt, poetry.lock, uv.lock) in pip, poetry, and uv builders


0.1.3 (2025-09-04)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**Bugfixes**

- Fix bug in ``_build`` scripts that used development install logic instead of production install logic for ``aws_lambda_artifact_builder`` dependency


0.1.2 (2025-09-04)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**Major Architecture Refactoring**

- **Command Pattern Implementation**: Refactored from functional API to Command Pattern architecture for better extensibility and customization
- **4-Step Workflow**: Standardized build process across all tools (Preflight Check → Prepare Environment → Execute Build → Finalize Artifacts)
- **Enhanced Builder Classes**: New base classes ``BasedLambdaLayerLocalBuilder`` and ``BasedLambdaLayerContainerBuilder`` with consistent interfaces

**New Features**

- **Multi-Tool Support**: Added UV builder alongside existing pip and Poetry builders
- **All-in-One Workflow**: New ``LambdaLayerBuildPackageUploadAndPublishWorkflow`` class for complete layer lifecycle management
- **Layer Packaging**: New ``LambdaLayerZipper`` class with intelligent package exclusions and optimization
- **Enhanced Logging**: Integrated ``BaseLogger`` for detailed build process visibility
- **Private Repository Support**: Improved credential handling for AWS CodeArtifact and private PyPI servers

**Builder Enhancements**

- **Pip Builder**: ``PipBasedLambdaLayerLocalBuilder`` and ``PipBasedLambdaLayerContainerBuilder`` with step-by-step execution
- **Poetry Builder**: ``PoetryBasedLambdaLayerLocalBuilder`` and ``PoetryBasedLambdaLayerContainerBuilder`` with lock file support
- **UV Builder**: ``UVBasedLambdaLayerLocalBuilder`` and ``UVBasedLambdaLayerContainerBuilder`` with ultra-fast dependency resolution

**Documentation Improvements**

- **Complete Guide Restructure**: Updated all documentation to reflect Command Pattern architecture
- **Usage Examples**: Comprehensive example collection covering all builders and workflows
- **Architecture Documentation**: Detailed explanation of 4-step workflow and Command Pattern benefits

**Public APIs**

- ``aws_lambda_artifact_builder.api.ZFILL``
- ``aws_lambda_artifact_builder.api.S3MetadataKeyEnum``
- ``aws_lambda_artifact_builder.api.LayerBuildToolEnum``
- ``aws_lambda_artifact_builder.api.write_bytes``
- ``aws_lambda_artifact_builder.api.is_match``
- ``aws_lambda_artifact_builder.api.copy_source_for_lambda_deployment``
- ``aws_lambda_artifact_builder.api.prompt_to_confirm_before_remove_dir``
- ``aws_lambda_artifact_builder.api.clean_build_directory``
- ``aws_lambda_artifact_builder.api.SourcePathLayout``
- ``aws_lambda_artifact_builder.api.SourceS3Layout``
- ``aws_lambda_artifact_builder.api.BuildSourceArtifactsResult``
- ``aws_lambda_artifact_builder.api.build_source_artifacts_using_pip``
- ``aws_lambda_artifact_builder.api.create_source_zip``
- ``aws_lambda_artifact_builder.api.upload_source_artifacts``
- ``aws_lambda_artifact_builder.api.build_package_upload_source_artifacts``
- ``aws_lambda_artifact_builder.api.Credentials``
- ``aws_lambda_artifact_builder.api.LayerPathLayout``
- ``aws_lambda_artifact_builder.api.LayerS3Layout``
- ``aws_lambda_artifact_builder.api.LayerManifestManager``
- ``aws_lambda_artifact_builder.api.BasedLambdaLayerLocalBuilder``
- ``aws_lambda_artifact_builder.api.BasedLambdaLayerContainerBuilder``
- ``aws_lambda_artifact_builder.api.PipBasedLambdaLayerLocalBuilder``
- ``aws_lambda_artifact_builder.api.PipBasedLambdaLayerContainerBuilder``
- ``aws_lambda_artifact_builder.api.PoetryBasedLambdaLayerLocalBuilder``
- ``aws_lambda_artifact_builder.api.PoetryBasedLambdaLayerContainerBuilder``
- ``aws_lambda_artifact_builder.api.UVBasedLambdaLayerLocalBuilder``
- ``aws_lambda_artifact_builder.api.UVBasedLambdaLayerContainerBuilder``
- ``aws_lambda_artifact_builder.api.move_to_dir_python``
- ``aws_lambda_artifact_builder.api.create_layer_zip_file``
- ``aws_lambda_artifact_builder.api.LambdaLayerZipper``
- ``aws_lambda_artifact_builder.api.upload_layer_zip_to_s3``
- ``aws_lambda_artifact_builder.api.LambdaLayerVersionPublisher``
- ``aws_lambda_artifact_builder.api.LambdaLayerBuildPackageUploadAndPublishWorkflow``
- ``aws_lambda_artifact_builder.api.temp_cwd``
- ``aws_lambda_artifact_builder.api.hashes``
- ``aws_lambda_artifact_builder.api.DateTimeTimer``


0.1.1 (2025-08-23)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
- Reserve PyPI package name.
