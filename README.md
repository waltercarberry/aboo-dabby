# ADIO positioning analysis

Keyword-frequency and positioning analysis of an Abu Dhabi investment search-results dump
(71 web rows, 22 news rows), with a positioning quadrant and a thematic heatmap.

## Run it

1. Install Python 3.8 or newer (check with `python3 --version`). No extra packages are needed.
2. Put `analyze_adio.py` and `abu_dhabi_investment_results.json` in the same folder.
3. Open a terminal in that folder.
4. Run: `python3 analyze_adio.py abu_dhabi_investment_results.json --out-dir output`
5. Open `output/adio_positioning.html` in a browser. The numbers behind every chart are in `output/analysis_data.json`.

## Show the page on GitHub

1. Create a repo and upload `analyze_adio.py`, `README.md` and `adio_positioning.html`.
2. In the repo go to Settings, then Pages.
3. Under "Build and deployment", choose "Deploy from a branch", pick `main` and `/ (root)`, then Save.
4. After a minute the page is live at `https://<your-username>.github.io/<repo-name>/adio_positioning.html`.

GitHub shows `.html` files as source code on the repo page, so Pages is the way to see the rendered version.

## Rationale by section

**Data cleaning.** The raw file mixes relevant pages with noise (Wikipedia entries, unrelated
market reports, flight and travel listings). Duplicate titles are removed (93 rows to 89), then
an off-topic screen drops the rest (89 to 50). Without this, generic words from junk pages would
dominate the counts. Web rows use `description` as their snippet; news rows use `snippet`.
Sector terms are searched in the first 6,000 characters of each row so one 10,000-character
interview cannot outweigh everything else.

**Keyword frequency.** Counted as document frequency (how many rows contain a term), not raw
term count, so one long page repeating a word 28 times does not look like a trend. Entity words
("Investment Office", "Falcon Economy", "Abu Dhabi") are excluded because they describe the
subject, not a sector. A separate list of named sector terms (fintech, agrifood, AI, health...)
answers your direct question about which sectors dominate.

**Sector lenses.** Ten sectors defined by keyword patterns (edit `SECT` in the script). A row can
belong to several sectors, so shares add up to more than 100%.

**ADIO positioning.** A row counts as ADIO if "ADIO" or "Abu Dhabi Investment Office" appears
anywhere in its title or full text. Those 8 rows are then read for how ADIO is described (the
"How ADIO is described" section is my reading of those rows, not an automated output).

**Positioning quadrant.** Horizontal axis: how big the sector is in the whole conversation (share
of all rows). Vertical axis: how much of that sector's discourse involves ADIO. The dashed
horizontal line is ADIO's overall share (8 of 50, 16%), so a bubble above it means ADIO appears
more than its average in that sector. The vertical line at 15% separates small conversations
from large ones; that cut-off is a judgement call. Bubble size is the number of ADIO rows.

**Thematic heatmap.** Rows are sectors; columns are who the row is about (ADIO, ADGM/ADFW,
sovereign funds, government, third parties). Cell shade is the share of that column's rows, which
makes columns of different sizes comparable. The counts are printed in each cell.

## Limitations

- Only 8 rows mention ADIO, and a few sectors rest on one article (the Gulf Business interview
  drives manufacturing, agrifood and automotive). Differences of one or two rows are noise.
- Keyword matching is crude: "power" can mean electricity or influence, "fund" can be any fund.
  Spot-check by reading the rows behind any cell you plan to quote.
- The data has no ADIO global-office information, so that part of the brief cannot be answered
  from this file.
