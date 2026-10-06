const places={
1:{name:'巷口牛肉麵研究所',type:'牛肉麵',area:'三重',distance:'450m',price:'$',rating:'4.8',queue:'10 分',revisit:'93%',thumb:'noodle',coords:[121.4869,25.0631]},
2:{name:'河岸咖啡室',type:'咖啡',area:'三重',distance:'800m',price:'$$',rating:'4.6',queue:'0 分',revisit:'88%',thumb:'cafe',coords:[121.4935,25.0554]},
3:{name:'小鍋計畫',type:'個人鍋',area:'中山',distance:'2.1km',price:'$$',rating:'4.7',queue:'35 分',revisit:'91%',thumb:'hotpot',coords:[121.5215,25.0568]},
4:{name:'南城鵝肉攤',type:'台菜',area:'大安',distance:'3.0km',price:'$$',rating:'4.5',queue:'15 分',revisit:'89%',thumb:'noodle',coords:[121.5364,25.0357]},
5:{name:'夜行飯糰',type:'宵夜',area:'松山',distance:'4.8km',price:'$',rating:'4.4',queue:'5 分',revisit:'84%',thumb:'hotpot',coords:[121.562,25.0498]},
6:{name:'木日甜點室',type:'甜點',area:'大安',distance:'3.4km',price:'$$',rating:'4.9',queue:'20 分',revisit:'95%',thumb:'cafe',coords:[121.5325,25.0273]}
};

const $=(s,r=document)=>r.querySelector(s),$$=(s,r=document)=>[...r.querySelectorAll(s)];
const toast=$('#toast');
let foodieMap=null;
const foodieMarkers=new Map();

function say(t){
  if(!toast)return;
  toast.textContent=t;
  toast.classList.add('show');
  clearTimeout(window.__t);
  window.__t=setTimeout(()=>toast.classList.remove('show'),1400);
}

function syncMarkerState(id){
  foodieMarkers.forEach((el,key)=>el.classList.toggle('active',String(key)===String(id)));
}

function selectPlace(id,{fly=true}={}){
  const p=places[id];
  if(!p)return;
  syncMarkerState(id);
  const t=$('#drawerTitle'),m=$('#drawerMeta'),th=$('#drawerThumb');
  if(t)t.textContent=p.name;
  if(m)m.textContent=`${p.type} · ${p.price} · 排 ${p.queue}`;
  if(th)th.className='food-thumb '+p.thumb;
  $('#drawer')?.classList.add('show');
  if(foodieMap&&fly){
    foodieMap.easeTo({center:p.coords,zoom:Math.max(foodieMap.getZoom(),14.8),duration:700});
  }
}

$$('.result-card[data-id]').forEach(el=>el.addEventListener('click',e=>{
  e.stopPropagation();
  selectPlace(el.dataset.id);
}));

$$('.chip').forEach(el=>el.onclick=()=>{
  el.classList.toggle('active');
  say(el.textContent+'篩選已更新');
});

function randomPlace(){
  const k=Object.keys(places);
  const id=k[Math.floor(Math.random()*k.length)];
  return [id,places[id]];
}

$('#randomBtn')?.addEventListener('click',()=>{
  const [id,p]=randomPlace();
  selectPlace(id);
  say('今天就吃：'+p.name);
});

const ds=$('#decisionShuffle');
if(ds)ds.onclick=()=>{
  const [,p]=randomPlace();
  $('#decisionName').textContent=p.name;
  $('#decisionMeta').textContent=`${p.distance} · 排 ${p.queue} · 再訪 ${p.revisit}`;
  say('換一間：'+p.name);
};

function goExplore(){
  const q=$('#homeSearch')?.value.trim()||'';
  location.href='explore.html'+(q?'?q='+encodeURIComponent(q):'');
}
$('#homeSearchBtn')?.addEventListener('click',goExplore);
$('#homeSearch')?.addEventListener('keydown',e=>{if(e.key==='Enter')goExplore()});
$$('.quick').forEach(b=>b.onclick=()=>{
  if($('#homeSearch'))$('#homeSearch').value=b.textContent;
  goExplore();
});

function findPlace(query){
  const q=(query||'').trim().toLowerCase();
  if(!q)return null;
  return Object.entries(places).find(([,p])=>
    (p.name+p.type+p.area).toLowerCase().includes(q)
  )||null;
}

function initRealMap(){
  const container=$('#realMap');
  if(!container)return;

  const fallback=$('#mapFallback');
  if(!window.maplibregl||!window.pmtiles||!window.basemaps){
    if(fallback)fallback.innerHTML='<span>地圖元件載入失敗，請重新整理。</span>';
    return;
  }

  try{
    const protocol=new pmtiles.Protocol();
    maplibregl.addProtocol('pmtiles',protocol.tile);

    const lowPower=
      matchMedia('(prefers-reduced-motion: reduce)').matches ||
      (navigator.hardwareConcurrency&&navigator.hardwareConcurrency<=4) ||
      innerWidth<700;

    const tilesURL='https://build.protomaps.com/20260925.pmtiles';
    const style={
      version:8,
      glyphs:'https://protomaps.github.io/basemaps-assets/fonts/{fontstack}/{range}.pbf',
      sprite:'https://protomaps.github.io/basemaps-assets/sprites/v4/light',
      sources:{
        protomaps:{
          type:'vector',
          url:'pmtiles://'+tilesURL,
          attribution:'© OpenStreetMap contributors · Protomaps'
        }
      },
      layers:basemaps.layers('protomaps',basemaps.namedFlavor('light'),{lang:'zh-Hant'})
    };

    foodieMap=new maplibregl.Map({
      container:'realMap',
      style,
      center:[121.4985,25.0615],
      zoom:13.35,
      pitch:lowPower?0:18,
      bearing:lowPower?0:-6,
      minZoom:10,
      maxZoom:18,
      maxPitch:50,
      antialias:!lowPower,
      attributionControl:false,
      renderWorldCopies:false
    });

    foodieMap.dragRotate.disable();
    foodieMap.touchZoomRotate.enableRotation();

    foodieMap.on('load',()=>{
      fallback?.classList.add('hidden');

      if(!lowPower){
        const layers=foodieMap.getStyle().layers||[];
        const before=layers.find(l=>l.type==='symbol')?.id;
        try{
          foodieMap.addLayer({
            id:'foodie-buildings-3d',
            type:'fill-extrusion',
            source:'protomaps',
            'source-layer':'buildings',
            minzoom:15.2,
            filter:['==',['get','kind'],'building'],
            paint:{
              'fill-extrusion-color':'#e4ddd3',
              'fill-extrusion-height':['case',['has','height'],['get','height'],8],
              'fill-extrusion-base':['case',['has','min_height'],['get','min_height'],0],
              'fill-extrusion-opacity':0.52
            }
          },before);
        }catch(_){}
      }

      Object.entries(places).forEach(([id,p])=>{
        const el=document.createElement('button');
        el.type='button';
        el.className='foodie-map-marker';
        el.dataset.id=id;
        el.setAttribute('aria-label',p.name+' 評分 '+p.rating);
        el.innerHTML=`<span class="foodie-marker-dot"></span><strong>${p.rating}</strong>`;
        el.addEventListener('click',e=>{
          e.stopPropagation();
          selectPlace(id,{fly:false});
        });
        new maplibregl.Marker({element:el,anchor:'bottom'}).setLngLat(p.coords).addTo(foodieMap);
        foodieMarkers.set(id,el);
      });

      const params=new URLSearchParams(location.search);
      const q=params.get('q');
      if(q){
        const input=$('#searchInput');
        if(input)input.value=q;
        const hit=findPlace(q);
        if(hit)selectPlace(hit[0]);
      }else{
        selectPlace('1',{fly:false});
      }
    });

    foodieMap.on('click',()=>$('#drawer')?.classList.remove('show'));

    const loadGuard=setTimeout(()=>{
      if(fallback&&!foodieMap.loaded()){
        fallback.innerHTML='<span>向量地圖載入較慢，請檢查網路後重新整理。</span>';
      }
    },10000);
    foodieMap.once('idle',()=>clearTimeout(loadGuard));

    $('#locateBtn')?.addEventListener('click',()=>{
      if(!navigator.geolocation){
        say('此瀏覽器不支援定位');
        return;
      }
      navigator.geolocation.getCurrentPosition(pos=>{
        foodieMap.easeTo({
          center:[pos.coords.longitude,pos.coords.latitude],
          zoom:15.2,
          duration:800
        });
        say('已移到你目前的位置');
      },()=>{
        foodieMap.easeTo({center:[121.4985,25.0615],zoom:13.35,duration:650});
        say('無法取得定位，已回到雙北示範區');
      },{enableHighAccuracy:false,timeout:5000,maximumAge:60000});
    });

    $('#searchInput')?.addEventListener('keydown',e=>{
      if(e.key!=='Enter')return;
      const hit=findPlace(e.currentTarget.value);
      if(hit){
        selectPlace(hit[0]);
        say('找到：'+hit[1].name);
      }else{
        say('目前 Demo 尚未接全台 POI 搜尋');
      }
    });

  }catch(err){
    if(fallback)fallback.innerHTML='<span>地圖初始化失敗，請重新整理。</span>';
  }
}

initRealMap();
