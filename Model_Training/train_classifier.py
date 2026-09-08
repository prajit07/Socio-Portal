"""Train a lightweight, high-accuracy problem classifier aligned to backend taxonomy.

Why this instead of Mistral-7B LoRA on Cloudflare:
- Backend taxonomy is 12 categories (backend/app/ml/taxonomy.json), NOT the 10
  in Model_Training/generate_dataset.py. Training on mismatched labels gives 0% useful accuracy.
- For 12-way topic classification with short citizen reports, TF-IDF + LogisticRegression
  hits 90%+ on synthetic data, runs offline in <10ms, no GPU / Cloudflare quota needed.
- Cloudflare BYO LoRA is valid for generative tasks, but overkill here: needs A100,
  unquantized adapters, manual upload via wrangler. Use this local model as primary,
  keep Cloudflare LLM + heuristic as fallback (already wired in ai_categorization.py).

Usage:
    python train_classifier.py --per-category 300 --model-out category_classifier.joblib

    Diverse-data retraining: NATURAL_TRAIN rows (natural_problems.py) are mixed
    in with --natural-repeat weight, plus optional human corrections:
    corrections.jsonl with {"text": ..., "category_id": ...} per line
    (e.g. exported from /classification/feedback). Unknown category_ids are
    skipped with a warning. HELD_OUT rows are NEVER ingested — eval only.
"""
import argparse
import csv
import json
import os
import random
import sys

BACKEND_DIR = os.path.join(os.path.dirname(__file__), "..", "backend")
sys.path.insert(0, BACKEND_DIR)

from app.ml import CATEGORIES  # noqa: E402
from app.ml.synthetic_data_generator import generate_example, TEMPLATES  # noqa: E402

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, classification_report
import joblib  # noqa: E402


def build_dataset(per_category: int, seed: int = 42, natural_repeat: int = 10,
                   corrections_path: str | None = None, corrections_repeat: int = 10,
                   paraphrases_path: str | None = None, paraphrases_repeat: int = 3):
    random.seed(seed)
    rows = []
    id_to_name = {c["id"]: c["name"] for c in CATEGORIES}
    for cat in CATEGORIES:
        templates = TEMPLATES.get(cat["id"])
        if not templates:
            print(f"WARNING: no templates for {cat['id']}, skipping")
            continue
        for _ in range(per_category):
            ex = generate_example(cat["id"], cat["name"], templates)
            # Combine all user-visible text into one training string
            text = f"{ex.title} {ex.description} {ex.transcript}".strip()
            rows.append({"text": text, "category_id": ex.category_id,
                         "category_name": ex.category_name})
    random.shuffle(rows)
    n_template = len(rows)

    # Diverse natural rows (weighted by repetition so template mass doesn't drown them)
    from natural_problems import NATURAL_TRAIN
    n_natural = 0
    for cid, title, desc in NATURAL_TRAIN:
        if cid not in id_to_name:
            print(f"WARNING: natural row has unknown category {cid!r}, skipping")
            continue
        text = f"{title} {desc}".strip()
        for _ in range(natural_repeat):
            rows.append({"text": text, "category_id": cid, "category_name": id_to_name[cid]})
            n_natural += 1

    # LLM paraphrases of the natural rows — the diversity mass that teaches
    # generalization instead of memorization (see paraphrase.py).
    n_para, n_para_bad = 0, 0
    if paraphrases_path and os.path.exists(paraphrases_path):
        import json as _json2
        with open(paraphrases_path, encoding="utf-8") as f:
            for lineno, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = _json2.loads(line)
                except Exception:
                    n_para_bad += 1
                    continue
                cid, text = obj.get("category_id"), (obj.get("text") or "").strip()
                if cid not in id_to_name or len(text) < 30:
                    n_para_bad += 1
                    continue
                for _ in range(paraphrases_repeat):
                    rows.append({"text": text, "category_id": cid, "category_name": id_to_name[cid]})
                    n_para += 1
    elif paraphrases_path:
        print(f"No paraphrases file at {paraphrases_path} — skipping (run paraphrase.py)")

    # Human corrections (highest value per row — user-verified real reports)
    n_corr, n_bad = 0, 0
    if corrections_path and os.path.exists(corrections_path):
        import json as _json
        with open(corrections_path, encoding="utf-8") as f:
            for lineno, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = _json.loads(line)
                except Exception:
                    print(f"WARNING: corrections line {lineno} is not JSON, skipping")
                    n_bad += 1
                    continue
                cid, text = obj.get("category_id"), (obj.get("text") or "").strip()
                if cid not in id_to_name or not text:
                    print(f"WARNING: corrections line {lineno} bad id/text, skipping")
                    n_bad += 1
                    continue
                for _ in range(corrections_repeat):
                    rows.append({"text": text, "category_id": cid, "category_name": id_to_name[cid]})
                    n_corr += 1
    elif corrections_path:
        print(f"No corrections file at {corrections_path} — skipping")

    random.shuffle(rows)
    print(f"Built {len(rows)} examples ({n_template} template + {n_natural} natural + "
          f"{n_para} paraphrases + "
          f"{n_corr} corrections, {n_bad} bad) across {len(id_to_name)} categories")
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-category", type=int, default=300)
    ap.add_argument("--model-out", default=os.path.join(os.path.dirname(__file__), "category_classifier.joblib"))
    ap.add_argument("--csv-out", default=os.path.join(os.path.dirname(__file__), "training_data_v2.csv"))
    ap.add_argument("--natural-repeat", type=int, default=10,
                    help="repetition weight for NATURAL_TRAIN rows (0 to disable)")
    ap.add_argument("--corrections", default=os.path.join(os.path.dirname(__file__), "corrections.jsonl"),
                    help="JSONL of {text, category_id}; missing file is skipped")
    ap.add_argument("--corrections-repeat", type=int, default=10)
    ap.add_argument("--no-corrections", action="store_true")
    ap.add_argument("--paraphrases", default=os.path.join(os.path.dirname(__file__), "paraphrases.jsonl"),
                    help="JSONL of {text, category_id, source_idx}; run paraphrase.py first")
    ap.add_argument("--paraphrases-repeat", type=int, default=3)
    ap.add_argument("--no-paraphrases", action="store_true")
    args = ap.parse_args()

    rows = build_dataset(args.per_category, natural_repeat=args.natural_repeat,
                         corrections_path=None if args.no_corrections else args.corrections,
                         corrections_repeat=args.corrections_repeat,
                         paraphrases_path=None if args.no_paraphrases else args.paraphrases,
                         paraphrases_repeat=args.paraphrases_repeat)

    # Save transparent CSV (title+description style, aligned to backend labels)
    with open(args.csv_out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["text", "category_id", "category_name"])
        w.writeheader()
        w.writerows(rows)
    print(f"Saved {args.csv_out}")

    X = [r["text"] for r in rows]
    y = [r["category_id"] for r in rows]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y)

    pipe = Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), max_features=20000,
                                  sublinear_tf=True, min_df=2)),
        ("clf", LogisticRegression(max_iter=1000, C=4.0, n_jobs=None)),
    ])
    pipe.fit(X_train, y_train)
    pred = pipe.predict(X_test)
    acc = accuracy_score(y_test, pred)
    print(f"\nTest accuracy: {acc*100:.2f}% ({len(y_test)} samples)")
    print(classification_report(y_test, pred, zero_division=0))

    joblib.dump({"pipeline": pipe,
                 "categories": [{"id": c["id"], "name": c["name"]} for c in CATEGORIES]},
                args.model_out)
    print(f"Saved model -> {args.model_out}")
    if acc < 0.85:
        print("NOTE: accuracy <85% suggests template overlap; increase --per-category or add keywords to taxonomy.json")
    return 0 if acc >= 0.80 else 2


if __name__ == "__main__":
    raise SystemExit(main())
