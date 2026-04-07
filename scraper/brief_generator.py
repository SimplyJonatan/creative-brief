"""
HTML Brief Generator
Builds the full index.html from analysis results.
"""

import json
from datetime import datetime
from pathlib import Path


def platform_badge(platform: str) -> str:
    colors = {
        "Meta": "#1877f2",
        "TikTok": "#ff0050",
        "Google/YouTube": "#ff0000",
        "YouTube": "#ff0000"
    }
    color = colors.get(platform, "#8b90b5")
    return f'<span style="background:rgba({_hex_to_rgb(color)},0.15);color:{color};border-radius:4px;padding:2px 7px;font-size:10px;font-weight:700;">{platform}</span>'


def _hex_to_rgb(h: str) -> str:
    h = h.lstrip("#")
    return ",".join(str(int(h[i:i+2], 16)) for i in (0, 2, 4))


def longevity_badge(days: int) -> str:
    if days >= 60:
        return f'<span style="background:rgba(62,207,142,0.1);border:1px solid #3ecf8e;border-radius:20px;padding:3px 10px;font-size:11px;color:#3ecf8e;font-weight:700;">🏆 {days}d running</span>'
    elif days >= 30:
        return f'<span style="background:rgba(247,201,72,0.1);border:1px solid #f7c948;border-radius:20px;padding:3px 10px;font-size:11px;color:#f7c948;font-weight:700;">⚡ {days}d running</span>'
    elif days > 0:
        return f'<span style="background:rgba(139,144,181,0.1);border:1px solid #2e3250;border-radius:20px;padding:3px 10px;font-size:11px;color:#8b90b5;">{days}d</span>'
    return ""


def ad_card_html(ad: dict, show_new_badge: bool = True) -> str:
    analysis = ad.get("analysis") or {}
    brand = ad.get("brand", "Unknown")
    platform = ad.get("platform", "")
    ad_copy = (ad.get("ad_copy") or "")[:200]
    days = ad.get("days_running", 0)
    is_new = ad.get("is_new", False)
    img_path = ad.get("image_path", "")
    video_url = ad.get("video_url", "")
    snapshot_url = ad.get("snapshot_url", "#")
    ad_type = ad.get("type", "image")

    # Selling points as tags
    sp_tags = ""
    for sp in (analysis.get("selling_points") or [])[:4]:
        sp_tags += f'<span style="background:#22263a;border:1px solid #2e3250;border-radius:4px;padding:2px 7px;font-size:10px;color:#8b90b5;">{sp}</span> '

    # Hook type tag
    hook = analysis.get("hook_type", "")
    hook_tag = f'<span style="background:rgba(108,99,255,0.1);border:1px solid #6c63ff;border-radius:4px;padding:2px 7px;font-size:10px;color:#6c63ff;">{hook}</span>' if hook else ""

    # New badge
    new_badge = '<span style="background:#6c63ff;color:#fff;border-radius:4px;padding:2px 8px;font-size:10px;font-weight:700;margin-left:6px;">NEW</span>' if is_new and show_new_badge else ""

    # Media section
    if img_path:
        if video_url:
            media_html = f'''
            <div style="position:relative;background:#1a1d27;aspect-ratio:16/9;overflow:hidden;">
              <video src="{video_url}" poster="{img_path}" style="width:100%;height:100%;object-fit:cover;" controls preload="metadata"></video>
            </div>'''
        else:
            media_html = f'<img src="{img_path}" style="width:100%;aspect-ratio:16/9;object-fit:cover;display:block;" alt="{brand} ad" loading="lazy">'
    else:
        media_html = f'<div style="width:100%;aspect-ratio:16/9;background:#22263a;display:flex;align-items:center;justify-content:center;font-size:32px;">📺</div>'

    format_type = analysis.get("format_type", "")
    hook_text = analysis.get("hook_text", "")
    notes = analysis.get("notes", "")

    return f'''
<div class="ad-card" style="background:#1a1d27;border:1px solid #2e3250;border-radius:12px;overflow:hidden;transition:all 0.2s;" onmouseover="this.style.borderColor='#6c63ff';this.style.transform='translateY(-2px)'" onmouseout="this.style.borderColor='#2e3250';this.style.transform='translateY(0)'">
  {media_html}
  <div style="padding:14px 16px;">
    <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;flex-wrap:wrap;">
      <span style="font-weight:700;font-size:14px;">{brand}</span>{new_badge}
      {platform_badge(platform)}
      {longevity_badge(days)}
    </div>
    {f'<div style="background:#22263a;border-radius:6px;padding:8px 12px;margin-bottom:10px;font-size:12px;color:#e8eaf6;font-style:italic;border-left:3px solid #6c63ff;">{hook_text}</div>' if hook_text else ''}
    <div style="font-size:12px;color:#8b90b5;margin-bottom:10px;line-height:1.6;">{ad_copy}</div>
    {f'<div style="font-size:11px;color:#8b90b5;margin-bottom:10px;">{notes}</div>' if notes else ''}
    <div style="display:flex;gap:5px;flex-wrap:wrap;margin-bottom:12px;">
      {hook_tag}
      {f'<span style="background:#22263a;border:1px solid #2e3250;border-radius:4px;padding:2px 7px;font-size:10px;color:#8b90b5;">{format_type}</span>' if format_type else ''}
      {sp_tags}
    </div>
    <div style="display:flex;gap:8px;">
      <a href="{snapshot_url}" target="_blank" style="flex:1;padding:8px;background:#6c63ff;color:#fff;border-radius:8px;font-size:12px;font-weight:600;text-align:center;text-decoration:none;">🔗 View Ad</a>
      {f'<a href="{video_url}" download style="flex:1;padding:8px;background:#22263a;color:#e8eaf6;border:1px solid #2e3250;border-radius:8px;font-size:12px;font-weight:600;text-align:center;text-decoration:none;">⬇ Video</a>' if video_url else ''}
    </div>
  </div>
</div>'''


def creative_brief_card(brief: dict) -> str:
    is_original = brief.get("segment_id") == "original"
    border_color = "#ff6584" if is_original else "#6c63ff"
    badge = "✨ Original Idea" if is_original else brief.get("segment_name", "")

    return f'''
<div style="background:#1a1d27;border:1px solid #2e3250;border-left:4px solid {border_color};border-radius:12px;padding:22px 24px;">
  <div style="display:flex;align-items:center;gap:10px;margin-bottom:14px;">
    <span style="background:rgba({_hex_to_rgb(border_color)},0.1);border:1px solid {border_color};border-radius:20px;padding:3px 12px;font-size:11px;color:{border_color};font-weight:600;">{badge}</span>
    {f'<span style="font-size:11px;color:#8b90b5;">ref: {brief.get("reference_brand")} / {brief.get("reference_platform")}</span>' if not is_original else ''}
  </div>
  {f'<div style="font-size:12px;color:#8b90b5;margin-bottom:12px;padding:10px 14px;background:#22263a;border-radius:8px;"><strong style="color:#e8eaf6;">What makes it work:</strong> {brief.get("what_makes_reference_work","")}</div>' if not is_original else ''}
  <div style="font-size:13px;color:#8b90b5;margin-bottom:14px;line-height:1.7;">{brief.get("sp_adaptation","")}</div>
  <div style="background:#22263a;border-radius:8px;padding:14px 16px;margin-bottom:12px;">
    <div style="font-size:10px;color:#8b90b5;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:6px;">HEADLINE</div>
    <div style="font-size:16px;font-weight:700;color:#e8eaf6;">{brief.get("headline","")}</div>
  </div>
  <div style="background:#22263a;border-radius:8px;padding:12px 16px;margin-bottom:10px;">
    <div style="font-size:10px;color:#8b90b5;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:4px;">HOOK / OPENING</div>
    <div style="font-size:13px;color:#e8eaf6;font-style:italic;">"{brief.get("hook_opening","")}"</div>
  </div>
  <div style="display:flex;gap:8px;flex-wrap:wrap;">
    <div style="flex:1;background:#22263a;border-radius:8px;padding:10px 14px;min-width:140px;">
      <div style="font-size:10px;color:#8b90b5;margin-bottom:3px;">VISUAL</div>
      <div style="font-size:12px;color:#e8eaf6;">{brief.get("visual_direction","")}</div>
    </div>
    <div style="background:#22263a;border-radius:8px;padding:10px 14px;">
      <div style="font-size:10px;color:#8b90b5;margin-bottom:3px;">CTA</div>
      <div style="font-size:13px;font-weight:700;color:#6c63ff;">{brief.get("cta","")}</div>
    </div>
  </div>
</div>'''


def generate_brief(analysis_results: dict, leaderboard: list, config: dict, output_path: Path, repo_root: Path, trigger_token: str = ""):  # trigger_token kept for backwards compat, no longer embedded
    ads = analysis_results.get("ads", [])
    gap = analysis_results.get("gap_analysis", {})
    briefs = analysis_results.get("creative_briefs", [])
    trends = analysis_results.get("trends", [])
    sunday_memo = analysis_results.get("sunday_memo", "")
    now = datetime.utcnow()
    date_str = now.strftime("%A, %B %-d, %Y")
    new_ads = [a for a in ads if a.get("is_new")]
    total_brands = len(set(a.get("brand") for a in ads))

    # ── Ad cards HTML ──
    # Show new ads if we have them; otherwise fall back to ALL collected ads
    display_ads = new_ads if new_ads else ads
    new_ads_html = "".join(ad_card_html(a) for a in display_ads[:12]) if display_ads else \
        '<div style="grid-column:1/-1;text-align:center;padding:48px;color:#8b90b5;border:1px dashed #2e3250;border-radius:12px;"><div style="font-size:32px;margin-bottom:10px;">🔍</div>No ads collected yet — check that your scraper secrets are set up correctly.</div>'
    ads_section_label = f"{len(new_ads)} new" if new_ads else f"{len(display_ads)} collected today"

    # ── Leaderboard HTML ──
    lb_html = ""
    for i, item in enumerate(leaderboard[:8]):
        lb_html += f'''
<div style="background:#1a1d27;border:1px solid #2e3250;border-radius:12px;padding:16px 20px;display:flex;align-items:center;gap:16px;">
  <div style="font-size:24px;font-weight:700;color:#6c63ff;min-width:36px;">#{i+1}</div>
  <div style="flex:1;">
    <div style="font-weight:700;font-size:15px;">{item.get("brand","")}</div>
    <div style="font-size:12px;color:#8b90b5;">{item.get("platform","")} · Last seen {item.get("last_seen","")}</div>
  </div>
  {longevity_badge(item.get("days_running",0))}
</div>'''
    if not lb_html:
        lb_html = '<div style="text-align:center;padding:32px;color:#8b90b5;border:1px dashed #2e3250;border-radius:12px;">Longevity data builds after 30 days of scanning. Check back soon.</div>'

    # ── Gap analysis HTML ──
    gap_missing = gap.get("angles_competitors_use_sp_doesnt", [])
    gap_unique = gap.get("angles_only_sp_uses", [])
    gap_saturated = gap.get("saturated_angles", [])

    missing_html = "".join(f'<div style="background:#1a1d27;border:1px solid #2e3250;border-left:3px solid #ff6584;border-radius:8px;padding:12px 16px;margin-bottom:8px;"><div style="font-weight:600;font-size:13px;">{g.get("angle","")}</div><div style="font-size:12px;color:#8b90b5;margin-top:3px;">{g.get("opportunity","")}</div><span style="font-size:10px;color:#ff6584;">{g.get("frequency","")}</span></div>' for g in gap_missing[:5]) or '<div style="color:#8b90b5;font-size:13px;">Analysis builds over time as more ads are collected.</div>'

    unique_html = "".join(f'<div style="background:#1a1d27;border:1px solid #2e3250;border-left:3px solid #3ecf8e;border-radius:8px;padding:12px 16px;margin-bottom:8px;"><div style="font-weight:600;font-size:13px;">{g.get("angle","")}</div><div style="font-size:12px;color:#8b90b5;margin-top:3px;">{g.get("recommendation","")}</div></div>' for g in gap_unique[:4]) or '<div style="color:#8b90b5;font-size:13px;">Keep scanning to identify your unique territory.</div>'

    # ── Creative briefs HTML ──
    briefs_html = "".join(creative_brief_card(b) for b in briefs) if briefs else \
        '<div style="color:#8b90b5;text-align:center;padding:32px;border:1px dashed #2e3250;border-radius:12px;">Creative briefs generated after first full scan with AI analysis.</div>'

    # ── Trends HTML ──
    trends_html = ""
    for t in trends:
        trends_html += f'''
<div style="background:#1a1d27;border:1px solid #2e3250;border-radius:12px;padding:18px 20px;">
  <div style="font-size:24px;margin-bottom:8px;">{t.get("icon","📊")}</div>
  <div style="font-weight:700;font-size:14px;margin-bottom:6px;">{t.get("title","")}</div>
  <div style="font-size:13px;color:#8b90b5;line-height:1.6;margin-bottom:10px;">{t.get("description","")}</div>
  <div style="font-size:11px;color:#f7c948;">⚡ {t.get("action","")}</div>
</div>'''

    # ── Watchlist HTML ──
    def watchlist_section(title: str, brands: list, category: str) -> str:
        cards = ""
        for b in brands:
            q = b.replace(" ", "+")
            cards += f'<a href="https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=US&q={q}&search_type=keyword_unordered" target="_blank" style="background:#1a1d27;border:1px solid #2e3250;border-radius:10px;padding:12px 14px;display:flex;align-items:center;gap:10px;text-decoration:none;color:#e8eaf6;transition:border-color 0.2s;" onmouseover="this.style.borderColor=\'#6c63ff\'" onmouseout="this.style.borderColor=\'#2e3250\'"><span style="font-size:14px;">🔗</span><div><div style="font-size:13px;font-weight:600;">{b.title()}</div><div style="font-size:10px;color:#8b90b5;">{category}</div></div></a>'
        return f'<div style="margin-bottom:20px;"><div style="font-size:11px;color:#8b90b5;background:#22263a;border-radius:20px;padding:3px 12px;display:inline-block;margin-bottom:12px;">{title}</div><div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:10px;">{cards}</div></div>'

    watchlist_html = (
        watchlist_section("🎯 Direct Competitors", config["watchlist"]["direct_competitors"], "Music Learning") +
        watchlist_section("📚 EdTech / Habit", config["watchlist"]["edtech"], "EdTech") +
        watchlist_section("👨‍👩‍👧 Kids & Family", config["watchlist"]["kids"], "Kids Education")
    )

    # ── Sunday memo ──
    memo_html = f'''
<div id="memo" style="margin-top:40px;">
  <div style="display:flex;align-items:center;gap:10px;margin-bottom:20px;">
    <h2 style="font-size:18px;font-weight:600;">📝 Sunday Strategy Memo</h2>
    <span style="background:#22263a;border:1px solid #2e3250;border-radius:20px;padding:2px 10px;font-size:11px;color:#8b90b5;">For Jonatan · {date_str}</span>
  </div>
  <div style="background:#1a1d27;border:1px solid #2e3250;border-radius:12px;padding:28px 32px;font-size:14px;color:#8b90b5;line-height:1.8;white-space:pre-wrap;">{sunday_memo}</div>
</div>''' if sunday_memo else ""

    # ── Full HTML ────────────────────────────────────────────────────
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1.0"/>
  <title>Simply Piano — Creative Brief · {date_str}</title>
  <style>
    *{{box-sizing:border-box;margin:0;padding:0;}}
    body{{background:#0f1117;color:#e8eaf6;font-family:'Segoe UI',system-ui,sans-serif;font-size:15px;line-height:1.6;}}
    .topbar{{background:#1a1d27;border-bottom:1px solid #2e3250;padding:14px 32px;display:flex;align-items:center;justify-content:space-between;position:sticky;top:0;z-index:100;}}
    .container{{max-width:1300px;margin:0 auto;padding:32px 24px;}}
    .hero{{background:linear-gradient(135deg,#1a1d27 0%,#22263a 100%);border:1px solid #2e3250;border-radius:12px;padding:28px 32px;margin-bottom:32px;display:grid;grid-template-columns:repeat(4,1fr);gap:24px;}}
    .hero-stat{{text-align:center;}}
    .hero-stat .num{{font-size:36px;font-weight:700;color:#6c63ff;}}
    .hero-stat .label{{font-size:12px;color:#8b90b5;margin-top:2px;}}
    .section-header{{display:flex;align-items:center;gap:10px;margin-bottom:20px;margin-top:40px;}}
    .ad-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:20px;}}
    .briefs-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(360px,1fr));gap:16px;}}
    .trends-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:14px;}}
    .gap-grid{{display:grid;grid-template-columns:1fr 1fr;gap:20px;}}
    a.pill{{background:#22263a;border:1px solid #2e3250;border-radius:20px;padding:4px 14px;font-size:12px;color:#8b90b5;cursor:pointer;transition:all 0.2s;text-decoration:none;display:inline-block;}}
    a.pill:hover,a.pill.active{{background:#6c63ff;color:#fff;border-color:#6c63ff;}}
    @media(max-width:768px){{.hero{{grid-template-columns:1fr 1fr;}}.gap-grid{{grid-template-columns:1fr;}}.topbar{{padding:12px 16px;flex-wrap:wrap;gap:8px;}}}}
    #refresh-btn{{background:#22263a;border:1px solid #2e3250;border-radius:20px;padding:6px 16px;font-size:12px;font-weight:600;color:#8b90b5;cursor:pointer;transition:all 0.2s;display:flex;align-items:center;gap:6px;}}
    #refresh-btn:hover{{border-color:#6c63ff;color:#6c63ff;}}
    #refresh-btn:disabled{{opacity:0.5;cursor:not-allowed;}}
    #refresh-modal{{display:none;position:fixed;inset:0;background:rgba(0,0,0,0.7);z-index:999;align-items:center;justify-content:center;}}
    #refresh-modal.open{{display:flex;}}
    #refresh-box{{background:#1a1d27;border:1px solid #2e3250;border-radius:16px;padding:32px;width:340px;text-align:center;}}
    #pin-input{{background:#0f1117;border:1px solid #2e3250;border-radius:8px;color:#e8eaf6;font-size:20px;letter-spacing:8px;padding:12px;width:100%;text-align:center;margin:16px 0;outline:none;}}
    #pin-input:focus{{border-color:#6c63ff;}}
    #pin-error{{color:#ff6584;font-size:12px;min-height:18px;margin-bottom:10px;}}
    #pin-submit{{background:#6c63ff;color:#fff;border:none;border-radius:8px;padding:10px 24px;font-size:14px;font-weight:600;cursor:pointer;width:100%;}}
    #pin-submit:hover{{opacity:0.9;}}
    #pin-cancel{{background:none;border:none;color:#8b90b5;font-size:12px;cursor:pointer;margin-top:10px;}}
    #status-toast{{display:none;position:fixed;bottom:24px;left:50%;transform:translateX(-50%);background:#1a1d27;border:1px solid #2e3250;border-radius:12px;padding:14px 24px;font-size:13px;color:#e8eaf6;z-index:1000;gap:10px;align-items:center;}}
    #status-toast.show{{display:flex;}}
  </style>
</head>
<body>

<!-- PIN MODAL -->
<div id="refresh-modal">
  <div id="refresh-box">
    <div style="font-size:24px;margin-bottom:8px;">🔄</div>
    <div style="font-weight:700;font-size:16px;margin-bottom:4px;">Refresh Brief</div>
    <div style="font-size:13px;color:#8b90b5;margin-bottom:4px;">Enter your PIN to start a new scan.</div>
    <div style="font-size:11px;color:#8b90b5;">Takes ~10 min. Page auto-refreshes when ready.</div>
    <input id="pin-input" type="password" maxlength="4" placeholder="PIN ····" autocomplete="off"/>
    <div id="token-row" style="display:none;">
      <div style="font-size:11px;color:#8b90b5;margin-bottom:6px;text-align:left;">GitHub Token (saved in your browser — only needed once)</div>
      <input id="token-input" type="password" placeholder="github_pat_..." autocomplete="off" style="background:#0f1117;border:1px solid #2e3250;border-radius:8px;color:#e8eaf6;font-size:13px;padding:10px;width:100%;outline:none;margin-bottom:8px;"/>
    </div>
    <div id="token-saved" style="display:none;font-size:11px;color:#3ecf8e;margin-bottom:8px;">✅ Token saved · <button onclick="forgetToken()" style="background:none;border:none;color:#8b90b5;font-size:11px;cursor:pointer;text-decoration:underline;">use a different one</button></div>
    <div id="pin-error"></div>
    <button id="pin-submit" onclick="submitPin()">Run Scan</button>
    <br/><button id="pin-cancel" onclick="closeModal()">Cancel</button>
  </div>
</div>

<!-- STATUS TOAST -->
<div id="status-toast">
  <span id="toast-icon">⏳</span>
  <span id="toast-msg">Scan started — brief will update in ~10 minutes.</span>
</div>

<script>
  const CORRECT_PIN   = '5698';
  const REPO_OWNER    = 'SimplyJonatan';
  const REPO_NAME     = 'creative-brief';
  const WORKFLOW_FILE = 'daily-brief.yml';
  const TOKEN_KEY     = 'cb_gh_token';

  function openModal() {{
    const saved = localStorage.getItem(TOKEN_KEY) || '';
    document.getElementById('pin-input').value = '';
    document.getElementById('token-input').value = saved ? '••••••••••••••••' : '';
    document.getElementById('token-row').style.display = saved ? 'none' : 'block';
    document.getElementById('token-saved').style.display = saved ? 'block' : 'none';
    document.getElementById('pin-error').textContent = '';
    document.getElementById('refresh-modal').classList.add('open');
    setTimeout(() => document.getElementById('pin-input').focus(), 100);
  }}
  function closeModal() {{
    document.getElementById('refresh-modal').classList.remove('open');
  }}
  function forgetToken() {{
    localStorage.removeItem(TOKEN_KEY);
    document.getElementById('token-row').style.display = 'block';
    document.getElementById('token-saved').style.display = 'none';
    document.getElementById('token-input').value = '';
  }}
  document.getElementById('pin-input').addEventListener('keydown', e => {{
    if (e.key === 'Enter') submitPin();
  }});
  function showToast(icon, msg, duration=6000) {{
    document.getElementById('toast-icon').textContent = icon;
    document.getElementById('toast-msg').textContent  = msg;
    const t = document.getElementById('status-toast');
    t.classList.add('show');
    if (duration) setTimeout(() => t.classList.remove('show'), duration);
  }}
  function submitPin() {{
    const pin = document.getElementById('pin-input').value.trim();
    if (pin !== CORRECT_PIN) {{
      document.getElementById('pin-error').textContent = 'Incorrect PIN. Try again.';
      document.getElementById('pin-input').value = '';
      return;
    }}
    // Get token — from input or localStorage
    let token = localStorage.getItem(TOKEN_KEY) || '';
    const inputVal = document.getElementById('token-input').value.trim();
    if (inputVal && !inputVal.startsWith('•')) {{
      token = inputVal;
      localStorage.setItem(TOKEN_KEY, token);
    }}
    if (!token) {{
      document.getElementById('pin-error').textContent = 'Please enter your GitHub token.';
      document.getElementById('token-row').style.display = 'block';
      return;
    }}
    closeModal();
    const btn = document.getElementById('refresh-btn');
    btn.disabled = true;
    btn.innerHTML = '⏳ Starting scan…';
    showToast('⏳', 'Scan started — brief will update in ~10 minutes.', 0);
    fetch(`https://api.github.com/repos/${{REPO_OWNER}}/${{REPO_NAME}}/actions/workflows/${{WORKFLOW_FILE}}/dispatches`, {{
      method: 'POST',
      headers: {{
        'Authorization': `token ${{token}}`,
        'Accept': 'application/vnd.github.v3+json',
        'Content-Type': 'application/json'
      }},
      body: JSON.stringify({{ ref: 'main' }})
    }})
    .then(r => {{
      if (r.status === 204) {{
        showToast('✅', 'Scan running! Come back in ~10 min and refresh the page.', 0);
        btn.innerHTML = '✅ Scan running…';
        setTimeout(() => location.reload(), 12 * 60 * 1000);
      }} else {{
        r.text().then(t => {{
          if (r.status === 401) {{
            localStorage.removeItem(TOKEN_KEY);
            showToast('❌', 'Token rejected — please refresh and enter a valid token.', 8000);
          }} else {{
            showToast('❌', `Error ${{r.status}}: ${{t}}`, 8000);
          }}
        }});
        btn.disabled = false;
        btn.innerHTML = '🔄 Refresh Brief';
      }}
    }})
    .catch(e => {{
      showToast('❌', `Network error: ${{e.message}}`, 8000);
      btn.disabled = false;
      btn.innerHTML = '🔄 Refresh Brief';
    }});
  }}
  document.getElementById('refresh-modal').addEventListener('click', e => {{
    if (e.target === document.getElementById('refresh-modal')) closeModal();
  }});
</script>

<nav class="topbar">
  <div style="display:flex;align-items:center;gap:14px;">
    <span style="font-size:20px;font-weight:700;color:#6c63ff;">🎹 Creative Brief</span>
    <span style="background:#22263a;border:1px solid #2e3250;border-radius:20px;padding:3px 12px;font-size:12px;color:#8b90b5;">{date_str}</span>
  </div>
  <div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center;">
    <a href="#new-ads" class="pill active">New Ads</a>
    <a href="#leaderboard" class="pill">Leaderboard</a>
    <a href="#gap" class="pill">Gap Analysis</a>
    <a href="#briefs" class="pill">SP Briefs</a>
    <a href="#trends" class="pill">Trends</a>
    <a href="#watchlist" class="pill">Watchlist</a>
    {"<a href='#memo' class='pill'>Sunday Memo</a>" if sunday_memo else ""}
    <button id="refresh-btn" onclick="openModal()">🔄 Refresh Brief</button>
  </div>
</nav>

<div class="container">

  <div class="hero">
    <div class="hero-stat"><div class="num">{len(new_ads) if new_ads else len(ads)}</div><div class="label">{"New Ads Today" if new_ads else "Ads Collected"}</div></div>
    <div class="hero-stat"><div class="num">{total_brands}</div><div class="label">Brands Scanned</div></div>
    <div class="hero-stat"><div class="num">{len(leaderboard)}</div><div class="label">Long-Running Winners</div></div>
    <div class="hero-stat"><div class="num">{len(briefs)}</div><div class="label">SP Briefs Generated</div></div>
  </div>

  <!-- NEW ADS -->
  <div id="new-ads">
    <div class="section-header">
      <h2 style="font-size:18px;font-weight:600;">🆕 {"New Ads Found Today" if new_ads else "Ads Collected Today"}</h2>
      <span style="background:#22263a;border:1px solid #2e3250;border-radius:20px;padding:2px 10px;font-size:11px;color:#8b90b5;">{ads_section_label}</span>
    </div>
    <div class="ad-grid">{new_ads_html}</div>
  </div>

  <!-- LEADERBOARD -->
  <div id="leaderboard">
    <div class="section-header">
      <h2 style="font-size:18px;font-weight:600;">🏆 Longevity Leaderboard</h2>
      <span style="background:#22263a;border:1px solid #2e3250;border-radius:20px;padding:2px 10px;font-size:11px;color:#8b90b5;">30+ days = profitable signal</span>
    </div>
    <div style="display:flex;flex-direction:column;gap:10px;">{lb_html}</div>
  </div>

  <!-- GAP ANALYSIS -->
  <div id="gap">
    <div class="section-header">
      <h2 style="font-size:18px;font-weight:600;">🎯 SP Gap Analysis</h2>
      <span style="background:#22263a;border:1px solid #2e3250;border-radius:20px;padding:2px 10px;font-size:11px;color:#8b90b5;">vs competitor field</span>
    </div>
    {f'<div style="background:#22263a;border-radius:10px;padding:14px 18px;margin-bottom:20px;font-size:13px;color:#8b90b5;line-height:1.7;">{gap.get("summary","")}</div>' if gap.get("summary") else ""}
    <div class="gap-grid">
      <div>
        <div style="font-size:12px;color:#ff6584;font-weight:700;margin-bottom:12px;text-transform:uppercase;letter-spacing:0.5px;">⚠️ Angles SP Is Missing</div>
        {missing_html}
      </div>
      <div>
        <div style="font-size:12px;color:#3ecf8e;font-weight:700;margin-bottom:12px;text-transform:uppercase;letter-spacing:0.5px;">✅ Only SP Does This — Protect It</div>
        {unique_html}
      </div>
    </div>
  </div>

  <!-- CREATIVE BRIEFS -->
  <div id="briefs">
    <div class="section-header">
      <h2 style="font-size:18px;font-weight:600;">✍️ SP Creative Briefs</h2>
      <span style="background:#22263a;border:1px solid #2e3250;border-radius:20px;padding:2px 10px;font-size:11px;color:#8b90b5;">One per segment + 1 original idea</span>
    </div>
    <div class="briefs-grid">{briefs_html}</div>
  </div>

  <!-- TRENDS -->
  <div id="trends">
    <div class="section-header">
      <h2 style="font-size:18px;font-weight:600;">📈 Platform Trends</h2>
      <span style="background:#22263a;border:1px solid #2e3250;border-radius:20px;padding:2px 10px;font-size:11px;color:#8b90b5;">What's shifting this week</span>
    </div>
    <div class="trends-grid">{trends_html}</div>
  </div>

  <!-- WATCHLIST -->
  <div id="watchlist">
    <div class="section-header">
      <h2 style="font-size:18px;font-weight:600;">👁️ Brand Watchlist</h2>
      <span style="background:#22263a;border:1px solid #2e3250;border-radius:20px;padding:2px 10px;font-size:11px;color:#8b90b5;">Click to open live ad library</span>
    </div>
    {watchlist_html}
  </div>

  {memo_html}

</div>

<div style="margin-top:60px;border-top:1px solid #2e3250;padding:24px 32px;text-align:center;font-size:12px;color:#8b90b5;">
  Simply Piano Creative Brief · Generated {date_str} at 08:00 IL ·
  <a href="{config['settings']['github_pages_url']}" style="color:#6c63ff;text-decoration:none;">{config['settings']['github_pages_url']}</a>
</div>

</body>
</html>'''

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"[Brief Generator] index.html written ({len(html):,} chars)")
