# -*- coding: utf-8 -*-
"""Recolector de La Torre (VTEX). En la red local da timeout; se prueba desde
GitHub Actions, donde puede responder (IP de datacenter distinta)."""
from . import _vtex

HOST = "www.latorre.com.gt"
TIENDA = "La Torre"
SLUG = "latorre"


def recolectar():
    return _vtex.recolectar_vtex(SLUG, TIENDA, HOST, prefijo="")
