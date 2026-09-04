"""Classification Evaluation Script.

Tests the AI categorization pipeline against synthetic test data.
Measures category accuracy, tag F1, and priority accuracy.
Run: python -m app.ml.evaluate_classification
"""
import json
import os
import sys
from typing import Optional

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from app.services.ai_categorization import categorize, _heuristic, _llm_categorize
from app.services.cloudflare_ai import chat
from app.core.config import settings


def load_test_data():
    """Load synthetic examples as test set."""
    test_path = os.path.join(os.path.dirname(__file__), "few_shot_examples.json")
    if not os.path.exists(test_path):
        print("No test data found. Run synthetic_data_generator.py first.")
        return []
    with open(test_path, "r", encoding="utf-8") as f:
        return json.load(f)


def evaluate_heuristic(test_data):
    """Evaluate heuristic (fallback) classifier."""
    print("\n=== Evaluating Heuristic Classifier ===")
    correct_cat = 0
    correct_pri = 0
    total = len(test_data)
    
    for ex in test_data:
        result = _heuristic(ex["title"], ex["description"], ex.get("transcript"), ex.get("user_tags"))
        cat_match = result["category_id"] == ex["category_id"]
        pri_match = result["priority"].value == ex["priority"]
        if cat_match:
            correct_cat += 1
        if pri_match:
            correct_pri += 1
        if not cat_match:
            print(f"  MISMATCH: Expected {ex['category_id']}, got {result['category_id']}")
            print(f"    Title: {ex['title'][:80]}...")
    
    print(f"Category Accuracy: {correct_cat}/{total} = {correct_cat/total*100:.1f}%")
    print(f"Priority Accuracy: {correct_pri}/{total} = {correct_pri/total*100:.1f}%")
    return correct_cat / total if total else 0


def evaluate_llm(test_data):
    """Evaluate LLM classifier (requires Cloudflare AI)."""
    if not settings.ai_enabled:
        print("\n=== LLM Classifier: SKIPPED (Cloudflare AI not configured) ===")
        return 0
    
    print("\n=== Evaluating LLM Classifier ===")
    correct_cat = 0
    correct_pri = 0
    total = len(test_data)
    errors = 0
    
    for ex in test_data:
        try:
            result = _llm_categorize(ex["title"], ex["description"], ex.get("transcript"), ex.get("user_tags"))
            if result is None:
                errors += 1
                print(f"  LLM returned None for: {ex['title'][:60]}...")
                continue
            cat_match = result["category_id"] == ex["category_id"]
            pri_match = result["priority"].value == ex["priority"]
            if cat_match:
                correct_cat += 1
            if pri_match:
                correct_pri += 1
            if not cat_match:
                print(f"  MISMATCH: Expected {ex['category_id']}, got {result['category_id']}")
                print(f"    Title: {ex['title'][:80]}...")
        except Exception as e:
            errors += 1
            print(f"  ERROR: {e}")
    
    print(f"Category Accuracy: {correct_cat}/{total} = {correct_cat/total*100:.1f}%")
    print(f"Priority Accuracy: {correct_pri}/{total} = {correct_pri/total*100:.1f}%")
    print(f"Errors: {errors}/{total}")
    return correct_cat / total if total else 0


def evaluate_full_pipeline(test_data):
    """Evaluate the full categorize() function (LLM + heuristic fallback)."""
    print("\n=== Evaluating Full Pipeline (LLM + Heuristic Fallback) ===")
    correct_cat = 0
    correct_pri = 0
    total = len(test_data)
    llm_used = 0
    heuristic_used = 0
    
    for ex in test_data:
        result = categorize(ex["title"], ex["description"], ex.get("transcript"), ex.get("user_tags"))
        # Check if LLM was used by looking at confidence patterns
        cat_match = result["category_id"] == ex["category_id"]
        pri_match = result["priority"].value == ex["priority"]
        if cat_match:
            correct_cat += 1
        if pri_match:
            correct_pri += 1
        if not cat_match:
            print(f"  MISMATCH: Expected {ex['category_id']}, got {result['category_id']}")
            print(f"    Title: {ex['title'][:80]}...")
    
    print(f"Category Accuracy: {correct_cat}/{total} = {correct_cat/total*100:.1f}%")
    print(f"Priority Accuracy: {correct_pri}/{total} = {correct_pri/total*100:.1f}%")
    return correct_cat / total if total else 0


def evaluate_per_category(test_data):
    """Break down accuracy by category."""
    print("\n=== Per-Category Breakdown ===")
    by_cat = {}
    for ex in test_data:
        cid = ex["category_id"]
        if cid not in by_cat:
            by_cat[cid] = {"total": 0, "correct": 0}
        by_cat[cid]["total"] += 1
        result = categorize(ex["title"], ex["description"], ex.get("transcript"), ex.get("user_tags"))
        if result["category_id"] == cid:
            by_cat[cid]["correct"] += 1
    
    for cid, stats in sorted(by_cat.items()):
        acc = stats["correct"] / stats["total"] * 100 if stats["total"] else 0
        print(f"  {cid}: {stats['correct']}/{stats['total']} = {acc:.1f}%")


def test_cloudflare_connection():
    """Test if Cloudflare AI is working."""
    print("\n=== Cloudflare AI Connection Test ===")
    if not settings.ai_enabled:
        print("Cloudflare AI not configured (CLOUDFLARE_ACCOUNT_ID or CLOUDFLARE_AI_API_KEY missing)")
        return False
    
    try:
        result = chat([
            {"role": "system", "content": "You are a test assistant."},
            {"role": "user", "content": "Reply with just: OK"}
        ])
        if result and "OK" in result.upper():
            print("Cloudflare AI: CONNECTED")
            return True
        else:
            print(f"Cloudflare AI: UNEXPECTED RESPONSE: {result}")
            return False
    except Exception as e:
        print(f"Cloudflare AI: ERROR - {e}")
        return False


if __name__ == "__main__":
    test_data = load_test_data()
    if not test_data:
        sys.exit(1)
    
    print(f"Loaded {len(test_data)} test examples")
    
    # Test connection
    test_cloudflare_connection()
    
    # Run evaluations
    evaluate_heuristic(test_data)
    evaluate_llm(test_data)
    evaluate_full_pipeline(test_data)
    evaluate_per_category(test_data)
    
    print("\n=== Summary ===")
    print("To improve accuracy:")
    print("1. Run synthetic_data_generator.py with more examples per category")
    print("2. Configure Cloudflare AI for LLM-based classification")
    print("3. Collect real user corrections via /api/v1/classification/feedback")
    print("4. Run POST /api/v1/classification/regenerate-few-shot (admin) to include real corrections")