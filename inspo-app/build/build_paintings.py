"""Generate a VQGAN+CLIP painting for each prompt listed in an ids file.

Uses the multimodalart/vqgan-clip-video Space on Hugging Face (ZeroGPU).
The GPT-2 title is the image prompt and the prompt id is the seed, so every
image can be regenerated. Images already in the output folder are skipped,
and the run stops cleanly when the daily GPU quota runs out, so rerunning
continues where it left off.

    python3 build/build_paintings.py build/preview_ids.txt OUT_DIR [STEPS, default 250] [MAX_IMAGES]

MAX_IMAGES caps one run, to stay inside the daily free GPU quota.
"""
import io
import json
import sys
import time
from pathlib import Path

from gradio_client import Client
from PIL import Image

DATA = Path(__file__).resolve().parents[1] / "data"
ids_file, out_dir = Path(sys.argv[1]), Path(sys.argv[2])
steps = int(sys.argv[3]) if len(sys.argv) > 3 else 250
max_images = int(sys.argv[4]) if len(sys.argv) > 4 else None
out_dir.mkdir(parents=True, exist_ok=True)

prompts = {p["id"]: p for p in json.loads((DATA / "prompts.json").read_text())["prompts"]}
ids = [int(l) for l in ids_file.read_text().split() if l.strip().isdigit()]
todo = [i for i in ids if not (out_dir / f"{i}.webp").exists()][:max_images]
done = sum((out_dir / f"{i}.webp").exists() for i in ids)
print(f"{done} of {len(ids)} done, making {len(todo)} this run", flush=True)

client = Client("multimodalart/vqgan-clip-video", verbose=False)
for n, pid in enumerate(todo, 1):
    title = prompts[pid]["t"]
    started = time.time()
    try:
        img, status = client.predict(
            prompt=title, iterations=steps, seed=pid, clip_model="ViT-B/16", init_image=None,
            use_compiled=True, width=512, height=512, cutn=32, lr=0.1, api_name="/generate")
    except Exception as e:
        msg = str(e)
        if "quota" in msg.lower() or "limit" in msg.lower():
            print(f"GPU quota used up after {n - 1} images; run again later to continue.", flush=True)
            break
        print(f"{pid} failed: {msg[:200]}", flush=True)
        continue
    Image.open(img).convert("RGB").save(out_dir / f"{pid}.webp", "WEBP", quality=82, method=6)
    print(f"[{n}/{len(todo)}] {pid} {title!r} {time.time() - started:.1f}s | {status.splitlines()[0]}", flush=True)
