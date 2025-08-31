Pip Builder
==============================================================================
The Pip Builder provides Lambda layer creation using pip's ``--target`` installation method. This approach works with pre-resolved ``requirements.txt`` files and supports both local and containerized builds.


Why Use Pip Builder
------------------------------------------------------------------------------
Pip Builder offers the simplest path to Lambda layer creation since pip is universally available with every Python installation. However, its lack of sophisticated dependency resolution means it works best when combined with other tools that handle the complex dependency management, leaving pip to focus on what it does reliably: installing packages to a target directory.

**Advantages:**

- **Universal availability** - pip is included with every Python installation
- **No bootstrap required** - no need to install additional dependency management tools  
- **Simple workflow** - straightforward pip install with target directory
- **Well-established** - mature tooling with extensive community support

**Limitations:**

- **Non-deterministic** - pip lacks robust dependency resolution compared to Poetry/UV
- **Sequential installation** - slower performance with many dependencies
- **Requires pre-resolved dependencies** - best used with ``requirements.txt`` exported from Poetry/UV

**Recommended workflow:** Use Poetry or UV to resolve dependencies, export to ``requirements.txt``, then use Pip Builder for installation.


How Pip Builder Works  
------------------------------------------------------------------------------
The core mechanism is remarkably straightforward: pip reads your requirements.txt file and installs each package directly into the Lambda-compatible directory structure using the ``--target`` flag. This bypasses virtual environments and places packages exactly where AWS Lambda expects to find them.

.. code-block:: bash

    pip install -r requirements.txt --target ./build/lambda/layer/artifacts/python/

**Key Steps:**

1. Reads dependencies from ``requirements.txt`` file
2. Installs packages to ``artifacts/python/`` directory using ``pip install --target``  
3. Optionally removes unnecessary packages (e.g., boto3, botocore)
4. Creates ``layer.zip`` ready for Lambda deployment


Build Options
------------------------------------------------------------------------------
You can choose between local and containerized builds depending on your development workflow and compatibility requirements. Local builds are faster for iteration (if you work on a Linux machine), while container builds guarantee your layer will work identically in the AWS Lambda runtime environment.

**Local Build:** :func:`~aws_lambda_artifact_builder.layer.pip_builder.build_layer_artifacts_using_pip_in_local`
    Uses local pip installation - fastest for development

**Container Build:** :func:`~aws_lambda_artifact_builder.layer.pip_builder.build_layer_artifacts_using_pip_in_container`
    Uses Docker container with AWS Lambda runtime - ensures compatibility


Working with Private Repositories
------------------------------------------------------------------------------
When your Lambda layer depends on packages from private repositories, the builder seamlessly integrates authentication through `pip's index URL mechanism <https://pip.pypa.io/en/stable/cli/pip_install/#finding-packages>`_. This allows you to access private PyPI servers or corporate package repositories without additional configuration complexity.

.. code-block:: bash

    --extra-index-url https://username:password@private.pypi.com/simple/