#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pywf import pywf

# Note, uv doesn't have the ``poetry config`` alternative command to store
# HTTP basic auth credentials, so we have to put uv_authorization and uv_lock
# in the same script.
token = pywf.get_codeartifact_authorization_token()
pywf.uv_authorization(token, real_run=True, verbose=True)
pywf.uv_lock(real_run=True, verbose=True)
