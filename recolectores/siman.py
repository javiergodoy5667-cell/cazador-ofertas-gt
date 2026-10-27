# -*- coding: utf-8 -*-
"""Recolector de Tiendas Simán (VTEX).

Nota: Simán publica el campo `link` incorrecto (da 400). La URL correcta
es https://www.siman.com/producto/{linkText}/p (verificada 200).
"""
from . import _vtex

HOST = "www.siman.com"
TIENDA = "Simán"
SLUG = "siman"


def recolectar():
    return _vtex.recolectar_vtex(SLUG, TIENDA, HOST, prefijo="/producto")
