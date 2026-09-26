# MotionBalance

MotionBalance is a data engineering and analytics portfolio project built on real
British Parliamentary (BP) debate results, pulled from public Tabbycat tournament
APIs. It ingests raw ballots into DuckDB, builds an analytics layer in SQL, exports
static JSON, and serves it from a Next.js site.

The site's central question:

> How do average points earned from Opening Government (OG), Opening Opposition
> (OO), Closing Government (CG) and Closing Opposition (CO) vary between teams
> with different levels of prior performance?

## How "prior performance" is defined

For each team's result in a preliminary-round debate, `prior_team_strength` is that
team's average points from its own **earlier** preliminary rounds only, computed as
a SQL window function (`sql/analytics.sql`, view `team_strength`) with a frame of
`UNBOUNDED PRECEDING AND 1 PRECEDING` — the current round and any future round can
never leak into it. A team only qualifies for the strength-band analysis once it
has **at least two** such earlier results (`prior_rounds_played >= 2`), so a band
reflects an actual track record rather than a single earlier result.

Teams are grouped into three bands by that prior average:

| Prior average points | Strength band             |
| --------------------- | -------------------------- |
| Below 1.0              | Lower prior performance    |
| 1.0 to below 2.0       | Middle prior performance   |
| 2.0 to 3.0             | Higher prior performance   |

A band describes performance *going into* a given round, not a fixed trait — the
same team can sit in a different band in round 5 than it did in round 2. The
aggregation itself (average points per band × position, with sample sizes) lives
in the `strength_band_stats` SQL view and is exported to
`web/public/data/strength_bands.json` by `scripts/export_data.py`; an empty
band/position combination is left out of the export rather than filled in as zero
— the site renders those as "no data," never a fabricated 0.

## Architecture

```
Tabbycat APIs → scripts/fetch_all_catalog.py → data/raw/ (JSON, gitignored)
              → scripts/load_all.py           → motionbalance.duckdb (gitignored)
                    (RAW tables, sql/schema.sql; validated by scripts/validate.py
                     before it's allowed to replace the live database)
              → scripts/export_data.py        → web/public/data/*.json
                    (ANALYTICS layer, sql/analytics.sql, applied fresh on every run)
              → web/ (Next.js, App Router)     → static site reading those JSON files
```

Every step is idempotent and safe to re-run: `load_all.py` builds into a throwaway
`.tmp` database and only swaps it in over the live one if `validate.py` passes, so
a bad or partial run can never leave you with a broken database. `export_data.py`
re-applies `sql/analytics.sql` at the top of every run rather than assuming the
views already exist.

## Setup

Python (3.10+):

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Node (for the website):

```
cd web
npm install
```

## Regenerating the data

These commands run from the repository root, with the Python virtualenv active.

1. **Fetch raw tournament data** (skips any tournament already marked complete;
   retries on rate limits with backoff instead of silently dropping data):

   ```
   python scripts/fetch_all_catalog.py
   ```

2. **Load it into DuckDB** (rebuilds `motionbalance.duckdb` from everything in
   `data/raw/`, validates the build, and only replaces the live database if
   validation passes):

   ```
   python scripts/load_all.py
   ```

3. **Export the static JSON the website reads**, including `strength_bands.json`:

   ```
   python scripts/export_data.py
   ```

4. Optional — print the two regression models (leakage-safe vs. leaky) to the
   terminal without regenerating any files:

   ```
   python scripts/regression.py
   ```

## Running the website

```
cd web
npm install
npm run dev      # local dev server at http://localhost:3000
```

For a production build:

```
cd web
npm run build
npm start
```

The site reads only `web/public/data/*.json` at build time — it has no runtime
dependency on Python, DuckDB, or network access once that data is exported. If
`strength_bands.json` hasn't been generated yet, the analytics page still builds
and shows an explicit empty state naming the exact command to run, instead of
failing.

## Deployment

This is a standard Next.js App Router app with no custom server requirements, so
it deploys cleanly to any host that runs `npm run build` then `npm start` (or a
static host, since every page is statically generated). On Vercel: connect this
GitHub repository, set the project's root directory to `web/` (the Next.js app is
not at the repo root), and it builds and deploys on every push. This step needs
your own hosting account, so it isn't something that can be completed from here —
the two lines above are the whole of what's left to do.

## Current status / what's not yet done

- The catalog currently has 757 of ~1,177 candidate tournaments fetched and
  loaded; the remaining ~374 are not yet fetched. Re-running
  `fetch_all_catalog.py` will pick them up.
- The strength-band sample (teams with 2+ prior results) is necessarily smaller
  than the full dataset — the site states both numbers side by side rather than
  implying they're the same population.
- The chart and regression models describe association, not causation — the site
  says this explicitly next to both.
- Beyond this release, known open items from an earlier code review are still
  deferred: a fuller write-up of what the leakage-safe regression does and
  doesn't control for, tighter scoping of the research question the modeling
  section answers, a glossary reconciling the several "how many debates/motions"
  counts used across pages, and automated tests/CI.
