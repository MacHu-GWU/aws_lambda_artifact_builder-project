#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pywf import pywf

token = pywf.get_codeartifact_authorization_token()
pywf.poetry_authorization(token, real_run=True, verbose=True)
