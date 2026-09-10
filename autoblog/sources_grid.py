"""v16.1: Official Sources Grid — 100+ curated sources, ZERO misses.

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
    except Exception:
        pass
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
            if news_radar._queue_url(it["link"]):
                new_items.append({"title": it["title"], "link": it["link"],
                                  "source_name": s["name"],
                                  "category_hint": s["cat"]})
    log.info("GRID: %d sources checked (daily %d + rotation %d) — %d new queued",
             len(batch), len(daily), take, len(new_items))
    return new_items
