# 정리본 표에 줄을 넣음. 넣기 전에 기준의 해당 부분을 보여 주고, check.py 검사에 오류가 있으면 넣지 않음.
# 쓰는 법: python3 add.py 파일 [구역제목] < 줄들
#   구역제목 예: "### 사실", "### 바탕", "## 전투". 없으면 마지막 "## " 구역(가장 뒤 권)의 첫 표.
#   그 제목이 여러 번 나오면 가장 뒤(최신 권)의 것에 넣음.
import sys, os, re, subprocess
TOOL = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(TOOL)
GIJUN = os.path.join(ROOT, '원작 정리본 기준.md')

def gijun_part(g):
    L = open(GIJUN, encoding='utf-8').read().split('\n')
    a = next(i for i, l in enumerate(L) if l.startswith('## 공통 기준'))
    b = next(i for i, l in enumerate(L) if l.startswith('## 갈래'))
    s = next(i for i, l in enumerate(L) if re.match(rf'{g}\. ', l))
    e = next((i for i in range(s + 1, len(L)) if re.match(r'\d+\. ', L[i]) or L[i].startswith('## ') or L[i].startswith('### ')), len(L))
    return '\n'.join(L[a:b]) + '\n' + '\n'.join(L[s:e])

path = os.path.abspath(sys.argv[1]); sec = sys.argv[2] if len(sys.argv) > 2 else None
g = os.path.basename(path).split('_')[0]
rows = [l.rstrip('\n') for l in sys.stdin if l.strip()]
print('===== 기준(공통 기준과 이 갈래) =====')
print(gijun_part(g))
print('===== 검사 =====')
table = sec[4:].strip() if sec in ('### 사실', '### 바탕') else None
if g == '1' and table is None:
    print('[오류] 인물 파일은 "### 사실" 또는 "### 바탕"을 꼭 적음'); sys.exit(1)
r = subprocess.run([sys.executable, os.path.join(TOOL, 'check.py'), 'rows', path] + ([table] if table else []),
                   input='\n'.join(rows), capture_output=True, text=True)
print(r.stdout, end='')
if r.stderr: print('[검사 도구 오류]', r.stderr)
if r.returncode != 0:
    print('넣지 않았음. 오류를 기준대로 고친 뒤 다시 넣음.'); sys.exit(1)
L = open(path, encoding='utf-8').read().split('\n')
i = max(k for k, l in enumerate(L) if (l.strip() == sec if sec else l.startswith('## ')))
h = next(k for k in range(i, len(L)) if L[k].startswith('|---'))
e = h + 1
while e < len(L) and L[e].startswith('|'): e += 1
L[e:e] = rows
open(path, 'w', encoding='utf-8').write('\n'.join(L))
print(f'{len(rows)}줄 넣음.')
