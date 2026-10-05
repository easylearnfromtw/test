const places={
1:{name:'巷口牛肉麵研究所',type:'牛肉麵',area:'三重',distance:'450m',price:'$',rating:'4.8',queue:'10 分',revisit:'93%',thumb:'noodle',badge:'Bib Gourmand'},
2:{name:'河岸咖啡室',type:'咖啡',area:'三重',distance:'800m',price:'$$',rating:'4.6',queue:'0 分',revisit:'88%',thumb:'cafe',badge:'適合聊天'},
3:{name:'小鍋計畫',type:'個人鍋',area:'中山',distance:'2.1km',price:'$$',rating:'4.7',queue:'35 分',revisit:'91%',thumb:'hotpot',badge:'2026 新進榜'},
4:{name:'南城鵝肉攤',type:'台菜',area:'大安',distance:'3.0km',price:'$$',rating:'4.5',queue:'15 分',revisit:'89%',thumb:'noodle',badge:'在地常客'},
5:{name:'夜行飯糰',type:'宵夜',area:'松山',distance:'4.8km',price:'$',rating:'4.4',queue:'5 分',revisit:'84%',thumb:'hotpot',badge:'23:00 後'},
6:{name:'木日甜點室',type:'甜點',area:'大安',distance:'3.4km',price:'$$',rating:'4.9',queue:'20 分',revisit:'95%',thumb:'cafe',badge:'社群熱門'}
};
const toast=document.getElementById('toast'); function say(msg){toast.textContent=msg;toast.classList.add('show');clearTimeout(window.__t);window.__t=setTimeout(()=>toast.classList.remove('show'),1600)}
function selectPlace(id){const p=places[id]; if(!p)return; document.querySelectorAll('.pin').forEach(el=>el.classList.toggle('active',el.dataset.id==id)); document.getElementById('drawerTitle').textContent=p.name; const th=document.querySelector('#drawer .thumb'); th.className='thumb '+p.thumb; th.innerHTML='<div class="badge">'+p.badge+'</div>'; document.getElementById('drawer').classList.add('show');}
document.querySelectorAll('.pin,.card[data-id]').forEach(el=>el.addEventListener('click',e=>{e.stopPropagation();selectPlace(el.dataset.id)}));
document.getElementById('drawerClose').onclick=()=>document.getElementById('drawer').classList.remove('show');
document.querySelectorAll('.chip').forEach(c=>c.onclick=()=>{c.classList.toggle('active');say(c.textContent+'篩選已更新')});
document.querySelectorAll('.save').forEach(b=>b.onclick=e=>{e.stopPropagation();b.textContent=b.textContent==='♡'?'♥':'♡';say(b.textContent==='♥'?'已收藏到「我的腹地」':'已取消收藏')});
document.getElementById('saveBtn').onclick=e=>{e.currentTarget.textContent=e.currentTarget.textContent.includes('♡')?'♥ 已收藏':'♡ 收藏';say('收藏狀態已更新')};
document.getElementById('discussBtn').onclick=()=>say('Prototype：討論串頁下一版接上');
function randomPick(){const ids=Object.keys(places);const id=ids[Math.floor(Math.random()*ids.length)];selectPlace(id);say('今天就吃：'+places[id].name)}
document.getElementById('randomBtn').onclick=randomPick;document.getElementById('heroRandom').onclick=randomPick;
document.getElementById('locateBtn').onclick=()=>say('示意定位：三重 · 光明生活圈');
const search=document.getElementById('searchInput');search.addEventListener('keydown',e=>{if(e.key==='Enter'){const q=search.value.trim();if(!q)return; const hit=Object.entries(places).find(([id,p])=>(p.name+p.type+p.area+p.badge).includes(q)); if(hit){selectPlace(hit[0]);say('找到：'+hit[1].name)}else say('Prototype：AI 條件搜尋下一階段接上')}});
window.addEventListener('keydown',e=>{if((e.metaKey||e.ctrlKey)&&e.key.toLowerCase()==='k'){e.preventDefault();search.focus()}});
const wrap=document.getElementById('mapWrap'),svg=document.getElementById('mapSvg');let scale=1,tx=0,ty=0,drag=false,sx=0,sy=0,bx=0,by=0;
function apply(){svg.style.transform='translate('+tx+'px,'+ty+'px) scale('+scale+')'}
wrap.addEventListener('wheel',e=>{e.preventDefault();scale=Math.max(.9,Math.min(1.45,scale+(e.deltaY<0?.08:-.08)));apply()},{passive:false});
wrap.addEventListener('pointerdown',e=>{if(e.target.closest('button'))return;drag=true;sx=e.clientX;sy=e.clientY;bx=tx;by=ty;wrap.setPointerCapture(e.pointerId);wrap.classList.add('dragging')});
wrap.addEventListener('pointermove',e=>{if(!drag)return;tx=bx+(e.clientX-sx);ty=by+(e.clientY-sy);apply()});
wrap.addEventListener('pointerup',()=>{drag=false;wrap.classList.remove('dragging')});