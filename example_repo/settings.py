# -*- coding: utf-8 -*-

from pathlib import Path
from pywf_internal_proprietary.api import PyWf

dir_here = Path(__file__).absolute().parent
path_pyproject_toml = dir_here.joinpath("pyproject.toml")
pywf = PyWf.from_pyproject_toml(path_pyproject_toml)

index_name = "esc"
index_url = pywf.get_codeartifact_repository_endpoint()
username = "aws"
password = pywf.get_codeartifact_authorization_token()