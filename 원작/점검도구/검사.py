#!/usr/bin/env python3
# 사용: python3 검사.py 1-3 2  → 결과/1-3_2_판정.json(기록 파일)을 검사.
#       통과면 "통과"와 셈을, 아니면 걸린 것을 모두 적고 끝 코드 1.
#       다른 파일을 검사하려면 셋째 인자로 기록 파일 경로를 줌.
#
# 기록 파일 꼴
# {
#  "판정": [                                  ← 목록의 줄마다 하나
#   {"줄": "1_인물.md:123", "판정": "맞음" | "고침" | "남은 것",
#    "인용": [{"행": "1234-1235", "구절": "원문 그대로"}],
#    "고친 줄": "| ... |",          ← 고침일 때
#    "까닭": "...",                 ← 고침일 때
#    "기준": ["기준 문장 그대로"],     ← 고침, 남은 것일 때
#    "남은 것": 59,                 ← 남은 것일 때. 아래 "남은 것"의 번호
#    "숫자 까닭": "..."}            ← 줄의 숫자가 인용에 없을 때
#  ],
#  "근거 덧붙임": [                            ← 같은 항목·같은 내용인 줄에 이 장 근거만 더할 때
#   {"줄": "1_인물.md:456", "고친 줄": "| ... |", "인용": [...], "기준": [...]}
#  ],
#  "단락": [                                  ← 목록의 단락마다 하나
#   {"단락": 3, "처리": "담김", "줄": ["1_인물.md:123"]}
#   {"단락": 4, "처리": "적을 것 없음", "까닭": "..."}
#   {"단락": 5, "처리": "빠짐", "남은 것": 60}
#  ],
#  "남은 것": [                               ← 이 장면에서 새로 생긴 남은 것
#   {"번호": 59, "종류": "빠진 내용", "무엇": "...", "문구 안": "...", "자리": "...", "까닭": "...",
#    "인용": [...], "기준": [...]}
#  ]
# }
import sys, os, json, re
T = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(T, '..', '정리본')
tag, n = sys.argv[1], int(sys.argv[2])
src = {'1': 'eun01_1.txt', '2': 'eun02.txt', '3': 'eun03.txt', '4': 'eun04.txt'}[tag.split('-')[0]]
SRC = open(os.path.join(T, '..', '원문', src), encoding='utf-8').read().split('\n')
lst = json.load(open(os.path.join(T, '결과', f'{tag}_{n}_목록.json'), encoding='utf-8'))
lo, hi = map(int, lst['행'].split('~'))
rp = sys.argv[3] if len(sys.argv) > 3 else os.path.join(T, '결과', f'{tag}_{n}_판정.json')
try:
    res = json.load(open(rp, encoding='utf-8'))
except Exception as e:
    print('기록 파일을 읽을 수 없음:', e); sys.exit(1)
bad = []
ws = re.compile(r'\s+')
def norm(s): return ws.sub('', s or '')

# 기준 문장, 남은 것의 종류, 이미 있는 남은 것 번호
CRIT = norm(open(os.path.join(D, '원작 정리본 기준.md'), encoding='utf-8').read())
NOW = open(os.path.join(D, '지금 하는 일.md'), encoding='utf-8').read()
m = re.search(r'고치지 않고 최종점검 남은 것\.md에 적음: (.*?)\.\n', NOW)
KINDS = [k.strip() for k in m.group(1).split(',')] if m else []
if not KINDS: bad.append('지금 하는 일.md에서 남은 것의 종류를 찾지 못함')
LEFT = open(os.path.join(D, '최종점검 남은 것.md'), encoding='utf-8').read()
used = [int(x) for x in re.findall(r'^\|?\s*-?\s*(\d+)[.|)]', LEFT, re.M)]
last = max(used) if used else 0

# 대조표: 기준 표기와 다른 번역본 표기
PYO = []
ALLSTD = set()
TITLE = r'(공작|후작|백작|자작|남작|제독|원수|대장|중장|소장|준장|대령|중령|소령|대위|중위|소위|부인|황제|황후|경)(?=\s|$)|^(공작|후작|백작|자작|남작|제독)\s'
sec = None
for l in open(os.path.join(D, '표기와 원문 문제.md'), encoding='utf-8'):
    if l.startswith('### '): sec = l[4:].strip(); continue
    if sec in ('인물', '지명', '그 밖의 이름') and l.startswith('| ') and not l.startswith('| 번역본') and not l.startswith('|---'):
        c = [x.strip() for x in l.rstrip().split('|')[1:-1]]
        if len(c) >= 2 and c[1]: ALLSTD.add(c[1])
        if len(c) >= 2 and c[0]:
            t = re.sub(r'\(.*?\)', '', c[0]).strip()   # 괄호 안은 같은 표기 가운데 누구인지 가르는 말
            core = re.sub(TITLE, '', t)   # 앞뒤에 붙은 작위·직함만 다른 것은 같은 표기
            if len(t) >= 2 and norm(core) not in norm(c[1]): PYO.append((t, c[1]))   # 기준 표기의 줄임은 문장 안에서 써도 됨
STD = sorted(ALLSTD, key=len, reverse=True)   # 다른 사람의 기준 표기와 같은 번역본 표기는 가릴 수 없어 지움

def chk_quotes(where, qs):
    if not isinstance(qs, list) or not qs:
        bad.append(f'{where}: 인용 없음'); return []
    out = []
    for q in qs:
        if not isinstance(q, dict): bad.append(f'{where}: 인용 꼴 틀림'); continue
        r, g = str(q.get('행', '')), q.get('구절', '')
        mm = re.fullmatch(r'(\d+)(?:-(\d+))?', r)
        if not mm: bad.append(f'{where}: 행 꼴 틀림 "{r}"'); continue
        a = int(mm.group(1)); b = int(mm.group(2) or a)
        if a > b or a < lo or b > hi: bad.append(f'{where}: 행 {r}이 장면 범위 {lo}~{hi} 밖'); continue
        if len(norm(g)) < 4: bad.append(f'{where}: 구절이 너무 짧음 "{g}"'); continue
        if norm(g) not in norm(''.join(SRC[a - 1:b])):
            bad.append(f'{where}: 인용 "{g[:40]}"이 원문 {r}행에 없음'); continue
        out.append((a, b, g))
    return out

def chk_crit(where, cs):
    if not isinstance(cs, list) or not cs:
        bad.append(f'{where}: 기준 인용 없음'); return
    for c in cs:
        if len(norm(c)) < 8: bad.append(f'{where}: 기준 인용이 너무 짧음 "{c}"'); continue
        if norm(c) not in CRIT: bad.append(f'{where}: 기준 인용 "{str(c)[:40]}"이 기준 파일에 없음')

ref_item = r'\d+-\d+\((?:\d+(?:-\d+)?)(?:, \d+(?:-\d+)?)*\)'
ref_re = re.compile(r'^' + ref_item + r'(?:(?:, | / )' + ref_item + r')*$')
def cells(row): return [c.strip() for c in row.rstrip().split('|')[1:-1]]
def chk_row(where, row, fname):
    if not isinstance(row, str) or not row.startswith('| ') or not row.rstrip().endswith('|'):
        bad.append(f'{where}: 고친 줄 꼴 틀림'); return False
    c = cells(row)
    need = 4 if fname == '표기와 원문 문제.md' else 5
    if len(c) != need: bad.append(f'{where}: 고친 줄 칸 수 {len(c)} (필요 {need})'); return False
    refc = c[2] if fname == '표기와 원문 문제.md' and c[0].isdigit() else c[-1]
    if not ref_re.match(refc): bad.append(f'{where}: 고친 줄 근거 꼴 틀림 "{refc[:50]}"'); return False
    return True

QUOTED = re.compile(r"'[^']*'|\"[^\"]*\"|“[^”]*”|‘[^’]*’|<[^>]*>|「[^」]*」|『[^』]*』")
def chk_pyo(where, row, fname):
    if fname == '표기와 원문 문제.md' or not row: return
    t = QUOTED.sub(' ', ' '.join(cells(row)[:-1]))
    for s in STD: t = t.replace(s, ' ')
    for a, b in PYO:
        if re.search(r'(?<![가-힣])' + re.escape(a), t): bad.append(f'{where}: 대조표의 번역본 표기 "{a}"가 쓰임(기준 표기 "{b}")')

NUM = re.compile(r'\d[\d,]*')
def chk_num(where, row, fname, quotes, why):
    if fname == '표기와 원문 문제.md' or not row: return
    c = cells(row)
    if len(c) < 5: return
    nums = {x.replace(',', '') for x in NUM.findall(c[2] + ' ' + c[3])}
    qtxt = norm(''.join(g for _, _, g in quotes)).replace(',', '')
    miss = sorted(x for x in nums if x not in qtxt)
    if miss and not why: bad.append(f'{where}: 줄의 숫자 {", ".join(miss)}가 인용에 없음(숫자 까닭 없음)')

cit = re.compile(r'(?<![\d-])(\d)-(\d{1,2})\(([^)]*)\)')
def spans(row):
    out = []
    for mm in cit.finditer(row or ''):
        if f'{mm.group(1)}-{mm.group(2)}' != tag: continue
        for part in mm.group(3).split(','):
            nums = re.findall(r'\d+', part)
            if nums: out.append((int(nums[0]), int(nums[-1])))
    return out

# 남은 것
left = {}
for j, p in enumerate(res.get('남은 것', []), 1):
    w = f'남은 것 {p.get("번호", f"(번호 없음 {j})")}'
    k = p.get('번호')
    if not isinstance(k, int): bad.append(f'{w}: 번호 없음'); continue
    if k in left: bad.append(f'{w}: 번호 겹침')
    left[k] = p
    if p.get('종류') not in KINDS: bad.append(f'{w}: 종류 "{p.get("종류")}"가 {KINDS} 가운데 하나가 아님')
    for f in ('무엇', '문구 안', '자리', '까닭'):
        if not p.get(f): bad.append(f'{w}: {f} 없음')
    chk_quotes(w, p.get('인용'))
    chk_crit(w, p.get('기준'))
if left:
    ks = sorted(left)
    if ks[0] <= last: bad.append(f'남은 것 번호 {ks[0]}이 이미 쓴 번호({last}까지)와 겹침')
    if ks != list(range(ks[0], ks[0] + len(ks))): bad.append(f'남은 것 번호가 이어지지 않음: {ks}')
ref_left = set()

# 판정
want = [r['줄'] for r in lst['목록']]
orig = {r['줄']: r['원래 줄'] for r in lst['목록']}
got = [p.get('줄') for p in res.get('판정', [])]
miss = [x for x in want if x not in got]
extra = [x for x in got if x not in want]
dup = sorted({x for x in got if got.count(x) > 1})
if miss: bad.append(f'판정 빠진 줄 {len(miss)}: ' + ', '.join(miss[:30]))
if extra: bad.append(f'목록에 없는 줄 {len(extra)}: ' + ', '.join(extra[:30]))
if dup: bad.append('겹친 줄: ' + ', '.join(dup[:30]))
for p in res.get('판정', []):
    w = p.get('줄'); k = p.get('판정'); fn = str(w).split(':')[0]
    if k not in ('맞음', '고침', '남은 것'): bad.append(f'{w}: 판정 값 "{k}"'); continue
    qs = chk_quotes(w, p.get('인용'))
    sp = [(a, b) for a, b in spans(orig.get(w)) + spans(p.get('고친 줄')) if a <= hi and b >= lo]
    if sp and qs and not any(any(qa <= b + 2 and qb >= a - 2 for a, b in sp) for qa, qb, _ in qs):
        bad.append(f'{w}: 인용 행이 그 줄의 이 장면 근거 행({", ".join(f"{a}-{b}" for a, b in sp)})과 겹치지 않음')
    row = p.get('고친 줄') if k == '고침' else orig.get(w)
    if k == '고침':
        if not p.get('까닭'): bad.append(f'{w}: 까닭 없음')
        if chk_row(w, p.get('고친 줄'), fn) and p.get('고친 줄', '').strip() == orig.get(w, '').strip():
            bad.append(f'{w}: 고친 줄이 원래 줄과 같음')
    if k in ('고침', '남은 것'): chk_crit(w, p.get('기준'))
    if k == '남은 것':
        r = p.get('남은 것')
        if r not in left: bad.append(f'{w}: 남은 것 번호 {r}가 기록의 "남은 것"에 없음')
        ref_left.add(r)
    if k != '남은 것':
        chk_pyo(w, row, fn)
        chk_num(w, row, fn, qs, p.get('숫자 까닭'))

# 근거 덧붙임
added = set()
for j, p in enumerate(res.get('근거 덧붙임', []), 1):
    w = f'근거 덧붙임 {j}'
    f = str(p.get('줄', '')).split(':')
    if len(f) != 2 or not f[1].isdigit(): bad.append(f'{w}: 줄 꼴 틀림'); continue
    path = os.path.join(D, f[0])
    if not os.path.exists(path): bad.append(f'{w}: 파일 없음 {f[0]}'); continue
    if p['줄'] in want: bad.append(f'{w}: 목록에 있는 줄임(판정에서 고침으로 적을 것)')
    cur = open(path, encoding='utf-8').read().split('\n')[int(f[1]) - 1]
    new = p.get('고친 줄', '')
    chk_quotes(w, p.get('인용'))
    chk_crit(w, p.get('기준'))
    if chk_row(w, new, f[0]):
        if tag + '(' not in new: bad.append(f'{w}: 고친 줄에 {tag} 근거가 없음')
        if cells(cur)[:-1] != cells(new)[:-1]: bad.append(f'{w}: 근거 칸 말고 다른 칸이 바뀜')
    added.add(p['줄'])

# 단락
paras = {q['단락']: q for q in lst['단락']}
seen = {}
for p in res.get('단락', []):
    k = p.get('단락'); w = f'단락 {k}'
    if k not in paras: bad.append(f'{w}: 목록에 없는 단락'); continue
    if k in seen: bad.append(f'{w}: 겹침'); continue
    seen[k] = p
    c = p.get('처리')
    if c == '담김':
        ls = p.get('줄')
        if not isinstance(ls, list) or not ls: bad.append(f'{w}: 담긴 줄 없음'); continue
        for x in ls:
            if x not in want and x not in added: bad.append(f'{w}: 줄 {x}가 목록에도 근거 덧붙임에도 없음')
    elif c == '적을 것 없음':
        if not p.get('까닭'): bad.append(f'{w}: 까닭 없음')
    elif c == '빠짐':
        r = p.get('남은 것')
        if r not in left: bad.append(f'{w}: 남은 것 번호 {r}가 기록의 "남은 것"에 없음')
        ref_left.add(r)
    else:
        bad.append(f'{w}: 처리 값 "{c}"')
nop = [k for k in paras if k not in seen]
if nop: bad.append(f'빈 단락 {len(nop)}: ' + ', '.join(map(str, nop)))
lonely = sorted(set(left) - ref_left)
if lonely: bad.append(f'판정이나 단락에서 가리키지 않은 남은 것: {lonely}')

if bad:
    print(f'{tag} 장면 {n}: 걸림 {len(bad)}'); print('\n'.join(bad)); sys.exit(1)
cnt = lambda xs, key, v: sum(1 for x in xs if x.get(key) == v)
J, P = res['판정'], res['단락']
print(f'{tag} 장면 {n}: 통과. 판정 {len(J)}줄(맞음 {cnt(J,"판정","맞음")}, 고침 {cnt(J,"판정","고침")}, 남은 것 {cnt(J,"판정","남은 것")}), '
      f'근거 덧붙임 {len(res.get("근거 덧붙임", []))}, 단락 {len(P)}(담김 {cnt(P,"처리","담김")}, 적을 것 없음 {cnt(P,"처리","적을 것 없음")}, 빠짐 {cnt(P,"처리","빠짐")}), '
      f'새 남은 것 {len(left)}')
