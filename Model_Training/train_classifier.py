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


def build_dataset(per_category: int, seed: int = 42):
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
    print(f"Built {len(rows)} examples across {len(id_to_name)} categories")
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-category", type=int, default=300)
    ap.add_argument("--model-out", default=os.path.join(os.path.dirname(__file__), "category_classifier.joblib"))
    ap.add_argument("--csv-out", default=os.path.join(os.path.dirname(__file__), "training_data_v2.csv"))
    args = ap.parse_args()

    rows = build_dataset(args.per_category)

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
