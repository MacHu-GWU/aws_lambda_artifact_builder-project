.. _Layer-Step-1:

Step 1: Build - Dependency Installation
==============================================================================
The **Build** step is the foundation of Lambda layer creation, responsible for installing and resolving 
Python dependencies using modern package management tools. This step transforms your project's dependency 
specifications into installed packages ready for Lambda layer packaging.

**Prerequisites and Project Requirements**

Before building Lambda layers, ensure your development environment meets these requirements:

**Python Project Structure**
    Your project must use a ``pyproject.toml`` file as the primary configuration. This modern Python 
    standard is required for dependency declaration and project metadata. The library does **NOT**
    support legacy ``setup.py`` files or ``requirements.txt`` as the primary dependency source.

**Supported Dependency Managers**
    Choose one of these compatible package management tools:
    
    - **pip**: Standard Python package installer with ``requirements.txt`` generation
    - **Poetry**: Modern dependency management with lock file reproducibility  
    - **UV**: Ultra-fast package resolver with Poetry-compatible lock files

**System Dependencies**
    - Python 3.10+ installed on your system
    - Docker (required only for container builds)
    - Your chosen package manager (pip, Poetry, or UV) installed and accessible

**Project Layout Assumptions**

The build process expects a standardized project structure centered around ``pyproject.toml``:

.. code-block:: text

    ${project_root}/                           # Your project directory
    ├── pyproject.toml                         # ✅ Required: Project configuration
    ├── poetry.lock                            # For Poetry projects
    ├── uv.lock                               # For UV projects  
    ├── requirements.txt                       # Generated for pip builds
    └── build/lambda/layer/                    # Build artifacts (auto-created)
        ├── layer.zip                          # Final layer package
        ├── repo/                              # Isolated build environment
        └── artifacts/python/                  # Lambda-compatible structure

**Important Design Decisions**

- **No setup.py Support**: The library exclusively uses ``pyproject.toml`` to align with modern Python packaging standards
- **Lock File Priority**: Poetry and UV builds use lock files for reproducible dependency resolution
- **Temporary Build Directory**: The ``build/lambda/layer/`` directory is cleaned before each build to prevent conflicts
- **AWS Lambda Compatibility**: All builds target the ``artifacts/python/`` structure required by Lambda layers

**Local vs Container Builds**

The library provides two build execution environments, each with distinct advantages:

**Local Builds** (:class:`~aws_lambda_artifact_builder.layer.builder.BasedLambdaLayerLocalBuilder`)
    Execute dependency installation directly on your host machine. Best suited for:
    
    - **Development Workflows**: Fast iteration during layer development
    - **Linux Environments**: When your development OS matches Lambda's Linux runtime
    - **Simple Dependencies**: Packages with only pure-Python and without complex C-extensions

    Local builds offer maximum speed but may encounter platform compatibility issues when 
    dependencies include native extensions compiled for different architectures.

**Container Builds** (:class:`~aws_lambda_artifact_builder.layer.builder.BasedLambdaLayerContainerBuilder`)
    Execute builds inside official AWS SAM Docker containers that mirror Lambda's runtime. Ideal for:
    
    - **Production Deployment**: Ensuring exact Lambda runtime compatibility
    - **Cross-Platform Development**: Building Linux-compatible layers on macOS/Windows
    - **Complex Dependencies**: Packages with native extensions (numpy, pandas, etc.)
    - **CI/CD Pipelines**: Consistent builds across different environments

    Container builds provide maximum compatibility at the cost of Docker overhead and longer build times.

**Build Process Architecture**

Both build types follow the same conceptual workflow implemented through the Command Pattern:

1. **Environment Preparation**: Clean build directories and create necessary folder structure
2. **Dependency Resolution**: Use the chosen tool (pip/Poetry/UV) to resolve and install packages
3. **Artifact Organization**: Structure installed packages for Lambda layer compatibility

The key difference lies in **execution context**: local builds run directly on your machine, 
while container builds execute the same logic inside Docker containers using official AWS Lambda base images.

**Tool-Specific Implementation**

Each package manager requires specialized handling for optimal Lambda layer creation:

**Next Steps: Choose Your Build Tool**

Select the dependency management approach that best fits your project requirements:

.. autotoctree::
    :maxdepth: 1

Each tool guide provides detailed examples, configuration options, and best practices for both 
local and container build environments. For tool comparison and selection guidance, see the 
build comparison section after reviewing individual tool capabilities.