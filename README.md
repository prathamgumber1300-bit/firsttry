# Mosaic Meta Ad Intelligence

A live-data intelligence layer for Meta Ad Library focused on what a D2C marketing manager can act on every Monday morning.

## Working URL
Deploy this Streamlit app to Streamlit Community Cloud / Render and add your public URL here.

## What this solves
Most teams can scrape ads. The hard part is turning noisy ad cards into strategic intelligence:
- **Strategic shift signals:** format migration (e.g., static -> video), longer-lived themes, and churned experiments.
- **What's working now:** ads with high **longevity** are proxied as likely performers.
- **Opportunity gaps:** themes competitors are *not* covering for each Mosaic brand.
- **Monday actions:** concise, non-generic recommendations from current competitor behavior.

## Real competitors tracked (12)
- **Bebodywise:** Minimalist, The Derma Co, Plum Goodness, mCaffeine
- **Man Matters:** Beardo, Ustraa, Traya Health, Bold Care
- **Little Joys:** Mamaearth Baby, The Moms Co, Cetaphil Baby, Sebamed Baby India

Rationale and competitor mapping live in `data/competitors.yml`.

## How it works
1. `scripts/scrape_meta_ads.py` visits Meta Ad Library pages for each competitor and captures ad cards from live pages.
2. Ads are normalized into `data/meta_ads_latest.csv` with fields: format, theme, started date, text, brand mapping.
3. `app.py` renders a filterable dashboard by brand, ad format, message theme, and recency.
4. `src/intelligence.py` computes:
   - trend table by competitor + format,
   - longest-running ads,
   - gap detection,
   - Monday morning action bullets.

## Run locally
```bash
pip install -r requirements.txt
python -m playwright install chromium
python scripts/scrape_meta_ads.py
streamlit run app.py
```

## Weekly refresh
A GitHub Action (`.github/workflows/weekly-refresh.yml`) runs every Monday 04:00 UTC and stores fresh data artifacts.

---

## Brief write-up (<=500 words)
**D2C insight that drove this build:** performance teams don’t need more ad cards; they need **decision-ready signal density**. In D2C, creative fatigue is fast and copy frameworks recycle quickly. So we prioritized three indicators that are useful in real planning cycles: (1) what competitors keep live longest, (2) where they are shifting budget by format, and (3) which themes they systematically ignore.

**What I learned while designing:** “competitor” is not just same category—it is **same conversion intent**. For Bebodywise, ingredient-led skincare challengers matter more than broad beauty marketplaces. For Man Matters, men’s grooming and hair-loss treatment players both matter because they compete for the same male self-improvement spend. For Little Joys, trust-and-safety baby-care brands are the true benchmark because parental risk perception drives purchase.

**Why these design choices matter:**
- Longevity is used as a pragmatic proxy for winner creatives in the absence of spend or conversion data.
- Theme clustering is intentionally simple and auditable, so marketing managers can trust and tune it.
- “Monday actions” convert analysis into immediate execution direction (what to test, what to de-prioritize).
- Weekly repeatability via GitHub Actions ensures trend comparisons stay consistent over time.

This structure keeps the intelligence layer focused on **what changes the next sprint**, not vanity dashboards.
