# -*- coding: utf-8 -*-
"""Recolector de Intelaf (HTML + ld+json)."""
from . import _html

HOST = "www.intelaf.com"
TIENDA = "Intelaf"
SLUG = "intelaf"


def recolectar():
    return _html.recolectar_html_ldjson(
        SLUG, TIENDA, "https://www.intelaf.com/sitemap.xml",
        "/precios_stock_detallado/", HOST)
