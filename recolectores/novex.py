# -*- coding: utf-8 -*-
"""
Recolector de Novex Guatemala (HTML propio).
Solo las subcategorias finales (sin hijas en /catalog-desktop.xml) muestran
productos: 15 tarjetas "catalog_products_card" por pagina, ?page=N.
Son ~2,900 hojas: no caben en una corrida, asi que se leen primero las
categorias de alerta y el resto rota segun la hora.
robots.txt pide Crawl-delay: 30 -> una pagina cada 30 s (~14 por corrida).
"""
import datetime as dt
import html as htmllib
import re
import time

from . import _base

HOST = "www.novex.com.gt"
TIENDA = "Novex"
SLUG = "novex"
POR_PAGINA = 15
# Prefijos de categoria Novex: herramientas, electrico, electrodomesticos,
# automotriz, bombas, refrigeracion, maquinaria de jardin, industrial, ferreteria.
PRIORIDAD = ["45", "46", "20", "50", "80", "60", "75", "86", "70", "40"]
EXCLUIR = ["99", "90"]  # productos de baja / no clasificados
HOJAS_POR_CORRIDA = 14
PAUSA = 30  # segundos (Crawl-delay de robots.txt)


def _hojas():
    st, _fu, xml = _base.get(f"https://{HOST}/catalog-desktop.xml", host=HOST)
    time.sleep(PAUSA)
    if st != 200 or not xml:
        return []
    cats = {}
    for u in re.findall(r"<loc>(https://www\.novex\.com\.gt/catalogo/(\d+)/[^<]+)</loc>", xml):
        cats.setdefault(u[1], u[0])
    ids = [i for i in cats if not any(i.startswith(e) for e in EXCLUIR)]
    hojas = [i for i in ids if not any(o != i and o.startswith(i) for o in ids)]

    def orden(i):
        return next((n for n, p in enumerate(PRIORIDAD) if i.startswith(p)), len(PRIORIDAD))
    hojas.sort(key=lambda i: (orden(i), i))
    return [(i, cats[i]) for i in hojas]


def _turno(hojas):
    """Casi todo el cupo para categorias de alerta y 4 hojas para el resto;
    cada mitad rota por hora, asi todo se cubre a lo largo del dia."""
    prio = [h for h in hojas if any(h[0].startswith(p) for p in PRIORIDAD[:5])]
    resto = [h for h in hojas if h not in prio]
    hora = dt.datetime.utcnow().hour
    out = []
    for lista, cupo in ((prio, HOJAS_POR_CORRIDA - 4), (resto, 4)):
        if len(lista) <= cupo:
            out += lista
        elif lista:
            ini = (hora * cupo) % len(lista)
            out += (lista + lista)[ini:ini + cupo]
    return out


def _num(txt):
    m = re.search(r"Q\s*(?:<[^>]+>\s*)*([\d,]+(?:\.\d+)?)", txt or "")
    return _base.limpiar_precio(m.group(1)) if m else None


def _tarjetas(html, ruta):
    out = []
    partes = re.split(r'class="catalog_products_card"', html)[1:]
    for b in partes:
        m = re.search(r'catalog_products_card_name">\s*<a href="([^"]+)">([^<]+)</a>', b)
        if not m:
            continue
        url, nombre = m.group(1), htmllib.unescape(m.group(2)).strip()
        pm = re.search(r'catalog_products_card_currentPrice">(.*?)</div>\s*</div>', b, re.S)
        precio = _num(pm.group(1)) if pm else None
        if not precio or precio <= 0:
            continue
        am = re.search(r'catalog_products_card__antes.*?(Q\s*[\d,]+(?:\.\d+)?)', b, re.S)
        antes = _num(am.group(1)) if am else None
        sku = re.search(r"Sku:\s*([\w-]+)", b)
        modelo = re.search(r"Modelo:\s*([^<]+)", b)
        marca = re.search(r'catalog_products_card_brand">\s*([^<]+?)\s*</div>', b)
        img = re.search(r'src="(https://[^"]+/large/[^"]+)"', b)
        agotado = re.search(r'catalog_products_card_stock[^>]*>[^<]*(agotado|sin existencia)', b, re.I)
        sid = sku.group(1) if sku else re.sub(r"\D", "", url)[:12]
        out.append(_base.nuevo_producto(
            id_=f"{SLUG}-{sid}", tienda=TIENDA, nombre=nombre, precio=precio,
            antes=antes if antes and antes > precio else None, url=url,
            imagen=img.group(1) if img else None, categoria=ruta,
            disponible=not agotado,
            marca=htmllib.unescape(marca.group(1)) if marca else "",
            modelo=htmllib.unescape(modelo.group(1)).strip() if modelo else ""))
    return out


def recolectar(tiempo_limite=420):
    inicio = time.monotonic()
    vistos = {}
    for _id, url in _turno(_hojas()):
        ruta = re.sub(r"^.*/catalogo/\d+/|\.html$", "", url)
        pagina = 1
        while time.monotonic() - inicio < tiempo_limite:
            st, _fu, html = _base.get(url + (f"?page={pagina}" if pagina > 1 else ""), host=HOST)
            time.sleep(PAUSA)
            if st != 200 or not html:
                break
            prods = _tarjetas(html, ruta)
            nuevos = [p for p in prods if p["id"] not in vistos]
            for p in nuevos:
                vistos[p["id"]] = p
            if len(prods) < POR_PAGINA or not nuevos or pagina >= 20:
                break
            pagina += 1
        if time.monotonic() - inicio >= tiempo_limite:
            break
    return list(vistos.values())
