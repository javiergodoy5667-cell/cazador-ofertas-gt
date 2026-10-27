# -*- coding: utf-8 -*-
"""Recolector de Pacifiko (HTML + ld+json)."""
from . import _html

HOST = "www.pacifiko.com"
TIENDA = "Pacifiko"
SLUG = "pacifiko"


def recolectar():
    return _html.recolectar_html_ldjson(
        SLUG, TIENDA, "https://www.pacifiko.com/pids-1.xml",
        "/compras-en-linea/", HOST)
