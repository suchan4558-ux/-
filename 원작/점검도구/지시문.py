#!/usr/bin/env python3
# 사용: python3 지시문.py 1-3 2  → 그 장면을 맡길 에이전트 지시문을 출력
import sys, os, json, re
T = os.path.dirname(os.path.abspath(__file__))
tag, n = sys.argv[1], int(sys.argv[2])
v, c = tag.split('-')
src = {'1': 'eun01_1.txt', '2': 'eun02.txt', '3': 'eun03.txt', '4': 'eun04.txt'}[v]
lst = json.load(open(os.path.join(T, '결과', f'{tag}_{n}_목록.json'), encoding='utf-8'))
lo, hi = lst['행'].split('~')
work = open(os.path.join(T, '..', '정리본', '지금 하는 일.md'), encoding='utf-8').read().split('\n')
bg = [l for l in work if l.startswith('  - 바로 고침:')]
nm = [l for l in work if l.startswith('  - 고치지 않고 최종점검 남은 것.md에 적음:')]
assert len(bg) == 1 and len(nm) == 1
t = open(os.path.join(T, '지시문.md'), encoding='utf-8').read()
rep = {'장_이름': f'{v}권 {"서" if c == "0" else c}장', '장_표기': tag, '장면': str(n),
       '원문파일': f'/home/user/-/원작/원문/{src}', '행_시작': lo, '행_끝': hi,
       '목록파일': os.path.join(T, '결과', f'{tag}_{n}_목록.json'), '줄수': str(lst['줄 수']),
       '결과파일': os.path.join(T, '결과', f'{tag}_{n}_판정.json'),
       '바로고침': bg[0].strip(), '남은것': nm[0].strip()}
for k, val in rep.items():
    t = t.replace('{' + k + '}', val)
assert not re.search(r'\{[가-힣_]+\}', t), re.findall(r'\{[가-힣_]+\}', t)
print(t)
