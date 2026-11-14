#!/usr/bin/env python3
# 사용: python3 검사.py 1-3 2  → 결과/1-3_2_기록.json을 검사.
#       통과면 "통과"와 셈을, 아니면 걸린 것을 모두 적고 끝 코드 1.
#       다른 파일을 검사하려면 셋째 인자로 기록 파일 경로를 줌.
#       기록에 "줄"이 아직 없으면(사실 뽑기 단계) 단락과 사실만 검사함.
#       "줄"이 있으면 갈래 1~11과 표기마다 뽑기.py로 기준과 줄을 모든 쪽까지 찍었는지도 봄(결과/1-3_2_띄움.json).
#       장면의 정리본 줄 목록은 뽑기.py의 파일을 읽지 않고 같은 규칙으로 직접 셈.
#
# 기록 파일 꼴
# {
#  "단락": [                                  ← 단락 목록의 단락마다 하나
#   {"단락": 1, "사실": [{"번호": 1, "이름표": "탈출", "행": "105-106", "구절": "원문 그대로(60자 안)", "내용": "사실 하나"}]},
#   {"단락": 2, "없음": "적을 사실이 없는 까닭"}
#   (단락의 숫자나 대조표 이름이 사실의 구절·내용에 없으면 단락에 "뺀 숫자", "뺀 이름" 까닭.
#    사실의 숫자가 이은 줄·넣은 줄에 없고 남는 사실로 처리하지도 않으면 사실에 "숫자 까닭")
#  ],
#  "줄": [                                    ← 정리본 줄 목록의 줄마다 하나
#   {"줄": "1_인물.md:123", "처리": "이음", "사실": [1, 2]},
#   {"줄": "...", "처리": "고침", "사실": [3], "고친 줄": "| ... |", "까닭": "...", "기준": ["기준 문장 그대로"],
#    "같은 줄": ["7_….md:34"] 또는 ["없음"]},   ← 고친 뒤에도 고치지 못한 물음이 남으면 "남은 것": 번호
#   {"줄": "...", "처리": "남은 것", "남은 것": 59, "기준": ["..."]}   ← 번호는 이 기록의 "남은 것"이나 "앞 남은 것"에 있어야 함
#   (이음과 고침에는 필요하면 "숫자 까닭", "이름 까닭". 까닭에는 줄의 근거 칸에 있는 권-장의 "권-장(행) '원문 구절'"이나 "원문 문제 N"을 적음)
#   (사실은 번호 대신 이름표로 가리켜도 됨. 줄, 남는 사실, 남은 것 모두 같음)
#  ],
#  "남는 사실": [                              ← 어느 줄에도 이어지지 않은 사실마다 하나
#   {"사실": 4, "처리": "근거 덧붙임", "줄": "1_인물.md:456", "고친 줄": "| ... |"},   ← 줄에 이은 사실도 적을 수 있음
#   {"사실": 5, "처리": "남은 것", "남은 것": 60},
#   {"사실": 6, "처리": "적을 것 없음", "종류": "기준상 뺌", "기준": ["..."], "까닭": "..."},
#   {"사실": 7, "처리": "적을 것 없음", "종류": "줄여 적힘", "줄": "7_….md:32", "받는 말": "그 줄 안의 말 그대로", "까닭": "..."},
#   {"사실": 8, "처리": "적을 것 없음", "종류": "꼭 적을 것 아님", "까닭": "이름, 숫자, 자리의 변동, 제도의 규칙 가운데 어느 것도 아닌 까닭"}
#  ],
#  "넣음": [                                  ← 새로 넣는 줄(나눠 떼어 낸 줄, 꼭 적을 것). 여기 든 사실은 이어진 것으로 봄
#   {"넣을 줄": "| ... |", "자리": "7_….md:43", "사실": [9], "기준": ["..."], "까닭": "..."}   ← 자리는 그 줄 바로 뒤
#  ],
#  "앞 남은 것": [                             ← 남은 것.md에 이미 있는 같은 물음. 그 번호에 자리와 원문 행만 덧붙임
#   {"번호": 4, "자리": "7_….md:53, 54", "장과 원문 행": "1권 서장 266-310"}
#  ],
#  "남은 것": [                               ← 이 장면에서 새로 생긴 남은 것(줄이나 남는 사실에서 가리키지 않으면 "사실"이 있어야 함)
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
rp = sys.argv[3] if len(sys.argv) > 3 else os.path.join(R, f'{tag}_{n}_기록.json')
try:
    res = json.load(open(rp, encoding='utf-8'))
except Exception as e:
    print('기록 파일을 읽을 수 없음:', e); sys.exit(1)
bad = []
ws = re.compile(r'\s+')
cit = re.compile(r'(?<![\d-])(\d)-(\d{1,2})\(([^)]*)\)')
def spans(row):
    out = []
    for mm in cit.finditer(row or ''):
        if f'{mm.group(1)}-{mm.group(2)}' != tag: continue
        for part in mm.group(3).split(','):
            nums = re.findall(r'\d+', part)
            if nums: out.append((int(nums[0]), int(nums[-1])))
    return [(a, b) for a, b in out if a <= hi and b >= lo]
def all_lines():
    import glob
    files = sorted([f for f in glob.glob(D + '/*.md') if re.match(r'\d+_', os.path.basename(f))],
                   key=lambda f: int(os.path.basename(f).split('_')[0])) + [D + '/표기와 원문 문제.md']
    rows = []
    for f in files:
        for i, l in enumerate(open(f, encoding='utf-8'), 1):
            if l.startswith('| ') and spans(l):
                rows.append({'줄': f'{os.path.basename(f)}:{i}', '원래 줄': l.rstrip('\n')})
    return rows
def file_line(k):
    f = str(k).split(':')
    if len(f) != 2 or not f[1].isdigit() or not os.path.exists(os.path.join(D, f[0])): return None
    L = open(os.path.join(D, f[0]), encoding='utf-8').read().split('\n')
    i = int(f[1])
    return L[i - 1] if 1 <= i <= len(L) else None
lines = all_lines() if '줄' in res else None
def norm(s): return ws.sub('', s or '')
QMAX, WHYMIN = 60, 10
NUMRE = re.compile(r'\d[\d,]*')

# 기준 문장, 남은 것의 종류, 이미 쓴 남은 것 번호
CRIT = norm(open(os.path.join(D, '원작 정리본 기준.md'), encoding='utf-8').read())
NOW = open(os.path.join(D, '지금 하는 일.md'), encoding='utf-8').read()
m = re.search(r'고치지 않고 최종점검 남은 것\.md에 적음: (.*?)\.\n', NOW)
KINDS = [k.strip() for k in m.group(1).split(',')] if m else []
if not KINDS: bad.append('지금 하는 일.md에서 남은 것의 종류를 찾지 못함')
LEFT = open(os.path.join(D, '최종점검 남은 것.md'), encoding='utf-8').read()
LEFTROW = {int(m.group(1)): m.group(2) for m in re.finditer(r'^- (\d+)\. (.*)$', LEFT, re.M)}
mine = {p.get('번호') for p in res.get('남은 것', []) if isinstance(p.get('번호'), int) and LEFTROW.get(p['번호'], '').startswith(str(p.get('무엇', '')) + '.')}
used = [k for k in LEFTROW if k not in mine]   # 이 기록에서 이미 반영한 번호(번호와 "무엇"이 같은 줄)는 겹침으로 보지 않음
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
TOKOWN = {}
for _std, _forms in FORMS.items():
    for _t in {t for form in _forms for t in re.split(r'[\s·.]+', form) if len(t) >= 2}: TOKOWN[_t] = TOKOWN.get(_t, 0) + 1
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
    fs = p.get('사실') or []
    if not fs: why_ok(w, '"없음"의 까닭', p.get('없음'))
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
        elif r[1] > r[0] and (norm(g) in norm(''.join(SRC[r[0]:r[1]])) or norm(g) in norm(''.join(SRC[r[0] - 1:r[1] - 1]))):
            bad.append(f'{fw}: 행 범위 {f.get("행")}이 구절보다 넓음')
    # 단락의 숫자와 대조표 이름이 사실에 들었는지
    ptxt = next(x['원문'] for x in para_list if x['단락'] == k)
    ftxt = norm(''.join((f.get('구절') or '') + ' ' + (f.get('내용') or '') for f in fs))
    fnum = {x.replace(',', '') for f in fs for x in NUMRE.findall(f.get('구절') or '')}
    mn = sorted({x.replace(',', '') for x in NUMRE.findall(ptxt)} - fnum)
    if mn:
        v = p.get('뺀 숫자') or ''
        left_n = [x for x in mn if x not in v]
        if left_n or len(norm(v)) < WHYMIN: bad.append(f'{w}: 원문의 숫자 {", ".join(left_n or mn)}가 사실의 구절에 없음("뺀 숫자" 까닭 없음)')
    pn = norm(ptxt); mnm = []
    for std, forms in FORMS.items():
        toks = {t for form in forms for t in re.split(r'[\s·.]+', form) if len(t) >= 2}
        # 낱말 하나로 찾는 것은 그 낱말이 이 이름에만 있을 때만(여러 이름에 든 낱말은 전체 표기로만 찾음)
        hit = any(len(norm(form)) >= 2 and norm(form) in pn for form in forms) or any(len(t) >= 3 and t in pn and TOKOWN.get(t) == 1 for t in toks)
        if hit and not (any(norm(form) in ftxt for form in forms) or any(t in ftxt for t in toks)): mnm.append(std)
    if mnm:
        v = p.get('뺀 이름') or ''
        left_m = [x for x in mnm if x not in v]
        if left_m or len(norm(v)) < WHYMIN: bad.append(f'{w}: 원문의 이름 {", ".join(left_m or mnm)}가 사실에 없음("뺀 이름" 까닭 없음)')
TAG = {}
for i, f in FACT.items():
    t = f.get('이름표')
    if t is None: continue
    if not isinstance(t, str) or not t.strip(): bad.append(f'사실 {i}: 이름표 꼴 틀림'); continue
    if t in TAG: bad.append(f'사실 {i}: 이름표 "{t}" 겹침(사실 {TAG[t]})'); continue
    TAG[t] = i
def rid(x, where):
    if isinstance(x, str):
        if x in TAG: return TAG[x]
        bad.append(f'{where}: 이름표 "{x}"인 사실이 없음'); return None
    return x
for p in res.get('줄', []):
    if isinstance(p.get('사실'), list): p['사실'] = [y for y in (rid(x, p.get('줄')) for x in p['사실']) if y is not None]
for p in res.get('남는 사실', []):
    if isinstance(p.get('사실'), str): p['사실'] = rid(p['사실'], '남는 사실')
for p in res.get('넣음', []):
    if isinstance(p.get('사실'), list): p['사실'] = [y for y in (rid(x, '넣음') for x in p['사실']) if y is not None]
for p in res.get('남은 것', []):
    if isinstance(p.get('사실'), list): p['사실'] = [y for y in (rid(x, f'남은 것 {p.get("번호")}') for x in p['사실']) if y is not None]
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
    PROB = {int(m.group(1)) for m in re.finditer(r'^\| (\d+) \|', open(os.path.join(D, '표기와 원문 문제.md'), encoding='utf-8').read(), re.M)}
    def src_ok(where, field, v, row):
        if not why_ok(where, field, v): return
        refc = cells(row)[-1] if row else ''
        ok = False
        for a, b, r1, r2, q in CITEQ.findall(v):
            if f'{a}-{b}(' not in refc:
                bad.append(f'{where}: {field}의 {a}-{b}가 줄의 근거 칸에 없음'); continue
            L = srcfile(a); x, y = int(r1), int(r2 or r1)
            if norm(q) and norm(q) in norm(''.join(L[x - 1:y])): ok = True
            else: bad.append(f'{where}: {field}의 구절 "{q[:30]}"이 {a}권 원문 {x}-{y}행에 없음')
        ok = ok or any(int(x) in PROB for x in re.findall(r'원문 문제 (\d+)', v))
        if not ok: bad.append(f"{where}: {field}에 줄의 근거 칸에 있는 \"권-장(행) '원문 구절'\"이나 원문 문제 표에 있는 번호가 없음")
    CITEQ = re.compile(r"(?<![\d-])(\d)-(\d{1,2})\((\d+)(?:-(\d+))?\)\s*['‘\"“]([^'’\"”]+)['’\"”]")
    SRCS = {}
    def srcfile(a):
        if a not in SRCS:
            fn = {'1': 'eun01_1.txt', '2': 'eun02.txt', '3': 'eun03.txt', '4': 'eun04.txt'}[a]
            SRCS[a] = open(os.path.join(T, '..', '원문', fn), encoding='utf-8').read().split('\n')
        return SRCS[a]
    NUM = re.compile(r'\d[\d,]*')
    def chk_facts_vs_row(where, p, row, fname, fids):
        fs = [FACT[i] for i in fids if i in FACT]
        if not fs: return
        sp = spans(row)
        fr = [rng(f['행']) for f in fs if rng(f.get('행', ''))]
        for sa, sb in sp:   # 근거 행 범위마다 겹치는 사실이 있어야 함
            if not any(a <= sb + 2 and b >= sa - 2 for a, b in fr):
                bad.append(f'{where}: 이은 사실이 근거 행 {sa}-{sb}과 겹치지 않음')
        for f in fs:        # 이은 사실의 행은 줄의 근거에 들어야 함
            r = rng(f.get('행', ''))
            if r and not any(r[0] <= sb + 2 and r[1] >= sa - 2 for sa, sb in sp):
                bad.append(f'{where}: 이은 사실 {f.get("이름표") or f.get("번호")}의 행 {f["행"]}이 줄의 근거에 없음')
        if fname == '표기와 원문 문제.md': return
        c = cells(row)
        if len(c) < 5: return
        q = norm(''.join(f.get('구절', '') for f in fs))
        nums = sorted({x.replace(',', '') for x in NUM.findall(c[2] + ' ' + c[3])})
        nm = [x for x in nums if x not in q.replace(',', '')]
        if nm and not p.get('숫자 까닭'): bad.append(f'{where}: 줄의 숫자 {", ".join(nm)}가 이은 사실의 인용에 없음(숫자 까닭 없음)')
        elif nm: src_ok(where, '숫자 까닭', p.get('숫자 까닭'), row)
        t = QUOTED.sub(' ', c[3]); names = []   # 이름은 내용 칸만 봄(시점 칸의 "아스타테 직전" 같은 말은 시점 꼴)
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
        elif nn: src_ok(where, '이름 까닭', p.get('이름 까닭'), row)

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
        if any(k in used for k in ks) or (ks[0] <= last and not set(ks) <= mine): bad.append(f'남은 것 번호 {ks[0]}이 이미 쓴 번호({last}까지)와 겹침')
        if ks != list(range(ks[0], ks[0] + len(ks))): bad.append(f'남은 것 번호가 이어지지 않음: {ks}')
    prev = {}
    for p in res.get('앞 남은 것', []):
        k = p.get('번호')
        if k not in LEFTROW or k in left: bad.append(f'앞 남은 것 {k}: 남은 것.md에 이미 있는 번호가 아님'); continue
        if not p.get('자리') or not p.get('장과 원문 행'): bad.append(f'앞 남은 것 {k}: 자리나 장과 원문 행 없음')
        prev[k] = p
    known = set(left) | set(prev)
    ref_left, linked = set(), set()
    FINAL = {}          # 사실 번호 → 그 사실을 받은 줄(고친 줄, 넣은 줄)의 글
    def take(fids, row):
        for i in fids: FINAL.setdefault(i, []).append(' '.join(cells(row)[:-1]) if row else '')

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
            take(fids, orig[w])
        if k == '고침':
            why_ok(w, '까닭', p.get('까닭'))
            chk_crit(w, p.get('기준'))
            sl = p.get('같은 줄')
            if not isinstance(sl, list) or not sl: bad.append(f'{w}: 같은 줄(같은 대상·같은 때를 적은 다른 줄, 없으면 ["없음"])이 없음')
            elif sl != ['없음']:
                for k2 in sl:
                    if file_line(k2) is None: bad.append(f'{w}: 같은 줄 {k2}이 없음')
            new = p.get('고친 줄')
            if chk_row(w, new, fn):
                if cells(new) == cells(orig[w]): bad.append(f'{w}: 고친 줄이 원래 줄과 같음(바뀐 칸 없음)')
                chk_pyo(w, new, fn)
                chk_facts_vs_row(w, p, new, fn, fids)
                take(fids, new)
            if p.get('남은 것') is not None:      # 고친 줄에 고치지 못한 물음이 남으면 그 번호도 가리킴
                if p.get('남은 것') not in known: bad.append(f'{w}: 남은 것 번호 {p.get("남은 것")}가 기록의 "남은 것"이나 "앞 남은 것"에 없음')
                ref_left.add(p.get('남은 것'))
        if k == '남은 것':
            chk_crit(w, p.get('기준'))
            if p.get('남은 것') not in known: bad.append(f'{w}: 남은 것 번호 {p.get("남은 것")}가 기록의 "남은 것"이나 "앞 남은 것"에 없음')
            ref_left.add(p.get('남은 것'))
            take(fids, orig[w])

    # 2-1. 넣음
    for j, p in enumerate(res.get('넣음', []), 1):
        w = f'넣음 {j}'
        at = str(p.get('자리', '')); fn = at.split(':')[0]
        if file_line(at) is None: bad.append(f'{w}: 자리 {at}의 줄이 없음'); continue
        fids = p.get('사실') or []
        if not fids: bad.append(f'{w}: 받쳐 주는 사실 없음')
        for i in fids:
            if i not in FACT: bad.append(f'{w}: 사실 {i}가 없음')
            else: linked.add(i)
        why_ok(w, '까닭', p.get('까닭'))
        chk_crit(w, p.get('기준'))
        new = p.get('넣을 줄')
        if chk_row(w, new, fn):
            if tag + '(' not in cells(new)[2 if fn == '표기와 원문 문제.md' and cells(new)[0].isdigit() else -1]: bad.append(f'{w}: 넣을 줄에 {tag} 근거가 없음')
            chk_pyo(w, new, fn)
            chk_facts_vs_row(w, p, new, fn, fids)
            take(fids, new)

    # 3. 남는 사실
    rest = set()
    for p in res.get('남는 사실', []):
        i = p.get('사실'); k = p.get('처리'); w = f'남는 사실 {i}'
        if i not in FACT: bad.append(f'{w}: 사실이 없음'); continue
        if i in rest and k != '근거 덧붙임': bad.append(f'{w}: 겹침')
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
                r = rng(FACT[i].get('행', ''))
                if r and not any(r[0] <= sb + 2 and r[1] >= sa - 2 for sa, sb in spans(new)): bad.append(f'{w}: 고친 줄의 근거가 사실의 행 {FACT[i]["행"]}을 덮지 않음')
                take([i], new)
        elif k == '남은 것':
            if p.get('남은 것') not in known: bad.append(f'{w}: 남은 것 번호 {p.get("남은 것")}가 기록의 "남은 것"이나 "앞 남은 것"에 없음')
            ref_left.add(p.get('남은 것'))
        elif k == '적을 것 없음':
            why_ok(w, '까닭', p.get('까닭'))
            kind = p.get('종류')
            if kind == '기준상 뺌': chk_crit(w, p.get('기준'))
            elif kind == '줄여 적힘':
                row = file_line(p.get('줄'))
                fr = rng(FACT[i].get('행', ''))
                if row is None: bad.append(f'{w}: 줄여 받은 줄 {p.get("줄")}이 없음')
                else:
                    if fr and not any(a <= fr[1] + 2 and b >= fr[0] - 2 for a, b in spans(row)):
                        bad.append(f'{w}: 줄여 받은 줄의 이 장 근거가 사실의 행 {FACT[i]["행"]}을 덮지 않음')
                    bm = p.get('받는 말')
                    if not bm or len(norm(bm)) < 2: bad.append(f'{w}: 받는 말(그 줄 안에서 이 사실을 받는 말)이 없음')
                    elif norm(bm) not in norm(row): bad.append(f'{w}: 받는 말 "{bm[:30]}"이 줄 {p.get("줄")}에 없음')
            elif kind != '꼭 적을 것 아님': bad.append(f'{w}: 종류가 "줄여 적힘", "기준상 뺌", "꼭 적을 것 아님"이 아님')
        else:
            bad.append(f'{w}: 처리 값 "{k}"')
    for k in prev:
        if k not in ref_left: bad.append(f'앞 남은 것 {k}: 줄이나 남는 사실에서 가리키지 않음')
    # 사실의 숫자가 그 사실을 받은 줄에 있는지(남는 사실로 처리했거나 "숫자 까닭"이 있으면 넘어감)
    handled = {p.get('사실') for p in res.get('남는 사실', []) if p.get('처리') in ('남은 것', '적을 것 없음')}
    for i, f in sorted(FACT.items()):
        if i not in FINAL or i in handled: continue
        have = {x.replace(',', '') for t in FINAL[i] for x in NUMRE.findall(t)}
        mn = sorted({x.replace(',', '') for x in NUMRE.findall(f.get('구절') or '')} - have)
        if mn and len(norm(f.get('숫자 까닭') or '')) < WHYMIN:
            bad.append(f'사실 {f.get("이름표") or i}: 구절의 숫자 {", ".join(mn)}가 이은 줄이나 넣은 줄에 없음(처리나 "숫자 까닭" 없음)')
    orphan = sorted(set(FACT) - linked - rest)
    if orphan: bad.append(f'줄에도 이어지지 않고 처리도 안 한 사실 {len(orphan)}: ' + ', '.join(map(str, orphan[:40])))
    lonely = sorted(k for k in set(left) - ref_left if not left[k].get('사실') or any(i not in FACT for i in left[k]['사실']))
    if lonely: bad.append(f'줄이나 남는 사실에서 가리키지 않았고 이 장면의 사실도 적지 않은 남은 것: {lonely}')

# 갈래마다 뽑기.py로 기준과 줄을 모든 쪽까지 찍었는지, 그 뒤 기준 파일과 줄 목록이 바뀌지 않았는지
if lines is not None:
    import hashlib
    sp_ = os.path.join(R, f'{tag}_{n}_띄움.json')
    shown_ = json.load(open(sp_, encoding='utf-8')) if os.path.exists(sp_) else {}
    ksig = hashlib.sha1(open(os.path.join(D, '원작 정리본 기준.md'), encoding='utf-8').read().encode('utf-8')).hexdigest()
    LINEKEYS = [r['줄'] for r in lines]
    for g_ in [str(i) for i in range(1, 12)] + ['표기']:
        pre = '표기와 원문 문제.md:' if g_ == '표기' else None
        mine = sorted(k for k in LINEKEYS if (k.startswith(pre) if pre else k.split('_')[0] == g_))
        e = shown_.get(g_)
        if not e: bad.append(f'갈래 {g_}: 뽑기.py로 기준과 줄을 찍은 기록이 없음'); continue
        left = [k for k in range(1, e.get('쪽 수', 0) + 1) if k not in e.get('띄운 쪽', [])]
        if left: bad.append(f'갈래 {g_}: 안 찍은 쪽이 있음 {left}')
        if e.get('기준 지문') != ksig: bad.append(f'갈래 {g_}: 찍은 뒤 기준 파일이 바뀜(다시 찍어야 함)')
        if sorted(e.get('줄', [])) != mine: bad.append(f'갈래 {g_}: 찍은 줄 목록이 지금의 줄 목록과 다름(다시 찍어야 함)')
    # 남는 사실을 처리하기 직전에 기준 전체를 폈는지(모든 쪽, 갈래의 줄을 다 찍은 뒤)
    e = shown_.get('기준')
    if not e: bad.append('기준 전체: 뽑기.py "기준"으로 찍은 기록이 없음')
    else:
        left = [k for k in range(1, e.get('쪽 수', 0) + 1) if k not in e.get('띄운 쪽', [])]
        if left: bad.append(f'기준 전체: 안 찍은 쪽이 있음 {left}')
        if e.get('기준 지문') != ksig: bad.append('기준 전체: 찍은 뒤 기준 파일이 바뀜(다시 찍어야 함)')
        late = [g_ for g_ in shown_ if g_ != '기준' and shown_[g_].get('때', 0) > e.get('때', 0)]
        if late: bad.append(f'기준 전체: 갈래 {", ".join(late)}의 줄을 그 뒤에 찍음(줄 판정을 다 마친 뒤 기준 전체를 다시 찍어야 함)')
stage = '사실 뽑기' if lines is None else '전체'
if bad:
    print(f'{tag} 장면 {n} ({stage}): 걸림 {len(bad)}'); print('\n'.join(bad)); sys.exit(1)
P = res.get('단락', [])
s = f'{tag} 장면 {n} ({stage}): 통과. 단락 {len(P)}(없음 {sum(1 for p in P if not p.get("사실"))}), 사실 {len(FACT)}'
if lines is not None:
    J, X = res.get('줄', []), res.get('남는 사실', [])
    c = lambda xs, v: sum(1 for x in xs if x.get('처리') == v)
    s += (f', 정리본 줄 {len(J)}(이음 {c(J, "이음")}, 고침 {c(J, "고침")}, 남은 것 {c(J, "남은 것")}), '
          f'남는 사실 {len(X)}(근거 덧붙임 {c(X, "근거 덧붙임")}, 남은 것 {c(X, "남은 것")}, 적을 것 없음 {c(X, "적을 것 없음")}), '
          f'넣음 {len(res.get("넣음", []))}, 새 남은 것 {len(res.get("남은 것", []))}, 앞 남은 것 {len(res.get("앞 남은 것", []))}')
print(s)
