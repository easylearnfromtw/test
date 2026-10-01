#!/usr/bin/env python3
from pathlib import Path
import shutil
ROOT=Path(__file__).resolve().parent
SITE=ROOT/"_site"
if SITE.exists():shutil.rmtree(SITE)
SITE.mkdir()

for name in [
    "index.html","404.html",".nojekyll",
    "remote-audio-map.js",
    "MUSIC_INSTALL_REPORT.json","theme_curation_manifest.json","fresh_city_manifest.json",
    "city-pass-preview.html"
]:
    p=ROOT/name
    if p.exists():shutil.copy2(p,SITE/name)

# City Pass depends on local QR artwork assets. Keep them in the final
# 23-theme / 1150-track GitHub Pages artifact.
assets=ROOT/"assets"
if assets.exists():
    shutil.copytree(assets,SITE/"assets")

folders=[
 "jazz","crooner","rock","sport","lo-fi",
 "taipei-style","old-tokyo","splendor-shanghai","vancouver","london","new-york",
 "emo","running","poem","traditional-beijing",
 "tropical-hawaii","bustling-hong-kong","slightly-tipsy-rome","psychedelic-la",
 "solemn-kyoto","miraculous-luoyang","champs-elysees","menacing-dubai"
]
for folder in folders:
    src=ROOT/folder
    if not src.exists():raise SystemExit(f"Missing folder: {folder}")
    shutil.copytree(src,SITE/folder)

size=sum(p.stat().st_size for p in SITE.rglob("*") if p.is_file())
print(f"Prepared 23-theme site: {size/1024/1024:.1f} MB")