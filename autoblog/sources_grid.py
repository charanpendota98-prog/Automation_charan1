"""v58/v96: Official Sources Grid — 180 curated sources, ZERO misses.

Official first (SSC/UPSC/TSPSC/APPSC/NEET...), private+software+walkins next.
Prathi source = Google News query. 17 daily hot-list sources prathi radar
run lo check (4x/day); bavita rotation lo (RADAR_SOURCES_PER_run/run). Kotha
edu-relevant items → sources_queue.txt (news_radar._queue_url).
"""

import logging

from . import config, news_radar, state

log = logging.getLogger("autoblog.grid")

# ---------------------------------------------------------------- sources
# (name, google-news query, category hint, daily hot-list)
# categories = LIVE site categories matrame (v14 rule — duplicate raavu)

_S = [
    # ---- Central: exams, banks, insurance, employment news ----
    ("SSC", "SSC notification 2026", "Central Govt Jobs", True),
    ("SSC CGL", "SSC CGL 2026", "Central Govt Jobs", False),
    ("SSC CHSL MTS", "SSC CHSL MTS 2026", "Central Govt Jobs", False),
    ("SSC GD Constable", "SSC GD constable 2026", "Central Govt Jobs", False),
    ("UPSC", "UPSC notification 2026", "Central Govt Jobs", True),
    ("UPSC CSE Prelims", "UPSC prelims 2026", "Central Govt Jobs", False),
    ("RRB Railways", "RRB railway recruitment 2026", "Central Govt Jobs", True),
    ("IBPS", "IBPS PO clerk 2026", "Central Govt Jobs", True),
    ("SBI Careers", "SBI PO clerk recruitment 2026", "Central Govt Jobs", True),
    ("LIC", "LIC recruitment 2026", "Central Govt Jobs", True),
    ("RBI", "RBI Grade B recruitment 2026", "Central Govt Jobs", False),
    ("NABARD", "NABARD recruitment 2026", "Central Govt Jobs", False),
    ("India Post GDS", "India Post GDS 2026", "Central Govt Jobs", False),
    ("Employment News", "Employment News this week", "Central Govt Jobs", False),
    # ---- Defence ----
    ("Indian Army Agniveer", "Agniveer army rally 2026", "Central Govt Jobs", False),
    ("Indian Navy", "Indian Navy recruitment 2026", "Central Govt Jobs", False),
    ("Indian Air Force", "Indian Air Force Agniveer 2026", "Central Govt Jobs", False),
    ("Indian Coast Guard", "Coast Guard recruitment 2026", "Central Govt Jobs", False),
    ("CRPF BSF Paramilitary", "CRPF BSF CISF recruitment 2026", "Central Govt Jobs", False),
    # ---- PSU ----
    ("NTPC", "NTPC recruitment 2026", "Central Govt Jobs", False),
    ("ONGC", "ONGC recruitment 2026", "Central Govt Jobs", False),
    ("IOCL", "IOCL recruitment 2026", "Central Govt Jobs", False),
    ("BHEL", "BHEL recruitment 2026", "Central Govt Jobs", False),
    ("Coal India", "Coal India recruitment 2026", "Central Govt Jobs", False),
    ("FCI", "FCI recruitment 2026", "Central Govt Jobs", False),
    ("ISRO", "ISRO recruitment 2026", "Central Govt Jobs", False),
    ("DRDO", "DRDO recruitment 2026", "Central Govt Jobs", False),
    # ---- Medical / health ----
    ("NEET UG", "NEET 2026", "Online Education", True),
    ("NEET Counselling", "NEET UG counselling 2026", "Online Education", False),
    ("AIIMS", "AIIMS recruitment 2026", "Central Govt Jobs", False),
    ("AIIMS Nursing", "AIIMS nursing officer 2026", "Central Govt Jobs", False),
    ("JIPMER", "JIPMER recruitment 2026", "Central Govt Jobs", False),
    ("NIMHANS", "NIMHANS recruitment 2026", "Central Govt Jobs", False),
    ("NHM Medical Officer", "NHM medical officer recruitment", "Central Govt Jobs", False),
    # ---- Central admissions/exams ----
    ("JEE Main", "JEE Main 2026", "Online Education", False),
    ("CUET UG", "CUET UG 2026", "Online Education", False),
    ("NTA Exams", "NTA exam 2026", "Hall Tickets", False),
    ("AICTE", "AICTE 2026", "Scholarships", False),
    # ---- Telangana ----
    ("TSPSC", "TSPSC notification 2026", "TS Govt Jobs", True),
    ("TGPSC Gurukul", "TGPSC Gurukul teacher recruitment", "TS Govt Jobs", True),
    ("Telangana DSC Teachers", "Telangana DSC teacher recruitment 2026", "TS Govt Jobs", False),
    ("TGRTC", "TGRTC Telangana RTC recruitment 2026", "TS Govt Jobs", True),
    ("TS EAMCET", "TS EAMCET 2026", "Online Education", False),
    ("TS Polycet", "Telangana Polytechnic admission 2026", "Online Education", False),
    ("DOST Telangana", "DOST Telangana counselling 2026", "Online Education", False),
    ("Telangana ePASS", "Telangana ePASS scholarship", "Scholarships", False),
    ("BIE Telangana Inter", "Telangana intermediate results 2026", "Results", False),
    ("TS SSC Board", "Telangana SSC results 2026", "Results", False),
    ("Osmania University", "Osmania University 2026", "Online Education", False),
    ("JNTUH", "JNTU Hyderabad results 2026", "Results", False),
    ("Kaloji Health University", "Kaloji Health University 2026", "Online Education", False),
    ("TSSPDCL", "TSSPDCL TGSPDCL recruitment", "TS Govt Jobs", False),
    ("HMWSSB", "HMWSSB recruitment", "TS Govt Jobs", False),
    ("Telangana Police", "Telangana police SI constable 2026", "TS Govt Jobs", False),
    ("Singareni Coal", "Singareni Collieries recruitment", "TS Govt Jobs", False),
    ("TS LAWCET PGETCET", "TS LAWCET PGETCET 2026", "Online Education", False),
    ("Telangana Forest", "Telangana forest recruitment", "TS Govt Jobs", False),
    ("Telangana Universities", "Telangana university recruitment 2026", "TS Govt Jobs", False),
    # ---- Andhra Pradesh ----
    ("APPSC", "APPSC notification 2026", "AP Govt Jobs", True),
    ("AP DSC Teachers", "AP DSC school teacher 2026", "AP Govt Jobs", True),
    ("APSRTC", "APSRTC recruitment 2026", "AP Govt Jobs", True),
    ("AP EAPCET", "AP EAPCET 2026", "Online Education", False),
    ("AP Polycet", "Andhra Polytechnic admission 2026", "Online Education", False),
    ("DOST Andhra", "AP DOST counselling 2026", "Online Education", False),
    ("Jnanabhumi AP", "Jnanabhumi scholarship 2026", "Scholarships", False),
    ("BIE AP Inter", "AP intermediate results 2026", "Results", False),
    ("AP SSC Board", "AP SSC results 2026", "Results", False),
    ("AP ePASS", "AP ePASS scholarship", "Scholarships", False),
    ("AP Police", "AP police SI constable 2026", "AP Govt Jobs", False),
    ("Dr NTR Health University", "NTR Health University 2026", "Online Education", False),
    ("AP DISCOMs", "APSPDCL APEPDCL recruitment", "AP Govt Jobs", False),
    ("Grama Sachivalayam AP", "AP grama sachivalayam ward secretary", "AP Govt Jobs", False),
    ("AP Forest", "AP forest department recruitment", "AP Govt Jobs", False),
    ("AP Universities", "Andhra University SV University recruitment", "AP Govt Jobs", False),
    ("AP ICET LAWCET", "AP ICET LAWCET 2026", "Online Education", False),
    # ---- Scholarships ----
    ("NSP Scholarship", "NSP scholarship apply 2026", "Scholarships", True),
    ("PM YASASVI", "PM YASASVI scholarship 2026", "Scholarships", False),
    ("AICTE Pragati Saksham", "AICTE Pragati Saksham 2026", "Scholarships", False),
    ("PM Internship", "PM Internship scheme 2026", "Internships", False),
    # ---- Telugu/private job publishers (discovery only; official notice wins) ----
    ("Adda247 Telugu Jobs", "site:adda247.com/te jobs notification Telugu", "Central Govt Jobs", True),
    ("Eenadu Pratibha Jobs", "site:pratibha.eenadu.net government jobs notification", "Central Govt Jobs", True),
    ("Sakshi Education Jobs", "site:education.sakshi.com jobs notification", "Central Govt Jobs", True),
    ("Job Updates Telugu", "site:jobupdatestelugu.com latest jobs", "Central Govt Jobs", True),
    ("Telugu Careers", "site:telugucareers.in jobs notification", "Central Govt Jobs", True),
    ("Telugu Jobs Point", "site:telugujobspoint.com jobs notification", "AP Govt Jobs", True),
    ("NaaJob AP TS", "site:naajob.com AP TS jobs", "Private Jobs", True),
    ("TS IndGovtJobs", "site:telangana.indgovtjobs.net jobs", "TS Govt Jobs", False),
    ("AP IndGovtJobs", "site:ap.indgovtjobs.net jobs", "AP Govt Jobs", False),
    ("TeacherNews", "site:teachernews.in teacher recruitment AP Telangana", "Online Education", False),
    ("Schools360", "site:schools360.in jobs results hall tickets", "Online Education", False),
    ("Manabadi", "site:manabadi.co.in results hall tickets notification", "Results", False),
    ("Vidyavision", "site:vidyavision.com results admissions jobs", "Online Education", False),
    # ---- National job publishers / aggregators (secondary evidence only) ----
    ("FreeJobAlert", "site:freejobalert.com latest government jobs 2026", "Central Govt Jobs", True),
    ("FreshersNow", "site:freshersnow.com government jobs AP Telangana", "Central Govt Jobs", False),
    ("Testbook Jobs", "site:testbook.com government jobs notification", "Central Govt Jobs", False),
    ("CareerPower Jobs", "site:careerpower.in government jobs notification", "Central Govt Jobs", False),
    ("JagranJosh Jobs", "site:jagranjosh.com government jobs recruitment", "Central Govt Jobs", False),
    ("GovtJobGuru", "site:govtjobguru.in recruitment notification", "Central Govt Jobs", False),
    ("Sarkari Result", "site:sarkariresult.com latest jobs", "Central Govt Jobs", False),
    ("FreshersLive", "site:fresherslive.com government jobs recruitment", "Central Govt Jobs", False),
    ("Naukri Freshers", "site:naukri.com fresher jobs Hyderabad Andhra Telangana", "Private Jobs", False),
    ("Foundit Jobs", "site:foundit.in fresher jobs Hyderabad", "Private Jobs", False),
    ("Indeed India Jobs", "site:in.indeed.com jobs Hyderabad Vijayawada freshers", "Private Jobs", False),
    ("Jobs.com Listings", "site:jobs.com India jobs freshers", "Private Jobs", False),
    # ---- Private / software ----
    ("TCS NQT", "TCS NQT 2026", "Private Jobs", True),
    ("Infosys", "Infosys fresher hiring 2026", "Software Jobs", False),
    ("Wipro", "Wipro hiring 2026", "Software Jobs", False),
    ("Accenture", "Accenture hiring 2026", "Software Jobs", False),
    ("Cognizant", "Cognizant hiring 2026", "Software Jobs", False),
    ("Capgemini", "Capgemini hiring 2026", "Software Jobs", False),
    ("HCLTech", "HCL Tech hiring 2026", "Software Jobs", False),
    ("Tech Mahindra", "Tech Mahindra hiring 2026", "Software Jobs", False),
    ("Amazon India", "Amazon jobs India 2026", "Software Jobs", False),
    ("Deloitte", "Deloitte hiring India 2026", "Software Jobs", False),
    ("Google Careers", "Google jobs India 2026", "Software Jobs", False),
    ("Microsoft Careers", "Microsoft hiring India 2026", "Software Jobs", False),
    ("Zoho Careers", "Zoho careers 2026", "Software Jobs", False),
    ("Software Jobs Hyderabad", "software jobs Hyderabad 2026", "Software Jobs", True),
    ("IT Jobs Freshers", "IT jobs freshers 2026", "Software Jobs", False),
    ("Work From Home Jobs", "work from home jobs India", "Part Time Jobs", False),
    ("Data Entry Jobs", "data entry work from home 2026", "Part Time Jobs", False),
    # ---- Walkins ----
    ("Walkins Hyderabad", "walkin interview Hyderabad", "Walkin Jobs", True),
    ("Walkins Vijayawada", "walkin interview Vijayawada", "Walkin Jobs", False),
    ("Walkins Vizag", "walkin interview Visakhapatnam", "Walkin Jobs", False),
    ("Walkins Bengaluru", "walkin interview Bangalore", "Walkin Jobs", False),
    ("Walkins Chennai", "walkin interview Chennai", "Walkin Jobs", False),
    # ---- Internships ----
    ("Internshala", "Internshala internship 2026", "Internships", False),
    ("AICTE Internship", "AICTE internship scheme 2026", "Internships", False),
    ("NATS Apprenticeship", "apprenticeship NATS India 2026", "Internships", False),
    ("Graduate Trainee Jobs", "graduate trainee recruitment 2026", "Central Govt Jobs", False),
    # --- v50: outsourcing / contract recruitment (TS + AP) ---
    ("TS Outsourcing Recruitment", "Telangana outsourcing recruitment 2026", "Outsourcing Jobs", True),
    ("TGSPDCL TSSPDCL Outsourcing", "TSSPDCL TGSPDCL outsourcing jobs 2026", "Outsourcing Jobs", False),
    ("TS GENCO Outsourcing", "TSGENCO TRANSCO outsourcing recruitment 2026", "Outsourcing Jobs", False),
    ("TS Medical & Health Outsourcing", "Telangana health department outsourcing 2026", "Outsourcing Jobs", False),
    ("AP Outsourcing Recruitment", "Andhra Pradesh outsourcing recruitment 2026", "Outsourcing Jobs", True),
    ("APSPDCL Outsourcing", "APSPDCL outsourcing jobs 2026", "Outsourcing Jobs", False),
    ("AP Village & Ward Secretariat", "AP ward secretariat contract recruitment 2026", "Outsourcing Jobs", False),
    ("Guest Faculty Recruitment", "guest faculty recruitment Telangana Andhra 2026", "Outsourcing Jobs", False),
    # --- v50: current affairs from official releases ---
    ("PIB Press Releases", "PIB press release education scheme", "Current Affairs", True),
    ("PIB Telugu Region", "PIB Telangana Andhra development scheme", "Current Affairs", False),
    ("Ministry of Education", "Ministry of Education announcement 2026", "Current Affairs", False),
    ("Telangana Govt Orders", "Telangana government order education 2026", "Current Affairs", False),
    ("AP Govt Orders", "Andhra Pradesh government order education 2026", "Current Affairs", False),
    ("NITI Aayog & Schemes", "central scheme students scholarship announcement", "Current Affairs", False),
    # --- v50: exam calendar / upcoming exams ---
    ("TSPSC Calendar", "TSPSC upcoming exams calendar 2026", "Upcoming Exams", True),
    ("APPSC Calendar", "APPSC upcoming exams schedule 2026", "Upcoming Exams", True),
    ("SSC Exam Calendar", "SSC exam calendar 2026 2027", "Upcoming Exams", False),
    ("RRB Exam Calendar", "RRB exam calendar 2026", "Upcoming Exams", False),
    ("NTA Exam Calendar", "NTA exam calendar 2026", "Upcoming Exams", False),
    ("State Board Exam Schedule", "Telangana Andhra board exam schedule 2026", "Upcoming Exams", False),
    # --- v50: exam preparation guidance ---
    ("TSPSC Preparation", "TSPSC exam preparation plan syllabus", "Exam Tips", False),
    ("APPSC Preparation", "APPSC group 2 preparation strategy syllabus", "Exam Tips", False),
    ("SSC Preparation", "SSC exam preparation strategy previous papers", "Exam Tips", False),
    ("Board Exam Prep", "10th inter board exam preparation tips 2026", "Exam Tips", False),
    # --- v58: విదేశీ ఉద్యోగాలు (Abroad/Gulf/NRI) — Tier-1 + high-CPC pillar ---
    ("eMigrate MEA", "eMigrate overseas job emigration India notification", "Abroad Jobs", True),
    ("MEA Emigration", "Ministry of External Affairs emigration update Indians", "Abroad Jobs", False),
    ("Gulf Jobs News", "Gulf jobs for Indians vacancy recruitment 2026", "Abroad Jobs", True),
    ("UAE Jobs", "UAE Dubai Abu Dhabi jobs for Indians 2026", "Abroad Jobs", False),
    ("Saudi Qatar Jobs", "Saudi Arabia Qatar jobs Indian workers recruitment", "Abroad Jobs", False),
    ("Kuwait Oman Bahrain Jobs", "Kuwait Oman Bahrain jobs for Indians 2026", "Abroad Jobs", False),
    ("IELTS Test Update", "IELTS PTE TOEFL test date fee change 2026", "Abroad Jobs", True),
    ("Study Abroad", "study abroad for Indian students intake scholarship 2026", "Abroad Jobs", True),
    ("Canada Visa", "Canada express entry study permit updates Indian students", "Abroad Jobs", False),
    ("UK Australia Visa", "UK skilled worker Australia student visa update 2026", "Abroad Jobs", False),
    ("Germany Japan Korea", "Germany opportunity card Japan Korea care work visa India", "Abroad Jobs", False),
    ("Passport Visa Update", "passport visa appointment rules update India 2026", "Abroad Jobs", False),
    ("NRI Guidance", "NRI students Telugu workers abroad guidance news", "Abroad Jobs", False),
    ("Overseas Scholarship", "overseas scholarship fellowship for Indian students 2026", "Abroad Jobs", False),
    # ======================================================================
    # v96 — MISS-ZERO EXPANSION (37 kotha sources → 180)
    # Brief: "em em posts vasthunnai … job melas … every district pages jobs
    # … university results … daily current affairs" — ee axes ippati varaku
    # grid lo LEVU (radar districts generic news matrame teesedhi).
    # ======================================================================
    # ---- Job melas / mega drives (district + city level) ----
    ("Job Mela Telangana", "job mela Telangana 2026 registration", "Walkin Jobs", True),
    ("Job Mela Andhra Pradesh", "job mela Andhra Pradesh 2026 registration", "Walkin Jobs", True),
    ("Job Mela Hyderabad", "job mela Hyderabad mega job fair", "Walkin Jobs", False),
    ("Job Mela Vijayawada Guntur", "job mela Vijayawada Guntur job fair", "Walkin Jobs", False),
    ("Job Mela Visakhapatnam", "job mela Visakhapatnam job fair", "Walkin Jobs", False),
    ("Job Mela Warangal Karimnagar", "job mela Warangal Karimnagar job fair", "Walkin Jobs", False),
    ("Job Mela Tirupati Nellore", "job mela Tirupati Nellore job fair", "Walkin Jobs", False),
    ("District Employment Job Fair", "district employment exchange job fair Telangana Andhra", "Walkin Jobs", False),
    # ---- Local / district-level jobs ("prathi district page" demand) ----
    ("TS District Jobs", "Telangana district level recruitment notification 2026", "TS Govt Jobs", True),
    ("AP District Jobs", "Andhra Pradesh district level recruitment notification 2026", "AP Govt Jobs", True),
    ("TS Collectorate Jobs", "Telangana collectorate district office recruitment", "Outsourcing Jobs", False),
    ("AP Collectorate Jobs", "Andhra Pradesh collectorate district office recruitment", "Outsourcing Jobs", False),
    ("Anganwadi Recruitment", "anganwadi teacher ayah recruitment Telangana Andhra 2026", "Outsourcing Jobs", False),
    ("ASHA & Health Worker", "ASHA worker ANM staff nurse recruitment Telangana Andhra", "Outsourcing Jobs", False),
    ("Municipal & Panchayat Jobs", "municipal corporation panchayat recruitment Telangana Andhra", "Outsourcing Jobs", False),
    ("Cooperative Bank Jobs", "DCCB cooperative bank recruitment Telangana Andhra 2026", "AP Govt Jobs", False),
    # ---- University results + admissions (TS + AP) ----
    ("JNTUH Results", "JNTUH B.Tech results 2026 revaluation", "Results", True),
    ("JNTUK Results", "JNTUK B.Tech results 2026 revaluation", "Results", True),
    ("JNTUA Results", "JNTUA B.Tech results 2026 revaluation", "Results", False),
    ("Osmania University Results", "Osmania University degree results 2026", "Results", False),
    ("Kakatiya University Results", "Kakatiya University degree results 2026", "Results", False),
    ("Andhra University Results", "Andhra University degree results 2026", "Results", False),
    ("SV University Results", "Sri Venkateswara University results 2026", "Results", False),
    ("Krishna & ANU Results", "Acharya Nagarjuna Krishna University results 2026", "Results", False),
    ("Palamuru & Satavahana", "Palamuru Satavahana University results 2026", "Results", False),
    ("TS Open University", "Dr BR Ambedkar Open University Telangana results admission", "Online Education", False),
    ("AP Open University", "Dr BR Ambedkar Open University AP results admission", "Online Education", False),
    ("Degree Admissions DOST OAMDC", "DOST OAMDC degree admission 2026 web options", "Online Education", False),
    # ---- Hall tickets (dedicated axis) ----
    ("TS Hall Tickets", "Telangana hall ticket download 2026", "Hall Tickets", True),
    ("AP Hall Tickets", "Andhra Pradesh hall ticket download 2026", "Hall Tickets", True),
    ("University Hall Tickets", "university exam hall ticket download 2026 Telangana Andhra", "Hall Tickets", False),
    # ---- Verified achiever stories (identity/result must be source-backed) ----
    ("UPSC Verified Achievers", "UPSC final result topper interview official 2026", "Success Stories", False),
    ("SSC Verified Achievers", "SSC final result selected candidate official interview", "Success Stories", False),
    ("TS AP Exam Achievers", "Telangana Andhra exam topper interview official university", "Success Stories", False),
    ("PIB Youth Achievers", "site:pib.gov.in youth achiever competitive exam interview", "Success Stories", False),
    # ---- Daily current affairs (roju students ki) ----
    ("Daily Current Affairs Telugu", "daily current affairs Telugu today competitive exams", "Current Affairs", True),
    ("Telangana Current Affairs", "Telangana current affairs today scheme GO", "Current Affairs", False),
    ("AP Current Affairs", "Andhra Pradesh current affairs today scheme GO", "Current Affairs", False),
    ("Budget & Student Schemes", "union budget state budget student scheme allocation 2026", "Current Affairs", False),
    # ---- Private / BPO local hiring ----
    ("BPO Voice Process Jobs", "BPO voice process hiring Hyderabad Vijayawada freshers", "Private Jobs", False),
    ("Retail & Field Jobs", "retail field sales executive hiring Telangana Andhra freshers", "Private Jobs", False),
]

SOURCES_GRID = [
    {"name": n, "q": q, "cat": c, **({"daily": True} if d else {})}
    for n, q, c, d in _S
]


def radar_sources(per_run: int = None) -> list:
    """Ee run ki check avalsina sources: daily hot-list + rotation batch.

    Fetch → edu filter → queue (news_radar._queue_url). Newly-queued items
    return avuthayi ({title, link, source_name, category_hint}).
    """
    per_run = per_run or config.RADAR_SOURCES_PER_RUN
    daily = [s for s in SOURCES_GRID if s.get("daily")]
    rotating = [s for s in SOURCES_GRID if not s.get("daily")]
    try:
        last = int(state.meta_get(config.STATE_PATH, "grid:last_idx") or -1)
    except (TypeError, ValueError):
        last = -1
    start = (last + 1) % max(1, len(rotating))
    take = min(per_run, len(rotating))
    batch = list(daily) + [rotating[(start + i) % len(rotating)] for i in range(take)]
    try:
        state.meta_set(config.STATE_PATH, "grid:last_idx", str((start + take - 1) % len(rotating)))
    except Exception as exc:  # noqa: BLE001 — best-effort (silent kaadu)
        log.debug("sources_grid.radar_sources skip: %s", exc)
    new_items = []
    for s in batch:
        try:
            items = news_radar.fetch_google_news(s["q"])
        except Exception as exc:
            log.debug("grid fetch fail (%s): %s", s["name"], exc)
            continue
        for it in items:
            if not news_radar._edu_relevant(it["title"]):
                continue
            if news_radar._queue_url(it["link"], title=it["title"]):
                new_items.append({"title": it["title"], "link": it["link"],
                                  "source_name": s["name"],
                                  "category_hint": s["cat"]})
    log.info("GRID: %d sources checked (daily %d + rotation %d) — %d new queued",
             len(batch), len(daily), take, len(new_items))
    return new_items
