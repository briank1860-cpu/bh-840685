#!/usr/bin/env python3
"""장소별 해루질 유튜브 영상 연결: 제목·설명에 장소 이름과 해루질 관련 말이 같이 나오는 영상을 그 장소에 붙여
index.html의 VIDEOS 상수를 갱신한다(장소마다 최근 1년 안 최신 8개).
사용:
  python3 tools/videos.py --tsv /tmp/c.tsv      collect.py 결과의 유튜브 줄로 갱신
  python3 tools/videos.py --search              장소마다 유튜브를 직접 검색해 갱신(느림, 1~2분)
둘 다 줘도 된다. 끝에 장소별 영상 수를 출력한다."""
import datetime, json, os, re, sys, time
sys.path.insert(0, os.path.dirname(__file__))

HERE = os.path.dirname(__file__)
HTML = os.path.join(HERE, '..', 'index.html')
KEEP, MAX_DAYS = 8, 365
WORD = re.compile(r'해루질|갯벌|조개|박하지|돌게|꽃게|소라|골뱅이|낙지|주꾸미|쭈꾸미|맛조개|백합|동죽|바지락|가무락|모시조개|체험')

# 장소별 이름표: any = 이 중 하나가 제목·설명에 있어야 함, need = 흔한 말이라 같이 있어야 하는 말(지역명)
ALIAS = {
    'ic_seonnyeo': {'any': ['선녀바위']},
    'ic_masian': {'any': ['마시안']},
    'ic_jangbong': {'any': ['한들해변', '한들해수욕장', '장봉도 한들']},
    'ic_hanagae': {'any': ['하나개']},
    'ta_mongsan': {'any': ['몽산포']},
    'ta_dalsan': {'any': ['달산포']},
    'ta_cheongpo': {'any': ['청포대']},
    'ta_sambong': {'any': ['삼봉해수욕장', '기지포', '삼봉해변']},
    'br_muchang': {'any': ['무창포']},
    'sc_chunjang': {'any': ['춘장대']},
    'sc_seondo': {'any': ['선도리']},
    'sc_wolha': {'any': ['월하성']},
    'gc_gusipo': {'any': ['구시포']},
    'gc_dongho': {'any': ['동호해수욕장', '동호해변', '고창 동호']},
    'ic_simnipo': {'any': ['십리포']},
    'ic_janggyeongri': {'any': ['장경리']},
    'ic_nogari': {'any': ['노가리해변', '노가리해수욕장', '용담리']},
    'ic_ongam': {'any': ['옹암']},
    'ic_sugi': {'any': ['수기해변', '수기해수욕장']},
    'ic_seopori': {'any': ['서포리', '밧지름']},
    'ic_jawol': {'any': ['자월도']},
    'ic_seungbong': {'any': ['승봉도', '이일레']},
    'ic_ijak': {'any': ['대이작도', '큰풀안', '작은풀안']},
    'ic_eulwangri': {'any': ['을왕리']},
    'ic_wangsan': {'any': ['왕산해수욕장', '왕산해변']},
    'ic_jamjindo': {'any': ['잠진도']},
    'ic_nambuk': {'any': ['남북어촌', '남북동']},
    'ic_silmi': {'any': ['실미도', '실미해변', '실미해수욕장']},
    'ic_somuuido': {'any': ['소무의도', '광명항']},
    'ic_yeongjongjin': {'any': ['구읍뱃터', '영종진']},
    'gg_bangamori': {'any': ['방아머리']},
    'gg_gubong': {'any': ['구봉도']},
    'gg_jonghyeon': {'any': ['종현어촌', '종현마을']},
    'gg_tando': {'any': ['탄도항', '누에섬']},
    'gg_seongam': {'any': ['선감도', '선감어촌']},
    'gg_heulgot': {'any': ['흘곶']},
    'gg_jebudo': {'any': ['제부도']},
    'gg_gungpyeong': {'any': ['궁평항', '궁평해수욕장', '궁평해변']},
    'gg_baekmiri': {'any': ['백미리']},
    'gg_goon': {'any': ['고온항', '고온이', '매향리']},
    'gg_gukhwado': {'any': ['국화도']},
    'gg_oido': {'any': ['오이도']},
    'ic_naeri': {'any': ['내리 갯벌', '내리갯벌', '영흥도 내리']},
    'ic_mokseom': {'any': ['목섬'], 'need': ['선재']},
    'ic_cheukdo': {'any': ['측도']},
    'ic_soya': {'any': ['소야도', '떼뿌루', '뒷목섬']},
    'ic_geojampo': {'any': ['거잠포']},
    'gg_mechuri': {'any': ['메추리섬']},
    'gg_jjokbak': {'any': ['쪽박섬']},
    'gg_ippado': {'any': ['입파도']},
    'dj_seokmun_main': {'any': ['석문방조제', '석문 방조제']},
    'dj_seokmun_west': {'any': ['석문방조제', '석문 방조제']},
    'ta_jinsan': {'any': ['진산리']},
    'ta_magumpo': {'any': ['마검포']},
    'ta_kkotji': {'any': ['꽃지']},
    'ta_baeksajang': {'any': ['백사장항', '백사장해수욕장']},
    'ss_beolcheonpo': {'any': ['벌천포']},
    'dj_waemok': {'any': ['왜목']},
    'br_wonsando': {'any': ['원산도']},
    'br_yongdu': {'any': ['용두해수욕장', '용두해변']},
    'ba_gosapo': {'any': ['고사포']},
}


def to_date(when, today):
    """'3일 전', '2주 전', '1년 전', '2026.10.30' 같은 표시를 날짜로(대략)."""
    w = (when or '').strip()
    m = re.match(r'(\d{4})\.\s?(\d{1,2})\.\s?(\d{1,2})', w)
    if m:
        return datetime.date(int(m[1]), int(m[2]), int(m[3]))
    m = re.match(r'(\d+)\s*(초|분|시간|일|주|개월|년)\s*전', w)
    if not m:
        return None
    n, u = int(m[1]), m[2]
    days = {'초': 0, '분': 0, '시간': 0, '일': n, '주': 7 * n, '개월': 30 * n, '년': 365 * n}[u]
    return today - datetime.timedelta(days=days)


def vid_of(url):
    m = re.search(r'(?:v=|shorts/)([A-Za-z0-9_-]{11})', url)
    return m.group(1) if m else None


def match_sites(text):
    out = []
    for sid, a in ALIAS.items():
        if any(k in text for k in a['any']) and all(k in text for k in a.get('need', [])):
            out.append(sid)
    return out


def main():
    args = sys.argv[1:]
    today = datetime.date.today()
    h = open(HTML, encoding='utf-8').read()
    m = re.search(r'^const VIDEOS=(\{.*\});[^\n]*$', h, re.M)
    V = json.loads(m.group(1)) if m else {}
    rows = []  # (when, title, url, desc)
    if '--tsv' in args:
        for line in open(args[args.index('--tsv') + 1], encoding='utf-8'):
            p = line.rstrip('\n').split('\t')
            if len(p) >= 6 and p[0] == 'youtube':
                rows.append((p[2], p[3], p[4], p[5]))
    if '--search' in args:
        import search
        for sid, a in ALIAS.items():
            try:
                for r in search.youtube(a['any'][0] + ' 해루질'):
                    rows.append(r)
            except Exception as e:
                print('# 실패', sid, e)
            time.sleep(0.4)
    added = 0
    for when, title, url, desc in rows:
        vid = vid_of(url)
        if not vid:
            continue
        text = title + ' ' + desc
        if not WORD.search(text):
            continue
        d = to_date(when, today)
        if d is None or (today - d).days > MAX_DAYS:
            continue
        for sid in match_sites(text):
            lst = V.setdefault(sid, [])
            if any(x['v'] == vid for x in lst):
                continue
            lst.append({'v': vid, 't': title[:90], 'd': d.isoformat(), 's': 1 if '/shorts/' in url else 0})
            added += 1
    for sid in list(V):  # 1년 지난 것 빼고 최신순 8개
        V[sid] = sorted([x for x in V[sid] if (today - datetime.date.fromisoformat(x['d'])).days <= MAX_DAYS],
                        key=lambda x: x['d'], reverse=True)[:KEEP]
        if not V[sid]:
            del V[sid]
    dump = 'const VIDEOS=' + json.dumps(V, ensure_ascii=False, separators=(',', ':')).replace('</', r'<\/') + '; // 장소별 해루질 유튜브(tools/videos.py가 갱신)'
    if m:
        h = h[:m.start()] + dump + h[m.end():]
    else:
        i = h.index('const SPOTS=')
        h = h[:i] + dump + '\n' + h[i:]
    open(HTML, 'w', encoding='utf-8', newline='').write(h)
    print('새로 붙은 영상', added, '/ 영상 있는 장소', len(V), '/ 전체', sum(len(v) for v in V.values()))
    for sid in ALIAS:
        print(sid, len(V.get(sid, [])))


if __name__ == '__main__':
    main()
