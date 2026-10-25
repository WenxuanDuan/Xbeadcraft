"""Rebuild bundled palette snapshots from pinned, MIT-licensed upstream data."""
from __future__ import annotations

import csv
import hashlib
import io
import json
import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    "beadcolors": ("maxcleme/beadcolors", "f97ff4283d03cef5cd7e1071a86f5892e0c0c61b"),
    "pindou": ("HansBug/pindou-color-data", "178dafbc9e77d3de556550dbd058270200129186"),
}
# Keep different bead sizes and product series separate rather than merging brands.
PALETTES = [
    ("pindou", "mard-291-github", "MARD 291", "MARD 291"),
    ("pindou", "coco-291", "COCO 291", "COCO 291"),
    ("pindou", "manman-278", "漫漫", "Manman"),
    ("pindou", "panpan-289", "盼盼", "Panpan"),
    ("pindou", "mixiaowo-290", "咪小窝", "Mixiaowo"),
    ("pindou", "artkal-c-197-official", "Artkal / 优肯 C · 2.6 mm", "Artkal C · 2.6 mm"),
    ("pindou", "artkal-m-221-official", "Artkal / 优肯 M · 2.6 mm", "Artkal M · 2.6 mm"),
    ("pindou", "artkal-c197-m221-418-official", "Artkal / 优肯 C+M · 2.6 mm", "Artkal C+M · 2.6 mm"),
    ("beadcolors", "artkal_a", "Artkal / 优肯 A · 2.6 mm", "Artkal A · 2.6 mm"),
    ("beadcolors", "artkal_r", "Artkal / 优肯 R · 5 mm", "Artkal R · 5 mm"),
    ("beadcolors", "artkal_s", "Artkal / 优肯 S · 5 mm", "Artkal S · 5 mm"),
    ("beadcolors", "perler", "Perler · Midi", "Perler · Midi"),
    ("beadcolors", "perler_mini", "Perler · Mini", "Perler · Mini"),
    ("beadcolors", "perler_caps", "Perler · Caps", "Perler · Caps"),
    ("beadcolors", "hama", "Hama · Midi", "Hama · Midi"),
    ("beadcolors", "hama_mini", "Hama · Mini", "Hama · Mini"),
    ("beadcolors", "hama_maxi", "Hama · Maxi", "Hama · Maxi"),
    ("beadcolors", "nabbi", "Nabbi", "Nabbi"),
    ("beadcolors", "yant", "Yant", "Yant"),
]


def fetch(url):
    with urlopen(url, timeout=45) as response:
        return response.read()


def build(entry):
    source, key, zh, en = entry
    repository, commit = SOURCES[source]
    path = f"{key}/colors.json" if source == "pindou" else f"raw/{key}.csv"
    url = f"https://raw.githubusercontent.com/{repository}/{commit}/{path}"
    raw = fetch(url)
    skipped, colors, upstream_sources = [], [], []
    if source == "pindou":
        payload = json.loads(raw)
        upstream_sources = payload.get("sources", [])
        for color in payload["colors"]:
            if color.get("unidentified") or str(color["code"]).startswith("UNKNOWN-"):
                skipped.append({"code": color["code"], "reason": "unidentified_code"})
            elif len(color.get("rgb", [])) == 4 and color["rgb"][3] < 255:
                skipped.append({"code": color["code"], "reason": "transparent_material"})
            else:
                colors.append((str(color["code"]), str(color.get("name", color["code"])), color["rgb"][:3]))
    else:
        for row in csv.reader(io.StringIO(raw.decode("utf-8-sig"))):
            if not row:
                continue
            colors.append((row[0].strip(), row[1].strip(), [int(x) for x in row[2:5]]))
    rows, seen = [], set()
    for code, name, rgb in colors:
        if code in seen or len(rgb) != 3 or any(not isinstance(x, int) or not 0 <= x <= 255 for x in rgb):
            raise ValueError(f"Invalid or duplicate color in {key}: {code}")
        seen.add(code)
        match = re.match(r"[A-Za-z]+", code)
        rows.append([code, '#'+''.join(f'{x:02X}' for x in rgb), *rgb, match[0].upper() if match else '', name])
    destination = ROOT/"data"/"palettes"/f"{key}.csv"
    with destination.open('w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['code', 'hex', 'r', 'g', 'b', 'series', 'name'])
        writer.writerows(rows)
    return {"id": key, "file": f"palettes/{key}.csv", "name_zh": zh, "name_en": en,
            "count": len(rows), "reference": "community", "source": url, "repository": repository,
            "commit": commit, "source_sha256": hashlib.sha256(raw).hexdigest(),
            "license": f"licenses/{source}-MIT.txt", "upstream_sources": upstream_sources,
            "excluded": skipped}


def main():
    for directory in ['palettes', 'licenses']:
        (ROOT/'data'/directory).mkdir(exist_ok=True)
    with ThreadPoolExecutor(max_workers=6) as pool:
        entries = list(pool.map(build, PALETTES))
    for key, (repository, commit) in SOURCES.items():
        (ROOT/'data'/'licenses'/f'{key}-MIT.txt').write_bytes(fetch(f'https://raw.githubusercontent.com/{repository}/{commit}/LICENSE'))
    original = {"id": "mard_221", "file": "mard_221.csv", "name_zh": "MARD 221 · 原版", "name_en": "MARD 221 · Original",
                "count": 221, "reference": "existing", "source": "https://www.pixel-beads.com/zh/mard-bead-color-chart", "excluded": []}
    (ROOT/'data'/'palettes.json').write_text(json.dumps([original, *entries], ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    for entry in [original, *entries]:
        print(entry['id'], entry['count'], 'excluded:', len(entry['excluded']))


if __name__ == '__main__':
    main()
