"""Synthetic evaluation of the classification system (local model + pipeline).

Covers what evaluate_classification.py misses:
  Set A — fresh template samples (different seed than training) -> local.predict()
  Set B — hand-written natural problems (non-template phrasing) -> local.predict()
  Set C — Set B through full categorize() with per-call path + latency report

Honesty notes: Set A shares templates with training data, so it measures
template fit, not generalization. Set B is the honest signal.

Run: python -m app.ml.synthetic_eval [--n 5] [--skip-pipeline]
"""
import argparse
import json
import os
import random
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from app.ml import CATEGORIES
from app.ml.synthetic_data_generator import generate_example, TEMPLATES
from app.services import local_classifier as local
from app.services.ai_categorization import categorize
from app.core.config import settings

# Hand-written natural citizen reports: 2 per category, deliberately NOT in
# generator-template phrasing (mixed Hindi words, specifics, varied structure).
NATURAL = [
    ("water_sanitation", "Handpump water smells of chemicals",
     "Two handpumps in our tola give yellow water that smells of medicine. Children got rashes after bathing. We complained to the panchayat twice."),
    ("water_sanitation", "Drainage overflow outside school gate",
     "Nali ka paani is flowing onto the road in front of the primary school. Kids wade through dirty water every morning. Mosquitoes have increased."),
    ("waste_management", "Garbage truck skips our lane",
     "The nagar nigam truck has not entered our gali for three weeks. Piles of kachra rot near the transformer, dogs tear the bags open every night."),
    ("waste_management", "Medical waste dumped behind clinic",
     "Used syringes and bandages are thrown on the vacant plot behind the private clinic. Ragpicker children play there."),
    ("health", "PHC runs without doctor",
     "Our primary health centre has had no doctor for two months. The pharmacist gives the same pills for every illness. A pregnant woman had to be rushed 40km last week."),
    ("health", "Dengue cases rising, no fogging",
     "Seven dengue cases in our mohalla this month. Nobody from the municipality has come for fogging or checked the coolers."),
    ("education", "School roof leaks in monsoon",
     "Class 6 and 7 sit in one room because rainwater pours through the roof of two classrooms. Books get wet, attendance has dropped."),
    ("education", "No science teacher for board class",
     "Class 10 has had no science teacher since July. Exams are four months away and the syllabus is half done."),
    ("transportation", "Bus stop removed, long walk",
     "The bus stop near our colony was removed during road widening. Elderly people now walk 2km to catch a bus."),
    ("transportation", "Speeding trucks at night",
     "Loaded trucks race through our residential street after midnight. Two goats were crushed last month and children play there in the day."),
    ("energy_environment", "Transformer burns every summer",
     "Our colony transformer has burnt out three times this summer. Each repair takes four days and the inverter batteries die."),
    ("energy_environment", "Factory smoke at night",
     "A nearby plant releases thick smoke after 11pm. Mornings smell of chemicals and several elders have breathing trouble."),
    ("agriculture", "Canal breach unrepaired",
     "The distributary canal breached near our fields in July and is still open. Paddy seedlings in six acres are drying."),
    ("agriculture", "No MSP counter for paddy",
     "This season there is no procurement counter within 30km. Traders offer far below MSP and small farmers are forced to sell."),
    ("housing_urban", "Slum eviction without notice",
     "Families in our basti got verbal orders to vacate in a week. No survey, no rehabilitation plan. Children study in the local school."),
    ("housing_urban", "Illegal floors on old building",
     "The landlord added two illegal floors on a 40-year-old building. Cracks have appeared on the ground floor walls."),
    ("digital_governance", "Ration card names deleted",
     "Three family members vanished from the ration list after e-KYC. The dealer refuses grain and the portal shows an error."),
    ("digital_governance", "Pension stopped without reason",
     "My mother's widow pension stopped three months ago. The block office says 'server problem' every visit."),
    ("livelihood", "MGNREGA wages pending",
     "Job card holders finished pond work in June but wages for 40 days are still pending. Families are borrowing for food."),
    ("livelihood", "SHG loan rejected",
     "Our women's self-help group applied for a mudra loan to buy sewing machines. The bank rejected it without giving a reason in writing."),
    ("disaster", "River embankment weak",
     "The river bund near our village developed rat holes and seepage. Last year's flood entered 200 homes. No repair yet."),
    ("disaster", "Landslide blocks hill road",
     "Loose boulders fall on the hill road every heavy rain. A bus was trapped for six hours last week."),
    ("public_safety", "Streetlights dead for months",
     "All six streetlights on our lane are dead since winter. Two phone snatchings happened this month after dark."),
    ("public_safety", "Harassment near bus stand",
     "Drunk men gather near the bus stand every evening and harass schoolgirls. Police patrol never comes to this side."),
]


def fresh_template_samples(n_per_cat: int, seed: int = 1234):
    """Samples from the same templates but a different RNG stream than training."""
    rng_state = random.getstate()
    random.seed(seed)
    try:
        out = []
        for cat in CATEGORIES:
            templates = TEMPLATES.get(cat["id"])
            if not templates:
                continue
            for _ in range(n_per_cat):
                ex = generate_example(cat["id"], cat["name"], templates)
                out.append((ex.category_id, ex.title, f"{ex.description} {ex.transcript or ''}".strip()))
        return out
    finally:
        random.setstate(rng_state)


def eval_predict(samples, label):
    ok, confs, misses, t0 = 0, [], [], time.time()
    for exp, title, desc in samples:
        t = time.time()
        res = local.predict(title, desc)
        dt = time.time() - t
        if res and res[0] == exp:
            ok += 1
            confs.append(res[2])
        else:
            got = f"{res[0]}@{res[2]}" if res else "DEFER(None)"
            misses.append((exp, got, title[:70], round(dt, 3)))
    dt_all = time.time() - t0
    n = len(samples)
    mean_conf = f"{sum(confs)/len(confs):.3f}" if confs else "n/a (all deferred)"
    print(f"[{label}] n={n} acc={ok}/{n}={100*ok/n:.1f}% mean_conf={mean_conf} time={dt_all:.1f}s")
    for m in misses:
        print(f"  MISS exp={m[0]:18s} got={m[1]:24s} t={m[3]}s | {m[2]}")
    return ok, n


def eval_pipeline(samples):
    """Full categorize() on natural set: which path served each call + latency."""
    print(f"\n[pipeline] {len(samples)} natural problems through categorize() "
          f"(local_min_conf={settings.LOCAL_MIN_CONFIDENCE}, loRA={'on' if settings.lora_enabled else 'off'})")
    ok, paths, lat = 0, {}, []
    for exp, title, desc in samples:
        pre = local.predict(title, desc)
        t = time.time()
        try:
            res = categorize(title, desc)
        except Exception as e:
            print(f"  ERROR {type(e).__name__}: {e} | {title[:60]}", flush=True)
            continue
        dt = time.time() - t
        lat.append(dt)
        served = "local" if (pre and pre[0] == res["category_id"]) else "llm/heuristic"
        paths[served] = paths.get(served, 0) + 1
        mark = "OK " if res["category_id"] == exp else "MISS"
        if mark == "OK ":
            ok += 1
        print(f"  [{mark}] via={served:13s} {dt:6.1f}s exp={exp:18s} got={res['category_id']:18s} | {title[:55]}", flush=True)
    n = len(samples)
    print(f"[pipeline] acc={ok}/{n}={100*ok/n:.1f}% paths={paths} "
          f"avg_lat={sum(lat)/len(lat):.1f}s" if lat else "[pipeline] no results")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=5, help="fresh template samples per category")
    ap.add_argument("--skip-pipeline", action="store_true")
    a = ap.parse_args()

    print(f"local model: {local.status()}")
    set_a = fresh_template_samples(a.n)
    eval_predict(set_a, "A/fresh-templates")
    set_b = [(c, t, d) for c, t, d in NATURAL]
    tot_ok, tot_n = eval_predict(set_b, "B/natural")
    if not a.skip_pipeline:
        eval_pipeline(set_b)
    print(f"\nDone. Set B (honest signal): {tot_ok}/{tot_n}.")


if __name__ == "__main__":
    main()
