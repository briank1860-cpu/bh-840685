#!/usr/bin/env python3
"""SPOTS(장소 안 포인트) 위치 검사: 포인트가 육지(건물·도로·마을)에 찍혔는지 본다.
index.html 안의 OSMBASE 해안선(C, OSM 규칙상 진행 방향 왼쪽이 육지)·갯벌(W)·모래사장(B)·도로(R)로 판단한다.
사용:
  python3 tools/check_spots.py            검사만(문제 있는 포인트 출력, 있으면 종료 코드 1)
  python3 tools/check_spots.py --fix      육지에 찍힌 포인트를 가장 가까운 해안선 바다 쪽(갯벌)으로 옮겨 저장
  --osm 을 붙이면 해안선 자료가 없는 장소도 OpenStreetMap에서 받아 검사(서버가 느리면 오래 걸림)
'판단 불가'로 남은 포인트는 위성 지도로 직접 확인한다(설명과 맞는 바위·갯벌·물골 위인지).
새 포인트를 SPOTS에 넣은 뒤에는 꼭 돌린다."""
import json, math, os, re, sys

HERE = os.path.dirname(__file__)
HTML = os.path.join(HERE, '..', 'index.html')
ROCK = {'bakhaji', 'pippul', 'gul', 'haesam', 'jukkumi', 'nakji'}  # 바위·물가 대상은 해안선 가까이


def xy(la, lo, la0):  # 위경도 → 미터(좁은 범위 평면 근사)
    return (lo * 111320 * math.cos(math.radians(la0)), la * 110540)


def seg_near(p, a, b):
    ax, ay = a; bx, by = b; px, py = p
    dx, dy = bx - ax, by - ay
    L = dx * dx + dy * dy
    t = 0 if L == 0 else max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / L))
    fx, fy = ax + t * dx, ay + t * dy
    return math.hypot(px - fx, py - fy), (fx, fy), (dx, dy)


def inside(p, ring):
    x, y = p; c = False
    for i in range(len(ring)):
        x1, y1 = ring[i]; x2, y2 = ring[i - 1]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1 + 1e-12) + x1:
            c = not c
    return c


def load():
    h = open(HTML, encoding='utf-8').read()
    S = json.loads(re.search(r'^const SPOTS=(\{.*\});', h, re.M).group(1))
    O = json.loads(re.search(r'^const OSMBASE=(\{.*\});', h, re.M).group(1))
    return h, S, O


def classify(la, lo, O, ids):
    """반환: (상태, 해안선까지 m, 바다쪽 이동점)  상태: sea/flat/beach/land/road/unknown"""
    P = xy(la, lo, la)
    feats = [O['f'][f] for f in ids if f in O['f']]
    if USE_OSM and not any(x['k'] == 'C' for x in feats):
        feats += list(osm_coast(la, lo).values())
    for x in feats:
        if x['k'] == 'W' and any(inside(P, [xy(a, b, la) for a, b in r]) for r in x['g']):
            return 'flat', 0, None
    best = None
    for x in feats:
        if x['k'] != 'C':
            continue
        for line in x['g']:
            pts = [xy(a, b, la) for a, b in line]
            for i in range(len(pts) - 1):
                d, foot, v = seg_near(P, pts[i], pts[i + 1])
                if best is None or d < best[0]:
                    best = (d, foot, v, pts[i])
    road = any(x['k'].startswith('R') and any(seg_near(P, xy(*l[i], la), xy(*l[i + 1], la))[0] < 25
               for l in x['g'] for i in range(len(l) - 1)) for x in feats)
    beach = any(x['k'] == 'B' and any(inside(P, [xy(a, b, la) for a, b in r]) for r in x['g']) for x in feats)
    if best is None or best[0] > 5000:
        return ('road' if road else 'unknown'), None, None
    d, foot, (vx, vy), a = best
    cross = vx * (P[1] - a[1]) - vy * (P[0] - a[0])  # >0 이면 왼쪽 = 육지
    land = cross > 0
    n = math.hypot(vx, vy) or 1
    sea_dir = (vy / n, -vx / n)  # 진행 방향 오른쪽 = 바다
    st = 'road' if road else ('beach' if beach else ('land' if land else 'sea'))
    return st, round(d), (foot, sea_dir)


_OSM = {}
USE_OSM = '--osm' in sys.argv  # 앱 안 자료에 해안선이 없는 곳은 OSM에서 받아 검사(느림)


def osm_coast(la, lo):
    """앱 안 자료에 해안선이 없을 때 Overpass에서 주변 3km 해안선을 받아 OSMBASE 모양으로 돌려준다(안 되면 빈 값)."""
    key = (round(la, 2), round(lo, 2))
    if key in _OSM:
        return _OSM[key]
    import urllib.request, urllib.parse
    q = f'[out:json][timeout:60];way(around:3000,{la},{lo})[natural=coastline];out geom;'
    feats = {}
    err = None
    for url in ('https://overpass.kumi.systems/api/interpreter', 'https://overpass-api.de/api/interpreter', 'https://overpass.private.coffee/api/interpreter'):
        try:
            req = urllib.request.Request(url, data=urllib.parse.urlencode({'data': q}).encode(), headers={'User-Agent': 'GetbeolFriend/1.0'})
            d = json.load(urllib.request.urlopen(req, timeout=60))
            for e in d.get('elements', []):
                feats['o%d' % e['id']] = {'k': 'C', 'g': [[[g['lat'], g['lon']] for g in e['geometry']]]}
            err = None
            break
        except Exception as e:
            err = e
    if err:
        print('# 해안선 받기 실패', la, lo, err)
    _OSM[key] = feats
    return feats


def to_ll(x, y, la0):
    return (round(y / 110540, 5), round(x / (111320 * math.cos(math.radians(la0))), 5))


def main():
    fix = '--fix' in sys.argv
    h, S, O = load()
    bad, moved, unk = [], 0, 0
    for sid, pts in S.items():
        ids = O['n'].get(sid, [])
        for p in pts:
            st, d, mv = classify(p['la'], p['lo'], O, ids)
            if st in ('land', 'road'):
                bad.append((sid, p['t'], p['la'], p['lo'], st, d, p['d'][:30]))
                if fix and mv:
                    (fx, fy), (sx, sy) = mv
                    off = 60 if set(p['t']) & ROCK else 150
                    nla, nlo = to_ll(fx + sx * off, fy + sy * off, p['la'])
                    if classify(nla, nlo, O, ids)[0] in ('sea', 'flat', 'beach'):
                        p['la'], p['lo'] = nla, nlo
                        p['p'] = '대략'
                        moved += 1
            elif st == 'unknown':
                unk += 1
            elif st == 'sea' and d is not None and d > 3000:
                bad.append((sid, p['t'], p['la'], p['lo'], '바다 너무 멀리', d, p['d'][:30]))
    for b in bad:
        print(*b, sep='\t')
    print('포인트', sum(len(v) for v in S.values()), '/ 문제', len(bad), '/ 옮김', moved, '/ 판단 불가(해안선 자료 없음)', unk)
    if fix and moved:
        dump = 'const SPOTS=' + json.dumps(S, ensure_ascii=False, separators=(',', ':')).replace('</', r'<\/') + ';'
        m = re.search(r'^const SPOTS=(\{.*\});', h, re.M)
        h = h[:m.start()] + dump + h[m.end():]
        open(HTML, 'w', encoding='utf-8', newline='').write(h)
    sys.exit(1 if bad and not fix else 0)


if __name__ == '__main__':
    main()
