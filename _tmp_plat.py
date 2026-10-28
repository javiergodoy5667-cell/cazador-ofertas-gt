import re, sys, json
sys.path.insert(0, ".")
from recolectores import _base
for nombre, host in (("Novex","www.novex.com.gt"), ("Max","www.max.com.gt")):
    st,_f,body = _base.get(f"https://{host}/", host=host, reintentos=1, timeout=20)
    low = body.lower() if body else ""
    plataformas = [s for s in ("vtex","shopify","magento","woocommerce","prestashop","bigcommerce","salesforce","sap","bcapp","jumpseller") if s in low]
    print(nombre, st, "| plataformas:", plataformas)
    # Product ld+json en home
    tipos = re.findall(r'"@type"\s*:\s*"(\w+)"', body or "")
    from collections import Counter
    print("   tipos ld+json:", dict(Counter(tipos)))
