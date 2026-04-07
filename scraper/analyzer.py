"""
AI Analyzer — uses Claude API to:
1. Analyze each ad (image + text) for selling points, hook, format, audience
2. Generate competitive gap analysis vs Simply Piano
3. Generate segment-specific creative briefs
4. Generate daily SP angles
5. Write the Sunday Strategy Memo (on Sundays)
"""

import os, json, base64
from pathlib import Path
from datetime import datetime
import anthropic

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))

AD_ANALYSIS_SCHEMA = {
    "hook_type": "one of: aspiration | pain_point | social_proof | question | transformation | humor | urgency | curiosity",
    "hook_text": "the opening line or visual hook in 1 sentence",
    "selling_points": ["list", "of", "key", "selling", "points", "used"],
    "target_audience": "one of: 50plus | parents_kids | general_adult | unclear",
    "format_type": "one of: testimonial | demo | lifestyle | talking_head | before_after | tutorial | product_showcase | ugc",
    "emotional_tone": "one of: inspiring | fun | urgent | reassuring | exciting | nostalgic | humorous",
    "cta": "the call to action text",
    "is_video": "true or false",
    "estimated_days_running": "number or 0 if unknown",
    "notes": "1-2 sentences of notable observations"
}


def encode_image(image_path: str) -> str | None:
    """Encode image to base64 for Claude vision."""
    try:
        with open(image_path, "rb") as f:
            return base64.standard_b64encode(f.read()).decode("utf-8")
    except Exception:
        return None


def analyze_single_ad(ad: dict, repo_root: Path) -> dict:
    """Send one ad to Claude for structured analysis."""
    image_b64 = None
    if ad.get("image_path"):
        full_path = repo_root / ad["image_path"]
        image_b64 = encode_image(str(full_path))

    prompt = f"""You are a creative strategist analyzing a competitor ad for Simply Piano — a piano learning app.

Ad details:
- Brand: {ad.get('brand', 'Unknown')}
- Platform: {ad.get('platform', 'Unknown')}
- Ad copy: {ad.get('ad_copy', 'No text available')}
- Title: {ad.get('title', '')}
- Days running: {ad.get('days_running', 0)}

{"[An image of this ad is attached. Analyze it visually as well.]" if image_b64 else "[No image available — analyze based on text only.]"}

Return ONLY a valid JSON object with these exact keys:
{json.dumps(AD_ANALYSIS_SCHEMA, indent=2)}

Be specific and concrete. If unsure, make your best inference."""

    messages = []
    if image_b64:
        messages = [{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": image_b64}},
                {"type": "text", "text": prompt}
            ]
        }]
    else:
        messages = [{"role": "user", "content": prompt}]

    try:
        response = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=600,
            messages=messages
        )
        text = response.content[0].text.strip()
        # Extract JSON even if wrapped in markdown code blocks
        if "```" in text:
            text = text.split("```")[1].lstrip("json").strip()
        return json.loads(text)
    except Exception as e:
        print(f"  [Analyzer] Error analyzing ad {ad.get('id')}: {e}")
        return {
            "hook_type": "unclear",
            "hook_text": ad.get("ad_copy", "")[:100],
            "selling_points": [],
            "target_audience": "unclear",
            "format_type": "unclear",
            "emotional_tone": "unclear",
            "cta": "",
            "is_video": False,
            "estimated_days_running": ad.get("days_running", 0),
            "notes": "Analysis failed."
        }


def generate_gap_analysis(all_ads: list, sp_angles: list) -> dict:
    """Compare competitor selling points vs SP's known angles."""
    # Aggregate all selling points across ads
    all_points = []
    for ad in all_ads:
        if ad.get("analysis") and ad["analysis"].get("selling_points"):
            all_points.extend(ad["analysis"]["selling_points"])

    # Count frequency
    from collections import Counter
    point_counts = Counter(all_points)
    top_competitor_points = [p for p, _ in point_counts.most_common(20)]

    prompt = f"""You are a creative strategist for Simply Piano — a piano learning app.

COMPETITOR SELLING POINTS (most used first):
{json.dumps(top_competitor_points, indent=2)}

SIMPLY PIANO'S KNOWN ANGLES:
{json.dumps(sp_angles, indent=2)}

Analyze the gap. Return ONLY a valid JSON object:
{{
  "angles_competitors_use_sp_doesnt": [
    {{"angle": "...", "frequency": "high/medium/low", "opportunity": "1 sentence why SP should try this"}}
  ],
  "angles_only_sp_uses": [
    {{"angle": "...", "recommendation": "1 sentence on how to protect/amplify this"}}
  ],
  "saturated_angles": [
    {{"angle": "...", "note": "1 sentence on differentiation opportunity"}}
  ],
  "summary": "2-3 sentence strategic summary"
}}"""

    try:
        response = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )
        text = response.content[0].text.strip()
        if "```" in text:
            text = text.split("```")[1].lstrip("json").strip()
        return json.loads(text)
    except Exception as e:
        print(f"[Analyzer] Gap analysis error: {e}")
        return {"angles_competitors_use_sp_doesnt": [], "angles_only_sp_uses": [], "saturated_angles": [], "summary": ""}


def generate_creative_briefs(top_ads: list, segments: list) -> list:
    """
    For each segment, find a relevant reference ad and generate a full SP creative brief.
    Also generates one completely original idea.
    """
    if not top_ads:
        return []

    ads_summary = []
    for ad in top_ads[:10]:
        ads_summary.append({
            "brand": ad.get("brand"),
            "platform": ad.get("platform"),
            "ad_copy": ad.get("ad_copy", "")[:200],
            "analysis": ad.get("analysis", {}),
            "days_running": ad.get("days_running", 0),
            "image_path": ad.get("image_path")
        })

    segments_info = [{"id": s["id"], "name": s["name"], "dos": s["dos"], "donts": s["donts"]} for s in segments]

    prompt = f"""You are a senior creative strategist at Simply Piano — a piano learning app.

TODAY'S TOP COMPETITOR ADS:
{json.dumps(ads_summary, indent=2)}

SIMPLY PIANO'S SEGMENTS:
{json.dumps(segments_info, indent=2)}

Generate creative briefs. Return ONLY a valid JSON array:
[
  {{
    "segment_id": "50plus | parents_kids | general_adult",
    "segment_name": "...",
    "reference_brand": "brand name this is inspired by",
    "reference_platform": "Meta | TikTok | Google/YouTube",
    "what_makes_reference_work": "2 sentences on what the competitor ad does well",
    "sp_adaptation": "3 sentences on what to keep, change, and add for Simply Piano",
    "headline": "Ready-to-use headline for this SP ad",
    "visual_direction": "1 sentence describing the visual",
    "cta": "Call to action text",
    "hook_opening": "First 3 seconds or opening line of the ad"
  }},
  {{
    "segment_id": "original",
    "segment_name": "Original Idea",
    "reference_brand": "None — original concept",
    "reference_platform": "Meta",
    "what_makes_reference_work": "N/A",
    "sp_adaptation": "Full description of the original creative concept",
    "headline": "Headline for this original ad",
    "visual_direction": "1 sentence describing the visual",
    "cta": "Call to action",
    "hook_opening": "Opening hook"
  }}
]

Generate one brief per segment PLUS one completely original idea that no competitor is doing."""

    try:
        response = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        text = response.content[0].text.strip()
        if "```" in text:
            text = text.split("```")[1].lstrip("json").strip()
        return json.loads(text)
    except Exception as e:
        print(f"[Analyzer] Creative briefs error: {e}")
        return []


def generate_platform_trends(all_ads: list) -> list:
    """Generate platform trend observations from today's finds."""
    if not all_ads:
        return []

    analyses = [ad.get("analysis", {}) for ad in all_ads if ad.get("analysis")]
    if not analyses:
        return []

    prompt = f"""Based on these ad analyses from today's competitive scan:
{json.dumps(analyses[:15], indent=2)}

Generate 4-5 platform trend observations. Return ONLY a valid JSON array:
[
  {{
    "icon": "emoji",
    "title": "Short trend title",
    "description": "2-3 sentences explaining the trend and why it matters",
    "action": "One concrete action Simply Piano should take"
  }}
]"""

    try:
        response = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=800,
            messages=[{"role": "user", "content": prompt}]
        )
        text = response.content[0].text.strip()
        if "```" in text:
            text = text.split("```")[1].lstrip("json").strip()
        return json.loads(text)
    except Exception as e:
        print(f"[Analyzer] Trends error: {e}")
        return []


def generate_sunday_memo(all_ads: list, gap_analysis: dict, briefs: list) -> str:
    """Generate the Sunday strategy memo for Jonatan (runs on Sundays only)."""
    today = datetime.utcnow()
    if today.weekday() != 6:  # 6 = Sunday
        return ""

    prompt = f"""You are a senior creative strategist writing a Sunday morning strategy memo for Jonatan,
the Creative Acquisition Manager at Simply Piano.

This week's competitive intelligence summary:
- Total ads analyzed: {len(all_ads)}
- Gap analysis: {json.dumps(gap_analysis.get('summary', ''), indent=2)}
- Key missing angles: {json.dumps([a['angle'] for a in gap_analysis.get('angles_competitors_use_sp_doesnt', [])[:3]], indent=2)}
- SP's unique angles: {json.dumps([a['angle'] for a in gap_analysis.get('angles_only_sp_uses', [])[:3]], indent=2)}

Write a 4-paragraph strategic memo:
1. What shifted in the competitive landscape this week
2. The one thing Simply Piano should start doing that competitors are doing well
3. The one thing Simply Piano should protect (their unique angle)
4. One bold creative experiment to try this week

Write as a smart peer, not a report. Conversational but substantive. No bullet points."""

    try:
        response = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=600,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text.strip()
    except Exception as e:
        print(f"[Analyzer] Sunday memo error: {e}")
        return ""


def run_full_analysis(all_ads: list, config: dict, repo_root: Path) -> dict:
    """Run complete analysis pipeline on all scraped ads."""
    print(f"[Analyzer] Analyzing {len(all_ads)} ads...")

    # 1. Analyze each ad individually
    for i, ad in enumerate(all_ads):
        print(f"  Analyzing ad {i+1}/{len(all_ads)}: {ad.get('brand')} ({ad.get('platform')})")
        ad["analysis"] = analyze_single_ad(ad, repo_root)

    # 2. Gap analysis vs SP
    print("[Analyzer] Running gap analysis...")
    gap_analysis = generate_gap_analysis(all_ads, config["simply_piano_known_angles"])

    # 3. Creative briefs per segment
    print("[Analyzer] Generating creative briefs...")
    creative_briefs = generate_creative_briefs(all_ads, config["segments"])

    # 4. Platform trends
    print("[Analyzer] Generating platform trends...")
    trends = generate_platform_trends(all_ads)

    # 5. Sunday memo
    sunday_memo = generate_sunday_memo(all_ads, gap_analysis, creative_briefs)
    if sunday_memo:
        print("[Analyzer] Sunday memo generated.")

    return {
        "ads": all_ads,
        "gap_analysis": gap_analysis,
        "creative_briefs": creative_briefs,
        "trends": trends,
        "sunday_memo": sunday_memo,
        "generated_at": datetime.utcnow().isoformat(),
        "total_ads_analyzed": len(all_ads)
    }
