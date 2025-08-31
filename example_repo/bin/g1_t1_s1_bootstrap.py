#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Install dependencies for Python development workflow automation.
"""

import subprocess
from pathlib import Path

bin_global_pip = Path.home().joinpath(".pyenv", "shims", "pip")
args = [
    f"{bin_global_pip}",
    "install",
    "--upgrade",
    "pywf_internal_proprietary>=0.0.1,<1.0.0",
]
subprocess.run(args, check=True)
