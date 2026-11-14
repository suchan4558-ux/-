#!/usr/bin/env python3
# 사용: python3 뽑기.py 1-3 2 단락 → 1권 3장의 2번째 장면(장면.json 차례) 원문을 단락으로 나눠
#                                  결과/1-3_2_단락.json에 적음(공백으로 시작하는 줄에서 새 단락, 빈 줄에서 단락 끝)
#       python3 뽑기.py 1-3 2 공통 → 원작 정리본 기준.md의 공통 기준을 화면에 찍음(장면마다 줄 판정을 시작할 때 한 번).
#       python3 뽑기.py 1-3 2 줄 7 [쪽] → 그 장면 행이 근거에 든 정리본 줄 가운데 갈래 7(7_….md)의 줄만
#                                  결과/1-3_2_줄_7.json에 적음. 갈래는 1~11 또는 "표기"(표기와 원문 문제.md).
#                                  갈래를 주지 않으면 돌리지 않음(갈래마다 그 갈래의 기준을 편 뒤 그 갈래만 봄).
#                                  1쪽 앞에 그 갈래의 기준(표기는 별도 절차)을 화면에 찍고, 결과 파일에도 "기준"으로 넣음.
#                                  줄마다 그 줄의 이 장면 근거 원문을 함께 찍음(같은 쪽에서 이미 찍은 행은 "(위에 찍음)").
#                                  한 번에 2만 자쯤만 찍고 끝 줄에 "쪽 1/3 (다음: 쪽 2)"처럼 알림. 다음 쪽은 다섯째 인자로 줌.
#                                  같은 대상·같은 항목인데 이 장 근거가 없는 줄은 화면에 찍지 않고 수만 알리며 결과 파일에 넣음.
#                                  출력을 버리거나(/dev/null) 파일로 돌리면 돌지 않음.
#       python3 뽑기.py 1-3 2 찾기 낱말 [항목] → 대상 칸에 낱말이 든 정리본 줄(모든 갈래)을 찍음(남는 사실을 처리할 때).
# 사실을 뽑는 동안에는 "줄"을 돌리지 않음.
# 검사.py는 이 파일을 읽지 않고 같은 규칙으로 장면의 줄 전체를 직접 셈.
import re, sys, glob, os, json
T = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(T, '..', '정리본')
tag, n, mode = sys.argv[1], int(sys.argv[2]), sys.argv[3]
g = sys.argv[4] if len(sys.argv) > 4 else None
scenes = json.load(open(os.path.join(T, '장면.json'), encoding='utf-8'))
lo, hi = map(int, scenes[tag][n - 1].split('~'))
os.makedirs(os.path.join(T, '결과'), exist_ok=True)
p = os.path.join(T, '결과', f'{tag}_{n}_줄_{g}.json' if mode == '줄' else f'{tag}_{n}_{mode}.json')

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

elif mode == '공통':
    import stat
    st = os.fstat(1)
    if stat.S_ISREG(st.st_mode) or (stat.S_ISCHR(st.st_mode) and st.st_rdev == os.stat('/dev/null').st_rdev):
        print('출력을 버리거나 파일로 돌리면 돌지 않음(기준을 화면에 찍어야 함)', file=sys.stderr); sys.exit(1)
    K = open(os.path.join(D, '원작 정리본 기준.md'), encoding='utf-8').read().split('\n')
    a = next(i for i, l in enumerate(K) if l.startswith('## 공통 기준'))
    b = next(i for i in range(a + 1, len(K)) if K[i].startswith('## '))
    print('\n'.join(K[a:b]).rstrip())

elif mode == '줄':
    if g is None or not (g == '표기' or (g.isdigit() and 1 <= int(g) <= 11)):
        print('넷째 인자로 갈래(1~11 또는 "표기")를 줌'); sys.exit(1)
    page = int(sys.argv[5]) if len(sys.argv) > 5 else 1
    import stat
    st = os.fstat(1)
    if stat.S_ISREG(st.st_mode) or (stat.S_ISCHR(st.st_mode) and st.st_rdev == os.stat('/dev/null').st_rdev):
        print('출력을 버리거나 파일로 돌리면 돌지 않음(기준과 줄을 화면에 찍어야 함)', file=sys.stderr); sys.exit(1)
    K = open(os.path.join(D, '원작 정리본 기준.md'), encoding='utf-8').read().split('\n')
    def sect(start, stop):
        a = next(i for i, l in enumerate(K) if start(l))
        b = next((i for i in range(a + 1, len(K)) if stop(K[i])), len(K))
        return '\n'.join(K[a:b]).rstrip()
    if g == '표기':
        own = sect(lambda l: l.startswith('## 별도 절차'), lambda l: l.startswith('- 중간점검'))
    else:
        own = sect(lambda l: re.match(rf'^{g}\. ', l), lambda l: re.match(r'^\d+\. ', l) or l.startswith('#'))
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
    # 쪽 나누기: 한 쪽에 찍을 글자가 PAGE를 넘지 않게 줄을 차례로 담음(1쪽에는 갈래 기준이 함께 들어감).
    # 한 쪽 안에서 이미 찍은 원문 행은 다시 찍지 않고 "(위에 찍음)"으로 가리킴.
    PAGE = 20000
    pages, cur, size, seen = [], [], len(own), set()
    for r in rows:
        need = [j for a, b in r['근거 행'] for j in range(a, b + 1)]
        add = len(r['줄']) + len(r['원래 줄']) + 2 + sum(len(SRC[j - 1]) + 12 for j in need if j not in seen)
        if cur and size + add > PAGE:
            pages.append(cur); cur, size, seen = [], 0, set()
            add = len(r['줄']) + len(r['원래 줄']) + 2 + sum(len(SRC[j - 1]) + 12 for j in need)
        cur.append(r); size += add; seen.update(need)
    pages.append(cur)
    if not 1 <= page <= len(pages):
        print(f'쪽은 1~{len(pages)}'); sys.exit(1)
    if page == 1:
        print(own); print()
    seen = set()
    for r in pages[page - 1]:
        print(r['줄'], r['원래 줄'])
        for a, b in r['근거 행']:
            old = [j for j in range(a, b + 1) if j in seen]
            if old: print(f'    (위에 찍음: {old[0]}' + (f'-{old[-1]}' if len(old) > 1 else '') + ')')
            for j in range(a, b + 1):
                if j not in seen: print(f'    {j}: {SRC[j - 1]}'); seen.add(j)
    for r in rows: r.pop('근거 행')
    out = {'장': tag, '장면': n, '갈래': g, '행': f'{lo}~{hi}', '기준': own, '줄 수': len(rows), '쪽 수': len(pages), '목록': rows, '같은 대상·같은 항목': others}
    json.dump(out, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'{tag} 장면 {n} ({lo}~{hi}) 갈래 {g}: 정리본 줄 {len(rows)}, 쪽 {page}/{len(pages)}'
          + (f' (다음: 쪽 {page + 1})' if page < len(pages) else ' (끝)')
          + f', 같은 대상·같은 항목인데 이 장 근거가 없는 줄 {len(others)}(화면에 찍지 않음) → {p}')

elif mode == '찾기':
    # 남는 사실을 처리할 때: 대상 칸에 낱말이 든 정리본 줄(모든 갈래)을 찍음. 항목을 주면 그 항목만.
    word, item = g, (sys.argv[5] if len(sys.argv) > 5 else None)
    if not word: print('넷째 인자로 대상에 든 낱말을 줌(다섯째는 항목)'); sys.exit(1)
    k = 0
    for f in sorted(glob.glob(D + '/*.md')):
        if not re.match(r'\d+_', os.path.basename(f)): continue
        for i, l in enumerate(open(f, encoding='utf-8'), 1):
            if not l.startswith('| ') or l.startswith('|---'): continue
            c = [x.strip() for x in l.rstrip().split('|')[1:-1]]
            if len(c) >= 2 and word in c[0] and (item is None or c[1] == item):
                print(f'{os.path.basename(f)}:{i}', l.rstrip('\n')); k += 1
    print(f'대상에 "{word}"가 든 줄' + (f'(항목 {item})' if item else '') + f': {k}')

else:
    print('셋째 인자는 "단락", "공통", "줄", "찾기"'); sys.exit(1)
