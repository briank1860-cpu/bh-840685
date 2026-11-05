// 갯벌친구 현장 기록 — 구글 시트(확장 프로그램 > Apps Script)에 붙여 웹 앱으로 배포
// 앱이 POST로 기록을 보내고, GET으로 모든 기록(기기 ID 제외)을 읽어 감
// 2026-11: 현장 친구 위치 공유(op:'loc', GET ?g=모임코드) 추가. 위치는 '위치' 시트에 모임코드·기기별 마지막 1줄만, 12시간 지나면 지움.
//          앱 문제·제안은 sid 'app_feedback' 기록으로 들어옴(첫 시트).
function sh() { return SpreadsheetApp.getActiveSpreadsheet().getSheets()[0]; }
function locSh() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  return ss.getSheetByName('위치') || ss.insertSheet('위치');
}
function out(o) { return ContentService.createTextOutput(JSON.stringify(o)).setMimeType(ContentService.MimeType.JSON); }
function cut(x, n) { return String(x || '').slice(0, n).replace(/^[=+\-@]/, "'$&"); }
const GRP = /^[A-Za-z0-9]{8,32}$/;

function doPost(e) {
  const lock = LockService.getScriptLock();
  lock.waitLock(10000);
  try {
    const b = JSON.parse(e.postData.contents);
    if (b.op === 'loc') { // 위치 공유: [시각, 모임코드, 기기, 별명, 위도, 경도, 정확도(m), 장소id]
      if (!GRP.test(b.g) || !isFinite(b.la) || !isFinite(b.lo)) return out({ ok: 0 });
      const s = locSh(), now = Date.now(), v = s.getDataRange().getValues();
      for (let i = v.length - 1; i >= 0; i--) { // 같은 기기 옛 위치·12시간 지난 위치 지우기
        const old = v[i][0] instanceof Date && now - v[i][0].getTime() > 12 * 3600e3;
        if (old || (String(v[i][1]) === String(b.g) && String(v[i][2]) === String(b.dev))) s.deleteRow(i + 1);
      }
      if (!b.stop) s.appendRow([new Date(), b.g, cut(b.dev, 40), cut(b.n, 20), Number(b.la).toFixed(6), Number(b.lo).toFixed(6), Math.round(b.acc || 0), cut(b.sid, 40)]);
      return out({ ok: 1 });
    }
    const s = sh();
    if (b.op === 'del') { // 같은 기기에서 쓴 기록만 지움
      const v = s.getDataRange().getValues();
      for (let i = v.length - 1; i >= 1; i--) {
        if (String(v[i][9]) === String(b.k) && String(v[i][8]) === String(b.dev)) s.deleteRow(i + 1);
      }
      return out({ ok: 1 });
    }
    if (!/^[a-z]{2,3}_[a-z0-9_]{2,30}$/.test(b.sid) || !/^\d{4}-\d{2}-\d{2}$/.test(b.d) || !/^[gmb]$/.test(b.r)) return out({ ok: 0 });
    s.appendRow([new Date(), b.sid, cut(b.name, 60), "'" + b.d, { g: '좋음', m: '보통', b: '나쁨' }[b.r],
      cut(b.c, 200), cut(b.m, 1000), cut(b.n, 30), cut(b.dev, 40), cut(b.k, 40)]);
    return out({ ok: 1 });
  } finally {
    lock.releaseLock();
  }
}

function doGet(e) {
  const g = e && e.parameter && e.parameter.g;
  if (g) { // 같은 모임코드의 2시간 안 위치만(기기 ID는 앞 6자만)
    if (!GRP.test(g)) return out({ locs: [] });
    const now = Date.now();
    const v = locSh().getDataRange().getValues().filter(r => String(r[1]) === g && r[0] instanceof Date && now - r[0].getTime() < 2 * 3600e3);
    return out({ locs: v.map(r => ({ t: r[0].getTime(), d: String(r[2]).slice(0, 6), n: r[3], la: +r[4], lo: +r[5], acc: +r[6], sid: r[7] })) });
  }
  const R = { '좋음': 'g', '보통': 'm', '나쁨': 'b' };
  const v = sh().getDataRange().getValues().slice(1).slice(-3000);
  const day = x => x instanceof Date ? Utilities.formatDate(x, 'Asia/Seoul', 'yyyy-MM-dd') : String(x);
  return out({ rows: v.filter(r => r[1]).map(r => ({ sid: r[1], d: day(r[3]), r: R[r[4]] || 'm', c: r[5], m: r[6], n: r[7], k: String(r[9]) })) });
}
