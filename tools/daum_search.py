#!/usr/bin/env python3
"""다음 검색 최신순 결과를 뽑는다(WebFetch로는 결과 칸이 비어 보임).
사용: python3 tools/daum_search.py [blog|cafe|news] 검색어 [검색어...]  (쪽수: PAGES=3 환경변수, 기본 1)
출력: 줄마다 '언제<TAB>제목<TAB>URL<TAB>요약'"""
import html, os, re, sys, time, urllib.parse, urllib.request

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36'

def clean(s):
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', '', s))).strip()

def search(col, q, page=1):
    url = 'https://search.daum.net/search?w=fusion&sort=recency&col=%s&q=%s&p=%d' % (col, urllib.parse.quote(q), page)
    req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept-Language': 'ko-KR,ko'})
    s = urllib.request.urlopen(req, timeout=30).read().decode('utf-8', 'replace')
    out = []
    for c in re.findall(r'<c-card[^>]*>(.*?)</c-card>', s, re.S):
        t = re.search(r'<c-title[^>]*data-href="([^"]+)"[^>]*>(.*?)</c-title>', c, re.S)
        if not t:
            continue
        d = re.search(r'<c-contents-desc[^>]*>(.*?)</c-contents-desc>', c, re.S)
        w = re.findall(r'<c-footer-desc[^>]*>(.*?)</c-footer-desc>', c, re.S)
        out.append((clean(' '.join(w)), clean(t.group(2)), html.unescape(t.group(1)), clean(d.group(1)) if d else ''))
    return out

if __name__ == '__main__':
    col, qs = sys.argv[1], sys.argv[2:]
    seen = set()
    for q in qs:
        rows = []
        for pg in range(1, int(os.environ.get('PAGES', '1')) + 1):
            try:
                rows += search(col, q, pg)
            except Exception as e:
                print('# 실패 %s p%d: %s' % (q, pg, e)); break
            time.sleep(0.5)
        print('# %s (%s) %d건' % (q, col, len(rows)))
        for r in rows:
            if r[2] in seen:
                continue
            seen.add(r[2]); print('\t'.join(r))
        time.sleep(1)
