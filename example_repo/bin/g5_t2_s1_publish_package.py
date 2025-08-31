#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
We primarily use twine to publish the package to AWS CodeArtifact.
"""

from pywf import pywf

pywf.publish_to_codeartifact(real_run=True, verbose=True)
