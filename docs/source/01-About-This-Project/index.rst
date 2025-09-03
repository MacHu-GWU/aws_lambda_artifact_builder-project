About This Project
==============================================================================


Project Overview
------------------------------------------------------------------------------
AWS Lambda Artifact Builder is a Python library that solves the deployment challenges every Python team faces when building Lambda applications. After years of working with Lambda in production environments, I recognized that teams repeatedly solve the same problems independently: platform compatibility issues, dependency management complexity, and enterprise deployment workflows.

This project provides battle-tested solutions through a Command Pattern architecture that handles both Lambda Layer creation and deployment package building across pip, Poetry, and UV dependency managers.

.. seealso::

    Better tested best practices:

    - `AWS Lambda Python Package Deployment Ultimate Guide <https://github.com/MacHu-GWU/aws_lambda_artifact_builder-project/blob/main/.claude/aws-lambda-python-package-deployment-ultimate-guide.md>`_
    - `AWS Lambda Layer for Python Ultimate Guide <https://github.com/MacHu-GWU/aws_lambda_artifact_builder-project/blob/main/.claude/aws-lambda-layer-for-python-ultimate-guide.md>`_


Why This Project Exists
------------------------------------------------------------------------------
**The Core Problem**: Modern Python tools (Poetry, UV, pip) don't naturally align with Lambda's deployment requirements. Teams spend weeks building custom solutions for:

- Platform compatibility (Windows/macOS → Linux)
- Dependency separation (layers vs application code)  
- Private repository integration
- Build reproducibility across environments
- Enterprise workflows (cross-account sharing, cleanup)

**The Solution**: Instead of every team solving these problems from scratch, this library provides proven patterns that work reliably in production.


Key Features
------------------------------------------------------------------------------
- **Multi-Tool Support**: Seamless integration with pip, Poetry, and UV
- **Cross-Platform Builds**: Container-based builds ensuring Linux compatibility
- **Private Repositories**: Built-in AWS CodeArtifact and private PyPI support
- **Command Pattern Architecture**: Granular control with ``builder.run()`` simplicity
- **Enterprise Ready**: Change detection, automated cleanup, cross-account sharing


Further Reading
------------------------------------------------------------------------------
For comprehensive implementation details, see:

- :ref:`Build-Lambda-Source-Guide`: Complete guide to Lambda deployment package creation
- :ref:`Build-Lambda-Layer-Guide`: In-depth Lambda Layer building strategies

These guides provide the theoretical foundation and detailed patterns implemented by this library.
