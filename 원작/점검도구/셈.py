#!/usr/bin/env python3
# 사용: python3 셈.py 1-0 "1권 서장" → 장 끝 보고 한 줄을 찍음(숫자는 결과/○-○_○_기록.json에서, 걸린 시간은 그 장 결과 파일의 첫 커밋과 마지막 커밋 사이).
import sys, os, json, glob, subprocess
T = os.path.dirname(os.path.abspath(__file__))
tag, name = sys.argv[1], sys.argv[2]
R = os.path.join(T, '결과')
fs = sorted(glob.glob(os.path.join(R, f'{tag}_*_기록.json')))
t = dict(고침=0, 넣음=0, 새=0, 단락=0, 사실=0, 줄=0, 없음=0); add = set()
for f in fs:
    d = json.load(open(f, encoding='utf-8'))
    t['단락'] += len(d['단락']); t['사실'] += sum(len(p.get('사실', [])) for p in d['단락'])
    t['줄'] += len(d.get('줄', [])); t['고침'] += sum(e['처리'] == '고침' for e in d.get('줄', []))
    t['넣음'] += len(d.get('넣음', [])); t['새'] += len(d.get('남은 것', []))
    for e in d.get('남는 사실', []):
        if e['처리'] == '근거 덧붙임': add.add(e['줄'])
        if e['처리'] == '적을 것 없음': t['없음'] += 1
ts = sorted(int(x) for x in subprocess.run(['git', 'log', '--format=%ct', '--', f'결과/{tag}_*'], cwd=T, capture_output=True, text=True).stdout.split())
mins = (ts[-1] - ts[0]) // 60 if ts else 0
h = subprocess.run(['git', 'log', '-1', '--format=%h'], cwd=T, capture_output=True, text=True).stdout.strip()
print(f'{name} 마침({h}): 걸린 시간 {mins}분, 고친 줄 {t["고침"]}, 넣은 줄 {t["넣음"]}, 근거 덧붙임 {len(add)}, 남은 것 {t["새"]}, 단락 {t["단락"]}, 사실 {t["사실"]}, 정리본 줄 {t["줄"]}, 적을 것 없음 {t["없음"]}')
