# -*- coding: utf-8 -*-
"""Paquete de recolectores. RECOLECTORES lista todos los modulos activos.
Pacifiko esta desactivado: bloquea las IP de datacenter de GitHub Actions."""
from . import walmart, elektra, cemaco, siman, intelaf, lacuracao, la_torre

RECOLECTORES = [walmart, elektra, cemaco, siman, intelaf, lacuracao, la_torre]
