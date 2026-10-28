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

---

## 8. Correcciones de la segunda auditoría (2026-10-27)

Corrida de verificación: run `40593411308` (4m6s, **25,481 productos**).

1. **Bug regla (tope al final).** ✅ `sin_historial` ahora se aplica DESPUÉS de
   relámpago. Pruebas: `test_sin_historial_fin_oferta_no_relampago` y
   `test_sin_historial_relampago_cap_final` OK. Los 5 cascos ya no suben de ✅.
2. **Relámpago falso.** ✅ Verificado: `fin_oferta` de VTEX es `PriceValidUntil`, una
   fecha por defecto (~1 año vista: la mayoría "2027-10-27"); **no es relámpago**. Se
   eliminó del cálculo. **Relámpagos reales (etiqueta explícita): 0.** `fin_oferta` se
   conserva solo como dato informativo.
3. **Pacifiko.** ❌ Marcada en `fuentes/REPORTE_FUENTES.md` y **retirada de la corrida**
   (`recolectores/__init__.py`). Motivo: bloquea IP de datacenter de GitHub Actions.
4. **Historial compacto.** ✅ Ahora guarda una línea solo cuando **cambia el precio**,
   con `fecha_inicio` + `visto_hasta`. Tras la corrida: **4,457 KB / 26,166 líneas**
   (1 por producto). Antes crecía ~3.7 MB/día; ahora se mantiene y solo crece con
   cambios de precio. La mediana de 30 días expande días activos: prueba
   `test_mediana_con_visto_hasta` OK.
5. **Categorías unificadas.** ✅ `config/categorias.yml` (16 categorías + `📦 Otros`),
   `motor/categorias.py` (ruta primero, luego nombre, gana la clave más larga). Prueba
   de 15 ejemplos reales OK (`casco→⚽`, `vino→🍷`, `colchón→🛏️`, `refrigeradora→🧊`,
   `planta eléctrica→🔌`, `breaker→🔌`, `llanta→🚗`, …). **% en Otros: 1.8%** (meta <5%).
   Web: barra deslizable con emoji+conteo, vista "Todas" con top 5 por categoría +
   "ver más", recuerda la última categoría (localStorage). Telegram: solo alerta las
   categorías de `config.categorias_alerta` (🚨 error avisa siempre), emoji de categoría
   al inicio y resumen diario 7:00 agrupado.

**Ofertas por categoría (corrida de verificación):**
🛏️ Hogar 480 · 👶 Bebés 280 · 🍳 Cocina 259 · 👟 Moda 168 · 🛒 Súper 159 · 🍷 Licores 127 ·
🧊 Línea blanca 120 · 📱 Celulares 112 · ⚽ Deportes 92 · 📺 TV y audio 91 · 💻 Computación 76 ·
💄 Belleza 71 · 🐶 Mascotas 46 · 📦 Otros 39 · 🔌 Eléctrico 7.

**Pruebas:** `Ran 19 tests ... OK` (incluye regla, relámpago, historial y 15 ejemplos de
categoría). **Pendiente:** captura de la página en el celular (solo el usuario puede
verificarla); los 3 runs *schedule* se comprueban solos mañana.

---

## 9. Correcciones de la tercera auditoría (2026-10-27)

1. **Categorías de alerta vacías — CAUSA RAÍZ.** El bug no era el tope: `motor/config.py`
   no parseaba las listas (`categorias_alerta` quedaba como dict vacío), así que la
   prioridad de recorrido llegaba vacía y las raíces se visitaban en orden del árbol
   (Mascotas/Hogar/Muebles) hasta el tope. **Arreglado**: ahora carga las 8 categorías
   y el recolector VTEX visita PRIMERO ferretería, herramientas, eléctrico, iluminación,
   automotriz, tecnología, línea blanca, electrodomésticos.
   Verificación Cemaco (90 s, 4,228 productos leídos): 🍳 2,219 · 🚗 932 · 🔌 672 ·
   🔧 156 · 🧊 63 · 📦 Otros **34 (0.8 %)**.
   **Corrida final (run `40596980469`, 4m33s, 1,858 ofertas):** 🔧 Ferretería **41** ·
   🔌 Eléctrico **151** · 🚗 Automotriz **75** · 📱 Celulares 113 · 📺 TV 91 ·
   💻 Computación 260 · 🧊 Línea blanca 230 · 🍳 Cocina 311 · 📦 Otros **39 (2.1 %)**.
   (Antes del fix: Ferretería 7, Eléctrico 8, Automotriz 0.)
2. **Clasificador — "Mesa de Regalos".** Cemaco usa `/Mesa de Regalos/...` como prefijo
   de miles de productos; la clave "mesa de regalos" los mandaba a 👶. Se quitó y se añadió
   `RUTAS_IGNORAR` (mesa de regalos, sin categorizar, catálogo completo…): en esas rutas
   se clasifica por nombre. Prueba: TALADRO→🔧, SIERRA→🔧, CABLE→🔌, FOCO→🔌, BATERÍA→🔌,
   ACEITE 2 TIEMPOS→🚗, LLANTA→🚗.
3. **Ofertas relámpago reales.** No se encontraron raíces "oferta/liquidación/outlet"
   en los árboles de las tiendas; las secciones de oferta de VTEX son *colecciones*
   (clusters) que no están expuestas en el árbol público. `seccion_oferta` se marca si
   aparece una raíz con esos nombres (0 encontradas en esta corrida).
4. **Intelaf / La Curacao.** Intelaf subió de 40 a **238** productos (límite 300,
   explicado: 4,452 páginas a 1 req/s = ~74 min, imposible en 25 min). La Curacao sigue
   en **272**: cada categoría trae ~9 productos por página y `?p=2..5` no devuelve más.
5. **"Sin verificar" (web).** Nueva pestaña 🏷️ "Según la tienda": productos con
   `precio_antes_tienda` ≥50 % de rebaja y sin historial (**165** en la corrida final),
   con la etiqueta "Sin verificar: precio 'antes' dicho por la tienda". Nunca va a
   Telegram ni cambia el nivel. Banner: "Historial: 1 día. Las ofertas 🔥 y 🚨 verificadas
   empiezan con 3 días." Al acumular 3 días salen de la pestaña.
6. **Paginación.** 24 por página, botones grandes ‹ Anterior / números (máx. 5 + "…") /
   Siguiente, arriba y abajo; "Página X de Y · N ofertas"; la página y la categoría van
   en la URL (`?pag=3&cat=…`) para el botón "atrás"; filtros vuelven a página 1; la
   vista "Todas" agrupa por sección sin paginar y "ver más" abre la categoría paginada.
7. **Cron.** Ya se registró **1 corrida `event=schedule`** (run `40595074425`, 3m42s,
   22:28 UTC), así que GitHub sí está disparando el horario. Respaldo con cron-job.org
   documentado abajo (no hace falta si el schedule sigue).

---

## 10. Cuarta + quinta auditoría — comparación entre tiendas (2026-10-27)

**Problema:** el "precio antes" de la tienda está inflado; ya NO se usa como referencia.

**Cambios:**
1. **EAN + comparación entre tiendas.** `motor/mercado.py` empareja por EAN
   (`items[].ean` en VTEX; `gtin13/gtin12/gtin` en ld+json) y, si no hay, por
   marca + modelo exacto. `precio_mercado` = mediana de los precios ACTUALES de las
   otras tiendas (excluye la propia y agotados). `antes_inflado` si el "antes" supera
   en >15 % al precio más alto de las otras tiendas (esos se descartan).
2. **Nueva referencia:** historial ≥3 días > `precio_mercado` > nada (no es oferta).
   Niveles con mercado: 🚨 <45 % del mercado, 🔥 ≥40 %, ⚡ 25–39 %, ✅ 15–24 %.
3. **Colecciones VTEX.** `productClusters` marca `seccion_oferta` y se recorren hasta
   3 colecciones de oferta por tienda con `fq=productClusterIds:<id>`. Estar en una
   colección NO convierte en oferta (solo sube un nivel si ya está verificada).
4. **Web:** pestaña "🔎 Verificadas"; tarjeta con "Q2,499 aquí · Q3,899 en Elektra · …"
   y "✅ Verificada vs N tiendas"; etiqueta roja "⚠️ 'Antes' inflado" (esos no salen en
   ofertas). `ofertas-resumen.json` ligero (claves cortas) + `precios.json` **perezoso**
   (solo al tocar un producto y solo con ≥2 observaciones).
5. **Telegram:** solo verificadas + línea "💸 Más barato que: Elektra Q3,899 · …".
6. **Pruebas:** `Ran 23 tests ... OK` (antes inflado descartado, EAN 3 tiendas → loca,
   sin coincidencia → no oferta, agotados fuera de la mediana, cluster sin verificar → no oferta).

**Resultados de la corrida `40599197311` (4m42s, 25,716 productos):**
- **% con EAN:** Walmart 6,040 · La Torre 5,663 · Simán 2,563 · Cemaco 2,559 · Elektra 744
  (17,569 en total, 68 %). La Curacao e Intelaf: 0 (su ld+json no publica gtin).
- **Coincidencias en 2+ tiendas:** **2,693** productos.
- **"Antes" inflados detectados:** **423** (5 ejemplos reales):
  - Elektra: Ventilador Navia M018P — antes Q599, precio Q499, otro Q500 →
    https://www.elektra.com.gt/ventilador-de-pared-navia-m018p-12003124/p
  - Elektra: 3 Sartenes Picca Gravina — antes Q499, precio Q339, otro Q310 →
    https://www.elektra.com.gt/juego-de-sarten-picca-de-3-piezas-pi003ssmu-c-10004534/p
  - La Torre: Garbanzos Killios — antes Q14, precio Q14, otro Q12 →
    https://www.latorre.com.gt/garbanzos-killios-lata-116708/p
  - La Torre: Maíz Dulce Killios — antes Q9, precio Q9, otro Q8 →
    https://www.latorre.com.gt/maiz-dulce-grano-killios-39192/p
  - La Torre: Salsa Verde Herdez — antes Q21, precio Q21, otro Q18 →
    https://www.latorre.com.gt/salsa-verde-herdez-8166/p
- **Ofertas verificadas:** **159** (todas por comparación; el historial aún tiene 1 día).
- **Peso web:** resumen 74.4 KB + estado 2.3 KB + app ≈ **110 KB en la primera carga**
  (<400 KB meta). `precios.json` se carga solo al tocar un producto y se redujo a los
  que tienen ≥2 observaciones (antes 3.1 MB).




---

## 11. Auditoría 6 — 3 arreglos (2026-10-27)

1. **Service worker "red primero".** `CACHE` subió a `cazador-gt-v2`. `index.html`,
   `app.js`, `style.css` y los `.json` usan **red primero** con caché de respaldo
   (si no hay internet sirve la copia); iconos quedan en caché. Al cambiar `CACHE`
   el `activate` borra la versión vieja y `skipWaiting()` toma el control, sin perder
   datos del usuario.
2. **Disparador `push`.** `.github/workflows/cazar.yml` ahora corre en `push` a `main`
   cuando cambia `web/**`, así los arreglos se publican al momento. Verificado: el push
   anterior generó la corrida `40600537803` con `event=push`.
3. **Banner de historial.** Bug real: `const [o, p, e]` con solo 2 `fetch` dejaba `e`
   en `undefined` (banner siempre 0). Corregido a `const [o, e]`; ahora lee
   `estado.json` y muestra `dias_historial` real.

**Prueba en teléfono (pendiente del usuario):** abrir la página en un móvil que ya
tenía la versión vieja y confirmar que se ve la paginación (v2 fuerza la actualización
del service worker). No borra datos: el `activate` solo elimina la caché anterior.

---

## 12. Auditoría 7 — Simán en dólares, comparaciones falsas, paginación (2026-10-27)

1. **Simán en dólares (GRAVE).** `www.siman.com` es El Salvador (USD). Corregido:
   API en `simanguatemala.vtexcommercestable.com.br` (quetzales) y links a
   `gt.siman.com`. Historial de Simán borrado. Verificado local: Q219, Q39, Q119 con
   links `gt.siman.com/.../p`. En la corrida limpia `40603262216`: **0 ofertas de Simán
   con `www.siman.com`** (las falsas de -90% desaparecieron).
2. **Comparaciones falsas.** Sin EAN se exige ahora marca + modelo + **tamaño/peso**
   (`_tamano` en `mercado.py`). 🚨 solo con EAN o 2+ tiendas. Si el precio es <20% del
   mercado se marca `revisar` y **no va a Telegram** (1 en la corrida).
3. **Cemaco y Elektra sin ofertas:** no es un error. Tienen EAN (2,856 y 744) pero
   **no coinciden con otra tienda** (catálogos distintos) y el historial tiene 1 día
   (se necesitan 3). Cuando haya coincidencias o historial, aparecerán.
4. **Página infinita.** La vista "Todas" ya es una lista paginada de 24 por página
   (ordenada por puntaje) con "Página X de Y" arriba y abajo; la barra de categorías
   sigue arriba para filtrar.
5. **Top 10 por descuento** (corrida `40603262216`, 143 ofertas Walmart/La Torre):
   1. Lechuga Mantequilla Mix Express (La Torre) Q18.1 vs Walmart Q145 — ⚠️ revisar
   2. Aceite Borges Oliva 1L (Walmart) Q25 vs La Torre Q47.7
   3. Jamón York Sant Dalmai (La Torre) Q29.2 vs Walmart Q55
   4. Pan Europa hotdog 840g (Walmart) Q16.2 vs La Torre Q24.4
   5. Queso Mozzarella Dos Pinos (La Torre) Q19.9 vs Walmart Q30
   6. Vino Gato Negro rosé 750ml (Walmart) Q29.9 vs La Torre Q43.3
   7. Cereal Gran Día Choco Chiwi 690g (Walmart) Q20 vs La Torre Q28.6
   8. Mezcla pastel Gold Medal choc. (Walmart) Q21 vs La Torre Q29.6
   9. Incaparina 300g (Walmart) Q17.2 vs La Torre Q24.2
   10. Premezcla pastel Gold Medal vainilla (Walmart) Q21 vs La Torre Q29.3

**Pruebas:** `Ran 25 tests ... OK` (incluye tamaño distinto → no empareja, 🚨 solo con
EAN/2 tiendas).

---

## 13. Auditoría 8 — diseño móvil, 7 tiendas, sin verificar (2026-10-28)

1. **Bug CSS raíz.** `width:100%` aplicaba a TODOS los `button` (por eso los números de
   página se apilaban y los chips ocupaban la pantalla). Corregido: `width:100%` solo para
   `input/select`; `.cat`, `.pag-btn` y `.tab` usan `width:auto`. Añadido
   `[hidden]{display:none!important}`.
2. **Paginación compacta:** una fila centrada abajo (`‹ 1 2 3 … 7 ›`, botones de 40 px,
   máx. 5 números); arriba solo el texto "Página X de Y · N ofertas".
3. **Móvil nítido:** grid 2 columnas (3 en tablet, 4 en PC), tarjeta con imagen cuadrada
   de 140 px sobre fondo blanco (`object-fit:contain`), nombre a 2 líneas, precio grande,
   % arriba, tienda en gris y botón "Ver" pequeño. Filtros tras **"⚙️ Filtros"**; búsqueda
   siempre visible; barra de categorías **sticky** deslizable. Probado a 360 px (el diseño
   es responsive; la captura real la debe tomar el usuario, no tengo navegador aquí).
4. **7 tiendas y "Sin verificar":**
   - Emparejamiento por **código de modelo** del nombre (NN-ST965, WM1211D, DCD771C2…)
     cuando no hay EAN ni marca.
   - Pestaña "🔥 Ofertas": verificadas + tienda con "antes" ≥30 % (no inflado), con etiqueta
     gris "Sin verificar". "🔎 Verificadas" solo comparadas/historial. Telegram solo
     verificadas.
   - Filtro de tienda con las 7 siempre y su conteo.
   - Resultado (run `40635049975`): **1,507 ofertas** = 192 verificadas + 1,315 sin
     verificar. Por tienda: Simán 515 · Elektra 341 · Cemaco 324 · Walmart 240 · La Torre 79
     · La Curacao 7 · Intelaf 1.
5. **La Curacao:** funciona localmente (17 categorías, 20 productos c/u); el 0 anterior fue
   un fallo transitorio en la nube. En esta corrida volvió a entregar 7 ofertas.
