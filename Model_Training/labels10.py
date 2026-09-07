"""Canonical 10 SIH problem-statement labels (training label space).

Backend app taxonomy has 12 different ids (backend/app/ml/taxonomy.json).
LoRA trains on THESE 10; backend maps 10->12 at inference (see
backend/app/services/lora_classifier.py LABEL_MAP_10_TO_12).
"""
LABELS_10 = [
    "Education",
    "Agriculture",
    "Healthcare",
    "Water Resources",
    "Environment",
    "Energy",
    "Urban Development",
    "Accessibility",
    "Public Administration",
    "Rural Livelihoods",
]
