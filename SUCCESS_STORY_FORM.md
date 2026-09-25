# StudentUp Verified Success Story Form

StudentUp can publish up to **three independently verified Telangana/AP success stories per ISO week**. The form is an intake channel, not a publication guarantee. Every submission remains a draft until the editorial team checks evidence, consent, identity, quote permission and photo rights.

## Google Form settings

1. Create the form in the owner's Google Workspace account.
2. Turn on a response receipt if appropriate, but do not publish the response sheet.
3. Use **File upload** only for an optional portrait/photo. Google may require the respondent to sign in; explain that the upload is private and used only for editorial review.
4. Do not ask for Aadhaar, PAN, bank details, OTPs, passwords, certificates, hall tickets or other identity/financial documents.
5. Restrict the response spreadsheet to the editorial team. Do not put its URL in a public article or `llms.txt`.
6. Put the final `https://forms.gle/...` URL in `.env` as `SUCCESS_STORY_FORM_URL`, then run `python run.py --push-theme-data`. Or set it in **WordPress Admin → StudentUp → Content & site → Verified Success Story Google Form URL**.
7. Create a WordPress page such as `/share-your-success-story/` and add:

```text
[studentup_success_story_form]
```

The theme also adds the CTA to the `Success Stories` category archive when the form URL is configured.

## Exact form fields

Use these labels/keys in the Google Sheet export. The intake validator uses the keys in parentheses.

### Person and location

- Public name to display (`public_name`) — short answer; allow initials if preferred.
- Full legal/contact name for editorial verification (`full_name`) — private; never publish automatically.
- State (`state`) — required choice: Telangana / Andhra Pradesh.
- District or city (`district`) — optional; do not publish an exact home address.
- Age group (`age_group`) — 18+ / Under 18 / Prefer not to say.
- Guardian consent (`guardian_consent`) — required when under 18.
- Safe contact email (`contact_email`) — private; editorial follow-up only.

### Achievement and evidence

- What did you achieve? (`achievement`) — exam result, job selection, scholarship, internship or career milestone.
- Achievement date (`achievement_date`) — month/year is enough if an exact date is not useful.
- Institution/employer/exam name (`institution`) — short answer.
- Your preparation/process in your own words (`lessons`) — paragraph; no guarantee claims.
- Official result, institution, employer or public verification links (`official_links`) — one or more complete `https://` URLs.
- Optional public portfolio/LinkedIn/channel link (`public_link`) — separate link permission is required.
- May StudentUp publish that public link? (`public_link_consent`) — Yes / No.

### Photo and publication rights

- Upload one portrait/photo you own or have permission to use (`photo_url`) — required for a selected story; the editor may ask for a replacement if it is not publishable.
- I own this photo or have permission to license it to StudentUp (`photo_rights`) — required Yes/No.
- Photo credit (`photo_credit`) — name or “self-supplied”.
- May StudentUp publish my name, achievement, edited story and photo? (`publish_consent`) — required explicit Yes.
- May StudentUp quote my written answers, edited for clarity but not meaning? (`quote_consent`) — Yes/No.
- Corrections permission (`correction_consent`) — Yes; the respondent may request factual corrections.

## Editorial selection and links

- Export the sheet to a private CSV only when the editor is ready to review.
- Run the private validator/manifest workflow; it rejects missing consent, unsupported geography, missing evidence and sensitive-document words.
- Select at most three valid stories per ISO week. Extra valid submissions are deferred or invited into the next week; they are not silently published.
- Verify at least one official or attributable result/source and seek a second corroborating source for high-impact claims.
- Write a fresh third-person article. Do not manufacture first-person experience, marks, rank, salary, hardship, quotes or family details.
- The article may link to the official result/institution/employer page. A personal LinkedIn, portfolio, YouTube or social link needs separate permission. Never publish a phone number, email, private Google Drive link, exact address or ID document.
- Credit the photo and state that the story was submitted and verified by StudentUp's editorial team. Do not imply that StudentUp guarantees a job, exam rank, income or future success.
- Keep a private consent/evidence record. Store only what is necessary and delete exports/photos according to the site's retention policy.

## Private review command

After adding the validator to an operations script, use a private path outside `preview/` and outside the public web root:

```python
from pathlib import Path
from autoblog.success_story_intake import load_csv, write_manifest

rows = load_csv(Path("/secure/private/google-form-export.csv"))
write_manifest(rows, Path("/secure/private/success-stories-review.json"))
```

The manifest is for human review. It never calls the publish pipeline and must not be committed to Git.
