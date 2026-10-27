# inspo.ai web app

A working version of the inspo.ai prototype, built on the final database from
`Iteration 3 - Prompt database and recommender system - APIs.ipynb`.
Nothing outside this folder was changed.

## What runs where

| Part | Source |
| --- | --- |
| Titles | GPT-2 titles in `colorstitlespexelsdf.csv` (1,200 prompts) |
| Palettes | the GPT-3 hex codes in the same file |
| Photos | the Pexels photo for each title, stored as WebP thumbnails in `data/photos-*.json` |
| Like / dislike | the notebook's recommender (soup = title + palette + Pexels alt, `CountVectorizer`, cosine similarity). Like queues the top 10 matches (`pthumbs_up`); dislike queues positions 200–210 (`pthumbs_down`). |
| Story plots | one plot per prompt, three sentences at most, written by Claude from the title and photo description (`data/stories.json`, rytr in the 2022 prototype) |
| Likes, tracker | saved per person on claude.ai; in this browser only when opened anywhere else |

Prompt 759 ("Hood Childrens Holiday Track") is left out of the app (`EXCLUDE` in `build/build_data.py`).

## Rebuilding the data

```sh
pip install pandas scikit-learn pillow
python3 build/build_data.py                 # data/prompts.json
python3 build/build_images.py /tmp/photos   # data/photo-index.json + data/photos-*.json
python3 build/build_stories.py              # data/stories.json from build/stories/*.json
```

11 of the 931 Pexels photos are no longer on Pexels; those prompts show their palette instead.

## Running locally

```sh
python3 -m http.server   # then open http://localhost:8000/
```
