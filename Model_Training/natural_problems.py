"""Shared natural-language problem sets for training and evaluation.

Two disjoint sets — NEVER mix them:
- NATURAL_TRAIN (24): hand-written citizen reports, deliberately non-template
  (mixed Hindi words, specifics, varied structure). Fed into training with
  repetition weight (see train_classifier.py --natural-repeat).
- HELD_OUT (12): fresh problems, 1 per category, NEVER used in training.
  This is the honest grading set — accuracy here measures generalization.

Both use backend taxonomy category_ids (12-class), not the SIH-10 labels.
"""

# (category_id, title, description) — goes INTO training (weighted).
NATURAL_TRAIN = [
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

# (category_id, title, description) — NEVER train on these. Honest grading only.
HELD_OUT = [
    ("water_sanitation", "Borewell runs dry each March",
     "Our street's only borewell sputters air from March to June. Tankers charge extra in summer and fights break out in the queue."),
    ("waste_management", "Drain desilting never happens",
     "The big storm drain behind our market hasn't been desilted in years. Plastic and silt choke it; monsoon water enters shops."),
    ("health", "Vaccination camp cancelled twice",
     "The immunisation camp for infants was cancelled twice without notice. Mothers who took leave lost a day's wages."),
    ("education", "Girls' toilet locked, used as storeroom",
     "The girls' toilet in our school stays locked and is used to dump broken furniture. Older girls skip school during periods."),
    ("transportation", "Footpath vendors block walkway",
     "Vendors occupy the entire footpath near the station. Pedestrians walk on the road where buses swerve close."),
    ("energy_environment", "Streetlight wires hang loose",
     "Live wires dangle from a tilted pole at the crossing. Sparks were seen during rain last week."),
    ("agriculture", "Fertiliser available only in black",
     "Urea is sold above MRP in black by two dealers. Small farmers who complain are denied stock later."),
    ("housing_urban", "Park turned into parking",
     "The neighbourhood park was fenced and converted into paid parking. Children now play cricket on the main road."),
    ("digital_governance", "Online complaint closes itself",
     "My grievance on the municipal portal auto-closes as 'resolved' within a day though nobody visited."),
    ("livelihood", "Apprenticeship stipend unpaid",
     "ITI apprentices at the local workshop have not received stipends for five months. Two trainees quit."),
    ("disaster", "Old trees fall in storms",
     "Two dead roadside trees crash every storm season. Last month one crushed a parked auto."),
    ("public_safety", "Chain-snatching on morning walk route",
     "Two chain-snatchings on bikes reported on the lakeside walk route this month. Walkers now avoid dawn walks."),
]
