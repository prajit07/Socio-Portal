"""Phase 1 verify: probe uploaded LoRA with 20 real-format problems.

Sends raw problem text (same format as training prompts) via
POST /ai/run/<lora-model> {messages, raw:true, lora:<finetune>, max_tokens:20}
and checks output names one of the 10 canonical labels (labels10.py).

20 probes = 2 per label, hand-written (not synthetic templates) so a
template-memorizing adapter scores poorly here by design.
Usage: python probe_lora.py --finetune jharkhand-classifier
  (needs CLOUDFLARE_API_TOKEN + CLOUDFLARE_ACCOUNT_ID env)
"""
import argparse
import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(__file__))
from labels10 import LABELS_10  # noqa: E402

# Canonical prompt MUST match training template byte-for-byte (raw:true
# inference continues verbatim). Single source of truth lives in backend.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
try:
    from app.services.lora_classifier import build_prompt  # noqa: E402
except ImportError:
    # Fallback for machines without backend deps: duplicate of the template.
    def build_prompt(text: str) -> str:  # noqa: D103
        print("WARNING: backend import failed — using inline template copy", file=sys.stderr)
        return f"### Human: Categorize this societal challenge: {(text or '').strip()} ### Assistant:"

LORA_MODEL = "@cf/mistralai/mistral-7b-instruct-v0.2-lora"

# (problem text, expected 10-label) — 2 per label, natural phrasing
PROBES = [
    ("Government school in our block has only two teachers for 200 students", "Education"),
    ("Girls dropping out as the village school has no functional toilets", "Education"),
    ("Tomato farmers need cold storage near Ranchi mandi to avoid distress sale", "Agriculture"),
    ("Paddy crop wilting as the canal breach was never repaired", "Agriculture"),
    ("PHC has no doctor for weeks, patients travel 40km for fever treatment", "Healthcare"),
    ("Children malnourished in the tribal hamlet, anganwadi stocks empty", "Healthcare"),
    ("Handpumps yield fluoride-laced water, skin lesions reported", "Water Resources"),
    ("Village pond dried up, summer drinking water tanker never arrives", "Water Resources"),
    ("Illegal mining dust coats our homes, breathing difficulty at night", "Environment"),
    ("Forest patch cleared for road, wildlife sightings gone", "Environment"),
    ("Eight-hour daily power cuts, transformers trip every evening", "Energy"),
    ("Tribal homes still burn kerosene, solar micro-grid never installed", "Energy"),
    ("Monsoon floods the market road every year, drains choked with silt", "Urban Development"),
    ("Traffic jam at the city crossing, no signal for months", "Urban Development"),
    ("Public office has steps only, wheelchair users cannot enter", "Accessibility"),
    ("Elderly cannot board overcrowded buses, no reserved seats honoured", "Accessibility"),
    ("Caste certificate stuck for months, clerk demands a bribe", "Public Administration"),
    ("Land records still on paper, mutation requests gather dust", "Public Administration"),
    ("Tribal artisans cannot reach buyers, middlemen take most of the price", "Rural Livelihoods"),
    ("MGNREGA wages delayed three months, families migrate for work", "Rural Livelihoods"),
]


def infer(problem: str, token: str, acct: str, finetune: str) -> str:
    url = f"https://api.cloudflare.com/client/v4/accounts/{acct}/ai/run/{LORA_MODEL}"
    body = {"messages": [{"role": "user", "content": build_prompt(problem)}],
            "raw": True, "lora": finetune, "max_tokens": 20, "temperature": 0.0}
    req = urllib.request.Request(url, data=json.dumps(body).encode(), method="POST",
                                 headers={"Authorization": f"Bearer {token}",
                                          "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        res = json.loads(r.read().decode())["result"]
    text = res.get("response", "") if isinstance(res, dict) else str(res)
    for lab in LABELS_10:  # exact-label match (case-insensitive substring)
        if lab.lower() in text.lower():
            return lab
    return f"UNMAPPED:{text[:80]}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--finetune", default="jharkhand-classifier")
    a = ap.parse_args()
    token = os.environ.get("CLOUDFLARE_API_TOKEN", "")
    acct = os.environ.get("CLOUDFLARE_ACCOUNT_ID", "")
    if not (token and acct):
        raise SystemExit("set CLOUDFLARE_API_TOKEN and CLOUDFLARE_ACCOUNT_ID env vars")
    ok = 0
    for text, exp in PROBES:
        try:
            got = infer(text, token, acct, a.finetune)
        except Exception as e:
            got = f"ERROR:{e}"
        mark = "OK " if got == exp else "MISS"
        if got == exp:
            ok += 1
        print(f"[{mark}] exp={exp:22s} got={got:22s} | {text[:60]}")
    print(f"\nprobe accuracy: {ok}/{len(PROBES)} = {100*ok/len(PROBES):.0f}% "
          f"(cutover bar: >=80% AND Phase-3 real-data eval)")


if __name__ == "__main__":
    main()
