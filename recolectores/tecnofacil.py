# -*- coding: utf-8 -*-
"""Recolector de Tecnofácil Guatemala (Next.js/Magento, ver _unicomer)."""
from . import _unicomer

HOST = "www.tecnofacil.com.gt"
TIENDA = "Tecnofácil"
SLUG = "tecnofacil"


def recolectar():
    return _unicomer.recolectar_unicomer(SLUG, TIENDA, HOST)
