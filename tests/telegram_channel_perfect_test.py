"""Unit & integration tests for Telegram channel post formatting,
category classification accuracy, and image banner pill badge protection.
"""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from autoblog import config, image_gen, notifier, pipeline


def test_category_classification_accuracy():
    # 1. Software jobs (Telugu + English + MNCs)
    cases_software = [
        ("Infor Recruitment 2026: సాఫ్ట్‌వేర్ ఇంజనీర్ — Best Guide", "Software Jobs"),
        ("Infor Software Engineer Hiring 2026", "Software Jobs"),
        ("TCS Software Developer Recruitment 2026", "Software Jobs"),
        ("Wipro Full Stack Developer Jobs", "Software Jobs"),
        ("హైదరాబాద్‌లో సాఫ్ట్‌వేర్ ఇంజనీర్ ఉద్యోగాలు 2026", "Software Jobs"),
        ("సాఫ్ట్‌వేర్ డెవలపర్ నోటిఫికేషన్ 2026", "Software Jobs"),
    ]
    for title, expected in cases_software:
        got = pipeline.classify_category(title)
        assert got == expected, f"Failed for {title}: expected {expected}, got {got}"

    # 2. Private jobs (non-software MNCs / private hiring)
    cases_private = [
        ("Deloitte Associate Analyst Hiring 2026", "Private Jobs"),
        ("ప్రైవేట్ కంపెనీ రిక్రూట్‌మెంట్ 2026", "Private Jobs"),
    ]
    for title, expected in cases_private:
        got = pipeline.classify_category(title)
        assert got == expected, f"Failed for {title}: expected {expected}, got {got}"

    # 3. Government jobs
    assert pipeline.classify_category("SSC CGL 2026 Notification") == "Central Govt Jobs"
    assert pipeline.classify_category("TSPSC Group 2 Notification 2026") == "TS Govt Jobs"
    assert pipeline.classify_category("APPSC Group 1 Notification 2026") == "AP Govt Jobs"
    assert pipeline.classify_category("NSP Central Sector Scholarship 2026") == "Scholarships"


def test_clean_title_text():
    cases = [
        ("Infor Recruitment 2026: సాఫ్ట్‌వేర్ ఇంజనీర్ — Best Guide",
         "Infor Recruitment 2026: సాఫ్ట్‌వేర్ ఇంజనీర్"),
        ("TCS NQT 2026 Registration – Complete Guide",
         "TCS NQT 2026 Registration"),
        ("APPSC Group 2 Notification 2026: A to Z Guide",
         "APPSC Group 2 Notification 2026:"),
        ("Wipro Elite National Talent Hunt - Ultimate Guide",
         "Wipro Elite National Talent Hunt"),
    ]
    for raw, expected in cases:
        got = pipeline.clean_title_text(raw)
        assert got == expected, f"Expected {expected}, got {got}"


def test_image_pill_label_guard():
    # Software jobs must NEVER receive GOVT JOBS badge even if cat is passed as Central Govt Jobs
    assert image_gen._pill_label("Central Govt Jobs", "Infor Software Engineer Jobs 2026") == "SOFTWARE JOBS"
    assert image_gen._pill_label("Central Govt Jobs", "సాఫ్ట్‌వేర్ ఇంజనీర్ ఉద్యోగాలు") == "SOFTWARE JOBS"
    assert image_gen._pill_label("Central Govt Jobs", "TCS Developer Hiring 2026") == "SOFTWARE JOBS"

    # Private jobs must NEVER receive GOVT JOBS badge
    assert image_gen._pill_label("Central Govt Jobs", "Deloitte Off Campus Hiring 2026") == "PRIVATE JOBS"

    # Genuine Govt jobs retain GOVT JOBS badge
    assert image_gen._pill_label("Central Govt Jobs", "SSC CGL Recruitment 2026") == "GOVT JOBS"
    assert image_gen._pill_label("TS Govt Jobs", "TSPSC Group 1 Notification") == "TS GOVT JOBS"
    assert image_gen._pill_label("AP Govt Jobs", "APPSC Group 2 Notification") == "AP GOVT JOBS"


def test_extract_article_from_snapshot():
    snapshot = {
        "title": {"rendered": "Infor Recruitment 2026: సాఫ్ట్‌వేర్ ఇంజనీర్ — Best Guide"},
        "excerpt": {"rendered": "<p>Infor Recruitment 2026 ద్వారా సాఫ్ట్‌వేర్ ఇంజనీర్ ఉద్యోగాలకు దరఖాస్తులు ప్రారంభమయ్యాయి.</p>"},
        "link": "https://studentup.in/infor-recruitment-2026-software-engineer-jobs-2/",
        "content": {
            "rendered": """
            <p>Job description and overview.</p>
            <script type="application/ld+json">
            {
                "@context": "https://schema.org",
                "@type": "JobPosting",
                "title": "Software Engineer",
                "hiringOrganization": {"@type": "Organization", "name": "Infor"},
                "jobLocation": {"@type": "Place", "address": {"@type": "PostalAddress", "addressLocality": "Hyderabad"}},
                "validThrough": "2026-10-31",
                "baseSalary": {"@type": "MonetaryAmount", "value": {"minValue": 500000, "maxValue": 800000}}
            }
            </script>
            <table>
                <tr><td>అర్హత</td><td>B.E / B.Tech / MCA</td></tr>
                <tr><td>ఖాళీలు</td><td>150 పోస్టులు</td></tr>
            </table>
            """
        }
    }

    art = notifier.extract_article_from_snapshot(snapshot)
    assert art["title"] == "Infor Recruitment 2026: సాఫ్ట్‌వేర్ ఇంజనీర్"
    assert art["category"] == "Software Jobs"
    assert art["recruitment"]["org_name"] == "Infor"
    assert art["recruitment"]["role"] == "Software Engineer"
    assert art["recruitment"]["location"] == "Hyderabad"
    assert art["recruitment"]["salary"] == "₹500,000 – ₹800,000"
    assert art["recruitment"]["qualification"] == "B.E / B.Tech / MCA"
    assert art["recruitment"]["vacancies"] == "150 పోస్టులు"
    assert art["recruitment"]["apply_end"] == "2026-10-31"


def test_channel_caption_and_post():
    art = {
        "title": "Infor Recruitment 2026: సాఫ్ట్‌వేర్ ఇంజనీర్ — Best Guide",
        "category": "Software Jobs",
        "meta_description": "Infor లో సాఫ్ట్‌వేర్ ఇంజనీర్ ఉద్యోగాలు. ఫ్రెషర్స్ దరఖాస్తు చేసుకోవచ్చు.",
        "recruitment": {
            "org_name": "Infor",
            "role": "Software Engineer",
            "qualification": "B.Tech / MCA",
            "vacancies": "100+",
            "location": "Hyderabad",
            "salary": "₹5,00,000 – ₹8,00,000",
            "apply_end": "2026-10-31",
        }
    }
    res = {"link": "https://studentup.in/infor-jobs/", "status": "publish", "id": 789}

    caption = notifier.channel_caption(art, res)
    assert "💻 <b>Infor Recruitment 2026: సాఫ్ట్‌వేర్ ఇంజనీర్</b>" in caption
    assert "— Best Guide" not in caption
    assert "🏢 <b>సంస్థ (Org):</b> Infor" in caption
    assert "💼 <b>ఉద్యోగం (Role):</b> Software Engineer" in caption
    assert "👉 <b>ఖాళీలు (Vacancies):</b> 100+" in caption
    assert "👉 <b>అర్హత (Eligibility):</b> B.Tech / MCA" in caption
    assert "📍 <b>జాబ్ లొకేషన్:</b> Hyderabad" in caption
    assert "💰 <b>వేతనం (Salary):</b> ₹5,00,000 – ₹8,00,000" in caption
    assert "31 Oct 2026" in caption
    assert "https://studentup.in/infor-jobs/" in caption

    # Test broadcast buttons
    sent = []
    notifier.send_telegram = lambda text, chat_id=None, buttons=None: sent.append(("TEXT", text, chat_id, buttons)) or True
    notifier.send_telegram_photo = lambda photo, caption, chat_id=None, buttons=None: sent.append(("PHOTO", photo, caption, buttons)) or True

    config.TELEGRAM_CHANNEL_CHAT_ID = "-100pub"
    ok = notifier.channel_post(art, res)
    assert ok is True
    assert len(sent) == 1
    # text or photo
    buttons = sent[0][3] if sent[0][0] == "TEXT" else sent[0][3]
    assert buttons["inline_keyboard"][0][0]["text"] == "🌐 పూర్తి వివరాలు & Apply Online"
    assert buttons["inline_keyboard"][0][0]["url"] == "https://studentup.in/infor-jobs/"
    assert buttons["inline_keyboard"][1][0]["text"] == "📲 Friends కి షేర్ చేయండి ↗️"


if __name__ == "__main__":
    test_category_classification_accuracy()
    test_clean_title_text()
    test_image_pill_label_guard()
    test_extract_article_from_snapshot()
    test_channel_caption_and_post()
    print("ALL TELEGRAM CHANNEL PERFECT TESTS PASSED ✔")
