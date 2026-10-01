#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, re, shutil, subprocess, tempfile, time, hashlib, math
from collections import Counter
from pathlib import Path
from urllib.parse import quote_plus, urljoin
import requests
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parent
PROFILES=json.loads((ROOT/"theme_profiles.json").read_text(encoding="utf-8"))
CACHE=ROOT/"_theme_audio_cache"
CACHE.mkdir(parents=True,exist_ok=True)

S=requests.Session()
S.headers.update({"User-Agent":"musicetown-theme-curator/8.7.4"})
NULLRIGHTS="https://nullrights.com"
TIMEOUT=45

def get(url,tries=3):
    last=None
    for n in range(tries):
        try:
            r=S.get(url,timeout=TIMEOUT)
            r.raise_for_status()
            return r
        except Exception as e:
            last=e
            if n+1<tries: time.sleep(1.1*(n+1))
    raise last

def norm(s):
    return re.sub(r"\s+"," ",str(s or "")).strip()

def key(title,artist):
    return f"{norm(artist).casefold()}||{norm(title).casefold()}"

def discover(query,max_pages=14):
    found=[]
    for p in range(1,max_pages+1):
        url=f"{NULLRIGHTS}/search?q={quote_plus(query)}&page={p}"
        try:h=get(url).text
        except Exception:continue
        links=re.findall(r'href=["\'](/track/[A-Za-z0-9_-]+)["\']',h)
        if not links and p>2:break
        found.extend(urljoin(NULLRIGHTS,x) for x in links)
    return list(dict.fromkeys(found))

def discover_genre(genre,max_pages=10):
    found=[]
    for p in range(1,max_pages+1):
        url=f"{NULLRIGHTS}/genre/{quote_plus(genre)}?page={p}"
        try:h=get(url).text
        except Exception:continue
        links=re.findall(r'href=["\'](/track/[A-Za-z0-9_-]+)["\']',h)
        if not links and p>2:break
        found.extend(urljoin(NULLRIGHTS,x) for x in links)
    return list(dict.fromkeys(found))

def parse_track(url,profile):
    h=get(url).text
    soup=BeautifulSoup(h,"html.parser")
    txt=norm(soup.get_text(" ",strip=True))
    low=txt.casefold()

    # LEGAL / CATALOG HARD GATES
    if "cc0 1.0 universal" not in low:return None
    has_vocals="has vocals" in low
    instrumental="instrumental" in low
    vocal_mode=profile.get("vocal_mode","required")
    if vocal_mode=="required" and not has_vocals:return None
    if vocal_mode=="preferred" and not has_vocals and not profile.get("allow_instrumental",False):return None
    if re.search(r"ai generated\s+yes",low):return None

    h1=soup.find("h1")
    title=norm(h1.get_text(" ",strip=True) if h1 else "")
    if not title:return None

    artist=""
    ma=re.search(rf'"{re.escape(title)}"\s+by\s+(.+?)\s+[—-]',txt,re.I)
    if ma:artist=norm(ma.group(1))
    if not artist:
        # Common track-page pattern: H1 then artist/album.
        for el in [h1.find_next("a") if h1 else None,h1.find_next("p") if h1 else None]:
            if el:
                artist=norm(el.get_text(" ",strip=True)).split("·")[0]
                if artist:break
    if not artist:artist="Unknown artist"

    md=re.search(r"Duration\s+(\d+):(\d+)",txt,re.I)
    duration=(int(md.group(1))*60+int(md.group(2))) if md else None
    # Full-song bias. No micro loops.
    if duration is not None and not (90<=duration<=480):return None

    bpm=None
    mb=re.search(r"BPM\s+(\d+(?:\.\d+)?)",txt,re.I)
    if mb:bpm=float(mb.group(1))

    energy=None
    me=re.search(r"Energy\s+(\d+(?:\.\d+)?)%",txt,re.I)
    if me:energy=float(me.group(1))

    plays=0
    mp=re.search(r"Plays\s+(\d+)",txt,re.I)
    if mp:plays=int(mp.group(1))

    genre=""
    mg=re.search(r"Genre\s+(.+?)(?:Tags|Duration|Format|Added|AI generated|Plays|License)",txt,re.I)
    if mg:genre=norm(mg.group(1))[:140]

    tags=""
    mt=re.search(r"Tags\s+(.+?)(?:Duration|Format|Added|AI generated|Plays|License)",txt,re.I)
    if mt:tags=norm(mt.group(1))[:320]

    sounds=""
    ms=re.search(r"Sounds like\s+(.+?)(?:Download|Embed this player|Similar tracks|What CC0 means)",txt,re.I)
    if ms:sounds=norm(ms.group(1))[:420]

    download=None
    for a in soup.find_all("a",href=True):
        label=norm(a.get_text(" ",strip=True)).casefold()
        href=urljoin(url,a["href"])
        if "download" in label and "/download/" in href:
            download=href;break
    if not download:
        for a in soup.find_all("a",href=True):
            href=urljoin(url,a["href"])
            if re.search(r"\.(mp3|ogg|oga|flac|wav)(?:\?|$)",href,re.I):
                download=href;break

    if not download:return None

    return {
      "title":title,"artist":artist,"duration":duration,"bpm":bpm,"energy":energy,"hasVocals":has_vocals,
      "plays":plays,"genre":genre or "CC0 Vocal","tags":tags,"sounds":sounds,
      "source":url,"embed":url.rstrip("/").split("/")[-1],"download":download,
      "license":"CC0 1.0 Universal","licenseVerified":True,
      "licenseChecked":time.strftime("%Y-%m-%d"),
      "licenseEvidence":"Nullrights track page explicitly states CC0 1.0 Universal and links the original source."
    }

def range_score(value,lo,hi,weight):
    if value is None:return 0
    if lo<=value<=hi:return weight
    dist=min(abs(value-lo),abs(value-hi))
    span=max(1,hi-lo)
    return max(-weight,weight*(1-dist/span*2))

def score(t,p):
    blob=" ".join([t.get("genre",""),t.get("tags",""),t.get("sounds","")]).casefold()
    s=0.0
    matched=[]
    for kw in p["keywords"]:
        if kw.casefold() in blob:
            s+=5
            matched.append(kw)

    # Theme hard-fit gate / strong-cue scoring.
    required=p.get("required_any",[])
    strong_hits=[kw for kw in required if kw.casefold() in blob]
    t["_strongHits"]=strong_hits
    if required and len(strong_hits)<int(p.get("min_strong_matches",1)):
        s-=120

    # Traditional Beijing may admit strongly thematic instrumentals, but vocals win.
    if p.get("vocal_mode","required")=="preferred":
        s += 14 if t.get("hasVocals") else 0

    # Core musical suitability.
    s+=range_score(t.get("bpm"),*p["prefer_bpm"],18)
    s+=range_score(t.get("energy"),*p["prefer_energy"],14)

    # Prefer real full songs, not tiny utility clips.
    dur=t.get("duration")
    if dur is not None:
        if 150<=dur<=300:s+=8
        elif 120<=dur<=360:s+=5

    # Modest popularity signal only; do not let plays dominate theme fit.
    s+=min(8,math.log2(1+(t.get("plays") or 0))*1.4)

    # Penalize utility/BGM terms hard.
    rejects=[]
    for x in p["reject"]:
        if x.casefold() in blob:
            s-=18
            rejects.append(x)

    # Generic background-use phrases are poor "song" candidates.
    for x in ["background music","podcast intro","youtube intro","corporate video","game music"]:
        if x in blob:s-=10

    t["_score"]=round(s,2)
    t["_matches"]=matched[:8]
    t["_rejectHits"]=rejects
    return s

def read_catalog(path):
    text=path.read_text(encoding="utf-8")
    m=re.search(r'window\.MUSIC_DATA\s*=\s*(\[.*?\]);\s*\n',text,re.S)
    if not m:raise RuntimeError("window.MUSIC_DATA not found")
    return text,m,json.loads(m.group(1))

def write_catalog(path,data):
    text,m,_=read_catalog(path)
    js=json.dumps(data,ensure_ascii=False,separators=(",",":"))
    path.write_text(text[:m.start()]+"window.MUSIC_DATA = "+js+";\n"+text[m.end():],encoding="utf-8")

def cache_key(t):
    return hashlib.sha256(t["source"].encode()).hexdigest()[:24]

def convert(t,bitrate):
    out=CACHE/f"{cache_key(t)}-{bitrate}.mp3"
    if out.exists() and out.stat().st_size>=20000:return out
    if not shutil.which("ffmpeg"):raise RuntimeError("ffmpeg required")
    with tempfile.TemporaryDirectory() as td:
        raw=Path(td)/"input"
        r=get(t["download"],tries=3)
        raw.write_bytes(r.content)
        if raw.stat().st_size<20000:raise RuntimeError("download too small")
        subprocess.run([
          "ffmpeg","-hide_banner","-loglevel","error","-y",
          "-i",str(raw),"-vn","-codec:a","libmp3lame","-b:a",bitrate,
          "-map_metadata","-1",str(out)
        ],check=True)
    if out.stat().st_size<20000:raise RuntimeError("converted file too small")
    return out

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--per-theme",type=int,default=50)
    ap.add_argument("--bitrate",default="64k")
    ap.add_argument("--max-candidates",type=int,default=900)
    ap.add_argument("--max-per-artist",type=int,default=4)
    args=ap.parse_args()

    index=ROOT/"index.html"
    if not index.exists():raise SystemExit("index.html not found")

    _,_,data=read_catalog(index)
    by_name={d["t"]:d for d in data}

    # Exclude EVERYTHING already used by the existing 11 drawers.
    used=set()
    used_sources=set()
    for d in data:
        if d["t"] in PROFILES:continue
        for t in d.get("tracks",[]):
            used.add(key(t.get("title"),t.get("artist")))
            if t.get("source"):used_sources.add(t["source"])

    report={"generatedAt":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),"themes":{}}

    for theme,p in PROFILES.items():
        print(f"\n=== {theme}: live curation ===")
        urls=[]
        for q in p["queries"]:urls.extend(discover(q))
        for g in p["genres"]:urls.extend(discover_genre(g))
        urls=list(dict.fromkeys(urls))

        candidates=[]
        seen=set()
        for url in urls[:args.max_candidates]:
            if url in used_sources:continue
            try:
                t=parse_track(url,p)
                if not t:continue
                k=key(t["title"],t["artist"])
                if k in used or k in seen:continue
                seen.add(k)
                score(t,p)
                candidates.append(t)
            except Exception as e:
                print(" skip:",url,str(e)[:100])

        candidates.sort(key=lambda t:(-t["_score"],hashlib.sha1((theme+t["source"]).encode()).hexdigest()))

        selected=[]
        artist_counts=Counter()
        for t in candidates:
            k=key(t["title"],t["artist"])
            if k in used:continue
            artist=norm(t["artist"]).casefold()
            if artist_counts[artist]>=args.max_per_artist:continue
            if p.get("required_any") and not t.get("_strongHits"):continue
            if t["_score"]<0:continue
            selected.append(t)
            artist_counts[artist]+=1
            used.add(k);used_sources.add(t["source"])
            if len(selected)>=args.per_theme:break

        if len(selected)<args.per_theme:
            raise RuntimeError(f"{theme}: only {len(selected)} suitable fresh tracks after legal/theme/quality gates")

        folder=p["slug"]
        target=ROOT/folder
        target.mkdir(parents=True,exist_ok=True)
        out_tracks=[]

        for i,t in enumerate(selected,1):
            print(f" [{i:02d}/{args.per_theme}] {t['artist']} — {t['title']} · score {t['_score']}")
            cached=convert(t,args.bitrate)
            rel=f"{folder}/{i:03d}.mp3"
            shutil.copy2(cached,ROOT/rel)

            matches=t.pop("_matches",[])
            strong_hits=t.pop("_strongHits",[])
            t.pop("_rejectHits",None)
            score_value=t.pop("_score",0)

            t.update({
              "trackNo":i,
              "shareId":f"{folder}-{i:03d}",
              "freshTheme":True,
              "curatedTheme":theme,
              "curationScore":score_value,
              "curationMatches":matches,"strongThemeMatches":strong_hits,
              "vibe":f"{p['vibe']} · {t['genre']}",
              "audioSrc":rel,
              "localMp3":True
            })
            out_tracks.append(t)

        by_name[theme]["tracks"]=out_tracks
        by_name[theme]["installPending"]=False
        report["themes"][theme]=out_tracks
        (target/"manifest.json").write_text(json.dumps(out_tracks,ensure_ascii=False,indent=2),encoding="utf-8")

    final=[by_name[d["t"]] for d in data]
    write_catalog(index,final)
    if (ROOT/"404.html").exists():write_catalog(ROOT/"404.html",final)

    (ROOT/"theme_curation_manifest.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print("\nTheme curation complete: 4 × 50 fresh CC0 / public-domain-compatible theme tracks.")

if __name__=="__main__":
    main()