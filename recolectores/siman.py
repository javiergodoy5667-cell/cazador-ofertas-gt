# -*- coding: utf-8 -*-
"""Recolector de Simán GUATEMALA (VTEX).

Importante (auditoría 7): `www.siman.com` es Simán El Salvador y cotiza en
DÓLARES. La tienda de Guatemala responde en
`simanguatemala.vtexcommercestable.com.br` con precios en QUETZALES
(verificado: microondas 25 L = Q799). El storefront público es `gt.siman.com`.
"""
from . import _vtex

HOST = "simanguatemala.vtexcommercestable.com.br"   # API (quetzales)
DOMINIO_LINK = "gt.siman.com"                        # storefront GT para links
TIENDA = "Simán"
SLUG = "siman"


def recolectar():
    return _vtex.recolectar_vtex(SLUG, TIENDA, HOST, prefijo="",
                                 dominio_link=DOMINIO_LINK)
