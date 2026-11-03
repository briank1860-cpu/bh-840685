// 백합 해루질 현장 기록 — 구글 시트(확장 프로그램 > Apps Script)에 붙여 웹 앱으로 배포
// 앱이 POST로 기록을 보내고, GET으로 모든 기록(기기 ID 제외)을 읽어 감
function sh() { return SpreadsheetApp.getActiveSpreadsheet().getSheets()[0]; }
function out(o) { return ContentService.createTextOutput(JSON.stringify(o)).setMimeType(ContentService.MimeType.JSON); }
function cut(x, n) { return String(x || '').slice(0, n).replace(/^[=+\-@]/, "'$&"); }

function doPost(e) {
  const lock = LockService.getScriptLock();
  lock.waitLock(10000);
  try {
    const b = JSON.parse(e.postData.contents);
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

function doGet() {
  const R = { '좋음': 'g', '보통': 'm', '나쁨': 'b' };
  const v = sh().getDataRange().getValues().slice(1).slice(-3000);
  const day = x => x instanceof Date ? Utilities.formatDate(x, 'Asia/Seoul', 'yyyy-MM-dd') : String(x);
  return out({ rows: v.filter(r => r[1]).map(r => ({ sid: r[1], d: day(r[3]), r: R[r[4]] || 'm', c: r[5], m: r[6], n: r[7], k: String(r[9]) })) });
}
