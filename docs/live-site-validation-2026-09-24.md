# StudentUp live-site validation — 2026-09-24

This is a public live-site observation, not a fixture, mock, local readiness score, or Rank Math prediction.

## Scope and limits

- Site checked: `https://studentup.in`
- Public WordPress REST and rendered article output were inspected.
- No WordPress owner credentials were available in this workspace, so private editor fields and the Rank Math editor UI could not be opened.
- The owner-reported Rank Math UI score of **23/100** is therefore the authoritative score for the affected post. Local QA/readiness percentages must not be substituted for it.

## Live observations

- `GET /wp-json/studentup/v1/theme-info` reported:
  - theme: `studentup`
  - version: `1.9.8`
  - SEO bridge: active
  - Rank Math: active
  - posts: `21`
- Public post inspected: WordPress post ID `4016`.
- Public URL: `https://studentup.in/upsc-indian-forest-service-exam-2026-telugu-2/`
- WordPress status: `publish`.
- Slug ends in `-2`, indicating a duplicate/collision that requires editorial review.

## Live content failures observed

1. A published article displays `Source-backed draft; verify the official notice`.
2. The article contains filler/promotional phrases such as `ప్రతిష్టాత్మకమైన`, `సువర్ణావకాశం`, and `గొప్ప కెరీర్ అవకాశం`.
3. It includes an estimated critical recruitment claim (`సుమారు 80` posts) rather than a clearly cited official vacancy value.
4. Repeated summary/advice paragraphs add length without helping the applicant complete a task.
5. Promotional Telegram copy interrupts the core recruitment information.
6. The article was publicly published instead of being retained as a review draft.
7. The live deployment does not yet demonstrate the new read-only Rank Math stored-score endpoint.

## Required acceptance criteria

The live workflow is not accepted until all of the following are demonstrated on a newly generated real draft:

- automatic source discovery uses real current URLs;
- at least three independent source domains are retained, including an official source for critical facts;
- no unsupported vacancy, date, fee, salary, result, or Hall Ticket release claim;
- no filler, repeated summary, generic motivation, fabricated quote, or fake personal experience;
- task-specific completeness for Jobs, Results, Hall Tickets, or a documented Success Story;
- WordPress post status remains `draft`;
- Telegram receives the draft link and evidence status;
- Rank Math Focus Keyword, SEO Title, and Description pass authenticated WordPress readback;
- only Rank Math's stored read-only score is reported when available; otherwise the score is `unknown`;
- a human reviews the official notice before publication.

## Current verdict

**FAIL — deployment and authenticated real-draft validation pending.**

Passing unit tests, fake WordPress tests, ZIP checks, code audits, or a local `100/100` preflight does not change this verdict and must never be presented as the live Rank Math result.
