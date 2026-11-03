#!/usr/bin/env python3
"""해루질 글 검색(최신순) — 여러 곳을 한 번에.
사용: python3 tools/search.py [경로,경로...|all] 검색어 [검색어...]
경로: daum_blog, daum_cafe, naver_blog, naver_cafe, youtube  (all = 전부)
출력: 줄마다 '경로<TAB>언제<TAB>제목<TAB>URL<TAB>요약'
인스타·X·틱톡은 로그인 없이 검색이 막혀 있어 넣지 않음(유튜브 쇼츠는 youtube에 포함)."""
import html, json, re, sys, time, urllib.parse, urllib.request

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36'
DATE = re.compile(r'(\d+\s*(?:분|시간|일|주|개월)\s*전|어제|\d{4}\.\s?\d{1,2}\.\s?\d{1,2}\.?)')


def get(url):
    req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept-Language': 'ko-KR,ko'})
    return urllib.request.urlopen(req, timeout=30).read().decode('utf-8', 'replace')


def clean(s):
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', s))).strip()


def daum(col, q):
    s = get('https://search.daum.net/search?w=fusion&sort=recency&col=%s&q=%s' % (col, urllib.parse.quote(q)))
    out = []
    for c in re.findall(r'<c-card[^>]*>(.*?)</c-card>', s, re.S):
        t = re.search(r'<c-title[^>]*data-href="([^"]+)"[^>]*>(.*?)</c-title>', c, re.S)
        if not t:
            continue
        d = re.search(r'<c-contents-desc[^>]*>(.*?)</c-contents-desc>', c, re.S)
        w = re.findall(r'<c-footer-desc[^>]*>(.*?)</c-footer-desc>', c, re.S)
        out.append((clean(' '.join(w)), clean(t.group(2)), html.unescape(t.group(1)), clean(d.group(1)) if d else ''))
    return out


def naver(where, q):
    # 클래스 이름이 자주 바뀌어서, 글 주소를 기준으로 앞뒤 글자를 잘라 씀
    u = 'https://search.naver.com/search.naver?where=%s&query=%s&%s' % (
        where, urllib.parse.quote(q), 'nso=so:dd' if where == 'blog' else 'sort=1')
    s = get(u)
    pat = r'https?://blog\.naver\.com/[A-Za-z0-9_-]+/\d+' if where == 'blog' else r'https?://cafe\.naver\.com/[A-Za-z0-9_-]+/\d+'
    pos, seen = [], set()
    for m in re.finditer(pat, s):
        if m.group(0) not in seen:
            seen.add(m.group(0))
            pos.append((m.start(), m.group(0)))
    out = []
    for i, (p, url) in enumerate(pos):
        prev = pos[i - 1][0] if i else max(0, p - 3000)
        nxt = pos[i + 1][0] if i + 1 < len(pos) else p + 6000
        before, seg = s[prev:p], s[p:nxt]
        titles = [clean(a) for a in re.findall(r'href="' + re.escape(url) + r'[^"]*"[^>]*>(.*?)</a>', seg, re.S)]
        titles = [t for t in titles if t and t != '새 창 열림']
        title = max(titles, key=len) if titles else ''
        text = clean(seg)
        desc = text.replace(title, '', 1).strip()[:300]
        d = DATE.search(clean(before[-2500:])) or DATE.search(text)
        out.append((d.group(1) if d else '', title[:120], url, desc))
    return out


def youtube(q):
    s = get('https://www.youtube.com/results?search_query=%s&sp=CAI%%253D' % urllib.parse.quote(q))  # 업로드 날짜순
    m = re.search(r'var ytInitialData = (\{.*?\});</script>', s, re.S)
    if not m:
        return []
    out = []

    def walk(o):
        if isinstance(o, dict):
            v = o.get('videoRenderer')
            if v:
                vid = v.get('videoId')
                title = ''.join(r.get('text', '') for r in v.get('title', {}).get('runs', []))
                when = v.get('publishedTimeText', {}).get('simpleText', '')
                desc = ''.join(r.get('text', '') for sn in v.get('detailedMetadataSnippets', []) for r in sn.get('snippetText', {}).get('runs', []))
                out.append((when, title, 'https://www.youtube.com/watch?v=' + vid, desc))
            r = o.get('reelItemRenderer') or o.get('shortsLockupViewModel')
            if r and isinstance(r, dict):
                vid = r.get('videoId') or (r.get('onTap', {}).get('innertubeCommand', {}).get('reelWatchEndpoint', {}).get('videoId'))
                title = (r.get('headline', {}) or {}).get('simpleText', '') or (r.get('overlayMetadata', {}).get('primaryText', {}) or {}).get('content', '')
                if vid:
                    out.append(('', title, 'https://www.youtube.com/shorts/' + vid, '(쇼츠)'))
            for x in o.values():
                walk(x)
        elif isinstance(o, list):
            for x in o:
                walk(x)
    walk(json.loads(m.group(1)))
    return out


SRC = {
    'daum_blog': lambda q: daum('blog', q),
    'daum_cafe': lambda q: daum('cafe', q),
    'naver_blog': lambda q: naver('blog', q),
    'naver_cafe': lambda q: naver('article', q),
    'youtube': youtube,
}

if __name__ == '__main__':
    srcs = list(SRC) if sys.argv[1] == 'all' else sys.argv[1].split(',')
    seen = set()
    for q in sys.argv[2:]:
        for sname in srcs:
            try:
                rows = SRC[sname](q)
            except Exception as e:
                print('# 실패 %s %s: %s' % (sname, q, e))
                continue
            print('# %s (%s) %d건' % (q, sname, len(rows)))
            for r in rows:
                if r[2] in seen:
                    continue
                seen.add(r[2])
                print('\t'.join((sname,) + tuple(x.replace('\t', ' ').replace('\n', ' ') for x in r)))
            time.sleep(0.7)
