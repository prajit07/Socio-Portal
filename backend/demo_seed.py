"""Seed rich demo data for all 7 user roles (used for the demo screenshot run)."""
import os
import sys
import json
from datetime import datetime, timedelta, timezone

sys.path.append(os.path.dirname(__file__))

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.user import User, generate_user_id
from app.models.tag import Tag
from app.models.org import University, UniversityMember, Industry
from app.models.problem import Problem, Solution, generate_problem_id, generate_solution_id
from app.models.team import Team, TeamMember
from app.models.collaboration import Collaboration, Milestone, Deliverable, IPRecord, SocialImpactReport
from app.models.routing import RoutingLog, Notification
from app.models.engagement import Comment, Upvote, CitizenProfile, AuditLog
from app.models.evidence import Evidence, generate_evidence_id
from app.models.enums import (
    RoleEnum, ProblemStatusEnum, ProblemPriorityEnum, SolutionStatusEnum,
    RoutingTypeEnum, NotificationTypeEnum, EvidenceTypeEnum,
)

PW = "Test@1234"
NOW = datetime.now(timezone.utc)


def days(n):
    return NOW - timedelta(days=n)


def main():
    db = SessionLocal()
    try:
        # ---- Wipe app data (this script owns the demo DB) ----
        db.execute(RoutingLog.__table__.delete())
        db.execute(Notification.__table__.delete())
        db.execute(Deliverable.__table__.delete())
        db.execute(Milestone.__table__.delete())
        db.execute(IPRecord.__table__.delete())
        db.execute(SocialImpactReport.__table__.delete())
        db.execute(Collaboration.__table__.delete())
        db.execute(Solution.__table__.delete())
        db.execute(TeamMember.__table__.delete())
        db.execute(Team.__table__.delete())
        db.execute(Comment.__table__.delete())
        db.execute(Upvote.__table__.delete())
        db.execute(CitizenProfile.__table__.delete())
        db.execute(AuditLog.__table__.delete())
        db.execute(Evidence.__table__.delete())
        for p in db.query(Problem).all():
            db.delete(p)
        db.execute(Problem.__table__.delete())
        db.execute(UniversityMember.__table__.delete())
        db.execute(University.__table__.delete())
        db.execute(Industry.__table__.delete())
        for u in db.query(User).all():
            db.delete(u)
        db.execute(User.__table__.delete())
        db.commit()

        # ---- Tags ----
        with open(os.path.join(os.path.dirname(__file__), "app", "ml", "taxonomy.json"), encoding="utf-8") as f:
            cats = json.load(f)["categories"]
        for c in cats:
            if not db.query(Tag).filter(Tag.id == c["id"]).first():
                db.add(Tag(id=c["id"], name=c["name"], description=c.get("name")))
        db.commit()
        print("Seeded tags.")

        # ---- Users (all roles) ----
        def user(email, name, role, tags=None, phone=None):
            u = User(id=generate_user_id(role), name=name, email=email,
                     password_hash=hash_password(PW), role=role,
                     domain_tags=tags, phone=phone, is_email_verified=True)
            db.add(u)
            db.flush()
            return u

        ananya = user("citizen@demo.com", "Ananya Rao", RoleEnum.CITIZEN)
        ravi = user("ravi@demo.com", "Ravi Kumar", RoleEnum.CITIZEN)
        student = user("student@demo.com", "Aarav Sharma", RoleEnum.STUDENT, tags=["water_sanitation", "waste_management"])
        faculty = user("faculty@demo.com", "Dr. Meera Nair", RoleEnum.FACULTY, tags=["water_sanitation"])
        hei = user("hei@demo.com", "Prof. Sanjay Verma", RoleEnum.UNIVERSITY_ADMIN)
        acme = user("industry@demo.com", "Acme Innovations", RoleEnum.INDUSTRY, tags=["water_sanitation", "waste_management"])
        gov = user("gov@demo.com", "District Collector Office", RoleEnum.GOVERNMENT)
        admin = user("admin@demo.com", "System Administrator", RoleEnum.ADMIN)
        print("Created 8 users.")

        # ---- Org records ----
        uni = University(name="SRM Institute of Science and Technology",
                         registration_no="UGC-13-08-1985-4093",
                         address="Kattankulathur, Chengalpattu District",
                         district="Chengalpattu District", state="Tamil Nadu",
                         verified=True)
        db.add(uni)
        db.flush()
        db.add_all([
            UniversityMember(university_id=uni.id, user_id=student.id, member_role="student",
                             department="Civil Engineering", roll_number="RA2011003010010"),
            UniversityMember(university_id=uni.id, user_id=faculty.id, member_role="faculty_mentor",
                             department="Environmental Engineering"),
            UniversityMember(university_id=uni.id, user_id=hei.id, member_role="admin",
                             department="Office of Research"),
        ])

        ind = Industry(name="Acme Innovations Pvt Ltd", type="startup",
                       registration_no="U74999TN2020PTC135268",
                       address="Tidel Park, Taramani, Chennai",
                       district="Chennai", state="Tamil Nadu",
                       latitude=12.9926, longitude=80.2244,
                       domain_tags=["water_sanitation", "waste_management"], verified=True)
        db.add(ind)
        db.flush()
        print("Created university + industry.")

        # ---- Problems ----
        def prob(title, desc, cat, prio, status, submitter, lat, lng, address, tagnames, created, evidence=None, dup_of=None):
            p = Problem(id=generate_problem_id(), title=title, description=desc,
                        evidence_text=evidence,
                        latitude=lat, longitude=lng, address=address,
                        tags=tagnames, ai_tags=tagnames,
                        ai_category=cat, ai_priority=prio,
                        ai_duplicate_check=(dup_of is not None), ai_duplicate_of=dup_of,
                        status=status, submitter_id=submitter.id,
                        created_at=created, updated_at=created)
            db.add(p)
            db.flush()
            return p

        p1 = prob(
            "Sewage overflow on Anna Main Road, Chennai",
            "Raw sewage has been overflowing from the manhole near the Anna Main Road junction for the past two weeks. The overflow runs into the storm drain and has created a severe health hazard for residents and shopkeepers nearby. Stray animals are drinking the contaminated water and the smell is unbearable.",
            "water_sanitation", ProblemPriorityEnum.HIGH, ProblemStatusEnum.OPEN,
            ananya, 13.0827, 80.2707, "Anna Main Road, Chennai, Tamil Nadu",
            ["sewage", "drainage", "stagnant water"], days(55),
            evidence="I recorded the overflow around 8 AM. Water has been accumulating for over a metre along the footpath.")

        p2 = prob(
            "Illegal garbage dumping near Adyar riverbank",
            "Construction debris and mixed domestic waste are being dumped illegally on the Adyar riverbank at night. The pile has grown over the last month and is close to the water line. During rains, this waste washes directly into the river.",
            "waste_management", ProblemPriorityEnum.MEDIUM, ProblemStatusEnum.IN_REVIEW,
            ravi, 13.0063, 80.2570, "Adyar Riverbank, Chennai, Tamil Nadu",
            ["garbage", "illegal dumping", "river pollution"], days(48))

        p3 = prob(
            "Stagnant water breeding mosquitoes in Velachery — dengue risk",
            "Waterlogging near the Velachery lake periphery has not been cleared for three weeks. Multiple households in the neighbourhood have reported vector-borne illness and there is a localised dengue scare. The municipal disinfection van has not visited this stretch.",
            "health", ProblemPriorityEnum.CRITICAL, ProblemStatusEnum.PENDING_VALIDATION,
            ananya, 12.9791, 80.2205, "Velachery Lake Area, Chennai, Tamil Nadu",
            ["dengue", "mosquito", "stagnant water"], days(4),
            evidence="Voice note from a resident describing three cases of fever within the last week.")

        p4 = prob(
            "Street lights dead on Kamarajar Salai, Coimbatore",
            "All twelve street lights along Kamarajar Salai have been non-functional for over three weeks. The stretch is dangerously dark after 7 PM, making it unsafe for pedestrians, women commuting, and two-wheeler riders returning from work.",
            "energy_environment", ProblemPriorityEnum.HIGH, ProblemStatusEnum.IN_COLLABORATION,
            ravi, 11.0168, 76.9558, "Kamarajar Salai, Coimbatore, Tamil Nadu",
            ["streetlight", "power", "safety"], days(70))

        p5 = prob(
            "Cluster of deep potholes on Trichy–Chennai highway near Samayapuram",
            "A 300-metre stretch of the highway has multiple deep potholes that formed after the northeast monsoon. Auto rickshaws and motorcycles have reported tyre damage, and two-axle vehicles are swerving dangerously to avoid the pits during peak hours.",
            "transportation", ProblemPriorityEnum.CRITICAL, ProblemStatusEnum.PROPOSAL_SUBMITTED,
            ananya, 10.7905, 78.7047, "Samayapuram, Trichy, Tamil Nadu",
            ["pothole", "road", "highway"], days(80))

        p6 = prob(
            "Open drain inside government school compound, Madurai",
            "The government primary school at Chokkikulam has an open storm-water drain that fills with sewage from the adjacent colony. Children play near it and two students have fallen in previously. The school has no compound lighting and no boundary fence on the drain side.",
            "education", ProblemPriorityEnum.MEDIUM, ProblemStatusEnum.PROTOTYPE,
            ravi, 9.9252, 78.1198, "Chokkikulam, Madurai, Tamil Nadu",
            ["school", "open drain", "child safety"], days(95),
            evidence="Photograph showing the drain running along the school compound wall.")

        p7 = prob(
            "Village drinking water contaminated in Sivathapuram hamlet, Salem",
            "Hand-pump water samples from the Sivathapuram hamlet showed elevated iron and coliform levels. Around 40 families depend on this single pump. There is no nearby protected water source, and residents boil water out of fear rather than awareness.",
            "water_sanitation", ProblemPriorityEnum.HIGH, ProblemStatusEnum.OPEN,
            ananya, 11.6643, 78.1460, "Sivathapuram, Salem, Tamil Nadu",
            ["drinking water", "contamination", "hand pump"], days(33))

        p8 = prob(
            "No street lighting or internal roads in slum pocket, Erode",
            "The notified slum pocket at Kumaran Street has no internal metalled roads and no street lighting. During the rains the unpaved lanes become impassable, and emergency vehicles cannot enter. Residents have petitioned for basic civic infrastructure for two years.",
            "housing_urban", ProblemPriorityEnum.MEDIUM, ProblemStatusEnum.IMPLEMENTED,
            ravi, 11.3410, 77.7172, "Kumaran Street, Erode, Tamil Nadu",
            ["slum", "road", "streetlight"], days(150))

        p9 = prob(
            "Plastic waste choke points in the Bhavani river course",
            "Plastic carry-bags and multilayer packaging accumulate against sandbars and vegetation along the Bhavani river course. During low flow these choke points trap organic matter and release leachate. Local fishermen report a decline in catch near three identified bends.",
            "waste_management", ProblemPriorityEnum.HIGH, ProblemStatusEnum.PILOT,
            ananya, 11.4546, 77.6363, "Bhavani River, Erode, Tamil Nadu",
            ["river", "plastic", "pollution"], days(120))

        p10 = prob(
            "Cyclone shelter roof damaged at Akkaraipettai, Nagapattinam",
            "The community cyclone shelter at Akkaraipettai lost its asbestos roof sheet during a squall. The structure is otherwise sound but the mounting for the solar light was also torn off. With cyclone season approaching the shelter must be restored before it is needed.",
            "disaster", ProblemPriorityEnum.CRITICAL, ProblemStatusEnum.PENDING_VALIDATION,
            ravi, 10.7676, 79.8499, "Akkaraipettai, Nagapattinam, Tamil Nadu",
            ["cyclone", "shelter", "disaster"], days(2),
            evidence="Photograph of the exposed interior after the roof sheet was removed.")

        p11 = prob(
            "Sewage overflow near Annai Sathya Nagar junction",
            "Sewage water has overflowed at the Annai Sathya Nagar junction — very similar to the issue reported on Anna Main Road. Residents say this is the same municipal line fault slightly further down the road.",
            "water_sanitation", ProblemPriorityEnum.LOW, ProblemStatusEnum.DUPLICATE,
            ananya, 13.0835, 80.2730, "Annai Sathya Nagar, Chennai, Tamil Nadu",
            ["sewage", "overflow"], days(12), dup_of=p1.id)

        p12 = prob(
            "Ration card grievance portal repeatedly shows server error",
            "The district ration card grievance portal throws a 500 error when submitting a document update. Residents at the camp office are being told to try later or visit physically. The same module reportedly fails across two other districts.",
            "digital_governance", ProblemPriorityEnum.MEDIUM, ProblemStatusEnum.CLOSED,
            ravi, 12.9063, 79.1346, "Ration Office, Vellore, Tamil Nadu",
            ["portal", "e-governance", "grievance"], days(200))
        print("Created 12 problems.")

        # ---- Evidence records ----
        db.add_all([
            Evidence(problem_id=p1.id, type=EvidenceTypeEnum.TEXT, transcript=p1.evidence_text, uploaded_by_id=ananya.id),
            Evidence(problem_id=p3.id, type=EvidenceTypeEnum.AUDIO, transcript=p3.evidence_text, uploaded_by_id=ananya.id),
            Evidence(problem_id=p6.id, type=EvidenceTypeEnum.IMAGE, transcript="School compound drain photo", uploaded_by_id=ravi.id),
            Evidence(problem_id=p10.id, type=EvidenceTypeEnum.IMAGE, transcript=p10.evidence_text, uploaded_by_id=ravi.id),
        ])

        # ---- Teams ----
        t1 = Team(problem_id=p1.id, university_id=uni.id, name="AquaPure Collective", created_by=student.id, created_at=days(48))
        t2 = Team(problem_id=p6.id, university_id=uni.id, name="EcoRestore Team", created_by=student.id, created_at=days(80))
        t3 = Team(problem_id=p4.id, university_id=uni.id, name="BrightPath Innovators", created_by=faculty.id, created_at=days(55))
        db.add_all([t1, t2, t3])
        db.flush()
        db.add_all([
            TeamMember(team_id=t1.id, user_id=student.id, role="lead"),
            TeamMember(team_id=t1.id, user_id=faculty.id, role="mentor"),
            TeamMember(team_id=t1.id, user_id=hei.id, role="admin"),
            TeamMember(team_id=t2.id, user_id=student.id, role="lead"),
            TeamMember(team_id=t2.id, user_id=faculty.id, role="mentor"),
            TeamMember(team_id=t3.id, user_id=student.id, role="member"),
            TeamMember(team_id=t3.id, user_id=faculty.id, role="lead"),
        ])
        print("Created 3 teams.")

        # ---- Proposals (Solutions) ----
        s1 = Solution(id=generate_solution_id(),
                      title="IoT-based smart sewage monitoring with AI leak detection",
                      description="A network of low-cost IoT level and flow sensors on manholes, connected over LoRaWAN, with an ML anomaly model on the backend that predicts overflow events 30-60 minutes before they happen. Includes a public citizen dashboard and alert routing to the municipal control room.",
                      approach="Deploy 20 sensor nodes on priority manholes; stream telemetry to a cloud pipeline; train an anomaly detector on flow signatures; expose an alerting API and dashboard. Escalation matrix to the drainage division.",
                      tech_stack=["LoRaWAN", "Raspberry Pi", "Python", "FastAPI", "React", "PostgreSQL"],
                      estimated_timeline="6 months", estimated_budget="₹8.5 lakh",
                      status=SolutionStatusEnum.ACCEPTED, problem_id=p1.id, team_id=t1.id,
                      author_id=student.id,
                      github_url="https://github.com/aquapure-innovations/sensor-bridge",
                      demo_url="https://demo.sensorbridge.demos.in",
                      created_at=days(44), updated_at=days(10))
        s2 = Solution(id=generate_solution_id(),
                      title="Low-cost bio-sand filtration + school hygiene programme",
                      description="A bio-sand gravity filter built from locally available masonry materials for the school campus, combined with a six-week cleanliness and hygiene curriculum for students and a community maintenance rota involving the parents' association.",
                      approach="Install 3 bio-sand units; train a student eco-club and 4 maintenance volunteers; run a water-quality before/after test with the district lab; hand over an operating manual to the school management committee.",
                      tech_stack=["Masonry", "Water testing kits", "Training modules"],
                      estimated_timeline="4 months", estimated_budget="₹2.1 lakh",
                      status=SolutionStatusEnum.SUBMITTED, problem_id=p6.id, team_id=t2.id,
                      author_id=student.id, created_at=days(30), updated_at=days(5))
        s3 = Solution(id=generate_solution_id(),
                      title="Solar micro-grid streetlight retrofit with motion dimming",
                      description="Retrofit of the twelve Kamarajar Salai streetlights with solar-plus-battery luminaries that dim to 30% output when the stretch is empty and restore to full power on motion, cutting grid load while keeping the road safe.",
                      approach="Replace 12 luminaries; pair each with a 100Wp panel and 60Ah battery; add IR motion sensors; monitor remotely via a light-weight dashboard; compare energy and incident data before and after for 3 months.",
                      tech_stack=["Solar PV", "LiFePO4 battery", "IoT dimmer", "Dashboards"],
                      estimated_timeline="5 months", estimated_budget="₹6 lakh",
                      status=SolutionStatusEnum.UNDER_REVIEW, problem_id=p4.id, team_id=t3.id,
                      author_id=student.id, created_at=days(38), updated_at=days(15))
        s4 = Solution(id=generate_solution_id(),
                      title="Manual inspection route optimisation app (exploration)",
                      description="An early exploration of an app that plans efficient weekly inspection routes for the drainage crew using their existing field data. Held as a draft while the sensor approach is being refined.",
                      approach="Not finalised.",
                      tech_stack=["React Native", "Python"],
                      estimated_timeline="2 months", estimated_budget="₹1 lakh",
                      status=SolutionStatusEnum.DRAFT, problem_id=p1.id, team_id=t1.id,
                      author_id=student.id, created_at=days(41))
        db.add_all([s1, s2, s3, s4])
        db.flush()
        print("Created 4 proposals.")

        # ---- Collaborations + milestones + IP + impact ----
        col1 = Collaboration(proposal_id=s1.id, industry_id=ind.id, stage="pilot",
                             notes="Acme is funding the 20-node pilot. Sensor BOM finalised, contracting underway.",
                             started_at=days(20), updated_at=days(3))
        db.add(col1)
        db.flush()
        m1 = Milestone(collaboration_id=col1.id, title="Feasibility study & site survey",
                       description="Walked the Anna Main Road stretch, marked manhole locations and network coverage.",
                       due_date=days(-15), completed_at=days(-14), status="completed", created_at=days(19))
        m2 = Milestone(collaboration_id=col1.id, title="Sensor prototype accepted",
                       description="Field prototype validated against manual depth readings for 10 days.",
                       due_date=days(-4), completed_at=days(-3), status="completed", created_at=days(10))
        m3 = Milestone(collaboration_id=col1.id, title="Pilot deployment at 20 manholes",
                       description="Install sensor nodes, commission gateway and connect the alert dashboard.",
                       due_date=days(+20), status="pending", created_at=days(5))
        m4 = Milestone(collaboration_id=col1.id, title="Handover & municipal training",
                       description="Train the drainage division operators and hand over runbooks.",
                       due_date=days(+50), status="pending", created_at=days(5))
        db.add_all([m1, m2, m3, m4])
        db.flush()
        db.add_all([
            Deliverable(milestone_id=m1.id, file_url="https://cdn.demos.in/feasibility.pdf", description="Feasibility report PDF"),
            Deliverable(milestone_id=m1.id, file_url="https://cdn.demos.in/site-map.png", description="Site survey map"),
            Deliverable(milestone_id=m2.id, file_url="https://cdn.demos.in/sensor-bom.xlsx", description="Sensor BOM & cost sheet"),
        ])
        db.add(IPRecord(collaboration_id=col1.id, type="patent", status="filed",
                        reference_no="IN/PAT/2026/000234", created_at=days(6)))
        db.add_all([
            SocialImpactReport(collaboration_id=col1.id, beneficiaries_count=1200,
                               impact_summary="1200 households in the catchment now receive earlier overflow alerts; diversion of sewage from storm drain reduced after pilot tuning.",
                               district="Chennai", state="Tamil Nadu", reported_at=days(9)),
            SocialImpactReport(collaboration_id=col1.id, beneficiaries_count=4200,
                               impact_summary="Overflow incidents at identified high-risk manholes down by ~60% during the pilot window; cleanup cost for the affected stretch reduced.",
                               district="Chennai", state="Tamil Nadu", reported_at=days(2)),
        ])

        col2 = Collaboration(proposal_id=s3.id, industry_id=ind.id, stage="interested",
                             notes="Acme is evaluating a joint pilot for solar streetlight retrofit in Chennai before committing funding.",
                             started_at=days(2), updated_at=days(1))
        db.add(col2)
        print("Created 2 collaborations.")

        # ---- Notifications ----
        db.add_all([
            Notification(user_id=ananya.id, type=NotificationTypeEnum.STATUS_UPDATED,
                         message="Your problem 'Street lights dead on Kamarajar Salai, Coimbatore' has moved to In Collaboration.", reference_id=p4.id),
            Notification(user_id=ananya.id, type=NotificationTypeEnum.DUPLICATE_FLAGGED,
                         message="Your report 'Sewage overflow near Annai Sathya Nagar junction' was flagged as a duplicate of an existing problem.", reference_id=p11.id),
            Notification(user_id=ananya.id, type=NotificationTypeEnum.GENERIC,
                         message="A proposal was accepted for your problem 'Sewage overflow on Anna Main Road, Chennai'.", reference_id=p1.id),
            Notification(user_id=ravi.id, type=NotificationTypeEnum.STATUS_UPDATED,
                         message="Your problem 'Open drain inside government school compound, Madurai' reached Prototype stage.", reference_id=p6.id),
            Notification(user_id=student.id, type=NotificationTypeEnum.PROBLEM_ROUTED,
                         message="A high-priority water & sanitation problem in Chennai was routed to your university.", reference_id=p1.id),
            Notification(user_id=student.id, type=NotificationTypeEnum.PROPOSAL_RECEIVED,
                         message="Acme Innovations started a collaboration on your proposal 'IoT-based smart sewage monitoring'.", reference_id=s1.id),
            Notification(user_id=faculty.id, type=NotificationTypeEnum.PROBLEM_ROUTED,
                         message="A new education-sector problem in Madurai was routed for your domain.", reference_id=p6.id),
            Notification(user_id=hei.id, type=NotificationTypeEnum.PROPOSAL_RECEIVED,
                         message="AquaPure Collective submitted a proposal for 'Sewage overflow on Anna Main Road, Chennai'.", reference_id=s1.id),
            Notification(user_id=acme.id, type=NotificationTypeEnum.PROBLEM_ROUTED,
                         message="A new waste management problem in Erode matches your domain tags.", reference_id=p9.id),
            Notification(user_id=acme.id, type=NotificationTypeEnum.STATUS_UPDATED,
                         message="Collaboration 'IoT-based smart sewage monitoring' moved to Pilot stage.", reference_id=col1.id),
            Notification(user_id=gov.id, type=NotificationTypeEnum.STATUS_UPDATED,
                         message="New impact report recorded for the Anna Main Road sewage collaboration.", reference_id=col1.id),
            Notification(user_id=admin.id, type=NotificationTypeEnum.GENERIC,
                         message="3 new university and industry registrations are pending verification this week."),
        ])

        # ---- Engagement ----
        db.add_all([
            Comment(entity_type="problem", entity_id=p1.id, user_id=student.id,
                    content="Team AquaPure is preparing a proposal — we can have sensors on-site within 6 weeks.", created_at=days(40)),
            Comment(entity_type="problem", entity_id=p1.id, user_id=ananya.id,
                    content="Thank you! Residents have already gathered a list of problem manholes.", created_at=days(38)),
            Comment(entity_type="problem", entity_id=p3.id, user_id=gov.id,
                    content="Disinfection squad scheduled for the Velachery stretch this week.", created_at=days(1)),
            Comment(entity_type="solution", entity_id=s1.id, user_id=acme.id,
                    content="Acme will fund the pilot sensor fleet. Sharing BOM access today.", created_at=days(6)),
        ])
        db.add_all([
            Upvote(problem_id=p1.id, user_id=ravi.id),
            Upvote(problem_id=p3.id, user_id=ravi.id),
            Upvote(problem_id=p3.id, user_id=ananya.id),
            Upvote(problem_id=p5.id, user_id=ravi.id),
        ])
        db.add_all([
            CitizenProfile(user_id=ananya.id, address="Anna Nagar, Chennai", district="Chennai", state="Tamil Nadu"),
            CitizenProfile(user_id=ravi.id, address="Madipakkam, Chennai", district="Chennai", state="Tamil Nadu"),
        ])

        # ---- Routing audit + audit log ----
        db.add_all([
            RoutingLog(problem_id=p1.id, routed_to_type=RoutingTypeEnum.UNIVERSITY, routed_to_id=student.id,
                       reason="Domain match: water_sanitation", created_at=days(48)),
            RoutingLog(problem_id=p4.id, routed_to_type=RoutingTypeEnum.INDUSTRY, routed_to_id=acme.id,
                       reason="Domain match: energy_environment", created_at=days(60)),
            RoutingLog(problem_id=p9.id, routed_to_type=RoutingTypeEnum.INDUSTRY, routed_to_id=acme.id,
                       reason="Domain match: waste_management", created_at=days(100)),
        ])
        db.add_all([
            AuditLog(user_id=admin.id, action="user.registered", entity_type="user", entity_id=ananya.id, timestamp=days(90)),
            AuditLog(user_id=gov.id, action="problem.validated", entity_type="problem", entity_id=p1.id, timestamp=days(50)),
            AuditLog(user_id=admin.id, action="proposal.accepted", entity_type="solution", entity_id=s1.id, timestamp=days(10)),
            AuditLog(user_id=acme.id, action="collaboration.started", entity_type="collaboration", entity_id=col1.id, timestamp=days(20)),
        ])

        db.commit()
        print("Demo seed complete.")
    finally:
        db.close()


if __name__ == "__main__":
    main()