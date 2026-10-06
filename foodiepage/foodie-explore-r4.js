const places={
1:{name:'巷口牛肉麵研究所',type:'牛肉麵',area:'三重',distance:'450m',price:'$',rating:'4.8',queue:'10 分',revisit:'93%',thumb:'noodle',coords:[121.4869,25.0631]},
2:{name:'河岸咖啡室',type:'咖啡',area:'三重',distance:'800m',price:'$$',rating:'4.6',queue:'0 分',revisit:'88%',thumb:'cafe',coords:[121.4935,25.0554]},
3:{name:'小鍋計畫',type:'個人鍋',area:'中山',distance:'2.1km',price:'$$',rating:'4.7',queue:'35 分',revisit:'91%',thumb:'hotpot',coords:[121.5215,25.0568]},
4:{name:'南城鵝肉攤',type:'台菜',area:'大安',distance:'3.0km',price:'$$',rating:'4.5',queue:'15 分',revisit:'89%',thumb:'noodle',coords:[121.5364,25.0357]},
5:{name:'夜行飯糰',type:'宵夜',area:'松山',distance:'4.8km',price:'$',rating:'4.4',queue:'5 分',revisit:'84%',thumb:'hotpot',coords:[121.562,25.0498]},
6:{name:'木日甜點室',type:'甜點',area:'大安',distance:'3.4km',price:'$$',rating:'4.9',queue:'20 分',revisit:'95%',thumb:'cafe',coords:[121.5325,25.0273]}
};
const $=(s,r=document)=>r.querySelector(s),$$=(s,r=document)=>[...r.querySelectorAll(s)];
const toast=$('#toast');let foodieMap=null,userMarker=null,activeId='1';const markerEls=new Map();

function say(t){if(!toast)return;toast.textContent=t;toast.classList.add('show');clearTimeout(window.__toast);window.__toast=setTimeout(()=>toast.classList.remove('show'),1350)}
function setSheet(state){document.body.classList.remove('sheet-expanded','sheet-collapsed');if(state)document.body.classList.add(state)}
function syncSelection(id){
  activeId=String(id);
  markerEls.forEach((el,key)=>el.classList.toggle('active',String(key)===activeId));
  $$('.result-card[data-id]').forEach(card=>card.classList.toggle('selected',card.dataset.id===activeId));
}
function renderSelection(id){
  const p=places[id];if(!p)return;
  syncSelection(id);
  const title=$('#drawerTitle'),meta=$('#drawerMeta'),thumb=$('#drawerThumb');
  if(title)title.textContent=p.name;if(meta)meta.textContent=`${p.type} · ${p.price} · 排 ${p.queue}`;if(thumb)thumb.className='food-thumb '+p.thumb;
  $('#drawer')?.classList.add('show');
  const mt=$('#mobileSelectedTitle'),mm=$('#mobileSelectedMeta'),mi=$('#mobileSelectedThumb');
  if(mt)mt.textContent=p.name;if(mm)mm.textContent=`${p.area} · ${p.type} · 再訪 ${p.revisit}`;if(mi)mi.className='food-thumb '+p.thumb;
  const decision=$('#decisionPlace');if(decision)decision.textContent=p.name;
}
function selectPlace(id,{fly=true,expandMobile=true}={}){
  const p=places[id];if(!p)return;renderSelection(id);
  if(foodieMap&&fly)foodieMap.easeTo({center:p.coords,zoom:Math.max(foodieMap.getZoom(),14.7),duration:620});
  if(innerWidth<=980&&expandMobile)setSheet('sheet-expanded');
}
function randomPick(){
  const ids=Object.keys(places),id=ids[Math.floor(Math.random()*ids.length)];
  selectPlace(id);say('今天就吃：'+places[id].name)
}
function findPlace(q){
  const s=(q||'').trim().toLowerCase();if(!s)return null;
  return Object.entries(places).find(([,p])=>(p.name+p.type+p.area).toLowerCase().includes(s))||null
}

$$('.result-card[data-id]').forEach(card=>{
  card.addEventListener('click',()=>selectPlace(card.dataset.id));
  card.addEventListener('mouseenter',()=>markerEls.get(card.dataset.id)?.classList.add('hover'));
  card.addEventListener('mouseleave',()=>markerEls.get(card.dataset.id)?.classList.remove('hover'));
});
$$('.chip').forEach(chip=>chip.addEventListener('click',()=>{chip.classList.toggle('active');say(chip.textContent+'篩選已更新')}));
$('#randomBtn')?.addEventListener('click',randomPick);
$('#decisionShuffle')?.addEventListener('click',randomPick);

let sheetCycle=0;
$('#sheetToggle')?.addEventListener('click',()=>{
  sheetCycle=(sheetCycle+1)%3;
  setSheet(sheetCycle===1?'sheet-expanded':sheetCycle===2?'sheet-collapsed':'');
});

function tuneStyle(map){
  const layers=map.getStyle().layers||[];
  for(const layer of layers){
    const sl=layer['source-layer'];
    try{
      if(sl==='water'&&layer.type==='fill')map.setPaintProperty(layer.id,'fill-color','#cfdfe5');
      if(sl==='buildings'&&layer.type==='fill')map.setPaintProperty(layer.id,'fill-color','#ebe5dc');
      if(layer.type==='symbol'&&map.getPaintProperty(layer.id,'text-halo-color')!==undefined){
        map.setPaintProperty(layer.id,'text-halo-color','#f7f3ec');
        map.setPaintProperty(layer.id,'text-halo-width',1.2);
      }
    }catch(_){}
  }
}
function addMarkers(){
  Object.entries(places).forEach(([id,p])=>{
    const el=document.createElement('button');el.type='button';el.className='foodie-map-marker';el.dataset.id=id;
    el.setAttribute('aria-label',p.name+' 評分 '+p.rating);
    el.innerHTML=`<span class="foodie-marker-dot"></span><strong>${p.rating}</strong>`;
    el.addEventListener('click',e=>{e.stopPropagation();selectPlace(id,{fly:false})});
    new maplibregl.Marker({element:el,anchor:'bottom'}).setLngLat(p.coords).addTo(foodieMap);markerEls.set(id,el)
  })
}
function initMap(){
  const container=$('#realMap');if(!container)return;
  const fallback=$('#mapFallback');
  if(!window.maplibregl||!window.pmtiles||!window.basemaps){if(fallback)fallback.innerHTML='<span>地圖元件載入失敗，請重新整理。</span>';return}
  try{
    const protocol=new pmtiles.Protocol();maplibregl.addProtocol('pmtiles',protocol.tile);
    const lowPower=matchMedia('(prefers-reduced-motion: reduce)').matches||(navigator.hardwareConcurrency&&navigator.hardwareConcurrency<=4)||innerWidth<700;
    const tilesURL='https://build.protomaps.com/20260925.pmtiles';
    const style={version:8,glyphs:'https://protomaps.github.io/basemaps-assets/fonts/{fontstack}/{range}.pbf',sprite:'https://protomaps.github.io/basemaps-assets/sprites/v4/light',sources:{protomaps:{type:'vector',url:'pmtiles://'+tilesURL,attribution:'© OpenStreetMap contributors · Protomaps'}},layers:basemaps.layers('protomaps',basemaps.namedFlavor('light'),{lang:'zh-Hant'})};
    foodieMap=new maplibregl.Map({container:'realMap',style,center:[121.493,25.061],zoom:13.55,pitch:lowPower?0:12,bearing:0,minZoom:10,maxZoom:18,maxPitch:45,antialias:!lowPower,attributionControl:false,renderWorldCopies:false});
    foodieMap.dragRotate.disable();foodieMap.touchZoomRotate.enableRotation();
    foodieMap.on('load',()=>{
      fallback?.classList.add('hidden');tuneStyle(foodieMap);addMarkers();
      if(!lowPower){
        const before=(foodieMap.getStyle().layers||[]).find(l=>l.type==='symbol')?.id;
        try{foodieMap.addLayer({id:'foodie-buildings-3d',type:'fill-extrusion',source:'protomaps','source-layer':'buildings',minzoom:15.2,paint:{'fill-extrusion-color':'#e5ded5','fill-extrusion-height':['case',['has','height'],['get','height'],7],'fill-extrusion-base':['case',['has','min_height'],['get','min_height'],0],'fill-extrusion-opacity':0.48}},before)}catch(_){}
      }
      foodieMap.addControl(new maplibregl.ScaleControl({maxWidth:90,unit:'metric'}),'bottom-left');
      const q=new URLSearchParams(location.search).get('q');if(q){if($('#searchInput'))$('#searchInput').value=q;const hit=findPlace(q);if(hit)selectPlace(hit[0],{expandMobile:false});else renderSelection('1')}else renderSelection('1')
    });
    foodieMap.on('click',e=>{if(!e.originalEvent.target.closest?.('.foodie-map-marker'))$('#drawer')?.classList.remove('show')});
    foodieMap.on('moveend',()=>{$('#zoomValue')&&( $('#zoomValue').textContent=Math.round(foodieMap.getZoom())+'×' )});
    $('#zoomIn')?.addEventListener('click',()=>foodieMap.zoomIn({duration:250}));
    $('#zoomOut')?.addEventListener('click',()=>foodieMap.zoomOut({duration:250}));
    $('#resetView')?.addEventListener('click',()=>foodieMap.easeTo({center:[121.493,25.061],zoom:13.55,pitch:0,bearing:0,duration:500}));
    $('#locateBtn')?.addEventListener('click',()=>{
      if(!navigator.geolocation){say('此瀏覽器不支援定位');return}
      navigator.geolocation.getCurrentPosition(pos=>{
        const ll=[pos.coords.longitude,pos.coords.latitude];
        foodieMap.easeTo({center:ll,zoom:15.4,duration:700});
        if(userMarker)userMarker.remove();
        const dot=document.createElement('div');dot.className='user-location-dot';
        userMarker=new maplibregl.Marker({element:dot,anchor:'center'}).setLngLat(ll).addTo(foodieMap);say('已移到你目前的位置')
      },()=>say('無法取得定位'),{enableHighAccuracy:false,timeout:5000,maximumAge:60000})
    });
    $('#searchInput')?.addEventListener('keydown',e=>{if(e.key!=='Enter')return;const hit=findPlace(e.currentTarget.value);if(hit){selectPlace(hit[0]);say('找到：'+hit[1].name)}else say('目前 Demo 尚未接全台 POI 搜尋')});
  }catch(err){if(fallback)fallback.innerHTML='<span>地圖初始化失敗，請重新整理。</span>'}
}
initMap();