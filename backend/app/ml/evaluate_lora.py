"""Phase 3: grade classifiers before trusting the LoRA cutover.

A) Synthetic holdout (always runs): Model_Training/lora_val.jsonl has 10-label
   ground truth. Baseline categorize() output is mapped to expected backend ids
   via LABEL_MAP_10_TO_12; reports baseline accuracy + per-label hits. LoRA arm
   runs only when settings.lora_enabled (else reports 'not configured').
B) Real Neon sample (--from-db N): read-only pull of N problems (title,
   description), runs baseline vs LoRA, reports agreement rate and writes
   lora_real_eval.csv (problem_id, text, baseline, lora) for MANUAL labeling —
   the DB has no ground-truth labels, so human grades the CSV. That graded CSV
   is the cutover evidence (bar: LoRA >=80% AND >= baseline).

Run: python -m app.ml.evaluate_lora [--from-db 200]
"""
import csv
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from app.services.ai_categorization import categorize
from app.services.lora_classifier import LABEL_MAP_10_TO_12, classify as lora_classify
from app.core.config import settings


def eval_holdout(val_path: str, limit: int = 0):
    rows = [json.loads(l) for l in open(val_path, encoding="utf-8")]
    if limit:
        rows = rows[:limit]
    base_ok = lora_ok = lora_ran = 0
    for r in rows:
        exp_backend = LABEL_MAP_10_TO_12[r["response"]][0]
        base = categorize(r["prompt"], "", None, [])
        if base.get("category_id") == exp_backend:
            base_ok += 1
        lo = lora_classify(r["prompt"], "", None)
        if lo is not None:
            lora_ran += 1
            if lo.get("category_id") == exp_backend:
                lora_ok += 1
    n = len(rows)
    print(f"[holdout] n={n} baseline={100*base_ok/n:.1f}%", end="")
    if lora_ran:
        print(f" lora={100*lora_ok/lora_ran:.1f}% (ran {lora_ran})")
    else:
        print(" lora=NOT CONFIGURED (set CLOUDFLARE_LORA_FINETUNE or MODAL_ENDPOINT)")


def eval_db(n: int):
    from sqlalchemy import create_engine, text
    if "placeholder" in settings.DATABASE_URL:
        print("[db] DATABASE_URL is placeholder — configure backend/.env first")
        return
    eng = create_engine(settings.DATABASE_URL)
    with eng.connect() as c:
        rows = c.execute(text(
            "SELECT id, title, description FROM problems ORDER BY created_at DESC LIMIT :n"),
            {"n": n}).mappings().all()
    print(f"[db] pulled {len(rows)} problems (read-only)")
    agree = lora_ran = 0
    out = []
    for r in rows:
        base = categorize(r["title"] or "", r["description"] or "", None, [])
        lo = lora_classify(r["title"] or "", r["description"] or "", None)
        lora_cat = (lo or {}).get("category_id", "")
        if lo is not None:
            lora_ran += 1
            agree += base.get("category_id") == lora_cat
        out.append({"problem_id": r["id"], "text": f"{r['title']} {r['description']}"[:300],
                    "baseline": base.get("category_id"), "lora": lora_cat,
                    "human_label10": ""})
    path = os.path.join(os.path.dirname(__file__), "lora_real_eval.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        csv.DictWriter(f, fieldnames=["problem_id", "text", "baseline", "lora", "human_label10"]).writeheader()
        csv.DictWriter(f, fieldnames=["problem_id", "text", "baseline", "lora", "human_label10"]).writerows(out)
    print(f"[db] wrote {path} — fill human_label10, then grade")
    if lora_ran:
        print(f"[db] baseline-vs-lora agreement: {100*agree/lora_ran:.1f}% ({agree}/{lora_ran})")
    else:
        print("[db] lora NOT CONFIGURED — baseline column only")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--from-db", type=int, default=0)
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()
    here = os.path.dirname(__file__)
    # Repo-relative by default; override with LORA_VAL_PATH env var if needed.
    vp = os.environ.get(
        "LORA_VAL_PATH",
        os.path.normpath(os.path.join(here, "..", "..", "..", "Model_Training", "lora_val.jsonl")),
    )
    if os.path.exists(vp):
        eval_holdout(vp, a.limit)
    else:
        print(f"[holdout] missing {vp} — run Model_Training/build_lora_dataset.py first")
    if a.from_db:
        eval_db(a.from_db)
