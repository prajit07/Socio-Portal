import csv
import random

# Categories from the problem statement
CATEGORIES = [
    "Education",
    "Agriculture",
    "Healthcare",
    "Water Resources",
    "Environment",
    "Energy",
    "Urban Development",
    "Accessibility",
    "Public Administration",
    "Rural Livelihoods"
]

# Templates for generating synthetic challenges
# Each category has a set of keywords and themes to make the data realistic for Jharkhand
THEMES = {
    "Education": [
        "lack of digital classrooms in rural schools",
        "high dropout rates among girls in primary schools",
        "insufficient vocational training centers for youth",
        "shortage of qualified teachers in remote tribal areas",
        "absence of libraries in village panchayats",
        "need for bilingual education materials in local languages",
        "poor infrastructure in government high schools",
        "lack of STEM labs for science education",
        "difficulty in accessing higher education scholarships",
        "ineffective adult literacy programs"
    ],
    "Agriculture": [
        "poor crop yield due to soil degradation",
        "lack of cold storage facilities for perishable crops",
        "inefficient irrigation systems in drought-prone areas",
        "high cost of quality seeds and fertilizers",
        "lack of access to real-time market prices for farmers",
        "pests destroying paddy crops in monsoon",
        "need for organic farming transition support",
        "ineffective seed distribution networks",
        "lack of livestock health services in remote villages",
        "poor post-harvest management techniques"
    ],
    "Healthcare": [
        "shortage of doctors in Primary Health Centers (PHCs)",
        "lack of maternal health facilities in rural blocks",
        "high prevalence of malnutrition among children",
        "difficulty in accessing emergency ambulance services",
        "poor sanitation in government hospitals",
        "lack of affordable diagnostic labs in districts",
        "ineffective vaccination drives in tribal belts",
        "shortage of essential medicines in rural clinics",
        "lack of mental health support systems",
        "poor hygiene practices in community living areas"
    ],
    "Water Resources": [
        "contamination of groundwater with arsenic and fluoride",
        "depleting water table due to over-extraction",
        "lack of rainwater harvesting systems in villages",
        "inefficient distribution of drinking water",
        "drying up of traditional ponds and wells",
        "poor wastewater treatment in semi-urban areas",
        "lack of piped water supply in remote hamlets",
        "ineffective management of river flood zones",
        "shortage of drinking water during summer months",
        "poor quality of water in community hand-pumps"
    ],
    "Environment": [
        "increasing deforestation in the plateau regions",
        "air pollution from illegal mining activities",
        "poor waste management and plastic pollution in forests",
        "soil erosion in hilly terrains",
        "lack of awareness about biodiversity conservation",
        "illegal poaching of wildlife in protected areas",
        "impact of industrial effluent on local streams",
        "lack of urban green spaces and parks",
        "improper disposal of electronic waste",
        "degradation of forest cover due to unplanned roads"
    ],
    "Energy": [
        "frequent power outages in rural agricultural blocks",
        "lack of solar lighting in remote tribal villages",
        "dependence on kerosene for cooking in rural households",
        "inefficient electricity billing and collection systems",
        "lack of renewable energy integration in public buildings",
        "poor maintenance of electrical transformers",
        "high cost of electricity for small-scale industries",
        "lack of energy-efficient appliances in low-income homes",
        "insufficient street lighting in village markets",
        "need for micro-grid solutions for off-grid areas"
    ],
    "Urban Development": [
        "congestion and poor traffic management in city centers",
        "lack of organized drainage systems leading to urban floods",
        "insufficient affordable housing for urban migrants",
        "poor maintenance of public roads and pavements",
        "lack of integrated public transport systems",
        "inefficient garbage collection and sorting in cities",
        "encroachment of public parks and open spaces",
        "lack of safe pedestrian crossings and cycling lanes",
        "poor urban planning in rapidly growing towns",
        "lack of smart parking solutions in commercial areas"
    ],
    "Accessibility": [
        "lack of ramps and lifts for disabled people in public offices",
        "poor connectivity of rural roads to main highways",
        "absence of braille signage in government buildings",
        "difficulty in accessing public transport for elderly",
        "lack of inclusive toilets in public places",
        "poor last-mile connectivity in hilly terrains",
        "absence of sign-language interpreters in hospitals",
        "lack of accessible walkways in urban areas",
        "poor road conditions hindering emergency vehicle access",
        "digital divide limiting access to online government services"
    ],
    "Public Administration": [
        "delays in processing government certificates and permits",
        "lack of transparency in the allocation of public funds",
        "inefficient grievance redressal mechanisms for citizens",
        "corruption in the distribution of welfare benefits",
        "poor coordination between different government departments",
        "lack of digitalization of land records",
        "difficulties in accessing social security schemes",
        "ineffective communication of government policies to citizens",
        "long queues and bureaucracy in public offices",
        "lack of accountability in local panchayat administration"
    ],
    "Rural Livelihoods": [
        "lack of market access for tribal handicrafts",
        "insufficient credit facilities for small rural entrepreneurs",
        "lack of training in non-farm income generating activities",
        "seasonal unemployment among rural youth",
        "poor packaging and branding for village-made products",
        "lack of storage for forest-based non-timber products",
        "ineffective implementation of MGNREGA schemes",
        "lack of micro-finance opportunities for women's groups",
        "poor infrastructure for rural cottage industries",
        "limited access to e-commerce platforms for rural artisans"
    ]
}

def generate_data(num_examples_per_cat=100):
    data = []
    for cat in CATEGORIES:
        themes = THEMES[cat]
        for i in range(num_examples_per_cat):
            # Use templates but add variety
            base_challenge = random.choice(themes)

            # Randomly vary the phrasing to make it look natural
            phrasings = [
                f"The community is facing {base_challenge}.",
                f"There is a critical {base_challenge} in our region.",
                f"We are reporting {base_challenge}.",
                f"Issue: {base_challenge}.",
                f"Problem statement: {base_challenge}.",
                f"Urgent need to address {base_challenge}.",
                f"The local area suffers from {base_challenge}.",
                f"Citizens are complaining about {base_challenge}."
            ]
            text = random.choice(phrasings)

            # Format for AutoTrain (Instruction tuning style)
            # ### Human: Categorize this societal challenge: [Text]
            # ### Assistant: [Category]
            formatted_text = f"### Human: Categorize this societal challenge: {text} ### Assistant: {cat}"
            data.append([formatted_text])

    random.shuffle(data)
    return data

if __name__ == "__main__":
    num_per_cat = 200 # Total 2000 examples for a strong start
    dataset = generate_data(num_per_cat)

    with open("training_data.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["text"]) # Header
        writer.writerows(dataset)

    print(f"Generated {len(dataset)} examples in training_data.csv")
