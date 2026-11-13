#!/usr/bin/env python3
"""장소별 해루질 유튜브 영상 연결: 제목·설명에 장소 이름과 해루질 관련 말이 같이 나오는 영상을 그 장소에 붙여
index.html의 VIDEOS 상수를 갱신한다(장소마다 최근 2년 안 최신 8개).
사용:
  python3 tools/videos.py --tsv /tmp/c.tsv      collect.py 결과의 유튜브 줄로 갱신
  python3 tools/videos.py --search              장소마다 유튜브를 직접 검색해 갱신(느림, 1~2분)
둘 다 줘도 된다. 끝에 장소별 영상 수를 출력한다."""
import datetime, json, os, re, sys, time
sys.path.insert(0, os.path.dirname(__file__))

HERE = os.path.dirname(__file__)
HTML = os.path.join(HERE, '..', 'index.html')
KEEP, MAX_DAYS = 8, 730  # 최근 2년
WORD = re.compile(r'해루질|갯벌|조개|박하지|돌게|꽃게|소라|골뱅이|낙지|주꾸미|쭈꾸미|맛조개|백합|동죽|바지락|가무락|모시조개|체험')

# 장소별 이름표: any = 이 중 하나가 제목·설명에 있어야 함, need = 흔한 말이라 같이 있어야 하는 말(지역명), not = 있으면 다른 곳(예: '당진해루질' 안의 '진해루')
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
    'gc_dongho': {'any': ['동호해수욕장', '동호해변', '고창 동호'], 'not': ['동해', '양양', '강릉', '비단조개']},
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
    'dj_dobido': {'any': ['도비도']},
    'ta_batgae': {'any': ['밧개']},
    'ta_sinduri': {'any': ['신두리']},
    'ta_hakampo': {'any': ['학암포']},
    'ta_duyeo': {'any': ['두여해변', '두여해수욕장']},
    'ss_hwanggeum': {'any': ['서산 황금산', '황금산 해루', '황금산 낙지', '황금산 소라', '황금산 갯벌', '황금산해루']},
    'ta_jinsan': {'any': ['진산리']},
    'ta_magumpo': {'any': ['마검포']},
    'ta_kkotji': {'any': ['꽃지']},
    'ta_baeksajang': {'any': ['백사장항', '백사장해수욕장']},
    'ss_beolcheonpo': {'any': ['벌천포']},
    'dj_waemok': {'any': ['왜목']},
    'br_wonsando': {'any': ['원산도']},
    'br_yongdu': {'any': ['용두해수욕장', '용두해변']},
    'ba_gosapo': {'any': ['고사포']},
    'jn_holtong': {'any': ['홀통']},
    'jn_jogeumnaru': {'any': ['조금나루']},
    'jn_songgye': {'any': ['도리포', '송계마을']},
    'jn_dolmeori': {'any': ['돌머리']},
    'jn_duuri': {'any': ['두우리', '백바위해수욕장']},
    'jn_songido': {'any': ['송이도']},
    'jn_jeungdo': {'any': ['짱뚱어해변', '우전해변', '증도']},
    'jn_imjado': {'any': ['임자도']},
    'jn_jaeundo': {'any': ['자은도']},
    'jn_hoedong': {'any': ['신비의바닷길', '회동'], 'need': ['진도']},
    'jn_geocha': {'any': ['거차'], 'need': ['순천']},
    'jn_jangcheok': {'any': ['장척'], 'need': ['여수']},
    'jn_sado': {'any': ['사도'], 'need': ['여수']},
    'jn_jangdo': {'any': ['장도'], 'need': ['벌교']},
    'jn_yulpo': {'any': ['율포']},
    'jn_baeksa': {'any': ['백사어촌', '백사마을']},
    'jn_sinri': {'any': ['신리'], 'need': ['장흥']},
    'jn_myeongsasimni': {'any': ['명사십리'], 'need': ['완도']},
    'jn_namseong': {'any': ['남성마을', '남성어촌']},
    'bs_sodam': {'any': ['소담공원', '신호동']},
    'bs_dadaepo': {'any': ['다대포']},
    'bs_ilgwang': {'any': ['일광해수욕장', '일광해변']},
    'gn_jinhaeru': {'any': ['진해루'], 'not': ['당진', '석문']},
    'gn_yongdaemi': {'any': ['룡대미', '용대미']},
    'gn_donghwa': {'any': ['동화마을', '동화어촌']},
    'gn_bito': {'any': ['비토섬', '비토리']},
    'gn_daedo': {'any': ['대도'], 'need': ['하동']},
    'gn_munhang': {'any': ['문항']},
    'gn_ieo': {'any': ['이어마을', '이어어촌']},
    'gn_jeondo': {'any': ['전도갯벌', '전도마을']},
    'gn_mijo': {'any': ['미조', '초전'], 'need': ['남해']},
    'gn_maemiseong': {'any': ['매미성', '대금마을']},
    'gn_sagok': {'any': ['사곡해수욕장', '사곡해변']},
    'jj_ojori': {'any': ['오조리']},
    'jj_hado': {'any': ['하도리', '하도어촌']},
    'jj_wimi': {'any': ['위미']},
    'jj_geumneung': {'any': ['금능']},
    'jj_iho': {'any': ['이호테우', '이호해수욕장']},
    'gw_ayajin': {'any': ['아야진', '청간정']},
    'gw_sacheonjin': {'any': ['사천진']},
    'gb_odori': {'any': ['오도리'], 'need': ['포항']},
    'gb_songdaemal': {'any': ['송대말']},
    'us_seuldo': {'any': ['슬도']},
    'us_jujeon': {'any': ['주전'], 'need': ['울산']},
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


def is_approx(when):
    """'3개월 전', '1년 전'처럼 정확한 날짜가 아닌 표시면 True(화면에 '~쯤'으로)."""
    return bool(re.match(r'\s*\d+\s*(개월|년)\s*전', when or ''))


FISH = re.compile(r'낚시|선상|에깅|루어')
HARU = re.compile(r'해루질|낮루질|갯벌|조개|체험|캐기|줍')


CAMP = re.compile(r'캠핑|차박|텐트|글램핑|백패킹|솔캠|캠핑카|야영|vlog|브이로그|여행', re.I)
CATCH = re.compile(r'해루|낮루질|갯벌|체험|조개|바지락|백합|맛조개|동죽|낙지|꽃게|박하지|소라|고둥|고동|잡이|캐기|줍')
# 제목만으로 못 거르는 무관 영상(여행 일지·놀이 영상 등). 사람이 보고 넣는다
BLOCK = {'P3P78OK47q8', '-jx207czt3w', '491tY9MmNwo', '4CmLd3w9U6Y', '72kRGcR9XIo', 'EGou-hugmqs', 'I0xfWjvJddo', 'MfYAf4bmNXA', 'NlmzLy_divo', 'V6tNH3jwwHY', 'XkWl7P_Tsvg', 'YCaDUfIR3kA', 'Yi8njCQafa4', '_5ItCMmjJ2w', 'a4rMRQviPzI', 'aKE_3vEExlI', 'c2KYK9_I0ho', 'd0Pgf-bulcs', 'e2JgMSSioPQ', 'itdCT3O187o', 'jqOCtw1ORUg', 'm6rj57KM9Sc', 'mEK0DSMlgas', 'n0dpCg9EWgU', 'ndAfoGmUKE8', 'xAtMVoansP0', 'zBg8wNoB28k'}


def skip_title(title, vid=''):
    """뺄 영상: 낚시 영상(해루질·갯벌 말이 제목에 없으면), 캠핑·차박·여행 영상(잡는 이야기가 제목에 없으면), BLOCK."""
    if vid in BLOCK:
        return True
    if FISH.search(title) and not HARU.search(title):
        return True
    return bool(CAMP.search(title)) and not CATCH.search(title)


DESC_CACHE = os.path.join(HERE, 'yt_desc_cache.json')  # 영상ID → 설명 전체에서 찾은 장소 id 목록(다시 안 열게)
_dc = None
def full_desc_sites(vid):
    """제목·검색 요약으로 장소를 못 찾은 해루질 영상: 영상 페이지의 설명 전체를 읽어 장소를 찾는다."""
    global _dc
    if _dc is None:
        try: _dc = json.load(open(DESC_CACHE, encoding='utf-8'))
        except Exception: _dc = {}
    if vid in _dc: return _dc[vid]
    import urllib.request
    try:
        req = urllib.request.Request('https://www.youtube.com/watch?v=' + vid, headers={'User-Agent': 'Mozilla/5.0', 'Accept-Language': 'ko-KR,ko'})
        h = urllib.request.urlopen(req, timeout=20).read().decode('utf-8', 'ignore')
        m = re.search(r'"shortDescription":"((?:[^"\\]|\\.)*)"', h)
        desc = json.loads('"' + m.group(1) + '"') if m else ''
        tm = re.search(r'<meta name="keywords" content="([^"]*)"', h)
        out = match_sites(desc + ' ' + (tm.group(1) if tm else '')) if desc or tm else []
        if len(out) != 1: out = []  # 해시태그로 여러 장소를 늘어놓은 영상은 어느 곳인지 몰라 붙이지 않음
    except Exception:
        return []
    _dc[vid] = out
    return out
def save_desc_cache():
    if _dc is not None:
        json.dump(_dc, open(DESC_CACHE, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))


def vid_of(url):
    m = re.search(r'(?:v=|shorts/)([A-Za-z0-9_-]{11})', url)
    return m.group(1) if m else None


def match_sites(text):
    out = []
    for sid, a in ALIAS.items():
        if any(k in text for k in a['any']) and all(k in text for k in a.get('need', [])) and not any(k in text for k in a.get('not', [])):
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
    before = {(k, x['v']) for k, l in V.items() for x in l}
    added = 0; opened = 0
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
        if is_approx(when) and re.search(r'([2-9]|\d\d)\s*년', when):  # '2년 전'은 2~3년 전이라 최근 2년 밖(날마다 붙었다 빠졌다 하는 것 막기)
            continue
        if skip_title(title, vid):
            continue
        # 제목에 장소 이름이 있으면 제목만 믿고, 없을 때만 설명까지 본다(설명에 이웃 장소가 섞이는 것 막기)
        ms = match_sites(title) or match_sites(text)
        if not ms and HARU.search(title) and opened < 80:  # 제목에 해루질은 있는데 장소를 못 찾으면 설명 전체를 열어 본다
            opened += 1; ms = full_desc_sites(vid); time.sleep(0.3)
        for sid in ms:
            lst = V.setdefault(sid, [])
            if any(x['v'] == vid for x in lst):
                continue
            item = {'v': vid, 't': title[:90], 'd': d.isoformat(), 's': 1 if '/shorts/' in url else 0}
            if is_approx(when):
                item['a'] = 1
            lst.append(item)
            added += 1
    for sid in list(V):  # 이미 붙은 것 중 제목이 다른 장소를 가리키거나 낚시·캠핑 영상이면 뺌
        keep = []
        for x in V[sid]:
            ts = match_sites(x['t'])
            bad_own = any(k in x['t'] for k in ALIAS.get(sid, {}).get('not', []))
            if skip_title(x['t'], x['v']) or bad_own or (ts and sid not in ts):
                continue
            keep.append(x)
        V[sid] = keep
    for sid in list(V):  # 2년 지난 것 빼고 최신순 8개
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
    save_desc_cache()
    after = {(k, x['v']) for k, l in V.items() for x in l}
    print('실제로 새로 보이는 영상', len(after - before), '/ 빠진 영상', len(before - after), '(검색에서 붙은 수', added, ') / 영상 있는 장소', len(V), '/ 전체', len(after))
    for sid in ALIAS:
        print(sid, len(V.get(sid, [])))


if __name__ == '__main__':
    main()
