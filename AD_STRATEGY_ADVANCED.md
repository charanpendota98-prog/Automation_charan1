# 📢 AD STRATEGY ADVANCED — studentup.in (v43)
### "Personal ads + college banners + shop ads — highest placements, high CTR, 100% safe (Google/AdSense policy compliant)."

**Ee file = complete ad playbook.** Implementation already bot lo unti (v43 Ad Manager) — `run.py --ads` / `--ads-demo` run chesi chudu. Ivide strategy + execution + safety rules anni.

---

## 1️⃣ AD TYPES — mee inventory lo em em undali

| Type | Example | Layout | Best categories |
|---|---|---|---|
| **college_banner** | Local colleges, coaching centers, polytechnics | `banner` (full-width, top/mid) | Admissions, Education News, Exam Updates |
| **shop** | Stationery, electronics, books, local stores | `card` (compact, sidebar) | Exam Updates, Results, Study Tips |
| **service** | Mee Student Internet Center, form-filling, resume service | `card` | Scholarships, Govt Jobs |
| **sponsorship** | Coaching programs, test series, mock exams | `banner` + dedicated page link | all |

**Inventory file:** `ads/inventory.json` (repo lo) — prathi ad:
```json
{
  "id": "unique-id", "name": "Display name", "type": "college_banner",
  "layout": "banner",              // banner | card
  "active": true, "demo": false,   // demo:true = [demo] badge
  "label": "College Sponsorship",  // kicker lo kanipinche text
  "title": "Ad headline (short, benefit-first)",
  "description": "One-line value prop (max 120 chars)",
  "cta": "Know More",              // button text — action verb
  "image": "https://.../1200x360.jpg",  // optional; 1200×360 recommended
  "link": "https://college.example.edu/apply",
  "categories": "Admissions, Exam Updates",   // empty = all posts
  "start": "2026-10-01", "end": "2026-12-31"  // date window (auto off!)
}
```

**Add flow:** JSON lo ad add → `run.py --ads` (verify) → next post publish ayyaka automatic ga slot lo vasthundi. Existing posts ki: refresh/update command tho re-generate avutundi.

---

## 2️⃣ HIGHEST AD PLACEMENTS — "highest ads place" (where CTR actually happens)

**Bot placement engine (v43) — exact order:**

| Slot | Position | Why high CTR | CTR band (industry) |
|---|---|---|---|
| **TOP** | Quick Answer box taruvata matrame | Reader already engaged + value got — trust peak. "First pause point" | 0.8–2.5% (best) |
| **MID** | First content H2 + paragraph taruvata | Natural reading pause; mid-article attention highest | 0.5–1.5% |
| **BOTTOM** | Related/affiliate blocks MUNDU | High-intent readers (full article finished) | 0.3–1.0% |
| **SIDEBAR** (homepage/sticky) | Trending list taruvata | Browsing-mode readers; low effort clicks | 0.2–0.6% |
| **QUIZ END** (advanced, manual) | Quiz result screen | Peak engagement moment — "congrats + offer" | 1–3% (highest!) |

**Rules (bot enforces — hard):**
- Max **2 personal ads/post** (AdSense approval ayyaka auto **1** ki drop avtundi — AdSense 2 slots keep chesthundi)
- **Never near links** (150 chars lo vere `<a>` unte slot skip — "links near ads" = accidental clicks + policy risk)
- **CLS-safe** (min-height reserved — layout shift ledu → CWV green + ad viewability)
- Content dominance: 70%+ real content matrame ads (AdSense policy #1)

**Homepage (preview/index.html lo demo undi):** mid-grid banner (after 4 cards) + sidebar card (after trending). Quiz-end CTA = mee highest-CTR manual slot (quiz result screen lo oka "Exam Kit offer" card — quiz JS lo `#qresult` block lo add cheyochu).

---

## 3️⃣ HIGH-CTR TRICKS — "CLICK HIGH GA VACHEKALA" (100% SAFE)

**Design (bot already does — verify matrame):**
1. **Benefit-first headline** — "2026 Admissions Open" ✓ vs "ABC College" ✗ (outcome, not name)
2. **One CTA button matrame** — orange, round pill, "Know More →" (action verb)
3. **Clear "SPONSORED" label** — small, top-left, visible (policy MUST + trust = more intentional clicks)
4. **Image with real photo** — college building/student photo > graphic (trust CTR +40%)
5. **Specificity** — "Fee ₹85,000/yr, hostel included" > "Affordable fees" (numbers = credibility)
6. **Relevance match** — ad category = article category (bot auto-matches: scholarship post lo coaching ad, admissions post lo college banner)

**Context tricks (safe, high impact):**
7. **Timed relevance** — admission season (Apr–Jul) lo college banner `active:true`, exam season lo test-series ad. Inventory lo `start/end` dates use cheyandi — season-off ads = low CTR + reader annoyance
8. **Deadline urgency** — "Applications close in 9 days" (bot countdown pattern) — urgency CTR double chesthundi
9. **Social proof line** — "2,400+ students enrolled 2025" (description lo) — real numbers matrame
10. **Quiz-end CTA** — quiz complete ayyaka "Test series free trial" — highest-intent moment
11. **TS/AP targeting** — AP students ki AP colleges, TS ki TS (category + district context) — local relevance CTR best

**Measurement (clicks prove cheyyadaniki):**
12. **UTM auto-tagging** — bot prathi ad link ki automatic ga:
    `?utm_source=studentup.in&utm_medium=sponsored&utm_campaign=<ad-id>&utm_content=<slot>`
    → GA4 lo ad-wise + slot-wise clicks/CTR report. **Ee ane real "click high ga vachchunda" measurement.**
13. **A/B test** — 2 versions of same ad (different headline) inventory lo add chesi, UTM tho CTR compare → winner keep. 2 weeks duration.
14. **Weekly check** — GA4 → Acquisition → Campaigns → `studentup.in` → ad CTR. < 0.3% unte creative change.

---

## 4️⃣ GOOGLE/ADSENSE SAFE RULES — "GOOGLE TRICKS SAFEGAA"

**MUST (bot enforces — hard-coded, override cheyagalanu):**

| Rule | Why | Bot behavior |
|---|---|---|
| Visible "Sponsored/Advertisement" label | AdSense policy: ads clearly identified | Prathi block lo `SPONSORED · <label>` kicker |
| `rel="sponsored nofollow noopener"` | Google: paid links marked | Prathi ad link automatic |
| No misleading link labels | Policy: "link that looks like content" ban | CTA button = obvious ad element |
| No ads next to links | Accidental clicks = penalty + low quality score | 150-char adjacency check → skip slot |
| Content dominance 70%+ | Site reputation / AdSense approval | Max 2 self-ads + 2 AdSense = content-first |
| No popups/interstitials | AdSense policy violation (account risk) | In-content matrame |
| No auto-redirecting ad links | Policy + UX | `target="_blank"` + user-initiated only |
| Disclosure line | FTC/India ASCI: commercial content marked | "Sponsored — partner ki direct link" |

**AdSense vs Personal Ads — coexistence (advanced):**
- **Before approval:** 2 personal ads fill the slot space (legit revenue start)
- **After approval:** `ADSENSE_APPROVED=1` → personal cap auto 1, AdSense takes 2 in-content slots + auto-ads
- Personal ads **NEVER styled like Google ads** (no "Ad" triangle confusion — use "SPONSORED" text, different visual system: orange/kicker vs AdSense neutral)
- No "advertorial" thin pages — every ad-linked page should be a real destination

**What NOT to do (account risk):**
- ❌ Clickbait ad labels ("FREE money", "You won't believe")
- ❌ Buying fake clicks / asking friends to click (policy violation — permanent ban)
- ❌ Ad-only pages (spam signal)
- ❌ Competitor ads / gambling / crypto without review (niche policy)
- ❌ Hiding the "Sponsored" label or making it invisible

---

## 5️⃣ COLLEGE BANNER DEALS — "vere college banners" (how to actually get them)

**Outreach template (WhatsApp/email — 2 min):**

> Hello, studentup.in ki — Telangana + AP students ki daily verified jobs/scholarship/exam updates chestunnam (studentup.in). Mee college admissions/exams ki related articles readers lo high traffic untundi.
>
> **Offer:** Admissions season lo mee college banner ad — article in-content (top placement) + homepage sidebar.
> - Placement: 1 top slot + 1 sidebar card
> - Duration: [30 days / admission season]
> - Tracking: UTM links (clicks report weekly share chestam)
> - Rate: ₹[X]/month (demo — market: local colleges ₹5k–25k/mo; coaching ₹10k–50k/mo)
>
> Sample: studentup.in/ads-preview lo placement chudachu. Interest unte mee college details + image (1200×360) send cheyyandi — 24 hrs lo live avvadam.

**Follow-up:** 3 days lo response lekapote oka follow-up. Admission season (March–July) BEFORE start cheyandi. Local coaching centers lo first deal easy avtundi (proof + reviews).

**Deal hygiene (safe):**
- Clear written agreement (scope, duration, rate, both-side cancellation)
- College info verify (UGC/AICTE approval) — fake college ads = site reputation risk
- `rel="sponsored"` + disclosure = mee + unna party rendu safe (ASCI rules)

---

## 6️⃣ SHOP ADS (personal) — "shoppuig ilaga"

1. **Own shop unte:** `service-ad-demo` entry edit cheyandi — real name, address (map link), phone, image. `active:true`
2. **Local partner unte:** commission/flat rate set chesi inventory lo add. Link = partner site/Google Business profile
3. **Best categories:** Exam Updates (stationery during exam season), Study Tips (books/test series)
4. **Season rotation:** exam season stationery, admission season hostel/scholarship service, year-round — resume/form service (mee own service)
5. **UGC proof:** customer photos/reviews description lo (real ones matrame)

---

## 7️⃣ QUICK START (today — 15 min)

```bash
# 1. Inventory chudu (status + slot plans)
run.py --ads

# 2. Visible preview (browser lo open)
run.py --ads-demo        # → output/ads-preview.html

# 3. First REAL ad add (ads/inventory.json):
#    - demo ad copy cheyandi, "demo": false
#    - real name/link/image/title
#    - categories target cheyandi
#    - start/end dates (season)
```

**After approval (AdSense):** `.env` lo `ADSENSE_APPROVED=1` + `ADSENSE_CLIENT_ID` → bot `--adsense-kit` → personal cap auto 1 → revenue streams 2 parallel ga (safe).

**Weekly (5 min):** GA4 → campaign `studentup.in` → ad CTR check → < 0.3% creative rotate → 2nd month lo best CTR ad expansion.

---

## ⚠️ Honest note

CTR numbers = industry benchmarks (news/education niche), not guarantees. Real CTR = content traffic × relevance × creative quality. "Click buying" ledu — ani. UTM tho measured clicks matrame truth. AdSense approval/revenue code tho guarantee cheyagalanu — safe practices (ee playbook) matrame protect chestayi.

*Last updated: v43 (2026-09-16) — Ad Manager implemented + tested (12 test cases · 31/31 suites).*
