# -*- coding: utf-8 -*-
"""Recolector de Intelaf (HTML + ld+json).
Nota: el catalogo son 4,452 paginas de producto (una peticion cada una). A
1 req/s serian ~74 min, imposible en el limite de 25 min por corrida; por eso
se toman hasta 300 productos por corrida con tope de tiempo."""
from . import _html

HOST = "www.intelaf.com"
TIENDA = "Intelaf"
SLUG = "intelaf"


def recolectar():
    return _html.recolectar_html_ldjson(
        SLUG, TIENDA, "https://www.intelaf.com/sitemap.xml",
        "/precios_stock_detallado/", HOST,
        max_productos=300, tiempo_limite=240)
