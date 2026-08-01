import json, collections

d = json.load(open('parsed.json'))
comps = d['comps']
for c in comps:
    c['stages'] = {int(k): v for k, v in c['stages'].items()}

MINOR_ONLY = {'Optics', 'Production Optics'}
changed = []
for c in comps:
    if c['division'] in MINOR_ONLY and c['factor'] == 'Major':
        c['origFactor'] = 'Major'
        c['factor'] = 'Minor'
        for s, st in c['stages'].items():
            st['origPts'], st['origHf'] = st['pts'], st['hf']
            st['pts'] = st['A']*5 + st['C']*3 + st['D']*1
            pen = 10*(st['MI']+st['NS']+st['PE'])
            st['hf'] = round(max(0.0, (st['pts']-pen)/st['time']), 4) if st['time'] else 0.0
        changed.append(c)
print('reclassified:', [(c['no'], c['name'], c['division']) for c in changed])

maxpts = {}
STAGES = sorted({s for c in comps for s in c['stages']})
for s in STAGES:
    cnt = collections.Counter((st['A']+st['C']+st['D']+st['MI'])*5
                              for c in comps if (st := c['stages'].get(s)))
    maxpts[s] = max(cnt)

def score(pool):
    best = {s: max([c['stages'][s]['hf'] for c in pool if s in c['stages']] or [0.0]) for s in STAGES}
    out = {}
    for c in pool:
        sp, tot = {}, 0.0
        for s in STAGES:
            st = c['stages'].get(s)
            p = st['hf']/best[s]*maxpts[s] if st and best[s] > 0 else 0.0
            sp[s] = round(p, 4); tot += p
        out[c['no']] = {'stage_pts': sp, 'match_pts': round(tot, 4)}
    win = max((v['match_pts'] for v in out.values()), default=0) or 1
    for i, (no, v) in enumerate(sorted(out.items(), key=lambda kv: -kv[1]['match_pts']), 1):
        v['rank'] = i; v['pct'] = round(v['match_pts']/win*100, 2)
    return out, best

results, stage_best = {}, {}
results['ALL'], stage_best['ALL'] = score(comps)
divs = sorted({c['division'] for c in comps})
for dv in divs:
    results[dv], stage_best[dv] = score([c for c in comps if c['division'] == dv])

rows = []
for c in comps:
    t = collections.Counter()
    time = 0.0
    for s, st in c['stages'].items():
        for k in ('A','C','D','MI','NS','PE','pts'): t[k] += st[k]
        time += st['time']
    hits = t['A']+t['C']+t['D']
    rows.append({'no': c['no'], 'name': c['name'], 'division': c['division'],
        'category': c['category'], 'factor': c['factor'], 'squad': c['squad'],
        'reclassed': 'origFactor' in c, 'stagesShot': len(c['stages']),
        'A': t['A'], 'C': t['C'], 'D': t['D'], 'MI': t['MI'], 'NS': t['NS'], 'PE': t['PE'],
        'rawPts': t['pts'], 'time': round(time, 2),
        'accA': round(t['A']/hits*100, 1) if hits else 0,
        'hf': {str(s): c['stages'][s]['hf'] for s in c['stages']},
        'stimes': {str(s): c['stages'][s]['time'] for s in c['stages']},
        'overall': results['ALL'][c['no']], 'div': results[c['division']][c['no']]})

json.dump({'match': 'Rooster Mountain 2026 - Handgun', 'printed': 'Jul 31, 2026 16:51:16',
    'stages': STAGES, 'maxpts': maxpts, 'divisions': divs, 'competitors': rows,
    'reclassNote': True,
    'stageBest': {k: {str(s): round(v,4) for s,v in b.items()} for k,b in stage_best.items()}},
    open('/tmp/results2.json','w'))

for r in sorted(rows, key=lambda r: r['overall']['rank'])[:8]:
    print(f"{r['overall']['rank']:>3} {r['overall']['pct']:>6.2f}% {r['overall']['match_pts']:>8.2f}  {r['name']:<24} {r['division']:<18}{'*RECLASSED' if r['reclassed'] else ''}")
print()
for c in changed:
    r = [x for x in rows if x['no'] == c['no']][0]
    print(f"#{r['no']} {r['name']:<22} {r['division']:<18} div {r['div']['rank']} ({r['div']['pct']}%)  overall {r['overall']['rank']}")
