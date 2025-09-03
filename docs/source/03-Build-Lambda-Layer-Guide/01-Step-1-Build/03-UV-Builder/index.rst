UV Builder
==============================================================================
The UV Builder provides Lambda layer creation using UV's ultra-fast dependency management and resolution system. This approach leverages UV's lock file mechanism and high-performance installation for rapid Lambda layer creation with reproducible builds.


Why Use UV Builder
------------------------------------------------------------------------------
UV Builder represents the cutting edge of Python dependency management, delivering significantly faster builds while maintaining the reproducibility benefits of lock files. It's ideal for projects requiring both speed and reliability in their Lambda layer creation workflow.

**Advantages:**

- **Ultra-fast performance** - UV offers the fastest dependency resolution and installation available
- **Reproducible builds** - ``uv.lock`` ensures identical dependency versions across environments
- **Modern tooling** - Built in Rust for maximum performance and reliability
- **pip/Poetry compatibility** - Works with existing pyproject.toml configurations
- **Advanced caching** - Sophisticated caching system reduces build times dramatically

**Limitations:**

- **Newer tooling** - Less ecosystem maturity compared to pip/Poetry
- **Bootstrap requirement** - UV must be installed on build systems
- **Learning curve** - New command patterns and configuration options

**Best for:** Projects prioritizing build speed, modern Python packaging standards, or teams already using UV for dependency management.


How UV Builder Works  
------------------------------------------------------------------------------
UV Builder leverages UV's ``sync`` command with frozen lock files to create Lambda-compatible package installations. The process copies your ``pyproject.toml`` and ``uv.lock`` files to an isolated build directory, then uses UV's high-performance resolver to install dependencies into a virtual environment with Lambda-specific configurations.

.. code-block:: bash

    uv sync --frozen --no-dev --no-install-project --link-mode=copy

**Key Steps:**

1. Copies ``pyproject.toml`` and ``uv.lock`` to isolated build directory
2. Uses UV's frozen sync to prevent lock file modifications during build
3. Installs dependencies with ``--no-dev`` (production only) and ``--no-install-project`` (excludes your project package)
4. Uses ``--link-mode=copy`` for Lambda compatibility (no symlinks)
5. Extracts packages from ``.venv/lib/python3.x/site-packages/`` to ``artifacts/python/``
6. Creates ``layer.zip`` ready for Lambda deployment

The ``--frozen`` flag ensures builds use exactly the same dependency versions as your development environment, while ``--no-install-project`` excludes your application code (which belongs in the Lambda function, not the layer).


Build Options
------------------------------------------------------------------------------
You can choose between local and containerized builds depending on your development workflow and compatibility requirements. Local builds are extremely fast for iteration with UV's performance optimizations, while container builds guarantee your layer will work identically in the AWS Lambda runtime environment.

**Local Build:** :class:`~aws_lambda_artifact_builder.layer.uv_builder.UVBasedLambdaLayerLocalBuilder`
    Uses local UV installation - fastest possible build experience

**Container Build:** :class:`~aws_lambda_artifact_builder.layer.uv_builder.UVBasedLambdaLayerContainerBuilder`
    Uses Docker container with UV installation - ensures compatibility and isolation


Working with Private Repositories
------------------------------------------------------------------------------
When your Lambda layer depends on packages from private repositories, UV Builder integrates with UV's credential system through environment variables. This allows secure access to private PyPI servers or corporate package repositories following UV's documented authentication patterns.

.. code-block:: bash

    # UV uses environment variables for HTTP basic authentication
    export UV_INDEX_PRIVATE_USERNAME=username
    export UV_INDEX_PRIVATE_PASSWORD=password

The builder automatically configures these environment variables when credentials are provided through the :meth:`~aws_lambda_artifact_builder.layer.uv_builder.UVBasedLambdaLayerLocalBuilder.step_3_1_uv_login` method, following UV's naming convention for private repository authentication.


Usage Examples
------------------------------------------------------------------------------
**Local Build Example:**

.. tip::

    - `settings <https://github.com/MacHu-GWU/aws_lambda_artifact_builder-project/blob/main/example_repo/settings.py>`_: example settings.
    - `example_2_1_build_lambda_layer_using_poetry_in_local.py <https://github.com/MacHu-GWU/aws_lambda_artifact_builder-project/blob/main/example_repo/example_2_1_build_lambda_layer_using_poetry_in_local.py>`_: usage example.

**Container Build Example:**

.. tip::

    - `settings <https://github.com/MacHu-GWU/aws_lambda_artifact_builder-project/blob/main/example_repo/settings.py>`_: example settings.
    - `example_2_2_build_lambda_layer_using_poetry_in_container.py <https://github.com/MacHu-GWU/aws_lambda_artifact_builder-project/blob/main/example_repo/example_2_2_build_lambda_layer_using_poetry_in_container.py>`_: usage example.
