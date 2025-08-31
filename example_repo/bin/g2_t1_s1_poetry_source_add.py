#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pywf import pywf

endpoint = pywf.get_codeartifact_repository_endpoint()
pywf.poetry_source_add_codeartifact(endpoint, real_run=True, verbose=True)
