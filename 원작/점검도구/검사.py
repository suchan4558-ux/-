#!/usr/bin/env python3
# 사용: python3 검사.py 1-3 2  → 결과/1-3_2_기록.json을 검사.
#       통과면 "통과"와 셈을, 아니면 걸린 것을 모두 적고 끝 코드 1.
#       다른 파일을 검사하려면 셋째 인자로 기록 파일 경로를 줌.
#       결과/1-3_2_줄.json이 아직 없으면(사실 뽑기 단계) 단락과 사실만 검사함.
#
# 기록 파일 꼴
# {
#  "단락": [                                  ← 단락 목록의 단락마다 하나
#   {"단락": 1, "사실": [{"번호": 1, "행": "105-106", "구절": "원문 그대로(60자 안)", "내용": "사실 하나"}]},
#   {"단락": 2, "없음": "적을 사실이 없는 까닭"}
#  ],
#  "줄": [                                    ← 정리본 줄 목록의 줄마다 하나
#   {"줄": "1_인물.md:123", "처리": "이음", "사실": [1, 2]},
#   {"줄": "...", "처리": "고침", "사실": [3], "고친 줄": "| ... |", "까닭": "...", "기준": ["기준 문장 그대로"]},
#   {"줄": "...", "처리": "남은 것", "남은 것": 59, "기준": ["..."]}
#   (이음과 고침에는 필요하면 "숫자 까닭", "이름 까닭")
#  ],
#  "남는 사실": [                              ← 어느 줄에도 이어지지 않은 사실마다 하나
#   {"사실": 4, "처리": "근거 덧붙임", "줄": "1_인물.md:456", "고친 줄": "| ... |"},
#   {"사실": 5, "처리": "남은 것", "남은 것": 60},
#   {"사실": 6, "처리": "적을 것 없음", "기준": ["..."], "까닭": "..."}
#  ],
#  "남은 것": [                               ← 이 장면에서 새로 생긴 남은 것
#   {"번호": 59, "종류": "빠진 내용", "무엇": "...", "문구 안": "...", "자리": "...", "까닭": "...",
#    "사실": [5], "기준": ["..."]}
#  ]
# }
import sys, os, json, re
T = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(T, '..', '정리본')
tag, n = sys.argv[1], int(sys.argv[2])
scenes = json.load(open(os.path.join(T, '장면.json'), encoding='utf-8'))
lo, hi = map(int, scenes[tag][n - 1].split('~'))
src = {'1': 'eun01_1.txt', '2': 'eun02.txt', '3': 'eun03.txt', '4': 'eun04.txt'}[tag.split('-')[0]]
SRC = open(os.path.join(T, '..', '원문', src), encoding='utf-8').read().split('\n')
R = os.path.join(T, '결과')
para_list = json.load(open(os.path.join(R, f'{tag}_{n}_단락.json'), encoding='utf-8'))['단락']
lp = os.path.join(R, f'{tag}_{n}_줄.json')
lines = json.load(open(lp, encoding='utf-8'))['목록'] if os.path.exists(lp) else None
rp = sys.argv[3] if len(sys.argv) > 3 else os.path.join(R, f'{tag}_{n}_기록.json')
try:
    res = json.load(open(rp, encoding='utf-8'))
except Exception as e:
    print('기록 파일을 읽을 수 없음:', e); sys.exit(1)
bad = []
ws = re.compile(r'\s+')
def norm(s): return ws.sub('', s or '')
QMAX, WHYMIN = 60, 10

# 기준 문장, 남은 것의 종류, 이미 쓴 남은 것 번호
CRIT = norm(open(os.path.join(D, '원작 정리본 기준.md'), encoding='utf-8').read())
NOW = open(os.path.join(D, '지금 하는 일.md'), encoding='utf-8').read()
m = re.search(r'고치지 않고 최종점검 남은 것\.md에 적음: (.*?)\.\n', NOW)
KINDS = [k.strip() for k in m.group(1).split(',')] if m else []
if not KINDS: bad.append('지금 하는 일.md에서 남은 것의 종류를 찾지 못함')
LEFT = open(os.path.join(D, '최종점검 남은 것.md'), encoding='utf-8').read()
used = [int(x) for x in re.findall(r'^\|?\s*-?\s*(\d+)[.|)]', LEFT, re.M)]
last = max(used) if used else 0

# 대조표
PYO = []            # (번역본 표기, 기준 표기): 기준 표기와 다른 번역본 표기
ALLSTD = set()      # 모든 기준 표기
FORMS = {}          # 기준 표기 → 원문에 나올 수 있는 표기들
TITLE = r'(공작|후작|백작|자작|남작|제독|원수|대장|중장|소장|준장|대령|중령|소령|대위|중위|소위|부인|황제|황후|경)(?=\s|$)|^(공작|후작|백작|자작|남작|제독)\s'
sec = None
for l in open(os.path.join(D, '표기와 원문 문제.md'), encoding='utf-8'):
    if l.startswith('### '): sec = l[4:].strip(); continue
    if sec in ('인물', '지명', '그 밖의 이름') and l.startswith('| ') and not l.startswith('| 번역본') and not l.startswith('|---'):
        c = [x.strip() for x in l.rstrip().split('|')[1:-1]]
        if len(c) < 2 or not c[1]: continue
        ALLSTD.add(c[1])
        t = re.sub(r'\(.*?\)', '', c[0]).strip()       # 괄호 안은 같은 표기 가운데 누구인지 가르는 말
        FORMS.setdefault(c[1], {c[1]}).add(t)
        core = re.sub(TITLE, '', t)                    # 앞뒤에 붙은 작위·직함만 다른 것은 같은 표기
        if len(t) >= 2 and norm(core) not in norm(c[1]): PYO.append((t, c[1]))   # 기준 표기의 줄임은 문장 안에서 써도 됨
STD = sorted(ALLSTD, key=len, reverse=True)            # 다른 사람의 기준 표기와 같은 번역본 표기는 가릴 수 없어 검사에서 뺌

def why_ok(where, field, v):
    if not v or len(norm(v)) < WHYMIN: bad.append(f'{where}: {field}이 없거나 너무 짧음({WHYMIN}자 미만)'); return False
    return True
def chk_crit(where, cs):
    if not isinstance(cs, list) or not cs: bad.append(f'{where}: 기준 인용 없음'); return
    for c in cs:
        if len(norm(c)) < 8: bad.append(f'{where}: 기준 인용이 너무 짧음 "{c}"')
        elif norm(c) not in CRIT: bad.append(f'{where}: 기준 인용 "{str(c)[:40]}"이 기준 파일에 없음')
def rng(r):
    mm = re.fullmatch(r'(\d+)(?:-(\d+))?', str(r))
    return (int(mm.group(1)), int(mm.group(2) or mm.group(1))) if mm else None

# 1. 단락과 사실
FACT = {}
paras = {p['단락']: rng(p['행']) for p in para_list}
seen = set()
for p in res.get('단락', []):
    k = p.get('단락'); w = f'단락 {k}'
    if k not in paras: bad.append(f'{w}: 단락 목록에 없음'); continue
    if k in seen: bad.append(f'{w}: 겹침'); continue
    seen.add(k)
    fs = p.get('사실')
    if not fs:
        why_ok(w, '"없음"의 까닭', p.get('없음')); continue
    pa, pb = paras[k]
    for f in fs:
        i = f.get('번호'); fw = f'사실 {i}'
        if not isinstance(i, int): bad.append(f'{w}: 번호 없는 사실'); continue
        if i in FACT: bad.append(f'{fw}: 번호 겹침'); continue
        FACT[i] = f
        r = rng(f.get('행', '')); g = f.get('구절', '')
        if not f.get('내용'): bad.append(f'{fw}: 내용 없음')
        if not r: bad.append(f'{fw}: 행 꼴 틀림 "{f.get("행")}"'); continue
        if r[0] < pa or r[1] > pb: bad.append(f'{fw}: 행 {f.get("행")}이 단락 {k}({pa}-{pb}) 밖'); continue
        if len(norm(g)) < 4: bad.append(f'{fw}: 구절이 너무 짧음 "{g}"'); continue
        if len(norm(g)) > QMAX: bad.append(f'{fw}: 구절이 {QMAX}자를 넘음({len(norm(g))}자)'); continue
        if norm(g) not in norm(''.join(SRC[r[0] - 1:r[1]])): bad.append(f'{fw}: 구절 "{g[:40]}"이 원문 {f.get("행")}행에 없음')
miss = [k for k in paras if k not in seen]
if miss: bad.append(f'빈 단락 {len(miss)}: ' + ', '.join(map(str, miss)))

if lines is not None:
    # 2. 줄
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
        if fname == '표기와 원문 문제.md': return
        t = QUOTED.sub(' ', ' '.join(cells(row)[:-1]))
        for s in STD: t = t.replace(s, ' ')
        for a, b in PYO:
            if re.search(r'(?<![가-힣])' + re.escape(a), t): bad.append(f'{where}: 대조표의 번역본 표기 "{a}"가 쓰임(기준 표기 "{b}")')
    cit = re.compile(r'(?<![\d-])(\d)-(\d{1,2})\(([^)]*)\)')
    def spans(row):
        out = []
        for mm in cit.finditer(row or ''):
            if f'{mm.group(1)}-{mm.group(2)}' != tag: continue
            for part in mm.group(3).split(','):
                nums = re.findall(r'\d+', part)
                if nums: out.append((int(nums[0]), int(nums[-1])))
        return [(a, b) for a, b in out if a <= hi and b >= lo]
    NUM = re.compile(r'\d[\d,]*')
    def chk_facts_vs_row(where, p, row, fname, fids):
        fs = [FACT[i] for i in fids if i in FACT]
        if not fs: return
        sp = spans(row)
        fr = [rng(f['행']) for f in fs if rng(f.get('행', ''))]
        for sa, sb in sp:   # 근거 행 범위마다 겹치는 사실이 있어야 함
            if not any(a <= sb + 2 and b >= sa - 2 for a, b in fr):
                bad.append(f'{where}: 이은 사실이 근거 행 {sa}-{sb}과 겹치지 않음')
        if fname == '표기와 원문 문제.md': return
        c = cells(row)
        if len(c) < 5: return
        q = norm(''.join(f.get('구절', '') for f in fs))
        nums = sorted({x.replace(',', '') for x in NUM.findall(c[2] + ' ' + c[3])})
        nm = [x for x in nums if x not in q.replace(',', '')]
        if nm and not p.get('숫자 까닭'): bad.append(f'{where}: 줄의 숫자 {", ".join(nm)}가 이은 사실의 인용에 없음(숫자 까닭 없음)')
        elif nm: why_ok(where, '숫자 까닭', p.get('숫자 까닭'))
        t = QUOTED.sub(' ', c[2] + ' ' + c[3]); names = []
        for s in STD:
            if re.search(r'(?<![가-힣])' + re.escape(s), t):
                names.append(s); t = t.replace(s, ' ')
        def found(s):
            for form in FORMS.get(s, {s}):
                if norm(form) in q: return True
                if any(len(tok) >= 2 and tok in q for tok in re.split(r'[\s·.]+', form)): return True
            return False
        nn = [s for s in names if not found(s)]
        if nn and not p.get('이름 까닭'): bad.append(f'{where}: 줄의 이름 {", ".join(nn)}가 이은 사실의 인용에 없음(이름 까닭 없음)')
        elif nn: why_ok(where, '이름 까닭', p.get('이름 까닭'))

    left = {}
    for p in res.get('남은 것', []):
        k = p.get('번호'); w = f'남은 것 {k}'
        if not isinstance(k, int): bad.append('번호 없는 남은 것'); continue
        if k in left: bad.append(f'{w}: 번호 겹침')
        left[k] = p
        if p.get('종류') not in KINDS: bad.append(f'{w}: 종류 "{p.get("종류")}"가 {KINDS} 가운데 하나가 아님')
        for f in ('무엇', '문구 안', '자리'):
            if not p.get(f): bad.append(f'{w}: {f} 없음')
        why_ok(w, '까닭', p.get('까닭'))
        chk_crit(w, p.get('기준'))
        for i in p.get('사실', []) or []:
            if i not in FACT: bad.append(f'{w}: 사실 {i}가 없음')
    if left:
        ks = sorted(left)
        if ks[0] <= last: bad.append(f'남은 것 번호 {ks[0]}이 이미 쓴 번호({last}까지)와 겹침')
        if ks != list(range(ks[0], ks[0] + len(ks))): bad.append(f'남은 것 번호가 이어지지 않음: {ks}')
    ref_left, linked = set(), set()

    want = [r['줄'] for r in lines]
    orig = {r['줄']: r['원래 줄'] for r in lines}
    got = [p.get('줄') for p in res.get('줄', [])]
    mi = [x for x in want if x not in got]
    ex = [x for x in got if x not in want]
    dup = sorted({x for x in got if got.count(x) > 1})
    if mi: bad.append(f'처리 안 한 줄 {len(mi)}: ' + ', '.join(mi[:30]))
    if ex: bad.append(f'줄 목록에 없는 줄 {len(ex)}: ' + ', '.join(ex[:30]))
    if dup: bad.append('겹친 줄: ' + ', '.join(dup[:30]))
    for p in res.get('줄', []):
        w = p.get('줄'); k = p.get('처리'); fn = str(w).split(':')[0]
        if w not in orig: continue
        if k not in ('이음', '고침', '남은 것'): bad.append(f'{w}: 처리 값 "{k}"'); continue
        fids = p.get('사실') or []
        for i in fids:
            if i not in FACT: bad.append(f'{w}: 사실 {i}가 없음')
            else: linked.add(i)
        if k in ('이음', '고침') and not fids: bad.append(f'{w}: 이은 사실 없음')
        if k == '이음':
            chk_pyo(w, orig[w], fn)
            chk_facts_vs_row(w, p, orig[w], fn, fids)
        if k == '고침':
            why_ok(w, '까닭', p.get('까닭'))
            chk_crit(w, p.get('기준'))
            new = p.get('고친 줄')
            if chk_row(w, new, fn):
                if new.strip() == orig[w].strip(): bad.append(f'{w}: 고친 줄이 원래 줄과 같음')
                chk_pyo(w, new, fn)
                chk_facts_vs_row(w, p, new, fn, fids)
        if k == '남은 것':
            chk_crit(w, p.get('기준'))
            if p.get('남은 것') not in left: bad.append(f'{w}: 남은 것 번호 {p.get("남은 것")}가 기록의 "남은 것"에 없음')
            ref_left.add(p.get('남은 것'))

    # 3. 남는 사실
    rest = set()
    for p in res.get('남는 사실', []):
        i = p.get('사실'); k = p.get('처리'); w = f'남는 사실 {i}'
        if i not in FACT: bad.append(f'{w}: 사실이 없음'); continue
        if i in rest: bad.append(f'{w}: 겹침')
        rest.add(i)
        if k == '근거 덧붙임':
            f = str(p.get('줄', '')).split(':')
            if len(f) != 2 or not f[1].isdigit(): bad.append(f'{w}: 줄 꼴 틀림'); continue
            path = os.path.join(D, f[0])
            if not os.path.exists(path): bad.append(f'{w}: 파일 없음 {f[0]}'); continue
            if p['줄'] in orig: bad.append(f'{w}: 줄 목록에 있는 줄임(그 줄에 사실을 이을 것)')
            cur = open(path, encoding='utf-8').read().split('\n')[int(f[1]) - 1]
            new = p.get('고친 줄', '')
            if chk_row(w, new, f[0]):
                if tag + '(' not in new: bad.append(f'{w}: 고친 줄에 {tag} 근거가 없음')
                if cells(cur)[:-1] != cells(new)[:-1]: bad.append(f'{w}: 근거 칸 말고 다른 칸이 바뀜')
        elif k == '남은 것':
            if p.get('남은 것') not in left: bad.append(f'{w}: 남은 것 번호 {p.get("남은 것")}가 기록의 "남은 것"에 없음')
            ref_left.add(p.get('남은 것'))
        elif k == '적을 것 없음':
            chk_crit(w, p.get('기준'))
            why_ok(w, '까닭', p.get('까닭'))
        else:
            bad.append(f'{w}: 처리 값 "{k}"')
    orphan = sorted(set(FACT) - linked - rest)
    if orphan: bad.append(f'줄에도 이어지지 않고 처리도 안 한 사실 {len(orphan)}: ' + ', '.join(map(str, orphan[:40])))
    lonely = sorted(set(left) - ref_left)
    if lonely: bad.append(f'줄이나 남는 사실에서 가리키지 않은 남은 것: {lonely}')

stage = '사실 뽑기' if lines is None else '전체'
if bad:
    print(f'{tag} 장면 {n} ({stage}): 걸림 {len(bad)}'); print('\n'.join(bad)); sys.exit(1)
P = res.get('단락', [])
s = f'{tag} 장면 {n} ({stage}): 통과. 단락 {len(P)}(없음 {sum(1 for p in P if not p.get("사실"))}), 사실 {len(FACT)}'
if lines is not None:
    J, X = res.get('줄', []), res.get('남는 사실', [])
    c = lambda xs, v: sum(1 for x in xs if x.get('처리') == v)
    s += (f', 정리본 줄 {len(J)}(이음 {c(J, "이음")}, 고침 {c(J, "고침")}, 남은 것 {c(J, "남은 것")}), '
          f'남는 사실 {len(X)}(근거 덧붙임 {c(X, "근거 덧붙임")}, 남은 것 {c(X, "남은 것")}, 적을 것 없음 {c(X, "적을 것 없음")}), 새 남은 것 {len(res.get("남은 것", []))}')
print(s)
