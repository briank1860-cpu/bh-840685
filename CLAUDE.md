# 백합 해루질 앱 — 작업 규칙

개인용 앱. 서해(인천·경기 중심, 충남·전북) 해루질 장소를 물때·간조 깊이·날씨·계절·조과 후기로 점수 매겨 날짜와 장소를 추천한다.

## 대화
- 답변·화면 문구 모두 한국어. 짧고 분명하게, 요청 안 한 설명·후보는 넣지 않는다.
- 사용자 원칙: "조과 좋은 게 장땡". 어촌계 유료 장소도 넣고 표시만 한다. 선택은 사용자 몫.
- 아무 곳이나 금지하지 않는다. 금지는 해경·지자체 공식 공고가 있을 때만. 사고 이력은 '주의'로만.
- 실시간 자료(날씨·조위)는 항상 최신이어야 한다. 오래된 날씨를 보여 주지 않는다.
- 쓰는 사람에게 설치·가입을 요구하는 방식은 피한다.

## 파일
- `index.html` — 앱 전체(단일 HTML, 약 3MB). GitHub Pages로 배포: https://briank1860-cpu.github.io/bh-840685/
- `sw.js`·`manifest.webmanifest`·아이콘 — 설치형 앱(PWA). 인터넷 되면 항상 새 버전 먼저 받음. 건드릴 일 거의 없음.
- `collect-log.md` — 매일 클라우드 자동 수집 기록(맨 위가 최신).
- `tools/search.py` — 해루질 글 최신순 검색(다음 블로그·카페, 네이버 블로그·카페, 유튜브·쇼츠). `python tools/search.py all "박하지 해루질"`. 인스타·X·틱톡은 로그인 없이 막혀 있음.
- `tools/collect.py` — 매일 수집 1단계: 정해진 검색어+오늘 차례 장소 15곳을 모든 경로로 검색해 한 파일(TSV)로. `python tools/collect.py /tmp/c.tsv`
- `tools/daum_search.py` — 다음만 검색하는 옛 도구(남겨 둠).
- `tools/sheet_script.gs` — 현장 기록 구글 시트(사용자 드라이브 "백합 해루질 현장 기록")에 붙인 Apps Script 원본.

## index.html 안의 데이터(스크립트 안 상수)
- 한 줄 JSON: `DETAIL`, `REVIEW`, `PARK`, `MODE`, `SITEF`, `TARGETS`, `OSMBASE`, `FREEZONE` 등. 고칠 땐 파이썬으로 그 줄 JSON을 읽어 고친 뒤 `ensure_ascii=False`, 구분자 공백 없이, `</` → `<\/` 로 되돌려 쓴다.
- 여러 줄 JS 객체: `SITES`(배열), `ACCESS`, `NIGHT`, `EXCLUDED`, `MONTHS`.
- `/*CORE-START*/ ~ /*CORE-END*/` 계산 코드, `DEFAULTS`, `EOJANG`은 신중히.
- 새 장소를 넣으면 SITES·DETAIL·ACCESS·REVIEW·MODE·SITEF·PARK를 모두 채운다(기존 장소 하나를 본보기로). bt = badatime.com 물때표 페이지 번호.
- 점수: 낮 점수(ds)·밤 점수(ns)를 따로 계산. 밤은 그 달 밤에 되는 대상이 있을 때만, 해경 밤 전체 금지면 없음. `TIMEP`(장소×대상 d/n/b, 후기 근거) → 없으면 `TIMEP_T`(대상 기본값, `ECO` 생태 근거). `EASY`(초보 대상) 후기·시간대 맞으면 +6.
- `SPOTS`: 장소 안 포인트 {장소id:[{la,lo,p:'정확|대략',t:[대상id],d:설명,src}]} — 장소 지도에 대상 이름표로 표시. 현장 기록에 위치가 있으면(메모 끝 `⌖위도,경도`) 지도에 결과 색 점으로 표시.
- `ECO`: 대상별 공인 생태(활동 시간·바닥·수온·금어기, 출처 포함). `TIMEW`: 낮·밤 판단 근거 한 줄.
- 현장 기록: 폰(localStorage `bh_notes`)에 먼저 저장 → 연결되면 `SHARE`(구글 Apps Script 웹앱 주소)로 전송. 다른 사람 기록도 같은 주소 GET으로 읽음.

## 작업 순서
1. 시작할 때 `git pull` (클라우드 자동 수집이 매일 아침 7시쯤 index.html·collect-log.md를 고쳐 올림).
2. 고친 뒤 문법 확인:
   `node -e "const h=require('fs').readFileSync('index.html','utf8');[...h.matchAll(/<script>([\s\S]*?)<\/script>/g)].forEach(x=>new Function(x[1]));console.log('OK')"`
3. 화면 확인: 브라우저로 공유 링크를 열어 바뀐 부분을 직접 본다(올린 뒤 1~2분이면 반영).
4. `git add` → `git commit` → `git push` (main 브랜치에 바로).
5. `<meta name="robots" content="noindex,nofollow,noarchive">` 줄은 지우지 않는다(링크 아는 사람만 쓰게).

## 자동 수집(클라우드 루틴)
- 이름 "해루질 매일 수집 · 백합 도구 갱신", 매일 07:07(한국시간). 관리: https://claude.ai/code/routines/trig_01A4YWcF17pAkLQQkdL8mVjd
- 기존 장소 갱신 + 근거 2건 이상인 새 장소 하루 3곳까지 추가 + 앱 현장 기록 반영.
- 클라우드 환경 네트워크 허용: search.daum.net, v.daum.net, *.daum.net, search.naver.com, *.tistory.com, brunch.co.kr, *.youtube.com (현장 기록 읽기에 script.google.com·script.googleusercontent.com이 필요할 수 있음).

## 하지 말 것
- 저장소 공개 범위·이름 바꾸기.
- 현장 기록 시트 내용 지우기(사용자가 직접 관리).
- 근거 없이 장소를 금지·제외하기.
