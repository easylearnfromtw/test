#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from urllib.parse import quote_plus, urljoin

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent
PROFILES = json.loads((ROOT / "fresh_city_profiles.json").read_text(encoding="utf-8"))
CACHE = ROOT / "_fresh_audio_cache"
MASTER_CACHE = ROOT / "_master_audio"
CACHE.mkdir(parents=True, exist_ok=True)

META_CACHE_PATH = CACHE / "track-meta.json"
try:
    META_CACHE = json.loads(META_CACHE_PATH.read_text(encoding="utf-8"))
except Exception:
    META_CACHE = {}

S = requests.Session()
S.headers.update({
    "User-Agent": "musicetown-production-city-curator/9.0",
    "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8",
})
NULLRIGHTS = "https://nullrights.com"
TIMEOUT = 45
CITY_NAMES = list(PROFILES.keys())

_LAST_REQUEST_AT = 0.0
MIN_REQUEST_GAP = 0.34


def _polite_wait():
    global _LAST_REQUEST_AT
    elapsed = time.monotonic() - _LAST_REQUEST_AT
    wait = MIN_REQUEST_GAP - elapsed
    if wait > 0:
        time.sleep(wait)


def get(url, tries=6):
    """Rate-limit politely and recover from Nullrights 429 responses."""
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


def track_key(title, artist):
    return f"{norm(artist).casefold()}||{norm(title).casefold()}"


def save_meta_cache():
    tmp = META_CACHE_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(META_CACHE, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    tmp.replace(META_CACHE_PATH)


def discover(query, max_pages=8):
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


def discover_genre(genre, max_pages=6):
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
        # Re-evaluate profile-dependent vocal gate below.
        if profile.get("vocal_mode", "required") == "required" and not t.get("hasVocals"):
            return None
        return t

    h = get(url).text
    soup = BeautifulSoup(h, "html.parser")
    txt = norm(soup.get_text(" ", strip=True))
    low = txt.casefold()

    # Legal hard gate.
    if "cc0 1.0 universal" not in low:
        return None
    has_vocals = "has vocals" in low
    if profile.get("vocal_mode", "required") == "required" and not has_vocals:
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
        pos = txt.find(title)
        tail = txt[pos + len(title):pos + len(title) + 180] if pos >= 0 else ""
        artist = norm(tail.split("·")[0].strip(" -–—·"))
    if not artist:
        artist = "Unknown artist"

    duration = None
    md = re.search(r"Duration\s+(\d+):(\d+)", txt, re.I)
    if md:
        duration = int(md.group(1)) * 60 + int(md.group(2))
    if duration is not None and not (60 <= duration <= 600):
        return None

    genre = ""
    mg = re.search(r"Genre\s+(.+?)(?:Tags|Duration|Format|Added|AI generated|Plays|License)", txt, re.I)
    if mg:
        genre = norm(mg.group(1))[:120]

    tags = ""
    mt = re.search(r"Tags\s+(.+?)(?:Duration|Format|Added|AI generated|Plays|License)", txt, re.I)
    if mt:
        tags = norm(mt.group(1))[:260]

    sounds = ""
    ms = re.search(r"Sounds like\s+(.+?)(?:Download|Embed this player|Similar tracks|What CC0 means)", txt, re.I)
    if ms:
        sounds = norm(ms.group(1))[:360]

    embed_id = url.rstrip("/").split("/")[-1]
    t = {
        "title": title,
        "artist": artist,
        "genre": genre or "CC0 Music",
        "tags": tags,
        "sounds": sounds,
        "duration": duration,
        "hasVocals": has_vocals,
        "source": url,
        "embed": embed_id,
        # Stable first-party Nullrights audio endpoint; extension is intentionally absent.
        "download": f"{NULLRIGHTS}/audio/{embed_id}",
        "license": "CC0 1.0 Universal",
        "licenseVerified": True,
        "licenseChecked": time.strftime("%Y-%m-%d"),
    }
    META_CACHE[url] = dict(t)
    if len(META_CACHE) % 25 == 0:
        save_meta_cache()
    return t


def score(track, profile):
    blob = " ".join([
        track.get("genre", ""),
        track.get("tags", ""),
        track.get("sounds", ""),
    ]).casefold()

    value = 0
    matches = []
    for kw in profile.get("keywords", []):
        if kw.casefold() in blob:
            value += 5
            matches.append(kw)

    required = profile.get("required_any", [])
    strong = [kw for kw in required if kw.casefold() in blob]
    track["_strongHits"] = strong
    track["_matches"] = matches[:10]
    if required and not strong:
        value -= 120

    if track.get("hasVocals"):
        value += 8

    for x in profile.get("reject", []):
        if x.casefold() in blob:
            value -= 18

    if any(x in blob for x in [
        "background music", "podcast intro", "youtube intro", "corporate video", "game music"
    ]):
        value -= 10

    return value


def direct_audio(track):
    return track.get("download") or (
        f"{NULLRIGHTS}/audio/{track.get('embed')}" if track.get("embed") else None
    )


def cache_key(track):
    return hashlib.sha256(track["source"].encode()).hexdigest()[:24]


def convert_to_cache(track, bitrate):
    cache = CACHE / f"{cache_key(track)}-{bitrate}.mp3"
    if cache.exists() and cache.stat().st_size >= 20000:
        return cache

    if not shutil.which("ffmpeg"):
        raise RuntimeError("ffmpeg is required")

    url = direct_audio(track)
    if not url:
        raise RuntimeError("no direct audio URL")

    with tempfile.TemporaryDirectory() as td:
        raw = Path(td) / "input"
        r = get(url, tries=6)
        raw.write_bytes(r.content)
        if raw.stat().st_size < 20000:
            raise RuntimeError("download too small")
        subprocess.run([
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-i", str(raw), "-vn", "-codec:a", "libmp3lame",
            "-b:a", bitrate, "-map_metadata", "-1", str(cache),
        ], check=True)

    if cache.stat().st_size < 20000:
        raise RuntimeError("converted output too small")
    return cache


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


def selection_cache_path(profile):
    return CACHE / f"selection-{profile['slug']}.json"


def save_selection(profile, tracks):
    selection_cache_path(profile).write_text(
        json.dumps(tracks, ensure_ascii=False, separators=(",", ":")), encoding="utf-8"
    )


def materialize_existing_slots(drawer, profile, per_city, bitrate):
    """Reuse repo metadata, verified master cache, then prior production selection cache."""
    folder = profile["slug"]
    target_dir = ROOT / folder
    target_dir.mkdir(parents=True, exist_ok=True)

    existing = list(drawer.get("tracks") or [])[:per_city]
    slots = [None] * per_city

    for idx, t in enumerate(existing):
        slot_no = idx + 1
        rel = t.get("audioSrc") or f"{folder}/{slot_no:03d}.mp3"
        dst = ROOT / rel

        ok = dst.exists() and dst.stat().st_size >= 20000
        if not ok and t.get("masterId"):
            master = MASTER_CACHE / f"{t['masterId']}.mp3"
            if master.exists() and master.stat().st_size >= 20000:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(master, dst)
                ok = True

        if ok:
            kept = dict(t)
            kept["trackNo"] = slot_no
            kept["audioSrc"] = rel
            kept["shareId"] = kept.get("shareId") or f"{folder}-{slot_no:03d}"
            kept["localMp3"] = True
            kept["curatedTheme"] = drawer["t"]
            slots[idx] = kept

    # New city themes are empty in the repo. Once curated successfully, cache the
    # exact legal selection so later UI-only deploys can rebuild without re-scraping.
    cached_file = selection_cache_path(profile)
    try:
        cached_tracks = json.loads(cached_file.read_text(encoding="utf-8"))
    except Exception:
        cached_tracks = []

    for idx, t in enumerate(list(cached_tracks)[:per_city]):
        if slots[idx] is not None:
            continue
        source = str(t.get("source") or "")
        if not source:
            continue
        audio_cache = CACHE / f"{hashlib.sha256(source.encode()).hexdigest()[:24]}-{bitrate}.mp3"
        if not audio_cache.exists() or audio_cache.stat().st_size < 20000:
            continue

        track_no = idx + 1
        rel = f"{folder}/{track_no:03d}.mp3"
        dst = ROOT / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(audio_cache, dst)

        kept = dict(t)
        kept["trackNo"] = track_no
        kept["audioSrc"] = rel
        kept["shareId"] = f"{folder}-{track_no:03d}"
        kept["localMp3"] = True
        kept["curatedTheme"] = drawer["t"]
        slots[idx] = kept

    return slots


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-city", type=int, default=50)
    ap.add_argument("--bitrate", default="64k")
    ap.add_argument("--max-candidates", type=int, default=520)
    ap.add_argument("--candidate-pool", type=int, default=86)
    args = ap.parse_args()

    index = ROOT / "index.html"
    if not index.exists():
        raise SystemExit("index.html not found. Put installer files in your musicetown repo root.")

    _, _, data = read_catalog(index)
    by_name = {d["t"]: d for d in data}

    report = {
        "generatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "cities": {},
    }

    for city in CITY_NAMES:
        profile = PROFILES[city]
        drawer = by_name[city]
        folder = profile["slug"]

        # First restore existing curated city tracks from the verified general master cache.
        slots = materialize_existing_slots(drawer, profile, args.per_city, args.bitrate)
        retained = [t for t in slots if t]
        missing_positions = [i for i, t in enumerate(slots) if t is None]

        if not missing_positions:
            print(f"\n=== {city}: restored existing {args.per_city} verified tracks ===")
            drawer["tracks"] = slots
            drawer["installPending"] = False
            report["cities"][city] = slots
            save_selection(profile, slots)
            (ROOT / folder / "manifest.json").write_text(
                json.dumps(slots, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            continue

        need = len(missing_positions)
        print(
            f"\n=== {city}: {len(retained)} restored · curating {need} fresh "
            f"theme-fit CC0 track(s) ==="
        )

        city_used = {track_key(t.get("title"), t.get("artist")) for t in retained}
        urls = []
        for q in profile["queries"]:
            urls.extend(discover(q))
        for g in profile["genres"]:
            urls.extend(discover_genre(g))
        urls = list(dict.fromkeys(urls))

        candidates = []
        seen = set(city_used)
        for url in urls[:args.max_candidates]:
            try:
                t = parse_track(url, profile)
                if not t:
                    continue
                k = track_key(t["title"], t["artist"])
                if k in seen:
                    continue
                seen.add(k)

                t["_score"] = score(t, profile)
                if profile.get("required_any") and not t.get("_strongHits"):
                    continue
                if t["_score"] < 0:
                    continue

                candidates.append(t)
                # Enough valid material for a high-quality ranked selection.
                if len(candidates) >= max(args.candidate_pool, need + 24):
                    break
            except Exception as e:
                print(" skip:", url, str(e)[:100])

        candidates.sort(
            key=lambda t: (
                -t["_score"],
                hashlib.sha1((city + t["source"]).encode()).hexdigest(),
            )
        )

        selected = []
        for t in candidates:
            k = track_key(t["title"], t["artist"])
            if k in city_used:
                continue
            selected.append(t)
            city_used.add(k)
            if len(selected) >= need:
                break

        if len(selected) < need:
            save_meta_cache()
            raise RuntimeError(
                f"{city}: need {need} fresh track(s), only {len(selected)} "
                "strong theme-fit CC0 tracks were available after legal/quality gates"
            )

        for slot_idx, t in zip(missing_positions, selected):
            track_no = slot_idx + 1
            score_value = t.pop("_score", 0)
            matches = t.pop("_matches", [])
            strong_hits = t.pop("_strongHits", [])

            t["curationScore"] = score_value
            t["curationMatches"] = matches
            t["strongThemeMatches"] = strong_hits
            t["trackNo"] = track_no
            t["shareId"] = f"{folder}-{track_no:03d}"
            t["freshCity"] = True
            t["curatedTheme"] = city
            t["vibe"] = f"{profile['label']} · {t['genre']}"
            t["audioSrc"] = f"{folder}/{track_no:03d}.mp3"
            t["localMp3"] = True

            print(
                f"  [{track_no:02d}/{args.per_city}] "
                f"{t['artist']} — {t['title']} · score {score_value}"
            )
            cached = convert_to_cache(t, args.bitrate)
            shutil.copy2(cached, ROOT / t["audioSrc"])
            slots[slot_idx] = t

        drawer["tracks"] = slots
        drawer["installPending"] = False
        report["cities"][city] = slots
        save_selection(profile, slots)
        (ROOT / folder / "manifest.json").write_text(
            json.dumps(slots, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        save_meta_cache()

    final = [by_name[d["t"]] for d in data]
    write_catalog(index, final)
    if (ROOT / "404.html").exists():
        write_catalog(ROOT / "404.html", final)

    save_meta_cache()
    (ROOT / "fresh_city_manifest.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\nFresh city installation complete: {len(CITY_NAMES)} × {args.per_city} tracks.")


if __name__ == "__main__":
    main()
