# 정리본 표에 줄을 넣음. 넣기 전에 기준의 해당 부분을 보여 주고, check.py 검사에 오류가 있으면 넣지 않음.
# 쓰는 법: python3 add.py 파일 [구역제목] < 줄들
#   구역제목 예: "### 사실", "### 바탕"(1_인물), "## 전투"(10_결). 다른 갈래는 적지 않아도 됨.
#   줄은 근거의 권(예: 1-2(1330)이면 1권)의 "## N권" 구역에 넣음. 10_결은 권으로 나누지 않고 종류 구역에 넣음.
#   넣을 구역이나 표 머리가 파일에 없으면 먼저 만듦(빈 파일에서도 됨).
import sys, os, re, subprocess
TOOL = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(TOOL)
GIJUN = os.path.join(ROOT, '원작 정리본 기준.md')

HEAD = {'사실': '| 인물 | 항목 | 시점 | 내용 | 근거 |',
        '바탕': '| 인물 | 항목 | 시점 | 장면 | 근거 |',
        None: '| 대상 | 항목 | 시점 | 내용 | 근거 |'}
SEP = '|---|---|---|---|---|'
KINDS10 = ['전투', '군의 운용', '사람과 조직', '나라와 세력']

def gijun_part(g):
    L = open(GIJUN, encoding='utf-8').read().split('\n')
    a = next(i for i, l in enumerate(L) if l.startswith('## 공통 기준'))
    b = next(i for i, l in enumerate(L) if l.startswith('## 갈래'))
    s = next(i for i, l in enumerate(L) if re.match(rf'{g}\. ', l))
    e = next((i for i in range(s + 1, len(L)) if re.match(r'\d+\. ', L[i]) or L[i].startswith('## ') or L[i].startswith('### ')), len(L))
    return '\n'.join(L[a:b]) + '\n' + '\n'.join(L[s:e])

def fail(msg):
    print('[오류] ' + msg); print('넣지 않았음.'); sys.exit(1)

def section_end(L, i, stops):
    """i 다음 줄부터, stops 가운데 하나로 시작하는 줄 앞까지"""
    return next((k for k in range(i + 1, len(L)) if L[k].startswith(stops)), len(L))

def put(L, at, block):
    """at 자리에 block을 넣음. 앞뒤가 붙지 않게 빈 줄을 둠."""
    if at > 0 and L[at - 1].strip(): block = [''] + block
    L[at:at] = block
    return at + (1 if block[0] == '' else 0)

def table_after(L, i, end, head):
    """i(제목 줄) 아래 end 앞까지에서 표 머리 구분선 위치. 없으면 제목 바로 아래에 표 머리를 만듦."""
    h = next((k for k in range(i + 1, end) if L[k].startswith('|---')), None)
    if h is None:
        L[i + 1:i + 1] = ['', head, SEP]
        h = i + 3
    return h

path = os.path.abspath(sys.argv[1]); sec = sys.argv[2] if len(sys.argv) > 2 else None
g = os.path.basename(path).split('_')[0]
rows = [l.rstrip('\n') for l in sys.stdin if l.strip()]
print('===== 기준(공통 기준과 이 갈래) =====')
print(gijun_part(g))
print('===== 검사 =====')
table = sec[4:].strip() if sec in ('### 사실', '### 바탕') else None
if g == '1' and table is None:
    print('[오류] 인물 파일은 "### 사실" 또는 "### 바탕"을 꼭 적음'); sys.exit(1)
if g == '10' and not (sec and sec.startswith('## ') and sec[3:].strip() in KINDS10):
    print('[오류] 10_결은 종류 구역을 꼭 적음: ' + ', '.join('"## ' + k + '"' for k in KINDS10)); sys.exit(1)
# 검수를 통과하지 않은 앞 장이 있으면 다른 장의 줄은 받지 않음(한 장씩 끝내고 넘어감)
sys.path.insert(0, TOOL); import check
chs = {f"{m.group(1)}-{m.group(2)}" for m in (re.match(r'\| .* \| (\d+)-(\d+)\(', l) for l in rows) if m}
left = check.unpassed_chapters() - chs
if left:
    print(f'[오류] 검수를 통과하지 않은 장이 있음: {", ".join(sorted(left))}. 그 장의 검수(도구/검수_지시.md)를 통과한 뒤 다음 장으로 넘어감')
    print('넣지 않았음.'); sys.exit(1)
r = subprocess.run([sys.executable, os.path.join(TOOL, 'check.py'), 'rows', path] + ([table] if table else []),
                   input='\n'.join(rows), capture_output=True, text=True)
print(r.stdout, end='')
if r.stderr: print('[검사 도구 오류]', r.stderr)
if r.returncode != 0:
    print('넣지 않았음. 오류를 기준대로 고친 뒤 다시 넣음.'); sys.exit(1)

txt = open(path, encoding='utf-8').read() if os.path.exists(path) else ''
L = txt.split('\n') if txt.strip() else []
while L and not L[-1].strip(): L.pop()

if g == '10':
    # 종류 구역: 없으면 종류의 차례에 맞는 자리에 만듦
    name = sec[3:].strip()
    i = next((k for k, l in enumerate(L) if l.strip() == sec), None)
    if i is None:
        later = KINDS10[KINDS10.index(name) + 1:]
        at = next((k for k, l in enumerate(L) if l.startswith('## ') and l[3:].strip() in later), len(L))
        i = put(L, at, [sec, '', HEAD[None], SEP] + ([''] if at < len(L) else []))
    end = section_end(L, i, ('## ',))
    h = table_after(L, i, end, HEAD[None])
else:
    # 권 구역: 근거의 권으로 정함. 없으면 권 차례에 맞는 자리에 만듦
    gwons = {m.group(1) for m in (re.match(r'\| .* \| (\d+)-\d+\(', l) for l in rows) if m}
    if len(gwons) != 1:
        fail('넣을 줄의 근거에서 권을 하나로 정할 수 없음: ' + (', '.join(sorted(gwons)) or '없음') + '. 한 번에 한 권의 줄만 넣음')
    n = int(gwons.pop()); title = f'## {n}권'
    i = next((k for k, l in enumerate(L) if l.strip() == title), None)
    if i is None:
        at = next((k for k, l in enumerate(L) if re.match(r'## (\d+)권\s*$', l) and int(re.match(r'## (\d+)권', l).group(1)) > n), len(L))
        if g == '1':
            block = [title, '', '### 사실', '', HEAD['사실'], SEP, '', '### 바탕', '', HEAD['바탕'], SEP]
        else:
            block = [title, '', HEAD[None], SEP]
        i = put(L, at, block + ([''] if at < len(L) else []))
    end = section_end(L, i, ('## ',))
    if g == '1':
        j = next((k for k in range(i + 1, end) if L[k].strip() == sec), None)
        if j is None:
            # 사실 표가 바탕 표보다 앞에 옴
            at = end
            if table == '사실':
                at = next((k for k in range(i + 1, end) if L[k].strip() == '### 바탕'), end)
            j = put(L, at, [sec, '', HEAD[table], SEP] + ([''] if at < len(L) else []))
            end = section_end(L, i, ('## ',))
        sub_end = section_end(L, j, ('## ', '### '))
        h = table_after(L, j, sub_end, HEAD[table])
    else:
        h = table_after(L, i, end, HEAD[None])

e = h + 1
while e < len(L) and L[e].startswith('|'): e += 1
L[e:e] = rows
open(path, 'w', encoding='utf-8').write('\n'.join(L) + '\n')
print(f'{len(rows)}줄 넣음.')
