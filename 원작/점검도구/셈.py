#!/usr/bin/env python3
# 사용: python3 셈.py 1-0 시작        → 그 장을 시작한 시각을 결과/1-0_시작.txt에 적음(이미 있으면 바꾸지 않음).
#       python3 셈.py 1-0 "1권 서장"  → 장 끝 보고 한 줄을 찍음. 숫자는 결과/1-0_○_기록.json을 모두 더한 것,
#                                      걸린 시간은 시작 시각부터 지금까지, 괄호 안은 지금의 마지막 커밋.
#                                      장면.json의 장면 가운데 기록 파일이 없는 것이 있으면 그 장면을 알림.
#       근거 덧붙임은 근거를 덧붙인 줄의 수(같은 줄에 사실 여럿을 덧붙여도 하나).
import sys, os, json, time, subprocess
T = os.path.dirname(os.path.abspath(__file__))
tag, name = sys.argv[1], sys.argv[2]
R = os.path.join(T, '결과'); S = os.path.join(R, f'{tag}_시작.txt')
if name == '시작':
    os.makedirs(R, exist_ok=True)
    if os.path.exists(S): print('이미 적힌 시작 시각:', open(S).read().strip())
    else:
        open(S, 'w').write(time.strftime('%Y-%m-%d %H:%M:%S %z') + '\n'); print('시작 시각:', open(S).read().strip())
    sys.exit(0)
scenes = json.load(open(os.path.join(T, '장면.json'), encoding='utf-8'))[tag]
t = dict(고침=0, 넣음=0, 새=0, 단락=0, 사실=0, 줄=0, 없음=0); add = set(); miss = []
for k in range(1, len(scenes) + 1):
    f = os.path.join(R, f'{tag}_{k}_기록.json')
    if not os.path.exists(f): miss.append(k); continue
    d = json.load(open(f, encoding='utf-8'))
    t['단락'] += len(d.get('단락', [])); t['사실'] += sum(len(p.get('사실') or []) for p in d.get('단락', []))
    t['줄'] += len(d.get('줄', [])); t['고침'] += sum(e.get('처리') == '고침' for e in d.get('줄', []))
    t['넣음'] += len(d.get('넣음', [])); t['새'] += len(d.get('남은 것', []))
    for e in d.get('남는 사실', []):
        if e.get('처리') == '근거 덧붙임': add.add(e.get('줄'))
        if e.get('처리') == '적을 것 없음': t['없음'] += 1
if miss: print(f'기록 파일이 없는 장면: {miss} (장면 {len(scenes)} 가운데)')
if os.path.exists(S):
    mins = int(time.time() - time.mktime(time.strptime(open(S).read().strip()[:19], '%Y-%m-%d %H:%M:%S'))) // 60
    took = f'{mins // 60}시간 {mins % 60}분' if mins >= 60 else f'{mins}분'
else: took = '시작 시각 없음'
h = subprocess.run(['git', 'log', '-1', '--format=%h'], cwd=T, capture_output=True, text=True).stdout.strip()
print(f'{name} 마침({h}): 걸린 시간 {took}, 고친 줄 {t["고침"]}, 넣은 줄 {t["넣음"]}, 근거 덧붙임 {len(add)}, 남은 것 {t["새"]}, 단락 수 {t["단락"]}, 사실 수 {t["사실"]}, 정리본 줄 수 {t["줄"]}, 적을 것 없음 수 {t["없음"]}')
