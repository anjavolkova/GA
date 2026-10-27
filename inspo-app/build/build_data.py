"""Build data/prompts.json for the web app from the final Iteration 3 database.

Re-runs the content-based recommender from
"Iteration 3 - Prompt database and recommender system - APIs.ipynb"
(soup = Title + Color + Pexels alt, CountVectorizer, cosine similarity)
and stores each prompt's thumbs-up and thumbs-down neighbours, so the
browser can serve the same recommendations without Python.
"""
import json
import re
import sys
from pathlib import Path

import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

ROOT = Path(__file__).resolve().parents[2]
# Prompts left out of the app (the recommender still runs on the full database)
EXCLUDE = {759}  # "Hood Childrens Holiday Track"
OUT = Path(__file__).resolve().parents[1] / "data" / "prompts.json"

pexelsdf = pd.read_csv(ROOT / "colorstitlespexelsdf.csv", index_col=0)

# Same soup and matrix as the notebook
# .map(str) turns missing values into "nan", as .astype(str) did in 2022's pandas
pexelsdf["soup"] = pexelsdf["Title"].map(str) + pexelsdf["Color"].map(str) + pexelsdf["alt"].map(str)
count = CountVectorizer(stop_words="english")
count_matrix1 = count.fit_transform(pexelsdf["soup"])
cosine_sim1 = cosine_similarity(count_matrix1, count_matrix1)


def neighbours(index, start, stop):
    sim_scores = sorted(enumerate(cosine_sim1[index]), key=lambda x: x[1], reverse=True)
    return [int(i) for i, _ in sim_scores[start:stop] if i != index and i not in EXCLUDE]


prompts = []
for i, row in pexelsdf.iterrows():
    if i in EXCLUDE:
        continue
    url = row["url"] if isinstance(row["url"], str) else ""
    m = re.search(r"-(\d+)/?$", url)
    prompts.append({
        "id": int(i),
        # drop U+FFFD left over from encoding errors in the scraped titles
        "t": re.sub(r"\s+", " ", str(row["Title"]).replace("\ufffd", "")).strip(),
        "c": [h.upper() for h in re.findall(r"#[0-9a-fA-F]{6}", str(row["Color"]))],
        "p": int(m.group(1)) if m else None,
        "u": url or None,
        "a": row["alt"] if isinstance(row["alt"], str) else None,
        # pthumbs_up: top 10; pthumbs_down: positions 200-210
        "up": neighbours(i, 0, 11)[:10],
        "down": neighbours(i, 200, 210),
    })

OUT.write_text(json.dumps({"source": "colorstitlespexelsdf.csv", "prompts": prompts}, separators=(",", ":")))
print(f"{len(prompts)} prompts -> {OUT}", file=sys.stderr)
