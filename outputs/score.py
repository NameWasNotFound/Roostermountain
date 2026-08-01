import json, collections

d = json.load(open('parsed.json'))
comps = d['comps']
maxpts = {int(k): v for k, v in d['maxpts'].items()}
STAGES = sorted(maxpts)

for c in comps:
    c['stages'] = {int(k): v for k, v in c['stages'].items()}

def score(pool, label):
    """IPSC stage-points scoring over a pool of competitors."""
    best = {}
    for s in STAGES:
        hfs = [c['stages'][s]['hf'] for c in pool if s in c['stages']]
        best[s] = max(hfs) if hfs else 0.0
    out = {}
    for c in pool:
        sp = {}
        tot = 0.0
        for s in STAGES:
            st = c['stages'].get(s)
            if st and best[s] > 0:
                p = st['hf'] / best[s] * maxpts[s]
            else:
                p = 0.0
            sp[s] = round(p, 4)
            tot += p
        out[c['no']] = {'stage_pts': sp, 'match_pts': round(tot, 4)}
    winner = max((v['match_pts'] for v in out.values()), default=0) or 1
    ranked = sorted(out.items(), key=lambda kv: -kv[1]['match_pts'])
    for i, (no, v) in enumerate(ranked, 1):
        v['rank'] = i
        v['pct'] = round(v['match_pts'] / winner * 100, 2)
    return out, best

results = {}
results['ALL'], best_all = score(comps, 'ALL')
divs = sorted({c['division'] for c in comps})
stage_best = {'ALL': best_all}
for dv in divs:
    results[dv], b = score([c for c in comps if c['division'] == dv], dv)
    stage_best[dv] = b

# per-competitor rollups
rows = []
for c in comps:
    tot = {'A':0,'C':0,'D':0,'MI':0,'NS':0,'PE':0,'ded':0,'pts':0,'time':0.0}
    for s, st in c['stages'].items():
        for k in ('A','C','D','MI','NS','PE','ded','pts'):
            tot[k] += st[k]
        tot['time'] += st['time']
    tot['time'] = round(tot['time'], 2)
    hits = tot['A']+tot['C']+tot['D']
    rows.append({
        'no': c['no'], 'name': c['name'], 'division': c['division'],
        'category': c['category'], 'factor': c['factor'], 'squad': c['squad'],
        'stagesShot': len(c['stages']),
        'A': tot['A'], 'C': tot['C'], 'D': tot['D'], 'MI': tot['MI'],
        'NS': tot['NS'], 'PE': tot['PE'], 'rawPts': tot['pts'],
        'time': tot['time'],
        'accA': round(tot['A']/hits*100, 1) if hits else 0,
        'hf': {str(s): c['stages'][s]['hf'] for s in c['stages']},
        'stimes': {str(s): c['stages'][s]['time'] for s in c['stages']},
        'overall': results['ALL'][c['no']],
        'div': results[c['division']][c['no']],
    })

payload = {
    'match': 'Rooster Mountain 2026 - Handgun',
    'printed': 'Jul 31, 2026 16:51:16',
    'stages': STAGES,
    'maxpts': maxpts,
    'divisions': divs,
    'competitors': rows,
    'stageBest': {k: {str(s): round(v, 4) for s, v in b.items()} for k, b in stage_best.items()},
}
json.dump(payload, open('results.json','w'))

for r in sorted(rows, key=lambda r: r['overall']['rank'])[:10]:
    print(f"{r['overall']['rank']:>3} {r['overall']['pct']:>6.2f}% {r['overall']['match_pts']:>8.2f}  {r['name']:<26} {r['division']:<18} {r['factor']} {r['category']}")
print()
for dv in divs:
    w = min((r for r in rows if r['division']==dv), key=lambda r: r['div']['rank'])
    print(f"{dv:<18} winner: {w['name']:<26} {w['div']['match_pts']:.2f}")
