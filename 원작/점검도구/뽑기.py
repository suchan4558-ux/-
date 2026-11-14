#!/usr/bin/env python3
# 사용: python3 뽑기.py 1-3 2 단락 → 1권 3장의 2번째 장면(장면.json 차례) 원문을 단락으로 나눠
#                                  결과/1-3_2_단락.json에 적음(공백으로 시작하는 줄에서 새 단락, 빈 줄에서 단락 끝)
#       python3 뽑기.py 1-3 2 줄 7 → 그 장면 행이 근거에 든 정리본 줄 가운데 갈래 7(7_….md)의 줄만
#                                  결과/1-3_2_줄_7.json에 적음. 갈래는 1~11 또는 "표기"(표기와 원문 문제.md).
#                                  갈래를 주지 않으면 돌리지 않음(갈래마다 기준을 편 뒤 그 갈래만 봄).
#                                  줄 목록보다 먼저 원작 정리본 기준.md의 공통 기준과 그 갈래의 기준
#                                  (표기는 별도 절차)을 화면에 찍고, 결과 파일에도 "기준"으로 넣음.
#                                  줄마다 그 줄의 이 장면 근거 원문을 함께 찍고(앞 줄과 근거가 같으면 "위와 같음"),
#                                  끝에 같은 대상·같은 항목인데 이 장 근거가 없는 줄을 찍음(표기는 뺌. 한 묶음이 15줄을 넘으면
#                                  화면에는 수만 찍고 전부는 결과 파일에 넣음).
#                                  출력을 버리거나(/dev/null) 파일로 돌리거나 다른 명령으로 넘겨(|) 자르면 돌지 않음.
#                                  출력이 길면 쪽으로 나눔. python3 뽑기.py 1-3 2 줄 7 2 → 2쪽을 찍음(쪽을 안 주면 1쪽).
#                                  찍은 쪽은 결과/1-3_2_띄움.json에 적고, 검사.py는 갈래마다 모든 쪽을 찍었는지 봄.
#       python3 뽑기.py 1-3 2 기준 [쪽] → 원작 정리본 기준.md 전체를 쪽으로 나눠 찍음(남는 사실을 처리하기 직전에 폄).
#                                  찍은 쪽과 때를 결과/1-3_2_띄움.json에 적고, 검사.py는 모든 쪽을 갈래의 줄보다 뒤에 찍었는지 봄.
# 사실을 뽑는 동안에는 "줄"을 돌리지 않음(기록 파일에 단락이 없으면 "줄"과 "기준"은 돌지 않음).
# 검사.py는 이 파일을 읽지 않고 같은 규칙으로 장면의 줄 전체를 직접 셈.
import re, sys, glob, os, json
T = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(T, '..', '정리본')
tag, n, mode = sys.argv[1], int(sys.argv[2]), sys.argv[3]
g = sys.argv[4] if len(sys.argv) > 4 else None
page = int(sys.argv[5]) if len(sys.argv) > 5 else 1
PAGE = 14000      # 한 쪽에 찍는 글자 수의 위
scenes = json.load(open(os.path.join(T, '장면.json'), encoding='utf-8'))
lo, hi = map(int, scenes[tag][n - 1].split('~'))
os.makedirs(os.path.join(T, '결과'), exist_ok=True)
p = os.path.join(T, '결과', f'{tag}_{n}_{mode}.json' if mode != '줄' else f'{tag}_{n}_줄_{g}.json')
import stat, hashlib, time
def screen_only():
    st = os.fstat(1)
    try: to = os.readlink('/proc/self/fd/1')
    except OSError: to = ''
    shown = re.search(r'/tasks/[^/]+\.output$', to)      # 채팅 도구가 화면 출력을 받아 두는 파일은 화면으로 봄
    if (stat.S_ISREG(st.st_mode) and not shown) or stat.S_ISFIFO(st.st_mode) or (stat.S_ISCHR(st.st_mode) and st.st_rdev == os.stat('/dev/null').st_rdev):
        print('출력을 버리거나 파일로 돌리거나 다른 명령으로 넘기면 돌지 않음(기준과 줄을 화면에 그대로 찍어야 함)', file=sys.stderr); sys.exit(1)
def facts_done():
    rp = os.path.join(T, '결과', f'{tag}_{n}_기록.json')
    if not (os.path.exists(rp) and json.load(open(rp, encoding='utf-8')).get('단락')):
        print('기록 파일에 단락(사실)이 없음. 사실 뽑기를 먼저 마침', file=sys.stderr); sys.exit(1)
def paginate(B):
    # 덩이를 차례로 담되 한 쪽이 PAGE자를 넘지 않게 함. 한 덩이가 PAGE자를 넘으면 그 덩이는 줄 사이에서 나눔
    B = [x.split('\n') for b in B for x in ['\n'.join(b)]]
    parts = []
    for b in B:
        cur = []
        for x in b:
            if cur and sum(len(y) + 1 for y in cur) + len(x) > PAGE:
                parts.append(cur); cur = []
            cur.append(x)
        if cur: parts.append(cur)
    pages = [[]]
    for b in parts:
        if pages[-1] and sum(len(y) + 1 for y in pages[-1]) + sum(len(y) + 1 for y in b) > PAGE:
            pages.append([])
        pages[-1] += b
    return pages
def show(key, pages, ksig, keys):
    sig = hashlib.sha1('\n'.join(x for pg in pages for x in pg).encode('utf-8')).hexdigest()
    if not 1 <= page <= len(pages):
        print(f'쪽은 1~{len(pages)}', file=sys.stderr); sys.exit(1)
    print('\n'.join(pages[page - 1]))
    sp_ = os.path.join(T, '결과', f'{tag}_{n}_띄움.json')
    shown_ = json.load(open(sp_, encoding='utf-8')) if os.path.exists(sp_) else {}
    e = shown_.get(key)
    if not e or e.get('지문') != sig:        # 내용이 바뀌었으면 처음부터 다시 찍어야 함
        e = {'지문': sig, '기준 지문': ksig, '쪽 수': len(pages), '띄운 쪽': [], '줄': keys}
    if page not in e['띄운 쪽']: e['띄운 쪽'] = sorted(e['띄운 쪽'] + [page])
    e['때'] = time.time()
    shown_[key] = e
    json.dump(shown_, open(sp_, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    left = [k for k in range(1, len(pages) + 1) if k not in e['띄운 쪽']]
    return f'{page}/{len(pages)}쪽' + (f'. 아직 안 찍은 쪽: {left}' if left else '. 모든 쪽을 찍음')

if mode == '단락':
    src = {'1': 'eun01_1.txt', '2': 'eun02.txt', '3': 'eun03.txt', '4': 'eun04.txt'}[tag.split('-')[0]]
    SRC = open(os.path.join(T, '..', '원문', src), encoding='utf-8').read().split('\n')
    paras, cur = [], None
    for i in range(lo, hi + 1):
        l = SRC[i - 1]
        if not l.strip():
            cur = None; continue
        if cur is None or l[0] in ' \t　':
            cur = [i, i]; paras.append(cur)
        else:
            cur[1] = i
    out = {'장': tag, '장면': n, '행': f'{lo}~{hi}', '단락 수': len(paras),
           '단락': [{'단락': k, '행': f'{a}-{b}', '원문': '\n'.join(SRC[a - 1:b])} for k, (a, b) in enumerate(paras, 1)]}
    json.dump(out, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'{tag} 장면 {n} ({lo}~{hi}): 단락 {len(paras)} → {p}')

elif mode == '줄':
    if g is None or not (g == '표기' or (g.isdigit() and 1 <= int(g) <= 11)):
        print('넷째 인자로 갈래(1~11 또는 "표기")를 줌'); sys.exit(1)
    screen_only(); facts_done()
    B = []                                   # 찍을 덩이(기준, 줄 하나와 그 근거 원문, 끝의 목록). 쪽은 덩이 사이에서 나눔
    def blk(): B.append([])
    def out(x=''): B[-1].append(x)
    K = open(os.path.join(D, '원작 정리본 기준.md'), encoding='utf-8').read().split('\n')
    def sect(start, stop):
        a = next(i for i, l in enumerate(K) if start(l))
        b = next((i for i in range(a + 1, len(K)) if stop(K[i])), len(K))
        return '\n'.join(K[a:b]).rstrip()
    common = sect(lambda l: l.startswith('## 공통 기준'), lambda l: l.startswith('## '))
    if g == '표기':
        own = sect(lambda l: l.startswith('## 별도 절차'), lambda l: l.startswith('- 중간점검'))
    else:
        own = sect(lambda l: re.match(rf'^{g}\. ', l), lambda l: re.match(r'^\d+\. ', l) or l.startswith('#'))
    blk(); out(common); out(); blk(); out(own); out()
    files = [D + '/표기와 원문 문제.md'] if g == '표기' else [f for f in glob.glob(D + '/*.md') if os.path.basename(f).split('_')[0] == g]
    cit = re.compile(r'(?<![\d-])(\d)-(\d{1,2})\(([^)]*)\)')
    src = {'1': 'eun01_1.txt', '2': 'eun02.txt', '3': 'eun03.txt', '4': 'eun04.txt'}[tag.split('-')[0]]
    SRC = open(os.path.join(T, '..', '원문', src), encoding='utf-8').read().split('\n')
    rows, others, allrows = [], [], []
    for f in files:
        for i, l in enumerate(open(f, encoding='utf-8'), 1):
            if not l.startswith('| ') or l.startswith('|---'):
                continue
            sp, chap = [], False
            for m in cit.finditer(l):
                if f'{m.group(1)}-{m.group(2)}' != tag:
                    continue
                chap = True
                for part in m.group(3).split(','):
                    nums = re.findall(r'\d+', part)
                    if nums and int(nums[0]) <= hi and int(nums[-1]) >= lo:
                        sp.append((max(int(nums[0]), lo), min(int(nums[-1]), hi)))
            key = f'{os.path.basename(f)}:{i}'
            c = [x.strip() for x in l.rstrip().split('|')[1:-1]]
            allrows.append((key, c[:2], chap, l.rstrip('\n')))
            if sp:
                rows.append({'줄': key, '원래 줄': l.rstrip('\n'), '근거 행': sp})
    if g != '표기':
        want = {tuple(c) for k, c, chap, l in allrows if any(r['줄'] == k for r in rows)}
        others = [{'줄': k, '원래 줄': l} for k, c, chap, l in allrows if tuple(c) in want and not chap]
    prev = None
    for r in rows:
        blk(); out(r['줄'] + ' ' + r['원래 줄'])
        if r['근거 행'] == prev:
            out('    (근거 원문은 위와 같음)')
        else:
            for a, b in r['근거 행']:
                for j in range(a, b + 1):
                    out(f'    {j}: {SRC[j - 1]}')
        prev = r['근거 행']
    if others:
        blk(); out(); out('같은 대상·같은 항목인데 이 장 근거가 없는 줄')
        grp = {}
        for r in others:
            c = [x.strip() for x in r['원래 줄'].split('|')[1:3]]
            grp.setdefault(tuple(c), []).append(r)
        for c, rs in grp.items():      # 한 묶음이 15줄을 넘으면 화면에는 수만 찍음(전부는 결과 파일의 "같은 대상·같은 항목"에 있음)
            if len(rs) > 15:
                out(f'({c[0]} | {c[1]}: {len(rs)}줄. 결과 파일에 있음)')
            else:
                for r in rs: out(r['줄'] + ' ' + r['원래 줄'])
    for r in rows: r.pop('근거 행')
    res_ = {'장': tag, '장면': n, '갈래': g, '행': f'{lo}~{hi}', '기준': common + '\n\n' + own, '줄 수': len(rows), '목록': rows, '같은 대상·같은 항목': others}
    json.dump(res_, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    ksig = hashlib.sha1('\n'.join(K).encode('utf-8')).hexdigest()
    msg = show(g, paginate(B), ksig, [r['줄'] for r in rows])
    print(f'{tag} 장면 {n} ({lo}~{hi}) 갈래 {g}: 정리본 줄 {len(rows)} → {p}. ' + msg)

elif mode == '기준':
    page = int(g) if g else 1
    screen_only(); facts_done()
    K = open(os.path.join(D, '원작 정리본 기준.md'), encoding='utf-8').read().split('\n')
    B, cur = [], []
    for l in K:                      # 덩이는 제목(##, ###)과 갈래 번호 줄에서 나눔
        if (l.startswith('#') or re.match(r'^\d+\. ', l)) and cur:
            B.append(cur); cur = []
        cur.append(l)
    if cur: B.append(cur)
    ksig = hashlib.sha1('\n'.join(K).encode('utf-8')).hexdigest()
    msg = show('기준', paginate(B), ksig, [])
    print(f'{tag} 장면 {n}: 원작 정리본 기준.md 전체. ' + msg)

else:
    print('셋째 인자는 "단락", "줄", "기준"'); sys.exit(1)
