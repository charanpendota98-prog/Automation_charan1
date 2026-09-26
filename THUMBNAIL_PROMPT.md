# StudentUp AI thumbnail prompt

The bot stores a category-aware prompt in the private article manifest at `_thumbnail_prompt`. It is designed for an image-capable Gemini/image model, while the current Pillow renderer remains the production-safe fallback.

## Important design decision

Do **not** ask the image model to draw Telugu headlines, dates, vacancy counts, government seals or logos. Image models often misspell small text or invent numbers. The model should create only the clean visual background and subject. StudentUp then overlays the exact verified title/facts after generation.

## Prompt

```text
Create a premium 16:9 editorial news thumbnail background for StudentUp, 1200 by 675 pixels, made for a Telugu student jobs website. Use a bold modern Indian news-card composition: deep navy and royal blue base, controlled saffron and red accents, bright white contrast, strong depth, clean lighting, crisp subject separation, subtle glass panels, and safe empty space for a headline overlay. Make it energetic and trustworthy, not sensational or clickbait.

Use one relevant realistic subject or a tasteful 2–3 element collage, with the main subject on the right or left according to the composition. Keep faces, uniforms, buildings and documents natural and sharp. No watermark, no random website name, no fake government seal, no fake number, no invented date, no competitor logo, no tiny unreadable text, and no text baked into the image.

For a government-job story, show a realistic public-service recruitment scene with a candidate, official-looking document folder and an appropriate office or exam environment. For software jobs, show a confident young developer in a modern workplace with abstract unreadable code. For scholarships, show a focused student with books and an application folder. For results or hall tickets, show a student checking an intentionally unreadable document or result screen. For walk-ins and job melas, show a clean interview desk, resume folder and organised venue.

Reserve a wide uncluttered central safe band and a clean lower panel area for post-processing. Avoid faces or important objects in the central text-safe area. No letters, words, dates, vacancy counts or logos should be generated inside the artwork. StudentUp will render the verified headline and facts in a separate safe overlay.
```
