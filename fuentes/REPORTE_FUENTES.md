# Reporte de fuentes — Cazador de Ofertas GT

Fecha de verificación: **2026-10-27** (hora de Guatemala). Todo fue probado en vivo,
sin suposiciones. Herramienta de sondeo: `scripts/sondear_fuentes.py` (solo biblioteca
estándar de Python, sin dependencias).

---

## Resumen

| # | Tienda | Plataforma | Vía de datos | Veredicto |
|---|---|---|---|---|
| 1 | Walmart GT | VTEX | API público de catálogo | ✅ usar |
| 2 | Elektra GT | VTEX | API público de catálogo | ✅ usar |
| 3 | Cemaco | VTEX | API público de catálogo | ✅ usar |
| 4 | Simán | VTEX | API público de catálogo | ✅ usar |
| 5 | Intelaf | Propio (HTML) | Sitemap + microdatos `ld+json` | ✅ usar |
| 6 | Pacifiko | Propio (HTML) | Sitemap + microdatos `ld+json` | ✅ usar |

Cada una tiene un archivo de muestra con **20 productos reales** (nombre, precio,
enlace verificado) en la carpeta `muestras/`:

- `muestras/walmart-gt.json`, `muestras/elektra-gt.json`, `muestras/cemaco.json`,
  `muestras/siman.json`, `muestras/intelaf.json`, `muestras/pacifiko.json`.

---

## Detalle por fuente (aprobada)

### 1. Walmart GT — ✅
- **Responde:** sí (`https://www.walmart.com.gt`, HTTP 200). Precios visibles sin login.
- **Plataforma:** VTEX. Confirmado probando
  `https://www.walmart.com.gt/api/catalog_system/pub/products/search?ft=televisor&_from=0&_to=9`
  (devuelve JSON con `items[].sellers[].commertialOffer.Price` y `ListPrice`).
- **Nota técnica:** su certificado TLS falla la verificación por cadena incompleta del
  CDN; se accede con SSL sin verificar (lectura de datos públicos).
- **Ofertas:** se detectan comparando `Price` (venta) contra `ListPrice` (precio "antes")
  y contra el historial propio. No se depende de una URL de ofertas.
- **robots.txt:** accesible; no bloquea el API de catálogo.
- **Modo de compra:** en línea.
- **Veredicto:** ✅ usar (VTEX).

### 2. Elektra GT — ✅
- **Responde:** sí (`https://www.elektra.com.gt`, con `www`, HTTP 200).
- **Plataforma:** VTEX (API de catálogo responde **206 Partial Content**, no 200).
- **Ofertas:** vía `Price` vs `ListPrice` + historial.
- **robots.txt:** no bloquea el API.
- **Modo de compra:** en línea.
- **Veredicto:** ✅ usar (VTEX).

### 3. Cemaco — ✅
- **Responde:** sí (`https://www.cemaco.com`, HTTP 200).
- **Plataforma:** VTEX (API responde 206). Enlace canónico `/{linkText}/p` verificado 200.
- **robots.txt:** bloquea `/liquidacion`, `/busca/` y rutas de cuenta/carrito. Se respeta:
  se recolecta por API de catálogo y categorías públicas, no por `/liquidacion`.
- **Modo de compra:** en línea.
- **Veredicto:** ✅ usar (VTEX).

### 4. Simán — ✅
- **Responde:** sí (`https://www.siman.com`, HTTP 200).
- **Plataforma:** VTEX (API responde 206). **Ojo:** el enlace canónico real es
  `https://www.siman.com/producto/{linkText}/p` (el campo `link` del API está mal en su
  configuración y da 400; se usa la plantilla `/producto/{linkText}/p`, verificada 200).
- **robots.txt:** no bloquea el API.
- **Modo de compra:** en línea.
- **Veredicto:** ✅ usar (VTEX).

### 5. Intelaf — ✅
- **Responde:** sí (`https://www.intelaf.com`, HTTP 200). Precios visibles sin login.
- **Plataforma:** propia (no VTEX/Shopify/Magento). El `sitemap.xml` lista **4,452 URLs**
  de producto bajo `/precios_stock_detallado/...`; cada página lleva microdatos
  `application/ld+json` tipo `Product` con `offers.price` y `priceCurrency: GTQ`.
- **Ofertas:** Intelaf publica solo precio actual (sin "antes"); el descuento real se
  calcula contra el historial propio (ideal para el motor de puntaje).
- **robots.txt:** solo bloquea `/docs/` y `/App/`. Se respeta.
- **Modo de compra:** en línea (tienen página de pagos y envíos).
- **Veredicto:** ✅ usar (HTML + ld+json).

### 6. Pacifiko — ❌ descartada (auditoría 2026-10-27)
- **Responde local:** sí (`https://www.pacifiko.com`, HTTP 200, precios sin login).
- **Plataforma:** propia (sitemap `pids-N.xml` + microdatos `ld+json`).
- **Problema:** funciona desde IP residencial (40 productos) pero devuelve **0 productos
  desde los servidores de GitHub Actions** (`estado: ROTA`). Bloquea las IP de datacenter
  (anti-bot).
- **Motivo de descarte:** no se puede corregir sin un proxy, y el proyecto prohíbe
  servicios para saltar bloqueos/captchas.
- **Veredicto:** ❌ descartar (bloquea IP de datacenter). Retirada de la corrida.

---

## Fuentes descartadas o pendientes (con motivo)

| Tienda | Motivo | Veredicto |
|---|---|---|
| Kemik (`kemik.gt`) | HTTP 403 y `robots.txt` prohíbe todo (`Disallow: /`) | ❌ descartar |
| PriceSmart GT | Requiere membresía; precios tras login; Cloudflare anti-bot | ❌ descartar |
| Office Depot GT | HTTP 403 en portada y robots | ❌ descartar |
| Agencias Way | `agenciasway.com.gt` responde 403; `agenciasway.com` está aparcado | ❌ descartar |
| La Torre (`latorre.com.gt`) | No responde (timeout) desde esta red; posible geo-bloqueo | ❌ descartar por ahora |
| Tiendas Max (`max.com.gt`) | Next.js (contenido por JavaScript); sitemap con enlaces rotos | ⚠️ requeriría Playwright |
| Novex (`novex.com.gt`) | Catálogo con 3,301 URLs pero detalle de producto no mapeado aún | ⚠️ pendiente |
| La Curacao (`lacuracaonline.com`) | Magento; la categoría sí trae precios en HTML | ⚠️ candidata a añadir |
| Super 24 | Verificación de edad al entrar; sitemap casi vacío | ❌ descartar |
| Paiz / Despensa Familiar | Paiz falla SSL y redirige a Walmart (mismo grupo); Despensa no resuelve | ❌ descartar (Walmart ya cubre el grupo) |
| Falabella GT / EPA / Decathlon / Sportline | Dominio no resuelve o sin contenido útil | ❌ descartar |

---

## Facebook Marketplace (regla especial)

**No se hará scraping de Facebook** (exige sesión y viola sus términos). En la página
web habrá una sección "Buscar en Marketplace" con enlaces ya armados a
`facebook.com/marketplace` con ubicación Guatemala, ordenado por más reciente y con
precio máximo, según palabras clave del usuario. El formato del enlace se verificará
abriéndolo al construir la página (Fase 4).

---

## Hallazgos técnicos que condicionan las siguientes fases

1. **VTEX responde 206**, no 200: los recolectores deben aceptar ambos códigos.
2. **Walmart** requiere SSL sin verificar (cadena TLS incompleta de su CDN).
3. **Simán** usa la plantilla de URL `/producto/{linkText}/p` (su campo `link` es erróneo).
4. **Pacifiko** conserva el parámetro `pid` en la URL; sin él el enlace puede fallar.
5. **Intelaf y Pacifiko** no publican "precio antes": el descuento real se mide contra
   el historial propio, que es justo el diseño del motor de puntaje.
