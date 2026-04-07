"""
TikTok Creative Center Scraper
Scrapes top-performing ads from TikTok Creative Center (no login required).
Also captures brand-specific content where accessible.
"""

import time, json
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright, Page

TIKTOK_TOP_ADS_URL = "https://ads.tiktok.com/business/creativecenter/inspiration/topads/pc/en?period=7&region=US&industry=280001"
TIKTOK_BRAND_SEARCH = "https://ads.tiktok.com/business/creativecenter/inspiration/topads/pc/en?period=30&region=US&keyword={brand}"


def wait_and_screenshot(page: Page, selector: str, save_path: Path, timeout: int = 10000) -> bool:
    """Wait for an element and screenshot it."""
    try:
        page.wait_for_selector(selector, timeout=timeout)
        el = page.query_selector(selector)
        if el:
            el.screenshot(path=str(save_path))
            return True
    except Exception as e:
        print(f"  [TikTok Screenshot] {e}")
    return False


def extract_video_url(page: Page) -> str | None:
    """Intercept network requests to find the video URL."""
    video_url = None
    try:
        requests_log = page.evaluate("""
            () => window.__videoRequests || []
        """)
        if requests_log:
            video_url = requests_log[0]
    except Exception:
        pass
    return video_url


def scrape_top_ads(page: Page, assets_dir: Path, max_ads: int = 10) -> list:
    """Scrape TikTok Creative Center top ads in Education category."""
    results = []
    print(f"[TikTok] Loading Creative Center top ads (Education)...")

    try:
        # Inject video URL interceptor
        page.add_init_script("""
            window.__videoRequests = [];
            const origOpen = XMLHttpRequest.prototype.open;
            XMLHttpRequest.prototype.open = function(m, url) {
                if (url && url.includes('.mp4')) window.__videoRequests.push(url);
                return origOpen.apply(this, arguments);
            };
        """)

        page.goto(TIKTOK_TOP_ADS_URL, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(5000)

        # Try to close any cookie/consent banners
        for selector in ["[class*='cookie'] button", "[class*='consent'] button", "button:has-text('Accept')", "[class*='accept']"]:
            try:
                btn = page.query_selector(selector)
                if btn:
                    btn.click()
                    page.wait_for_timeout(500)
                    break
            except Exception:
                pass

        # Scroll to load content
        page.evaluate("window.scrollTo(0, 500)")
        page.wait_for_timeout(3000)

        # Try specific TikTok Creative Center selectors first
        specific_selectors = [
            "[class*='video-card-item']",
            "[class*='videoCardItem']",
            "[class*='TopAdsItem']",
            "[class*='top-ads-item']",
            "[class*='InspirationCard']",
            "[class*='inspiration-card']",
            "[class*='AdCard']",
            "li[class*='card']",
        ]

        ad_cards = []
        for sel in specific_selectors:
            found = page.query_selector_all(sel)
            if len(found) >= 2:
                ad_cards = found
                print(f"[TikTok] Selector '{sel}' matched {len(found)} cards")
                break

        # Fallback to broader search but filter by size
        if not ad_cards:
            candidates = page.query_selector_all("[class*='card'], [class*='Card']")
            print(f"[TikTok] Found {len(candidates)} potential ad cards, filtering by size...")
            for c in candidates:
                try:
                    box = c.bounding_box()
                    if box and box["width"] > 150 and box["height"] > 150:
                        ad_cards.append(c)
                except Exception:
                    pass
            print(f"[TikTok] {len(ad_cards)} cards pass size filter")

        tiktok_dir = assets_dir / "tiktok" / "top_ads"
        tiktok_dir.mkdir(parents=True, exist_ok=True)

        collected = 0
        for i, card in enumerate(ad_cards):
            if collected >= max_ads:
                break
            try:
                # Get bounding box — skip tiny elements
                box = card.bounding_box()
                if not box or box["width"] < 150 or box["height"] < 150:
                    continue

                # Get text content
                text = card.inner_text().strip()[:500]

                # Screenshot the card
                img_path = tiktok_dir / f"top_ad_{collected}.png"
                card.scroll_into_view_if_needed()
                page.wait_for_timeout(300)
                card.screenshot(path=str(img_path))
                collected += 1

                results.append({
                    "id": f"tiktok_top_{collected}_{int(time.time())}",
                    "platform": "TikTok",
                    "brand": "TikTok Top Ad",
                    "search_term": "top_ads_education",
                    "ad_copy": text or "TikTok top education ad",
                    "title": "",
                    "days_running": 0,
                    "start_date": "",
                    "snapshot_url": TIKTOK_TOP_ADS_URL,
                    "image_path": str(img_path.relative_to(assets_dir.parent)),
                    "video_url": None,
                    "type": "video",
                    "scraped_at": datetime.utcnow().isoformat(),
                    "analysis": None
                })
            except Exception as e:
                print(f"  [TikTok] Error processing card {i}: {e}")
                continue

    except Exception as e:
        print(f"[TikTok] Error scraping top ads: {e}")
        # Fall back — screenshot the whole page
        try:
            fb_path = assets_dir / "tiktok" / "creative_center_fallback.png"
            fb_path.parent.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(fb_path), full_page=False)
            results.append({
                "id": f"tiktok_cc_{int(time.time())}",
                "platform": "TikTok",
                "brand": "TikTok Creative Center",
                "search_term": "top_ads_education",
                "ad_copy": "TikTok Creative Center — Education top ads. See full page screenshot.",
                "title": "Top Education Ads",
                "days_running": 0,
                "start_date": "",
                "snapshot_url": TIKTOK_TOP_ADS_URL,
                "image_path": str(fb_path.relative_to(assets_dir.parent)),
                "video_url": None,
                "type": "image",
                "scraped_at": datetime.utcnow().isoformat(),
                "analysis": None
            })
        except Exception:
            pass

    return results


def scrape_tiktok(brands: list, assets_dir: Path, config: dict) -> list:
    """Main entry: scrape TikTok for all brands + top ads."""
    max_ads = config["settings"]["max_ads_per_brand"]
    all_results = []

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1440, "height": 900},
            locale="en-US"
        )
        page = context.new_page()

        # Scrape TikTok Creative Center top ads
        top_ads = scrape_top_ads(page, assets_dir, max_ads * 2)
        all_results.extend(top_ads)

        browser.close()

    print(f"[TikTok] Collected {len(all_results)} items.")
    return all_results
