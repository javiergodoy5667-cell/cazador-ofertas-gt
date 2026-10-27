# 🛒 Cazador de Ofertas GT

Revisa tiendas de Guatemala cada hora, detecta **descuentos reales** comparando contra
el historial de precios (no contra el "antes" que las tiendas inflan) y avisa por
**Telegram** al instante. Incluye una **página web instalable** (PWA) con todas las
ofertas vigentes y su historial de precio.

Todo corre **gratis** en GitHub Actions (la computadora del usuario no necesita estar
encendida) y la web se publica en GitHub Pages.

## Cómo funciona

1. `recolectores/*.py` — un archivo por tienda, devuelve productos con precio actual y
   "precio antes" (si la tienda lo publica).
2. `motor/historial.py` — guarda un precio por producto por día (JSONL), borra lo de
   más de 90 días.
3. `motor/puntaje.py` — calcula el descuento **real** contra la mediana de los últimos
   30 días y asigna nivel: 🚨 error de precio, 🔥 loca, ⚡ muy buena, ✅ buena.
4. `alertas/*.py` — envía alertas por Telegram.
5. `web/` — página (HTML + JS puro) que lee `web/ofertas.json`, con filtros y gráficas,
   instalable como app (PWA).
6. `.github/workflows/cazar.yml` — lo ejecuta cada hora en la nube y publica la web.

## Requisitos

- Python 3.11+ (solo biblioteca estándar, sin dependencias).
- Bot de Telegram (token + chat_id) y un repositorio público en GitHub.

## Puesta en marcha (resumen)

1. Crear el repo en GitHub y subir este código.
2. En *Settings → Secrets and variables → Actions*, crear dos secretos:
   `TELEGRAM_TOKEN` y `TELEGRAM_CHAT_ID`.
3. En *Settings → Pages*, poner **Source: GitHub Actions**.
4. Esperar la primera corrida (o dispararla en *Actions → Cazar ofertas → Run workflow*).

## Configuración (`config/config.yml`)

- **Niveles:** umbrales de descuento (`loca`, `muy_buena`, `buena`, `error_precio`).
- **Frecuencia:** `frecuencia_dia`, `frecuencia_madrugada`, `hora_inicio`, `hora_fin`.
- **`precio_basura_min`:** ignora productos finales por debajo de ese monto.
- **`historial_dias` / `historial_max_dias`:** ventana de referencia y poda.
- **`deseos`** (Fase 6): productos con precio máximo para alertar sin importar el %.

## Cómo agregar una tienda

1. Verifica la plataforma (VTEX, Shopify, HTML con sitemap…).
2. Crea `recolectores/<tienda>.py` que exponga `recolectar()` y devuelva el formato
   estándar (ver `recolectores/_vtex.py` o `recolectores/_html.py`).
3. Regístralo en `recolectores/__init__.py` (lista `RECOLECTORES`).

## Cómo cambiar los niveles

Edita `config/config.yml` → sección `niveles`. Los valores son fracción de descuento
(0.50 = 50 %).

## Cómo apagarlo

- Pausa temporal: en *Actions → Cazar ofertas*, botón *Disable workflow*.
- Borrar la automatización: elimina `.github/workflows/cazar.yml` del repo.

## Notas

- El historial vive en `data/historial/` y se guarda (commit) en cada corrida para que
  los descuentos se comparen contra días reales, no solo contra el "precio antes".
- En repositorios **públicos** GitHub Actions y Pages son gratuitos (minutos ilimitados).
