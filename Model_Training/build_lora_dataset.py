"""Phase 0: build LoRA-ready dataset from the 10-label synthetic themes.

Input : generate_dataset.py THEMES (10 SIH labels) — the only labeled source.
Output: lora_train.jsonl / lora_val.jsonl with AutoTrain-compatible fields:
    {"prompt": "<raw user text, NO chat wrapper>", "response": "<exact label>"}
plus lora_dataset.csv (prompt,response) for the AutoTrain UI CSV upload path.

Why raw prompt (no ### Human/### Assistant wrapper): inference uses
`raw: true` with a messages template (docs), so the adapter must learn
P(label | problem text), not wrapper tokens. The probe script sends the same
raw problem text at inference — train/inference formats match.

Stratified 90/10 split, seed fixed for reproducibility.
Usage: python build_lora_dataset.py --per-category 200
"""
import argparse
import csv
import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(__file__))
from generate_dataset import THEMES, CATEGORIES  # noqa: E402
from labels10 import LABELS_10  # noqa: E402

assert CATEGORIES == LABELS_10, f"generate_dataset labels drifted: {CATEGORIES}"

PHRASINGS = [
    "Categorize this societal challenge: {t}",
    "{t}",
    "Problem statement: {t}",
    "Citizen report: {t}",
]


def build(per_category: int, seed: int = 42):
    rng = random.Random(seed)
    rows = []
    for cat in LABELS_10:
        for theme in THEMES[cat]:
            for _ in range(max(1, per_category // len(THEMES[cat]))):
                t = rng.choice(PHRASINGS).format(t=theme)
                # Light augmentation: Jharkhand place names teach location invariance
                if rng.random() < 0.3:
                    t += f" in {rng.choice(['Ranchi', 'Dhanbad', 'Bokaro', 'Jamshedpur', 'Hazaribagh', 'Deoghar', 'rural Jharkhand'])}"
                rows.append({"prompt": t, "response": cat})
    rng.shuffle(rows)
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-category", type=int, default=200)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--val-frac", type=float, default=0.1)
    a = ap.parse_args()
    base = os.path.dirname(__file__)

    rows = build(a.per_category, a.seed)
    n_val = int(len(rows) * a.val_frac)
    val, train = rows[:n_val], rows[n_val:]

    for name, split in (("lora_train.jsonl", train), ("lora_val.jsonl", val)):
        with open(os.path.join(base, name), "w", encoding="utf-8") as f:
            for r in split:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with open(os.path.join(base, "lora_dataset.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["prompt", "response"])
        w.writeheader()
        w.writerows(rows)
    print(f"train={len(train)} val={len(val)} total={len(rows)} labels=10")
    print("wrote lora_train.jsonl lora_val.jsonl lora_dataset.csv")


if __name__ == "__main__":
    main()
