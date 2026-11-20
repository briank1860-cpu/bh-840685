// 화면 문구 모순 자동 검사(2026-11-20). 앱을 연 브라우저에서 실행:
//   await import('./tools/ui_check.js').then(m=>m.run())   → {count, examples}
// 고른 대상이 끝까지 이어지는지, 한 화면에서 좋다·나쁘다가 섞이지 않는지, 점수가 화면마다 같은지 본다.
// 모든 장소 × (대상 없음, 장소의 대상 하나씩, 장소에 없는 대상 하나, 대상 두 개) × 날짜 3개.
export function chkSite(sid){
 const out=[],rows=siteRows(sid);if(!rows.length)return out;
 const days=[...new Set([rows.slice().sort((a,b)=>b.score-a.score)[0].n,rows[0].n,rows[Math.floor(rows.length/2)].n])];
 const tl=(DETAIL[sid]?.targets||[]).map(x=>findTarget(x.name)).filter(Boolean).filter((t,i,a)=>a.indexOf(t)===i);
 const notHere=TARGETS.find(t=>!siteHas(sid,t)&&EASY.test(t.id));
 const sets=[[],...tl.map(t=>[t]),notHere?[notHere]:null,tl.length>=2?tl.slice(0,2):null].filter(Boolean);
 for(const Ts of sets)for(const n of days){
  const ids=Ts.map(t=>t.id);lsSet('bh_wkT',ids.join(','));FOCUS.ts=ids.length?ids:null;siteDetail(sid,n,ids);
  const d=document.querySelector('#dlg').cloneNode(true);
  d.querySelectorAll('details').forEach(x=>x.querySelectorAll(':scope > :not(summary)').forEach(y=>y.remove()));
  d.querySelectorAll('a[href*="youtube"]').forEach(x=>x.remove()); // 영상 제목은 원문 그대로라 검사에서 뺌
  const t=document.querySelector('#dlg').innerText,tNoYt=d.innerText,card=t.slice(t.indexOf('이렇게 하세요'),t.indexOf('밖에서 고른 조건'));
  const tag=sid+'|'+fmtD(n)+'|'+(ids.join('+')||'-'),P=(k,x)=>out.push([tag,k,x]);
  const sc=+((card.match(/^이렇게 하세요 (?:낮|밤) (\d+)점/)||[])[1]);
  if(/undefined|NaN|\[object|null점/.test(t))P('깨진 값',(t.match(/.{20}(undefined|NaN|\[object|null점).{10}/)||[''])[0]);
  if(sc>=RECO_MIN&&/날씨 안 맞음/.test(card)&&!(Ts.length>1&&/만 가능/.test(t)))P('점수 높은데 날씨 안 맞음',sc);
  if(sc&&sc<RECO_MIN&&!/추천 기준/.test(card))P('추천 기준 아래인데 안내 없음',sc);
  const hd=t.match(/(고른 날|다음 좋은 날) (\S+) · (낮|밤) (\d+)점/);if(hd&&sc&&+hd[4]!==sc)P('머리·카드 점수 다름',hd[4]+'/'+sc);
  Ts.forEach(T=>{const nm=T.name;
   if(new RegExp('이 장소에서 '+nm+'.{0,2} 잡은 후기는 없어요').test(card)&&new RegExp(nm+'.{0,2} 잡은 후기 \\d+건').test(card))P('후기 있음·없음 동시',nm);
   if(/(\d+)월엔 잘 안 나옴/.test(card)&&new RegExp(nm+'[^\\n]*잡은 후기 \\d+건\\(최근 '+tMonth(n)+'월').test(card))P('그달 안 나옴인데 그달 후기',nm);
   if(sc>=RECO_MIN&&mStat(T.id,tMonth(n))==='x'&&!/금어기/.test(card))P('금어기 안내 없음',nm)});
  if(card.split('\n').some(l=>/잘 맞음/.test(l)&&/잡은 후기 없음/.test(l)))P('잘 맞음인데 후기 없음','');
  if(/이에요이에요|어요어요|요요\.|\.\./.test(tNoYt))P('말 중복',(tNoYt.match(/.{15}(이에요이에요|어요어요|요요\.|\.\.).{5}/)||[''])[0]);
  if(Ts.length){const body=card.split('\n').filter(l=>!/^주의|고립|구조|숨졌|사고/.test(l)).join('\n');
   const others=TARGETS.filter(x=>!Ts.includes(x)&&x.name.length>=2&&body.includes(x.name)&&!Ts.some(T=>T.name.includes(x.name)||x.name.includes(T.name))).map(x=>x.name);
   if(others.length)P('다른 대상 섞임',others.join(','))}
 }
 return out}
export async function run(){
 const dm=drawMap;drawMap=function(){};const bad=[];
 try{for(const sid of [...new Set(RESULT.rows.map(r=>r.site.id))]){try{bad.push(...chkSite(sid))}catch(e){bad.push([sid,'오류',String(e).slice(0,120)])}await new Promise(r=>setTimeout(r,0))}}
 finally{drawMap=dm;lsSet('bh_wkT','');FOCUS.ts=null;try{$('dlg').close()}catch(e){}}
 const count={},ex={};bad.forEach(b=>{count[b[1]]=(count[b[1]]||0)+1;(ex[b[1]]=ex[b[1]]||[]).length<5&&ex[b[1]].push(b[0]+' '+b[2])});
 window._uiBad=bad;return {count,examples:ex}}
