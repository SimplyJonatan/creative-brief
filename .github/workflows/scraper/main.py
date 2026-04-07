"""
Simply Piano Creative Brief Bot — Main Orchestrator
Runs daily at 05:00 UTC via GitHub Actions.
"""

import os, sys, json
from datetime import datetime
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────
REPO_ROOT   = Path(__file__).parent.parent
CONFIG_PATH = REPO_ROOT / "config.json"
DATA_PATH   = REPO_ROOT / "data" / "ads_history.json"
ASSETS_DIR  = REPO_ROOT / "assets"
OUTPUT_HTML = REPO_ROOT / "index.html"

# ── Load config ────────────────────────────────────────────────────────
def load_config() -> dict:
    with open(CONFIG_PATH) as f:
        return json.load(f)

# ── History store ──────────────────────────────────────────────────────
def load_history() -> dict:
    DATA_PATH.parent.mkdir(exist_ok=True)
    if DATA_PATH.exists():
        with open(DATA_PATH) as f:
            return json.load(f)
    return {"ads": {}, "first_seen": {}}

def save_history(history: dict):
    with open(DATA_PATH, "w") as f:
        json.dump(history, f, indent=2)

def update_history(history: dict, new_ads: list) -> list:
    """Mark new ads, update days_running for known ads, return enriched list."""
    today = datetime.utcnow().date().isoformat()
    enriched = []
    for ad in new_ads:
        ad_id = ad["id"]
        if ad_id not in history["first_seen"]:
            history["first_seen"][ad_id] = today
            ad["is_new"] = True
        else:
            ad["is_new"] = False
            first = datetime.fromisoformat(history["first_seen"][ad_id]).date()
            now = datetime.utcnow().date()
            ad["days_running"] = max(ad.get("days_running", 0), (now - first).days)
        history["ads"][ad_id] = {
            "brand": ad.get("brand"),
            "platform": ad.get("platform"),
            "last_seen": today,
            "days_running": ad.get("days_running", 0)
        }
        enriched.append(ad)
    return enriched

# ── Longevity leaderboard ──────────────────────────────────────────────
def build_leaderboard(history: dict, threshold_days: int) -> list:
    """Pull long-running ads from history."""
    today = datetime.utcnow().date()
    winners = []
    for ad_id, info in history["ads"].items():
        first_seen = history["first_seen"].get(ad_id)
        if not first_seen:
            continue
        days = (today - datetime.fromisoformat(first_seen).date()).days
        if days >= threshold_days:
            winners.append({
                "ad_id": ad_id,
                "brand": info.get("brand", "Unknown"),
                "platform": info.get("platform", ""),
                "days_running": days,
                "last_seen": info.get("last_seen", "")
            })
    return sorted(winners, key=lambda x: x["days_running"], reverse=True)[:10]

# ── Main ───────────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print(f"Simply Piano Creative Brief Bot")
    print(f"Run date: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    print("=" * 60)

    config = load_config()
    history = load_history()
    ASSETS_DIR.mkdir(exist_ok=True)

    all_ads = []

    # ── Scrape Meta ────────────────────────────────────────────────────
    if config["platforms"].get("meta"):
        meta_token = os.environ.get("META_ACCESS_TOKEN", "")
        if meta_token:
            from meta_scraper import scrape_meta
            all_brands = (
                config["watchlist"]["direct_competitors"] +
                config["watchlist"]["edtech"][:3]
            )
            meta_ads = scrape_meta(all_brands, meta_token, ASSETS_DIR, config)
            all_ads.extend(meta_ads)
        else:
            print("[Main] META_ACCESS_TOKEN not set — skipping Meta.")

    # ── Scrape TikTok ──────────────────────────────────────────────────
    if config["platforms"].get("tiktok"):
        from tiktok_scraper import scrape_tiktok
        tiktok_ads = scrape_tiktok(
            config["watchlist"]["direct_competitors"],
            ASSETS_DIR, config
        )
        all_ads.extend(tiktok_ads)

    # ── Scrape Google ──────────────────────────────────────────────────
    if config["platforms"].get("google"):
        from google_scraper import scrape_google
        priority = (
            config["watchlist"]["direct_competitors"][:4] +
            config["watchlist"]["edtech"][:2]
        )
        google_ads = scrape_google(priority, ASSETS_DIR, config)
        all_ads.extend(google_ads)

    print(f"\n[Main] Total raw ads collected: {len(all_ads)}")

    if not all_ads:
        print("[Main] No ads collected — generating brief with history only.")

    # ── Update history & flag new vs returning ────────────────────────
    all_ads = update_history(history, all_ads)
    save_history(history)

    # ── AI Analysis ───────────────────────────────────────────────────
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")
    analysis_results = {
        "ads": all_ads,
        "gap_analysis": {},
        "creative_briefs": [],
        "trends": [],
        "sunday_memo": "",
        "generated_at": datetime.utcnow().isoformat(),
        "total_ads_analyzed": len(all_ads)
    }

    if anthropic_key:
        from analyzer import run_full_analysis
        analysis_results = run_full_analysis(all_ads, config, REPO_ROOT)
    else:
        print("[Main] No ANTHROPIC_API_KEY — skipping AI analysis.")

    # ── Longevity leaderboard ─────────────────────────────────────────
    leaderboard = build_leaderboard(
        history,
        config["settings"]["longevity_warning_days"]
    )

    # ── Generate HTML brief ───────────────────────────────────────────
    trigger_token = os.environ.get("TRIGGER_TOKEN", "")
    from brief_generator import generate_brief
    generate_brief(
        analysis_results=analysis_results,
        leaderboard=leaderboard,
        config=config,
        output_path=OUTPUT_HTML,
        repo_root=REPO_ROOT,
        trigger_token=trigger_token
    )

    print(f"\n✅ Brief generated: {OUTPUT_HTML}")
    print(f"   Ads analyzed:  {len(all_ads)}")
    print(f"   Leaderboard:   {len(leaderboard)} long-running ads")
    print(f"   Creative briefs: {len(analysis_results.get('creative_briefs', []))}")


if __name__ == "__main__":
    # Run from repo root so relative paths work
    os.chdir(Path(__file__).parent)
    sys.path.insert(0, str(Path(__file__).parent))
    main()
