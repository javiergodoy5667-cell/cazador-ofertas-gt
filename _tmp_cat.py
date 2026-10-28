import json, sys
sys.path.insert(0, ".")
from motor import categorias
r = json.load(open("web/ofertas-resumen.json", encoding="utf-8"))
otros = [x for x in r if x["c"] == "\U0001F4E6 Otros"]
print("Otros antes:", len(otros))
quedan = []
for x in otros:
    nueva = categorias.clasificar("", x["n"])
    if nueva == "\U0001F4E6 Otros":
        quedan.append(x["n"])
print("Otros despues:", len(quedan))
for n in quedan:
    print("   ", n)
