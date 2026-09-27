# StudentUp theme — MilesWeb + WordPress setup (Telugu / Tinglish)

Theme version: **1.9.19** · zip: `wordpress-theme/studentup-theme.zip`

---

## 1. Zip upload (5 nimishalu)

1. MilesWeb cPanel → **WordPress admin** login (`https://studentup.in/wp-admin`).
2. **Appearance → Themes → Add New → Upload Theme**.
3. `studentup-theme.zip` select cheyandi → **Install Now** → **Activate**.

Activate ayina venteney theme **one-click setup** run avutundi:

| Em jarugutundi | Detail |
|---|---|
| Categories create | ts-jobs, ap-jobs, central-jobs, private-jobs, walkin-jobs, software-jobs, results, hall-ticket, admissions, **scholarships**, internships, current-affairs, success-stories |
| Policy pages create | About, Contact, Privacy Policy, Disclaimer, Terms, Editorial Policy (AdSense ki compulsory) |
| Menus build | "StudentUp Main" → header + mobile lo assign; "StudentUp Footer" → policy pages |
| Settings | Permalink `/%postname%/`, posts per page 10, timezone Asia/Kolkata |

> Already unna categories/pages/menus ni **touch cheyyadu** — kevalam missing vi matrame add chestundi. Safe.

Malli run cheyyali ante: **Appearance → StudentUp Setup → Run setup now**.

---

## 2. Setup tarvata 3 steps

1. **Appearance → StudentUp** — social links (WhatsApp / Instagram / YouTube / Telegram), AdSense client + slot IDs, homepage sections ON/OFF (16 toggles).
2. **Appearance → StudentUp Score** — go-live readiness score. 90+ vaste AdSense apply cheyyandi.
3. **AdSense approve ayyaka matrame** → Appearance → StudentUp → *AdSense APPROVED* toggle ON. Appativaraku house ads matrame padtayi (blank box / policy risk zero).

---

## 3. Post publish chesetappudu (chala mukhyam)

Prathi job post lo **Job data box** nimpandi (post edit screen kinda vastundi):

| Field | Enduku |
|---|---|
| Last date (`2026-03-15` format) | Sticky apply bar lo countdown ("Only 3 days left"), job calendar, expiry auto-hide |
| Apply URL | Bottom **Apply online** button (CTR ki #1 lever) |
| Qualification | Qualification filter, eligibility checker, **Google for Jobs** schema |
| Salary / Vacancies / Age min-max | Cards, compare tool, salary calculator |

Ee 3 (last date + apply URL + qualification) unte post ki **JobPosting schema** auto vastundi → Google Jobs lo kanipinche chance.

---

## 4. Bot tho draft (autoblog)

Bot REST API dwara publish chestundi. Theme lo ee meta keys anni **REST lo registered** unnayi, so bot okate call lo full job card raayagaladu:

```
studentup_qual · studentup_last_date · studentup_apply_url · studentup_salary
studentup_vacancies · studentup_age_min · studentup_age_max
studentup_source_url · studentup_source_urls · studentup_source_checked · studentup_org_url
```

Bot side steps:

```bash
python run.py --site-setup      # WordPress settings + menus audit/fix
python run.py --once            # oka draft generate
python run.py --test-all        # full gate
```

WordPress lo: **Users → Profile → Application Passwords** create chesi `.env` lo pettandi.

---

## 5. Verify checklist (upload tarvata 2 nimishalu)

- [ ] Phone lo homepage open — hero, hot jobs, stories, quiz ring, bottom nav anni kanipistunnaya?
- [ ] Right side social rail (middle lo) icons sarigga unnaya?
- [ ] Laptop menu lo **Scholarships** + **Daily Quiz** unnaya?
- [ ] Oka job post open chesi bottom lo **Apply online** bar vachinda?
- [ ] `https://studentup.in/privacy/` lo third-party vendor + opt-out wording unda? (AdSense rule)
- [ ] Appearance → StudentUp Score → 90+?
