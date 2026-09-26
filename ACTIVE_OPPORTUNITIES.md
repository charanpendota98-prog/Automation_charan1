# StudentUp Active Opportunities Board

StudentUp now has a live `https://studentup.in/latest-jobs/` board designed for daily circulation.

## What it does

- Displays Telangana Government Jobs, Andhra Pradesh Government Jobs, Central Government Jobs, walk-ins, job melas, software jobs, private jobs, scholarships, results, hall tickets and daily current affairs in separate sections.
- Reads the verified `studentup_last_date` metadata on each published post.
- Hides a post from the active board after the real deadline passes, without deleting the original article URL.
- Keeps an unavailable deadline visible as **Not announced**; it never invents a date.
- Uses verified deadlines only as an inclusion rule; the forward-ready Telegram list does not print a separate `Last date` line.
- Adds a responsive section jump rail and a compact `Latest active jobs` menu link.

## Daily owner digest

At the configured IST hour, the bot reads published posts and sends the owner a forward-ready HTML Telegram list. With `SHORTLINK_ENABLED=1` and the recommended `SHORTLINK_PROVIDER=wordpress`, the active StudentUp theme creates a root link such as `/ssc-cgl-2026`, stores its destination and click count in WordPress, and redirects to the exact article. TinyURL, Bitly, Short.io and is.gd remain optional adapters. If a provider is unavailable, the bot falls back to a native WordPress link; it never sends a dead link. Official application URLs are never shortened or hidden, and the digest is not published to the public channel automatically.

Configuration:

```env
OPPORTUNITY_DIGEST_ENABLED=1
OPPORTUNITY_DIGEST_HOUR=8
OPPORTUNITY_DIGEST_PER_SECTION=6
```

The public channel still receives an individual attractive image/caption post only after the owner approves and publishes an article.

## Category accuracy

URL-backed article generation now gives explicit official-domain signals priority before model labels. TSPSC/Telangana, APPSC/Andhra Pradesh, central portals, scholarship portals, walk-in/job-fair URLs and software/private career domains are checked first. Aggregator URLs fall back to the title and fetched source text, so a generic word such as “notification” cannot by itself create a government category.

The board also has a conservative legacy-title fallback so older miscategorised posts can appear in the most useful section without silently changing their WordPress taxonomy.

## Deployment notes

After the theme is activated, visit **Settings → Permalinks → Save Changes** if the `/latest-jobs/` route does not immediately resolve. The bot requires the existing WordPress Application Password and Telegram/Gemini environment configuration. Draft-first approval remains enabled.
