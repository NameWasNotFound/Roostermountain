import re, json, collections

txt = open('raw.txt').read()
lines = txt.split('\n')

comps = []
cur = None
DIV_RE = re.compile(r'^Division (.+?) Class (\S+) Category (.*?)Factor (\S+) Squad (\S+)$')
HDR_RE = re.compile(r'^#(\d+) (.+)$')
STAGE_RE = re.compile(r'^(\d+) ([\d.]+) (-?\d+) (\d+) (\d+) (\d+) (\d+) (\d+) (\d+) (\d+) ([\d.]+)$')

for i, l in enumerate(lines):
    l = l.strip()
    m = HDR_RE.match(l)
    if m and DIV_RE.match(lines[i+1].strip() or ''):
        cur = {'no': int(m.group(1)), 'name': m.group(2).strip(), 'stages': {}}
        d = DIV_RE.match(lines[i+1].strip())
        cur['division'] = d.group(1).strip()
        cur['class'] = d.group(2)
        cur['category'] = d.group(3).strip() or 'None'
        cur['factor'] = d.group(4)
        cur['squad'] = d.group(5)
        comps.append(cur)
        continue
    m = STAGE_RE.match(l)
    if m and cur is not None:
        s = int(m.group(1))
        cur['stages'][s] = dict(hf=float(m.group(2)), pts=int(m.group(3)),
            A=int(m.group(4)), C=int(m.group(5)), D=int(m.group(6)),
            ded=int(m.group(7)), MI=int(m.group(8)), NS=int(m.group(9)),
            PE=int(m.group(10)), time=float(m.group(11)))

print('competitors', len(comps))
stagenos = sorted({s for c in comps for s in c['stages']})
print('stages', stagenos)
# max points per stage
maxpts = {}
for s in stagenos:
    cnt = collections.Counter()
    for c in comps:
        st = c['stages'].get(s)
        if st: cnt[(st['A']+st['C']+st['D']+st['MI'])*5] += 1
    maxpts[s] = max(cnt)
    print(s, cnt.most_common(4))
json.dump({'comps':comps,'maxpts':maxpts}, open('parsed.json','w'))
