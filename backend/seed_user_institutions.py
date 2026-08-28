"""Seed the user-provided official list of 128 Indian universities/institutes.

Idempotent by case-insensitive name. Run with:
    python seed_user_institutions.py
"""
import sys
sys.path.insert(0, r"C:\Users\praji\OneDrive\Desktop\SIH\backend")

from app.core.database import SessionLocal
from app.models.org import University

# (name, state)
INSTITUTIONS = [
    # Central Universities
    ("Aligarh Muslim University", "Uttar Pradesh"),
    ("Babasaheb Bhimrao Ambedkar University", "Uttar Pradesh"),
    ("Banaras Hindu University", "Uttar Pradesh"),
    ("Central University of Gujarat", "Gujarat"),
    ("Central University of Punjab", "Punjab"),
    ("English and Foreign Language University", "Telangana"),
    ("Jamia Millia Islamia", "Delhi"),
    ("Mahatma Gandhi Antarrashtriya Hindi Vishwavidhyalaya", "Maharashtra"),
    ("Manipur University", "Manipur"),
    ("Mizoram University", "Mizoram"),
    ("Nalanda University", "Bihar"),
    ("National Forensic Science University", "Gujarat"),
    ("Tezpur University", "Assam"),
    ("University of Delhi", "Delhi"),
    ("University of Hyderabad", "Telangana"),
    ("Visva Bharati University", "West Bengal"),
    # State Universities
    ("Alagappa University", "Tamil Nadu"),
    ("Andhra University", "Andhra Pradesh"),
    ("Anna University", "Tamil Nadu"),
    ("Bangalore University", "Karnataka"),
    ("Bharathiar University", "Tamil Nadu"),
    ("Cochin University of Science and Technology", "Kerala"),
    ("Delhi Technological University", "Delhi"),
    ("Dibrugarh University", "Assam"),
    ("Dr. Babasaheb Ambedkar Marathawada University", "Maharashtra"),
    ("Gauhati University", "Assam"),
    ("Goa University", "Goa"),
    ("Gujarat Technological University", "Gujarat"),
    ("Gujarat University", "Gujarat"),
    ("Guru Gobind Singh Indraprastha University", "Delhi"),
    ("Guru Nanak Dev University", "Punjab"),
    ("Indraprastha Institute of Information Technology", "Delhi"),
    ("Jawaharlal Nehru Technological University", "Telangana"),
    ("Kerala University", "Kerala"),
    ("Kurukshetra University", "Haryana"),
    ("Mahatma Gandhi University", "Kerala"),
    ("Mangalore University", "Karnataka"),
    ("Mumbai University", "Maharashtra"),
    ("Osmania University", "Telangana"),
    ("Panjab University", "Chandigarh"),
    ("Punjabi University", "Punjab"),
    ("Rabindra Bharati University", "West Bengal"),
    ("Sardar Patel University", "Gujarat"),
    ("Savitribai Phule Pune University", "Maharashtra"),
    ("Shivaji University", "Maharashtra"),
    ("Shree Somnath Sanskrit University", "Gujarat"),
    ("The Maharaja Sayajirao University", "Gujarat"),
    ("University of Calcutta", "West Bengal"),
    ("University of Kashmir", "Jammu and Kashmir"),
    ("University of Lucknow", "Uttar Pradesh"),
    ("University of Mysore", "Karnataka"),
    ("University of Jammu", "Jammu and Kashmir"),
    ("Utkal University", "Odisha"),
    ("Veer Narmad South Gujarat University", "Gujarat"),
    # Centrally Funded Technical Institutes
    ("IIT Roorkee", "Uttarakhand"),
    ("IIT Kanpur", "Uttar Pradesh"),
    ("IIT (BHU)", "Uttar Pradesh"),
    ("IIT Gandhinagar", "Gujarat"),
    ("IIT Patna", "Bihar"),
    ("IIT Kharagpur", "West Bengal"),
    ("IIT Madras", "Tamil Nadu"),
    ("IIT (ISM) Dhanbad", "Jharkhand"),
    ("IIT Bombay", "Maharashtra"),
    ("IIT Indore", "Madhya Pradesh"),
    ("IIT Hyderabad", "Telangana"),
    ("IIT Ropar", "Punjab"),
    ("IIT Delhi", "Delhi"),
    ("MNIT Jaipur", "Rajasthan"),
    ("NIT Calicut", "Kerala"),
    ("NIT Durgapur", "West Bengal"),
    ("NIT Hamirpur", "Himachal Pradesh"),
    ("NIT Jalandhar", "Punjab"),
    ("NIT Kurukshetra", "Haryana"),
    ("NIT Meghalaya", "Meghalaya"),
    ("NIT Rourkela", "Odisha"),
    ("NIT Tiruchirappalli", "Tamil Nadu"),
    ("NIT Warangal", "Telangana"),
    ("NIT Surathkal", "Karnataka"),
    ("NIT Silchar", "Assam"),
    ("Sardar Vallabhbhai National Institute Of Technology (SVNIT)", "Gujarat"),
    # Dance / Music / Traditional knowledge
    ("Dev Sanskriti Vishwavidyalaya", "Uttarakhand"),
    ("Indira Kala Sangeet Vishwavidyalaya", "Chhattisgarh"),
    ("Kalakshetra Foundation", "Tamil Nadu"),
    ("Kathak Kendra", "Delhi"),
    ("Kendriya Hindi Sansthan", "Delhi"),
    ("Pracheen Kala Kendra", "Chandigarh"),
    # Agricultural Universities
    ("Acharya Narendra Deva University of Agriculture and Technology", "Uttar Pradesh"),
    ("Ch. Sarwan Kumar Krishi Vishvavidyalaya", "Himachal Pradesh"),
    ("Chaudhary Charan Singh Haryana Agricultural University", "Haryana"),
    ("Dr. Yaswant Singh Parmar University of Horticulture & Forestry", "Himachal Pradesh"),
    ("Guru Angad Dev Veterinary and Animal Sciences University", "Punjab"),
    ("Jawaharlal Nehru Krishi Vishwa Vidyalaya", "Madhya Pradesh"),
    ("Kerala Agricultural University", "Kerala"),
    ("Nanaji Deshmukh Veterinary Science University", "Madhya Pradesh"),
    ("Punjab Agricultural University", "Punjab"),
    ("Sardar Vallabhbhai Patel University of Agriculture and Technology", "Uttar Pradesh"),
    ("Sher-e-Kashmir University of Agricultural Sciences and Technology of Jammu", "Jammu and Kashmir"),
    ("Sher-e-Kashmir University of Agricultural Sciences and Technology of Kashmir", "Jammu and Kashmir"),
    ("University of Agricultural Sciences Dharwad", "Karnataka"),
    ("University of Agricultural Sciences Bangalore", "Karnataka"),
    # Ayurveda / Yoga / Siddha / Unani / Homoeopathy
    ("Bhartiya Sanskriti Darshan Trust Ayurved Mahavidyalaya", "Maharashtra"),
    ("Ch. Brahm Prakash Ayurved Charak Sansthan", "Delhi"),
    ("Dr BRKR Govt Ayurveda College", "Telangana"),
    ("Government Ayurved College Wazirabad", "Maharashtra"),
    ("Government Ayurveda Medical College", "Karnataka"),
    ("Govt Ayurved Mahavidyalaya Nagpur", "Maharashtra"),
    ("Govt Ayurvedic College Gwalior", "Madhya Pradesh"),
    ("Govt Nizamia Tibbi College", "Telangana"),
    ("Govt Siddha Medical College", "Tamil Nadu"),
    ("Institute of Training and Research in Ayurved", "Gujarat"),
    ("JS Ayurved Mahavidyalaya Nadiad", "Gujarat"),
    ("JSPS Govt Homoeopathic Medical College", "Telangana"),
    ("Kaivalyadhama Yoga Institute", "Maharashtra"),
    ("KLE Shri B.M. Kankanawadi Ayurveda Mahavidyalaya", "Karnataka"),
    ("Maharashtra Arogya Mandala Sumati Bhai Shah Ayurved Mahavidyalaya", "Maharashtra"),
    ("Morarji Desai National Institute of Yoga", "Delhi"),
    ("National Institute of Ayurved", "Rajasthan"),
    ("National Institute of Homoeopathy", "West Bengal"),
    ("National Institute of Siddha", "Tamil Nadu"),
    ("National Institute of Unani Medicine", "Karnataka"),
    ("Pt. Khushilal Sharma Government Ayurveda College", "Madhya Pradesh"),
    ("RA Podar Ayurved College", "Maharashtra"),
    ("Rajiv Gandhi Government Post Graduate Ayurvedic College", "Himachal Pradesh"),
    ("SDM College of Ayurveda and Hospital Udupi", "Karnataka"),
    ("Shri Radha Krishna Toshniwal Ayurved Mahavidyalaya", "Maharashtra"),
    ("Sri Dharmasthala Manjunatheshwara College of Ayurveda", "Karnataka"),
    ("The North Eastern Institute of Ayurveda and Homoeopathy", "Meghalaya"),
    ("Tilak Ayurved Mahavidyalya", "Maharashtra"),
]


def main():
    db = SessionLocal()
    existing = {u.name.strip().lower() for u in db.query(University.name).all()}
    added = 0
    for name, state in INSTITUTIONS:
        if name.strip().lower() in existing:
            continue
        db.add(University(name=name.strip(), state=state, verified=True))
        existing.add(name.strip().lower())
        added += 1
    db.commit()
    total = db.query(University).count()
    db.close()
    print(f"Added {added} new institutions from official list. Total in directory: {total}")


if __name__ == "__main__":
    main()
