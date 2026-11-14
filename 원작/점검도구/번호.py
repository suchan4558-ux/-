#!/usr/bin/env python3
# 사용: python3 번호.py 1-3 2  → 결과/1-3_2_기록.json의 사실에 번호를 1부터 차례로(단락 차례, 단락 안에서는 적힌 차례) 다시 매김.
#       다른 파일에 매기려면 셋째 인자로 기록 파일 경로를 줌.
#       줄, 남는 사실, 넣음, 남은 것이 사실을 번호로 가리키고 있으면 새 번호로 함께 바꿈(이름표로 가리킨 것은 그대로 둠).
#       옛 번호가 겹쳐 있는데 번호로 가리킨 곳이 있으면 어느 사실인지 알 수 없으므로 매기지 않고 멈춤.
import sys, os, json
T = os.path.dirname(os.path.abspath(__file__))
tag, n = sys.argv[1], sys.argv[2]
p = sys.argv[3] if len(sys.argv) > 3 else os.path.join(T, '결과', f'{tag}_{n}_기록.json')
d = json.load(open(p, encoding='utf-8'))
facts = [f for para in d.get('단락', []) for f in (para.get('사실') or [])]
old = [f.get('번호') for f in facts]
refs = []   # (담긴 것, 열쇠나 자리)
for sec in ('줄', '넣음', '남은 것'):
    for e in d.get(sec, []):
        if isinstance(e.get('사실'), list):
            refs += [(e['사실'], i) for i, x in enumerate(e['사실']) if isinstance(x, int)]
for e in d.get('남는 사실', []):
    if isinstance(e.get('사실'), int): refs.append((e, '사실'))
if refs:
    ints = [x for x in old if isinstance(x, int)]
    if len(ints) != len(old) or len(set(ints)) != len(ints):
        sys.exit('옛 번호가 없거나 겹친 사실이 있는데 번호로 가리킨 곳이 있음: 매기지 않음')
    m = {x: i for i, x in enumerate(old, 1)}
    lost = sorted({c[k] for c, k in refs if c[k] not in m})
    if lost: sys.exit(f'없는 사실 번호를 가리킨 곳이 있음: {lost}')
    for c, k in refs: c[k] = m[c[k]]
changed = sum(1 for i, f in enumerate(facts, 1) if f.get('번호') != i)
for i, f in enumerate(facts, 1):
    rest = {k: v for k, v in f.items() if k != '번호'}
    f.clear(); f['번호'] = i; f.update(rest)
json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(f'{tag} 장면 {n}: 사실 {len(facts)}에 번호를 매김(바뀐 번호 {changed}, 번호로 가리킨 곳 {len(refs)})')
