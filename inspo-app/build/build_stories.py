"""Merge the hand-written story plots in build/stories/*.json into data/stories.json.

One plot per prompt, at most three sentences. Fails if a prompt is missing
a plot or a plot runs longer.
"""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE.parent / "data"

stories = {}
for f in sorted((HERE / "stories").glob("*.json")):
    stories.update(json.loads(f.read_text()))

ids = {str(p["id"]) for p in json.loads((DATA / "prompts.json").read_text())["prompts"]}
missing = sorted(ids - stories.keys(), key=int)
too_long = [k for k, v in stories.items() if len(re.findall(r"[.!?](?=\s+[A-Z'\"]|$)", v.strip())) > 3]
if missing or too_long:
    sys.exit(f"missing: {missing}\nover three sentences: {too_long}")

out = {k: stories[k] for k in sorted(ids, key=int)}
(DATA / "stories.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")))
print(f"{len(out)} story plots -> {DATA / 'stories.json'}", file=sys.stderr)
