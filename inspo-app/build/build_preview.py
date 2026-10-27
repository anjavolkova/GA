"""Build a self-contained preview of the app for a static website.

Takes a hand-picked list of prompt ids, reruns the notebook's recommender on
just those prompts, and writes a folder that any static host can serve:
index.html, data/prompts.json, data/stories.json, data/photo-index.json and
one image file per photo and per VQGAN painting.

    python3 build/build_preview.py IDS_FILE PHOTO_CACHE PAINTINGS_DIR OUT_DIR

PHOTO_CACHE is the folder build_images.py downloaded the Pexels thumbnails to;
PAINTINGS_DIR is the output folder of build_paintings.py.
"""
import json
import shutil
import sys
from pathlib import Path

import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

APP = Path(__file__).resolve().parents[1]
ROOT = APP.parent
ids_file, photo_cache, paintings_dir, out = (Path(a) for a in sys.argv[1:5])

ids = [int(l) for l in ids_file.read_text().split() if l.strip().isdigit()]
full = {p["id"]: p for p in json.loads((APP / "data" / "prompts.json").read_text())["prompts"]}
stories = json.loads((APP / "data" / "stories.json").read_text())

# Same soup and matrix as the notebook, over the full database
pexelsdf = pd.read_csv(ROOT / "colorstitlespexelsdf.csv", index_col=0)
pexelsdf["soup"] = pexelsdf["Title"].map(str) + pexelsdf["Color"].map(str) + pexelsdf["alt"].map(str)
count_matrix1 = CountVectorizer(stop_words="english").fit_transform(pexelsdf["soup"])
cosine_sim1 = cosine_similarity(count_matrix1, count_matrix1)

# Thumbs up: the 10 closest prompts in the preview. Thumbs down: the notebook
# used positions 200-210 of ~1,200; keep the same relative distance here.
down_start = round(200 / len(full) * (len(ids) - 1))

(out / "data" / "photos").mkdir(parents=True, exist_ok=True)
(out / "data" / "paintings").mkdir(parents=True, exist_ok=True)
prompts, photo_index, paintings = [], {}, 0
for i in ids:
    p = dict(full[i])
    ranked = sorted((j for j in ids if j != i), key=lambda j: cosine_sim1[i][j], reverse=True)
    p["up"], p["down"] = ranked[:10], ranked[down_start:down_start + 10]
    photo = out / "data" / "photos" / f"{p['p']}.webp"
    if p["p"] and (photo_cache / photo.name).exists():
        shutil.copy(photo_cache / photo.name, photo)
    if p["p"] and photo.exists():  # copied now, or kept from an earlier build
        photo_index[str(p["p"])] = f"data/photos/{photo.name}"
    if (paintings_dir / f"{i}.webp").exists():
        shutil.copy(paintings_dir / f"{i}.webp", out / "data" / "paintings" / f"{i}.webp")
        p["g"] = f"data/paintings/{i}.webp"
        paintings += 1
    prompts.append(p)

(out / "data" / "prompts.json").write_text(json.dumps({"source": "colorstitlespexelsdf.csv", "prompts": prompts}, separators=(",", ":")))
(out / "data" / "stories.json").write_text(json.dumps({str(i): stories[str(i)] for i in ids}, ensure_ascii=False, separators=(",", ":")))
(out / "data" / "photo-index.json").write_text(json.dumps(photo_index, separators=(",", ":")))
# The app page is written for claude.ai, which adds the document shell; add it here
(out / "index.html").write_text('<!doctype html>\n<html lang="en">\n<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n' + (APP / "index.html").read_text())
print(f"{len(prompts)} prompts, {len(photo_index)} photos, {paintings} paintings -> {out}", file=sys.stderr)
