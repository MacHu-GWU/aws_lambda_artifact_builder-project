All-in-One Lambda Layer Workflow
==============================================================================
Execute the complete Lambda layer creation and deployment process in a single unified interface.


Overview
------------------------------------------------------------------------------
The all-in-one workflow combines all four steps of Lambda layer creation into a single class, providing both unified execution and granular control. This approach is ideal for automated deployments, CI/CD pipelines, and users who want a streamlined experience.

**Complete Workflow in One Interface:**

The :class:`~aws_lambda_artifact_builder.layer.workflow.LambdaLayerBuildPackageUploadAndPublishWorkflow` class orchestrates:

1. **Build** - :ref:`Layer-Step-1:` using containerized environments
2. **Package** - :ref:`Layer-Step-2` into optimized zip archives
3. **Upload** - :ref:`Layer-Step-3` to S3 storage with versioning
4. **Publish** - :ref:`Layer-Step-4` as versioned Lambda layers with intelligent change detection

**Key Benefits:**

- **Unified Interface**: Single class manages the entire layer lifecycle
- **Multi-Tool Support**: Automatically selects pip, Poetry, or UV builders
- **Intelligent Publishing**: Only creates new layer versions when dependencies change
- **Flexible Execution**: Run complete workflow or individual steps
- **Containerized Builds**: Ensures AWS Lambda compatibility across platforms


When to Use the All-in-One Workflow
------------------------------------------------------------------------------
**Ideal For:**

- **CI/CD Pipelines**: Automated layer deployment in build systems
- **Simplified Workflows**: Users who prefer single-command execution
- **Complete Deployments**: When you need to go from source to published layer
- **Production Environments**: Consistent, repeatable layer deployments

**Individual Steps Are Better For:**

- **Development/Testing**: When you need to inspect artifacts between steps
- **Custom Workflows**: When you need different configurations per step
- **Debugging**: When troubleshooting specific build, package, upload, or publish issues
- **Learning**: When understanding each step of the layer creation process


Basic Usage
------------------------------------------------------------------------------
- `settings <https://github.com/MacHu-GWU/aws_lambda_artifact_builder-project/blob/main/example_repo/settings.py>`_: example settings.
- `example_7_workflow <https://github.com/MacHu-GWU/aws_lambda_artifact_builder-project/blob/main/example_repo/example_7_workflow.py>`_: all-in-one workflow example.
