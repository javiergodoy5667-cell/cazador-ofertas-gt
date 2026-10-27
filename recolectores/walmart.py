# -*- coding: utf-8 -*-
"""Recolector de Walmart Guatemala (VTEX)."""
from . import _vtex

HOST = "www.walmart.com.gt"
TIENDA = "Walmart GT"
SLUG = "walmart-gt"


def recolectar():
    return _vtex.recolectar_vtex(SLUG, TIENDA, HOST, prefijo="")
