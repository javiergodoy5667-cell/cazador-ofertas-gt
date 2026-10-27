# -*- coding: utf-8 -*-
"""
Genera los iconos PNG de la PWA (192 y 512) sin dependencias externas:
fondo naranja con esquinas redondeadas y un simbolo "%" blanco.
El diseño coincide con web/icon.svg.
"""
import struct
import zlib
from pathlib import Path

WEB = Path(__file__).resolve().parent.parent / "web"


def _chunk(tipo, datos):
    c = struct.pack(">I", len(datos)) + tipo + datos
    c += struct.pack(">I", zlib.crc32(tipo + datos) & 0xFFFFFFFF)
    return c


def _escribir_png(path, S, filas):
    raw = b"".join(b"\x00" + b"".join(struct.pack("4B", *px) for px in fila)
                   for fila in filas)
    ihdr = struct.pack(">IIBBBBB", S, S, 8, 6, 0, 0, 0)
    png = (b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", ihdr)
           + _chunk(b"IDAT", zlib.compress(raw, 9)) + _chunk(b"IEND", b""))
    Path(path).write_bytes(png)


def _en_rect_redondeado(x, y, S, R):
    if R <= x <= S - R or R <= y <= S - R:
        return True
    for cx, cy in ((R, R), (S - R, R), (R, S - R), (S - R, S - R)):
        if (x - cx) ** 2 + (y - cy) ** 2 <= R * R:
            return True
    return False


def _dist_segmento(px, py, ax, ay, bx, by):
    vx, vy = bx - ax, by - ay
    wx, wy = px - ax, py - ay
    denom = vx * vx + vy * vy
    t = 0 if denom == 0 else max(0, min(1, (wx * vx + wy * vy) / denom))
    return ((px - (ax + t * vx)) ** 2 + (py - (ay + t * vy)) ** 2) ** 0.5


def generar(S):
    R = S * 0.19
    # circulos del "%"
    c1, r = (S * 0.332, S * 0.293), S * 0.102
    c2 = (S * 0.668, S * 0.707)
    # diagonal
    p1, p2 = (S * 0.293, S * 0.715), (S * 0.707, S * 0.285)
    ancho = S * 0.039

    naranja = (255, 106, 0, 255)
    blanco = (255, 255, 255, 255)
    transparente = (0, 0, 0, 0)

    filas = []
    for y in range(S):
        fila = []
        py = y + 0.5
        for x in range(S):
            px = x + 0.5
            if not _en_rect_redondeado(px, py, S, R):
                fila.append(transparente)
                continue
            en_c1 = (px - c1[0]) ** 2 + (py - c1[1]) ** 2 <= r * r
            en_c2 = (px - c2[0]) ** 2 + (py - c2[1]) ** 2 <= r * r
            en_diag = _dist_segmento(px, py, p1[0], p1[1], p2[0], p2[1]) <= ancho
            fila.append(blanco if (en_c1 or en_c2 or en_diag) else naranja)
        filas.append(fila)
    return filas


if __name__ == "__main__":
    for S in (192, 512):
        filas = generar(S)
        _escribir_png(WEB / f"icon-{S}.png", S, filas)
        print(f"icon-{S}.png generado")
