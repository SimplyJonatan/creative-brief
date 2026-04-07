"""
Meta Ad Library Scraper
Uses the official Meta Ad Library API for structured data,
then screenshots the ad snapshot page for each creative found.
"""

import os, json, time, requests
from datetime import datetime, timezone
from pathlib import Path
from playwright.sync_api import sync_playwright

META_API_BASE = "https://graph.facebook.com/v21.0/ads_archive"
FIELDS = ",".join([
    "id", "page_name", "ad_creative_bodies",
    "ad_creative_link_titles", "ad_creative_link_descriptions",
    "ad_delivery_start_time", "ad_snapshot_url",
    "ad_creative_link_captions"
])


def fetch_ads_for_brand(brand: str, access_token: str, country: str = "US", limit: int = 5) -> list:
    """Query Meta Ad Library API for a brand's active ads."""
    params = {
        "search_terms": brand,
        "ad_reached_countries": f'["{country}"]',
        "ad_type": "ALL",
        "ad_active_status": "ACTIVE",
        "fields": FIELDS,
        "limit": limit,
        "access_token": access_token,
    }
    try:
        resp = requests.get(META_API_BASE, params=params, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        return data.get("data", [])
    except Exception as e:
        print(f"  [Meta API] Error fetching {brand}: {e}")
        return []


def screenshot_snapshot(page, snapshot_url: str, save_path: Path) -> bool:
    """Load a Meta ad snapshot URL and take a screenshot."""
    try:
        page.goto(snapshot_url, wait_until="networkidle", timeout=20000)
        page.wait_for_timeout(2000)
        page.screenshot(path=str(save_path), full_page=False)
        return True
    except Exception as e:
        print(f"  [Meta Screenshot] Failed: {e}")
        return False


def calculate_days_running(start_date_str: str) -> int:
    """Calculate how many days an ad has been running."""
    try:
        start = datetime.fromisoformat(start_date_str.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        return (now - start).days
    except Exception:
        return 0


def scrape_meta(brands: list, access_token: str, assets_dir: Path, config: dict) -> list:
    """
    Main entry: scrape Meta ads for all brands in watchlist.
    Returns list of ad dicts ready for analysis.
    """
    if not access_token:
        print("[Meta] No META_ACCESS_TOKEN set — skipping Meta scraping.")
        return []

    country = config["settings"]["meta_country"]
    max_ads = config["settings"]["max_ads_per_brand"]
    results = []

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 900}
        )
        page = context.new_page()

        for brand in brands:
            print(f"[Meta] Scanning: {brand}")
            raw_ads = fetch_ads_for_brand(brand, access_token, country, max_ads)

            for ad in raw_ads:
                ad_id = ad.get("id", "")
                page_name = ad.get("page_name", brand)
                bodies = ad.get("ad_creative_bodies", [])
                titles = ad.get("ad_creative_link_titles", [])
                body_text = bodies[0] if bodies else ""
                title_text = titles[0] if titles else ""
                snapshot_url = ad.get("ad_snapshot_url", "")
                start_date = ad.get("ad_delivery_start_time", "")
                days_running = calculate_days_running(start_date) if start_date else 0

                # Screenshot the ad snapshot
                brand_dir = assets_dir / "meta" / brand.replace(" ", "_")
                brand_dir.mkdir(parents=True, exist_ok=True)
                img_path = brand_dir / f"{ad_id}.png"
                has_screenshot = False

                if snapshot_url and not img_path.exists():
                    has_screenshot = screenshot_snapshot(page, snapshot_url, img_path)
                elif img_path.exists():
                    has_screenshot = True

                results.append({
                    "id": f"meta_{ad_id}",
                    "platform": "Meta",
                    "brand": page_name,
                    "search_term": brand,
                    "ad_copy": body_text,
                    "title": title_text,
                    "days_running": days_running,
                    "start_date": start_date,
                    "snapshot_url": snapshot_url,
                    "image_path": str(img_path.relative_to(assets_dir.parent)) if has_screenshot else None,
                    "video_url": None,
                    "type": "image",
                    "scraped_at": datetime.utcnow().isoformat(),
                    "analysis": None
                })

            time.sleep(1)  # Polite delay between brands

        browser.close()

    print(f"[Meta] Found {len(results)} ads across {len(brands)} brands.")
    return results
