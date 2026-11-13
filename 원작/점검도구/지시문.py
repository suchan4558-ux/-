#!/usr/bin/env python3
# 사용: python3 지시문.py 1-3 2  → 그 장면을 맡길 에이전트 지시문을 출력(자료를 모두 넣음)
import sys, os, json, re, glob
T = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(T, '..', '정리본')
tag, n = sys.argv[1], int(sys.argv[2])
v, c = tag.split('-')
src = {'1': 'eun01_1.txt', '2': 'eun02.txt', '3': 'eun03.txt', '4': 'eun04.txt'}[v]
lst = json.load(open(os.path.join(T, '결과', f'{tag}_{n}_목록.json'), encoding='utf-8'))
lo, hi = map(int, lst['행'].split('~'))
work = open(os.path.join(D, '지금 하는 일.md'), encoding='utf-8').read().split('\n')
bg = [l for l in work if l.startswith('  - 바로 고침:')]
nm = [l for l in work if l.startswith('  - 고치지 않고 최종점검 남은 것.md에 적음:')]
assert len(bg) == 1 and len(nm) == 1

# 자료 1: 기준 전체
gijun = open(os.path.join(D, '원작 정리본 기준.md'), encoding='utf-8').read()
# 자료 2: 원문 장면(행 번호 붙임)
SRC = open(os.path.join(T, '..', '원문', src), encoding='utf-8').read().split('\n')
scene = '\n'.join(f'{i}\t{SRC[i - 1]}' for i in range(lo, hi + 1))
# 자료 3: 목록
mok = '\n'.join(f'{r["줄"]}\t{r["원래 줄"]}' for r in lst['목록'])
# 자료 4: 이 장을 근거로 쓴 다른 정리본 줄(목록에 든 줄은 뺌)
files = sorted([f for f in glob.glob(D + '/*.md') if re.match(r'\d+_', os.path.basename(f))],
               key=lambda f: int(os.path.basename(f).split('_')[0]))
cit = re.compile(r'(?<![\d-])(\d)-(\d{1,2})\(')
inlist = {r['줄'] for r in lst['목록']}
ch = []
for f in files:
    for i, l in enumerate(open(f, encoding='utf-8'), 1):
        key = f'{os.path.basename(f)}:{i}'
        if l.startswith('| ') and key not in inlist and any(f'{a}-{b}' == tag for a, b in cit.findall(l)):
            ch.append(f'{key}\t{l.rstrip()}')
# 자료 5: 대조표에서 이 장면 원문에 나오는 이름의 줄
pyo_path = os.path.join(D, '표기와 원문 문제.md')
plain = re.sub(r'\s+', '', ''.join(SRC[lo - 1:hi]))
pyo, sec = [], ''
for i, l in enumerate(open(pyo_path, encoding='utf-8'), 1):
    if l.startswith('### '):
        sec = l.strip()
        if sec == '### 원문 문제': break
        continue
    if not l.startswith('| ') or l.startswith('| 번역본 표기') or l.startswith('|---'):
        continue
    cells = [x.strip() for x in l.split('|')[1:-1]]
    names = set()
    for cell in cells[:2]:
        names.add(re.sub(r'\s+', '', cell))
        names.update(w for w in re.split(r'[\s·.]+', cell) if len(w) >= 2)
    if any(nm_ and nm_ in plain for nm_ in names):
        pyo.append(f'표기와 원문 문제.md:{i}\t{sec[4:]}\t{l.rstrip()}')

jaryo = (f'## 자료 1: 원작 정리본 기준.md 전체\n{gijun}\n\n'
         f'## 자료 2: 원문 {src} {lo}~{hi}행 (행 번호\\t원문)\n{scene}\n\n'
         f'## 자료 3: 목록 ({lst["줄 수"]}줄. 파일:줄\\t원래 줄)\n{mok}\n\n'
         f'## 자료 4: 이 장({tag})을 근거로 쓴 다른 정리본 줄 ({len(ch)}줄)\n' + '\n'.join(ch) + '\n\n'
         f'## 자료 5: 표기 대조표 가운데 이 장면 원문에 나오는 이름의 줄 ({len(pyo)}줄)\n' + '\n'.join(pyo))
t = open(os.path.join(T, '지시문.md'), encoding='utf-8').read()
rep = {'장_이름': f'{v}권 {"서" if c == "0" else c}장', '장_표기': tag, '장면': str(n),
       '원문파일': f'/home/user/-/원작/원문/{src}', '행_시작': str(lo), '행_끝': str(hi),
       '목록파일': os.path.join(T, '결과', f'{tag}_{n}_목록.json'), '줄수': str(lst['줄 수']),
       '결과파일': os.path.join(T, '결과', f'{tag}_{n}_판정.json'),
       '바로고침': bg[0].strip(), '남은것': nm[0].strip()}
for k, val in rep.items():
    t = t.replace('{' + k + '}', val)
assert re.findall(r'\{[가-힣_]+\}', t) == ['{자료}'], re.findall(r'\{[가-힣_]+\}', t)
t = t.replace('{자료}', jaryo)
print(t)
