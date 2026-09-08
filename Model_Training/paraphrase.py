"""Paraphrase augmentation for the classifier training set.

Expands each NATURAL_TRAIN row into K diverse rewrites via Cloudflare LLM so
training sees varied phrasing instead of 24 memorized strings. Output feeds
train_classifier.py (--paraphrases).

Output: paraphrases.jsonl with {"text", "category_id", "source_idx"} per line.
Resumable: existing lines for an index are kept, only missing ones generated.
Validation per paraphrase: non-empty, >30 chars, not identical to the source,
not an exact duplicate of a sibling. Failures retry once, then skip.

Usage:
    python paraphrase.py [--per-row 8] [--out paraphrases.jsonl]
Requires CLOUDFLARE_ACCOUNT_ID + CLOUDFLARE_AI_API_KEY (backend/.env).
~192 short LLM calls for defaults; well within the free daily allowance.
"""
import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from natural_problems import NATURAL_TRAIN  # noqa: E402
from app.services.cloudflare_ai import chat  # noqa: E402

# Rotated styles force lexical/syntactic diversity across the K rewrites.
STYLES = [
    "Rewrite in completely different words. Change all place names, numbers and names.",
    "Make it much shorter, like an SMS complaint under 30 words.",
    "Make it longer with extra concrete detail (names, dates, places).",
    "Mix in Hindi/Hinglish words naturally, as a villager would speak.",
    "Write it as an elderly person dictating to someone writing for them.",
    "Write it as an angry complaint demanding immediate action.",
    "Keep the same problem but change every specific detail (different village, different day).",
    "Rewrite as a formal written application addressed to the authorities.",
]


def paraphrase_once(source: str, style: str) -> str | None:
    out = chat(
        [
            {"role": "system",
             "content": "You rewrite citizen problem reports. Preserve the exact problem and "
                        "meaning. Reply with ONLY the rewritten report, no preamble."},
            {"role": "user",
             "content": f"{style}\n\nOriginal report:\n{source}"},
        ],
        max_tokens=220,
        temperature=0.75,
    )
    if not out:
        return None
    text = out.strip().strip('"')
    if len(text) < 30 or text.lower() == source.lower():
        return None
    return text


def load_existing(path: str) -> dict[int, list[dict]]:
    done: dict[int, list[dict]] = {}
    if not os.path.exists(path):
        return done
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                done.setdefault(int(obj["source_idx"]), []).append(obj)
            except Exception:
                continue
    return done


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-row", type=int, default=8)
    ap.add_argument("--out", default=os.path.join(os.path.dirname(__file__), "paraphrases.jsonl"))
    args = ap.parse_args()

    done = load_existing(args.out)
    total_new, total_skip = 0, 0
    with open(args.out, "a", encoding="utf-8") as f:
        for idx, (cid, title, desc) in enumerate(NATURAL_TRAIN):
            have = len(done.get(idx, []))
            need = max(0, args.per_row - have)
            if need == 0:
                print(f"[{idx+1}/{len(NATURAL_TRAIN)}] {cid}: already have {have}, skipping", flush=True)
                continue
            source = f"{title}. {desc}"
            seen = {o["text"].lower() for o in done.get(idx, [])}
            made = 0
            for attempt in range(need + 4):  # headroom for retries/skips
                if made >= need:
                    break
                style = STYLES[(have + made + attempt) % len(STYLES)]
                try:
                    text = paraphrase_once(source, style)
                except Exception as e:
                    print(f"  LLM error ({type(e).__name__}), retrying...", flush=True)
                    time.sleep(5)
                    continue
                finally:
                    time.sleep(2)  # stay under Cloudflare rate limits on bulk runs
                if not text or text.lower() in seen or text.lower() == source.lower():
                    continue
                seen.add(text.lower())
                f.write(json.dumps({"text": text, "category_id": cid,
                                    "source_idx": idx}, ensure_ascii=False) + "\n")
                f.flush()
                made += 1
                total_new += 1
            if made < need:
                total_skip += need - made
                print(f"[{idx+1}/{len(NATURAL_TRAIN)}] {cid}: only {made}/{need} (skipped {need-made})", flush=True)
            else:
                print(f"[{idx+1}/{len(NATURAL_TRAIN)}] {cid}: +{made} paraphrases", flush=True)
    print(f"Done. new={total_new} short={total_skip} file={args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
