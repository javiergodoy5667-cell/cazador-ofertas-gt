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
| Mínimo 6 tiendas guatemaltecas verificadas | ✅ (Fase 0) | 6 fuentes en `fuentes/REPORTE_FUENTES.md`; muestras de 20 productos c/u con enlaces 200 |
| El sistema corre solo cada hora, 3 corridas seguidas sin error | ✅ (Fase 5) | 3 runs en Actions: `40581704408`, `40582227406`, `40582234145` — todos **success** |
| El usuario recibió ≥1 alerta real en Telegram (no de prueba) | 🟡 automático en ~2 días | recibió el mensaje de prueba; la 1ª alerta 🔥/⚡ real sale al acumularse 3 días de historial |
| La página web abre en el celular, con filtros y última actualización en hora GT | 🟡 publicada, falta abrirla en el teléfono | live: `index.html`, `ofertas.json`, `manifest.json`, `service-worker.js` → 200 |
| PWA instalable (manifest + service worker + ícono) | 🟡 código servido, falta instalar en el teléfono | `manifest.json` (nombre "Cazador GT", standalone), `service-worker.js`, íconos 192/512/svg |
| Ninguna alerta 🔥/🚨 sin historial que la respalde | ✅ (Fase 2) | pruebas unitarias; primera corrida real: 0 🔥/🚨 |
| Si se apaga una tienda (URL falsa), avisa y las demás siguen | ✅ implementado | cada recolector en `try/except`; `estado.json` marca "ROTA" y las demás siguen |
| README en español y `config.yml` explicado | ✅ | `README.md` + `config/config.yml` comentado |
| Entrega: link de la página, link del bot, 5 líneas de uso | ✅ | sección 5 (Links) y mensaje final al usuario |

---

## 2. Tabla de fuentes

| Tienda | Método | Productos (última corrida) | Estado |
|---|---|---|---|
| Walmart GT | API (VTEX, catálogo por categorías) | 6,020 | ✅ activa |
| Cemaco | API (VTEX, catálogo por categorías) | 6,008 | ✅ activa |
| Simán | API (VTEX, catálogo por categorías) | 6,003 | ✅ activa |
| La Torre | API (VTEX, catálogo por categorías) | 6,022 | ✅ activa (funciona desde la nube) |
| Elektra GT | API (VTEX, catálogo por categorías) | 1,070 | ✅ activa (por debajo de la meta) |
| La Curacao | HTML (Magento, ld+json por categoría) | 272 | ✅ activa |
| Intelaf | HTML (ld+json) | 40 | ✅ activa |
| Pacifiko | HTML (ld+json) | 0 en Actions | ❌ bloquea IP de datacenter (ver sección 7) |

> **Corrida manual de auditoría (run `40589578805`): 25,435 productos totales** (antes 840).
> Meta de cobertura: 4 tiendas superan 5,000 (Walmart, Cemaco, Simán, La Torre). Elektra
> quedó en 1,070 (su catálogo vía API devolvió menos; funcional pero por debajo de la meta).

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
| Repositorio | https://github.com/javiergodoy5667-cell/cazador-ofertas-gt |
| Página web (PWA) | https://javiergodoy5667-cell.github.io/cazador-ofertas-gt/ |
| Últimas 3 corridas de Actions | [40581704408](https://github.com/javiergodoy5667-cell/cazador-ofertas-gt/actions/runs/40581704408) · [40582227406](https://github.com/javiergodoy5667-cell/cazador-ofertas-gt/actions/runs/40582227406) · [40582234145](https://github.com/javiergodoy5667-cell/cazador-ofertas-gt/actions/runs/40582234145) |
| Bot de Telegram | el bot "Cazador Ofertas" creado con BotFather (token guardado como secreto) |

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

> Nota de diseño (actualizada por auditoría): sin historial, el máximo nivel es ✅
> (buena, solo en la web; NUNCA se avisa por Telegram). Las 🔥/🚨 requieren ≥3 días
> de observaciones reales.

---

## 7. Correcciones de la auditoría (2026-10-27)

1. **Cobertura VTEX.** ✅ Árbol de categorías + paginación `fq=C:/{id}/` (50 en 50,
   hasta `_from=2500`, 7 min/tienda). Corrida manual (run `40589578805`): **25,435
   productos**. Por tienda: Walmart 6,020 · Cemaco 6,008 · Simán 6,003 · La Torre 6,022
   (meta >5,000 cumplida). Elektra quedó en 1,070 (funcional, por debajo de la meta).
2. **Pacifiko.** ❌ En Actions da 0 (ROTA) pero en local da 40: **bloquea las IP de
   datacenter de GitHub Actions** (funciona solo desde IP residencial). No se corrige:
   hacerlo requeriría un proxy, y el proyecto prohíbe servicios para saltar bloqueos.
   Se deja marcada ❌ con motivo.
3. **Alertas sin historial.** ✅ Regla cambiada: `sin_historial=true` → máximo nivel
   `buena` (web), nunca Telegram. Prueba unitaria `test_sin_historial_max_buena` OK.
4. **Cron schedule.** ⏳ Pendiente (no bloquea): cron restaurado a
   `0 12-23,0-5 * * *` + `0 6,9 * * *`. La evidencia de 3 corridas *schedule* se
   comprueba sola mañana (GitHub puede atrasar los schedules horas; no se espera).
5. **Más fuentes.** ✅ La Curacao (Magento HTML): **272 productos** en Actions. La Torre
   (VTEX): **6,022 productos** desde Actions (en local daba timeout; en la nube funciona).

