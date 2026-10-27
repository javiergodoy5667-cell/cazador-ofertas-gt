# -*- coding: utf-8 -*-
"""Recolector de Elektra Guatemala (VTEX)."""
from . import _vtex

HOST = "www.elektra.com.gt"
TIENDA = "Elektra GT"
SLUG = "elektra-gt"


def recolectar():
    return _vtex.recolectar_vtex(SLUG, TIENDA, HOST, prefijo="")
