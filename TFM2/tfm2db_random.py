#!/usr/bin/env python3
"""TFM2 데이터베이스(.tfm2db) 랜덤 도구 — 총정리 5-3 규칙 5~7

사용법:  python tfm2db_random.py 입력.tfm2db 출력.tfm2db [--seed 숫자]

- 에고: 0~100
- 공격성: 탑 70~100 / 정글 60~90 / 미드 40~80 / 원딜 30~80 / 서폿 50~90
- 챔피언 숙련도: 주 역할군 60~100, 나머지 20~80 (저장값은 ×10)
  주 역할군 (태그 기준 매칭, 총정리 5-3):
    탑   Bruiser (늑대인간·악마·테일 제외) 22
    정글 Assassin + 늑대인간·악마·테일 + Tank(1코어 예외 아님) 17
    미드 Mage (1코어 예외 아님) 16
    원딜 ADC 16
    서폿 Support + Mage·Tank 1코어 예외 21
- 선수 포지션은 가장 높은 포지션 값으로 판단 (규칙 3 적용된 기본 파일 기준)
- 그 외 바이트는 그대로. 값은 정수 균등분포
"""
import sys, re, struct, zlib, gzip, time, random, argparse

AGGR = [(70, 100), (60, 90), (40, 80), (30, 80), (50, 90)]   # 탑 정글 미드 원딜 서폿
EGO = (0, 100)
PROF_MAIN = (60, 100)
PROF_SUB = (20, 80)
POS_MAIN = {'archer': 3, 'gambler': 3, 'poison_dart_hunter': 3, 'dancer': 3, 'boomerang_hunter': 3, 'crossbowman': 3, 'soldier': 3, 'harpooner': 3, 'whip_master': 3, 'gunner': 3, 'bombardier': 3, 'bomber': 3, 'longear': 3, 'witness': 3, 'harpy': 3, 'hellion': 3, 'circus_blade': 1, 'clown': 1, 'ninja': 1, 'nightmare': 1, 'hunter': 1, 'ghost': 1, 'inquisitor': 1, 'hitman': 1, 'nullifier': 1, 'shadowmancer': 2, 'necromancer': 2, 'druid': 2, 'magic_knight': 2, 'sand_mage': 2, 'white_mage': 2, 'lightning_mage': 2, 'ice_mage': 2, 'astrologer': 2, 'pyromancer': 2, 'dark_mage': 2, 'vampire': 2, 'voidling': 2, 'ghostrabbit': 2, 'cf_sun_mage': 2, 'planemage': 2, 'taoist': 4, 'wind_mage': 4, 'voodoo_shaman': 4, 'alchemist': 4, 'hypnotist': 4, 'illusionist': 4, 'esper': 4, 'knight': 1, 'shield_bearer': 1, 'android': 1, 'ogre': 1, 'construct': 1, 'monk': 4, 'exorcist': 4, 'plague_doctor': 4, 'chef': 4, 'jiangshi': 0, 'swordman': 0, 'gladiator': 0, 'fighter': 0, 'siege_breaker': 0, 'berserker': 0, 'strongman': 0, 'cavalry_knight': 0, 'werewolf': 1, 'dokkaebi': 0, 'dual_blader': 0, 'pole_warrior': 0, 'spellbreaker': 0, 'demon': 1, 'prisoner': 0, 'hammerer': 0, 'lancer': 0, 'executioner': 0, 'squirrel': 0, 'beastman': 0, 'amazon': 0, 'candygel': 0, 'tale': 1, 'fireblade': 0, 'panda': 0, 'barrier_magician': 4, 'pythoness': 4, 'ferryman': 4, 'priest': 4, 'guardian_spirit': 4, 'bard': 4, 'enchanter': 4, 'spirit_caller': 4, 'mistguide': 4, 'oni': 4}   # 챔피언 id -> 주 역할군 포지션 (0 탑, 1 정글, 2 미드, 3 원딜, 4 서폿)

STAT_RE = re.compile(rb'(?=([\x00-\x0a])\x00{7}((?:[\x01-\x78]\x00{7}){10}))')
ENT_RE = re.compile(rb'([\x03-\x18])\x00{7}([a-z_]{3,24})\x00{8}(..)(..)', re.S)

def read_db(path):
    raw = open(path, 'rb').read()
    if raw[:4] != b'TFM2':
        sys.exit('TFM2 데이터베이스 파일이 아님')
    clen, crc = struct.unpack('<QI', raw[13:25])
    comp = raw[25:]
    if len(comp) != clen or zlib.crc32(comp) != crc:
        sys.exit('헤더 길이/CRC가 맞지 않음')
    return raw[:5], zlib.decompressobj(31).decompress(comp)

def write_db(path, head5, body):
    comp = gzip.compress(bytes(body), compresslevel=6)
    hdr = head5 + struct.pack('<QQI', int(time.time() * 1000), len(comp), zlib.crc32(comp))
    open(path, 'wb').write(hdr + comp)

def find_records(b):
    """(offset, name, tag) — tag 1 = 선수, 0 = 코치/스태프"""
    recs = []
    for m in STAT_RE.finditer(b):
        p = m.start()
        for L in range(1, 31):
            s = p - L; lp = s - 8
            if lp < 0: break
            if b[lp] == L and b[lp + 1:lp + 8] == b'\x00' * 7:
                try: nm = b[s:p].decode('utf-8')
                except UnicodeDecodeError: continue
                if nm.isprintable() and nm.strip():
                    recs.append((p, nm, m.group(1)[0])); break
    return recs

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('src'); ap.add_argument('dst'); ap.add_argument('--seed', type=int)
    a = ap.parse_args()
    seed = a.seed if a.seed is not None else int(time.time())
    rnd = random.Random(seed)
    head5, body = read_db(a.src)
    b = bytearray(body)
    recs = find_records(body)
    athletes = [r for r in recs if r[2] == 1]
    starts = [r[0] for r in recs]
    n_prof = 0; unknown = set()
    for p, nm, _ in athletes:
        pos = list(struct.unpack('<5Q', body[p + 104:p + 144]))
        pi = pos.index(max(pos))
        struct.pack_into('<QQ', b, p + 88, rnd.randint(*AGGR[pi]), rnd.randint(*EGO))
        end = starts[starts.index(p) + 1] if starts.index(p) + 1 < len(starts) else p + 6000
        for m in ENT_RE.finditer(body, p, end):
            if m.group(1)[0] != len(m.group(2)): continue
            cid = m.group(2).decode()
            mp = POS_MAIN.get(cid)
            if mp is None:
                unknown.add(cid); continue
            lo, hi = PROF_MAIN if mp == pi else PROF_SUB
            struct.pack_into('<H', b, m.start(3), rnd.randint(lo, hi) * 10)
            n_prof += 1
    write_db(a.dst, head5, b)
    print('선수 %d명, 숙련도 %d개 변경, seed %d' % (len(athletes), n_prof, seed))
    if unknown:
        print('매칭 표에 없는 챔피언 (숙련도 안 바꿈):', ', '.join(sorted(unknown)))

if __name__ == '__main__':
    main()
