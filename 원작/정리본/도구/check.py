# 정리본 줄 검사. 기준의 '적을 것'과 공통 기준 가운데 기계로 볼 수 있는 것만 검사함.
# 쓰는 법
#   python3 check.py rows 파일 [사실|바탕] < 줄들   : 넣기 전의 줄 검사(add.py가 부름)
#   python3 check.py diff [파일...]                 : HEAD에 없던 새 줄만 검사(훅이 부름)
#   python3 check.py diff --commit                 : 위에 더해, 새 줄의 장마다 검수 기록이 있는지 봄
#   python3 check.py all [파일...]                  : 파일 전체 검사(이미 쓴 줄 정리용)
#   python3 check.py fingerprint 권-장              : 그 장 줄들의 지문(검수 기록에 적음)
#   python3 check.py geomsu 권-장                   : 검수 기록이 통과로 인정되는지 확인
# 오류: 기준을 어긴 것. 경고: 어겼을 수 있으니 기준과 대조해 볼 것.
import re, sys, os, glob, subprocess, collections

TOOL = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(TOOL)                       # 원작/정리본
PYOGI = os.path.join(ROOT, '표기와 원문 문제.md')
GEOMSU = os.path.join(TOOL, '검수')

ITEMS = {
 '1사실': ['세력','계급','작위','보직','가진 것','출신','이력','관계','평판','생김새와 몸','기호와 습관'],
 '1바탕': ['성격','감정 반응','말투와 말버릇','가치관','바라는 것','판단','사람을 대하는 태도','전략과 전술 성향','능력'],
 '2': ['소속','사람과 자리','규모','기반','관계','평판','목표','민심'],
 '3': ['소속','지형','이어진 곳','시설','겉모습','주둔','인구와 주민','경제','관계','평판'],
 '4': ['정해진 것','평판'],
 '5': ['소속','겉모습','성능','역할','평판'],
 '6': ['내용','인용','따르는 쪽','평판'],
 '7': ['경과','남긴 것','평판'],
 '8': ['하는 법','조건','강약','평판'],
 '9': ['걸린 시간'],
 '10': ['사례'],
 '11': ['수'],
}
SERYEOK = {'제국', '동맹', '페잔', '그 밖의 세력'}
JAKWI = ['공작', '후작', '백작', '자작', '남작', '제국 기사']
GEUNGEO = re.compile(r'\d+-\d+\(\d+(-\d+)?(, \d+(-\d+)?)*\)(, \d+-\d+\(\d+(-\d+)?(, \d+(-\d+)?)*\))*')

def cells(line):
    return [c.strip() for c in line.strip().strip('|').split('|')]

def is_row(line):
    return line.startswith('|') and not line.startswith('|--') and not re.match(r'\|\s*(대상|인물|번역본 표기)\s*\|', line)

def gallae(path):
    return os.path.basename(path).split('_')[0]

TITLE = {'공작','후작','백작','자작','남작','제독','원수','대장','중장','소장','준장','대령','중령','소령','대위','중위','소위','왕조','황제','경','부인','양','함장','사령관'}
QUOTE = re.compile(r'"[^"]*"|“[^”]*”|「[^」]*」|\'[^\']*\'|‘[^’]*’')

def load_pyogi():
    """인물 기준 표기 모음과, 쓰면 안 되는 번역본 표기 → 기준 표기."""
    names, wrong, sec = set(), {}, None
    for l in open(PYOGI, encoding='utf-8'):
        if l.startswith('### '): sec = l[4:].strip()
        if not is_row(l): continue
        c = cells(l)
        if len(c) < 2: continue
        bon, gi = c[0], c[1]
        if sec == '인물': names.add(gi)
        if sec in ('인물', '지명', '그 밖의 이름'):
            for alt in bon.split(' / '):
                alt = re.sub(r'\(.*?\)', '', alt).strip()
                if len(alt) >= 2 and alt != gi and alt not in gi:
                    wrong.setdefault(alt, gi)
    # 기준 이름에 직함만 붙은 꼴(예: "브라운슈바이크 공작")은 틀린 표기가 아님
    toks = set()
    for l in open(PYOGI, encoding='utf-8'):
        if is_row(l) and len(cells(l)) > 1: toks |= set(cells(l)[1].split())
    wrong = {a: g for a, g in wrong.items() if not all(t in toks or t in TITLE for t in a.split())}
    return names, wrong

def year_of(s):
    m = re.search(r'\d+', s)
    return int(m.group()) if m else None

def check_row(g, table, c, names, wrong):
    """한 줄 검사 → (오류들, 경고들)"""
    E, W = [], []
    if len(c) != 5:
        return [f'칸이 {len(c)}개임(5개여야 함)'], W
    dae, hang, si, nae, gn = c
    for nm, v in (('대상', dae), ('항목', hang), ('시점', si), ('내용', nae), ('근거', gn)):
        if not v: E.append(f'{nm} 칸이 비었음')
    if gn and not GEUNGEO.fullmatch(gn):
        E.append(f'근거 꼴이 "권-장(행)"이 아님: {gn}')
    for a, b in re.findall(r'(\d+)-(\d+)(?=[,)])', gn):
        if int(b) - int(a) + 1 > 30:
            W.append(f'근거 범위 {a}-{b}가 30줄을 넘음. 그 내용이 있는 행만 가리키도록 좁힐 수 있는지 볼 것')
    key = '1' + (table or '') if g == '1' else g
    if key not in ITEMS:
        E.append('인물 파일인데 사실 표인지 바탕 표인지 모름'); return E, W
    if hang and hang not in ITEMS[key]:
        E.append(f'항목 "{hang}"은 기준 적을 것에 없음. 쓸 수 있는 것: {", ".join(ITEMS[key])}')
    for alt, gi in wrong.items():
        txt = dae + ' ' + QUOTE.sub('', nae)   # 따옴표 안 인용은 원문대로 둠
        if alt in txt and gi not in txt:
            E.append(f'번역본 표기 "{alt}"를 씀. 기준 표기는 "{gi}"')
    if g == '1':
        if dae and dae not in names:
            E.append(f'인물 "{dae}"이 표기와 원문 문제.md 인물 표의 기준 표기에 없음(새 인물이면 표기표에 먼저 넣음)')
        if table == '사실':
            if hang == '세력' and nae not in SERYEOK:
                E.append(f'세력은 제국, 동맹, 페잔, 그 밖의 세력 가운데 하나만 적음(괄호나 덧붙임 없이): "{nae}"')
            if hang == '계급':
                for j in JAKWI:
                    if j in nae: E.append(f'계급 칸에 작위 "{j}"가 들어감. 작위는 작위 항목에 적음')
            if hang == '이력':
                y = year_of(si)
                ok = ('아스타테' in si and '전' in si) or (y is not None and (y < 796 or (y == 796 and '전' in si and '797' not in si)))
                if not ok: E.append(f'이력은 아스타테 회전 이전 것만 적음. 시점 "{si}"')
            if hang == '보직' and (len(nae) > 40 or '. ' in nae):
                W.append('보직 내용이 길거나 문장이 여럿임. 보직·처지만 적었는지, 경위를 넣지 않았는지 볼 것')
            elif len(nae) > 80 or nae.count('. ') >= 2:
                W.append('내용이 길거나 문장이 여럿임. 한 줄에 한 가지만 적었는지 볼 것')
        if table == '바탕':
            if '→' not in nae:
                E.append('바탕 장면에 "→"가 없음. "상황 → 행동이나 말"로 적음(형용사 요약 금지)')
            elif nae.count('→') > 1:
                W.append('"→"가 둘 이상임. 장면 하나만 적었는지 볼 것')
    return E, W

def parse(path, text=None):
    """(줄번호, 원문, 권, 표, 칸들) 목록"""
    out, gwon, table = [], None, None
    lines = (text if text is not None else open(path, encoding='utf-8').read()).split('\n')
    for i, l in enumerate(lines, 1):
        m = re.match(r'## (\d+)권', l)
        if m: gwon, table = m.group(1), None
        if l.startswith('### 사실'): table = '사실'
        if l.startswith('### 바탕'): table = '바탕'
        if is_row(l): out.append((i, l, gwon, table, cells(l)))
    return out

def gwon_jang(gn):
    m = re.match(r'(\d+)-(\d+)', gn)
    return (m.group(1), m.group(2)) if m else (None, None)

def dupkey(g, gwon, table, c):
    return (gwon or gwon_jang(c[-1])[0], table, c[0], c[1], c[3])

def report(path, ln, line, E, W):
    rel = os.path.relpath(path, ROOT)
    for e in E: print(f'[오류] {rel}:{ln} {e}\n    {line[:150]}')
    for w in W: print(f'[경고] {rel}:{ln} {w}\n    {line[:150]}')

def galle_files(args):
    fs = [f for f in args if not f.startswith('--')] or sorted(glob.glob(os.path.join(ROOT, '[0-9]*_*.md')))
    return [os.path.abspath(f) for f in fs if re.match(r'\d+_', os.path.basename(f))]

def head_text(path):
    rel = os.path.relpath(path, subprocess.check_output(['git', 'rev-parse', '--show-toplevel'], cwd=ROOT, text=True).strip())
    r = subprocess.run(['git', 'show', 'HEAD:' + rel], cwd=ROOT, capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else ''

import hashlib
GIJUN = os.path.join(ROOT, '원작 정리본 기준.md')

def chapter_rows(gj):
    """근거의 첫 장이 gj인 줄 전부(모든 갈래)"""
    out = []
    for path in galle_files([]):
        for ln, l, gw, t, c in parse(path):
            if len(c) == 5 and '-'.join(gwon_jang(c[-1])) == gj:
                out.append(os.path.basename(path) + '\t' + l.strip())
    return sorted(out)

def fingerprint(gj):
    return hashlib.sha256('\n'.join(chapter_rows(gj)).encode()).hexdigest()[:16]

GOCHIM = os.path.join(TOOL, '고침')

def geomsu_status(gj):
    """검수 기록 확인 → (통과인지, 문제들)
    통과: 검수 기록이 "결과: 통과"이고 지문이 맞음.
    또는 검수가 한 번 끝난 뒤 고침 기록(도구/고침/권-장.md)이 있고, 지적 수와 고침 줄 수가 같으며, 고침 기록의 지문이 지금 줄과 맞음."""
    p = os.path.join(GEOMSU, gj + '.md')
    if not os.path.exists(p): return False, [f'검수 기록 도구/검수/{gj}.md가 없음']
    txt = open(p, encoding='utf-8').read(); P = []
    m = re.search(r'^지문: ([0-9a-f]+)', txt, re.M)
    if not m: P.append('기록에 "지문:" 줄이 없음')
    gj_txt = re.sub(r'\s+', ' ', open(GIJUN, encoding='utf-8').read())
    for q in re.findall(r'기준: "([^"]+)"', txt):
        if re.sub(r'\s+', ' ', q).strip() not in gj_txt: P.append(f'기준 인용이 기준 파일에 없음: "{q[:60]}"')
    n_items = 0
    for sec in ('어긋난 줄', '빠진 것', '기준 질문'):
        b = re.search(rf'^## {sec}\n(.*?)(?=^## |^결과:|\Z)', txt, re.M | re.S)
        if b is None: P.append(f'"## {sec}" 절이 없음'); continue
        k = len(re.findall(r'^- ', b.group(1), re.M)); n_items += k
        if k and '결과: 통과' in txt: P.append(f'"{sec}"에 남은 것이 있는데 통과로 적음')
    if P: return False, P
    fp = fingerprint(gj)
    if re.search(r'^결과: 통과\s*$', txt, re.M):
        if m.group(1) != fp: return False, ['검수한 뒤에 그 장의 줄이 바뀌었음(지문 불일치). 고친 것을 고침 기록에 적음']
        return True, []
    # 검수에서 고칠 것이 나온 경우: 고침 기록으로 끝냄(다시 검수하지 않음)
    g = os.path.join(GOCHIM, gj + '.md')
    if not os.path.exists(g): return False, [f'검수에서 고칠 것 {n_items}개가 나왔는데 고침 기록 도구/고침/{gj}.md가 없음']
    gt = open(g, encoding='utf-8').read()
    gm = re.search(r'^지문: ([0-9a-f]+)', gt, re.M)
    n_fix = len(re.findall(r'^- ', gt, re.M))
    if not gm: P.append('고침 기록에 "지문:" 줄이 없음')
    elif gm.group(1) != fp: P.append('고침 기록을 적은 뒤에 그 장의 줄이 바뀌었음(지문 불일치). 고침 기록을 다시 적음')
    if n_fix != n_items: P.append(f'검수 지적은 {n_items}개인데 고침 기록은 {n_fix}줄임. 지적마다 한 줄씩 적음')
    return not P, P

def unpassed_chapters():
    """HEAD에 없던 새 줄이 있는데 검수 기록에 "결과: 통과"가 없는 장들"""
    out = set()
    for path in galle_files([]):
        old = set(head_text(path).split('\n'))
        for ln, l, gw, t, c in parse(path):
            if l in old or len(c) != 5: continue
            g2, j = gwon_jang(c[-1])
            if g2: out.add(f'{g2}-{j}')
    return {gj for gj in out if not geomsu_status(gj)[0]}

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else 'diff'
    if mode == 'fingerprint':
        gj = sys.argv[2]; print(f'지문: {fingerprint(gj)}  (줄 {len(chapter_rows(gj))}개)'); return
    if mode == 'geomsu':
        ok, P = geomsu_status(sys.argv[2])
        for x in P: print('[문제]', x)
        print('통과' if ok else '통과 아님'); sys.exit(0 if ok else 1)
    names, wrong = load_pyogi()
    nerr = 0
    if mode == 'rows':
        path, table = os.path.abspath(sys.argv[2]), (sys.argv[3] if len(sys.argv) > 3 else None)
        g = gallae(path)
        existing = parse(path)
        seen = {dupkey(g, gw, t, c) for _, _, gw, t, c in existing if len(c) == 5}
        gwon_now = max((gw for _, _, gw, _, _ in existing if gw), default=None, key=int)
        for k, l in enumerate([l.rstrip('\n') for l in sys.stdin if l.strip()], 1):
            c = cells(l)
            E, W = check_row(g, table, c, names, wrong)
            if len(c) == 5:
                dk = dupkey(g, gwon_now, table, c)
                if dk in seen: E.append('그 권에 같은 대상·항목·내용 줄이 이미 있음. 새 줄 대신 기존 줄에 근거만 덧붙임')
                seen.add(dk)
            report(path, f'넣을 줄 {k}', l, E, W); nerr += len(E)
    else:
        files = galle_files(sys.argv[2:])
        need = set()
        for path in files:
            g = gallae(path)
            rows = parse(path)
            old = set(head_text(path).split('\n')) if mode == 'diff' else set()
            cnt = collections.Counter(dupkey(g, gw, t, c) for _, _, gw, t, c in rows if len(c) == 5)
            for ln, l, gw, t, c in rows:
                if mode == 'diff' and l in old: continue
                E, W = check_row(g, t, c, names, wrong)
                if len(c) == 5 and cnt[dupkey(g, gw, t, c)] > 1:
                    E.append('그 권에 같은 대상·항목·내용 줄이 또 있음. 한 줄로 합치고 근거를 덧붙임')
                report(path, ln, l, E, W); nerr += len(E)
                if len(c) == 5:
                    gw2, jang = gwon_jang(c[-1])
                    if gw2: need.add(f'{gw2}-{jang}')
        if '--commit' in sys.argv:
            for gj in sorted(need):
                ok, P = geomsu_status(gj)
                for x in P:
                    print(f'[오류] {gj}장 검수: {x}. 도구/검수_지시.md대로 검수를 받음'); nerr += 1
    print(f'오류 {nerr}개')
    sys.exit(1 if nerr else 0)

if __name__ == '__main__':
    main()
