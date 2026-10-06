const places={
1:{name:'巷口牛肉麵研究所',type:'牛肉麵',area:'三重',distance:'450m',price:'$',rating:'4.8',queue:'10 分',revisit:'93%',thumb:'noodle',badge:'Bib Gourmand'},
2:{name:'河岸咖啡室',type:'咖啡',area:'三重',distance:'800m',price:'$$',rating:'4.6',queue:'0 分',revisit:'88%',thumb:'cafe',badge:'適合聊天'},
3:{name:'小鍋計畫',type:'個人鍋',area:'中山',distance:'2.1km',price:'$$',rating:'4.7',queue:'35 分',revisit:'91%',thumb:'hotpot',badge:'2026 新進榜'},
4:{name:'南城鵝肉攤',type:'台菜',area:'大安',distance:'3.0km',price:'$$',rating:'4.5',queue:'15 分',revisit:'89%',thumb:'noodle',badge:'在地常客'},
5:{name:'夜行飯糰',type:'宵夜',area:'松山',distance:'4.8km',price:'$',rating:'4.4',queue:'5 分',revisit:'84%',thumb:'hotpot',badge:'23:00 後'},
6:{name:'木日甜點室',type:'甜點',area:'大安',distance:'3.4km',price:'$$',rating:'4.9',queue:'20 分',revisit:'95%',thumb:'cafe',badge:'社群熱門'}
};
const $=(s,r=document)=>r.querySelector(s),$$=(s,r=document)=>[...r.querySelectorAll(s)];
const toast=$('#toast');function say(msg){if(!toast)return;toast.textContent=msg;toast.classList.add('show');clearTimeout(window.__t);window.__t=setTimeout(()=>toast.classList.remove('show'),1500)}
function selectPlace(id){const p=places[id];if(!p)return;$$('.pin').forEach(el=>el.classList.toggle('active',el.dataset.id==id));const t=$('#drawerTitle');if(t)t.textContent=p.name;const th=$('#drawer .thumb');if(th){th.className='thumb '+p.thumb;th.innerHTML='<div class="badge">'+p.badge+'</div>'}const d=$('#drawer');if(d)d.classList.add('show')}
$$('.pin,.card[data-id]').forEach(el=>el.addEventListener('click',e=>{e.stopPropagation();selectPlace(el.dataset.id)}));
const drawerClose=$('#drawerClose');if(drawerClose)drawerClose.onclick=()=>$('#drawer')?.classList.remove('show');
$$('.chip').forEach(c=>c.onclick=()=>{c.classList.toggle('active');say(c.textContent+'篩選已更新')});
$$('.save,.save-action').forEach(b=>b.onclick=e=>{e.preventDefault();e.stopPropagation();const on=b.dataset.saved==='1';b.dataset.saved=on?'0':'1';b.textContent=on?'♡ 收藏':'♥ 已收藏';say(on?'已取消收藏':'已收藏到「我的腹地」')});
const saveBtn=$('#saveBtn');if(saveBtn)saveBtn.onclick=e=>{e.currentTarget.textContent=e.currentTarget.textContent.includes('♡')?'♥ 已收藏':'♡ 收藏';say('收藏狀態已更新')};
const discussBtn=$('#discussBtn');if(discussBtn)discussBtn.onclick=()=>location.href='forum.html';
function randomPlace(){const ids=Object.keys(places);const id=ids[Math.floor(Math.random()*ids.length)];return places[id]}
function randomPick(){const p=randomPlace();if($('#drawer')){const id=Object.keys(places).find(k=>places[k]===p);selectPlace(id)}say('今天就吃：'+p.name)}
const randomBtn=$('#randomBtn');if(randomBtn)randomBtn.onclick=randomPick;
const heroRandom=$('#heroRandom');if(heroRandom)heroRandom.onclick=randomPick;
const locateBtn=$('#locateBtn');if(locateBtn)locateBtn.onclick=()=>say('示意定位完成');
const search=$('#searchInput');if(search)search.addEventListener('keydown',e=>{if(e.key==='Enter'){const q=search.value.trim();if(!q)return;const hit=Object.entries(places).find(([id,p])=>(p.name+p.type+p.area+p.badge).includes(q));if(hit){selectPlace(hit[0]);say('找到：'+hit[1].name)}else say('Prototype：條件搜尋下一階段接資料庫')}});
window.addEventListener('keydown',e=>{if((e.metaKey||e.ctrlKey)&&e.key.toLowerCase()==='k'){e.preventDefault();(search||$('#homeSearch'))?.focus()}});
const wrap=$('#mapWrap'),svg=$('#mapSvg');if(wrap&&svg){let scale=1,tx=0,ty=0,drag=false,sx=0,sy=0,bx=0,by=0;const apply=()=>svg.style.transform='translate('+tx+'px,'+ty+'px) scale('+scale+')';wrap.addEventListener('wheel',e=>{e.preventDefault();scale=Math.max(.9,Math.min(1.45,scale+(e.deltaY<0?.08:-.08)));apply()},{passive:false});wrap.addEventListener('pointerdown',e=>{if(e.target.closest('button'))return;drag=true;sx=e.clientX;sy=e.clientY;bx=tx;by=ty;wrap.setPointerCapture(e.pointerId);wrap.classList.add('dragging')});wrap.addEventListener('pointermove',e=>{if(!drag)return;tx=bx+(e.clientX-sx);ty=by+(e.clientY-sy);apply()});wrap.addEventListener('pointerup',()=>{drag=false;wrap.classList.remove('dragging')})}
const homeSearch=$('#homeSearch'),homeSearchBtn=$('#homeSearchBtn');function goExplore(){const q=homeSearch?.value.trim()||'';location.href='explore.html'+(q?'?q='+encodeURIComponent(q):'')}if(homeSearchBtn)homeSearchBtn.onclick=goExplore;if(homeSearch)homeSearch.addEventListener('keydown',e=>{if(e.key==='Enter')goExplore()});
$$('.quick').forEach(b=>b.onclick=()=>{if(homeSearch)homeSearch.value=b.textContent;goExplore()});
const decisionName=$('#decisionName'),decisionMeta=$('#decisionMeta'),shuffle=$('#decisionShuffle');if(shuffle)shuffle.onclick=()=>{const p=randomPlace();decisionName.textContent=p.name;decisionMeta.textContent=p.distance+' · 排 '+p.queue+' · 再訪 '+p.revisit;say('換一間：'+p.name)};
const composerBtn=$('#composerBtn');if(composerBtn)composerBtn.onclick=()=>say('Prototype：發文編輯器下一步接後端');
