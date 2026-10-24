#!/usr/bin/env python3
"""Build TV guides (XMLTV) that fit this repository's Kodi playlists.

A public guide (see SOURCES) names channels with its own ids, so Kodi's IPTV Simple Client cannot pair it with
our playlist by id. This script matches guide channels to the channels in channels_pvr.m3u by name, rewrites the
channel ids to the playlist's tvg-id values and keeps only the matched channels:

    epg_telugu.xml.gz   Telugu channels only (small, quick to load)
    epg_pvr.xml.gz      every language in channels_pvr.m3u

Only guide data (titles, times, descriptions) is used. If the source cannot be downloaded, or very few channels
match, the existing files are left untouched.
"""
from __future__ import annotations

import argparse
import copy
import gzip
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"

# Tried in order. Same file, different hosts.
SOURCES = [
    "https://raw.githubusercontent.com/mitthu786/tvepg/main/epg.xml.gz",
    "https://cdn.jsdelivr.net/gh/mitthu786/tvepg/epg.xml.gz",
]

EXTINF_RE = re.compile(r"^#EXTINF:(-?\d+)\s*(.*?),(.*)$")
ATTR_RE = re.compile(r'([\w-]+)="([^"]*)"')

# Spelling differences between our playlist and the guide: normalized playlist name -> normalized guide name.
# Matching is strict on purpose: "Zee Telugu" must never pick up "Zee TV" (Hindi), so only list pairs that are
# really the same channel.
ALIASES = {
    "abnandhrajyoti": "abnandhrajyothi",
    "6tvtelugu": "6tv",
    "vanithatv": "vanitha",
    "svbcsrivenkateswarabhaktichannel": "svbc",
    "hungamatv": "hungama",
}


def norm(name: str) -> str:
    """Name without case, spaces, punctuation, bracketed tags and a plain HD/SD marker."""
    s = name.lower().replace("&", "and")
    s = re.sub(r"\(.*?\)|\[.*?\]", "", s)
    s = re.sub(r"\b(hd|sd)\b", "", s)
    return re.sub(r"[^a-z0-9]", "", s)


def read_playlist(path: Path) -> list[dict]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        m = EXTINF_RE.match(line.strip())
        if m:
            attrs = dict(ATTR_RE.findall(m.group(2)))
            rows.append({"name": m.group(3).strip(), "id": attrs.get("tvg-id") or "", "logo": attrs.get("tvg-logo", ""),
                         "group": attrs.get("group-title", "")})
    # The same channel can sit in several language groups with the same tvg-id; keep one row per group.
    seen, unique = set(), []
    for r in rows:
        key = (r["id"], r["group"])
        if r["id"] and key not in seen:
            seen.add(key)
            unique.append(r)
    return unique


def download(urls: list[str]) -> bytes | None:
    for url in urls:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = resp.read()
            xml = gzip.decompress(data)
            if b"<programme" in xml[:5_000_000] or b"<programme" in xml:
                print(f"[epg] source ok: {url} ({len(xml) // 1024} KiB of XML)")
                return xml
        except Exception as exc:
            print(f"[epg] source failed: {url}: {exc}", file=sys.stderr)
    return None


def build(xml: bytes, channels: list[dict]):
    root = ET.fromstring(xml)
    guide_name = {c.get("id"): (c.findtext("display-name") or "") for c in root.findall("channel")}
    counts = Counter(p.get("channel") for p in root.findall("programme"))
    by_norm: dict[str, list[tuple[int, str]]] = defaultdict(list)
    for gid, gname in guide_name.items():
        by_norm[norm(gname)].append((counts[gid], gid))

    wanted: dict[str, list[dict]] = defaultdict(list)  # guide channel id -> our channels
    unmatched = []
    for ch in channels:
        key = norm(ch["name"])
        key = ALIASES.get(key, key)
        cands = [c for c in by_norm.get(key, []) if c[0] > 0]
        if not cands:
            unmatched.append(ch["name"])
            continue
        wanted[max(cands)[1]].append(ch)  # the guide channel with the most programmes

    programmes = defaultdict(list)
    for p in root.findall("programme"):
        if p.get("channel") in wanted:
            programmes[p.get("channel")].append(p)
    return wanted, programmes, unmatched


def render(wanted, programmes, only_group: str | None) -> tuple[bytes, int, int]:
    tv = ET.Element("tv", {"generator-info-name": "telugulive epg builder"})
    out_channels, out_programmes, emitted = [], [], set()
    for gid, ours in wanted.items():
        for ch in ours:
            if only_group and ch["group"] != only_group:
                continue
            if ch["id"] in emitted:  # same id in several language groups: one guide entry is enough
                continue
            emitted.add(ch["id"])
            node = ET.Element("channel", {"id": ch["id"]})
            ET.SubElement(node, "display-name").text = ch["name"]
            if ch["logo"]:
                ET.SubElement(node, "icon", {"src": ch["logo"]})
            out_channels.append(node)
            for p in programmes.get(gid, []):
                q = copy.deepcopy(p)
                q.set("channel", ch["id"])
                out_programmes.append(q)
    for n in out_channels:
        tv.append(n)
    for q in sorted(out_programmes, key=lambda e: (e.get("channel"), e.get("start", ""))):
        tv.append(q)
    xml = ET.tostring(tv, encoding="utf-8", xml_declaration=True)
    buf = gzip.compress(xml, 9, mtime=0)  # fixed mtime: identical input gives identical bytes
    return buf, len(out_channels), len(out_programmes)


def write_if_changed(path: Path, data: bytes) -> None:
    if not path.exists() or path.read_bytes() != data:
        path.write_bytes(data)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--playlist", default=str(ROOT / "channels_pvr.m3u"))
    ap.add_argument("--out-dir", default=str(ROOT))
    ap.add_argument("--source-file", help="Use this local .xml.gz instead of downloading (for testing)")
    ap.add_argument("--min-channels", type=int, default=10,
                    help="Do not overwrite the guides if fewer channels than this match")
    args = ap.parse_args()

    channels = read_playlist(Path(args.playlist))
    if not channels:
        print("[epg] playlist is empty or missing; nothing to do", file=sys.stderr)
        return 1
    if args.source_file:
        xml = gzip.decompress(Path(args.source_file).read_bytes())
    else:
        xml = download(SOURCES)
    if xml is None:
        print("[epg] no guide source reachable; keeping the existing guides", file=sys.stderr)
        return 0

    wanted, programmes, unmatched = build(xml, channels)
    out_dir = Path(args.out_dir)
    for fname, group in (("epg_telugu.xml.gz", "Telugu"), ("epg_pvr.xml.gz", None)):
        data, n_ch, n_pr = render(wanted, programmes, group)
        print(f"[epg] {fname}: {n_ch} channels, {n_pr} programmes, {len(data) // 1024} KiB")
        if n_ch < args.min_channels:
            print(f"[epg] only {n_ch} channels matched; keeping the existing {fname}", file=sys.stderr)
            continue
        write_if_changed(out_dir / fname, data)
    matched = {c["id"] for lst in wanted.values() for c in lst}
    tel = [c for c in channels if c["group"] == "Telugu"]
    missing = sorted({c["name"] for c in tel if c["id"] not in matched})
    print(f"[epg] Telugu channels with a guide: {len(tel) - sum(1 for c in tel if c['id'] not in matched)} of {len(tel)}")
    print(f"[epg] Telugu channels without a guide: {', '.join(missing)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
