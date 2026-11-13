#!/usr/bin/env python3
# 사용: python3 뽑기.py 1-3 2   → 1권 3장의 2번째 장면(장면.json 차례) 행이 근거에 든 정리본 줄을
#       결과/1-3_2_목록.json에 적음. 장면 원문을 단락으로 나눈 목록도 함께 적음
#       (공백으로 시작하는 줄에서 새 단락, 빈 줄에서 단락 끝)
import re, sys, glob, os, json
T = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(T, '..', '정리본')
tag, n = sys.argv[1], int(sys.argv[2])
scenes = json.load(open(os.path.join(T, '장면.json'), encoding='utf-8'))
lo, hi = map(int, scenes[tag][n - 1].split('~'))
files = sorted([f for f in glob.glob(D + '/*.md') if re.match(r'\d+_', os.path.basename(f))],
               key=lambda f: int(os.path.basename(f).split('_')[0])) + [D + '/표기와 원문 문제.md']
cit = re.compile(r'(?<![\d-])(\d)-(\d{1,2})\(([^)]*)\)')
rows = []
for f in files:
    for i, l in enumerate(open(f, encoding='utf-8'), 1):
        if not l.startswith('| '):
            continue
        hit = False
        for m in cit.finditer(l):
            if f'{m.group(1)}-{m.group(2)}' != tag:
                continue
            for part in m.group(3).split(','):
                nums = re.findall(r'\d+', part)
                if nums and int(nums[0]) <= hi and int(nums[-1]) >= lo:
                    hit = True
        if hit:
            rows.append({'줄': f'{os.path.basename(f)}:{i}', '원래 줄': l.rstrip('\n')})
src = {'1': 'eun01_1.txt', '2': 'eun02.txt', '3': 'eun03.txt', '4': 'eun04.txt'}[tag.split('-')[0]]
SRC = open(os.path.join(T, '..', '원문', src), encoding='utf-8').read().split('\n')
paras, cur = [], None
for i in range(lo, hi + 1):
    l = SRC[i - 1]
    if not l.strip():
        cur = None; continue
    if cur is None or l[0] in ' \t\u3000':
        cur = [i, i, l.strip()[:40]]; paras.append(cur)
    else:
        cur[1] = i
paras = [{'단락': k, '행': f'{a}-{b}', '첫머리': h} for k, (a, b, h) in enumerate(paras, 1)]
out = {'장': tag, '장면': n, '행': f'{lo}~{hi}', '줄 수': len(rows), '단락 수': len(paras), '목록': rows, '단락': paras}
p = os.path.join(T, '결과', f'{tag}_{n}_목록.json')
json.dump(out, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(f'{tag} 장면 {n} ({lo}~{hi}): {len(rows)}줄, 단락 {len(paras)} → {p}')
