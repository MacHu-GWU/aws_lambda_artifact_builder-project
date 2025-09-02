Poetry Builder
==============================================================================
The Poetry Builder provides Lambda layer creation using Poetry's sophisticated dependency management and lock file system. This approach leverages Poetry's virtual environment handling and reproducible builds for consistent Lambda layer deployment.


Why Use Poetry Builder
------------------------------------------------------------------------------
Poetry Builder excels at creating reproducible Lambda layers through its lock file mechanism and sophisticated dependency resolution. It's ideal for projects that require strict version control and complex dependency management across multiple environments.

**Advantages:**

- **Reproducible builds** - ``poetry.lock`` ensures identical dependency versions across environments
- **Sophisticated dependency resolution** - handles complex version constraints and conflicts automatically  
- **Virtual environment isolation** - clean separation between project and system dependencies
- **Modern tooling** - follows current Python packaging standards and best practices

**Limitations:**

- **Bootstrap overhead** - requires Poetry installation on build systems
- **Learning curve** - more complex configuration than simple pip workflows

**Best for:** Projects requiring strict dependency reproducibility, complex version constraints, or teams using Poetry for dependency management.


How Poetry Builder Works  
------------------------------------------------------------------------------
Poetry Builder leverages Poetry's ``install --no-root`` command within an in-project virtual environment to create Lambda-compatible package installations. The process copies your ``pyproject.toml`` and ``poetry.lock`` files to an isolated build directory, then uses Poetry to install only the dependencies (not your project code) into the virtual environment.

.. code-block:: bash

    poetry config virtualenvs.in-project true
    poetry install --no-root

**Key Steps:**

1. Copies ``pyproject.toml`` and ``poetry.lock`` to isolated build directory
2. Configures Poetry to create virtual environment in project (``virtualenvs.in-project true``)
3. Installs dependencies using ``poetry install --no-root`` (excludes your project package)
4. Extracts packages from ``.venv/lib/python3.x/site-packages/`` to ``artifacts/python/``
5. Creates ``layer.zip`` ready for Lambda deployment

The ``--no-root`` flag is crucial as it installs only your dependencies, not your project code, which is exactly what's needed for a reusable Lambda layer.


Build Options
------------------------------------------------------------------------------
You can choose between local and containerized builds depending on your development workflow and compatibility requirements. Local builds are faster for iteration, while container builds guarantee your layer will work identically in the AWS Lambda runtime environment.

**Local Build:** :func:`~aws_lambda_artifact_builder.layer.poetry_builder.build_layer_artifacts_using_poetry_in_local`
    Uses local Poetry installation - fastest for development with Poetry already configured

**Container Build:** :func:`~aws_lambda_artifact_builder.layer.poetry_builder.build_layer_artifacts_using_poetry_in_container`
    Uses Docker container with Poetry installation - ensures compatibility and isolation


Working with Private Repositories
------------------------------------------------------------------------------
When your Lambda layer depends on packages from private repositories, Poetry Builder integrates with Poetry's credential system through environment variables. This allows secure access to private PyPI servers or corporate package repositories following Poetry's documented authentication patterns.

.. code-block:: bash

    # Poetry uses environment variables for HTTP basic authentication
    export POETRY_HTTP_BASIC_PRIVATE_USERNAME=username
    export POETRY_HTTP_BASIC_PRIVATE_PASSWORD=password

The builder automatically configures these environment variables when :meth:`~aws_lambda_artifact_builder.layer.poetry_builder.PoetryBasedLambdaLayerLocalBuilder.poetry_login` are provided, following Poetry's naming convention for private repository authentication.
