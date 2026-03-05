import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yaml
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

DATE_PATTERN = re.compile(r"Started running on\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})")


def normalize_theme(text: str) -> str:
    t = text.lower()
    rules = {
        "offer_promo": ["off", "sale", "discount", "buy", "offer", "combo"],
        "problem_solution": ["hair fall", "acne", "pigmentation", "dandruff", "dry skin", "erectile", "pcos"],
        "social_proof": ["review", "trusted", "clinically", "dermat", "doctor", "lakhs"],
        "education": ["how to", "why", "routine", "ingredient", "explained", "tips"],
        "urgency": ["limited", "today", "hurry", "last chance", "ending"],
    }
    for theme, keywords in rules.items():
        if any(k in t for k in keywords):
            return theme
    return "generic"


def parse_started_on(text: str):
    m = DATE_PATTERN.search(text)
    if not m:
        return None
    try:
        return datetime.strptime(m.group(1), "%B %d, %Y").date().isoformat()
    except ValueError:
        return None


def scrape_brand(page, brand_name: str, country: str, limit: int):
    q = brand_name.replace(" ", "%20")
    url = (
        "https://www.facebook.com/ads/library/?active_status=all&ad_type=all"
        f"&country={country}&is_targeted_country=false&media_type=all&q={q}&search_type=keyword_unordered"
    )
    page.goto(url, wait_until="domcontentloaded", timeout=90000)
    page.wait_for_timeout(6000)

    for _ in range(5):
        page.mouse.wheel(0, 6000)
        page.wait_for_timeout(2000)

    cards = page.locator("div[role='article']")
    count = min(cards.count(), limit)
    rows = []

    for i in range(count):
        card = cards.nth(i)
        text = card.inner_text(timeout=5000)
        started_on = parse_started_on(text)

        media_type = "static"
        if card.locator("video").count() > 0:
            media_type = "video"
        elif card.locator("[aria-label*='carousel' i]").count() > 0:
            media_type = "carousel"

        rows.append(
            {
                "brand_query": brand_name,
                "scraped_at": datetime.now(timezone.utc).isoformat(),
                "started_on": started_on,
                "ad_text": " ".join(text.split())[:1500],
                "media_type": media_type,
                "message_theme": normalize_theme(text),
                "source_url": url,
            }
        )
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="data/competitors.yml")
    parser.add_argument("--output", default="data/meta_ads_latest.csv")
    args = parser.parse_args()

    config = yaml.safe_load(Path(args.config).read_text())
    country = config["meta"]["country"]
    max_ads = int(config["meta"].get("max_ads_per_brand", 20))

    brands = []
    for mosaic_brand, payload in config["brands"].items():
        for comp in payload["competitors"]:
            brands.append((mosaic_brand, comp["name"]))

    all_rows = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_extra_http_headers({"Accept-Language": "en-US,en;q=0.9"})

        for mosaic_brand, competitor in brands:
            try:
                rows = scrape_brand(page, competitor, country, max_ads)
                for r in rows:
                    r["mosaic_brand"] = mosaic_brand
                    r["competitor_brand"] = competitor
                all_rows.extend(rows)
                print(f"Scraped {len(rows)} ads for {competitor}")
            except PlaywrightTimeoutError:
                print(f"Timeout while scraping {competitor}")
        browser.close()

    df = pd.DataFrame(all_rows)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.output, index=False)

    metadata = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "rows": len(df),
        "brands": len(brands),
    }
    Path("data/run_metadata.json").write_text(json.dumps(metadata, indent=2))
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
