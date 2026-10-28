# -*- coding: utf-8 -*-
"""Recolector de Max Guatemala (Next.js/Magento, ver _unicomer)."""
from . import _unicomer

HOST = "www.max.com.gt"
TIENDA = "Max"
SLUG = "max-gt"


def recolectar():
    return _unicomer.recolectar_unicomer(SLUG, TIENDA, HOST)
