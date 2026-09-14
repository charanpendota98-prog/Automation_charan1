"""v38: TOP POST DOMINANCE ENGINE — "top post veyyali, anni keywords".

Ee module 4 panulu chestundi (anni offline, deterministic, no API key needed):

1. **KEYWORD UNIVERSE (anni keywords)** — ~175 entities (exams, boards,
   universities, scholarships, skills, internships) × 54 search intents
   (14 core + 40 long-tail) = **9000+ exact search phrases**. Prathi keyword ki
   cluster, funnel (TOFU/MOFU/BOFU), content-type, *heuristic* demand band,
   competition band, aur priority score. Volume/difficulty bands heuristics —
   Google data kaadu (adi `--gsc` CSV tho replace cheyandi).

2. **TOP POST BLUEPRINT** — keyword iste SERP-intent-wise complete on-page
   pack: title options (char-count tho), meta, slug, H1, H2/H3 outline,
   entities to cover, PAA questions, table plan, snippet answer pattern,
   schema list, image + alt text, internal/external link plan, E-E-A-T
   checklist, word target, ranking levers — plus files (.md/.html/.json).

3. **TOP POST SCORE** — real article/HTML ni 30+ weighted checks tho score
   chestundi (0-100): keyword family coverage, snippet readiness, structure,
   tables/lists, FAQ, links, schema, E-E-A-T, density (over-optimization
   penalty!), readability. Grade: TOP POST 🏆 / STRONG / OK / WEAK.

4. **HARDEN + GATE** — publish mundu structural fixes (keyword meta/slug,
   snippet answer, FAQ extraction from ARTICLE OWN content, density cap) —
   kotha facts eppudu invent cheyyadu. Live publish ki score gate.

CLI:
  python run.py --top-post "SSC CGL 2026 apply online"
  python run.py --top-post "TSPSC Group 2 2026 notification" --publish-top-post
  python run.py --top-post-plan --top-post-days 90
  python run.py --keyword-universe
  python run.py --score-post output/top-posts/x.html --score-keyword "ssc cgl 2026"
"""

from __future__ import annotations

import csv
import hashlib
import html as _html
import json
import logging
import re
from datetime import date, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from . import config, validator

log = logging.getLogger("autoblog.top_post")

TELUGU_RANGE = "\u0c00-\u0c7f"
POWER_WORDS = ("complete", "best", "top", "easy", "free", "guide", "full",
               "latest", "pakka", "ultimate")

# ===========================================================================
# 1. ENTITY LAYER — exams / boards / scholarships / skills
# (name, live category, popularity weight 1-5, official site or "")
# ===========================================================================

ENTITIES: List[tuple] = [
    # ---------------- Central govt exams / banks / defence ----------------
    ("SSC CGL", "Central Govt Jobs", 5, "ssc.gov.in"),
    ("SSC CHSL", "Central Govt Jobs", 5, "ssc.gov.in"),
    ("SSC MTS", "Central Govt Jobs", 5, "ssc.gov.in"),
    ("SSC GD", "Central Govt Jobs", 5, "ssc.gov.in"),
    ("SSC CPO", "Central Govt Jobs", 4, "ssc.gov.in"),
    ("SSC JE", "Central Govt Jobs", 4, "ssc.gov.in"),
    ("SSC Stenographer", "Central Govt Jobs", 3, "ssc.gov.in"),
    ("SSC Selection Post", "Central Govt Jobs", 3, "ssc.gov.in"),
    ("UPSC CSE", "Central Govt Jobs", 5, "upsc.gov.in"),
    ("UPSC CDS", "Central Govt Jobs", 4, "upsc.gov.in"),
    ("UPSC NDA", "Central Govt Jobs", 4, "upsc.gov.in"),
    ("UPSC EPFO", "Central Govt Jobs", 3, "upsc.gov.in"),
    ("UPSC CAPF", "Central Govt Jobs", 3, "upsc.gov.in"),
    ("RRB NTPC", "Central Govt Jobs", 5, "indianrailways.gov.in"),
    ("RRB Group D", "Central Govt Jobs", 5, "indianrailways.gov.in"),
    ("RRB ALP", "Central Govt Jobs", 4, "indianrailways.gov.in"),
    ("RRB JE", "Central Govt Jobs", 3, "indianrailways.gov.in"),
    ("RRB Staff Nurse", "Central Govt Jobs", 2, "indianrailways.gov.in"),
    ("IBPS PO", "Central Govt Jobs", 5, "ibps.in"),
    ("IBPS Clerk", "Central Govt Jobs", 5, "ibps.in"),
    ("IBPS SO", "Central Govt Jobs", 3, "ibps.in"),
    ("IBPS RRB Officer", "Central Govt Jobs", 4, "ibps.in"),
    ("IBPS RRB Assistant", "Central Govt Jobs", 3, "ibps.in"),
    ("SBI PO", "Central Govt Jobs", 5, "sbi.co.in"),
    ("SBI Clerk", "Central Govt Jobs", 5, "sbi.co.in"),
    ("SBI SO", "Central Govt Jobs", 3, "sbi.co.in"),
    ("SBI Apprentice", "Central Govt Jobs", 3, "sbi.co.in"),
    ("RBI Grade B", "Central Govt Jobs", 4, "rbi.org.in"),
    ("RBI Assistant", "Central Govt Jobs", 4, "rbi.org.in"),
    ("NABARD Grade A", "Central Govt Jobs", 3, "nabard.org"),
    ("LIC AAO", "Central Govt Jobs", 4, "licindia.in"),
    ("LIC Assistant", "Central Govt Jobs", 3, "licindia.in"),
    ("NIACL AO", "Central Govt Jobs", 3, "newindia.co.in"),
    ("UIIC Assistant", "Central Govt Jobs", 2, "uiic.co.in"),
    ("India Post GDS", "Central Govt Jobs", 5, "indiapostgdsonline.gov.in"),
    ("India Post MTS", "Central Govt Jobs", 3, "indiapost.gov.in"),
    ("Army Agniveer", "Central Govt Jobs", 5, "joinindianarmy.nic.in"),
    ("Navy Agniveer SSR", "Central Govt Jobs", 4, "joinindiannavy.gov.in"),
    ("Air Force Agniveer", "Central Govt Jobs", 4, "agnipathvayu.cdac.in"),
    ("Coast Guard Navik", "Central Govt Jobs", 3, "joinindiancoastguard.cdac.in"),
    ("BSF Constable", "Central Govt Jobs", 3, "rect.bsf.gov.in"),
    ("CISF Constable", "Central Govt Jobs", 3, "cisf.gov.in"),
    ("CRPF Constable", "Central Govt Jobs", 3, "crpf.gov.in"),
    ("ITBP Constable", "Central Govt Jobs", 2, "itbpolice.nic.in"),
    ("Delhi Police Constable", "Central Govt Jobs", 4, "delhipolice.gov.in"),
    ("BSNL JTO", "Central Govt Jobs", 3, "bsnl.co.in"),
    ("EPFO SSA", "Central Govt Jobs", 3, "epfindia.gov.in"),
    ("ESIC UDC", "Central Govt Jobs", 3, "esic.gov.in"),
    ("KVS Teacher", "Central Govt Jobs", 3, "kvsangathan.nic.in"),
    ("DSSSB", "Central Govt Jobs", 3, "dsssb.delhi.gov.in"),
    ("NTA UGC NET", "Online Education", 5, "ugcnet.nta.nic.in"),
    ("CSIR NET", "Online Education", 3, "csirnet.nta.nic.in"),
    ("GATE", "Online Education", 5, "gate.iitk.ac.in"),
    ("BARC OCES", "Central Govt Jobs", 2, "barc.gov.in"),
    ("ISRO Scientist", "Central Govt Jobs", 2, "isro.gov.in"),
    ("DRDO Apprentice", "Central Govt Jobs", 2, "drdo.gov.in"),
    # ---------------- Telangana ----------------
    ("TSPSC Group 1", "TS Govt Jobs", 5, "tspsc.gov.in"),
    ("TSPSC Group 2", "TS Govt Jobs", 5, "tspsc.gov.in"),
    ("TSPSC Group 3", "TS Govt Jobs", 4, "tspsc.gov.in"),
    ("TSPSC Group 4", "TS Govt Jobs", 4, "tspsc.gov.in"),
    ("TSPSC AEE", "TS Govt Jobs", 3, "tspsc.gov.in"),
    ("TSPSC AE", "TS Govt Jobs", 4, "tspsc.gov.in"),
    ("TSPSC Junior Lecturer", "TS Govt Jobs", 4, "tspsc.gov.in"),
    ("TSPSC Degree Lecturer", "TS Govt Jobs", 3, "tspsc.gov.in"),
    ("TSPSC VRO", "TS Govt Jobs", 3, "tspsc.gov.in"),
    ("TGPSC Gurukul", "TS Govt Jobs", 4, "tgtgurukulam.telangana.gov.in"),
    ("TG DSC", "TS Govt Jobs", 5, "tgdsc.aptonline.in"),
    ("TG DSC SGT", "TS Govt Jobs", 4, "tgdsc.aptonline.in"),
    ("TG DSC School Assistant", "TS Govt Jobs", 4, "tgdsc.aptonline.in"),
    ("TSLPRB SI", "TS Govt Jobs", 5, "tslprb.in"),
    ("TSLPRB Constable", "TS Govt Jobs", 5, "tslprb.in"),
    ("TS TET", "TS Govt Jobs", 4, "tstet.cgg.gov.in"),
    ("TG POLYCET", "Online Education", 4, "polycet.sbtet.telangana.gov.in"),
    ("TG EAPCET", "Online Education", 5, "eapcet.tsche.ac.in"),
    ("TS ICET", "Online Education", 4, "icet.tsche.ac.in"),
    ("TS ECET", "Online Education", 3, "ecet.tsche.ac.in"),
    ("TS PGECET", "Online Education", 3, "pgecet.tsche.ac.in"),
    ("TS LAWCET", "Online Education", 3, "lawcet.tsche.ac.in"),
    ("TS DEECET", "Online Education", 2, "deecet.cgg.gov.in"),
    ("TGRTC", "TS Govt Jobs", 3, "tsrtc.telangana.gov.in"),
    ("Singareni", "TS Govt Jobs", 4, "scclmines.com"),
    ("TSSPDCL", "TS Govt Jobs", 4, "tssouthernpower.com"),
    ("TS GENCO", "TS Govt Jobs", 3, "tsgenco.co.in"),
    ("TS High Court", "TS Govt Jobs", 3, "tshc.gov.in"),
    ("TS Excise Constable", "TS Govt Jobs", 3, "excise.telangana.gov.in"),
    ("TS Fire Department", "TS Govt Jobs", 2, "fire.telangana.gov.in"),
    ("Osmania University", "Online Education", 3, "osmania.ac.in"),
    ("JNTUH", "Online Education", 3, "jntuh.ac.in"),
    ("Kakatiya University", "Online Education", 2, "kakatiya.ac.in"),
    ("TS Inter Supplementary", "Online Education", 3, "tsbie.cgg.gov.in"),
    ("TS SSC", "Online Education", 4, "bse.telangana.gov.in"),
    # ---------------- Andhra Pradesh ----------------
    ("APPSC Group 1", "AP Govt Jobs", 5, "psc.ap.gov.in"),
    ("APPSC Group 2", "AP Govt Jobs", 5, "psc.ap.gov.in"),
    ("APPSC Group 3", "AP Govt Jobs", 3, "psc.ap.gov.in"),
    ("APPSC AEE", "AP Govt Jobs", 3, "psc.ap.gov.in"),
    ("APPSC Junior Lecturer", "AP Govt Jobs", 3, "psc.ap.gov.in"),
    ("AP DSC", "AP Govt Jobs", 5, "apdsc.apcfss.in"),
    ("AP DSC SGT", "AP Govt Jobs", 4, "apdsc.apcfss.in"),
    ("AP DSC School Assistant", "AP Govt Jobs", 4, "apdsc.apcfss.in"),
    ("AP Police Constable", "AP Govt Jobs", 5, "slprb.ap.gov.in"),
    ("AP Police SI", "AP Govt Jobs", 4, "slprb.ap.gov.in"),
    ("AP Grama Sachivalayam", "AP Govt Jobs", 5, "gramasachivalayam.ap.gov.in"),
    ("AP VRO VRA", "AP Govt Jobs", 3, "gramasachivalayam.ap.gov.in"),
    ("APSRTC", "AP Govt Jobs", 3, "apsrtconline.in"),
    ("AP High Court", "AP Govt Jobs", 3, "aphc.gov.in"),
    ("AP COOP Bank", "AP Govt Jobs", 2, "apcob.org"),
    ("AP TET", "AP Govt Jobs", 4, "aptet.apcfss.in"),
    ("AP EAPCET", "Online Education", 5, "eapcet-sche.aptonline.in"),
    ("AP POLYCET", "Online Education", 4, "polycetap.nic.in"),
    ("AP ICET", "Online Education", 3, "icet-sche.aptonline.in"),
    ("AP ECET", "Online Education", 2, "ecet-sche.aptonline.in"),
    ("AP PGECET", "Online Education", 2, "pgcet-sche.aptonline.in"),
    ("AP LAWCET", "Online Education", 2, "lawcet-sche.aptonline.in"),
    ("AP DEECET", "Online Education", 2, "deecet.apcfss.in"),
    ("AP Residential", "Online Education", 3, "aprs.ap.gov.in"),
    ("AP Model Schools", "Online Education", 3, "apms.cgg.gov.in"),
    # ---------------- Scholarships + welfare schemes ----------------
    ("NSP Scholarship", "Scholarships", 5, "scholarships.gov.in"),
    ("PM YASASVI", "Scholarships", 4, "yet.nta.ac.in"),
    ("Post Matric Scholarship", "Scholarships", 5, "scholarships.gov.in"),
    ("Pre Matric Scholarship", "Scholarships", 4, "scholarships.gov.in"),
    ("Telangana ePASS", "Scholarships", 5, "telanganaepass.cgg.gov.in"),
    ("AP Jnanabhumi", "Scholarships", 5, "jnanabhumi.ap.gov.in"),
    ("Vidya Lakshmi", "Scholarships", 3, "vidyalakshmi.co.in"),
    ("Central Sector Scholarship", "Scholarships", 4, "scholarships.gov.in"),
    ("INSPIRE Scholarship", "Scholarships", 3, "online-inspire.gov.in"),
    ("Maulana Azad Fellowship", "Scholarships", 2, "maef.nic.in"),
    ("MOMA Scholarship", "Scholarships", 3, "scholarships.gov.in"),
    ("Pragati Scholarship", "Scholarships", 3, "aicte-india.org"),
    ("Saksham Scholarship", "Scholarships", 3, "aicte-india.org"),
    ("PM Vidyalaxmi", "Scholarships", 3, "vidyalakshmi.co.in"),
    ("NMMS", "Scholarships", 4, "scholarships.gov.in"),
    ("NTSE", "Scholarships", 3, "ncert.nic.in"),
    ("TS Fee Reimbursement", "Scholarships", 4, "telanganaepass.cgg.gov.in"),
    ("AP Fee Reimbursement", "Scholarships", 4, "jnanabhumi.ap.gov.in"),
    ("Minority Scholarship", "Scholarships", 3, "scholarships.gov.in"),
    ("BC Welfare Scholarship", "Scholarships", 3, "telanganaepass.cgg.gov.in"),
    ("SC ST Scholarship", "Scholarships", 3, "scholarships.gov.in"),
    ("PMKVY", "Scholarships", 3, "pmkvyofficial.org"),
    # ---------------- Entrances / admissions / schools ----------------
    ("NEET UG", "Online Education", 5, "neet.nta.nic.in"),
    ("NEET PG", "Online Education", 4, "natboard.edu.in"),
    ("JEE Main", "Online Education", 5, "jeemain.nta.nic.in"),
    ("JEE Advanced", "Online Education", 4, "jeeadv.ac.in"),
    ("CUET UG", "Online Education", 5, "cuet.samarth.ac.in"),
    ("CUET PG", "Online Education", 3, "cuet.nta.nic.in"),
    ("IGNOU", "Online Education", 4, "ignou.ac.in"),
    ("BITSAT", "Online Education", 3, "bitsadmission.com"),
    ("VITEEE", "Online Education", 3, "viteee.vit.ac.in"),
    ("SRMJEEE", "Online Education", 2, "srmist.edu.in"),
    ("KCET", "Online Education", 3, "kea.kar.nic.in"),
    ("WBJEE", "Online Education", 3, "wbjeeb.nic.in"),
    ("MHT CET", "Online Education", 3, "mahacet.org"),
    ("COMEDK", "Online Education", 2, "comedk.org"),
    ("CLAT", "Online Education", 3, "consortiumofnlus.ac.in"),
    ("CAT", "Online Education", 4, "iimcat.ac.in"),
    ("MAT", "Online Education", 2, "aima.in"),
    ("NIFT", "Online Education", 2, "nift.ac.in"),
    ("Navodaya Vidyalaya", "Online Education", 4, "navodaya.gov.in"),
    ("Sainik School", "Online Education", 4, "sainikschooladmission.in"),
    ("TSRJC", "Online Education", 3, "tsrjdc.cgg.gov.in"),
    ("APRJC", "Online Education", 3, "aprs.ap.gov.in"),
    # ---------------- Skills / private / internships ----------------
    ("NPTEL", "Online Education", 3, "nptel.ac.in"),
    ("Swayam", "Online Education", 3, "swayam.gov.in"),
    ("Coursera Free Courses", "Online Education", 2, "coursera.org"),
    ("Google Career Certificate", "Online Education", 2, "grow.google"),
    ("TCS iON", "Private Jobs", 2, "learning.tcsionhub.in"),
    ("Infosys Springboard", "Private Jobs", 2, "infyspringboard.onwingspan.com"),
    ("Wipro TalentNext", "Private Jobs", 2, "wipro.com"),
    ("AWS Certification", "Software Jobs", 2, "aws.amazon.com"),
    ("TCS NQT", "Private Jobs", 4, "tcs.com"),
    ("Infosys Off Campus", "Private Jobs", 3, "infosys.com"),
    ("Wipro Elite NTH", "Private Jobs", 3, "careers.wipro.com"),
    ("Cognizant GenC", "Private Jobs", 3, "cognizant.com"),
    ("Accenture Off Campus", "Private Jobs", 3, "accenture.com"),
    ("Zoho Recruitment", "Software Jobs", 2, "zoho.com"),
    ("Fresher Software Jobs", "Software Jobs", 3, "studentup.in"),
    ("Data Analyst Jobs", "Software Jobs", 3, "studentup.in"),
    ("Work From Home Internship", "Internships", 3, "internshala.com"),
    ("Government Internship", "Internships", 3, "internship.aicte-india.org"),
    ("NATS Apprenticeship", "Internships", 3, "nats.education.gov.in"),
    ("AICTE Internship", "Internships", 2, "internship.aicte-india.org"),
    ("Resume for Freshers", "Internships", 3, "studentup.in"),
    ("Interview Questions Telugu", "Internships", 3, "studentup.in"),
    ("Aptitude Test Preparation", "Internships", 3, "studentup.in"),
    ("Typing Test Telugu", "Part Time Jobs", 2, "studentup.in"),
    ("Tally Course", "Part Time Jobs", 2, "studentup.in"),
    ("Digital Marketing Course", "Part Time Jobs", 2, "studentup.in"),
    ("Data Entry Jobs", "Part Time Jobs", 3, "studentup.in"),
    ("Part Time Jobs for Students", "Part Time Jobs", 3, "studentup.in"),
]

# Keep only the live-site categories (pipeline.CATEGORY_RULES names)
LIVE_CATEGORIES = {
    "Scholarships", "Central Govt Jobs", "TS Govt Jobs", "AP Govt Jobs",
    "Private Jobs", "Software Jobs", "Part Time Jobs", "Walkin Jobs",
    "Hall Tickets", "Results", "Internships", "Online Education",
}

# ===========================================================================
# 2. INTENT LAYER — core intents + long-tail axes
# id, title template, keyword template, funnel, outline family,
# demand 1-5, competition 1-5
# ===========================================================================

CORE_INTENTS: List[tuple] = [
    ("notification", "{exam} {year} Notification – Vacancies, Dates, Apply Online Telugu lo",
     "{exam} {year} notification", "MOFU", "notification", 5, 5),
    ("apply online", "{exam} {year} Apply Online – Eligibility, Fee & Steps Telugu lo",
     "{exam} {year} apply online", "BOFU", "apply", 5, 5),
    ("hall ticket", "{exam} {year} Hall Ticket Download – Direct Link & Steps",
     "{exam} {year} hall ticket", "BOFU", "hallticket", 5, 4),
    ("results", "{exam} {year} Results – Check Marks & Direct Link Telugu lo",
     "{exam} {year} results", "BOFU", "result", 5, 5),
    ("answer key", "{exam} {year} Answer Key – Download & Objection Process",
     "{exam} {year} answer key", "MOFU", "answerkey", 4, 3),
    ("cut off", "{exam} {year} Cut Off – Expected & Previous Year Marks Analysis",
     "{exam} {year} cut off", "MOFU", "cutoff", 4, 4),
    ("syllabus", "{exam} Syllabus {year} – Complete Subject wise PDF Telugu lo",
     "{exam} syllabus {year}", "TOFU", "syllabus", 5, 4),
    ("exam date", "{exam} {year} Exam Date – Complete Schedule Telugu lo",
     "{exam} {year} exam date", "MOFU", "notification", 4, 3),
    ("vacancies", "{exam} {year} Vacancies – Category wise Total Posts",
     "{exam} {year} vacancies", "MOFU", "notification", 4, 3),
    ("salary", "{exam} {year} Salary – Pay Scale, Allowances & Job Profile",
     "{exam} {year} salary", "TOFU", "salary", 4, 3),
    ("selection process", "{exam} {year} Selection Process – Stages & Exam Pattern",
     "{exam} {year} selection process", "MOFU", "notification", 4, 3),
    ("previous papers", "{exam} Previous Papers – Free PDF Download & Solutions",
     "{exam} previous papers pdf", "TOFU", "syllabus", 4, 3),
    ("best books", "{exam} {year} Best Books – Telugu Medium Strategy Complete",
     "{exam} {year} best books", "TOFU", "books", 4, 3),
    ("preparation tips", "{exam} {year} Preparation Tips – 90 Days Study Plan Telugu lo",
     "{exam} {year} preparation tips", "TOFU", "plan", 4, 3),
]

# year_in_title: prathi intent title lo year untunda (evergreen intents ki ledu)
EVERGREEN_INTENT_IDS = {"previous papers"}

LONGTAIL_INTENTS: List[tuple] = [
    ("telugu-guide", "{exam} {year} in Telugu – Complete Guide",
     "{exam} {year} in telugu", "TOFU", "guide", 3, 3),
    ("last-date", "{exam} {year} Last Date – Deadline & Late Fee Details",
     "{exam} {year} last date", "BOFU", "notification", 5, 3),
    ("how-to-apply", "{exam} {year} Apply Ela Cheyali? Step by Step Telugu",
     "how to apply {exam} {year} in telugu", "BOFU", "apply", 4, 2),
    ("eligibility", "{exam} {year} Eligibility – Age, Qualification & Relaxation",
     "{exam} {year} eligibility", "MOFU", "notification", 5, 3),
    ("age-limit", "{exam} {year} Age Limit – Category wise Relaxation Table",
     "{exam} {year} age limit", "MOFU", "notification", 4, 2),
    ("application-fee", "{exam} {year} Application Fee – Category wise Amount",
     "{exam} {year} application fee", "MOFU", "notification", 4, 2),
    ("documents", "{exam} {year} Documents List – Form Reject Avvakunda",
     "{exam} {year} required documents", "MOFU", "apply", 4, 2),
    ("notification-pdf", "{exam} {year} Notification PDF Download – Direct Link",
     "{exam} {year} notification pdf download", "BOFU", "notification", 4, 3),
    ("direct-link", "{exam} {year} Apply Online Direct Link – Official Site",
     "{exam} {year} apply online direct link", "BOFU", "apply", 5, 4),
    ("district-wise", "{exam} {year} District wise Vacancies – Full List",
     "{exam} {year} district wise vacancies", "MOFU", "notification", 3, 2),
    ("category-wise", "{exam} {year} Category wise Vacancies & Reservation",
     "{exam} {year} category wise vacancies", "MOFU", "notification", 3, 2),
    ("exam-pattern", "{exam} {year} Exam Pattern & Marking Scheme Details",
     "{exam} {year} exam pattern", "MOFU", "syllabus", 4, 3),
    ("negative-marking", "{exam} {year} Negative Marking – Rules & Safe Attempts",
     "{exam} {year} negative marking", "TOFU", "syllabus", 3, 2),
    ("study-plan", "{exam} {year} 90 Day Study Plan – Telugu lo Timetable",
     "{exam} {year} study plan in telugu", "TOFU", "plan", 4, 3),
    ("topper-strategy", "{exam} Toppers Strategy – Rank Ela Sadhinchali?",
     "{exam} toppers strategy telugu", "TOFU", "plan", 3, 3),
    ("common-mistakes", "{exam} {year} Common Mistakes – Ivi Avoid Cheyandi",
     "{exam} {year} common mistakes", "TOFU", "mistakes", 3, 2),
    ("mock-test", "{exam} {year} Free Mock Test – Online Practice Telugu",
     "{exam} {year} free mock test telugu", "TOFU", "practice", 3, 3),
    ("previous-cutoff", "{exam} Previous Year Cut Off – All Categories Table",
     "{exam} previous year cut off", "MOFU", "cutoff", 4, 3),
    ("expected-cutoff", "{exam} {year} Expected Cut Off – Category wise Analysis",
     "{exam} {year} expected cut off", "MOFU", "cutoff", 4, 3),
    ("result-date", "{exam} {year} Result Date – Official vs Expected",
     "{exam} {year} result date", "BOFU", "result", 4, 3),
    ("merit-list", "{exam} {year} Merit List – Selection Status Check",
     "{exam} {year} merit list", "BOFU", "result", 3, 2),
    ("certificate-verification", "{exam} {year} Certificate Verification – Documents List",
     "{exam} {year} certificate verification", "MOFU", "apply", 3, 2),
    ("joining-letter", "{exam} {year} Joining Letter & Training Details",
     "{exam} {year} joining letter", "BOFU", "salary", 3, 2),
    ("posting-details", "{exam} {year} Posting Details – District Allotment Rules",
     "{exam} {year} posting details", "MOFU", "salary", 3, 2),
    ("salary-in-hand", "{exam} {year} Salary in Hand – Pay Scale Breakdown",
     "{exam} {year} salary in hand", "TOFU", "salary", 4, 3),
    ("job-profile", "{exam} Job Profile – Duties, Shifts & Work Pressure",
     "{exam} job profile", "TOFU", "salary", 4, 3),
    ("promotion", "{exam} Promotion & Career Growth – Full Details",
     "{exam} promotion chances", "TOFU", "salary", 3, 2),
    ("transfer-policy", "{exam} Transfer Policy – Rules Telugu lo",
     "{exam} transfer policy", "TOFU", "salary", 3, 2),
    ("syllabus-pdf", "{exam} Syllabus PDF – Subject wise Download Link",
     "{exam} syllabus pdf download", "TOFU", "syllabus", 4, 3),
    ("telugu-medium", "{exam} Preparation in Telugu Medium – Material List",
     "{exam} preparation in telugu medium", "TOFU", "books", 4, 2),
    ("coaching-vs-self", "{exam} Coaching vs Self Study – Best Choice",
     "{exam} coaching vs self study", "TOFU", "plan", 3, 2),
    ("girls-candidates", "{exam} for Girls – Vacancies, Eligibility & Safety",
     "{exam} for girls eligibility", "TOFU", "notification", 3, 2),
    ("tenth-pass", "{exam} for 10th Pass – Eligible Posts List",
     "{exam} for 10th pass", "TOFU", "notification", 4, 2),
    ("degree-holders", "{exam} for Degree Holders – Which Posts Eligible?",
     "{exam} for degree holders", "TOFU", "notification", 3, 2),
    ("fresher-guide", "{exam} for Freshers – Zero Experience Full Guide",
     "{exam} for freshers", "TOFU", "guide", 3, 2),
    ("faq", "{exam} {year} FAQ – Students Common Doubts Telugu lo",
     "{exam} {year} faq", "MOFU", "guide", 3, 2),
    ("status-check", "{exam} {year} Application Status Check – Online Steps",
     "{exam} {year} application status check", "BOFU", "apply", 4, 2),
    ("correction-window", "{exam} {year} Form Correction – Edit Window Details",
     "{exam} {year} form correction", "BOFU", "apply", 3, 2),
    ("helpline", "{exam} Helpline Number & Email – Official Contact",
     "{exam} helpline number", "MOFU", "guide", 3, 2),
    ("exam-centre", "{exam} {year} Exam Centre List – City wise Details",
     "{exam} {year} exam centre list", "MOFU", "hallticket", 3, 2),
    ("official-website", "{exam} Official Website – Login, Links & Notifications",
     "{exam} official website login", "MOFU", "guide", 3, 2),
    ("youtube-channels", "{exam} Best YouTube Channels – Free Classes Telugu",
     "{exam} best youtube channels telugu", "TOFU", "practice", 3, 2),
    ("telegram-groups", "{exam} Telegram & WhatsApp Alerts – Free Joining Links",
     "{exam} telegram group link", "TOFU", "guide", 3, 3),
    ("previous-analysis", "{exam} Previous Year Analysis – Trend & Repeat Topics",
     "{exam} previous year analysis", "TOFU", "cutoff", 3, 2),
    ("free-material", "{exam} Free Study Material PDF – Download List",
     "{exam} free study material pdf", "TOFU", "books", 4, 2),
    ("photo-signature", "{exam} Photo & Signature Size – Upload Rules",
     "{exam} photo signature size", "MOFU", "apply", 3, 2),
    ("fee-refund", "{exam} Fee Refund & Double Payment Rules",
     "{exam} fee refund rules", "MOFU", "apply", 2, 2),
    ("exam-day-checklist", "{exam} Exam Day Checklist – Items to Carry",
     "{exam} exam day checklist", "MOFU", "hallticket", 3, 2),
    ("seat-matrix", "{exam} Seat Matrix & Allotment – Full Details",
     "{exam} seat matrix", "MOFU", "admission", 3, 2),
    ("success-story", "{exam} Success Story – Topper Interview Telugu",
     "{exam} success story telugu", "TOFU", "plan", 3, 2),
    ("scholarship-renewal", "{exam} Renewal Process – Documents & Deadline",
     "{exam} renewal process", "MOFU", "scholarship", 3, 2),
    ("income-certificate", "{exam} Income & Caste Certificate – Documents Guide",
     "{exam} income certificate documents", "MOFU", "scholarship", 3, 2),
]

ALL_INTENTS: List[tuple] = CORE_INTENTS + LONGTAIL_INTENTS
HOT_INTENTS = {"notification", "apply online", "hall ticket", "results",
               "answer key", "cut off", "last date", "direct-link",
               "eligibility", "result-date", "admit-card"}

# Category-wise intent hygiene: scholarship/skill pages ki exam-mechanics
# keywords meaningless (negative marking, exam centre...) — aa combos
# universe lo create cheyyadu (anni keywords = sensical keywords).
EXAM_MECHANICS = {"hall ticket", "answer key", "cut off", "exam date",
                  "exam-pattern", "negative-marking", "exam-centre",
                  "previous papers", "previous-cutoff", "expected-cutoff",
                  "merit-list", "results", "result-date", "mock-test",
                  "mock test", "selection process", "vacancies", "salary",
                  "salary-in-hand", "job-profile", "promotion",
                  "transfer-policy", "posting-details", "joining-letter",
                  "category-wise", "district-wise", "syllabus",
                  "syllabus-pdf", "exam pattern", "negative marking",
                  "previous year cut off", "exam centre list",
                  "previous-analysis", "exam-day-checklist", "seat-matrix"}
APPLY_MECHANICS = {"certificate-verification", "correction-window",
                   "status-check", "documents", "application-fee",
                   "age-limit", "last-date", "notification-pdf",
                   "photo-signature", "fee-refund", "tenth-pass",
                   "girls-candidates"}
# Self-help / skill / course entities ki exam-focussed axes meaningless.
SKILL_ENTITIES = {
    "NPTEL", "Swayam", "Coursera Free Courses", "Google Career Certificate",
    "TCS iON", "Infosys Springboard", "Wipro TalentNext", "AWS Certification",
    "Resume for Freshers", "Interview Questions Telugu",
    "Aptitude Test Preparation", "Typing Test Telugu", "Tally Course",
    "Digital Marketing Course", "Data Entry Jobs", "Fresher Software Jobs",
    "Work From Home Internship", "Zoho Recruitment",
}
# Scholarship-only axes (exam entities ki income certificate/ renewal odd).
SCHOLARSHIP_ONLY = {"scholarship-renewal", "income-certificate"}
# Category-wise hygiene (scholarships lo exam-mechanics keyword noise).
CATEGORY_INTENT_FILTER = {
    "Scholarships": (EXAM_MECHANICS - {"merit-list", "results"}) | {
        "correction-window", "exam-centre"},
}


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ",
                  re.sub(r"[^\w\d\u0c00-\u0c7f]+", " ", (text or "").lower())).strip()


def _slugish(text: str, max_len: int = 60) -> str:
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", (text or "").lower())).strip("-")[:max_len]


def _stable_int(seed: str, modulo: int) -> int:
    if modulo <= 0:
        return 0
    return int(hashlib.md5((seed or "x").encode("utf-8")).hexdigest()[:8], 16) % modulo


def target_year(text: str = "") -> int:
    """Keyword lo year unte adhe, lekapote current year (2025/2026 kanna purana kaadu)."""
    years = [int(y) for y in re.findall(r"\b(20[2-9]\d)\b", text or "")]
    years = [y for y in years if y >= date.today().year - 1]
    return years[0] if years else date.today().year


# ===========================================================================
# 3. KEYWORD UNIVERSE
# ===========================================================================

_UNIVERSE_CACHE: Optional[List[dict]] = None


def _priority(entity_weight: int, demand: int, competition: int,
              funnel: str, hot: bool) -> int:
    """Heuristic 0-100 priority — Google data KAADU (proxy model).

    Weighted blend: entity popularity 34% + intent demand 30% + funnel value
    16% + winnability 20% (+ hot bonus). Spread untundi — aanni 100 avvavu.
    GSC CSV vasthe aa real data ki preference ivvandi (`run.py --gsc`).
    """
    pop = max(0.0, min(1.0, entity_weight / 5))
    dem = max(0.0, min(1.0, demand / 5))
    fun = {"BOFU": 1.0, "MOFU": 0.7, "TOFU": 0.45}.get(funnel, 0.45)
    win = max(0.0, min(1.0, 1 - (competition - 1) / 4))
    score = 0.34 * pop + 0.30 * dem + 0.16 * fun + 0.20 * win
    score += 0.03 if hot else 0.0
    return max(5, min(99, int(round(score * 100))))


def keyword_universe(force: bool = False) -> List[dict]:
    """Anni keywords: entity × intent (9000+) — deterministic + cached."""
    global _UNIVERSE_CACHE
    if _UNIVERSE_CACHE is not None and not force:
        return _UNIVERSE_CACHE

    seen: Dict[str, dict] = {}
    for exam, cat, weight, site in ENTITIES:
        if cat not in LIVE_CATEGORIES:
            cat = "Online Education"
        pillar_ids = {"notification", "apply online", "syllabus", "results",
                      "hall ticket", "direct-link", "last-date", "eligibility"}
        skip_intents = set(CATEGORY_INTENT_FILTER.get(cat, set()))
        if cat != "Scholarships":
            skip_intents |= SCHOLARSHIP_ONLY
        if exam in SKILL_ENTITIES:
            skip_intents |= EXAM_MECHANICS | APPLY_MECHANICS
        for intent_id, title_tmpl, kw_tmpl, funnel, family, demand, comp in ALL_INTENTS:
            if intent_id in skip_intents:
                continue
            evergreen = intent_id in EVERGREEN_INTENT_IDS
            year = target_year("")
            year_txt = "" if evergreen else f" {year}"
            title = title_tmpl.format(exam=exam, year=year_txt.strip() or year)
            keyword = _norm(kw_tmpl.format(exam=exam, year=year))
            if not keyword or keyword in seen:
                continue
            seen[keyword] = {
                "kw": keyword,
                "title": title,
                "exam": exam,
                "cat": cat,
                "intent": intent_id,
                "tier": "core" if (intent_id, title_tmpl, kw_tmpl, funnel, family,
                                   demand, comp) in CORE_INTENTS else "longtail",
                "funnel": funnel,
                "family": family,
                "role": "pillar" if intent_id in pillar_ids else "support",
                "demand": "high" if demand >= 5 else ("medium" if demand >= 4 else "low"),
                "competition": "high" if comp >= 5 else ("medium" if comp >= 4 else "low"),
                "priority": _priority(weight, demand, comp, funnel,
                                      intent_id in HOT_INTENTS),
                "cluster": exam,
                "official": site,
                "year": year,
                "serp": _serp_features(family, demand),
            }
    _UNIVERSE_CACHE = sorted(seen.values(),
                             key=lambda e: (-e["priority"], e["cluster"], e["kw"]))
    log.info("Keyword universe ready: %d keywords (%d entities × %d intents)",
             len(_UNIVERSE_CACHE), len(ENTITIES), len(ALL_INTENTS))
    return _UNIVERSE_CACHE


def _serp_features(family: str, demand: int) -> List[str]:
    """Honest SERP feature targets (placement guarantee kaadu — pattern clue)."""
    base = ["Quick answer snippet", "People also ask"]
    extra = {
        "notification": ["Table snippet", "Deadline rich text"],
        "apply": ["How-to steps list", "Video results"],
        "result": ["Direct link block", "Sitelinks"],
        "hallticket": ["Direct download steps"],
        "syllabus": ["PDF results", "Topic table"],
        "cutoff": ["Comparison table snippet"],
        "salary": ["Pay scale table"],
        "plan": ["Checklist snippet"],
        "books": ["List snippet"],
        "practice": ["Interactive content"],
        "mistakes": ["Bullet snippet"],
        "guide": ["FAQ block"],
    }.get(family, [])
    out = base + extra
    if demand >= 5:
        out.append("Top stories (news intent)")
    return out


def universe_stats(uni: Optional[List[dict]] = None) -> dict:
    uni = uni if uni is not None else keyword_universe()
    by_intent, by_cat, by_funnel, by_cluster = {}, {}, {}, {}
    for e in uni:
        by_intent[e["intent"]] = by_intent.get(e["intent"], 0) + 1
        by_cat[e["cat"]] = by_cat.get(e["cat"], 0) + 1
        by_funnel[e["funnel"]] = by_funnel.get(e["funnel"], 0) + 1
        by_cluster[e["cluster"]] = by_cluster.get(e["cluster"], 0) + 1
    hot = sum(1 for e in uni if e["intent"] in HOT_INTENTS)
    return {
        "total": len(uni),
        "entities": len(ENTITIES),
        "intents": len(ALL_INTENTS),
        "core_intents": len(CORE_INTENTS),
        "longtail_intents": len(LONGTAIL_INTENTS),
        "hot": hot,
        "pillars": sum(1 for e in uni if e["role"] == "pillar"),
        "by_category": dict(sorted(by_cat.items(), key=lambda kv: -kv[1])),
        "by_funnel": by_funnel,
        "by_intent_top": dict(sorted(by_intent.items(), key=lambda kv: -kv[1])[:12]),
        "clusters": len(by_cluster),
        "avg_priority": round(sum(e["priority"] for e in uni) / max(1, len(uni)), 1),
        "note": ("Demand/competition bands are HEURISTIC proxies, not Google "
                 "volume data. Real data ki: run.py --gsc export.csv"),
    }


def keyword_family(keyword: str, limit: int = 14) -> dict:
    """Oka keyword ki related search phrases (universe nunchi + templates).

    Returns {primary, secondary[], questions[], long_tail[], variants[]}.
    """
    kw = _norm(keyword)
    if not kw:
        return {"primary": "", "secondary": [], "questions": [],
                "long_tail": [], "variants": []}
    ent = detect_entity(keyword)
    year = target_year(keyword)
    uni = keyword_universe()
    cluster = ent["name"] if ent else ""
    siblings = [e for e in uni if cluster and e["cluster"] == cluster]
    if not siblings and not ent:
        # free-form keyword: token overlap match
        toks = set(kw.split())
        siblings = [e for e in uni
                    if len(toks & set(e["kw"].split())) >= 2][:400]

    secondary, long_tail = [], []
    for e in siblings:
        if e["kw"] == kw or e["kw"] in secondary or e["kw"] in long_tail:
            continue
        (secondary if e["intent"] in HOT_INTENTS else long_tail).append(e["kw"])
    questions = question_keywords(keyword)
    variants = [f"{kw} {year}", f"{kw} telugu", f"{kw} pdf", f"{kw} direct link",
                f"{kw} latest update"]
    return {
        "primary": kw,
        "secondary": secondary[:limit],
        "questions": questions[:8],
        "long_tail": long_tail[:limit],
        "variants": [v for v in variants if v != kw][:5],
    }


def question_keywords(keyword: str) -> List[str]:
    """Students phone lo adige question-form searches (PAA style)."""
    ent = detect_entity(keyword)
    year = target_year(keyword)
    subject = ent["name"] if ent else _norm(keyword)
    return [
        f"{subject} {year} last date enti",
        f"{subject} apply ela cheyali",
        f"{subject} eligibility enti",
        f"{subject} {year} fee emiti",
        f"{subject} hall ticket eppudu vastundi",
        f"{subject} cut off entha untundi",
        f"{subject} salary enti in hand",
        f"{subject} {year} notification eppudu vastundi",
        f"{subject} documents emi kavali",
        f"{subject} exam centre ela chusukovali",
    ]


def detect_entity(keyword: str) -> Optional[dict]:
    """Keyword lo unna enti (longest match wins) ni detect chey."""
    kw = _norm(keyword)
    best = None
    for name, cat, weight, site in ENTITIES:
        n = _norm(name)
        if n and (f" {n} " in f" {kw} " or kw == n):
            if best is None or len(n) > len(_norm(best["name"])):
                best = {"name": name, "cat": cat, "weight": weight,
                        "official": site, "key": n}
    return best


def detect_intent(keyword: str) -> dict:
    """Keyword lo unna intent (best-scoring axis) ni detect chey."""
    kw = _norm(keyword)
    best, best_hits = None, 0
    for intent_id, title_tmpl, kw_tmpl, funnel, family, demand, comp in ALL_INTENTS:
        phrase = _norm(kw_tmpl.replace("{exam}", "").replace("{year}", ""))
        toks = [t for t in phrase.split() if len(t) > 2]
        hits = sum(1 for t in toks if t in kw.split())
        if hits > best_hits:
            best, best_hits = {
                "intent": intent_id, "funnel": funnel, "family": family,
                "demand": demand, "competition": comp,
            }, hits
    return best or {"intent": "guide", "funnel": "TOFU", "family": "guide",
                    "demand": 3, "competition": 2}


def clusters(uni: Optional[List[dict]] = None) -> List[dict]:
    """Topic clusters = pillar + supporting posts (topical authority plan)."""
    uni = uni if uni is not None else keyword_universe()
    by_cluster: Dict[str, List[dict]] = {}
    for e in uni:
        by_cluster.setdefault(e["cluster"], []).append(e)
    out = []
    for name, rows in by_cluster.items():
        rows = sorted(rows, key=lambda r: (-r["priority"], r["kw"]))
        pillar = next((r for r in rows if r["role"] == "pillar"), rows[0])
        out.append({
            "cluster": name,
            "category": rows[0]["cat"],
            "keywords": len(rows),
            "pillar": pillar["kw"],
            "pillar_title": pillar["title"],
            "cluster_score": round(
                sum(r["priority"] for r in rows[:10]) / max(1, min(10, len(rows))), 1),
            "support": [r["kw"] for r in rows if r["kw"] != pillar["kw"]][:12],
        })
    return sorted(out, key=lambda c: (-c["cluster_score"], c["cluster"]))


PILLAR_INTENT_CYCLE = ("notification", "apply online", "last date", "eligibility",
                       "results", "hall ticket", "syllabus", "direct-link")


def _cluster_pillar(cluster: str, key: str, rows: List[dict]) -> dict:
    """Cluster ki pillar pick — intent cycle tho variety (okke pattern kaadu)."""
    rows = [e for e in rows if e["role"] == "pillar"] or list(rows)
    if not rows:
        return {}
    want = PILLAR_INTENT_CYCLE[_stable_int(cluster + key, len(PILLAR_INTENT_CYCLE))]
    pref = [r for r in rows if r["intent"] == want]
    chosen = (pref or rows)[0]
    return {"kw": chosen["kw"], "title": chosen["title"], "role": "pillar",
            "cluster": cluster, "cat": chosen["cat"], "intent": chosen["intent"],
            "funnel": chosen["funnel"], "priority": chosen["priority"]}


def build_plan(days: int = 90, per_day: int = 1,
               start: Optional[date] = None) -> List[dict]:
    """Dominance calendar: prathi roju top-post keyword (cluster balanced).

    Mix: pillar (exam hub post) + support posts (specific long-tail wins),
    cluster + intent variety tho — okka exam meeda 90 posts kottakunda
    spread (topical authority + spam-safe). Same-day slots veru clusters.
    Deterministic: same arguments → same plan.
    """
    days = max(1, min(int(days or 90), 730))
    per_day = max(1, min(int(per_day or 1), 5))
    start = start or date.today()
    target = days * per_day

    cl = clusters()
    uni = keyword_universe()
    uni_by_kw = {e["kw"]: e for e in uni}
    rows_by_cluster: Dict[str, List[dict]] = {}
    for e in uni:
        rows_by_cluster.setdefault(e["cluster"], []).append(e)

    pillars, supports = [], []
    for idx, c in enumerate(cl):
        p = _cluster_pillar(c["cluster"], f"{idx}",
                            rows_by_cluster.get(c["cluster"], []))
        if p:
            pillars.append(p)
        for s in c["support"]:
            row = uni_by_kw.get(s)
            if not row:
                continue
            supports.append({"kw": row["kw"], "title": row["title"],
                             "role": row.get("role", "support"),
                             "cluster": c["cluster"], "cat": row["cat"],
                             "intent": row.get("intent", ""),
                             "funnel": row.get("funnel", ""),
                             "priority": row.get("priority", 0)})

    # support queue: intent-wise round-robin (okke intent repeat avvakunda)
    pillar_kws = {p["kw"] for p in pillars}
    by_intent: Dict[str, List[dict]] = {}
    for row in sorted((r for r in supports if r["kw"] not in pillar_kws),
                      key=lambda r: (-r["priority"], r["kw"])):
        by_intent.setdefault(row["intent"], []).append(row)
    intent_order = sorted(by_intent,
                          key=lambda i: (-max(r["priority"] for r in by_intent[i]), i))
    ordered_supports = []
    while any(by_intent[i] for i in intent_order):
        for i in intent_order:
            if by_intent[i]:
                ordered_supports.append(by_intent[i].pop(0))

    # pool: pillar, support, support, pillar, ... (2x target — variety kosam)
    pool, pi, si = [], 0, 0
    while len(pool) < target * 2 + per_day:
        if pi < len(pillars) and len(pool) % 3 == 0:
            pool.append(pillars[pi]); pi += 1
        elif si < len(ordered_supports):
            pool.append(ordered_supports[si]); si += 1
        elif pi < len(pillars):
            pool.append(pillars[pi]); pi += 1
        else:
            break

    # greedy day-wise selection: same-day clusters distinct + day-to-day variety
    chosen, cursor, last_day_lead = [], 0, ""
    while len(chosen) < target and cursor < len(pool):
        day_used: set = set()
        for slot in range(per_day):
            if len(chosen) >= target:
                break
            pick = None
            for k in range(cursor, len(pool)):
                item = pool[k]
                if item["cluster"] in day_used:
                    continue
                if slot == 0 and item["cluster"] == last_day_lead and k + 1 < len(pool):
                    continue          # next day different cluster tho start avvali
                pick = k
                break
            if pick is None:          # tail: cluster uniqueness compromise
                for k in range(cursor, len(pool)):
                    if pool[k]["cluster"] not in day_used:
                        pick = k
                        break
            if pick is None:
                break
            day_used.add(pool[pick]["cluster"])
            chosen.append(pool.pop(pick))
            if slot == 0:
                last_day_lead = chosen[-1]["cluster"]
            if pick < cursor:
                cursor = 0
        if not day_used:
            break

    plan = []
    for i, item in enumerate(chosen):
        day_index, slot = divmod(i, per_day)
        day = start + timedelta(days=day_index)
        plan.append(dict(item, date=day.isoformat(), weekday=day.strftime("%a"),
                         slot=slot + 1, weekday_index=day.weekday()))
    return plan

# ===========================================================================
# 4. TOP POST BLUEPRINT
# ===========================================================================

# Outline families: (H2 heading pattern, child H3s, target keywords, purpose)
OUTLINES: Dict[str, List[tuple]] = {
    "notification": [
        ("{exam} {year} – ఒక్క చూపులో ముఖ్య వివరాలు", ["Total vacancies", "Organisation", "Job location"],
         ["quick facts"], "Snippet-ready summary table"),
        ("ముఖ్యమైన తేదీలు (Important Dates)", ["Notification date", "Apply start", "Last date", "Exam date"],
         ["important dates", "last date"], "Date table + deadline box"),
        ("వేకెన్సీలు & పోస్టులు (Vacancy Details)", ["Post wise vacancies", "Category wise breakup", "District wise"],
         ["vacancies", "category wise vacancies"], "Vacancy table (snippet)"),
        ("అర్హతలు ఏమిటి? (Eligibility)", ["Age limit", "Qualification", "Age relaxation", "Physical standards"],
         ["eligibility", "age limit"], "Plain-language eligibility"),
        ("దరఖాస్తు ఫీజు (Application Fee)", ["Category wise fee", "Payment modes", "Fee refund rules"],
         ["application fee"], "Fee table"),
        ("అప్లై ఎలా చేయాలి? (Step by Step Apply)", ["Registration", "Form filling", "Photo & signature upload", "Final submit"],
         ["how to apply", "apply online", "direct link"], "Numbered steps (how-to)"),
        ("అవసరమైన డాక్యుమెంట్స్ (Documents Checklist)", ["Certificates", "Photo signature format", "Common rejection reasons"],
         ["required documents"], "Checklist"),
        ("సెలెక్షన్ ప్రాసెస్ (Selection Process)", ["Written exam", "Physical test", "Certificate verification"],
         ["selection process", "exam pattern"], "Stage-wise table"),
        ("సాలరీ & జాబ్ ప్రొఫైల్", ["Pay scale", "In-hand estimate", "Duties"],
         ["salary", "job profile"], "Only officially published values"),
        ("కామన్ మిస్టేక్స్ (Form Reject Avvakunda)", ["Photo mismatch", "Fee not paid", "Wrong category"],
         ["common mistakes"], "Value-add section"),
        ("FAQ – విద్యార్థుల సాధారణ సందేహాలు", ["6-8 questions"], ["faq"], "Visible Q&A + short answers"),
    ],
    "apply": [
        ("{exam} {year} – Quick Answer (యాప్లై ముందు చదవండి)", ["Last date", "Fee", "Direct link"],
         ["quick answer"], "40-word snippet answer"),
        ("అప్లై చేయడానికి ముందు రెడీ చేసుకోవాల్సినవి", ["Documents", "Photo/signature", "Card details"],
         ["required documents"], "Pre-check list"),
        ("రిజిస్ట్రేషన్ స్టెప్స్ (Step 1)", ["Basic details", "OTP verification", "Password note"],
         ["how to apply"], "Numbered steps"),
        ("ఫారమ్ ఫిల్లింగ్ (Step 2)", ["Personal details", "Education details", "Post preference"],
         ["apply online"], "Numbered steps"),
        ("ఫోటో & సిగ్నేచర్ అప్లోడ్ (Step 3)", ["Specs", "Common errors", "Resize tools"],
         ["photo signature upload"], "Spec table"),
        ("ఫీజు పేమెంట్ (Step 4)", ["Modes", "Failed payment fix", "Receipt check"],
         ["application fee"], "Table + troubleshooting"),
        ("ఫైనల్ సబ్మిట్ & ప్రింట్ (Step 5)", ["Preview check", "Ack number", "Print copy"],
         ["application status check"], "Checklist"),
        ("తరచుగా వచ్చే ఎర్రర్స్ & ఫిక్స్లు", ["Submission error", "Session timeout", "Duplicate application"],
         ["form correction"], "Troubleshooting"),
        ("FAQ – అప్లికేషన్ సందేహాలు", ["5-7 questions"], ["faq"], "Visible Q&A"),
    ],
    "result": [
        ("{exam} {year} రిజల్ట్ – Quick Answer", ["Result status", "Direct link", "Marks memo"],
         ["quick answer"], "Snippet answer"),
        ("రిజల్ట్ ఎలా చూడాలి? (Step by Step)", ["Official site", "Login details", "Download scorecard"],
         ["results check steps"], "Numbered steps"),
        ("మార్క్స్ మెమోలో ఏమి ఉంటుంది?", ["Score", "Percentile", "Qualifying status"],
         ["marks memo"], "Explanation"),
        ("కటాఫ్ (Cut Off) విశ్లేషణ", ["Category wise cut off", "Previous year comparison"],
         ["cut off"], "Comparison table"),
        ("ఇక తర్వాత ఏమి? (Next Steps)", ["Certificate verification", "Counselling", "Joining process"],
         ["next steps"], "Action checklist"),
        ("FAQ – రిజల్ట్ సందేహాలు", ["5-7 questions"], ["faq"], "Visible Q&A"),
    ],
    "hallticket": [
        ("{exam} {year} హాల్ టికెట్ – Quick Answer", ["Release status", "Direct link", "Exam date"],
         ["quick answer"], "Snippet answer"),
        ("హాల్ టికెట్ డౌన్లోడ్ ఎలా చేయాలి?", ["Registration number", "DOB", "PDF save"],
         ["hall ticket download"], "Numbered steps"),
        ("పరీక్ష తేదీ & షిఫ్ట్ టైమింగ్స్", ["Shift timings", "Reporting time", "Gate closing"],
         ["exam date"], "Timing table"),
        ("పరీక్ష కేంద్రంలో పాటించాల్సిన నియమాలు", ["ID proof", "Allowed items", "Banned items"],
         ["exam centre rules"], "Do's and don'ts"),
        ("హాల్ టికెట్లో తప్పు ఉంటే ఏమి చేయాలి?", ["Correction process", "Helpline"],
         ["hall ticket correction"], "Escalation steps"),
        ("FAQ – హాల్ టికెట్ సందేహాలు", ["5-6 questions"], ["faq"], "Visible Q&A"),
    ],
    "answerkey": [
        ("{exam} {year} ఆన్సర్ కీ – Quick Answer", ["Release date", "Download link"],
         ["quick answer"], "Snippet answer"),
        ("ఆన్సర్ కీ డౌన్లోడ్ స్టెప్స్", ["Official link", "PDF", "Set wise key"],
         ["answer key download"], "Numbered steps"),
        ("అభ్యంతరాలు ఎలా పెట్టాలి? (Objection Process)", ["Fee", "Window dates", "Proof format"],
         ["objection process"], "Steps + fee table"),
        ("మార్కులు ఎలా లెక్కించాలి?", ["Correct answers", "Negative marking", "Expected score"],
         ["marks calculation"], "Formula table"),
        ("FAQ – ఆన్సర్ కీ సందేహాలు", ["5 questions"], ["faq"], "Visible Q&A"),
    ],
    "cutoff": [
        ("{exam} {year} కటాఫ్ – Quick Answer", ["Expected range", "Category wise"],
         ["quick answer"], "Snippet answer"),
        ("ఈసారి కటాఫ్ ఎంత ఉండొచ్చు?", ["Factors", "Vacancy effect", "Difficulty"],
         ["expected cut off"], "Reasoned estimate (clearly labelled)"),
        ("గత సంవత్సరాల కటాఫ్ టేబుల్", ["Year wise", "Category wise", "Shift wise"],
         ["previous year cut off"], "Comparison table"),
        ("కటాఫ్ దాటడానికి స్ట్రాటజీ", ["Safe attempts", "Sectional cutoff", "Time management"],
         ["cut off strategy"], "Actionable plan"),
        ("FAQ – కటాఫ్ సందేహాలు", ["5 questions"], ["faq"], "Visible Q&A"),
    ],
    "syllabus": [
        ("{exam} సిలబస్ – Quick Answer", ["Subjects", "Total marks", "Time"],
         ["quick answer"], "Snippet answer"),
        ("ఎగ్జామ్ ప్యాటర్న్ & మార్కింగ్", ["Sections", "Questions", "Negative marking"],
         ["exam pattern", "negative marking"], "Pattern table"),
        ("సబ్జెక్ట్ wise టాపిక్స్", ["Subject 1", "Subject 2", "Subject 3"],
         ["syllabus subject wise"], "Topic lists"),
        ("వెయిటేజ్ & ఇంపార్టెంట్ టాపిక్స్", ["High weight topics", "Repeated topics"],
         ["weightage"], "Weightage table"),
        ("బెస్ట్ బుక్స్ & మెటీరియల్", ["Telugu medium books", "Free PDFs", "Mock tests"],
         ["best books", "previous papers"], "Book table"),
        ("స్టడీ ప్లాన్ (90 రోజులు)", ["Daily timetable", "Revision", "Mock schedule"],
         ["study plan in telugu"], "Timetable table"),
        ("FAQ – సిలబస్ సందేహాలు", ["5-7 questions"], ["faq"], "Visible Q&A"),
    ],
    "salary": [
        ("{exam} సాలరీ – Quick Answer", ["Pay level", "In-hand estimate"],
         ["quick answer"], "Snippet answer"),
        ("పే స్కేల్ వివరాలు", ["Pay level", "Basic pay", "DA/HRA"],
         ["salary in hand"], "Pay table (official values only)"),
        ("ఇన్-హ్యాండ్ సాలరీ ఎలా లెక్కిస్తారు?", ["Deductions", "NPS", "Example calculation"],
         ["in hand salary calculation"], "Example table"),
        ("జాబ్ ప్రొఫైల్ & డ్యూటీలు", ["Work timings", "Field vs office", "Transfer chances"],
         ["job profile"], "Honest duties"),
        ("ప్రమోషన్ & కెరీర్ గ్రోత్", ["Promotion path", "Departmental exams"],
         ["promotion chances"], "Career ladder table"),
        ("FAQ – సాలరీ సందేహాలు", ["5 questions"], ["faq"], "Visible Q&A"),
    ],
    "plan": [
        ("{exam} స్టడీ ప్లాన్ – Quick Answer", ["Days", "Hours/day", "Mock count"],
         ["quick answer"], "Snippet answer"),
        ("మొదట 30 రోజులు – బేసిక్స్", ["Subjects", "Daily target", "Notes method"],
         ["study plan in telugu"], "Week-wise table"),
        ("రెండో 30 రోజులు – ప్రాక్టీస్", ["Mock tests", "Weak areas", "Error log"],
         ["mock test"], "Weekly table"),
        ("చివరి 30 రోజులు – రివిజన్", ["Revision cycle", "Cut off strategy", "Health routine"],
         ["revision plan"], "Checklist"),
        ("టాపర్స్ ఫాలో అయ్యే 7 అలవాట్లు", ["Habits", "Common mistakes"],
         ["toppers strategy", "common mistakes"], "Value-add list"),
        ("FAQ – ప్లాన్ సందేహాలు", ["5 questions"], ["faq"], "Visible Q&A"),
    ],
    "books": [
        ("{exam} బెస్ట్ బుక్స్ – Quick Answer", ["Top 3 books", "Where to buy"],
         ["quick answer"], "Snippet answer"),
        ("స్టాండర్డ్ బుక్స్ లిస్ట్", ["Subject wise", "Author", "Edition"],
         ["best books"], "Book table"),
        ("తెలుగు మీడియం మెటీరియల్", ["Telugu books", "Free PDFs", "YouTube channels"],
         ["preparation in telugu medium"], "Material list"),
        ("కోచింగ్ vs సెల్ఫ్ స్టడీ", ["Cost", "Time", "Result pattern"],
         ["coaching vs self study"], "Comparison table"),
        ("ఫ్రీ రిసోర్సెస్", ["Official PDFs", "Previous papers", "Mock tests"],
         ["previous papers pdf"], "Link list"),
        ("FAQ – బుక్స్ సందేహాలు", ["5 questions"], ["faq"], "Visible Q&A"),
    ],
    "practice": [
        ("{exam} మాక్ టెస్ట్ – Quick Answer", ["Free mock", "Questions", "Time"],
         ["quick answer"], "Snippet answer"),
        ("మాక్ టెస్ట్ ఎలా వాడాలి?", ["Attempt plan", "Analysis", "Error log"],
         ["free mock test telugu"], "Steps"),
        ("ప్రాక్టీస్ స్కోర్ ఇంప్రూవ్ చేసుకునే దారి", ["Accuracy", "Speed", "Section strategy"],
         ["mock test analysis"], "Method"),
        ("FAQ – మాక్ టెస్ట్ సందేహాలు", ["5 questions"], ["faq"], "Visible Q&A"),
    ],
    "mistakes": [
        ("{exam} కామన్ మిస్టేక్స్ – Quick Answer", ["Top mistakes"],
         ["quick answer"], "Snippet answer"),
        ("అప్లికేషన్ లో చేసే తప్పులు", ["Photo", "Fee", "Category", "Signature"],
         ["common mistakes"], "Bullet list"),
        ("పరీక్ష లో చేసే తప్పులు", ["Time", "OMR", "Guess work"],
         ["exam mistakes"], "Bullet list"),
        ("ఎలా కరెక్ట్ చేసుకోవాలి?", ["Checklist", "Reminder system"],
         ["mistake correction"], "Action plan"),
        ("FAQ – సందేహాలు", ["5 questions"], ["faq"], "Visible Q&A"),
    ],
    "scholarship": [
        ("{exam} {year} – Quick Answer", ["Amount", "Last date", "Apply link"],
         ["quick answer"], "Snippet answer"),
        ("ఎవరు అర్హులు? (Eligibility)", ["Income limit", "Marks/Course rules", "Category rules"],
         ["eligibility"], "Plain-language eligibility"),
        ("అవసరమైన డాక్యుమెంట్స్", ["Aadhaar/ID", "Income certificate", "Bonafide/fee receipt"],
         ["required documents"], "Checklist"),
        ("అప్లై ఎలా చేయాలి? (Step by Step)", ["Registration", "Details fill", "Upload", "Submit"],
         ["how to apply", "apply online"], "Numbered steps"),
        ("స్టేటస్ & రెన్యువల్", ["Status check", "Renewal rules", "Common rejections"],
         ["application status check"], "Steps + table"),
        ("ముఖ్యమైన తేదీలు", ["Open date", "Last date", "Verification date"],
         ["last date"], "Date table"),
        ("FAQ – స్కాలర్‌షిప్ సందేహాలు", ["6 questions"], ["faq"], "Visible Q&A"),
    ],
    "admission": [
        ("{exam} {year} – Quick Answer", ["Counselling mode", "Dates", "Official link"],
         ["quick answer"], "Snippet answer"),
        ("కౌన్సెలింగ్ షెడ్యూల్ & తేదీలు", ["Phase 1", "Phase 2", "Spot round"],
         ["counselling dates", "last date"], "Date table"),
        ("వెబ్ ఆప్షన్స్ ఎలా పెట్టాలి? (Step by Step)", ["Login", "Choice order", "Freeze options"],
         ["web options", "how to apply"], "Numbered steps"),
        ("సీట్ అలాట్మెంట్ & ఫీజు", ["Allotment order", "Tuition fee", "Self-reporting steps"],
         ["seat allotment", "application fee"], "Table + steps"),
        ("అవసరమైన డాక్యుమెంట్స్ & సర్టిఫికెట్ వెరిఫికేషన్", ["Certificates", "Rank card", "Verification venues"],
         ["certificate verification"], "Checklist"),
        ("కాలేజీ ఎంపిక & ఫీచర్స్", ["Placements", "Fee vs value", "Hostel"],
         ["best colleges"], "Comparison table"),
        ("FAQ – అడ్మిషన్ సందేహాలు", ["6 questions"], ["faq"], "Visible Q&A"),
    ],
    "career": [
        ("{exam} – Quick Answer", ["Eligibility", "Steps", "Timeline"],
         ["quick answer"], "Snippet answer"),
        ("మొదట ఏమి సిద్ధం చేసుకోవాలి?", ["Checklist", "Free tools", "Time needed"],
         ["how to start"], "Action checklist"),
        ("దశల వారీ ప్రాసెస్ (Step by Step)", ["Step 1", "Step 2", "Step 3"],
         ["how to apply", "step by step"], "Numbered steps"),
        ("టెంప్లేట్ / ఉదాహరణ", ["Sample structure", "Do's", "Don'ts"],
         ["sample format", "template"], "Table + example"),
        ("కామన్ తప్పులు & ఫిక్స్లు", ["Mistakes", "Recruiter expectations"],
         ["common mistakes"], "Bullet list"),
        ("ఫ్రీ రిసోర్సెస్ & ప్రాక్టీస్", ["Free courses", "Practice sites", "Mock"],
         ["free resources"], "Link list (verified only)"),
        ("FAQ – సందేహాలు", ["6 questions"], ["faq"], "Visible Q&A"),
    ],
    "guide": [
        ("{exam} {year} – Quick Answer", ["One-line answer", "Direct link"],
         ["quick answer"], "Snippet answer"),
        ("అన్ని వివరాలు ఒక్క టేబుల్ లో", ["Dates", "Fee", "Vacancies"],
         ["quick facts"], "Summary table"),
        ("ఎలిజిబిలిటీ & ఎంపిక విధానం", ["Age", "Qualification", "Stages"],
         ["eligibility", "selection process"], "Tables"),
        ("దరఖాస్తు & ముఖ్యమైన లింక్స్", ["Apply steps", "Official link", "Helpline"],
         ["apply online", "helpline number"], "Steps + links"),
        ("స్టూడెంట్స్ కోసం టిప్స్", ["Preparation", "Documents", "Deadline"],
         ["preparation tips"], "Value-add"),
        ("FAQ – సాధారణ సందేహాలు", ["6 questions"], ["faq"], "Visible Q&A"),
    ],
}

WORD_TARGETS = {
    "notification": 1900, "apply": 1800, "result": 1300, "hallticket": 1300,
    "answerkey": 1200, "cutoff": 1500, "syllabus": 2000, "salary": 1700,
    "plan": 1800, "books": 1700, "practice": 1300, "mistakes": 1400,
    "guide": 1700, "scholarship": 1700, "admission": 1700, "career": 1600,
}

# Category → family overrides (job-notice language scholarship/admission/
# career pages ki set avvadu — correct outline family vadali).
CAREER_CATEGORIES = {"Internships", "Software Jobs", "Private Jobs",
                     "Part Time Jobs", "Walkin Jobs", "Hall Tickets", "Results"}


def _family_for(family: str, cat: str, keyword: str = "") -> str:
    """Category-aware outline family (scholarship/admission/career pages)."""
    low = (keyword or "").lower()
    if cat == "Online Education" and family in {"guide", "notification", "apply"} \
            and any(w in low for w in ("counselling", "counseling", "web options",
                                       "seat allotment", "admission", "phase")):
        return "admission"
    if cat in {"Internships", "Software Jobs", "Private Jobs", "Part Time Jobs"} \
            and family in {"guide", "notification", "apply", "salary"} \
            and any(w in low for w in ("resume", "interview", "aptitude", "typing",
                                       "internship", "apprentice", "off campus",
                                       "work from home", "course")):
        return "career"
    if cat == "Scholarships" and family in {
            "notification", "apply", "salary", "plan", "guide", "books",
            "practice", "mistakes"}:
        return "scholarship"
    if cat in {"Internships", "Software Jobs", "Private Jobs", "Part Time Jobs",
               "Walkin Jobs"} and family in {
            "notification", "apply", "salary", "plan", "guide", "books",
            "practice", "mistakes", "cutoff", "result"}:
        return "career"
    if cat == "Online Education" and family in {"notification", "apply"}:
        return "admission"
    return family if family in OUTLINES else "guide"


def build_blueprint(keyword: str, category: str = "") -> dict:
    """Keyword → complete top-post plan (offline; deterministic)."""
    kw = _norm(keyword)
    if not kw:
        raise ValueError("keyword khali ga undi — oka search phrase ivvandi")
    ent = detect_entity(keyword)
    intent = detect_intent(keyword)
    year = target_year(keyword)
    exam = ent["name"] if ent else " ".join(w for w in kw.split()[:4]).title()
    cat = category or (ent["cat"] if ent else "Online Education")
    if cat not in LIVE_CATEGORIES:
        cat = "Online Education"
    family = _family_for(intent["family"], cat, keyword)

    outline = []
    idx = 0
    for h2_tmpl, h3s, target_kws, purpose in OUTLINES[family]:
        idx += 1
        h2 = h2_tmpl.format(exam=exam, year=year)
        outline.append({
            "n": idx,
            "h2": h2,
            "id": _slugish(re.sub(r"[^\x00-\x7F]+", " ", h2)) or f"section-{idx}",
            "h3": [h.format(exam=exam, year=year) for h in h3s],
            "target_keywords": [k.format(exam=exam, year=year) for k in target_kws],
            "purpose": purpose,
            "words": max(120, int(WORD_TARGETS[family] / max(1, len(OUTLINES[family])))),
        })

    fam = keyword_family(keyword)
    disp = _pretty_kw(kw, ent)
    title_options = _title_options(kw, exam, year, family, ent=ent)
    meta = _meta_description(kw, exam, year, family, disp=disp)
    words_target = WORD_TARGETS[family]
    official = (ent or {}).get("official", "") or ""
    paa = fam["questions"]
    faq_plan = _faq_plan(exam, year, family)
    schema = ["Article", "BreadcrumbList"]
    if family == "notification":
        schema.append("JobPosting (ONLY with org + real future deadline from the notice)")
    banner = [_clip(exam.upper(), 22),
              _clip(f"{year} {_family_hook(family).upper()}", 22),
              _clip("Telugu + English", 22)]

    bp = {
        "engine": "v38 top-post dominance",
        "keyword": kw,
        "keyword_display": keyword.strip(),
        "exam": exam,
        "year": year,
        "category": cat,
        "intent": intent["intent"],
        "intent_family": family,
        "funnel": intent["funnel"],
        "cluster": exam,
        "role": "pillar" if intent["intent"] in HOT_INTENTS else "support",
        "official_site": official,
        "title_options": title_options,
        "h1": title_options[0]["title"],
        "meta_description": meta,
        "slug": _slugish(kw.replace(" ", "-"), 60) or _slugish(title_options[0]["title"], 60),
        "outline": outline,
        "subtopics_total": sum(len(o["h3"]) for o in outline),
        "entities_to_cover": _entities_to_cover(ent, family),
        "keyword_family": fam,
        "paa_questions": paa,
        "faq_plan": faq_plan,
        "table_plan": _table_plan(family, exam, year),
        "snippet_answer": _snippet_answer(kw, exam, year, family),
        "schema": schema,
        "image": {"banner_lines": banner,
                  "alt": f"{kw} – {cat} {year} | studentup.in",
                  "layout": "bottom-band (crop-safe, center 56% safe zone)"},
        "internal_link_plan": [
            f"{exam} hub page (pillar) — 'Complete {exam} Guide' anchor",
            f"{exam} {year} notification post — 'Notification details' anchor",
            f"{exam} previous papers post — 'Previous papers PDF' anchor",
            f"{cat} category archive — '{cat} latest updates' anchor",
        ],
        "external_link_plan": (
            [f"Official website: https://{official} (only if verified live)"]
            if official else
            ["Official website link MUST be added by the editor — bot does not "
             "guess government URLs"]),
        "word_target": words_target,
        "reading_target_min": max(4, round(words_target / 220)),
        "eeat_checklist": [
            "Named byline + editorial reviewer line",
            "Source check date + corrections email (trust box)",
            "Deadline badge only from the official notice",
            "Facts (dates/fees/vacancies) verifiable — no guessing rule",
            "Visible FAQ + About-this-article block",
        ],
        "ranking_levers": [
            "First 40 words = complete direct answer (WhatsApp forward friendly)",
            "Exact search phrase in title + first paragraph + 2 H2s (no stuffing)",
            "Question-form H2s in student language (Apply ela cheyali? Fee emiti?)",
            "One comparison/summary table + short list items (10 words)",
            "Entities: exam name, organisation, post names, fee, deadline, districts",
            "Internal links: pillar + 3 sibling posts (topical authority)",
            "One verified official external link (E-E-A-T)",
            "Crop-safe thumbnail + keyword alt text",
            "Article + Breadcrumb schema (JobPosting only when honest)",
            "Freshness: update when the official notice changes (dateModified)",
        ],
        "quality_gates": {
            "target_score": getattr(config, "TOP_POST_MIN_SCORE", 78),
            "max_keyword_density": getattr(config, "TOP_POST_MAX_DENSITY", 0.03),
            "min_words": words_target,
            "max_section_words": 320,
            "max_list_item_words": 12,
        },
        "honesty_notes": [
            "Search volume/difficulty bands = heuristic proxies, NOT Google data",
            "Ranking/rich results are never guaranteed by this plan",
            "Dates, fees and vacancies must come from the official notice only",
        ],
    }
    bp["score_preview"] = _blueprint_self_score(bp)
    return bp


SMALL_WORDS = {"and", "or", "in", "of", "to", "for", "the", "a", "an", "lo",
               "on", "with", "vs", "at", "by"}


def _pretty_kw(kw: str, ent: Optional[dict] = None) -> str:
    """'ssc cgl 2026 apply online' → 'SSC CGL 2026 Apply Online' (acronym safe)."""
    text = kw
    if ent:
        n = _norm(ent["name"])
        text = re.sub(r"(?<![\w])" + re.escape(n) + r"(?![\w])",
                      ent["name"].replace("\\", "\\\\"), text, flags=re.I)
    out = []
    for i, w in enumerate(text.split()):
        if re.search(r"[A-Z\d]", w):
            out.append(w)
        elif i and w.lower() in SMALL_WORDS:
            out.append(w.lower())
        else:
            out.append(w[:1].upper() + w[1:])
    return " ".join(out)


def _title_options(kw: str, exam: str, year: int, family: str,
                   ent: Optional[dict] = None) -> List[dict]:
    """3 title variants — keyword front-loaded, 40-62 char sweet spot."""
    kw_title = _pretty_kw(kw, ent)
    year_in_kw = str(year) in kw
    hook = _family_hook(family)
    candidates = [
        f"{kw_title} – Complete Guide" if year_in_kw else f"{kw_title} – Complete Guide {year}",
        f"{exam} {year}: {hook} Telugu lo",
        (f"{kw_title} – Direct Link, Steps & Details" if year_in_kw
         else f"{kw_title} {year} – Direct Link & Steps"),
        f"{hook}: {kw_title}",
        (f"{kw_title} – Latest Update Telugu" if year_in_kw
         else f"{kw_title} {year} – Latest Update Telugu"),
    ]
    out, seen = [], set()
    for c in candidates:
        t = re.sub(r"\s+", " ", c).strip()
        if t.lower() in seen:
            continue
        seen.add(t.lower())
        note = ("sweet spot ✔" if 40 <= len(t) <= 62 else
                ("short — add year/power word" if len(t) < 40 else
                 "long — trim word (Rank Math 40-62)"))
        out.append({"title": t, "chars": len(t), "note": note,
                    "keyword_in_first_half": kw.split()[0] in t[:max(1, len(t) // 2)].lower()})
    out.sort(key=lambda r: (abs(len(r["title"]) - 52), not r["keyword_in_first_half"]))
    return out[:3]


def _clip(text: str, limit: int) -> str:
    """Word-boundary trim (thumbnail banner line ki — mid-word cut avvakudadu)."""
    text = " ".join((text or "").split())
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0].strip()
    return cut or text[:limit]


def _family_hook(family: str) -> str:
    return {
        "notification": "Notification Out",
        "apply": "Apply Online",
        "result": "Result Out",
        "hallticket": "Hall Ticket",
        "answerkey": "Answer Key",
        "cutoff": "Cut Off Analysis",
        "syllabus": "Syllabus & Exam Pattern",
        "salary": "Salary & Job Profile",
        "plan": "Study Plan",
        "books": "Best Books",
        "practice": "Free Mock Test",
        "mistakes": "Common Mistakes",
        "guide": "Full Details",
    }.get(family, "Complete Guide")


def _meta_description(kw: str, exam: str, year: int, family: str,
                      disp: str = "") -> str:
    """110-156 chars, keyword tho start, action + year (Rank Math rule)."""
    head = disp or kw
    core = {
        "notification": (f"{kw} — vacancy count, important dates, eligibility, "
                         f"fee and apply steps. Official notification link and "
                         f"last date {year} complete details Telugu lo."),
        "apply": (f"{kw} — step by step application process, fee, documents "
                  f"checklist and direct link. Form reject avvakunda ee steps "
                  f"follow cheyandi ({year})."),
        "result": (f"{kw} — result check steps, marks memo details, cut off "
                   f"analysis and next steps. Direct link + download process "
                   f"Telugu lo ({year})."),
        "hallticket": (f"{kw} — download steps, exam date, shift timings, centre "
                       f"rules and ID proof list. Common mistakes avoid cheyandi "
                       f"({year})."),
        "answerkey": (f"{kw} — download link, objection process, fee and marks "
                      f"calculation method. Expected score ela lekkinchali Telugu lo."),
        "cutoff": (f"{kw} — expected cut off, previous year tables and category "
                   f"wise analysis. Safe attempts strategy tho target set cheyandi."),
        "syllabus": (f"{kw} — subject wise topics, exam pattern, weightage and "
                     f"best books list. 90 day study plan Telugu medium students ki."),
        "salary": (f"{kw} — pay scale, in-hand calculation, allowances, job "
                   f"profile and promotion details. Officially published values matrame."),
        "plan": (f"{kw} — 90 day timetable, mock test schedule, revision cycle "
                 f"and toppers habits. Daily targets tho preparation start cheyandi."),
        "books": (f"{kw} — subject wise standard books, Telugu medium material, "
                  f"free PDFs and coaching vs self study comparison."),
        "practice": (f"{kw} — free mock test practice, analysis method and speed "
                     f"strategy. Accuracy penchukovadam ela Telugu lo."),
        "mistakes": (f"{kw} — application and exam lo jarige common mistakes, "
                     f"fix steps and checklist. Form reject avvakunda chusukondi."),
        "scholarship": (f"{kw} — eligibility, income limit, required documents, "
                        f"apply steps and status check. Renewal rules and common "
                        f"rejection reasons Telugu lo."),
        "admission": (f"{kw} — counselling schedule, web options steps, seat "
                      f"allotment, fee and certificate verification details. "
                      f"Phase wise dates Telugu lo."),
        "career": (f"{kw} — step by step process, sample format, recruiter "
                   f"expectations and free practice resources. Freshers ki "
                   f"practical guide Telugu lo."),
    }.get(family, (f"{kw} — complete details: eligibility, dates, fee, apply "
                   f"steps and official links. Telugu lo simple ga explain chesam."))
    if core.lower().startswith(kw):
        core = head + core[len(kw):]
    elif not core.lower().startswith(kw.split()[0]):
        core = f"{head} – " + core
    if len(core) > 156:
        core = core[:153].rsplit(" ", 1)[0] + "..."
    if len(core) < 110:
        core = (core + f" {exam} {year} latest update, official link and "
                        "student tips tho complete guide.")[:156]
    return core


def _entities_to_cover(ent: Optional[dict], family: str) -> List[str]:
    base = ["Exam name", "Recruiting organisation", "Post names", "Year",
            "Application fee", "Deadline", "Official portal"]
    if ent:
        base.insert(0, ent["name"])
        base.append(f"{ent['name']} helpline")
    extra = {
        "notification": ["Age relaxation categories", "Vacancy breakup (category/district)",
                         "Exam centres", "Pay level"],
        "apply": ["Photo/signature specs", "Payment modes", "Acknowledgement number"],
        "result": ["Marks memo fields", "Cut off table", "Verification dates"],
        "hallticket": ["Shift timings", "Allowed/banned items", "Exam centre code"],
        "syllabus": ["Subjects", "Marking scheme", "Weightage", "Reference books"],
        "salary": ["Pay level", "DA/HRA", "Deductions", "Promotion path"],
        "plan": ["Daily hours", "Mock count", "Revision cycle"],
        "scholarship": ["Income limit", "Documents", "Renewal rules"],
        "cutoff": ["Category wise marks", "Shift wise variation", "Normalisation"],
    }.get(family, ["Eligibility", "Selection stages", "Preparation strategy"])
    seen, out = set(), []
    for e in base + extra:
        if e.lower() not in seen:
            seen.add(e.lower())
            out.append(e)
    return out


def _table_plan(family: str, exam: str, year: int) -> List[str]:
    tables = {
        "notification": [f"{exam} {year} important dates", "Vacancy & category breakup",
                         "Application fee by category", "Selection stages & marks"],
        "apply": [f"{exam} {year} application fee", "Photo/signature specification",
                  "Apply step timing"],
        "result": ["Category wise cut off", "Previous vs current pass percentage"],
        "hallticket": ["Shift & reporting time", "Allowed vs banned items"],
        "answerkey": ["Subject wise expected score", "Objection fee details"],
        "cutoff": ["Year wise cut off", "Category wise cut off", "Shift wise variation"],
        "syllabus": ["Exam pattern", "Subject wise weightage", "Best books"],
        "salary": ["Pay level & basic pay", "In-hand example calculation",
                   "Promotion ladder"],
        "plan": ["30/60/90 day plan", "Daily timetable", "Mock schedule"],
        "books": ["Book list (subject/author/price band)", "Coaching vs self study"],
        "practice": ["Mock test score tracker", "Section wise accuracy target"],
        "mistakes": ["Common mistakes + fix", "Rejection reasons"],
        "guide": [f"{exam} {year} quick facts", "Eligibility & stages"],
        "scholarship": ["Income limit & amount table", "Documents checklist table",
                        "Important dates"],
        "admission": ["Counselling schedule", "Fee & seat matrix", "Documents checklist"],
        "career": ["Step vs time needed", "Do's vs Don'ts", "Free resource list"],
    }.get(family, ["Quick facts table", "Comparison table"])
    return tables


def _snippet_answer(kw: str, exam: str, year: int, family: str) -> str:
    """First 40 words direct answer — featured snippet pattern."""
    if family == "scholarship":
        return (f"{kw} — ఎవరు అర్హులు, ఎంత ఇస్తారు, ఏ డాక్యుమెంట్స్ కావాలి, "
                f"అప్లై ఎలా చేయాలి, స్టేటస్ ఎలా చూడాలి — అన్నీ ఈ పేజీలో "
                f"స్టెప్ బై స్టెప్ ఉన్నాయి.")
    if family == "admission":
        return (f"{kw} — కౌన్సెలింగ్ తేదీలు, వెబ్ ఆప్షన్స్ స్టెప్స్, సీట్ అలాట్మెంట్, "
                f"ఫీజు, సర్టిఫికెట్ వెరిఫికేషన్ — అన్నీ ఒకే పేజీలో "
                f"క్రమంగా ఉన్నాయి.")
    if family == "career":
        return (f"{kw} — మొదటి నుంచి చివరి వరకు స్టెప్ బై స్టెప్ ప్రాసెస్, "
                f"సాంపిల్ ఫార్మాట్, కామన్ తప్పులు, ఫ్రీ ప్రాక్టీస్ రిసోర్సెస్ "
                f"— అన్నీ ఇక్కడే ఉన్నాయి.")
    text = {
        "notification": (f"{kw} గురించి ముఖ్యమైన వివరాలు: ఎన్ని పోస్టులు, ఎప్పుడు "
                         "దరఖాస్తు, చివరి తేదీ, ఫీజు, అర్హత — అన్నీ ఈ పేజీలో "
                         "ఒక్క టేబుల్ లో ఉన్నాయి. Official notification link కూడా ఇదే."),
        "apply": (f"{kw} — రిజిస్ట్రేషన్ → ఫారమ్ → ఫోటో/సిగ్నేచర్ → ఫీజు → "
                  "ఫైనల్ సబ్మిట్ అనే 5 స్టెప్స్ లో పూర్తి అవుతుంది. ప్రతి స్టెప్ "
                  "స్క్రీన్ షాట్ లాగా క్రింద వివరించాం."),
        "result": (f"{kw} — ఫలితం విడుదలైంది/విడుదల కాబోతుంది. రోల్ నంబర్ + DOB "
                   "ఇచ్చి డైరెక్ట్ లింక్ నుంచి మార్కులు, కటాఫ్ స్టేటస్ చూడొచ్చు. "
                   "స్టెప్ బై స్టెప్ క్రింద ఉంది."),
        "hallticket": (f"{kw} — హాల్ టికెట్ రోల్ నంబర్/రిజిస్ట్రేషన్ నంబర్ + DOB "
                       "ఇచ్చి డౌన్లోడ్ చేసుకోవచ్చు. పరీక్ష తేదీ, షిఫ్ట్ టైమింగ్స్, "
                       "కేంద్రం నియమాలు క్రింద ఉన్నాయి."),
        "cutoff": (f"{kw} — గత సంవత్సరాల ట్రెండ్ బట్టి కటాఫ్ ఇంత ఉండొచ్చు అనే "
                   "అంచనా, కేటగిరీ wise టేబుల్, మరియు సేఫ్ స్కోర్ టార్గెట్ ఈ పేజీలో "
                   "ఉన్నాయి (అంచనా మాత్రమే)."),
        "syllabus": (f"{kw} — సబ్జెక్ట్ wise టాపిక్స్, ఎగ్జామ్ ప్యాటర్న్, మార్కింగ్ "
                    "స్కీమ్, వెయిటేజ్ టేబుల్, బెస్ట్ బుక్స్ — అన్నీ ఒకే పేజీలో."),
        "salary": (f"{kw} — పే లెవెల్, బేసిక్ పే, DA/HRA తో ఇన్-హ్యాండ్ ఎంత "
                   "అవుతుంది అనే ఉదాహరణ లెక్క, డ్యూటీలు, ప్రమోషన్ — అన్నీ ఇక్కడే."),
        "plan": (f"{kw} — 90 రోజుల ప్లాన్: మొదటి 30 బేసిక్స్, రెండో 30 ప్రాక్టీస్, "
                 "చివరి 30 రివిజన్. రోజూ ఎంత సేపు చదవాలి అనే టేబుల్ క్రింద ఉంది."),
    }.get(family, (f"{kw} — అవసరమైన అన్ని వివరాలు: అర్హత, తేదీలు, ఫీజు, "
                   "దరఖాస్తు స్టెప్స్, అధికారిక లింక్స్. ఒక్క చూపులో తెలుసుకోండి."))
    if text.lower().startswith(kw):
        text = _pretty_kw(kw, detect_entity(kw)) + text[len(kw):]
    return text


def _faq_plan(exam: str, year: int, family: str) -> List[str]:
    common = [f"{exam} {year} last date ఎప్పుడు?",
              f"{exam} కి అర్హత ఏమిటి?",
              f"{exam} application fee ఎంత?",
              f"{exam} hall ticket ఎప్పుడు వస్తుంది?",
              f"{exam} సెలెక్షన్ ప్రాసెస్ ఏమిటి?"]
    extra = {
        "notification": [f"{exam} లో ఎన్ని ఖాళీలు ఉన్నాయి?",
                         f"{exam} సాలరీ ఎంత?"],
        "apply": ["అప్లికేషన్ లో ఫోటో సైజు ఎంత?",
                  "ఫీజు పేమెంట్ ఫెయిల్ అయితే ఏమి చేయాలి?"],
        "result": ["మార్క్స్ మెమో ఎలా డౌన్లోడ్ చేయాలి?",
                   "కటాఫ్ కి తక్కువ వచ్చింది, ఇంకా ఛాన్స్ ఉందా?"],
        "hallticket": ["హాల్ టికెట్ లో తప్పు ఉంటే ఏమి చేయాలి?",
                       "పరీక్షకు ఏ ID ప్రూఫ్ తీసుకెళ్లాలి?"],
        "syllabus": ["సిలబస్ లో ఏ టాపిక్స్ ఎక్కువ మార్కులు?",
                     "తెలుగు మీడియం మెటీరియల్ ఎక్కడ దొరుకుతుంది?"],
        "salary": ["ఇన్-హ్యాండ్ సాలరీ ఎంత?",
                   "ప్రమోషన్ కి ఎన్ని సంవత్సరాలు?"],
        "scholarship": ["ఇన్కమ్ లిమిట్ ఎంత?", "స్టేటస్ ఎలా చెక్ చేయాలి?"],
        "admission": ["వెబ్ ఆప్షన్స్ ఎప్పుడు?", "సీట్ వచ్చాక ఏమి చేయాలి?"],
        "career": ["ఎంత టైమ్ పడుతుంది?", "ఫ్రెషర్స్ కి అవకాశం ఉందా?"],
    }.get(family, [f"{exam} official website ఏది?", "అప్లికేషన్ ఎలా మొదలుపెట్టాలి?"])
    return common + extra


def _blueprint_self_score(bp: dict) -> dict:
    """Blueprint completeness score (plan quality, not the article)."""
    checks = []

    def chk(label, ok, weight, fix=""):
        checks.append({"label": label, "ok": bool(ok), "weight": weight, "fix": fix})

    chk("title sweet spot (40-62 chars)", 40 <= bp["title_options"][0]["chars"] <= 62, 10)
    chk("keyword front-loaded title",
        bp["title_options"][0]["keyword_in_first_half"], 8)
    chk("meta description 110-156",
        110 <= len(bp["meta_description"]) <= 156, 8)
    chk("meta/slug keyword present",
        bp["keyword"].split()[0] in bp["meta_description"].lower() and
        bp["keyword"].split()[0] in bp["slug"], 6)
    chk("outline 6+ sections", len(bp["outline"]) >= 6, 12)
    chk("subtopics 10+", bp["subtopics_total"] >= 10, 8)
    chk("question/FAQ plan 5+", len(bp["faq_plan"]) >= 5, 8)
    chk("PAA questions 5+", len(bp["paa_questions"]) >= 5, 6)
    chk("table plan 1+", len(bp["table_plan"]) >= 1, 6)
    chk("snippet answer ready", bool(bp["snippet_answer"]), 8)
    chk("schema planned", len(bp["schema"]) >= 2, 5)
    chk("internal link plan", len(bp["internal_link_plan"]) >= 3, 5)
    chk("image + alt ready", bool(bp["image"]["alt"]), 4)
    chk("word target 1200+", bp["word_target"] >= 1200, 6)
    earned = sum(c["weight"] for c in checks if c["ok"])
    possible = sum(c["weight"] for c in checks) or 1
    score = round(100 * earned / possible)
    return {"score": score,
            "grade": grade_for(score),
            "failed": [c["label"] for c in checks if not c["ok"]]}


def grade_for(score: float) -> str:
    if score >= 90:
        return "TOP POST 🏆"
    if score >= 78:
        return "STRONG 💪"
    if score >= 65:
        return "OK 👌"
    return "WEAK ⚠️"


# --------------------------------------------------------------- blueprint IO

def blueprint_markdown(bp: dict) -> str:
    tl = "\n".join(f"- **{o['title']}** ({o['chars']} chars, {o['note']})"
                   for o in bp["title_options"])
    outline = "\n".join(
        f"{o['n']}. **{o['h2']}** — {o['purpose']} (~{o['words']} words)\n"
        + "".join(f"   - H3: {h}\n" for h in o["h3"])
        + f"   - target keywords: {', '.join(o['target_keywords'])}"
        for o in bp["outline"])
    kwf = bp["keyword_family"]
    tables = "\n".join(f"- {t}" for t in bp["table_plan"])
    schema = "\n".join(f"- {s}" for s in bp["schema"])
    eeat = "\n".join(f"- {s}" for s in bp["eeat_checklist"])
    levers = "\n".join(f"- {s}" for s in bp["ranking_levers"])
    links = "\n".join(f"- {s}" for s in bp["internal_link_plan"])
    ext = "\n".join(f"- {s}" for s in bp["external_link_plan"])
    ents = ", ".join(bp["entities_to_cover"])
    pq = "\n".join(f"- {q}" for q in bp["paa_questions"])
    fq = "\n".join(f"- {q}" for q in bp["faq_plan"])
    honesty = "\n".join(f"- {s}" for s in bp["honesty_notes"])
    return f"""# 🏆 TOP POST BLUEPRINT — {bp['keyword_display']}

**Cluster:** {bp['cluster']} · **Category:** {bp['category']} · **Intent:** {bp['intent']} ({bp['intent_family']}, {bp['funnel']}) · **Role:** {bp['role']}
**Plan quality:** {bp['score_preview']['score']}/100 — {bp['score_preview']['grade']}
**Target:** {bp['word_target']} words (~{bp['reading_target_min']} min) · max section 320 words · keyword density ≤ {bp['quality_gates']['max_keyword_density']:.0%}

## 1. Title options (char-count checked)
{tl}

- Meta: `{bp['meta_description']}`
- H1: {bp['h1']}
- Slug: `{bp['slug']}`
- Official site: {bp['official_site'] or '⚠️ verify manually'}

## 2. H2/H3 outline ({len(bp['outline'])} sections, {bp['subtopics_total']} subtopics)
{outline}

## 3. Keyword family
- Primary: **{kwf['primary']}**
- Secondary: {', '.join(kwf['secondary'][:10]) or '—'}
- Questions: {', '.join(kwf['questions'][:6]) or '—'}
- Long-tail: {', '.join(kwf['long_tail'][:10]) or '—'}

## 4. Entities to cover
{ents}

## 5. Tables to build
{tables}

## 6. Snippet answer (first 40 words)
> {bp['snippet_answer']}

## 7. People Also Ask (target honestly — no placement guarantee)
{pq}

## 8. Visible FAQ plan
{fq}

## 9. Schema
{schema}

## 10. Links
Internal:
{links}

External:
{ext}

## 11. E-E-A-T checklist
{eeat}

## 12. Ranking levers (this is the "top post" difference)
{levers}

## 13. Image
- Banner lines: {' | '.join(bp['image']['banner_lines'])}
- Alt text: `{bp['image']['alt']}`
- Layout: {bp['image']['layout']}

## 14. Honesty notes
{honesty}

---
*Generated by studentup.in v38 Top Post Dominance Engine — plan is deterministic; facts always come from the official source.*
"""


def blueprint_html(bp: dict) -> str:
    """Self-contained, mobile-first blueprint page (design-kit palette)."""
    e = _html.escape
    titles = "".join(
        f"<tr><td>{e(o['title'])}</td><td class='num'>{o['chars']}</td>"
        f"<td>{e(o['note'])}</td></tr>" for o in bp["title_options"])
    outline = "".join(
        f"<div class='card'><h3>{o['n']}. {e(o['h2'])}</h3>"
        f"<p class='muted'>{e(o['purpose'])} · ~{o['words']} words</p>"
        + ("<ul>" + "".join(f"<li>{e(h)}</li>" for h in o["h3"]) + "</ul>")
        + f"<p class='chips'>{''.join(f'<span class=chip>{e(k)}</span>' for k in o['target_keywords'])}</p></div>"
        for o in bp["outline"])
    kwf = bp["keyword_family"]
    chips = lambda items, cls="chip": "".join(f"<span class='{cls}'>{e(i)}</span>" for i in items)  # noqa: E731
    tables = "".join(f"<li>{e(t)}</li>" for t in bp["table_plan"])
    paa = "".join(f"<li>{e(q)}</li>" for q in bp["paa_questions"])
    faq = "".join(f"<li>{e(q)}</li>" for q in bp["faq_plan"])
    levers = "".join(f"<li>{e(s)}</li>" for s in bp["ranking_levers"])
    eeat = "".join(f"<li>{e(s)}</li>" for s in bp["eeat_checklist"])
    links = "".join(f"<li>{e(s)}</li>" for s in bp["internal_link_plan"])
    ext = "".join(f"<li>{e(s)}</li>" for s in bp["external_link_plan"])
    schema = "".join(f"<span class='chip navy'>{e(s)}</span>" for s in bp["schema"])
    honesty = "".join(f"<li>{e(s)}</li>" for s in bp["honesty_notes"])
    gates = bp["quality_gates"]
    failed_label = ", ".join(bp["score_preview"]["failed"]) or "emi ledu — plan perfect ✔"
    return f"""<!doctype html>
<html lang="te">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>TOP POST BLUEPRINT — {e(bp['keyword_display'])}</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Noto+Sans+Telugu:wght@400;600;700&display=swap');
:root{{--navy:#12356B;--navy2:#1B4B90;--orange:#E8842B;--ink:#16233A;--muted:#5C6B82;
--line:#E2E9F3;--soft:#F5F8FD;--green:#14875A;--white:#fff}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--soft);color:var(--ink);
font-family:Inter,'Noto Sans Telugu',system-ui,sans-serif;line-height:1.65}}
header{{background:linear-gradient(135deg,var(--navy),var(--navy2));color:#fff;padding:30px 20px 26px}}
.wrap{{max-width:1080px;margin:auto;padding:0 20px}}
header .wrap{{padding:0}}
.tag{{display:inline-block;background:rgba(255,255,255,.16);border-radius:999px;
padding:6px 12px;font-size:11px;font-weight:700;letter-spacing:.08em;text-transform:uppercase}}
h1{{font-size:clamp(23px,4vw,36px);margin:14px 0 8px;line-height:1.2}}
.sub{{opacity:.9;font-size:13px}}
.scorebar{{display:flex;gap:10px;flex-wrap:wrap;margin-top:16px}}
.score{{background:rgba(255,255,255,.14);border:1px solid rgba(255,255,255,.22);
border-radius:14px;padding:10px 14px;min-width:130px}}
.score b{{display:block;font-size:20px}}
.score span{{font-size:11px;opacity:.85}}
main{{padding:26px 0 70px}}
section{{background:var(--white);border:1px solid var(--line);border-radius:18px;
padding:20px 22px;margin-bottom:16px;box-shadow:0 8px 24px rgba(18,53,107,.05)}}
h2{{font-size:19px;color:var(--navy);margin:0 0 12px;padding-bottom:9px;
border-bottom:2px solid var(--line)}}
h3{{font-size:15px;color:var(--navy);margin:0 0 4px}}
table{{width:100%;border-collapse:collapse;font-size:13.5px}}
th,td{{border:1px solid var(--line);padding:9px 10px;text-align:left;vertical-align:top}}
th{{background:var(--soft);color:var(--navy);font-weight:700}}
td.num{{text-align:center;font-weight:700;color:var(--orange)}}
tr:nth-child(even) td{{background:#FBFDFF}}
ul,ol{{margin:8px 0 0 20px;padding:0}}
li{{margin:5px 0;font-size:13.5px}}
.card{{border:1px solid var(--line);border-left:4px solid var(--orange);
border-radius:12px;padding:13px 15px;margin:10px 0;background:#FFFDFA}}
.muted{{color:var(--muted);font-size:12px;margin:3px 0 6px}}
.chips{{margin:8px 0 0}}
.chip{{display:inline-block;background:#FFF1E3;color:#9A5209;border:1px solid #F6DCC0;
border-radius:999px;padding:3px 10px;font-size:11px;margin:2px 4px 2px 0;font-weight:600}}
.chip.navy{{background:#EAF1FB;color:var(--navy);border-color:#D3E1F5}}
.quote{{background:#FFF8F0;border-left:4px solid var(--orange);border-radius:0 12px 12px 0;
padding:12px 15px;font-size:13.5px;color:#4A5568}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:14px}}
.pill{{display:inline-block;background:#E9F7F0;color:var(--green);border-radius:999px;
padding:4px 11px;font-size:11.5px;font-weight:700;margin:0 6px 6px 0}}
.pill.warn{{background:#FFF4E5;color:#A55B00}}
footer{{text-align:center;color:var(--muted);font-size:12px;padding:0 20px 40px}}
@media print{{header{{background:var(--navy)!important;-webkit-print-color-adjust:exact}}
section{{box-shadow:none;break-inside:avoid}}}}
</style>
</head>
<body>
<header><div class="wrap">
  <span class="tag">v38 Top Post Dominance Engine</span>
  <h1>🏆 {e(bp['keyword_display'])}</h1>
  <p class="sub">Cluster: <b>{e(bp['cluster'])}</b> · Category: {e(bp['category'])} ·
     Intent: {e(bp['intent'])} ({e(bp['intent_family'])}/{e(bp['funnel'])}) ·
     Role: {e(bp['role'])}</p>
  <div class="scorebar">
    <div class="score"><b>{bp['score_preview']['score']}/100</b><span>Plan quality</span></div>
    <div class="score"><b>{bp['word_target']} words</b><span>Target length (~{bp['reading_target_min']} min)</span></div>
    <div class="score"><b>{len(bp['outline'])} H2 · {bp['subtopics_total']} H3</b><span>Outline</span></div>
    <div class="score"><b>{len(kwf['secondary']) + len(kwf['long_tail'])}</b><span>Keyword family</span></div>
  </div>
</div></header>
<main class="wrap">
  <section><h2>1. Title options (Rank Math 40-62 chars)</h2>
    <table><tr><th>Title</th><th>Chars</th><th>Note</th></tr>{titles}</table>
    <p class="muted" style="margin-top:12px"><b>Meta:</b> {e(bp['meta_description'])}</p>
    <p class="muted"><b>H1:</b> {e(bp['h1'])} · <b>Slug:</b> <code>{e(bp['slug'])}</code> ·
       <b>Official:</b> {e(bp['official_site'] or '⚠️ editor verify cheyali')}</p>
  </section>
  <section><h2>2. Section-by-section outline</h2>{outline}</section>
  <section><h2>3. Keyword family (anni keywords)</h2>
    <h3>Primary</h3><p class="chips">{chips([kwf['primary']], 'chip navy')}</p>
    <h3>Secondary (hot intents)</h3><p class="chips">{chips(kwf['secondary'][:12]) or '<span class="muted">—</span>'}</p>
    <h3>Question keywords (PAA style)</h3><p class="chips">{chips(kwf['questions'][:8], 'chip navy')}</p>
    <h3>Long-tail</h3><p class="chips">{chips(kwf['long_tail'][:12]) or '<span class="muted">—</span>'}</p>
  </section>
  <section><h2>4. Entities · Tables · Snippet</h2>
    <div class="grid">
      <div><h3>Entities to cover</h3><p class="chips">{chips(bp['entities_to_cover'], 'chip navy')}</p></div>
      <div><h3>Tables to build</h3><ul>{tables}</ul></div>
    </div>
    <h3 style="margin-top:14px">Snippet answer (first 40 words)</h3>
    <p class="quote">{e(bp['snippet_answer'])}</p>
  </section>
  <section><h2>5. People Also Ask + visible FAQ plan</h2>
    <div class="grid">
      <div><h3>People Also Ask targets</h3><ul>{paa}</ul></div>
      <div><h3>Visible FAQ (in-post)</h3><ul>{faq}</ul></div>
    </div>
  </section>
  <section><h2>6. Schema · Links · Image</h2>
    <h3>Schema</h3><p class="chips">{schema}</p>
    <div class="grid" style="margin-top:12px">
      <div><h3>Internal links (topical authority)</h3><ul>{links}</ul></div>
      <div><h3>External / official links</h3><ul>{ext}</ul></div>
    </div>
    <p class="muted" style="margin-top:10px"><b>Image:</b>
      {' | '.join(e(x) for x in bp['image']['banner_lines'])} —
      alt: <code>{e(bp['image']['alt'])}</code> · {e(bp['image']['layout'])}</p>
  </section>
  <section><h2>7. E-E-A-T + Ranking levers</h2>
    <div class="grid">
      <div><h3>E-E-A-T checklist</h3><ul>{eeat}</ul></div>
      <div><h3>Why this becomes a top post</h3><ul>{levers}</ul></div>
    </div>
  </section>
  <section><h2>8. Quality gates (auto-enforced at publish)</h2>
    <p><span class="pill">score ≥ {gates['target_score']}/100</span>
       <span class="pill">density ≤ {gates['max_keyword_density']:.0%}</span>
       <span class="pill">min {gates['min_words']} words</span>
       <span class="pill">section ≤ {gates['max_section_words']} words</span>
       <span class="pill">list item ≤ {gates['max_list_item_words']} words</span></p>
    <p class="muted">Plan lo migilinavi: {e(failed_label)}</p>
  </section>
  <section><h2>9. Honesty notes</h2><ul>{honesty}</ul></section>
</main>
<footer>studentup.in · v38 Top Post Dominance Engine · blueprint deterministic ·
  facts official source nunchi matrame · ranking guarantee ledu</footer>
</body>
</html>
"""


def write_blueprint(bp: dict, out_dir: Optional[Path] = None) -> Dict[str, str]:
    """Blueprint ni .md + .html + .json ga save chey (output/top-posts)."""
    out = Path(out_dir or (getattr(config, "OUTPUT_DIR", Path("output")) / "top-posts"))
    out.mkdir(parents=True, exist_ok=True)
    base = _slugish(bp["keyword"], 60) or "top-post"
    paths = {"markdown": out / f"{base}.md", "html": out / f"{base}.html",
             "json": out / f"{base}.json"}
    paths["markdown"].write_text(blueprint_markdown(bp), encoding="utf-8")
    paths["html"].write_text(blueprint_html(bp), encoding="utf-8")
    paths["json"].write_text(json.dumps(bp, ensure_ascii=False, indent=2),
                             encoding="utf-8")
    return {k: str(v) for k, v in paths.items()}


def write_universe(out_dir: Optional[Path] = None) -> Dict[str, str]:
    """Anni keywords ni CSV + JSON ga export (Excel lo open cheyochu)."""
    uni = keyword_universe()
    out = Path(out_dir or (getattr(config, "OUTPUT_DIR", Path("output")) / "keywords"))
    out.mkdir(parents=True, exist_ok=True)
    csv_path, json_path = out / "keyword_universe.csv", out / "keyword_universe.json"
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["keyword", "priority", "cluster", "exam", "intent", "tier",
                         "funnel", "family", "role", "category", "demand_band",
                         "competition_band", "year", "official_site", "target_title"])
        for e in uni:
            writer.writerow([e["kw"], e["priority"], e["cluster"], e["exam"],
                             e["intent"], e["tier"], e["funnel"], e["family"],
                             e["role"], e["cat"], e["demand"], e["competition"],
                             e["year"], e["official"], e["title"]])
    json_path.write_text(json.dumps(uni, ensure_ascii=False, indent=2),
                         encoding="utf-8")
    return {"csv": str(csv_path), "json": str(json_path), "count": len(uni)}


def write_plan(plan: List[dict], out_dir: Optional[Path] = None) -> Dict[str, str]:
    out = Path(out_dir or (getattr(config, "OUTPUT_DIR", Path("output")) / "top-posts"))
    out.mkdir(parents=True, exist_ok=True)
    csv_path, json_path = out / "dominance-plan.csv", out / "dominance-plan.json"
    md_path = out / "dominance-plan.md"
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["date", "weekday", "keyword", "role", "cluster", "category",
                    "intent", "funnel", "priority", "proposed_title"])
        for p in plan:
            w.writerow([p["date"], p["weekday"], p["kw"], p["role"], p["cluster"],
                        p.get("cat", ""), p.get("intent", ""), p.get("funnel", ""),
                        p.get("priority", ""), p["title"]])
    json_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = ["# 🗓️ 90-Day Keyword Domination Plan", "",
             f"Total posts: {len(plan)} · clusters: "
             f"{len({p['cluster'] for p in plan})}", "",
             "| Date | Day | Keyword | Role | Cluster | Proposed title |",
             "|---|---|---|---|---|---|"]
    for p in plan:
        lines.append(f"| {p['date']} | {p['weekday']} | {p['kw']} | {p['role']} | "
                     f"{p['cluster']} | {p['title']} |")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"csv": str(csv_path), "json": str(json_path), "markdown": str(md_path)}


# ===========================================================================
# 5. TOP POST SCORE (real article/HTML ni measure cheyadam)
# ===========================================================================

UTILITY_PARA_CLASSES = ("su-reading-badge", "su-qa", "su-byline",
                        "su-deadline", "su-breadcrumbs", "su-crumb-current",
                        "su-reading", "screen-reader")
UTILITY_PARA_STARTS = ("last updated", "source check", "reading time",
                       "reviewed by", "✍️", "⏱️", "🗓️", "📊")


def _first_content_para(html: str) -> str:
    """Article ki first CONTENT paragraph (badge/byline/snippet cards skip)."""
    for m in re.finditer(r"<p([^>]*)>(.*?)</p>", html, flags=re.S):
        attrs, inner = m.group(1), m.group(2)
        cls = (re.search(r"""class=["']([^"']*)["']""", attrs) or [None, ""])[1]
        if any(u in cls for u in UTILITY_PARA_CLASSES):
            continue
        text = " ".join(validator.strip_tags(inner).split())
        if len(text.split()) < 8:
            continue
        if text.lower().startswith(UTILITY_PARA_STARTS):
            continue
        return text.lower()
    return ""


def _count_phrase(text_low: str, phrase: str) -> int:
    if not phrase:
        return 0
    return len(re.findall(r"(?<![\w])" + re.escape(phrase) + r"(?![\w])", text_low))


def score_top_post(article: dict, keyword: str = "", html: str = "") -> dict:
    """30+ weighted checks → 0-100 Top Post Score + graded fixes.

    Article dict nunchi title/meta/slug/faq/tags, HTML nunchi content.
    Keyword default = article['focus_keyword'].
    """
    kw = _norm(keyword or article.get("focus_keyword") or "")
    html = html or article.get("content_html", "") or ""
    title = article.get("title", "") or ""
    title_low = title.lower()
    meta = article.get("meta_description", "") or ""
    slug = article.get("slug", "") or ""
    plain = validator.strip_tags(html)
    plain_low = plain.lower()
    words = max(1, len(plain.split()))
    h2s = [validator.strip_tags(h) for h in
           re.findall(r"<h2[^>]*>(.*?)</h2>", html, flags=re.S)]
    h3s = [validator.strip_tags(h) for h in
           re.findall(r"<h3[^>]*>(.*?)</h3>", html, flags=re.S)]
    fam = keyword_family(kw) if kw else {"secondary": [], "questions": [],
                                         "long_tail": [], "variants": []}
    checks: List[dict] = []

    def chk(cid, label, ok, weight, fix=""):
        checks.append({"id": cid, "label": label, "ok": bool(ok),
                       "weight": weight, "fix": fix})

    if not kw:
        chk("kw-set", "focus keyword set", False, 4,
            "focus_keyword set cheyandi — top post ki exact search phrase kavali")

    # --- title layer ---
    chk("kw-title", "focus keyword title lo", kw and kw in title_low, 7,
        "title lo exact focus keyword pettandi (first half lo)")
    kw_pos = title_low.find(kw) if kw else -1
    chk("kw-title-half", "keyword title MODALO (first 40%)",
        bool(kw) and 0 <= kw_pos <= max(1, int(len(title_low) * 0.4)), 4,
        "keyword ni title MODALO ki move cheyandi (first 40% lo start avvali)")
    chk("title-len", "title 40-62 chars", 40 <= len(title) <= 62, 4,
        f"title {len(title)} chars — 40-62 ki adjust cheyandi")
    chk("title-number", "title lo number/year", bool(re.search(r"\d", title)), 3,
        "title lo year/vacancy number add cheyandi")
    chk("title-power", "power word (Complete/Best/Top)",
        any(w in title_low for w in POWER_WORDS), 3,
        "title lo Complete/Best/Top/Easy lanti power word add cheyandi")

    # --- meta + slug ---
    chk("kw-meta", "keyword meta description lo", kw and kw in meta.lower(), 5,
        "meta description lo focus keyword undali")
    chk("meta-len", "meta 110-160 chars", 110 <= len(meta) <= 160, 3,
        f"meta {len(meta)} chars — 110-156 ki set cheyandi")
    slug_tokens = [t for t in kw.split() if len(t) > 2] if kw else []
    chk("kw-slug", "keyword tokens URL lo",
        bool(slug) and sum(1 for t in slug_tokens if t in slug.lower()) >=
        min(2, max(1, len(slug_tokens))), 4,
        "slug lo keyword tokens pettandi")

    # --- body keyword placement ---
    first_para = _first_content_para(html)
    first100 = " ".join(plain_low.split()[:100])
    chk("kw-first-para", "keyword first content paragraph lo",
        kw and kw in first_para, 6,
        "first content paragraph lo focus keyword rawali (intro lo)")
    chk("kw-first-100", "keyword first 100 words lo", kw and kw in first100, 4,
        "first 100 words lo keyword + clear answer ivvandi")
    chk("kw-h2", "2+ H2 lo keyword", kw and sum(1 for h in h2s if kw in h.lower()) >= 2, 5,
        "2 H2 headings lo focus keyword undali")
    occ = _count_phrase(plain_low, kw) if kw else 0
    density = occ / words
    chk("kw-density", "density 0.4%-3% (stuffing ledu)",
        0.004 <= density <= 0.03, 5,
        f"density {density:.2%} — 8-15 mentions madhya pettandi")

    # --- keyword family coverage ---
    sec_hits = sum(1 for k in fam["secondary"][:10] if k.lower() in plain_low)
    chk("secondary-cov", "secondary keywords 3+ present", sec_hits >= 3, 5,
        f"secondary keywords {sec_hits} matrame — inko 2 related phrases natural ga add cheyandi")
    lt_hits = sum(1 for k in fam["long_tail"][:12] if k.lower() in plain_low)
    chk("longtail-cov", "long-tail phrases 2+ present", lt_hits >= 2, 4,
        "long-tail phrases (district wise, in telugu, pdf...) 2+ natural ga cover cheyandi")
    q_hits = sum(1 for q in fam["questions"][:8]
                 if _norm(q) and _norm(q) in _norm(plain))
    has_question_h = any(re.search(r"\?|ela|enti|emiti|eppudu|how|what", h.lower())
                         for h in h2s + h3s)
    chk("question-headings", "question-form headings/question keywords", q_hits >= 1 or has_question_h, 4,
        "'Apply ela cheyali?' lanti question H2/H3 add cheyandi")

    # --- structure ---
    chk("words", f"words >= {getattr(config, 'TOP_POST_WORDS_TARGET', 1500)}",
        words >= int(getattr(config, "TOP_POST_WORDS_TARGET", 1500)), 6,
        f"content {words} words — target {getattr(config, 'TOP_POST_WORDS_TARGET', 1500)}+")
    chk("h2-count", "6+ H2 sections", len(h2s) >= 6, 4,
        f"H2 sections {len(h2s)} — 6+ ki split cheyandi")
    chk("h3-count", "4+ H3 subtopics", len(h3s) >= 4, 3,
        "H3 subtopics add cheyandi (scan-ability)")
    seg = re.split(r"<h[23][^>]*>", html)
    seg_words = [len(validator.strip_tags(s).split()) for s in seg[1:]]
    long_sec = sum(1 for w in seg_words if w > 320)
    chk("section-split", "no section 320+ words", long_sec == 0, 3,
        f"{long_sec} sections 320+ words — kotha H2/H3 tho split cheyandi")
    paras = [validator.strip_tags(p) for p in
             re.findall(r"<p[^>]*>(.*?)</p>", html, flags=re.S)]
    long_paras = sum(1 for p in paras if len(p.split()) > 120)
    chk("para-length", "no paragraph 120+ words", long_paras == 0, 3,
        f"{long_paras} paragraphs 120+ words — 2-3 sentences ki chotu cheyandi")

    # --- snippets + rich elements ---
    chk("table", "table 1+ (snippet)",
        html.count("<table") >= 1, 4, "oka summary/comparison table add cheyandi")
    chk("lists", "ul/ol lists", ("<ul" in html or "<ol" in html), 3,
        "step-by-step list add cheyandi")
    lis = [validator.strip_tags(x).split()
           for x in re.findall(r"<li[^>]*>(.*?)</li>", html, flags=re.S)]
    bad_li = sum(1 for w in lis if len(w) > 12)
    chk("list-short", "list items <= 12 words", bad_li == 0 and bool(lis), 3,
        f"{bad_li} list items 12+ words — step ni split cheyandi")
    chk("snippet-answer", "quick answer / snippet block",
        ("su-quick-answer" in html) or bool(article.get("quick_answer")), 5,
        "quick_answer / snippet block add cheyandi (first 40 words answer)")
    chk("faq-visible", "FAQ 4+ questions",
        len(article.get("faq") or []) >= 4
        or sum(1 for h in h3s if h.strip().endswith("?")) >= 4, 4,
        "FAQ 4+ questions (visible + honest answers)")

    # --- links + schema + image ---
    links = re.findall(r"""href=["'](http[^"']+)["']""", html)
    host = validator.config_site_host()
    n_internal = sum(1 for l in links if host and host in l)
    n_external = len(links) - n_internal
    chk("internal-links", "internal links 2+", n_internal >= 2, 4,
        f"internal links {n_internal} — pillar + sibling posts ki link cheyandi")
    chk("external-links", "official external link 1+", n_external >= 1, 3,
        "oka official website link add cheyandi (E-E-A-T)")
    chk("schema", "Article/Breadcrumb schema",
        "application/ld+json" in html and '"Article"' in html, 4,
        "Article + Breadcrumb JSON-LD emit avvali (SEO_SCHEMA_ENABLED check)")
    media_alt = str(article.get("_media_alt") or "").lower()
    chk("image-alt", "image alt lo keyword",
        (bool(kw) and kw in media_alt)
        or bool(re.search(r"""alt=["'][^"']*""" + re.escape((kw or "\x00").split()[0])
                           + r"""[^"']*["']""", html)) if kw else False, 2,
        "featured image alt text lo keyword pettandi")
    chk("byline", "byline / editorial line",
        ("su-byline" in html) or bool(article.get("author")), 2,
        "byline + reviewer line add cheyandi (E-E-A-T)")
    chk("trust-box", "corrections/trust box",
        ("su-trust-box" in html) or ("corrections" in html.lower()), 2,
        "About-this-article + corrections line add cheyandi")
    chk("fresh-date", "source check / updated date", bool(
        re.search(r"\d{4}-\d{2}-\d{2}|Last Updated|Source check", html)), 2,
        "source check date / last-updated line add cheyandi")
    chk("readability", "avg sentence <= 22 words",
        _avg_sentence_words(plain) <= 22, 3,
        "sentences poduguparuchu — 15-20 words ki chotu cheyandi")
    chk("entities", "5+ entity mentions",
        _entity_hits(plain, kw) >= 5, 3,
        "exam/org/post/fee/date lanti entities cover cheyandi")

    earned = sum(c["weight"] for c in checks if c["ok"])
    possible = sum(c["weight"] for c in checks) or 1
    score = round(100 * earned / possible)
    failed = [c for c in checks if not c["ok"]]
    return {
        "score": score,
        "grade": grade_for(score),
        "checks": checks,
        "failed": [c["label"] for c in failed],
        "fixes": [c["fix"] for c in failed if c["fix"]],
        "words": words,
        "keyword": kw,
        "density": round(density, 4),
        "occurrences": occ,
        "secondary_hits": sec_hits,
        "longtail_hits": lt_hits,
        "question_hits": q_hits,
        "internal_links": n_internal,
        "external_links": n_external,
    }


def _avg_sentence_words(text: str) -> float:
    sents = [s for s in re.split(r"[.!?\u0964]\s", text) if len(s.split()) >= 3]
    if not sents:
        return 0.0
    return sum(len(s.split()) for s in sents) / len(sents)


def _entity_hits(plain: str, kw: str) -> int:
    """Content lo unna distinct entity-ish mentions (exam/org/number/fee)."""
    low = plain.lower()
    hits = 0
    for name, _cat, _w, _s in ENTITIES:
        if _norm(name) in _norm(low):
            hits += 2
            break
    for pat in (r"₹\s?\d", r"\brs\.?\s?\d", r"\b\d{4}\b", r"\bfee\b",
                r"\bsalary|pay scale|pay level\b", r"\bdocument", r"\bexam centre",
                r"\bhelpline", r"\b\d+\s?(posts|vacancies)", r"\bdistrict"):
        if re.search(pat, low):
            hits += 1
    return hits


# ===========================================================================
# 6. HARDEN (structural fixes only — no invented facts) + publish gate
# ===========================================================================

def _first_sentence(html: str, max_words: int = 45) -> str:
    m = re.search(r"<p[^>]*>(.*?)</p>", html, flags=re.S)
    if not m:
        return ""
    text = " ".join(validator.strip_tags(m.group(1)).split())
    parts = re.split(r"(?<=[.!?\u0964])\s", text)
    out = parts[0] if parts else text
    return " ".join(out.split()[:max_words]).strip()


def _extract_faq_from_html(html: str, limit: int = 6) -> List[Dict[str, str]]:
    """Article OWN content nunchi Q&A pairs teeyadam (kotha facts ledu)."""
    pairs: List[Dict[str, str]] = []
    pattern = re.compile(
        r"<h3[^>]*>(.*?)</h3>\s*(?:<p[^>]*>(.*?)</p>)", flags=re.S)
    for m in pattern.finditer(html):
        q = " ".join(validator.strip_tags(m.group(1)).split())
        a = " ".join(validator.strip_tags(m.group(2)).split())
        if not q or not a or len(a.split()) < 4:
            continue
        looks_question = ("?" in q or re.search(
            r"\b(ela|enti|emiti|eppudu|ekkada|entha|how|what|when|where|why|which)\b",
            q.lower()))
        if not looks_question:
            continue
        pairs.append({"question": q[:160], "answer": a[:320]})
        if len(pairs) >= limit:
            break
    return pairs


def _cap_density(html: str, kw: str, max_count: int) -> Tuple[str, int]:
    """Exact keyword repeat ni cap chey — over-optimization (spam) signal safe.

    Only text nodes touch chestundi (tags/attributes/links safe). Cap paina
    unna extras ni intent-aware short reference tho replace chestundi.
    """
    if not kw or max_count < 1:
        return html, 0
    parts = re.split(r"(<[^>]+>)", html)
    pattern = re.compile(r"(?<![\w])(" + re.escape(kw) + r")(?![\w])", re.I)
    seen = 0
    replaced = 0

    def _sub(m: re.Match) -> str:
        nonlocal seen, replaced
        seen += 1
        if seen <= max_count:
            return m.group(0)
        replaced += 1
        return "ee notification" if "notification" in kw else (
            "ee exam" if any(w in kw for w in ("exam", "test", "tet")) else "idi")

    for i in range(0, len(parts), 2):        # even indices = text nodes
        parts[i] = pattern.sub(_sub, parts[i])
    return "".join(parts), replaced


def harden(article: dict, keyword: str = "") -> Tuple[dict, dict]:
    """Publish mundu structural hardening (kotha facts eppudu add cheyyadu).

    Fixes: focus keyword default, secondary keywords fill, meta description
    length/keyword, slug tokens, snippet answer (article nunchi extract),
    visible FAQ extraction (article own H3s), density cap (max repeat).
    """
    if not getattr(config, "TOP_POST_ENGINE", True):
        return article, {"enabled": False}
    kw = _norm(keyword or article.get("focus_keyword") or "")
    before = score_top_post(article, kw).get("score", 0)
    changes: List[str] = []

    if not article.get("focus_keyword") and kw:
        article["focus_keyword"] = kw
        changes.append("focus_keyword default set")

    fam = keyword_family(kw) if kw else {"secondary": [], "questions": [],
                                         "long_tail": []}
    sec = [str(s) for s in (article.get("secondary_keywords") or []) if str(s).strip()]
    if len(sec) < 3:
        for cand in fam["secondary"] + fam["long_tail"] + fam["questions"]:
            if cand and cand not in sec:
                sec.append(cand)
            if len(sec) >= 6:
                break
        if sec != (article.get("secondary_keywords") or []):
            article["secondary_keywords"] = sec[:6]
            changes.append(f"secondary_keywords filled ({len(sec[:6])})")

    meta = (article.get("meta_description") or "").strip()
    if kw and (kw not in meta.lower() or not (110 <= len(meta) <= 160)):
        src = (article.get("quick_answer") or _first_sentence(
            article.get("content_html", "")) or meta)
        src = " ".join(validator.strip_tags(src).split())
        new_meta = (f"{kw} – {src}" if src and kw not in src.lower() else src)
        if len(new_meta) > 160:
            new_meta = new_meta[:157].rsplit(" ", 1)[0] + "..."
        if len(new_meta) < 110:
            new_meta = (new_meta + f" {kw} latest update, official link and "
                                    "step by step details Telugu lo.")[:160]
        if new_meta and new_meta != meta:
            article["meta_description"] = new_meta
            changes.append("meta_description length/keyword fixed")

    slug = (article.get("slug") or "").lower()
    if kw and slug:
        toks = [t for t in kw.split() if len(t) > 2]
        if sum(1 for t in toks if t in slug) < min(2, max(1, len(toks))):
            from . import seo as _seo

            new_slug = _seo.optimize_slug(slug, focus_keyword=kw)
            if new_slug and new_slug != slug:
                article["slug"] = new_slug
                changes.append(f"slug -> {new_slug}")

    if kw and not (article.get("quick_answer") or "").strip():
        first = _first_sentence(article.get("content_html", ""))
        if first and len(first.split()) >= 6:
            article["quick_answer"] = first
            changes.append("quick_answer extracted from the article's own first paragraph")

    faq = list(article.get("faq") or [])
    if len(faq) < 4:
        found = _extract_faq_from_html(article.get("content_html", ""),
                                       limit=6 - len(faq))
        for pair in found:
            if not any(_norm(pair["question"]) == _norm(f.get("question", ""))
                       for f in faq):
                faq.append(pair)
        if len(faq) > len(article.get("faq") or []):
            article["faq"] = faq
            changes.append(f"faq extracted from own H3 answers ({len(faq)})")

    html = article.get("content_html", "") or ""
    words = max(1, len(validator.strip_tags(html).split()))
    occ = _count_phrase(validator.strip_tags(html).lower(), kw) if kw else 0
    max_count = int(words * float(getattr(config, "TOP_POST_MAX_DENSITY", 0.03)))
    if kw and occ > max(max_count, 3):
        html, replaced = _cap_density(html, kw, max_count)
        if replaced:
            article["content_html"] = html
            changes.append(f"density cap: {replaced} extra keyword repeats trimmed")

    after_report = score_top_post(article, kw)
    report = {
        "enabled": True,
        "score_before": before,
        "score_after": after_report["score"],
        "grade": after_report["grade"],
        "changes": changes,
        "failed_checks": after_report["failed"],
        "fixes_for_editor": after_report["fixes"][:8],
        "density": after_report["density"],
    }
    article["_top_post"] = report
    if changes:
        log.info("v38 harden: %s (score %s -> %s)", "; ".join(changes),
                 before, after_report["score"])
    return article, report


def publish_gate(article: dict, keyword: str = "",
                 html: str = "", live: Optional[bool] = None) -> Tuple[bool, str]:
    """Live publish ki Top Post Score gate (draft lu eppudu allow).

    live=None → article status / DEFAULT_POST_STATUS nunchi decide.
    """
    if not getattr(config, "TOP_POST_ENGINE", True):
        return True, "engine off"
    if not getattr(config, "TOP_POST_STRICT", True):
        return True, "strict mode off"
    if live is None:
        live = (article.get("status") or config.DEFAULT_POST_STATUS) == "publish"
    if not live:
        return True, "draft — gate not enforced"
    report = article.get("_top_post") or article.get("_top") or score_top_post(
        article, keyword, html)
    target = int(getattr(config, "TOP_POST_MIN_SCORE", 78))
    if report.get("score", 0) < target:
        return False, (f"TOP-POST GATE: score {report.get('score')}/100 < {target} — "
                       f"fix these first: " + "; ".join((report.get("fixes") or [])[:4]))
    return True, f"top post score {report.get('score')}/100 ✔"



# ===========================================================================
# 7. BLUEPRINT → ARTICLE (Gemini brief / offline mock)
# ===========================================================================

def gemini_brief(bp: dict) -> str:
    """Blueprint ni Gemini prompt ki compact Top Post brief ga marchu."""
    outline = "\n".join(
        f"{o['n']}. H2: {o['h2']} | H3s: {', '.join(o['h3'])} | "
        f"target: {', '.join(o['target_keywords'])}" for o in bp["outline"])
    kwf = bp["keyword_family"]
    return f"""TOP POST BLUEPRINT (v38 — idi follow cheyandi; facts matrame source nunchi):
- PRIMARY KEYWORD (exact search phrase): {bp['keyword']}
- SECONDARY: {', '.join(kwf['secondary'][:6]) or '—'}
- QUESTION KEYWORDS (students actually type): {'; '.join(kwf['questions'][:5]) or '—'}
- TITLE: focus keyword FIRST HALF lo + year + power word, 40-62 chars.
- META: 110-156 chars, keyword tho start.
- WORD TARGET: {bp['word_target']}+ words, prathi section <= 320 words.
- STRUCTURE (ee order lo, H2 text ni mee own words lo rayochu):
{outline}
- ENTITIES to mention: {', '.join(bp['entities_to_cover'][:10])}
- TABLES: {'; '.join(bp['table_plan'][:3])}
- SNIPPET ANSWER (first 40 words direct answer): {bp['snippet_answer'][:220]}
- FAQ (visible, honest): {'; '.join(bp['faq_plan'][:6])}
- KEYWORD RULE: exact phrase 8-15 sarlu matrame (density 1-2%); stuffing = penalty.
- LINKS: official website 1 + mana site related pages ki anchor phrases.
- DO NOT invent dates/fees/vacancies; source notice lo lenivi rayakandi.
- E-E-A-T: "notification prakaram" phrasing + source check line."""


def mock_article(bp: dict) -> dict:
    """Offline blueprint-driven draft (test/preview kosam — fake facts ledu)."""
    rows = "".join(
        f"<tr><td>{o['h2'][:40]}</td><td>{o['purpose']}</td><td>~{o['words']} words</td></tr>"
        for o in bp["outline"][:5])
    body = [f"<p>{bp['snippet_answer']}</p>", "<h2>Section overview</h2>",
            "<table><tr><th>Section</th><th>Purpose</th><th>Length</th></tr>"
            + rows + "</table>"]
    for o in bp["outline"]:
        body.append(f"<h2>{o['h2']}</h2>")
        for h in o["h3"]:
            body.append(f"<h3>{h}</h3><p>[Editor: source-notice nunchi details "
                        f"verify chesi rayandi — {h}.]</p>")
    content = "".join(body)
    return {
        "title": bp["title_options"][0]["title"],
        "slug": bp["slug"],
        "meta_description": bp["meta_description"],
        "category": bp["category"],
        "tags": [bp["exam"], str(bp["year"]), bp["exam"].split()[0], "Students",
                 "Telugu", bp["intent"]][:8],
        "focus_keyword": bp["keyword"],
        "secondary_keywords": (bp["keyword_family"]["secondary"][:4]
                               + bp["keyword_family"]["questions"][:2]),
        "quick_answer": bp["snippet_answer"],
        "banner_text": "\n".join(bp["image"]["banner_lines"]),
        "content_html": content,
        "faq": [],
        "external_links": ([{"text": f"{bp['exam']} official site",
                             "url": "https://" + bp["official_site"]}]
                           if bp["official_site"] else []),
        "article_type": "top-post",
        "_mock": True,
        "_blueprint": {"keyword": bp["keyword"], "intent": bp["intent"],
                       "family": bp["intent_family"]},
    }


# ===========================================================================
# 8. CLI helpers (main.py vadutundi)
# ===========================================================================

def run_blueprint(keyword: str, category: str = "", out_dir: Optional[Path] = None,
                  quiet: bool = False) -> int:
    bp = build_blueprint(keyword, category=category)
    paths = write_blueprint(bp, out_dir)
    if not quiet:
        print("=" * 68)
        print(f"  🏆 TOP POST BLUEPRINT — {bp['keyword_display']}")
        print("=" * 68)
        print(f"  Cluster      : {bp['cluster']}  ({bp['category']})")
        print(f"  Intent       : {bp['intent']}  [{bp['intent_family']} · {bp['funnel']} · {bp['role']}]")
        print(f"  Plan quality : {bp['score_preview']['score']}/100  {bp['score_preview']['grade']}")
        print(f"  Target       : {bp['word_target']} words · {len(bp['outline'])} H2 · "
              f"{bp['subtopics_total']} H3 · density ≤ {bp['quality_gates']['max_keyword_density']:.0%}")
        print("\n  TITLE OPTIONS")
        for o in bp["title_options"]:
            print(f"    • {o['title']}  [{o['chars']} chars · {o['note']}]")
        print(f"\n  META  : {bp['meta_description']}")
        print(f"  SLUG  : {bp['slug']}")
        print("\n  OUTLINE")
        for o in bp["outline"]:
            print(f"    {o['n']}. {o['h2']}  ({o['purpose']})")
            for h in o["h3"]:
                print(f"        · {h}")
        kwf = bp["keyword_family"]
        print(f"\n  KEYWORD FAMILY: primary 1 · secondary {len(kwf['secondary'])} · "
              f"questions {len(kwf['questions'])} · long-tail {len(kwf['long_tail'])}")
        print(f"    secondary : {', '.join(kwf['secondary'][:6]) or '—'}")
        print(f"    questions : {', '.join(kwf['questions'][:4]) or '—'}")
        print(f"\n  TABLES : {'; '.join(bp['table_plan'][:3])}")
        print(f"  SCHEMA : {', '.join(bp['schema'])}")
        print(f"  IMAGE  : alt='{bp['image']['alt']}'")
        print(f"\n  FILES  : {paths['html']}")
        print(f"           {paths['markdown']}")
        print(f"           {paths['json']}")
        if bp["score_preview"]["failed"]:
            print(f"\n  ⚠️  Plan gaps: {', '.join(bp['score_preview']['failed'])}")
        print("=" * 68)
    return 0


def run_plan(days: int = 90, per_day: int = 1, out_dir: Optional[Path] = None,
             show: int = 14) -> int:
    plan = build_plan(days=days, per_day=per_day)
    paths = write_plan(plan, out_dir)
    clusters_n = len({p["cluster"] for p in plan})
    print("=" * 68)
    print(f"  🗓️  KEYWORD DOMINATION PLAN — {len(plan)} posts · {clusters_n} clusters")
    print("=" * 68)
    for p in plan[:show]:
        print(f"  {p['date']} {p['weekday']}  [{p['role']:<7}] {p['kw'][:44]:<44} "
              f"→ {p['cluster']}")
    if len(plan) > show:
        print(f"  … inka {len(plan) - show} posts (full list files lo)")
    print(f"\n  FILES: {paths['csv']}\n         {paths['markdown']}\n         {paths['json']}")
    print("=" * 68)
    return 0


def run_universe(export: bool = True, show: int = 12,
                 out_dir: Optional[Path] = None) -> int:
    uni = keyword_universe()
    st = universe_stats(uni)
    print("=" * 68)
    print(f"  🌐 KEYWORD UNIVERSE — {st['total']} keywords")
    print(f"     {st['entities']} entities × {st['intents']} intents "
          f"({st['core_intents']} core + {st['longtail_intents']} long-tail)")
    print("=" * 68)
    print(f"  Hot intents : {st['hot']} keywords")
    print(f"  Pillars     : {st['pillars']} · Clusters: {st['clusters']} · "
          f"Avg priority: {st['avg_priority']}")
    print(f"  Funnel      : {st['by_funnel']}")
    print("\n  Category breakdown:")
    for cat, n in list(st["by_category"].items())[:10]:
        print(f"    {cat:<22} {n}")
    print("\n  Top priority keywords:")
    for e in uni[:show]:
        print(f"    {e['priority']:>3}  {e['kw'][:50]:<50} [{e['intent']}/{e['funnel']}]")
    if export:
        paths = write_universe(out_dir)
        print(f"\n  EXPORT: {paths['csv']}\n          {paths['json']}")
        print(f"          ({paths['count']} rows — Excel/Sheets lo open cheyochu)")
    print(f"\n  ℹ️  {st['note']}")
    print("=" * 68)
    return 0


def run_score_file(path: str, keyword: str = "") -> int:
    fp = Path(path)
    if not fp.exists():
        print(f"❌ File dorakaledu: {path}")
        return 1
    raw = fp.read_text(encoding="utf-8", errors="ignore")
    title = ""
    m = re.search(r"<title[^>]*>(.*?)</title>", raw, flags=re.S | re.I)
    if m:
        title = validator.strip_tags(m.group(1)).strip()
    article = {"title": title, "content_html": raw, "focus_keyword": keyword,
               "meta_description": "", "slug": "", "faq": [],
               "quick_answer": ""}
    report = score_top_post(article, keyword)
    print("=" * 68)
    print(f"  📊 TOP POST SCORE — {path}")
    print(f"     keyword: {keyword or article['focus_keyword'] or '(none)'}")
    print("=" * 68)
    print(f"  SCORE : {report['score']}/100   {report['grade']}")
    print(f"  Words : {report['words']} · density {report['density']:.2%} "
          f"({report['occurrences']} mentions) · secondary hits {report['secondary_hits']} · "
          f"long-tail {report['longtail_hits']} · questions {report['question_hits']}")
    print(f"  Links : internal {report['internal_links']} · external {report['external_links']}")
    print("\n  CHECKS:")
    for c in report["checks"]:
        print(f"    {'✔' if c['ok'] else '✘'} [{c['weight']:>2}] {c['label']}"
              + (f"  → {c['fix']}" if not c["ok"] and c["fix"] else ""))
    print("=" * 68)
    return 0


def create_top_post(keyword: str, mock: bool = False, dry_run: bool = False,
                    category: str = "") -> dict:
    """Blueprint → article → (draft/publish). pipeline vadutundi."""
    from . import gemini_client, pipeline, seo as _seo
    from .main import _safe_slug

    bp = build_blueprint(keyword, category=category)
    if mock:
        article = mock_article(bp)
    else:
        article = gemini_client.generate_top_post(bp, date.today().year)
    article["focus_keyword"] = article.get("focus_keyword") or bp["keyword"]
    article["slug"] = _seo.optimize_slug(
        _safe_slug(article.get("slug", ""), article["title"]), focus_keyword=bp["keyword"])
    article.setdefault("category", bp["category"])
    if article["category"] not in LIVE_CATEGORIES:
        article["category"] = bp["category"]
    article.setdefault("secondary_keywords", bp["keyword_family"]["secondary"][:5])
    article.setdefault("quick_answer", bp["snippet_answer"])
    article.setdefault("external_links", [])
    article.setdefault("faq", [])
    article.setdefault("seo_title", "")
    article["_blueprint"] = {"keyword": bp["keyword"], "intent": bp["intent"],
                             "family": bp["intent_family"],
                             "plan_score": bp["score_preview"]["score"]}
    if dry_run:
        out = Path(config.OUTPUT_DIR) / "top-posts"
        out.mkdir(parents=True, exist_ok=True)
        fp = out / f"{article['slug']}.draft.html"
        fp.write_text("<!doctype html><html><head><meta charset='utf-8'>"
                      f"<title>{article['title']}</title></head><body>"
                      f"<h1>{article['title']}</h1>{article['content_html']}</body></html>",
                      encoding="utf-8")
        log.info("TOP-POST DRY-RUN saved: %s (WordPress touch cheyaledu)", fp)
        return {"id": 0, "status": "dry-run", "link": str(fp)}
    return pipeline.publish_article(article)
