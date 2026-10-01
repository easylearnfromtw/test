#!/usr/bin/env python3
from __future__ import annotations
import argparse, html, json, re, shutil, subprocess, tempfile
from pathlib import Path
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parent
MANIFEST=json.loads((ROOT/"verified_audio_manifest.json").read_text(encoding="utf-8"))
CACHE=ROOT/"_master_audio"
CACHE.mkdir(parents=True,exist_ok=True)
S=requests.Session()
S.headers.update({"User-Agent":"musicetown-audio-installer/8.7.3"})
TIMEOUT=45

def get(url):
    r=S.get(url,timeout=TIMEOUT)
    r.raise_for_status()
    return r

def verify_cc0(page_text, source):
    low=page_text.lower()
    if "nullrights.com/track/" in source:
        return "cc0 1.0 universal" in low and ("public domain" in low or "no rights reserved" in low)
    return "cc0 1.0 universal" in low

def find_fma_track_page(album_url,title):
    h=get(album_url).text
    if not verify_cc0(h,album_url):
        raise RuntimeError("FMA source no longer shows CC0 1.0 Universal")
    soup=BeautifulSoup(h,"html.parser")
    norm=lambda s:re.sub(r"\s+"," ",s or "").strip().casefold()
    target=norm(title)
    candidates=[]
    for a in soup.find_all("a",href=True):
        label=norm(a.get_text(" ",strip=True))
        if label==target or target in label or label in target:
            u=urljoin(album_url,a["href"])
            if "/music/" in u:candidates.append(u)
    return candidates[0] if candidates else album_url

def direct_audio_from_page(url,title):
    h=get(url).text
    if not verify_cc0(h,url):
        raise RuntimeError("source no longer shows CC0 1.0 Universal")
    soup=BeautifulSoup(h,"html.parser")
    # visible Download link
    for a in soup.find_all("a",href=True):
        label=a.get_text(" ",strip=True).lower()
        href=urljoin(url,a["href"])
        if "download" in label and re.search(r"\.(mp3|ogg|oga|flac|wav)(?:\?|$)",href,re.I):
            return href
    # media/src links
    for node in soup.find_all(["audio","source","a"],src=True):
        u=urljoin(url,node.get("src"))
        if re.search(r"\.(mp3|ogg|oga|flac|wav)(?:\?|$)",u,re.I):return u
    for a in soup.find_all("a",href=True):
        u=urljoin(url,a["href"])
        if re.search(r"\.(mp3|ogg|oga|flac|wav)(?:\?|$)",u,re.I):return u
    # FMA embeds fileUrl in page source on many versions
    pats=[
      r'fileUrl["\']?\s*:\s*["\']([^"\']+)',
      r'(https://files\.freemusicarchive\.org/[^"\']+?\.(?:mp3|ogg)(?:\?[^"\']*)?)'
    ]
    for pat in pats:
        m=re.search(pat,h,re.I)
        if m:return html.unescape(m.group(1)).replace("\\/","/")
    return None

def resolve_master_audio(master):
    src=master["source"]
    if "nullrights.com/track/" in src:
        return direct_audio_from_page(src,master["title"])
    track_page=find_fma_track_page(src,master["title"])
    return direct_audio_from_page(track_page,master["title"])

def convert(url,dst,bitrate):
    if not shutil.which("ffmpeg"):
        raise RuntimeError("ffmpeg is required (Mac: brew install ffmpeg)")
    with tempfile.TemporaryDirectory() as td:
        raw=Path(td)/"input"
        r=S.get(url,timeout=120,stream=True);r.raise_for_status()
        with raw.open("wb") as f:
            for chunk in r.iter_content(256*1024):
                if chunk:f.write(chunk)
        if raw.stat().st_size<20000:raise RuntimeError("download too small")
        subprocess.run([
          "ffmpeg","-hide_banner","-loglevel","error","-y","-i",str(raw),
          "-vn","-codec:a","libmp3lame","-b:a",bitrate,"-map_metadata","-1",str(dst)
        ],check=True)
        if dst.stat().st_size<20000:raise RuntimeError("output too small")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--bitrate",default="64k")
    ap.add_argument("--verify-only",action="store_true")
    args=ap.parse_args()
    failures=[]
    for n,master in enumerate(MANIFEST["masters"],1):
        mid=master["masterId"]
        cache=CACHE/f"{mid}.mp3"
        try:
            print(f"[{n}/{len(MANIFEST['masters'])}] {master['artist']} — {master['title']}")
            if args.verify_only:
                page=get(master["source"]).text
                if not verify_cc0(page,master["source"]):raise RuntimeError("CC0 verification failed")
                continue
            if not cache.exists() or cache.stat().st_size<20000:
                u=resolve_master_audio(master)
                if not u:raise RuntimeError("could not resolve direct audio URL")
                convert(u,cache,args.bitrate)
            for rel in master["targets"]:
                dst=ROOT/rel
                dst.parent.mkdir(parents=True,exist_ok=True)
                shutil.copy2(cache,dst)
        except Exception as e:
            print("  FAILED:",e)
            failures.append({"masterId":mid,"title":master["title"],"error":str(e)})
    (ROOT/"audio_build_report.json").write_text(json.dumps({"failures":failures},ensure_ascii=False,indent=2),encoding="utf-8")
    print("DONE. failures:",len(failures))
    raise SystemExit(1 if failures else 0)

if __name__=="__main__":
    main()