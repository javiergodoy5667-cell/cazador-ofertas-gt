# -*- coding: utf-8 -*-
from pathlib import Path
import traceback

base = Path(__file__).resolve().parent.parent / "data"
base.mkdir(parents=True, exist_ok=True)

def intento(nombre):
    p = base / nombre
    try:
        p.write_text("hola\n", encoding="utf-8")
        print(f"OK    {p}")
    except Exception as e:
        print(f"FALLO {p} -> {type(e).__name__}: {e}")

intento("sin_espacio.jsonl")
intento("con espacio.jsonl")
sub = base / "_test_sub"
sub.mkdir(parents=True, exist_ok=True)
intento("_test_sub/dentro.jsonl")
intento("_test_sub/con espacio.jsonl")
