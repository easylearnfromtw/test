#!/usr/bin/env python3
from pathlib import Path
from urllib.parse import urlencode
import qrcode

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"assets"/"city-pass-qr"
OUT.mkdir(parents=True,exist_ok=True)

BASE="https://easylearnfromtw.github.io/test/"
SLUGS=[
 "taipei-style",
 "old-tokyo",
 "splendor-shanghai",
 "vancouver",
 "london",
 "new-york",
 "traditional-beijing",
 "tropical-hawaii",
 "bustling-hong-kong",
 "slightly-tipsy-rome",
 "psychedelic-la",
 "solemn-kyoto",
 "miraculous-luoyang",
 "champs-elysees",
 "menacing-dubai",
]

for slug in SLUGS:
    url=BASE+"?"+urlencode({"theme":slug})
    img=qrcode.make(url)
    dst=OUT/f"{slug}.png"
    img.save(dst)
    print("QR",dst.relative_to(ROOT),url)

print(f"Generated {len(SLUGS)} City Pass QR assets.")
