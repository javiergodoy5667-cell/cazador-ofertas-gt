# -*- coding: utf-8 -*-
"""
Pruebas unitarias del motor de puntaje y del historial.
Casos: descuento falso inflado, error de precio, sin historial, agotado,
cambio de tamaño (precio por unidad), producto basura, antispam.
Uso:  python -m unittest pruebas.test_motor -v
"""
import datetime as dt
import unittest
import uuid
from pathlib import Path

from motor import historial, puntaje, config, categorias

HOY = dt.date(2026, 10, 27)
PID = "tienda-1"


def prod(**kw):
    base = {
        "id": PID, "tienda": "Tienda X", "nombre": "Producto de prueba",
        "categoria": "test", "precio_actual": 100.0,
        "precio_antes_tienda": None, "moneda": "GTQ",
        "url": "https://x.example/p", "imagen": None, "disponible": True,
        "modo_compra": "en_linea", "fin_oferta": None,
        "visto_en": "2026-10-27T14:00:00-06:00",
    }
    base.update(kw)
    return base


def obs(dias_atras, precio, **kw):
    d = {"id": PID, "fecha": (HOY - dt.timedelta(days=dias_atras)).isoformat(),
         "precio": precio}
    d.update(kw)
    return d


class TestPuntaje(unittest.TestCase):

    def test_descuento_falso_inflado(self):
        # Sin historial: el "antes" inflado de la tienda no puede dar alerta.
        p = prod(precio_actual=100.0, precio_antes_tienda=1000.0)
        o = puntaje.evaluar(p, [], hoy=HOY)
        self.assertIsNotNone(o)
        self.assertEqual(o["nivel"], "buena")
        self.assertTrue(o["sin_historial"])

    def test_error_de_precio(self):
        h = [obs(1, 100), obs(2, 100), obs(3, 100)]
        o = puntaje.evaluar(prod(precio_actual=30.0), h, hoy=HOY)
        self.assertEqual(o["nivel"], "error")
        self.assertFalse(o["sin_historial"])
        self.assertAlmostEqual(o["descuento_real"], 0.70, places=2)

    def test_sin_historial_max_buena(self):
        # 60% de "descuento" contra el antes, pero sin historial -> maximo BUENA.
        o = puntaje.evaluar(prod(precio_actual=40.0, precio_antes_tienda=100.0),
                            [], hoy=HOY)
        self.assertEqual(o["nivel"], "buena")
        self.assertTrue(o["sin_historial"])
        # Nunca nivel de aviso por Telegram (error/loca/muy_buena).
        self.assertNotIn(o["nivel"], ("error", "loca", "muy_buena"))

    def test_sin_historial_fin_oferta_no_relampago(self):
        # fin_oferta (PriceValidUntil) no es relampago real; sin historial -> buena.
        o = puntaje.evaluar(prod(precio_actual=40.0, precio_antes_tienda=100.0,
                                 fin_oferta="2027-10-27T00:00:00Z"), [], hoy=HOY)
        self.assertEqual(o["nivel"], "buena")
        self.assertFalse(o["relampago"])

    def test_sin_historial_relampago_cap_final(self):
        # Etiqueta real "flash" + sin historial: el tope se aplica AL FINAL.
        o = puntaje.evaluar(prod(precio_actual=40.0, precio_antes_tienda=100.0,
                                 nombre="Casco flash hoy"), [], hoy=HOY)
        self.assertTrue(o["relampago"])
        self.assertEqual(o["nivel"], "buena")
        self.assertNotIn(o["nivel"], ("error", "loca", "muy_buena"))

    def test_agotado_no_alerta(self):
        o = puntaje.evaluar(prod(precio_actual=40.0, precio_antes_tienda=100.0,
                                 disponible=False), [], hoy=HOY)
        self.assertEqual(o["nivel"], "agotado")

    def test_cambio_tamano_sin_falso_descuento(self):
        # Mismo precio por unidad: el "descuento" por menor tamaño se descarta.
        h = [obs(1, 100, precio_unidad=10, unidad="kg"),
             obs(2, 100, precio_unidad=10, unidad="kg"),
             obs(3, 100, precio_unidad=10, unidad="kg")]
        p = prod(precio_actual=20.0, precio_unidad=10, unidad="kg")
        o = puntaje.evaluar(p, h, hoy=HOY)
        self.assertIsNone(o)

    def test_minimo_historico_sube_a_muy_buena(self):
        h = [obs(1, 100), obs(2, 100), obs(3, 100)]
        o = puntaje.evaluar(prod(precio_actual=75.0), h, hoy=HOY)
        self.assertTrue(o["minimo_historico"])
        self.assertEqual(o["nivel"], "muy_buena")

    def test_basura_ignorada(self):
        # Precio final < Q15 sin historia -> ignorar.
        o = puntaje.evaluar(prod(precio_actual=5.0, precio_antes_tienda=100.0),
                            [], hoy=HOY)
        self.assertIsNone(o)

    def test_basura_permitida_si_error(self):
        h = [obs(1, 100), obs(2, 100), obs(3, 100)]
        o = puntaje.evaluar(prod(precio_actual=5.0), h, hoy=HOY)
        self.assertEqual(o["nivel"], "error")

    def test_buena(self):
        # 20% de descuento SIN ser minimo historico (ya hubo un 60 en el pasado).
        h = [obs(1, 100), obs(2, 100), obs(3, 100), obs(4, 60)]
        o = puntaje.evaluar(prod(precio_actual=80.0), h, hoy=HOY)
        self.assertEqual(o["nivel"], "buena")
        self.assertAlmostEqual(o["descuento_real"], 0.20, places=2)
        self.assertFalse(o["minimo_historico"])

    def test_mediana_con_visto_hasta(self):
        # Una sola linea vigente 5 dias equivale a 5 dias de historial (mediana OK).
        linea = {"id": PID, "fecha_inicio": (HOY - dt.timedelta(days=5)).isoformat(),
                 "precio": 100.0, "visto_hasta": HOY.isoformat()}
        ref, sin_hist, _ = puntaje.precio_referencia([linea], HOY)
        self.assertEqual(ref, 100.0)
        self.assertFalse(sin_hist)

    def test_debe_alertar_antispam(self):
        self.assertTrue(puntaje.debe_alertar(PID, 100, {}))
        # ya alertado al mismo precio -> no repetir
        self.assertFalse(puntaje.debe_alertar(PID, 100, {PID: 100}))
        # bajó 5% -> volver a alertar
        self.assertTrue(puntaje.debe_alertar(PID, 95, {PID: 100}))
        # bajó solo 4% -> no
        self.assertFalse(puntaje.debe_alertar(PID, 96, {PID: 100}))


class TestHistorial(unittest.TestCase):

    def setUp(self):
        self._dir_original = historial.HISTORIAL_DIR
        base = Path(__file__).resolve().parent.parent / "data" / "_test_historial"
        base.mkdir(parents=True, exist_ok=True)
        historial.HISTORIAL_DIR = base
        # nombre de tienda unico por ejecucion (evita que corridas previas
        # dejen observaciones que ensucien la prueba)
        self.tienda = f"Tienda_Test_{self._testMethodName}_{uuid.uuid4().hex[:6]}"

    def tearDown(self):
        # limpiar el archivo de esta prueba
        try:
            historial.ruta(self.tienda).unlink(missing_ok=True)
        except Exception:
            pass
        historial.HISTORIAL_DIR = self._dir_original

    def test_precio_igual_no_agrega_linea(self):
        # Mismo precio en dias distintos -> una sola linea con visto_hasta extendido.
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
        p = prod(precio_actual=100.0)
        historial.registrar(self.tienda, p, fecha=HOY)
        p2 = prod(precio_actual=80.0)
        historial.registrar(self.tienda, p2, fecha=HOY + dt.timedelta(days=1))
        lineas = historial.cargar(self.tienda)
        self.assertEqual(len(lineas), 2)
        self.assertEqual(lineas[0]["precio"], 100.0)
        self.assertEqual(lineas[0]["visto_hasta"], HOY.isoformat())
        self.assertEqual(lineas[1]["precio"], 80.0)

    def test_podar_viejas(self):
        p = prod(precio_actual=100.0)
        # no se vuelve a ver -> visto_hasta queda en HOY-120 (viejo)
        historial.registrar(self.tienda, p, fecha=HOY - dt.timedelta(days=120))
        quitados = historial.podar(self.tienda, dias=90, fecha=HOY)
        self.assertEqual(quitados, 1)
        self.assertEqual(len(historial.cargar(self.tienda)), 0)


class TestConfig(unittest.TestCase):

    def test_cargar(self):
        cfg = config.cargar()
        self.assertIn("niveles", cfg)
        self.assertEqual(cfg["niveles"]["loca"], 0.50)
        self.assertEqual(cfg["zona_horaria"], "America/Guatemala")


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
