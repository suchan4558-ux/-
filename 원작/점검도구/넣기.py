#!/usr/bin/env python3
# 사용: python3 넣기.py 1-3 2  → 검사를 통과한 결과/1-3_2_기록.json의 고침, 근거 덧붙임, 넣음을 정리본에 넣고
#                              남은 것을 최종점검 남은 것.md에 적음(앞 남은 것은 그 번호 줄 끝에 자리와 원문 행만 덧붙임).
#       넣음은 자리의 줄 바로 뒤에 넣음. 한 파일 안에서는 아래 줄부터 넣어 줄 번호가 밀리지 않게 함.
import json, sys, os, subprocess
T = os.path.dirname(os.path.abspath(__file__)); D = os.path.join(T, '..', '정리본')
tag, n = sys.argv[1], sys.argv[2]
if subprocess.run([sys.executable, os.path.join(T, '검사.py'), tag, n], capture_output=True).returncode != 0:
    sys.exit('검사를 통과하지 못한 기록은 넣지 않음')
d = json.load(open(os.path.join(T, '결과', f'{tag}_{n}_기록.json'), encoding='utf-8'))
files = {}
def L(f):
    if f not in files: files[f] = open(os.path.join(D, f), encoding='utf-8').read().split('\n')
    return files[f]
rep, ins = {}, []
for p in d.get('줄', []):
    if p['처리'] == '고침': rep[p['줄']] = p['고친 줄']
for p in d.get('남는 사실', []):
    if p['처리'] == '근거 덧붙임':
        if rep.get(p['줄'], p['고친 줄']) != p['고친 줄']: sys.exit(f"같은 줄을 다르게 고침: {p['줄']}")
        rep[p['줄']] = p['고친 줄']
for k, new in rep.items():
    f, i = k.split(':'); L(f)[int(i) - 1] = new; print('고침', k)
for j, p in enumerate(d.get('넣음', [])):
    f, i = p['자리'].split(':'); ins.append((f, int(i), -j, p['넣을 줄']))
for f, i, j, row in sorted(ins, key=lambda x: (x[0], -x[1], x[2])):   # 같은 자리에 여럿이면 기록에 적힌 차례대로 놓임
    L(f).insert(i, row); print('넣음', f'{f}:{i} 뒤')
for f, ls in files.items(): open(os.path.join(D, f), 'w', encoding='utf-8').write('\n'.join(ls))
LP = os.path.join(D, '최종점검 남은 것.md')
ls = open(LP, encoding='utf-8').read().rstrip('\n').split('\n')
for x in d.get('남은 것', []):
    head = f"- {x['번호']}. {x['무엇']}."
    if any(l.startswith(head) for l in ls): continue
    ls.append(f"{head} 장과 원문 행: {x['장과 원문 행']}. 종류: {x['종류']}. 문구 안: {x['문구 안']}. 자리: {x['자리']}. 까닭: {x['까닭']}."); print('남은 것', x['번호'])
for x in d.get('앞 남은 것', []):
    add = f" 덧붙임: {x['장과 원문 행']}, 자리 {x['자리']}."
    for j, l in enumerate(ls):
        if l.startswith(f"- {x['번호']}. ") and add not in l: ls[j] = l + add; print('앞 남은 것', x['번호'])
open(LP, 'w', encoding='utf-8').write('\n'.join(ls) + '\n')
