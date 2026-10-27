# -*- coding: utf-8 -*-
"""Recolector de Cemaco (VTEX)."""
from . import _vtex

HOST = "www.cemaco.com"
TIENDA = "Cemaco"
SLUG = "cemaco"


def recolectar():
    return _vtex.recolectar_vtex(SLUG, TIENDA, HOST, prefijo="")
