#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
We primarily use poetry to build the package.
"""

from pywf import pywf

pywf.poetry_build(real_run=True, verbose=True)
