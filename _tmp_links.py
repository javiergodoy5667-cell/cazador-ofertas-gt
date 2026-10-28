import re, sys, json
sys.path.insert(0, ".")
from recolectores import _base
for nombre, host in (("Novex","www.novex.com.gt"), ("Max","www.max.com.gt")):
    st,_f,body = _base.get(f"https://{host}/", host=host, reintentos=1, timeout=20)
    if st != 200:
        print(nombre, "home", st); continue
    hrefs = re.findall(r'href="([^"]+)"', body)
    cands = [h for h in hrefs if re.search(r'/(producto|product|p|item|articulo)/', h)]
    print(nombre, "home", len(body), "| enlaces producto:", len(cands))
    for h in list(dict.fromkeys(cands))[:3]:
        print("   ", h[:110])
