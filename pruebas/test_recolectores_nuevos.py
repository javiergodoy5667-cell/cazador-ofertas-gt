# -*- coding: utf-8 -*-
"""Pruebas sin red de los lectores de Max/Tecnofacil, Novex y Office Depot
(con HTML recortado de las paginas reales)."""
import json
import unittest

from recolectores import _unicomer, novex, officedepot

NEXT = ('<script id="__NEXT_DATA__" type="application/json">' + json.dumps({
    "props": {"pageProps": {"totalCount": 1, "productsList": [{
        "sku": "IPHONE16128B", "slug": "apple-iphone-16-128gb-negro",
        "title": "Apple iPhone 16, 128GB", "status": "IN_STOCK",
        "eanCode": "195949035913", "brand": {"title": "Apple"},
        "thumbnailImage": {"url": "https://x/i.jpg"},
        "regularPrice": {"currency": "GTQ", "value": 8995},
        "salesPrice": {"currency": "GTQ", "value": 7496}}]}}}) + "</script>")

NOVEX = '''<div class="catalog_products_card"> <div class="catalog_products_card_brand"> DREMEL </div>
<div class="catalog_products_card_name"> <a href="https://www.novex.com.gt/producto/1/x.html">Herramienta rotativa</a> </div>
<div class="catalog_products_card_sku_model"> <span>Sku: 129123</span> <span>Modelo: 7350LA</span> </div>
<div class="catalog_products_card_pricing"> <div class="catalog_products_card_currentPrice"> <div> Q <span class="">215.60</span> <sup>JGO</sup> </div> </div>
<div class="catalog_products_card_savings"> <div class="catalog_products_container_antes"> <span class="catalog_products_card__antes"><span class="antes_label">Antes:</span> Q245.00</span>'''

OD = '''<form id="addToCartForm1310000365" class="add_to_cart_form"><input type="hidden" name="productNamePost" value="BOCINA KLIP BLUETOOTH"/>
<button onclick="addToCartDatalayer('1310000365','BOCINA KLIP BLUETOOTH','Audio y Video','KLIP XTREME','386.4');"></button></form>
<form id="configureForm1310000365" class="configure_form" action="/officedepotGuatemala/en/Bocinas/BOCINA/p/1310000365/configuratorPage/" method="get"></form>
<button data-productcart='Q644.00'
      data-productdiscounted='Q386.40'
      data-productcode='1310000365'></button>'''


class TestNuevos(unittest.TestCase):
    def test_max_precio_y_antes(self):
        _t, items = _unicomer._lista(NEXT)
        p = _unicomer._producto(items[0], "max-gt", "Max", "www.max.com.gt", "celulares")
        self.assertEqual((p["precio_actual"], p["precio_antes_tienda"]), (7496.0, 8995.0))
        self.assertEqual(p["ean"], "195949035913")

    def test_max_rechaza_otra_moneda(self):
        _t, items = _unicomer._lista(NEXT.replace("GTQ", "USD"))
        self.assertIsNone(_unicomer._producto(items[0], "max-gt", "Max", "h", "r"))

    def test_novex_precio_y_antes(self):
        p = novex._tarjetas(NOVEX, "x")[0]
        self.assertEqual((p["precio_actual"], p["precio_antes_tienda"]), (215.6, 245.0))
        self.assertEqual((p["marca"], p["modelo"]), ("DREMEL", "7350LA"))

    def test_officedepot_precio_y_antes(self):
        t = officedepot._tarjetas(OD)["1310000365"]
        self.assertEqual((t["actual"], t["normal"]), (386.4, 644.0))
        self.assertTrue(t["url"].endswith("/p/1310000365"))


if __name__ == "__main__":
    unittest.main()
