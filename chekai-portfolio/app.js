const SECTIONS = [
  {id:'about',no:'01',title:'ABOUT',theme:'hero',x:0,y:-180,z:130,w:360,h:650,d:120,ry:0,
   lede:'林哲愷 / Che-Kai Lin。這座中央塔是整個個人網站的入口：以文字、設計、學習與公共參與構成一個持續成長的個人檔案。',
   preview:['林哲愷 / CHE-KAI LIN','WRITER × DESIGNER × STUDENT','Culture · Design · Ideas'],
   items:[['Identity','WRITER X DESIGNER X STUDENT'],['Focus','Web Design · Visual Culture · Writing · Art · Public Affairs'],['Direction','Culture-led digital work with a clear visual system.'],['Archive','Personal projects, experiences, learning and public life.']]},
  {id:'web',no:'02',title:'WEB WORKS',theme:'dark',x:-640,y:-205,z:-20,w:500,h:600,d:150,ry:13,
   lede:'網站作品集中在左側數位大樓。每個專案之後都可以再做成可點擊的獨立作品頁。',
   preview:['SignWell 欣緯生醫','Tai-Wan Way 閒台文','CITYMUS','健人'],
   items:[['SignWell / 欣緯生醫','醫療、產業內容與編輯感導向的數位平台。'],['Tai-Wan Way / 閒台文','外國人學中文的互動網站，結合台灣文化、語音與遊戲化。'],['CITYMUS','音樂、城市與視覺氛圍導向的數位品牌實驗。'],['健人','網站概念與視覺研究專案。']]},
  {id:'experience',no:'03',title:'EXPERIENCE',theme:'dark',x:-700,y:250,z:-170,w:470,h:430,d:140,ry:10,
   lede:'文字刊載、文學參與與企劃經驗放在同一棟 Experience 大樓。',
   preview:['Newtalk 新頭殼 投書刊載','基隆海洋文學大賽 參與','台灣聯合大學企劃 參與'],
   items:[['Newtalk 新頭殼 投書刊載','公開投書刊載經歷。'],['基隆海洋文學大賽 參與','文學競賽參與經歷。'],['台灣聯合大學企劃 參與','企劃與專案參與經歷。']]},
  {id:'academic',no:'04',title:'ACADEMIC',theme:'paper',x:640,y:-205,z:-30,w:500,h:570,d:150,ry:-12,
   lede:'把不同校系的培育與先修經驗集中成 Academic Tower，避免散落在整張畫面。',
   preview:['台英學士培育計劃','中央大學人工智慧學系先修課程','清華大學經濟系先修課程','中原大學先修課程'],
   items:[['台英學士培育計劃','培育計畫參與。'],['國立中央大學人工智慧學系先修課程','人工智慧領域先修。'],['國立清華大學經濟系先修課程','經濟領域先修。'],['私立中原大學先修課程','大學先修課程。']]},
  {id:'writing',no:'05',title:'WRITING',theme:'paper',x:890,y:-115,z:-260,w:390,h:500,d:130,ry:-15,
   lede:'Writing 看板保留成內容創作入口，未來可以直接連到文章或作品全文。',
   preview:['文章創作','時事觀察','散文 / 隨筆','競賽作品'],
   items:[['文章創作','長短篇文字作品。'],['時事觀察','公共議題與社會觀察。'],['散文 / 隨筆','個人書寫與生活觀察。'],['競賽作品','文學競賽與主題創作。']]},
  {id:'running',no:'06',title:'RUNNING',theme:'dark',x:510,y:245,z:-110,w:390,h:410,d:130,ry:-10,
   lede:'跑步與競賽另外成一棟低樓層建築，和學術、社團履歷分開。',
   preview:['烘爐地定向越野 9K組完賽','基隆半程馬拉松 9K組完賽','103 / 1581'],
   items:[['烘爐地定向越野 9K組完賽','9K 組完賽。'],['基隆半程馬拉松 9K組完賽（103/1581）','完賽紀錄。']]},
  {id:'roles',no:'07',title:'ROLES',theme:'paper',x:825,y:255,z:-290,w:430,h:470,d:140,ry:-14,
   lede:'公司、創辦與學生社團角色集中於 Roles Building；點開後顯示完整清單。',
   preview:['欣緯科技有限公司董事','欣緯生醫創辦人','閒台文創辦人','CITYMUS 創辦人'],
   items:[['欣緯科技有限公司董事','公司治理與發展方向相關角色。'],['欣緯生醫創辦人','品牌與平台創辦角色。'],['閒台文創辦人','語言與文化平台創辦角色。'],['CITYMUS創辦人','音樂與數位品牌創辦角色。'],['市三重見賢思琪社 創社副社長、美萱','創社與社團組織經歷。'],['市三重高中前扶輪少年團團員','學生社團參與經歷。']]},
  {id:'public',no:'08',title:'PUBLIC',theme:'paper',x:1090,y:245,z:-520,w:330,h:440,d:120,ry:-17,
   lede:'公共參與以履歷紀錄方式呈現，和作品、學術內容保持明確分區。',
   preview:['台灣民眾黨青年團第二屆員','日本自民黨來台接待','核三公投街頭宣講、車掃'],
   items:[['台灣民眾黨青年團第二屆員','青年政治與公共事務參與經歷。'],['日本自民黨來台接待','來台交流接待參與。'],['核三公投街頭宣講、車掃','公共議題宣講與行動參與。']]},
  {id:'art',no:'09',title:'ART ARCHIVE',theme:'dark',x:-1080,y:245,z:-500,w:330,h:420,d:120,ry:17,
   lede:'藝術作品與視覺素材的收藏入口，之後可換成你的真實作品圖與作品內頁。',
   preview:['設計作品','手繪創作','攝影紀錄','靈感收藏','未來計劃'],
   items:[['設計作品','視覺與平面設計。'],['手繪創作','手繪與圖像作品。'],['攝影紀錄','攝影與日常影像。'],['靈感收藏','視覺研究與參考。'],['未來計劃','尚在形成中的作品與方向。']]}
];
const viewport=document.getElementById('viewport'),camera=document.getElementById('camera'),city=document.getElementById('city'),buildings=document.getElementById('buildings');
const rail=document.getElementById('rail'),drawer=document.getElementById('drawer'),drawerClose=document.getElementById('drawerClose');
const drawerNo=document.getElementById('drawerNo'),drawerTitle=document.getElementById('drawerTitle'),drawerLede=document.getElementById('drawerLede'),drawerList=document.getElementById('drawerList');
const focusLabel=document.getElementById('focusLabel'),modelBtn=document.getElementById('modelBtn'),resetBtn=document.getElementById('resetBtn');
let state={yaw:0,pitch:-4,zoom:-235,panX:0,panY:-68,drag:false,lastX:0,lastY:0,moved:false,selected:null};
function px(n){return `${n}px`}
function renderBuildings(){buildings.innerHTML='';rail.innerHTML='';SECTIONS.forEach(s=>{const b=document.createElement('article');b.className='building';b.dataset.id=s.id;const hw=s.w/2,hh=s.h/2,hd=s.d/2;b.style.cssText=`--x:${px(s.x)};--y:${px(s.y)};--z:${px(s.z)};--w:${px(s.w)};--h:${px(s.h)};--d:${px(s.d)};--hw:${px(hw)};--hh:${px(hh)};--hd:${px(hd)};--bfz:${px(hd+7)};--ry:${s.ry}deg;`;const themeClass=s.theme==='hero'?'red':(s.theme==='dark'?'dark':'');const preview=s.preview.slice(0,5).map(x=>`<div>${x}</div>`).join('');b.innerHTML=`<div class="volume"><div class="face front"></div><div class="face back"></div><div class="face left"></div><div class="face right"></div><div class="face top"></div></div><div class="coord-tag">${s.id} · x${s.x} y${s.y} z${s.z}</div><button class="billboard ${s.theme==='hero'?'hero-board':''}" aria-label="Open ${s.title}"><div class="board ${themeClass}"><div class="board-inner"><div class="board-no">${s.no}</div><div class="board-title">${s.id==='about'?'CHE-KAI LIN':s.title}</div><div class="board-kicker">${s.id==='about'?'WRITER × DESIGNER × STUDENT':'CLICK TO EXPLORE'}</div><div class="preview">${preview}</div><span class="enter">OPEN</span></div></div></button>`;b.querySelector('.billboard').addEventListener('click',e=>{if(state.moved)return;e.stopPropagation();selectSection(s.id,true)});buildings.appendChild(b);const rb=document.createElement('button');rb.textContent=s.no;rb.title=s.title;rb.dataset.id=s.id;rb.addEventListener('click',()=>selectSection(s.id,true));rail.appendChild(rb)})}
function applyCamera(){const responsive=window.innerWidth<700?.56:(window.innerWidth<1050?.69:.80);camera.style.transform=`translate3d(${state.panX}px,${state.panY}px,${state.zoom}px) rotateX(${state.pitch}deg) rotateY(${state.yaw}deg) scale(${responsive})`}
function setActive(id){document.querySelectorAll('.building').forEach(b=>{b.classList.toggle('selected',b.dataset.id===id);b.classList.toggle('dim',id&&b.dataset.id!==id)});rail.querySelectorAll('button').forEach(b=>b.classList.toggle('active',b.dataset.id===id));focusLabel.textContent=id?(SECTIONS.find(s=>s.id===id)?.title||id):'Central Plaza'}
function openDrawer(s){drawerNo.textContent=s.no;drawerTitle.textContent=s.title;drawerLede.textContent=s.lede;drawerList.innerHTML=s.items.map(([a,b])=>`<div class="detail"><b>${a}</b><span>${b}</span></div>`).join('');drawer.classList.add('open');drawer.setAttribute('aria-hidden','false')}
function selectSection(id,open=true){const s=SECTIONS.find(x=>x.id===id);if(!s)return;state.selected=id;setActive(id);state.yaw=Math.max(-17,Math.min(17,-s.x/105));state.pitch=-3.5;state.zoom=40;state.panX=-s.x*.16;state.panY=-s.y*.11;applyCamera();if(open)openDrawer(s);history.replaceState(null,'','#'+id)}
function resetView(){state.selected=null;state.yaw=0;state.pitch=-4;state.zoom=-235;state.panX=0;state.panY=-68;drawer.classList.remove('open');drawer.setAttribute('aria-hidden','true');setActive(null);applyCamera();history.replaceState(null,' ',location.pathname+location.search)}
drawerClose.addEventListener('click',()=>{drawer.classList.remove('open');drawer.setAttribute('aria-hidden','true')});resetBtn.addEventListener('click',resetView);modelBtn.addEventListener('click',()=>{city.classList.toggle('model');modelBtn.classList.toggle('on',city.classList.contains('model'))});
viewport.addEventListener('pointerdown',e=>{if(e.target.closest('button'))return;state.drag=true;state.lastX=e.clientX;state.lastY=e.clientY;state.moved=false;viewport.classList.add('dragging');viewport.setPointerCapture?.(e.pointerId)});viewport.addEventListener('pointermove',e=>{if(!state.drag)return;const dx=e.clientX-state.lastX,dy=e.clientY-state.lastY;if(Math.abs(dx)+Math.abs(dy)>2)state.moved=true;state.yaw+=dx*.075;state.pitch-=dy*.045;state.yaw=Math.max(-24,Math.min(24,state.yaw));state.pitch=Math.max(-11,Math.min(6,state.pitch));state.lastX=e.clientX;state.lastY=e.clientY;applyCamera()});function endDrag(){state.drag=false;viewport.classList.remove('dragging');setTimeout(()=>state.moved=false,0)}viewport.addEventListener('pointerup',endDrag);viewport.addEventListener('pointercancel',endDrag);viewport.addEventListener('wheel',e=>{state.zoom-=e.deltaY*.48;state.zoom=Math.max(-420,Math.min(360,state.zoom));applyCamera();e.preventDefault()},{passive:false});viewport.addEventListener('dblclick',resetView);window.addEventListener('keydown',e=>{if(e.key==='Escape'){drawer.classList.remove('open');drawer.setAttribute('aria-hidden','true')}if(e.key==='r'||e.key==='R')resetView();if(e.key==='m'||e.key==='M'){city.classList.toggle('model');modelBtn.classList.toggle('on',city.classList.contains('model'))}});window.addEventListener('resize',applyCamera);renderBuildings();applyCamera();const initial=location.hash.slice(1);if(SECTIONS.some(s=>s.id===initial))setTimeout(()=>selectSection(initial,false),120);
