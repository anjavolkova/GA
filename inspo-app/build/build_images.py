"""Download each prompt's Pexels photo as a small WebP thumbnail and pack them
into data/photos-N.json files ({photo_id: data URI}).

The packs let the app show the photos where hotlinking images.pexels.com is
not allowed. Photos are from Pexels (https://www.pexels.com/license/).
"""
import base64
import io
import json
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PIL import Image

DATA = Path(__file__).resolve().parents[1] / "data"
CACHE = Path(sys.argv[1]) if len(sys.argv) > 1 else DATA / ".photo-cache"
PACK_SIZE = 50
CACHE.mkdir(parents=True, exist_ok=True)

ids = sorted({p["p"] for p in json.loads((DATA / "prompts.json").read_text())["prompts"] if p["p"]})


def fetch(pid):
    out = CACHE / f"{pid}.webp"
    if out.exists():
        return pid, True
    raw = None
    for ext in ("jpeg", "png"):  # a few photos are stored as PNG
        url = f"https://images.pexels.com/photos/{pid}/pexels-photo-{pid}.{ext}?auto=compress&cs=tinysrgb&w=480"
        try:
            raw = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "inspo-app-build"}), timeout=30).read()
            break
        except Exception as e:
            err = e
    if raw is None:
        print(f"{pid}: {err}", file=sys.stderr)
        return pid, False
    try:
        im = Image.open(io.BytesIO(raw)).convert("RGB")
        im.thumbnail((480, 640))
        im.save(out, "WEBP", quality=60, method=6)
        return pid, True
    except Exception as e:
        print(f"{pid}: {e}", file=sys.stderr)
        return pid, False


with ThreadPoolExecutor(8) as ex:
    ok = [pid for pid, good in ex.map(fetch, ids) if good]

for n, start in enumerate(range(0, len(ok), PACK_SIZE)):
    pack = {str(pid): "data:image/webp;base64," + base64.b64encode((CACHE / f"{pid}.webp").read_bytes()).decode()
            for pid in ok[start:start + PACK_SIZE]}
    (DATA / f"photos-{n}.json").write_text(json.dumps(pack, separators=(",", ":")))

# Which pack holds which photo
(DATA / "photo-index.json").write_text(json.dumps({str(pid): i // PACK_SIZE for i, pid in enumerate(ok)}, separators=(",", ":")))
print(f"{len(ok)}/{len(ids)} photos packed", file=sys.stderr)
