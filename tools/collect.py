#!/usr/bin/env python3
"""매일 수집 1단계: 정해진 검색어 전부 + 장소 이름(날마다 돌아가며)을 모든 경로로 검색해 한 파일에 모은다.
사용: python3 tools/collect.py [출력파일]   (기본 /tmp/collect_YYYYMMDD.tsv)
끝에 경로별·검색어별 건수와 막힌 경로를 출력한다. 이 파일을 다 읽은 뒤 반영 판단을 한다."""
import datetime, os, re, sys, time
sys.path.insert(0, os.path.dirname(__file__))
import search

BASE = ['해루질 후기', '해루질', '야간 해루질', '낮 해루질', '백합 해루질', '맛조개 해루질', '박하지 해루질', '꽃게 해루질',
        '소라 해루질', '보말 해루질', '문어 해루질', '낙지 해루질', '주꾸미 해루질', '동죽 해루질', '해루질 고립', '해루질 출입통제', '갯벌체험장 후기']
REGION = ['태안', '서산', '당진', '홍성', '보령', '서천', '군산', '부안', '고창', '옹진', '영흥도', '대부도', '화성', '영종도', '무의도',
          '무안', '신안', '영광', '진도', '여수', '고흥', '완도', '순천', '남해', '거제', '통영', '사천', '부산', '제주', '포항', '울산', '강릉']


def site_names():
    h = open(os.path.join(os.path.dirname(__file__), '..', 'index.html'), encoding='utf-8').read()
    a = h.index('const SITES=[')
    b = h.index('\n];', a)
    names = re.findall(r"""['"]?name['"]?\s*:\s*['"]([^'"]+)['"]""", h[a:b])
    # '인천 무의도 하나개' → '하나개' 처럼 마지막 말만, 괄호·번호 정리
    gen = {'체험장', '해수욕장', '해변', '어촌계', '갯벌', '체험마을', '갯벌체험장', '어촌체험마을', '어촌체험휴양마을'}
    out = []
    for n in names:
        w = [re.sub(r'(해수욕장|해변|어촌체험마을|체험마을|갯벌체험장)$', '', x) for x in re.sub(r'\(.*?\)', '', n).replace('·', ' ').split()[1:]]
        w = [x for x in w if x and x not in gen and not re.fullmatch(r'[\d~번]+', x)]
        if w:
            out.append(w[-1])
    return list(dict.fromkeys(out))


def main():
    today = datetime.date.today()
    path = sys.argv[1] if len(sys.argv) > 1 else '/tmp/collect_%s.tsv' % today.strftime('%Y%m%d')
    names = site_names()
    k = today.toordinal() % max(1, len(names))
    todays = (names[k:] + names[:k])[:15]  # 날마다 15곳씩 돌아가며
    region = REGION[today.toordinal() % len(REGION):] + REGION[:today.toordinal() % len(REGION)]
    queries = BASE + [r + ' 해루질' for r in region[:6]] + [n + ' 해루질' for n in todays]
    seen, cnt, fail = set(), {}, {}
    with open(path, 'w', encoding='utf-8') as f:
        for q in queries:
            for s in search.SRC:
                try:
                    rows = search.SRC[s](q)
                except Exception as e:
                    fail[s] = fail.get(s, 0) + 1
                    f.write('#실패\t%s\t%s\t%s\n' % (s, q, str(e)[:120]))
                    continue
                n = 0
                for r in rows:
                    if r[2] in seen:
                        continue
                    seen.add(r[2])
                    n += 1
                    f.write('\t'.join((s, q) + tuple(x.replace('\t', ' ').replace('\n', ' ') for x in r)) + '\n')
                cnt[(s, q)] = n
                time.sleep(0.5)
    by_src = {}
    for (s, q), n in cnt.items():
        by_src[s] = by_src.get(s, 0) + n
    print('파일:', path)
    print('검색어 %d개, 글 %d건(중복 제외)' % (len(queries), len(seen)))
    print('경로별:', ', '.join('%s %d' % (s, by_src.get(s, 0)) for s in search.SRC))
    if fail:
        print('막힌 경로(실패 횟수):', ', '.join('%s %d' % kv for kv in fail.items()))
    print('오늘 장소 검색어:', ', '.join(todays))
    print('줄 형식: 경로<TAB>검색어<TAB>언제<TAB>제목<TAB>URL<TAB>요약')
    # 영상 갱신은 빠뜨리기 쉬워 여기서 바로 한다(장소별 유튜브 VIDEOS)
    import subprocess
    print('--- 영상 갱신(videos.py) ---', flush=True)
    subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'videos.py'), '--tsv', path, '--search'])


if __name__ == '__main__':
    main()
