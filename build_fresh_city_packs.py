#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, re, shutil, subprocess, tempfile, time, hashlib
from pathlib import Path
from urllib.parse import quote_plus, urljoin
import requests
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parent
PROFILES=json.loads((ROOT/"fresh_city_profiles.json").read_text(encoding="utf-8"))
CACHE=ROOT/"_fresh_audio_cache"
CACHE.mkdir(parents=True,exist_ok=True)

S=requests.Session()
S.headers.update({"User-Agent":"musicetown-fresh-city-installer/8.9.0"})
NULLRIGHTS="https://nullrights.com"
TIMEOUT=45
CITY_NAMES=list(PROFILES.keys())

def get(url, tries=3):
    last=None
    for n in range(tries):
        try:
            r=S.get(url,timeout=TIMEOUT)
            r.raise_for_status()
            return r
        except Exception as e:
            last=e
            if n+1<tries: time.sleep(1.2*(n+1))
    raise last

def norm(s):
    return re.sub(r"\s+"," ",str(s or "")).strip()

def track_key(title,artist):
    return f"{norm(artist).casefold()}||{norm(title).casefold()}"

def discover(query,max_pages=12):
    found=[]
    for p in range(1,max_pages+1):
        url=f"{NULLRIGHTS}/search?q={quote_plus(query)}&page={p}"
        try:h=get(url).text
        except Exception:continue
        links=re.findall(r'href=["\'](/track/[A-Za-z0-9_-]+)["\']',h)
        if not links and p>2:break
        found.extend(urljoin(NULLRIGHTS,x) for x in links)
    return list(dict.fromkeys(found))

def discover_genre(genre,max_pages=8):
    found=[]
    for p in range(1,max_pages+1):
        url=f"{NULLRIGHTS}/genre/{quote_plus(genre)}?page={p}"
        try:h=get(url).text
        except Exception:continue
        links=re.findall(r'href=["\'](/track/[A-Za-z0-9_-]+)["\']',h)
        if not links and p>2:break
        found.extend(urljoin(NULLRIGHTS,x) for x in links)
    return list(dict.fromkeys(found))

def parse_track(url, profile):
    h=get(url).text
    soup=BeautifulSoup(h,"html.parser")
    txt=norm(soup.get_text(" ",strip=True))
    low=txt.casefold()

    # Hard legal gate; vocals can be required or merely preferred per theme.
    if "cc0 1.0 universal" not in low:return None
    has_vocals="has vocals" in low
    if profile.get("vocal_mode","required")=="required" and not has_vocals:return None
    if re.search(r"ai generated\s+yes",low):return None

    h1=soup.find("h1")
    title=norm(h1.get_text(" ",strip=True) if h1 else "")
    if not title:return None

    artist=""
    ma=re.search(rf'"{re.escape(title)}"\s+by\s+(.+?)\s+[—-]',txt,re.I)
    if ma:artist=norm(ma.group(1))
    if not artist:
        pos=txt.find(title)
        tail=txt[pos+len(title):pos+len(title)+180] if pos>=0 else ""
        artist=norm(tail.split("·")[0].strip(" -–—·"))
    if not artist:artist="Unknown artist"

    duration=None
    md=re.search(r"Duration\s+(\d+):(\d+)",txt,re.I)
    if md:duration=int(md.group(1))*60+int(md.group(2))
    if duration is not None and not (60<=duration<=600):return None

    genre=""
    mg=re.search(r"Genre\s+(.+?)(?:Tags|Duration|Format|Added|AI generated|Plays|License)",txt,re.I)
    if mg:genre=norm(mg.group(1))[:120]

    tags=""
    mt=re.search(r"Tags\s+(.+?)(?:Duration|Format|Added|AI generated|Plays|License)",txt,re.I)
    if mt:tags=norm(mt.group(1))[:260]

    sounds=""
    ms=re.search(r"Sounds like\s+(.+?)(?:Download|Embed this player|Similar tracks|What CC0 means)",txt,re.I)
    if ms:sounds=norm(ms.group(1))[:360]

    download=None
    for a in soup.find_all("a",href=True):
        label=norm(a.get_text(" ",strip=True)).casefold()
        href=urljoin(url,a["href"])
        if "download" in label:
            download=href
            break
    if not download:
        for a in soup.find_all("a",href=True):
            u=urljoin(url,a["href"])
            if re.search(r"\.(mp3|ogg|oga|flac|wav)(?:\?|$)",u,re.I):
                download=u
                break

    embed_id=url.rstrip("/").split("/")[-1]
    return {
      "title":title,"artist":artist,"genre":genre or "CC0 Music",
      "tags":tags,"sounds":sounds,"duration":duration,"hasVocals":has_vocals,
      "source":url,"embed":embed_id,"download":download,
      "license":"CC0 1.0 Universal","licenseVerified":True,
      "licenseChecked":time.strftime("%Y-%m-%d")
    }

def score(track,profile):
    blob=" ".join([track.get("genre",""),track.get("tags",""),track.get("sounds","")]).casefold()
    score=0
    matches=[]
    for kw in profile.get("keywords",[]):
        if kw.casefold() in blob:
            score+=5
            matches.append(kw)
    required=profile.get("required_any",[])
    strong=[kw for kw in required if kw.casefold() in blob]
    track["_strongHits"]=strong
    track["_matches"]=matches[:10]
    if required and not strong:score-=120
    if track.get("hasVocals"):score+=8
    for x in profile.get("reject",[]):
        if x.casefold() in blob:score-=18
    if any(x in blob for x in ["background music","podcast intro","youtube intro","corporate video","game music"]):score-=10
    return score

def direct_audio(track):
    if track.get("download"):return track["download"]
    h=get(track["source"]).text
    soup=BeautifulSoup(h,"html.parser")
    for a in soup.find_all("a",href=True):
        u=urljoin(track["source"],a["href"])
        if re.search(r"\.(mp3|ogg|oga|flac|wav)(?:\?|$)",u,re.I):
            return u
    return None

def cache_key(track):
    return hashlib.sha256(track["source"].encode()).hexdigest()[:24]

def convert_to_cache(track, bitrate):
    cache=CACHE/f"{cache_key(track)}-{bitrate}.mp3"
    if cache.exists() and cache.stat().st_size>=20000:
        return cache

    if not shutil.which("ffmpeg"):
        raise RuntimeError("ffmpeg is required")

    url=direct_audio(track)
    if not url:raise RuntimeError("no direct audio URL")

    with tempfile.TemporaryDirectory() as td:
        raw=Path(td)/"input"
        r=get(url,tries=3)
        with raw.open("wb") as f:
            f.write(r.content)
        if raw.stat().st_size<20000:raise RuntimeError("download too small")
        subprocess.run([
          "ffmpeg","-hide_banner","-loglevel","error","-y",
          "-i",str(raw),"-vn","-codec:a","libmp3lame",
          "-b:a",bitrate,"-map_metadata","-1",str(cache)
        ],check=True)
    if cache.stat().st_size<20000:raise RuntimeError("converted output too small")
    return cache

def read_catalog(path):
    text=path.read_text(encoding="utf-8")
    m=re.search(r'window\.MUSIC_DATA\s*=\s*(\[.*?\]);\s*\n',text,re.S)
    if not m:raise RuntimeError("window.MUSIC_DATA not found")
    return text,m,json.loads(m.group(1))

def write_catalog(path,data):
    text,m,_=read_catalog(path)
    js=json.dumps(data,ensure_ascii=False,separators=(",",":"))
    path.write_text(text[:m.start()]+"window.MUSIC_DATA = "+js+";\n"+text[m.end():],encoding="utf-8")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--per-city",type=int,default=50)
    ap.add_argument("--bitrate",default="64k")
    ap.add_argument("--max-candidates",type=int,default=700)
    args=ap.parse_args()

    index=ROOT/"index.html"
    if not index.exists():
        raise SystemExit("index.html not found. Put installer files in your musicetown repo root.")

    _,_,data=read_catalog(index)
    by_name={d["t"]:d for d in data}

    # Exclude all songs already used by the general 5 categories.
    used=set()
    for d in data:
        if d["t"] in {"JAZZ","CROONER","ROCK","SPORT","LO-FI"}:
            for t in d["tracks"]:
                used.add(track_key(t.get("title"),t.get("artist")))

    report={"generatedAt":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),"cities":{}}

    for city in CITY_NAMES:
        profile=PROFILES[city]
        print(f"\n=== {city}: discovering fresh CC0 theme-fit tracks ===")

        urls=[]
        for q in profile["queries"]:urls+=discover(q)
        for g in profile["genres"]:urls+=discover_genre(g)
        urls=list(dict.fromkeys(urls))

        candidates=[]
        for url in urls[:args.max_candidates]:
            try:
                t=parse_track(url,profile)
                if not t:continue
                k=track_key(t["title"],t["artist"])
                if k in used:continue
                t["_score"]=score(t,profile)
                candidates.append(t)
            except Exception as e:
                print(" skip:",url,str(e)[:100])

        candidates.sort(
            key=lambda t:(-t["_score"],hashlib.sha1((city+t["source"]).encode()).hexdigest())
        )

        selected=[]
        for t in candidates:
            k=track_key(t["title"],t["artist"])
            if k in used:continue
            if profile.get("required_any") and not t.get("_strongHits"):continue
            if t.get("_score",0)<0:continue
            selected.append(t);used.add(k)
            if len(selected)>=args.per_city:break

        if len(selected)<args.per_city:
            raise RuntimeError(f"{city}: only {len(selected)} fresh unique theme-fit CC0 tracks found")

        folder=profile["slug"]
        target_dir=ROOT/folder
        target_dir.mkdir(parents=True,exist_ok=True)

        out_tracks=[]
        for i,t in enumerate(selected,1):
            score_value=t.pop("_score",0)
            matches=t.pop("_matches",[])
            strong_hits=t.pop("_strongHits",[])
            t["curationScore"]=score_value
            t["curationMatches"]=matches
            t["strongThemeMatches"]=strong_hits
            t["trackNo"]=i
            t["shareId"]=f"{folder}-{i:03d}"
            t["freshCity"]=True
            t["curatedTheme"]=city
            t["vibe"]=f"{profile['label']} · {t['genre']}"
            t["audioSrc"]=f"{folder}/{i:03d}.mp3"

            print(f"  [{i:02d}/{args.per_city}] {t['artist']} — {t['title']}")
            cache=convert_to_cache(t,args.bitrate)
            shutil.copy2(cache,ROOT/t["audioSrc"])
            out_tracks.append(t)

        by_name[city]["tracks"]=out_tracks
        report["cities"][city]=out_tracks
        (target_dir/"manifest.json").write_text(
            json.dumps(out_tracks,ensure_ascii=False,indent=2),encoding="utf-8"
        )

    final=[by_name[d["t"]] for d in data]
    write_catalog(index,final)
    if (ROOT/"404.html").exists():write_catalog(ROOT/"404.html",final)

    (ROOT/"fresh_city_manifest.json").write_text(
        json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8"
    )
    print(f"\nFresh city installation complete: {len(CITY_NAMES)} × {args.per_city} tracks.")

if __name__=="__main__":
    main()