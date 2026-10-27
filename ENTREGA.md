# ENTREGA — Cazador de Ofertas GT

> Estado: **en construcción**. Este archivo se llena fase por fase y queda completo
> solo cuando el sistema está funcionando de punta a punta. Al terminar, cada punto
> tendrá su prueba (salida de comando, captura o link).

---

## Requisitos añadidos durante el desarrollo

1. **PWA (Fase 4):** la página debe ser instalable como app en el teléfono:
   - `manifest.json` con nombre **"Cazador GT"**, ícono propio y `"display": "standalone"`.
   - `service-worker.js` que guarde en caché la última lista de ofertas para verla
     **sin internet**.
   - En Android debe ofrecer **"Instalar app"** y abrir a pantalla completa.
   - Instalación en Android (3 toques):
     1. Abrir la página en **Chrome**.
     2. Tocar **⋮** (tres puntos, arriba a la derecha) → **"Instalar app"**.
     3. Tocar **"Instalar"** en la ventana de confirmación.
2. **ENTREGA.md** (este archivo): documenta la entrega para auditoría, con pruebas.

---

## 1. Checklist de "terminado"

| Punto | Estado | Prueba |
|---|---|---|
| Mínimo 6 tiendas guatemaltecas verificadas | ✅ (Fase 0) | 6 fuentes en `fuentes/REPORTE_FUENTES.md`; muestras de 20 productos c/u en `muestras/` con enlaces 200 |
| El sistema corre solo cada hora, 3 corridas seguidas sin error | ⬜ pendiente | — |
| El usuario recibió ≥1 alerta real en Telegram (no de prueba) | ⬜ pendiente | — |
| La página web abre en el celular, con filtros y última actualización en hora GT | ⬜ pendiente | — |
| PWA instalable (manifest + service worker + ícono) | 🟡 código listo, prueba en celular pendiente | `web/manifest.json` (nombre "Cazador GT", `display: standalone`), `web/service-worker.js` (cachea la última lista), `web/icon-192.png` + `web/icon-512.png` + `web/icon.svg` generados |
| Ninguna alerta 🔥/🚨 sin historial que la respalde | ✅ (Fase 2) | pruebas unitarias `test_descuento_falso_inflado` y `test_sin_historial_cap_loca` (0 fallos); primera corrida real: **0 🔥/🚨, solo 218 ⚡** |
| Si se apaga una tienda (URL falsa), avisa y las demás siguen | ⬜ pendiente | — |
| README en español y `config.yml` explicado | ⬜ pendiente | — |
| Entrega: link de la página, link del bot, 5 líneas de uso | ⬜ pendiente | — |

---

## 2. Tabla de fuentes

| Tienda | Método | Productos (última corrida) | Estado |
|---|---|---|---|
| Walmart GT | API (VTEX) | 200 | ✅ activa |
| Elektra GT | API (VTEX) | 200 | ✅ activa |
| Cemaco | API (VTEX) | 200 | ✅ activa |
| Simán | API (VTEX) | 200 | ✅ activa |
| Intelaf | HTML (ld+json) | 40 | ✅ activa |
| Pacifiko | HTML (ld+json) | 40 | ✅ activa |

> Última corrida de recolectores (Fase 1): **880 productos** totales, 427 con
> "antes > actual" (descuento real), 0 precios inválidos. Comando:
> `python -m pruebas.probar_recolectores` → "OK: todas las fuentes trajeron productos".

---

## 3. Decisiones distintas al prompt (y por qué)

- *(se irán anotando según surjan. Hasta ahora:)*
- **Solo biblioteca estándar de Python** en la Fase 0 en vez de `httpx`/`selectolax`:
  el entorno del agente no permite instalar dependencias fuera del workspace
  (`pip install` falla por sandbox). Se usó `urllib` + `gzip` + `json`, sin perder
  funcionalidad. En GitHub Actions sí se podrá instalar `httpx` con normalidad si se
  desea, pero se mantiene sin dependencias para robustez.
- **6 fuentes en lugar de "mínimo 6"** ya en Fase 0, incluyendo 2 no-VTEX (Intelaf y
  Pacifiko) que aportan diversidad de plataformas al motor.
- **"mínimo histórico" se mide contra días anteriores** (no contra el precio de hoy):
  si no, en el primer día de vida de un producto aparecería como "mínimo histórico"
  sin historia real. Añadido tras verlo en la salida real.
- **Ícono de la PWA generado por código** (PNG sin dependencias) en vez de pedir un
  diseñador, porque el entorno no permite instalar Pillow.

---

## 4. Errores conocidos / pendientes (con honestidad)

- **Simán** publica `link` incorrecto en su API (da 400); se usa la plantilla
  `/producto/{linkText}/p` (verificada 200). Documentado en `REPORTE_FUENTES.md`.
- **Walmart GT** falla verificación TLS (cadena incompleta del CDN); se lee con SSL
  sin verificar. Es solo lectura de precios públicos.
- **La Curacao** (Magento) y **Novex** son candidatas a añadir, no bloquean el mínimo.
- Sin acceso de administrador al entorno local; la automatización final vivirá en
  GitHub Actions (no depende de esta PC).
- **La web aún no se probó en un navegador/celular**: está construida y los datos son
  correctos, pero la prueba real de instalación PWA requiere publicarla en GitHub
  Pages (Fase 5). Se marcará ✅ al verificar el link en un teléfono.

---

## 5. Links

| Elemento | Link |
|---|---|
| Repositorio | ⬜ pendiente (aún no se crea) |
| Página web | ⬜ pendiente |
| Últimas 3 corridas de Actions | ⬜ pendiente |
| Bot de Telegram | ⬜ pendiente |

---

## 6. Evidencia por fase (comandos y salidas)

**Fase 0 — Fuentes.** `python scripts/sondear_fuentes.py` → 15 tiendas sondeadas;
6 aprobadas, 9 descartadas con motivo (detalle en `fuentes/REPORTE_FUENTES.md`).
`python scripts/check_links.py` → enlaces de producto 200 (Salvo Simán, corregido a
`/producto/{linkText}/p`).

**Fase 1 — Recolectores.** `python -m pruebas.probar_recolectores`
→ `walmart 200 · elektra 200 · cemaco 200 · siman 200 · intelaf 40 · pacifiko 40`
= **880 productos**, "OK: todas las fuentes trajeron productos". Resumen:
427 con descuento real, 0 precios inválidos.

**Fase 2 — Historial y motor.** `python -m unittest pruebas.test_motor`
→ `Ran 13 tests ... OK` (0 fallos). `python -m motor.pipeline`
→ **220 ofertas** (218 ⚡ + 2 agotadas), 6 fuentes OK, 0 fallos, 62.8 s,
historial con 880 observaciones en `data/historial/*.jsonl`.

> Nota de diseño: la primera corrida solo produce nivel ⚡ (aún sin historial), que es
> exactamente la regla "sin historial → máximo ⚡". Las 🔥/🚨 aparecerán cuando haya
> ≥3 días de observaciones.
