#!/usr/bin/env python3
from pathlib import Path
import json,re,subprocess,shutil,sys

ROOT=Path(__file__).resolve().parent
text=(ROOT/"index.html").read_text(encoding="utf-8")
m=re.search(r'window\.MUSIC_DATA\s*=\s*(\[.*?\]);\s*\n',text,re.S)
if not m:raise SystemExit("MUSIC_DATA not found")
data=json.loads(m.group(1))

expected=[]
for d in data:
    for t in d.get("tracks",[]):
        expected.append((d["t"],t.get("title",""),t.get("audioSrc","")))

missing=[];bad=[]
ffprobe=shutil.which("ffprobe")
for drawer,title,rel in expected:
    p=ROOT/rel
    if not rel or not p.exists():
        missing.append(f"{drawer} :: {title} :: {rel}");continue
    if p.stat().st_size<20000:
        bad.append(f"{rel}: too small ({p.stat().st_size} bytes)");continue
    if ffprobe:
        r=subprocess.run([ffprobe,"-v","error","-show_entries","format=duration","-of","default=nw=1:nk=1",str(p)],capture_output=True,text=True)
        if r.returncode!=0:bad.append(f"{rel}: ffprobe failed")

total=len(expected)
ready=total-len(missing)-len(bad)
report={"drawers":len(data),"expected":total,"ready":ready,"missing":missing,"bad":bad}
(ROOT/"MUSIC_INSTALL_REPORT.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
print(f"MUSIC READY: {ready}/{total} · DRAWERS {len(data)}")

if len(data)!=23:
    print(f"ERROR: expected 23 themes, got {len(data)}")
    sys.exit(1)
if total!=1150:
    print(f"ERROR: expected 1150 tracks, got {total}")
    sys.exit(1)
sys.exit(1 if missing or bad else 0)