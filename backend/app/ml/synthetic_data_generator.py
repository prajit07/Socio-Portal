"""Synthetic labeled data generator for few-shot prompt bootstrapping.

Uses taxonomy keywords to generate realistic problem examples per category.
No manual labeling needed — runs once to create few-shot examples.
"""
import json
import os
import random
from typing import Optional
from dataclasses import dataclass, asdict

from app.ml import CATEGORIES


@dataclass
class SyntheticExample:
    title: str
    description: str
    transcript: str
    user_tags: list[str]
    category_id: str
    category_name: str
    tags: list[dict]  # [{id, name, confidence}]
    priority: str


# Template pools per category — mix keywords into natural sentences
TEMPLATES = {
    "water_sanitation": {
        "titles": [
            "Sewage overflow in {location}",
            "Contaminated drinking water in {location}",
            "Drainage blockage causing flooding in {location}",
            "No clean water supply in {location}",
            "Toilet facilities broken in {location}",
            "Water leakage from main pipeline in {location}",
        ],
        "descriptions": [
            "Residents report {keyword} issue for {duration}. The {keyword} has affected {impact}. "
            "Children and elderly are particularly vulnerable. Request immediate intervention.",
            "There is a severe {keyword} problem in our area. The {keyword} has been ongoing for {duration}. "
            "Multiple complaints have been filed but no action taken. This poses serious health risks.",
            "The {keyword} situation in {location} has worsened. {impact} are affected. "
            "We need urgent repair and regular maintenance to prevent recurrence.",
        ],
        "transcripts": [
            "There is dirty water coming from taps and it smells bad. My kids got stomach ache.",
            "Sewage is overflowing on the main road. Very bad smell and mosquitoes everywhere.",
            "No water for three days. Tanker comes once but not enough for all families.",
        ],
    },
    "waste_management": {
        "titles": [
            "Garbage not collected in {location} for weeks",
            "Illegal dumping near {location}",
            "Overflowing dustbins in {location}",
            "No waste segregation in {location}",
            "Burning of waste causing pollution in {location}",
        ],
        "descriptions": [
            "Garbage has not been collected for {duration}. Piles of {keyword} are accumulating "
            "causing foul smell and attracting stray animals. Health hazard for residents.",
            "People are illegally dumping {keyword} near {location}. This has been happening for {duration}. "
            "Municipal authorities need to install cameras and enforce penalties.",
            "Dustbins in {location} are overflowing with {keyword}. No segregation at source. "
            "Request regular collection and awareness drives for waste segregation.",
        ],
        "transcripts": [
            "Garbage truck hasn't come in two weeks. Piles everywhere, very bad smell.",
            "People throwing trash on empty plot near my house. Need action.",
        ],
    },
    "health": {
        "titles": [
            "Dengue outbreak in {location}",
            "No doctor at primary health center in {location}",
            "Medicine shortage at government hospital in {location}",
            "Mosquito menace in {location}",
            "Ambulance not available in {location}",
        ],
        "descriptions": [
            "There is a {keyword} outbreak in {location} with {impact} cases reported in {duration}. "
            "Fogging and larvicide spraying not done. Urgent medical camp needed.",
            "The primary health center in {location} has no doctor for {duration}. "
            "Patients have to travel {distance} km for basic treatment. Critical for emergencies.",
            "Government hospital in {location} facing severe {keyword} shortage. "
            "Patients asked to buy from outside at high cost. Affects poor families most.",
        ],
        "transcripts": [
            "Many dengue cases in our area. No fogging done. Hospital full.",
            "PHC closed most days. Have to go to city for small fever also.",
        ],
    },
    "education": {
        "titles": [
            "School building in dangerous condition in {location}",
            "Teacher shortage in government school in {location}",
            "No drinking water or toilets in school in {location}",
            "Mid-day meal not served in {location}",
            "Digital learning not available in {location}",
        ],
        "descriptions": [
            "The government school in {location} has {keyword} problem. Building has cracks, "
            "roof leaks during rain. {impact} students at risk. Need urgent repair or new building.",
            "Severe {keyword} in {location} school. Only {number} teachers for {impact} students. "
            "Classes combined, learning affected. Request immediate posting of teachers.",
            "School in {location} lacks basic {keyword}. No drinking water, toilets broken. "
            "Girls dropping out. This violates RTE norms. Need immediate provision.",
        ],
        "transcripts": [
            "School roof leaks, children sit in wet classroom. Very dangerous.",
            "Only two teachers for five classes. Children not learning anything.",
        ],
    },
    "transportation": {
        "titles": [
            "Potholes on main road in {location}",
            "Bus service discontinued in {location}",
            "Traffic signal not working in {location}",
            "No streetlights on highway near {location}",
            "Bridge damaged in {location}",
        ],
        "descriptions": [
            "The main road in {location} has severe {keyword}. Multiple accidents reported in {duration}. "
            "Vehicles damaged, two-wheeler riders at high risk. Need immediate resurfacing.",
            "Bus service to {location} stopped for {duration}. {impact} daily commuters affected. "
            "Students, workers, elderly have no alternative transport. Restore service urgently.",
            "Traffic signal at {location} junction not working for {duration}. "
            "Chaos during peak hours, frequent near-misses. Traffic police rarely deployed.",
        ],
        "transcripts": [
            "Big potholes on highway, bike slipped yesterday. Someone will die if not fixed.",
            "No bus from our village since lockdown. Walk 10km daily.",
        ],
    },
    "energy_environment": {
        "titles": [
            "Frequent power cuts in {location}",
            "Air pollution from factory in {location}",
            "No electricity in {location} village",
            "Solar streetlights not working in {location}",
            "Illegal tree cutting in {location}",
        ],
        "descriptions": [
            "{location} faces {duration} of daily power cuts. {impact} households affected. "
            "Students cannot study, businesses lose income. Transformers overloaded, need upgrade.",
            "Factory in {location} releasing {keyword} causing breathing problems. "
            "Pollution board complaints ignored for {duration}. Children and elderly suffering.",
            "Village {location} has no electricity connection despite poles installed {duration} ago. "
            "Only {number}% households have access. Demand grid connection under Saubhagya scheme.",
        ],
        "transcripts": [
            "Power goes 8 hours daily. Children study in dark. Inverter battery dead.",
            "Factory smoke enters our homes. Coughing all night. No action taken.",
        ],
    },
    "agriculture": {
        "titles": [
            "Crop failure due to pest attack in {location}",
            "Irrigation canal broken in {location}",
            "No fair price for crops in {location}",
            "Fertilizer shortage in {location}",
            "Stray cattle destroying crops in {location}",
        ],
        "descriptions": [
            "Farmers in {location} facing {keyword} destroying {impact} hectares of {crop}. "
            "No guidance from agriculture department. Pest control measures needed urgently.",
            "Main irrigation canal in {location} broken for {duration}. {impact} farmers unable to irrigate. "
            "Crops drying up. Request immediate repair before rabi season.",
            "Farmers in {location} not getting MSP for {crop}. Middlemen exploiting. "
            "Need procurement center and fair price mechanism.",
        ],
        "transcripts": [
            "Pests ate entire cotton crop. No officer visited. Lost everything.",
            "Canal broken since monsoon. Wheat sowing delayed. Big loss.",
        ],
    },
    "housing_urban": {
        "titles": [
            "Slum dwellers facing eviction in {location}",
            "Building collapse risk in {location}",
            "Unauthorized construction in {location}",
            "No housing for EWS in {location}",
            "Waterlogging in low-lying areas in {location}",
        ],
        "descriptions": [
            "{impact} families in {location} slum served eviction notice without rehabilitation. "
            "Living here for {duration} years. Children's education will be disrupted. Need in-situ rehabilitation.",
            "Old building in {location} showing cracks, {keyword} visible. {number} families living in fear. "
            "Municipal engineer inspection overdue. Need structural audit and repair.",
            "Unauthorized commercial construction in {location} residential zone. "
            "Blocking light, ventilation, drainage. Complaints to authority ignored for {duration}.",
        ],
        "transcripts": [
            "They want to demolish our homes. Where will we go? No notice, no new house.",
            "Building shaking when train passes. Cracks getting bigger. Scared to sleep.",
        ],
    },
    "digital_governance": {
        "titles": [
            "Online certificate portal not working in {location}",
            "Grievance redressal system broken in {location}",
            "No internet access in {location} village",
            "Digital literacy center needed in {location}",
            "Corruption in online service delivery in {location}",
        ],
        "descriptions": [
            "Citizens in {location} unable to get {keyword} certificates online for {duration}. "
            "Portal shows error, offline offices demand bribe. {impact} applications pending.",
            "Grievance portal in {location} not responding. Complaints auto-closed without resolution. "
            "No accountability. Need transparent tracking and timeline enforcement.",
            "Village {location} has no broadband connectivity. Students cannot access online classes, "
            "farmers cannot check market prices. Digital divide widening. Need BharatNet connection.",
        ],
        "transcripts": [
            "Portal not working since months. Clerk asks money for caste certificate.",
            "Complaint closed without solving. No one answers phone.",
        ],
    },
    "livelihood": {
        "titles": [
            "No employment opportunities in {location}",
            "Skill training center not functional in {location}",
            "SHG loan application rejected in {location}",
            "Artisan crafts dying in {location}",
            "Migration due to no income in {location}",
        ],
        "descriptions": [
            "Youth in {location} have no {keyword} opportunities. {impact} educated unemployed. "
            "Migration to cities increasing. Need local industrial unit or skill training.",
            "Skill training center in {location} non-functional for {duration}. Equipment broken, "
            "no trainer. {number} youth enrolled but no classes. Waste of potential.",
            "SHG women in {location} loan applications rejected without reason. "
            "Bank demands collateral SHGs cannot provide. Need simplified credit process.",
        ],
        "transcripts": [
            "My son BTech graduate sitting home two years. No factory, no office here.",
            "Training center locked. Machine rusting. No teacher came.",
        ],
    },
    "disaster": {
        "titles": [
            "Flood relief not reached in {location}",
            "Cyclone shelter damaged in {location}",
            "Landslide risk in {location} hills",
            "Fire station far from {location}",
            "Earthquake cracks in houses in {location}",
        ],
        "descriptions": [
            "After recent {keyword}, {location} received no relief for {duration}. "
            "{impact} families in temporary shelters without food, water, medicine. "
            "Administration unresponsive. Urgent relief distribution needed.",
            "Cyclone shelter in {location} damaged, roof blown off. {number} villages "
            "have no safe shelter. Monsoon approaching. Need immediate repair.",
            "Landslide risk in {location} after heavy rains. {impact} houses in danger zone. "
            "No early warning system. Geological survey and retention wall needed.",
        ],
        "transcripts": [
            "Flood water went but no relief came. Eating dry rice for week. Children sick.",
            "Shelter roof gone. Where will we go if cyclone comes again?",
        ],
    },
    "public_safety": {
        "titles": [
            "Streetlights not working in {location}",
            "CCTV cameras broken in {location}",
            "Police patrol absent in {location}",
            "Harassment of women in {location}",
            "Speeding vehicles in residential area in {location}",
        ],
        "descriptions": [
            "All streetlights in {location} not working for {duration}. {keyword} incidents increased. "
            "Women afraid to step out after dark. Need immediate repair and maintenance contract.",
            "CCTV cameras in {location} market area non-functional. Recent {keyword} cases unsolved. "
            "Traders demand working surveillance. Police say no budget for repair.",
            "No police patrol in {location} for {duration}. {keyword} and drug menace rising. "
            "Residents formed watch groups but need official presence. Request police outpost.",
        ],
        "transcripts": [
            "Dark streets, girls harassed daily. Police says no vehicle for patrol.",
            "CCTV broken six months. Thief caught on phone camera but police no action.",
        ],
    },
}


LOCATIONS = [
    "Sector 12", "Rampur village", "Gandhi Nagar", "MG Road", "Jahanabad",
    "Koramangala", "Dharavi", "Anna Nagar", "Salt Lake", "Vijay Nagar",
    "Panchsheel Enclave", "BHEL Township", "KPHB Colony", "Rajajinagar",
    "Civil Lines", "Model Town", "Adyar", "Banjara Hills", "Whitefield",
    "Korba", "Bhilai", "Durg", "Raipur", "Bilaspur", "Ambikapur",
]

DURATIONS = ["3 days", "2 weeks", "1 month", "3 months", "6 months", "over a year"]
IMPACTS = ["50 families", "200 residents", "150 students", "300 households", "1000 people", "50 farmers", "20 shops"]
CROPS = ["cotton", "wheat", "paddy", "soybean", "sugarcane", "vegetables"]
NUMBERS = ["2", "3", "5", "10", "15"]


def generate_example(category_id: str, category_name: str, templates: dict) -> SyntheticExample:
    """Generate one synthetic example for a category."""
    template_titles = templates["titles"]
    template_descs = templates["descriptions"]
    template_transcripts = templates.get("transcripts", [""])

    title_template = random.choice(template_titles)
    desc_template = random.choice(template_descs)
    transcript = random.choice(template_transcripts)

    # Fill placeholders
    location = random.choice(LOCATIONS)
    duration = random.choice(DURATIONS)
    impact = random.choice(IMPACTS)
    crop = random.choice(CROPS)
    number = random.choice(NUMBERS)
    distance = random.choice(["10", "25", "40", "60"])
    keyword = random.choice([kw for cat in CATEGORIES if cat["id"] == category_id for kw in cat["keywords"]])

    title = title_template.format(location=location)
    description = desc_template.format(
        location=location, duration=duration, impact=impact, crop=crop,
        number=number, distance=distance, keyword=keyword
    )

    # Generate tags from category keywords
    cat_keywords = [kw for cat in CATEGORIES if cat["id"] == category_id for kw in cat["keywords"]]
    selected_keywords = random.sample(cat_keywords, min(3, len(cat_keywords)))
    user_tags = selected_keywords[:2]

    tags = [
        {"id": category_id, "name": category_name, "confidence": 0.95},
        *[{"id": kw.replace(" ", "_"), "name": kw, "confidence": round(random.uniform(0.7, 0.9), 2)}
          for kw in selected_keywords[:2]]
    ]

    # Priority based on keywords
    priority_keywords = ["outbreak", "collapse", "fire", "flood", "emergency", "dangerous", "urgent", "critical"]
    priority = "critical" if any(kw in (title + description).lower() for kw in priority_keywords) else random.choice(["high", "medium"])

    return SyntheticExample(
        title=title,
        description=description,
        transcript=transcript,
        user_tags=user_tags,
        category_id=category_id,
        category_name=category_name,
        tags=tags,
        priority=priority,
    )


def generate_few_shot_examples(examples_per_category: int = 3) -> list[SyntheticExample]:
    """Generate few-shot examples for all categories."""
    examples = []
    for cat in CATEGORIES:
        cat_templates = TEMPLATES.get(cat["id"], {})
        if not cat_templates:
            continue
        for _ in range(examples_per_category):
            examples.append(generate_example(cat["id"], cat["name"], cat_templates))
    return examples


def save_few_shot_examples(examples: list[SyntheticExample], output_path: str):
    """Save examples as JSON for inspection and as formatted prompt snippets."""
    # Save raw data
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump([asdict(e) for e in examples], f, indent=2, ensure_ascii=False)

    # Save formatted for prompt injection
    prompt_path = output_path.replace(".json", "_prompt.txt")
    with open(prompt_path, "w", encoding="utf-8") as f:
        f.write("FEW_SHOT_EXAMPLES = [\n")
        for ex in examples:
            f.write("    {\n")
            f.write(f'        "title": "{ex.title}",\n')
            f.write(f'        "description": "{ex.description}",\n')
            f.write(f'        "transcript": "{ex.transcript}",\n')
            f.write(f'        "user_tags": {ex.user_tags},\n')
            f.write(f'        "expected": {{\n')
            f.write(f'            "category_id": "{ex.category_id}",\n')
            f.write(f'            "category_name": "{ex.category_name}",\n')
            f.write(f'            "tags": {json.dumps(ex.tags)},\n')
            f.write(f'            "priority": "{ex.priority}"\n')
            f.write("        }\n")
            f.write("    },\n")
        f.write("]\n")


if __name__ == "__main__":
    # Generate and save
    examples = generate_few_shot_examples(examples_per_category=3)
    output_path = os.path.join(os.path.dirname(__file__), "few_shot_examples.json")
    save_few_shot_examples(examples, output_path)
    print(f"Generated {len(examples)} few-shot examples -> {output_path}")

    # Print sample
    for ex in examples[:2]:
        print(f"\n--- {ex.category_name} ---")
        print(f"Title: {ex.title}")
        print(f"Desc: {ex.description[:100]}...")
        print(f"Priority: {ex.priority}")