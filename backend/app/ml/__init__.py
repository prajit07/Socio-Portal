"""ML package exports."""
import json
import os

_TAXONOMY_PATH = os.path.join(os.path.dirname(__file__), "taxonomy.json")

with open(_TAXONOMY_PATH, "r", encoding="utf-8") as f:
    TAXONOMY = json.load(f)

CATEGORIES = TAXONOMY["categories"]
ID_TO_NAME = {c["id"]: c["name"] for c in CATEGORIES}
NAME_TO_ID = {c["name"]: c["id"] for c in CATEGORIES}
ALL_KEYWORDS = {c["id"]: c["keywords"] for c in CATEGORIES}

__all__ = ["CATEGORIES", "ID_TO_NAME", "NAME_TO_ID", "ALL_KEYWORDS", "TAXONOMY"]