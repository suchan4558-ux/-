#!/usr/bin/env python3
# 사용: python3 검사.py 1-3 2  → 결과/1-3_2_판정.json을 검사. 통과면 "통과", 아니면 걸린 것을 모두 적고 끝 코드 1
import sys, os, json, re
T = os.path.dirname(os.path.abspath(__file__))
tag, n = sys.argv[1], int(sys.argv[2])
v = tag.split('-')[0]
src = {'1': 'eun01_1.txt', '2': 'eun02.txt', '3': 'eun03.txt', '4': 'eun04.txt'}[v]
SRC = open(os.path.join(T, '..', '원문', src), encoding='utf-8').read().split('\n')
lst = json.load(open(os.path.join(T, '결과', f'{tag}_{n}_목록.json'), encoding='utf-8'))
lo, hi = map(int, lst['행'].split('~'))
bad = []
try:
    res = json.load(open(os.path.join(T, '결과', f'{tag}_{n}_판정.json'), encoding='utf-8'))
except Exception as e:
    print('판정 파일을 읽을 수 없음:', e); sys.exit(1)
ws = re.compile(r'\s+')
def norm(s): return ws.sub('', s)
def chk_quotes(where, qs):
    if not isinstance(qs, list) or not qs:
        bad.append(f'{where}: 인용 없음'); return
    for q in qs:
        r, g = str(q.get('행', '')), q.get('구절', '')
        m = re.fullmatch(r'(\d+)(?:-(\d+))?', r)
        if not m: bad.append(f'{where}: 행 꼴 틀림 "{r}"'); continue
        a = int(m.group(1)); b = int(m.group(2) or a)
        if a > b or a < lo or b > hi: bad.append(f'{where}: 행 {r}이 장면 범위 {lo}~{hi} 밖'); continue
        if len(norm(g)) < 4: bad.append(f'{where}: 구절이 너무 짧음 "{g}"'); continue
        if '…' in g or '...' in g.replace('......', ''):
            pass
        if norm(g) not in norm(''.join(SRC[a - 1:b])):
            bad.append(f'{where}: 인용 "{g[:40]}"이 원문 {r}행에 없음')
ref_item = r'\d+-\d+\((?:\d+(?:-\d+)?)(?:, \d+(?:-\d+)?)*\)'
ref_re = re.compile(r'^' + ref_item + r'(?:, ' + ref_item + r')*$')
def chk_row(where, row, fname):
    if not isinstance(row, str) or not row.startswith('| ') or not row.rstrip().endswith('|'):
        bad.append(f'{where}: 고친 줄 꼴 틀림'); return
    cells = [c.strip() for c in row.rstrip().split('|')[1:-1]]
    need = 4 if fname == '표기와 원문 문제.md' else 5
    if len(cells) != need: bad.append(f'{where}: 고친 줄 칸 수 {len(cells)} (필요 {need})'); return
    refcell = cells[3] if fname == '표기와 원문 문제.md' and cells[0].isdigit() is False else cells[-1]
    if fname != '표기와 원문 문제.md' and not ref_re.match(cells[4]):
        bad.append(f'{where}: 고친 줄 근거 꼴 틀림 "{cells[4][:50]}"')
want = [r['줄'] for r in lst['목록']]
orig = {r['줄']: r['원래 줄'] for r in lst['목록']}
got = [p.get('줄') for p in res.get('판정', [])]
miss = [x for x in want if x not in got]
extra = [x for x in got if x not in want]
dup = sorted({x for x in got if got.count(x) > 1})
if miss: bad.append(f'판정 빠진 줄 {len(miss)}: ' + ', '.join(miss[:20]))
if extra: bad.append(f'목록에 없는 줄 {len(extra)}: ' + ', '.join(extra[:20]))
if dup: bad.append('겹친 줄: ' + ', '.join(dup[:20]))
cit = re.compile(r'(?<![\d-])(\d)-(\d{1,2})\(([^)]*)\)')
def spans(row):
    out = []
    for m in cit.finditer(row or ''):
        if f'{m.group(1)}-{m.group(2)}' != tag: continue
        for part in m.group(3).split(','):
            nums = re.findall(r'\d+', part)
            if nums: out.append((int(nums[0]), int(nums[-1])))
    return out
def qspan(q):
    m = re.fullmatch(r'(\d+)(?:-(\d+))?', str(q.get('행', '')))
    return (int(m.group(1)), int(m.group(2) or m.group(1))) if m else None
for p in res.get('판정', []):
    w = p.get('줄'); k = p.get('판정')
    if k not in ('맞음', '고침', '남은 것'): bad.append(f'{w}: 판정 값 "{k}"'); continue
    chk_quotes(w, p.get('인용'))
    sp = [(a, b) for a, b in spans(orig.get(w)) + spans(p.get('고친 줄')) if a <= hi and b >= lo]
    qs = [qspan(q) for q in (p.get('인용') or []) if isinstance(q, dict)]
    if sp and not any(q and any(q[0] <= b + 2 and q[1] >= a - 2 for a, b in sp) for q in qs):
        bad.append(f'{w}: 인용 행이 그 줄의 이 장면 근거 행({", ".join(f"{a}-{b}" for a, b in sp)})과 겹치지 않음')
    if k == '고침':
        if not p.get('까닭'): bad.append(f'{w}: 까닭 없음')
        chk_row(w, p.get('고친 줄'), str(w).split(':')[0])
        if p.get('고친 줄', '').strip() == orig.get(w, '').strip(): bad.append(f'{w}: 고친 줄이 원래 줄과 같음')
    if k == '남은 것':
        for f in ('까닭', '문구 안', '자리'):
            if not p.get(f): bad.append(f'{w}: {f} 없음')
for j, p in enumerate(res.get('빠진 것', []), 1):
    w = f'빠진 것 {j}'; k = p.get('종류')
    if k not in ('근거 덧붙임', '남은 것'): bad.append(f'{w}: 종류 값 "{k}"'); continue
    chk_quotes(w, p.get('인용'))
    if not p.get('내용'): bad.append(f'{w}: 내용 없음')
    if k == '근거 덧붙임':
        fn = str(p.get('줄', '')).split(':')
        if len(fn) != 2 or not fn[1].isdigit(): bad.append(f'{w}: 줄 꼴 틀림'); continue
        path = os.path.join(T, '..', '정리본', fn[0])
        if not os.path.exists(path): bad.append(f'{w}: 파일 없음 {fn[0]}'); continue
        cur = open(path, encoding='utf-8').read().split('\n')[int(fn[1]) - 1]
        new = p.get('고친 줄', '')
        chk_row(w, new, fn[0])
        if tag + '(' not in new: bad.append(f'{w}: 고친 줄에 {tag} 근거가 없음')
        strip = lambda s: [c.strip() for c in s.rstrip().split('|')[1:-2]]
        if strip(cur) != strip(new): bad.append(f'{w}: 근거 칸 말고 다른 칸이 바뀜(근거만 덧붙여야 함)')
    else:
        for f in ('문구 안', '자리', '까닭'):
            if not p.get(f): bad.append(f'{w}: {f} 없음')
if bad:
    print(f'{tag} 장면 {n}: 걸림 {len(bad)}'); print('\n'.join(bad)); sys.exit(1)
c = {k: sum(1 for p in res['판정'] if p['판정'] == k) for k in ('맞음', '고침', '남은 것')}
print(f'{tag} 장면 {n}: 통과. 판정 {len(got)}줄 {c}, 빠진 것 {len(res.get("빠진 것", []))}건')
