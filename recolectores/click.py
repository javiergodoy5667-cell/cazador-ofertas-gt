# -*- coding: utf-8 -*-
"""Recolector de Click Guatemala (Shopify, ver _shopify)."""
from . import _shopify

HOST = "www.click.gt"
TIENDA = "Click"
SLUG = "click"


def recolectar():
    return _shopify.recolectar_shopify(SLUG, TIENDA, HOST)
