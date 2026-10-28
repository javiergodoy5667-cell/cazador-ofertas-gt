import json, collections
r = json.load(open('web/ofertas-resumen.json', encoding='utf-8'))
print('total:', len(r))
print('por categoria:'); [(print(f'  {c}: {n}')) for c,n in collections.Counter(x['c'] for x in r).most_common()]
print('por tienda:', dict(collections.Counter(x['t'] for x in r)))
print('por nivel:', dict(collections.Counter(x['lv'] for x in r)))
print('Otros:')
for x in r:
    if x['c'] == '📦 Otros':
        print(f"  {x['t']} | {x['n'][:55]} | Q{x['p']}")
