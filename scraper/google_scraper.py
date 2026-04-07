"""
Google Ads Transparency Center Scraper
Scrapes active ads for each brand — works well without login,
supports both image and video ad capture.
"""

import time, re
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright, Page

GOOGLE_SEARCH_URL = "https://adstransparency.google.com/?region=US&query={brand}"


def scrape_brand(page: Page, brand: str, assets_dir: Path, max_ads: int = 5) -> list:
    """Scrape Google Ads Transparency for a single brand."""
    results = []
    url = GOOGLE_SEARCH_URL.format(brand=brand.replace(" ", "+"))
    brand_dir = assets_dir / "google" / brand.replace(" ", "_")
    brand_dir.mkdir(parents=True, exist_ok=True)

    print(f"[Google] Scanning: {brand}")
    try:
        # Intercept video URLs before navigation
        video_urls = []
        page.on("response", lambda r: video_urls.append(r.url) if ".mp4" in r.url else None)

        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(5000)

        # Handle consent page if shown
        for consent_sel in ["[aria-label='Accept all']", "button:has-text('Accept all')", "button:has-text('Accept')", "[id*='accept']"]:
            try:
                btn = page.query_selector(consent_sel)
                if btn:
                    btn.click()
                    page.wait_for_timeout(2000)
                    break
            except Exception:
                pass

        # Scroll down to trigger lazy loading
        page.evaluate("window.scrollTo(0, 400)")
        page.wait_for_timeout(3000)
        page.evaluate("window.scrollTo(0, 800)")
        page.wait_for_timeout(2000)

        # Find ad creative cards — Google Transparency uses Angular web components
        card_selectors = [
            "creative-preview",
            "ad-creative-shared-video-thumbnail",
            "[class*='advertiser-result-ad']",
            "mat-card",
            "[class*='creative-wrapper']",
            "[class*='result-item']",
            "[role='listitem']",
            "[class*='ad-unit']",
        ]

        cards = []
        for sel in card_selectors:
            found = page.query_selector_all(sel)
            if len(found) > 1:
                cards = found
                print(f"  [Google] Selector '{sel}' found {len(found)} cards for {brand}")
                break

        if not cards:
            # Last resort: grab any visible images that look like ad thumbnails
            cards = page.query_selector_all("img[src*='googleusercontent'], img[src*='gstatic']")
            if cards:
                print(f"  [Google] Found {len(cards)} thumbnail images for {brand}")

        print(f"  [Google] {len(cards)} cards found for {brand}")

        for i, card in enumerate(cards[:max_ads]):
            try:
                text = card.inner_text().strip()[:400]
                img_path = brand_dir / f"ad_{i}.png"

                # Screenshot the card
                card.scroll_into_view_if_needed()
                page.wait_for_timeout(500)
                card.screenshot(path=str(img_path))

                # Try to find video inside card
                vid_el = card.query_selector("video")
                video_url = None
                if vid_el:
                    video_url = vid_el.get_attribute("src") or vid_el.get_attribute("data-src")
                if not video_url and video_urls:
                    video_url = video_urls[0]

                ad_type = "video" if video_url else "image"

                results.append({
                    "id": f"google_{brand.replace(' ', '_')}_{i}_{int(time.time())}",
                    "platform": "Google/YouTube",
                    "brand": brand.title(),
                    "search_term": brand,
                    "ad_copy": text,
                    "title": "",
                    "days_running": 0,
                    "start_date": "",
                    "snapshot_url": url,
                    "image_path": str(img_path.relative_to(assets_dir.parent)),
                    "video_url": video_url,
                    "type": ad_type,
                    "scraped_at": datetime.utcnow().isoformat(),
                    "analysis": None
                })

            except Exception as e:
                print(f"  [Google] Error on card {i} for {brand}: {e}")
                continue

        # If no cards found, screenshot the full page as fallback
        if not results:
            fb_path = brand_dir / "page_fallback.png"
            page.screenshot(path=str(fb_path), full_page=False)
            results.append({
                "id": f"google_{brand.replace(' ', '_')}_fallback",
                "platform": "Google/YouTube",
                "brand": brand.title(),
                "search_term": brand,
                "ad_copy": f"Google Ads Transparency page for {brand}. See screenshot.",
                "title": "",
                "days_running": 0,
                "start_date": "",
                "snapshot_url": url,
                "image_path": str(fb_path.relative_to(assets_dir.parent)),
                "video_url": None,
                "type": "image",
                "scraped_at": datetime.utcnow().isoformat(),
                "analysis": None
            })

    except Exception as e:
        print(f"[Google] Failed for {brand}: {e}")

    return results


def scrape_google(brands: list, assets_dir: Path, config: dict) -> list:
    """Main entry: scrape Google Ads Transparency for all brands."""
    max_ads = config["settings"]["max_ads_per_brand"]
    all_results = []

    # Focus on top competitors for Google — not every brand
    priority_brands = brands[:8]

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1440, "height": 900},
            locale="en-US"
        )
        page = context.new_page()

        for brand in priority_brands:
            brand_ads = scrape_brand(page, brand, assets_dir, max_ads)
            all_results.extend(brand_ads)
            time.sleep(2)

        browser.close()

    print(f"[Google] Collected {len(all_results)} ads.")
    return all_results
