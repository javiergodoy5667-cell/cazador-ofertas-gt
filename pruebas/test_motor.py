# -*- coding: utf-8 -*-
"""
Pruebas del motor con la nueva referencia (historial > mercado > nada).
Casos exigidos: antes inflado -> descartado; mismo EAN en 3 tiendas 40% mas
caro -> loca; sin coincidencia ni historial -> no oferta; agotados no cuentan
para la mediana; cluster de oferta sin verificacion -> no oferta.
"""
import datetime as dt
import unittest
import uuid
from pathlib import Path

from motor import historial, puntaje, config, categorias, mercado

HOY = dt.date(2026, 10, 27)
PID = "tienda-1"


def prod(**kw):
    base = {
        "id": PID, "tienda": "Tienda X", "nombre": "Producto de prueba",
        "categoria": "test", "precio_actual": 100.0,
        "precio_antes_tienda": None, "moneda": "GTQ",
        "url": "https://x.example/p", "imagen": None, "disponible": True,
        "modo_compra": "en_linea", "fin_oferta": None,
        "ean": "", "marca": "", "modelo": "",
        "visto_en": "2026-10-27T14:00:00-06:00",
    }
    base.update(kw)
    return base


def obs(dias_atras, precio, **kw):
    d = {"id": PID, "fecha_inicio": (HOY - dt.timedelta(days=dias_atras)).isoformat(),
         "visto_hasta": (HOY - dt.timedelta(days=dias_atras)).isoformat(), "precio": precio}
    d.update(kw)
    return d


class TestPuntaje(unittest.TestCase):

    def test_error_de_precio(self):
        h = [obs(1, 100), obs(2, 100), obs(3, 100)]
        o = puntaje.evaluar(prod(precio_actual=30.0), h, hoy=HOY)
        self.assertEqual(o["nivel"], "error")
        self.assertEqual(o["fuente_referencia"], "historial")

    def test_agotado_no_alerta(self):
        h = [obs(1, 100), obs(2, 100), obs(3, 100)]
        o = puntaje.evaluar(prod(precio_actual=40.0, disponible=False), h, hoy=HOY)
        self.assertEqual(o["nivel"], "agotado")

    def test_cambio_tamano_sin_falso_descuento(self):
        h = [obs(1, 100, precio_unidad=10, unidad="kg"),
             obs(2, 100, precio_unidad=10, unidad="kg"),
             obs(3, 100, precio_unidad=10, unidad="kg")]
        o = puntaje.evaluar(prod(precio_actual=20.0, precio_unidad=10, unidad="kg"),
                            h, hoy=HOY)
        self.assertIsNone(o)

    def test_minimo_historico_sube_a_muy_buena(self):
        h = [obs(1, 100), obs(2, 100), obs(3, 100)]
        o = puntaje.evaluar(prod(precio_actual=75.0), h, hoy=HOY)
        self.assertTrue(o["minimo_historico"])
        self.assertEqual(o["nivel"], "muy_buena")

    def test_buena(self):
        h = [obs(1, 100), obs(2, 100), obs(3, 100), obs(4, 60)]
        o = puntaje.evaluar(prod(precio_actual=80.0), h, hoy=HOY)
        self.assertEqual(o["nivel"], "buena")
        self.assertFalse(o["minimo_historico"])

    def test_mediana_con_visto_hasta(self):
        linea = {"id": PID, "fecha_inicio": (HOY - dt.timedelta(days=5)).isoformat(),
                 "precio": 100.0, "visto_hasta": HOY.isoformat()}
        ref, sin_hist, _ = puntaje.precio_referencia([linea], HOY)
        self.assertEqual(ref, 100.0)
        self.assertFalse(sin_hist)

    def test_basura_ignorada(self):
        o = puntaje.evaluar(prod(precio_actual=5.0), [], hoy=HOY)
        self.assertIsNone(o)

    def test_basura_permitida_si_error(self):
        h = [obs(1, 100), obs(2, 100), obs(3, 100)]
        o = puntaje.evaluar(prod(precio_actual=5.0), h, hoy=HOY)
        self.assertEqual(o["nivel"], "error")

    def test_sin_referencia_no_oferta(self):
        # Sin historial ni mercado: NO es oferta (aunque el "antes" sea alto).
        o = puntaje.evaluar(prod(precio_actual=40.0, precio_antes_tienda=1000.0),
                            [], hoy=HOY)
        self.assertIsNone(o)

    def test_antes_inflado_descartado(self):
        merc = {"precio_mercado": 120.0,
                "mercado": [{"tienda": "Otra", "precio": 120.0, "url": ""}],
                "antes_inflado": True}
        o = puntaje.evaluar(prod(precio_actual=100.0, precio_antes_tienda=1000.0),
                            [], hoy=HOY, mercado=merc)
        self.assertIsNone(o)

    def test_mercado_loca_40_por_ciento(self):
        merc = {"precio_mercado": 100.0,
                "mercado": [{"tienda": "Otra", "precio": 100.0, "url": ""}],
                "antes_inflado": False}
        o = puntaje.evaluar(prod(precio_actual=60.0), [], hoy=HOY, mercado=merc)
        self.assertEqual(o["nivel"], "loca")
        self.assertEqual(o["fuente_referencia"], "mercado")

    def test_mercado_muy_buena_25_por_ciento(self):
        merc = {"precio_mercado": 100.0,
                "mercado": [{"tienda": "Otra", "precio": 100.0, "url": ""}],
                "antes_inflado": False}
        o = puntaje.evaluar(prod(precio_actual=74.0), [], hoy=HOY, mercado=merc)
        self.assertEqual(o["nivel"], "muy_buena")

    def test_cluster_sin_verificacion_no_oferta(self):
        # Estar en una coleccion de oferta NO lo convierte en oferta.
        o = puntaje.evaluar(prod(precio_actual=100.0, seccion_oferta="Ofertas"),
                            [], hoy=HOY)
        self.assertIsNone(o)

    def test_debe_alertar_antispam(self):
        self.assertTrue(puntaje.debe_alertar(PID, 100, {}))
        self.assertFalse(puntaje.debe_alertar(PID, 100, {PID: 100}))
        self.assertTrue(puntaje.debe_alertar(PID, 95, {PID: 100}))
        self.assertFalse(puntaje.debe_alertar(PID, 96, {PID: 100}))


class TestMercado(unittest.TestCase):

    def test_ean_3_tiendas_mediana(self):
        prods = [
            {"id": "a", "tienda": "A", "ean": "12345678", "precio_actual": 60.0, "disponible": True},
            {"id": "b", "tienda": "B", "ean": "12345678", "precio_actual": 100.0, "disponible": True},
            {"id": "c", "tienda": "C", "ean": "12345678", "precio_actual": 100.0, "disponible": True},
        ]
        info = mercado.calcular(prods)
        self.assertAlmostEqual(info["a"]["precio_mercado"], 100.0)
        o = puntaje.evaluar(prod(id_="a", ean="12345678", precio_actual=60.0),
                            [], hoy=HOY, mercado=info["a"])
        self.assertEqual(o["nivel"], "loca")

    def test_agotados_no_cuentan(self):
        prods = [
            {"id": "a", "tienda": "A", "ean": "12345678", "precio_actual": 60.0, "disponible": True},
            {"id": "b", "tienda": "B", "ean": "12345678", "precio_actual": 100.0, "disponible": True},
            {"id": "c", "tienda": "C", "ean": "12345678", "precio_actual": 5.0, "disponible": False},
        ]
        info = mercado.calcular(prods)
        self.assertAlmostEqual(info["a"]["precio_mercado"], 100.0)

    def test_marca_modelo_sin_ean(self):
        prods = [
            {"id": "a", "tienda": "A", "ean": "", "marca": "DeWalt", "modelo": "DCD771C2", "precio_actual": 60.0, "disponible": True},
            {"id": "b", "tienda": "B", "ean": "", "marca": "DeWalt", "modelo": "DCD771C2", "precio_actual": 100.0, "disponible": True},
            {"id": "c", "tienda": "C", "ean": "", "marca": "DeWalt", "modelo": "OTRO", "precio_actual": 5.0, "disponible": True},
        ]
        info = mercado.calcular(prods)
        self.assertAlmostEqual(info["a"]["precio_mercado"], 100.0)

    def test_tamano_distinto_no_empareja(self):
        # Mismo marca+modelo pero distinto tamano -> NO se comparan.
        prods = [
            {"id": "a", "tienda": "A", "ean": "", "marca": "Borges", "modelo": "AceiteOliva", "precio_actual": 30.0, "disponible": True, "nombre": "Aceite de oliva Borges 1L"},
            {"id": "b", "tienda": "B", "ean": "", "marca": "Borges", "modelo": "AceiteOliva", "precio_actual": 60.0, "disponible": True, "nombre": "Aceite de oliva Borges 2L"},
        ]
        info = mercado.calcular(prods)
        self.assertNotIn("a", info)

    def test_error_solo_con_ean_o_2_tiendas(self):
        # >55% bajo mercado pero sin EAN y 1 tienda -> loca (no error).
        merc = {"precio_mercado": 100.0,
                "mercado": [{"tienda": "Otra", "precio": 100.0, "url": ""}],
                "antes_inflado": False, "por_ean": False, "tiendas": 1}
        o = puntaje.evaluar(prod(precio_actual=40.0), [], hoy=HOY, mercado=merc)
        self.assertEqual(o["nivel"], "loca")


class TestHistorial(unittest.TestCase):

    def setUp(self):
        self._dir_original = historial.HISTORIAL_DIR
        base = Path(__file__).resolve().parent.parent / "data" / "_test_historial"
        base.mkdir(parents=True, exist_ok=True)
        historial.HISTORIAL_DIR = base
        self.tienda = f"Tienda_Test_{self._testMethodName}_{uuid.uuid4().hex[:6]}"

    def tearDown(self):
        try:
            historial.ruta(self.tienda).unlink(missing_ok=True)
        except Exception:
            pass
        historial.HISTORIAL_DIR = self._dir_original

    def test_precio_igual_no_agrega_linea(self):
        p = prod(precio_actual=100.0)
        self.assertTrue(historial.registrar(self.tienda, p, fecha=HOY))
        for dias in (1, 2, 3):
            self.assertFalse(historial.registrar(self.tienda, p,
                                                 fecha=HOY + dt.timedelta(days=dias)))
        lineas = historial.cargar(self.tienda)
        self.assertEqual(len(lineas), 1)
        self.assertEqual(lineas[0]["visto_hasta"],
                         (HOY + dt.timedelta(days=3)).isoformat())

    def test_precio_cambia_agrega_linea(self):
        historial.registrar(self.tienda, prod(precio_actual=100.0), fecha=HOY)
        historial.registrar(self.tienda, prod(precio_actual=80.0),
                            fecha=HOY + dt.timedelta(days=1))
        lineas = historial.cargar(self.tienda)
        self.assertEqual(len(lineas), 2)
        self.assertEqual(lineas[0]["precio"], 100.0)
        self.assertEqual(lineas[1]["precio"], 80.0)

    def test_podar_viejas(self):
        historial.registrar(self.tienda, prod(precio_actual=100.0),
                            fecha=HOY - dt.timedelta(days=120))
        quitados = historial.podar(self.tienda, dias=90, fecha=HOY)
        self.assertEqual(quitados, 1)
        self.assertEqual(len(historial.cargar(self.tienda)), 0)


class TestConfig(unittest.TestCase):

    def test_cargar(self):
        cfg = config.cargar()
        self.assertIn("niveles", cfg)
        self.assertEqual(cfg["niveles"]["loca"], 0.50)
        self.assertEqual(len(cfg["categorias_alerta"]), 8)


class TestCategorias(unittest.TestCase):

    CASOS = [
        ("", "Casco integral para moto", "⚽ Deportes, bicis y motos"),
        ("", "Vino tinto reserva", "🍷 Licores"),
        ("", "Colchón king size", "🛏️ Hogar y muebles"),
        ("", "Refrigeradora Top Mount 12 pies", "🧊 Línea blanca"),
        ("", "Planta eléctrica 6500W", "🔌 Eléctrico"),
        ("", "Breaker 20A", "🔌 Eléctrico"),
        ("", "Llanta 205/55 R16", "🚗 Automotriz"),
        ("", "Televisor Samsung 55", "📺 TV y audio"),
        ("", "Laptop HP Pavilion", "💻 Computación y videojuegos"),
        ("", "Taladro Bosch inalámbrico", "🔧 Ferretería y herramientas"),
        ("", "Alimento para perro adulto", "🐶 Mascotas"),
        ("", "Shampoo anticaspa", "💄 Belleza y cuidado personal"),
        ("", "Muñeca bebé con accesorios", "👶 Bebés y juguetes"),
        ("", "Bicicleta de montaña 26", "⚽ Deportes, bicis y motos"),
        ("", "Whisky 12 años", "🍷 Licores"),
    ]

    def test_clasificacion(self):
        for ruta, nombre, esperado in self.CASOS:
            self.assertEqual(categorias.clasificar(ruta, nombre), esperado,
                             msg=f"fallo: {nombre!r}")

    def test_ruta_prioridad(self):
        self.assertEqual(categorias.clasificar("/Automotriz/Llantas/", "Neumático"),
                         "🚗 Automotriz")


if __name__ == "__main__":
    unittest.main()
