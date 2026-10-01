#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import shutil
import subprocess
import tempfile
import time
from collections import Counter
from pathlib import Path
from urllib.parse import quote_plus, urljoin

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent
PROFILES = json.loads((ROOT / "theme_profiles.json").read_text(encoding="utf-8"))
CACHE = ROOT / "_theme_audio_cache"
CACHE.mkdir(parents=True, exist_ok=True)

META_CACHE_PATH = CACHE / "track-meta.json"
try:
    META_CACHE = json.loads(META_CACHE_PATH.read_text(encoding="utf-8"))
except Exception:
    META_CACHE = {}

S = requests.Session()
S.headers.update({
    "User-Agent": "musicetown-production-theme-curator/9.0",
    "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8",
})
NULLRIGHTS = "https://nullrights.com"
TIMEOUT = 45

_LAST_REQUEST_AT = 0.0
MIN_REQUEST_GAP = 0.34


def _polite_wait():
    global _LAST_REQUEST_AT
    elapsed = time.monotonic() - _LAST_REQUEST_AT
    wait = MIN_REQUEST_GAP - elapsed
    if wait > 0:
        time.sleep(wait)


def get(url, tries=6):
    global _LAST_REQUEST_AT
    last = None
    for n in range(tries):
        _polite_wait()
        try:
            r = S.get(url, timeout=TIMEOUT)
            _LAST_REQUEST_AT = time.monotonic()

            if r.status_code == 429:
                retry = str(r.headers.get("Retry-After") or "").strip()
                try:
                    delay = float(retry)
                except Exception:
                    delay = min(24.0, 2.0 * (2 ** n))
                delay = max(2.0, delay)
                print(f" rate-limit: waiting {delay:.1f}s")
                time.sleep(delay)
                last = requests.HTTPError(f"429 Too Many Requests for url: {url}")
                continue

            r.raise_for_status()
            return r
        except Exception as e:
            last = e
            if n + 1 < tries:
                time.sleep(min(12.0, 1.6 * (n + 1)))
    raise last


def norm(s):
    return re.sub(r"\s+", " ", str(s or "")).strip()


def key(title, artist):
    return f"{norm(artist).casefold()}||{norm(title).casefold()}"


def save_meta_cache():
    tmp = META_CACHE_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(META_CACHE, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    tmp.replace(META_CACHE_PATH)


def discover(query, max_pages=9):
    found = []
    for p in range(1, max_pages + 1):
        url = f"{NULLRIGHTS}/search?q={quote_plus(query)}&page={p}"
        try:
            h = get(url).text
        except Exception as e:
            print(" search skip:", query, p, str(e)[:100])
            continue
        links = re.findall(r'href=["\'](/track/[A-Za-z0-9_-]+)["\']', h)
        if not links and p > 2:
            break
        found.extend(urljoin(NULLRIGHTS, x) for x in links)
    return list(dict.fromkeys(found))


def discover_genre(genre, max_pages=7):
    found = []
    for p in range(1, max_pages + 1):
        url = f"{NULLRIGHTS}/genre/{quote_plus(genre)}?page={p}"
        try:
            h = get(url).text
        except Exception as e:
            print(" genre skip:", genre, p, str(e)[:100])
            continue
        links = re.findall(r'href=["\'](/track/[A-Za-z0-9_-]+)["\']', h)
        if not links and p > 2:
            break
        found.extend(urljoin(NULLRIGHTS, x) for x in links)
    return list(dict.fromkeys(found))


def parse_track(url, profile):
    cached = META_CACHE.get(url)
    if isinstance(cached, dict) and cached.get("license") == "CC0 1.0 Universal":
        t = dict(cached)
        vocal_mode = profile.get("vocal_mode", "required")
        if vocal_mode == "required" and not t.get("hasVocals"):
            return None
        if vocal_mode == "preferred" and not t.get("hasVocals") and not profile.get("allow_instrumental", False):
            return None
        return t

    h = get(url).text
    soup = BeautifulSoup(h, "html.parser")
    txt = norm(soup.get_text(" ", strip=True))
    low = txt.casefold()

    # Legal / catalog hard gates.
    if "cc0 1.0 universal" not in low:
        return None
    has_vocals = "has vocals" in low
    vocal_mode = profile.get("vocal_mode", "required")
    if vocal_mode == "required" and not has_vocals:
        return None
    if vocal_mode == "preferred" and not has_vocals and not profile.get("allow_instrumental", False):
        return None
    if re.search(r"ai generated\s+yes", low):
        return None

    h1 = soup.find("h1")
    title = norm(h1.get_text(" ", strip=True) if h1 else "")
    if not title:
        return None

    artist = ""
    ma = re.search(rf'"{re.escape(title)}"\s+by\s+(.+?)\s+[—-]', txt, re.I)
    if ma:
        artist = norm(ma.group(1))
    if not artist:
        for el in [h1.find_next("a") if h1 else None, h1.find_next("p") if h1 else None]:
            if el:
                artist = norm(el.get_text(" ", strip=True)).split("·")[0]
                if artist:
                    break
    if not artist:
        artist = "Unknown artist"

    md = re.search(r"Duration\s+(\d+):(\d+)", txt, re.I)
    duration = int(md.group(1)) * 60 + int(md.group(2)) if md else None
    if duration is not None and not (90 <= duration <= 480):
        return None

    bpm = None
    mb = re.search(r"BPM\s+(\d+(?:\.\d+)?)", txt, re.I)
    if mb:
        bpm = float(mb.group(1))

    energy = None
    me = re.search(r"Energy\s+(\d+(?:\.\d+)?)%", txt, re.I)
    if me:
        energy = float(me.group(1))

    plays = 0
    mp = re.search(r"Plays\s+(\d+)", txt, re.I)
    if mp:
        plays = int(mp.group(1))

    genre = ""
    mg = re.search(r"Genre\s+(.+?)(?:Tags|Duration|Format|Added|AI generated|Plays|License)", txt, re.I)
    if mg:
        genre = norm(mg.group(1))[:140]

    tags = ""
    mt = re.search(r"Tags\s+(.+?)(?:Duration|Format|Added|AI generated|Plays|License)", txt, re.I)
    if mt:
        tags = norm(mt.group(1))[:320]

    sounds = ""
    ms = re.search(r"Sounds like\s+(.+?)(?:Download|Embed this player|Similar tracks|What CC0 means)", txt, re.I)
    if ms:
        sounds = norm(ms.group(1))[:420]

    embed_id = url.rstrip("/").split("/")[-1]
    t = {
        "title": title,
        "artist": artist,
        "duration": duration,
        "bpm": bpm,
        "energy": energy,
        "hasVocals": has_vocals,
        "plays": plays,
        "genre": genre or "CC0 Music",
        "tags": tags,
        "sounds": sounds,
        "source": url,
        "embed": embed_id,
        "download": f"{NULLRIGHTS}/audio/{embed_id}",
        "license": "CC0 1.0 Universal",
        "licenseVerified": True,
        "licenseChecked": time.strftime("%Y-%m-%d"),
        "licenseEvidence": "Nullrights track page explicitly states CC0 1.0 Universal.",
    }
    META_CACHE[url] = dict(t)
    if len(META_CACHE) % 25 == 0:
        save_meta_cache()
    return t


def range_score(value, lo, hi, weight):
    if value is None:
        return 0
    if lo <= value <= hi:
        return weight
    dist = min(abs(value - lo), abs(value - hi))
    span = max(1, hi - lo)
    return max(-weight, weight * (1 - dist / span * 2))


def score(t, p):
    blob = " ".join([
        t.get("genre", ""),
        t.get("tags", ""),
        t.get("sounds", ""),
    ]).casefold()

    value = 0.0
    matched = []
    for kw in p["keywords"]:
        if kw.casefold() in blob:
            value += 5
            matched.append(kw)

    required = p.get("required_any", [])
    strong_hits = [kw for kw in required if kw.casefold() in blob]
    t["_strongHits"] = strong_hits
    if required and len(strong_hits) < int(p.get("min_strong_matches", 1)):
        value -= 120

    if p.get("vocal_mode", "required") == "preferred":
        value += 14 if t.get("hasVocals") else 0

    value += range_score(t.get("bpm"), *p["prefer_bpm"], 18)
    value += range_score(t.get("energy"), *p["prefer_energy"], 14)

    dur = t.get("duration")
    if dur is not None:
        if 150 <= dur <= 300:
            value += 8
        elif 120 <= dur <= 360:
            value += 5

    value += min(8, math.log2(1 + (t.get("plays") or 0)) * 1.4)

    rejects = []
    for x in p["reject"]:
        if x.casefold() in blob:
            value -= 18
            rejects.append(x)

    for x in ["background music", "podcast intro", "youtube intro", "corporate video", "game music"]:
        if x in blob:
            value -= 10

    t["_score"] = round(value, 2)
    t["_matches"] = matched[:8]
    t["_rejectHits"] = rejects
    return value


def read_catalog(path):
    text = path.read_text(encoding="utf-8")
    m = re.search(r'window\.MUSIC_DATA\s*=\s*(\[.*?\]);\s*\n', text, re.S)
    if not m:
        raise RuntimeError("window.MUSIC_DATA not found")
    return text, m, json.loads(m.group(1))


def write_catalog(path, data):
    text, m, _ = read_catalog(path)
    js = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    path.write_text(text[:m.start()] + "window.MUSIC_DATA = " + js + ";\n" + text[m.end():], encoding="utf-8")


def cache_key(t):
    return hashlib.sha256(t["source"].encode()).hexdigest()[:24]


def convert(t, bitrate):
    out = CACHE / f"{cache_key(t)}-{bitrate}.mp3"
    if out.exists() and out.stat().st_size >= 20000:
        return out
    if not shutil.which("ffmpeg"):
        raise RuntimeError("ffmpeg required")

    with tempfile.TemporaryDirectory() as td:
        raw = Path(td) / "input"
        r = get(t["download"], tries=6)
        raw.write_bytes(r.content)
        if raw.stat().st_size < 20000:
            raise RuntimeError("download too small")
        subprocess.run([
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-i", str(raw), "-vn", "-codec:a", "libmp3lame",
            "-b:a", bitrate, "-map_metadata", "-1", str(out),
        ], check=True)

    if out.stat().st_size < 20000:
        raise RuntimeError("converted file too small")
    return out


def existing_slots(drawer, p, per_theme):
    folder = p["slug"]
    target = ROOT / folder
    target.mkdir(parents=True, exist_ok=True)
    slots = [None] * per_theme

    for idx, t in enumerate(list(drawer.get("tracks") or [])[:per_theme]):
        rel = t.get("audioSrc") or f"{folder}/{idx + 1:03d}.mp3"
        path = ROOT / rel
        if path.exists() and path.stat().st_size >= 20000:
            kept = dict(t)
            kept["trackNo"] = idx + 1
            kept["audioSrc"] = rel
            kept["shareId"] = kept.get("shareId") or f"{folder}-{idx + 1:03d}"
            kept["localMp3"] = True
            slots[idx] = kept
    return slots


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-theme", type=int, default=50)
    ap.add_argument("--bitrate", default="64k")
    ap.add_argument("--max-candidates", type=int, default=620)
    ap.add_argument("--candidate-pool", type=int, default=92)
    ap.add_argument("--max-per-artist", type=int, default=5)
    args = ap.parse_args()

    index = ROOT / "index.html"
    if not index.exists():
        raise SystemExit("index.html not found")

    _, _, data = read_catalog(index)
    by_name = {d["t"]: d for d in data}

    report = {
        "generatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "themes": {},
    }

    for theme, p in PROFILES.items():
        drawer = by_name[theme]
        folder = p["slug"]
        slots = existing_slots(drawer, p, args.per_theme)
        retained = [t for t in slots if t]
        missing_positions = [i for i, t in enumerate(slots) if t is None]

        if not missing_positions:
            print(f"\n=== {theme}: keep existing {args.per_theme} ready tracks ===")
            drawer["tracks"] = slots
            drawer["installPending"] = False
            report["themes"][theme] = slots
            (ROOT / folder / "manifest.json").write_text(
                json.dumps(slots, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            continue

        need = len(missing_positions)
        print(f"\n=== {theme}: curating {need} legal, strong-fit track(s) ===")

        theme_used = {key(t.get("title"), t.get("artist")) for t in retained}
        urls = []
        for q in p["queries"]:
            urls.extend(discover(q))
        for g in p["genres"]:
            urls.extend(discover_genre(g))
        urls = list(dict.fromkeys(urls))

        candidates = []
        seen = set(theme_used)
        for url in urls[:args.max_candidates]:
            try:
                t = parse_track(url, p)
                if not t:
                    continue
                k = key(t["title"], t["artist"])
                if k in seen:
                    continue
                seen.add(k)

                score(t, p)
                if p.get("required_any") and not t.get("_strongHits"):
                    continue
                if t["_score"] < 0:
                    continue
                candidates.append(t)

                if len(candidates) >= max(args.candidate_pool, need + 30):
                    break
            except Exception as e:
                print(" skip:", url, str(e)[:100])

        candidates.sort(
            key=lambda t: (
                -t["_score"],
                hashlib.sha1((theme + t["source"]).encode()).hexdigest(),
            )
        )

        selected = []
        artist_counts = Counter()
        for t in candidates:
            k = key(t["title"], t["artist"])
            if k in theme_used:
                continue
            artist = norm(t["artist"]).casefold()
            if artist_counts[artist] >= args.max_per_artist:
                continue
            selected.append(t)
            artist_counts[artist] += 1
            theme_used.add(k)
            if len(selected) >= need:
                break

        if len(selected) < need:
            save_meta_cache()
            raise RuntimeError(
                f"{theme}: need {need} track(s), only {len(selected)} suitable "
                "strong-fit CC0 tracks passed legal/theme/quality gates"
            )

        for slot_idx, t in zip(missing_positions, selected):
            track_no = slot_idx + 1
            print(
                f" [{track_no:02d}/{args.per_theme}] "
                f"{t['artist']} — {t['title']} · score {t['_score']}"
            )
            cached = convert(t, args.bitrate)
            rel = f"{folder}/{track_no:03d}.mp3"
            shutil.copy2(cached, ROOT / rel)

            matches = t.pop("_matches", [])
            strong_hits = t.pop("_strongHits", [])
            t.pop("_rejectHits", None)
            score_value = t.pop("_score", 0)

            t.update({
                "trackNo": track_no,
                "shareId": f"{folder}-{track_no:03d}",
                "freshTheme": True,
                "curatedTheme": theme,
                "curationScore": score_value,
                "curationMatches": matches,
                "strongThemeMatches": strong_hits,
                "vibe": f"{p['vibe']} · {t['genre']}",
                "audioSrc": rel,
                "localMp3": True,
            })
            slots[slot_idx] = t

        drawer["tracks"] = slots
        drawer["installPending"] = False
        report["themes"][theme] = slots
        (ROOT / folder / "manifest.json").write_text(
            json.dumps(slots, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        save_meta_cache()

    final = [by_name[d["t"]] for d in data]
    write_catalog(index, final)
    if (ROOT / "404.html").exists():
        write_catalog(ROOT / "404.html", final)

    save_meta_cache()
    (ROOT / "theme_curation_manifest.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\nTheme curation complete: {len(PROFILES)} × {args.per_theme} tracks.")


if __name__ == "__main__":
    main()
