# v202 PROOF — "Breaking News" header nav item (Central Jobs laage click tho open)

Owner ask (2026-10-04): *"Breaking News kuda same like Central Jobs alaga undali —
akkada click chethe open avvali … phone and laptop lo neat ga undali."*

Ee folder lo unna screenshots **nijamaina clicks** (headless Chromium, theme JS tho)
to teesukunna stills — forced classes kaadu:

| File | Em chupistundi |
|---|---|
| `v202-laptop-panel.png` | Laptop 1440px: *Breaking News* meeda **click** → panel open (5 verified rows + `All updates` CTA), Central Jobs panel laage |
| `v202-phone-drawer.png` | Phone 390px: ☰ → drawer top lo **Breaking News** block (4 rows + All updates) |
| `v202-laptop-dark.png` | Same, **dark mode** |
| `v202-phone-dark.png` | Same, phone + dark mode |

## Measured proof (eyeball kaadu)

```
NODE_PATH=/tmp/chr/node_modules node tools/verify_breaking_ui.js
```

| viewport (light + dark = 16 runs) | horizontal overflow | panel / drawer |
|---|---|---|
| phone 360 · 390 · 414 | **0 px** | drawer 306 / 332 / 340 px · 4 rows · row overflow ledu |
| tablet 768 | **0 px** | drawer 340 px · 4 rows |
| laptop 1024 · 1280 · 1440 | **0 px** | panel **420×361**, viewport lopala, radius **16 px**, z-index **1000**, CTA ok |
| desktop 1920 | **0 px** | panel 420×361 |

**"Central Jobs laage" measured:** Breaking panel top offset vs *Central Jobs mega
panel* top offset = **3 px** (radius + z-index renditiki same) → same panel family,
same click/hover/keyboard contract.

## Live ki enduku inka ravaledu

Live `studentup.in` inka **theme 1.9.41** (pre-v201) tho nadustundi — `style.css`
lo `Version: 1.9.41`, mariyu header nav lo **Breaking News item ledu** (2026-10-04
measurement). Repo zip ippudu **1.9.42 (v202.1)**.

### Upload cheyyadam (2 nimushalu)

1. **Zip download:** https://raw.githubusercontent.com/charanpendota98-prog/Automation_charan1/arena/01a1035e-automation-charan1/wordpress-theme/studentup-theme.zip
   (138 files · 932 KB · sha256 `f8c9d12b2a32…`; GitHub lo file size 954174 bytes —
   local build tho exact match, verified)
2. WP Admin → **Appearance → Themes → Add New → Upload Theme** → ee zip →
   **Replace current with uploaded** → (LiteSpeed) **Purge All** → hard refresh.

Tarvata laptop lo Breaking News meeda hover/click; phone lo ☰ → drawer top lo
Breaking News block.
