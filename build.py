#!/usr/bin/env python3
"""
FLIRTY CHAT OPENERS
Production-ready, zero-dependency static website generator.

Run:
    python3 build.py

Input:
    data.csv

Output:
    dist/

Python:
    Python 3.9+

Features:
    - Editorial dark-mode responsive design
    - 18+ age verification
    - LocalStorage age approval
    - Full server-rendered SEO content
    - Live homepage search
    - Random opener navigation
    - Unique category counting
    - Name personalization
    - Individual copyable opener messages
    - Random message spotlight
    - Related content recommendations
    - Category pagination
    - Subcategory and tag hubs
    - Article, BreadcrumbList and FAQPage JSON-LD
    - Canonical and OpenGraph metadata
    - XML sitemap index and XSL stylesheet
    - Privacy, Terms, DMCA and 2257 pages
    - Google and Bing verification
    - Ten-site network footer
    - Current browser year and freshness labels
    - Build validation
"""

import csv
import html
import json
import math
import os
import random
import re
import shutil
import sys
import unicodedata

from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path
from urllib.parse import quote


# ============================================================
# 1. EXACT SITE CONFIGURATION
# ============================================================

BASE_URL = "https://flirty-chat-openers.velvetgrid.workers.dev"
SITE_NAME = "Flirty Chat Openers"
CONTACT_EMAIL = "nancympatten@gmail.com"
AFFILIATE_URL = "#affiliate-link"

CSV_FILE = "data.csv"
OUTPUT_DIR = "dist"

ITEMS_PER_CATEGORY_PAGE = 24
HOMEPAGE_ITEMS = 30
RELATED_ITEMS = 8
SITEMAP_URL_LIMIT = 45000

RATING_VERIFICATION = "RTA-5042-1996-1400-1577-RTA"

GOOGLE_VERIFICATION = (
    "Ee2L9A2G2nVVNtBt7HiplcBJf1nSen-Rcz4sNqLuAdc"
)

BING_VERIFICATION = "4573069C62AEC27DA4F08DC57760BAD4"

EXPECTED_COLUMNS = [
    "slug",
    "title",
    "category",
    "subcategory",
    "target_keyword",
    "openers_list",
    "follow_up_tips",
    "description",
    "tags",
    "faq_q1",
    "faq_a1",
    "faq_q2",
    "faq_a2",
    "upload_date",
]

TODAY = date.today().isoformat()
CURRENT_YEAR = date.today().year

MONTH_YEAR = date.today().strftime("%B %Y")


# ============================================================
# 2. GENERAL UTILITIES
# ============================================================

def esc(value):
    """Safely escape HTML."""
    return html.escape(str(value or ""), quote=True)


def clean_text(value):
    """Normalize whitespace."""
    return re.sub(r"\s+", " ", str(value or "")).strip()


def slugify(value):
    """Generate URL-safe slugs."""
    value = unicodedata.normalize("NFKD", str(value or ""))
    value = value.encode("ascii", "ignore").decode("ascii")
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = value.strip("-")
    return value or "general"


def truncate(value, limit=155):
    value = clean_text(value)

    if len(value) <= limit:
        return value

    return value[:limit].rsplit(" ", 1)[0].rstrip(" ,.-") + "..."


def canonical(path=""):
    path = str(path).lstrip("/")

    if not path:
        return BASE_URL.rstrip("/") + "/"

    return BASE_URL.rstrip("/") + "/" + path


def reading_time(text):
    words = len(str(text or "").split())
    return max(1, math.ceil(words / 200))


def parse_tags(value):
    if not value:
        return []

    result = []
    seen = set()

    for tag in re.split(r"[,;|]", str(value)):
        tag = clean_text(tag)

        if tag and tag.lower() not in seen:
            result.append(tag)
            seen.add(tag.lower())

    return result


def parse_openers(value):
    if not value:
        return []

    return [
        clean_text(item)
        for item in str(value).split("|")
        if clean_text(item)
    ]


def parse_date(value):
    value = clean_text(value)

    if not value:
        return date.min

    formats = [
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%d-%m-%Y",
        "%m/%d/%Y",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue

    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return date.min


def write_file(relative_path, content):
    path = Path(OUTPUT_DIR) / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)

    path.write_text(
        content,
        encoding="utf-8"
    )


def json_ld(data):
    serialized = json.dumps(
        data,
        ensure_ascii=False,
        separators=(",", ":")
    )

    serialized = (
        serialized
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
    )

    return (
        '<script type="application/ld+json">'
        + serialized
        + '</script>'
    )


# ============================================================
# 3. TEN-SITE NETWORK FOOTER
# ============================================================

NETWORK_FOOTER = """
<div style="background:#0d1018;border-top:1px solid #1f2433;padding:24px 16px;margin-top:40px;font-family:system-ui,-apple-system,sans-serif;text-align:center;">
  <p style="color:#9ca3af;font-size:12px;letter-spacing:1px;text-transform:uppercase;margin:0 0 12px 0;">Explore Our Interactive Network</p>
  <div style="display:flex;flex-wrap:wrap;justify-content:center;gap:8px;max-width:960px;margin:0 auto;">
    <a href="https://ai-girlfriend-prompts.velvetgrid.workers.dev" style="color:#c4b5fd;background:#161b28;padding:6px 12px;border-radius:6px;font-size:13px;text-decoration:none;border:1px solid #262d40;">AI Girlfriend Prompts</a>
    <a href="https://couples-intimacy-games.velvetgrid.workers.dev" style="color:#c4b5fd;background:#161b28;padding:6px 12px;border-radius:6px;font-size:13px;text-decoration:none;border:1px solid #262d40;">Couples Intimacy Games</a>
    <a href="https://fantasy-roleplay-hub.velvetgrid.workers.dev" style="color:#c4b5fd;background:#161b28;padding:6px 12px;border-radius:6px;font-size:13px;text-decoration:none;border:1px solid #262d40;">Fantasy Roleplay Hub</a>
    <a href="https://character-persona-hub.velvetgrid.workers.dev" style="color:#c4b5fd;background:#161b28;padding:6px 12px;border-radius:6px;font-size:13px;text-decoration:none;border:1px solid #262d40;">Character Persona Hub</a>
    <a href="https://flirty-chat-openers.velvetgrid.workers.dev" style="color:#c4b5fd;background:#161b28;padding:6px 12px;border-radius:6px;font-size:13px;text-decoration:none;border:1px solid #262d40;">Flirty Chat Openers</a>
    <a href="https://midnight-audio-stories.velvetgrid.workers.dev" style="color:#c4b5fd;background:#161b28;padding:6px 12px;border-radius:6px;font-size:13px;text-decoration:none;border:1px solid #262d40;">Midnight Audio Stories</a>
    <a href="https://spicy-party-games.velvetgrid.workers.dev" style="color:#c4b5fd;background:#161b28;padding:6px 12px;border-radius:6px;font-size:13px;text-decoration:none;border:1px solid #262d40;">Spicy Party Games</a>
    <a href="https://intimacy-quiz-hub.velvetgrid.workers.dev" style="color:#c4b5fd;background:#161b28;padding:6px 12px;border-radius:6px;font-size:13px;text-decoration:none;border:1px solid #262d40;">Intimacy Quiz Hub</a>
    <a href="https://couples-bucket-list.velvetgrid.workers.dev" style="color:#c4b5fd;background:#161b28;padding:6px 12px;border-radius:6px;font-size:13px;text-decoration:none;border:1px solid #262d40;">Couples Bucket List</a>
    <a href="https://adult-ai-art-prompts.velvetgrid.workers.dev" style="color:#c4b5fd;background:#161b28;padding:6px 12px;border-radius:6px;font-size:13px;text-decoration:none;border:1px solid #262d40;">Adult AI Art Prompts</a>
  </div>
</div>
"""


# ============================================================
# 4. EDITORIAL DESIGN SYSTEM
# ============================================================

CSS = r"""
:root {
    color-scheme: dark;

    --bg: #0b0d14;
    --surface: #131722;
    --surface-2: #191e2c;
    --surface-3: #202638;

    --pink: #ec4899;
    --violet: #8b5cf6;
    --rose-light: #f9a8d4;
    --purple-light: #c4b5fd;

    --text: #f4f4f8;
    --muted: #a4a9b8;
    --border: #292f40;
    --success: #34d399;

    --radius: 17px;
}

* {
    box-sizing: border-box;
}

html {
    scroll-behavior: smooth;
}

body {
    margin: 0;
    min-height: 100vh;
    background: var(--bg);
    color: var(--text);
    font-family: Inter, ui-sans-serif, system-ui,
        -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    line-height: 1.8;
}

a {
    color: inherit;
    text-decoration: none;
}

a:hover {
    color: var(--rose-light);
}

button,
input {
    font: inherit;
}

button {
    cursor: pointer;
}

.container {
    width: min(1120px, calc(100% - 36px));
    margin: 0 auto;
}

.navbar {
    position: sticky;
    top: 0;
    z-index: 100;
    background: rgba(11,13,20,.96);
    backdrop-filter: blur(15px);
    border-bottom: 1px solid var(--border);
}

.nav-inner {
    min-height: 72px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 18px;
}

.logo {
    font-size: 19px;
    font-weight: 850;
    letter-spacing: -.8px;
}

.logo span {
    color: var(--pink);
}

.age-badge {
    display: inline-block;
    padding: 3px 7px;
    margin-left: 5px;
    background: #ec489915;
    border: 1px solid #ec489955;
    color: #f9a8d4;
    font-size: 10px;
    font-weight: 800;
    border-radius: 5px;
    vertical-align: middle;
    letter-spacing: .4px;
}

.nav-links {
    display: flex;
    align-items: center;
    gap: 19px;
    color: var(--muted);
    font-size: 13px;
}

.btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    padding: 12px 18px;
    border: none;
    border-radius: 11px;
    background: linear-gradient(110deg,var(--pink),var(--violet));
    color: white;
    font-weight: 750;
    transition: .2s;
}

.btn:hover {
    color: white;
    transform: translateY(-2px);
    box-shadow: 0 8px 25px #ec489933;
}

.btn-secondary {
    background: var(--surface-2);
    border: 1px solid var(--border);
}

.hero {
    padding: 88px 0 72px;
    text-align: center;
    background:
        radial-gradient(ellipse at 18% 20%,#ec48991b,transparent 48%),
        radial-gradient(ellipse at 82% 28%,#8b5cf624,transparent 48%);
}

.eyebrow {
    display: inline-block;
    padding: 6px 13px;
    border: 1px solid #ec48994a;
    border-radius: 30px;
    background: #ec489912;
    color: var(--rose-light);
    font-size: 11px;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 1.1px;
}

.hero h1 {
    max-width: 850px;
    margin: 23px auto;
    font-size: clamp(36px,7vw,67px);
    line-height: 1.12;
    letter-spacing: -2.5px;
}

.gradient-text {
    background: linear-gradient(100deg,#f472b6,#a78bfa);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
}

.hero p {
    max-width: 680px;
    margin: 0 auto 30px;
    color: var(--muted);
    font-size: 16px;
}

.search-box {
    max-width: 680px;
    margin: 0 auto;
}

.search-box input {
    width: 100%;
    padding: 19px 22px;
    border-radius: 14px;
    border: 1px solid #353c50;
    background: var(--surface);
    color: white;
    outline: none;
}

.search-box input:focus {
    border-color: var(--pink);
    box-shadow: 0 0 0 4px #ec48991a;
}

.search-result {
    margin-top: 10px;
    color: var(--muted);
    font-size: 12px;
}

.section {
    padding: 42px 0;
}

.section-heading {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 12px;
    margin-bottom: 23px;
}

.section-heading h2 {
    margin: 0;
    font-size: clamp(23px,4vw,31px);
    letter-spacing: -.8px;
}

.grid {
    display: grid;
    grid-template-columns: repeat(3,minmax(0,1fr));
    gap: 17px;
}

.card {
    min-width: 0;
    padding: 22px;
    border-radius: var(--radius);
    border: 1px solid var(--border);
    background: var(--surface);
    transition: transform .2s,border-color .2s;
}

.card:hover {
    transform: translateY(-3px);
    border-color: #8b5cf677;
}

.card h3 {
    margin: 11px 0;
    font-size: 17px;
    line-height: 1.5;
}

.card p {
    color: var(--muted);
    font-size: 13px;
}

.category-count {
    color: var(--rose-light);
    font-size: 12px;
    font-weight: 750;
}

.pills {
    display: flex;
    flex-wrap: wrap;
    gap: 9px;
}

.pill {
    display: inline-block;
    padding: 6px 12px;
    border-radius: 30px;
    border: 1px solid #373e51;
    background: var(--surface-2);
    color: var(--purple-light);
    font-size: 12px;
}

.pill:hover {
    color: white;
    border-color: var(--pink);
}

.card-link {
    color: var(--rose-light);
    font-size: 13px;
    font-weight: 750;
}

.muted {
    color: var(--muted);
}

.detail-hero {
    padding: 58px 0 35px;
    background:
        radial-gradient(ellipse at 15% 15%,#ec489918,transparent 60%);
}

.detail-hero h1 {
    font-size: clamp(31px,6vw,49px);
    line-height: 1.2;
    letter-spacing: -1.5px;
}

.breadcrumb {
    margin-bottom: 20px;
    color: var(--muted);
    font-size: 12px;
}

.freshness {
    display: inline-block;
    padding: 6px 12px;
    margin: 12px 0;
    border: 1px solid #34d39944;
    border-radius: 30px;
    background: #34d39912;
    color: #6ee7b7;
    font-size: 12px;
    font-weight: 700;
}

.metadata {
    display: flex;
    flex-wrap: wrap;
    gap: 16px;
    color: var(--muted);
    font-size: 12px;
    margin: 17px 0;
}

.customizer {
    margin: 28px 0;
    padding: 25px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
}

.customizer h2 {
    margin-top: 0;
}

.input-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 15px;
}

.field label {
    display: block;
    margin-bottom: 7px;
    color: var(--muted);
    font-size: 12px;
}

.field input {
    width: 100%;
    padding: 13px;
    border: 1px solid var(--border);
    border-radius: 9px;
    background: #0b0d14;
    color: white;
    outline: none;
}

.field input:focus {
    border-color: var(--pink);
}

.opener-list {
    display: grid;
    gap: 15px;
}

.opener-card {
    padding: 21px;
    border: 1px solid var(--border);
    border-radius: 15px;
    background: linear-gradient(120deg,#171d2b,#131722);
}

.opener-number {
    display: inline-block;
    margin-bottom: 9px;
    color: var(--rose-light);
    font-size: 11px;
    font-weight: 800;
    letter-spacing: .8px;
    text-transform: uppercase;
}

.opener-text {
    margin: 0 0 17px;
    color: var(--text);
    font-size: 16px;
    line-height: 1.8;
    white-space: pre-wrap;
    overflow-wrap: anywhere;
}

.opener-actions {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
}

.copy-btn {
    padding: 9px 14px;
    border: 1px solid #494057;
    border-radius: 9px;
    background: #211a30;
    color: var(--rose-light);
    font-size: 12px;
    font-weight: 750;
}

.copy-btn.copied {
    color: var(--success);
    border-color: var(--success);
}

.spotlight {
    margin: 25px 0;
    padding: 26px;
    border: 1px solid #a855f755;
    border-radius: var(--radius);
    background: linear-gradient(120deg,#30172f,#211a3e);
}

.spotlight p {
    font-size: 19px;
    font-weight: 750;
}

.editorial-content {
    max-width: 850px;
    margin: 0 auto;
    padding: 30px 0;
}

.editorial-content h2 {
    font-size: 25px;
    letter-spacing: -.5px;
}

.editorial-content p {
    color: #c1c5d1;
    line-height: 1.95;
}

.strategy {
    margin: 25px 0;
    padding: 24px;
    border: 1px solid var(--border);
    border-radius: var(--radius);
    background: var(--surface);
}

.strategy summary {
    cursor: pointer;
    color: var(--rose-light);
    font-weight: 750;
}

.affiliate-box {
    margin: 28px 0;
    padding: 25px;
    border: 1px solid var(--border);
    border-radius: var(--radius);
    background: var(--surface);
    text-align: center;
}

.affiliate-link {
    display: inline-flex;
    padding: 13px 20px;
    border-radius: 10px;
    background: linear-gradient(110deg,var(--pink),var(--violet));
    color: white;
    font-weight: 750;
}

.affiliate-link:hover {
    color: white;
}

.faq-list {
    display: grid;
    gap: 12px;
}

.faq-item {
    padding: 19px;
    border: 1px solid var(--border);
    border-radius: 13px;
    background: var(--surface);
}

.faq-item summary {
    cursor: pointer;
    color: var(--rose-light);
    font-weight: 750;
}

.faq-item p {
    color: var(--muted);
}

.pagination {
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    gap: 9px;
    margin: 35px 0;
}

.pagination a {
    padding: 9px 15px;
    border: 1px solid var(--border);
    border-radius: 9px;
    background: var(--surface);
}

.pagination a.active {
    background: var(--pink);
    color: white;
}

.content-page {
    max-width: 850px;
    padding: 55px 0;
    margin: auto;
}

.content-page h1 {
    font-size: 37px;
}

.content-page h2 {
    margin-top: 32px;
    font-size: 22px;
}

.content-page p,
.content-page li {
    color: var(--muted);
}

.site-footer {
    margin-top: 50px;
    padding: 35px 0;
    border-top: 1px solid var(--border);
    color: var(--muted);
    font-size: 13px;
}

.footer-links {
    display: flex;
    flex-wrap: wrap;
    gap: 18px;
    margin: 18px 0;
}

.empty-state {
    padding: 35px;
    text-align: center;
    color: var(--muted);
    grid-column: 1/-1;
}

/* 18+ AGE VERIFICATION */

.age-overlay {
    position: fixed;
    inset: 0;
    z-index: 99999;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 20px;
    background: rgba(4,5,10,.96);
    backdrop-filter: blur(15px);
}

.age-dialog {
    width: min(470px,100%);
    padding: 34px 27px;
    border: 1px solid #3a304b;
    border-radius: 20px;
    background: #131722;
    box-shadow: 0 25px 100px #0009;
    text-align: center;
}

.age-icon {
    width: 65px;
    height: 65px;
    margin: 0 auto 18px;
    display: grid;
    place-items: center;
    border: 1px solid #ec489955;
    border-radius: 50%;
    background: #ec48991a;
    color: #f9a8d4;
    font-size: 24px;
    font-weight: 900;
}

.age-dialog h2 {
    margin: 0 0 15px;
    font-size: 25px;
}

.age-dialog p {
    color: var(--muted);
    font-size: 14px;
    line-height: 1.8;
}

.age-actions {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 11px;
    margin-top: 24px;
}

.age-actions button {
    min-height: 48px;
    border-radius: 10px;
    font-weight: 800;
}

.age-enter {
    border: 0;
    background: linear-gradient(110deg,var(--pink),var(--violet));
    color: white;
}

.age-exit {
    border: 1px solid var(--border);
    background: var(--surface-2);
    color: white;
}

body.age-locked {
    overflow: hidden;
}

@media(max-width:800px) {
    .grid {
        grid-template-columns: repeat(2,minmax(0,1fr));
    }

    .nav-links {
        gap: 11px;
    }
}

@media(max-width:560px) {
    .grid {
        grid-template-columns: 1fr;
    }

    .nav-inner {
        flex-wrap: wrap;
        padding: 12px 0;
    }

    .nav-links {
        width: 100%;
        justify-content: space-between;
    }

    .hero {
        padding: 62px 0 48px;
    }

    .input-grid {
        grid-template-columns: 1fr;
    }

    .age-dialog {
        padding: 28px 20px;
    }
}

@media(prefers-reduced-motion:reduce) {
    *,
    *::before,
    *::after {
        scroll-behavior: auto !important;
        transition-duration: .01ms !important;
    }
}
"""


# ============================================================
# 5. AGE VERIFICATION
# ============================================================

AGE_GATE_HTML = """
<div class="age-overlay"
     id="ageGate"
     role="dialog"
     aria-modal="true"
     aria-labelledby="ageTitle"
     aria-describedby="ageDescription"
     hidden>

  <div class="age-dialog">

    <div class="age-icon">18+</div>

    <h2 id="ageTitle">18+ Adults Only</h2>

    <p id="ageDescription">
      This website contains mature relationship and flirting
      content intended strictly for consenting adults aged
      18 and older.
    </p>

    <p>
      Please confirm that you are at least 18 years old
      before continuing.
    </p>

    <div class="age-actions">
      <button class="age-enter"
              type="button"
              id="ageEnter">
        I am 18+ (Enter)
      </button>

      <button class="age-exit"
              type="button"
              id="ageExit">
        Exit
      </button>
    </div>

  </div>
</div>
"""


AGE_GATE_JS = r"""
<script>
(function() {
    'use strict';

    const STORAGE_KEY = 'flirty_chat_openers_age_verified_v1';

    const gate = document.getElementById('ageGate');
    const enter = document.getElementById('ageEnter');
    const exit = document.getElementById('ageExit');

    if (!gate || !enter || !exit) return;

    /*
       Content remains fully server-rendered and available in the
       original HTML for every visitor and crawler.

       The age dialog is a client-side consent interface, not a
       crawler-specific content substitution mechanism.
    */

    let approved = false;

    try {
        approved = localStorage.getItem(STORAGE_KEY) === 'yes';
    } catch (error) {
        approved = false;
    }

    function showGate() {
        gate.hidden = false;
        document.body.classList.add('age-locked');

        window.setTimeout(function() {
            enter.focus();
        }, 50);
    }

    function hideGate() {
        gate.hidden = true;
        document.body.classList.remove('age-locked');
    }

    if (!approved) {
        showGate();
    } else {
        hideGate();
    }

    enter.addEventListener('click', function() {
        try {
            localStorage.setItem(STORAGE_KEY, 'yes');
        } catch (error) {
            // The current visit can still continue without storage.
        }

        hideGate();
    });

    exit.addEventListener('click', function() {
        window.location.replace('https://www.google.com');
    });

    gate.addEventListener('keydown', function(event) {
        if (event.key === 'Escape') {
            event.preventDefault();
        }
    });
})();
</script>
"""


# ============================================================
# 6. SHARED JAVASCRIPT
# ============================================================

GLOBAL_JS = r"""
<script>
(function() {
    'use strict';

    // Automatically update copyright and freshness year.
    document.querySelectorAll('.live-year').forEach(function(el) {
        el.textContent = new Date().getFullYear();
    });

    document.querySelectorAll('.live-month-year').forEach(function(el) {
        el.textContent = new Date().toLocaleDateString(
            undefined,
            {month: 'long', year: 'numeric'}
        );
    });

    // Random detail page navigation.
    const randomButtons = document.querySelectorAll(
        '[data-random-page]'
    );

    randomButtons.forEach(function(button) {
        button.addEventListener('click', function() {
            const pages = window.RANDOM_PAGES || [];

            if (!pages.length) return;

            const selected = pages[
                Math.floor(Math.random() * pages.length)
            ];

            window.location.href = selected;
        });
    });

    // Homepage live search.
    const search = document.getElementById('liveSearch');

    if (search) {
        const cards = Array.from(
            document.querySelectorAll('[data-search-card]')
        );

        const result = document.getElementById('searchResult');
        const empty = document.getElementById('noSearchResults');

        search.addEventListener('input', function() {
            const query = search.value.toLowerCase().trim();
            let visible = 0;

            cards.forEach(function(card) {
                const searchable = (
                    card.dataset.searchCard || ''
                ).toLowerCase();

                const matches = searchable.includes(query);

                card.hidden = !matches;

                if (matches) visible++;
            });

            if (result) {
                result.textContent = query
                    ? visible + ' matching collections found'
                    : 'Browse all available collections';
            }

            if (empty) {
                empty.hidden = visible !== 0;
            }
        });
    }

    // Clipboard functionality.
    document.querySelectorAll('[data-copy]').forEach(function(button) {
        button.addEventListener('click', async function() {
            const target = document.getElementById(
                button.dataset.copy
            );

            if (!target) return;

            const original = button.textContent;
            const text = target.textContent;

            try {
                if (navigator.clipboard && window.isSecureContext) {
                    await navigator.clipboard.writeText(text);
                } else {
                    const area = document.createElement('textarea');

                    area.value = text;
                    area.style.position = 'fixed';
                    area.style.opacity = '0';

                    document.body.appendChild(area);
                    area.select();

                    const success = document.execCommand('copy');

                    area.remove();

                    if (!success) {
                        throw new Error('Clipboard unavailable');
                    }
                }

                button.textContent = 'Copied!';
                button.classList.add('copied');

                setTimeout(function() {
                    button.textContent = original;
                    button.classList.remove('copied');
                }, 1600);

            } catch (error) {
                button.textContent = 'Copy unavailable';

                setTimeout(function() {
                    button.textContent = original;
                }, 1600);
            }
        });
    });

    // Name personalization.
    const crushInput = document.getElementById('crushName');
    const yourInput = document.getElementById('yourName');

    function personalize() {
        const crush = crushInput
            ? crushInput.value.trim()
            : '';

        const yourName = yourInput
            ? yourInput.value.trim()
            : '';

        document.querySelectorAll('.opener-text').forEach(function(el) {
            const original = el.dataset.original || '';

            const personalized = original
                .replace(/\[Crush Name\]/gi, crush || 'you')
                .replace(/\[Your Name\]/gi, yourName || 'me')
                .replace(/\{Crush Name\}/gi, crush || 'you')
                .replace(/\{Your Name\}/gi, yourName || 'me');

            el.textContent = personalized;
        });
    }

    if (crushInput) {
        crushInput.addEventListener('input', personalize);
    }

    if (yourInput) {
        yourInput.addEventListener('input', personalize);
    }

    // Random individual message spotlight.
    const randomLineButton = document.getElementById(
        'pickRandomLine'
    );

    if (randomLineButton) {
        randomLineButton.addEventListener('click', function() {
            const lines = Array.from(
                document.querySelectorAll('.opener-text')
            );

            if (!lines.length) return;

            const selected = lines[
                Math.floor(Math.random() * lines.length)
            ];

            const spotlight = document.getElementById(
                'spotlightText'
            );

            spotlight.textContent = selected.textContent;

            const section = document.getElementById('spotlight');

            if (section) {
                section.scrollIntoView({
                    behavior: 'smooth',
                    block: 'center'
                });
            }
        });
    }
})();
</script>
"""


# ============================================================
# 7. NAVIGATION AND PAGE TEMPLATE
# ============================================================

def navigation():

    return """
    <header class="navbar">
      <div class="container nav-inner">

        <a href="/" class="logo">
          Flirty<span>Chat</span> 💗
          <span class="age-badge">18+</span>
        </a>

        <nav class="nav-links" aria-label="Main navigation">
          <a href="/">Home</a>
          <a href="/#categories">Categories</a>

          <button class="btn"
                  type="button"
                  data-random-page>
            🎲 Random Opener
          </button>
        </nav>

      </div>
    </header>
    """


def page_footer():

    return f"""
    <footer class="site-footer">

      <div class="container">

        <div class="footer-links">
          <a href="/privacy.html">Privacy Policy</a>
          <a href="/terms.html">Terms of Use</a>
          <a href="/dmca.html">DMCA</a>
          <a href="/2257.html">2257 Statement</a>
          <a href="mailto:{esc(CONTACT_EMAIL)}">Contact</a>
        </div>

        <p>
          <span class="age-badge">18+ ADULTS ONLY</span>
        </p>

        <p>
          © <span class="live-year">{CURRENT_YEAR}</span>
          {SITE_NAME}. All rights reserved.
        </p>

        <p>
          Thoughtful conversation starters for meaningful,
          respectful connections between consenting adults.
        </p>

      </div>

    </footer>

    {NETWORK_FOOTER}
    """


def page_template(
    title,
    description,
    path,
    content,
    extra_head="",
    extra_scripts="",
    robots="index,follow",
    page_type="website"
):

    page_url = canonical(path)

    head = f"""
    <meta charset="UTF-8">

    <meta name="viewport"
          content="width=device-width, initial-scale=1">

    <meta name="robots" content="{esc(robots)}">

    <meta name="description"
          content="{esc(description)}">

    <meta name="theme-color" content="#0b0d14">

    <meta name="rating"
          content="RTA-5042-1996-1400-1577-RTA" />

    <meta name="google-site-verification"
          content="Ee2L9A2G2nVVNtBt7HiplcBJf1nSen-Rcz4sNqLuAdc" />

    <meta name="msvalidate.01"
          content="4573069C62AEC27DA4F08DC57760BAD4" />

    <link rel="canonical"
          href="{esc(page_url)}">

    <meta property="og:type"
          content="{esc(page_type)}">

    <meta property="og:site_name"
          content="{esc(SITE_NAME)}">

    <meta property="og:title"
          content="{esc(title)}">

    <meta property="og:description"
          content="{esc(description)}">

    <meta property="og:url"
          content="{esc(page_url)}">

    <meta property="og:locale"
          content="en_US">

    <meta name="twitter:card"
          content="summary">

    <meta name="twitter:title"
          content="{esc(title)}">

    <meta name="twitter:description"
          content="{esc(description)}">

    <title>{esc(title)}</title>

    <style>
    {CSS}
    </style>

    {extra_head}
    """

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
{head}
</head>

<body>

{navigation()}

{content}

{page_footer()}

{AGE_GATE_HTML}

<script>
window.RANDOM_PAGES = {json.dumps(RANDOM_PAGE_URLS)};
</script>

{GLOBAL_JS}

{AGE_GATE_JS}

{extra_scripts}

</body>
</html>
"""


# ============================================================
# 8. CSV LOADER
# ============================================================

def load_data():

    csv_path = Path(CSV_FILE)

    if not csv_path.exists():
        raise FileNotFoundError(
            f"{CSV_FILE} not found. "
            "Place data.csv beside build.py."
        )

    records = []

    with csv_path.open(
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as file:

        reader = csv.DictReader(file)

        if not reader.fieldnames:
            raise ValueError("CSV header row is missing.")

        reader.fieldnames = [
            clean_text(name)
            for name in reader.fieldnames
        ]

        missing = [
            column
            for column in EXPECTED_COLUMNS
            if column not in reader.fieldnames
        ]

        if missing:
            raise ValueError(
                "Missing required CSV columns: "
                + ", ".join(missing)
            )

        used_slugs = set()

        for line_number, original in enumerate(reader, start=2):

            row = {
                column: clean_text(original.get(column, ""))
                for column in EXPECTED_COLUMNS
            }

            if not row["title"] or not row["openers_list"]:
                print(
                    f"WARNING: Skipping incomplete row {line_number}"
                )
                continue

            base_slug = slugify(
                row["slug"] or row["title"]
            )

            slug = base_slug
            suffix = 2

            while slug in used_slugs:
                slug = f"{base_slug}-{suffix}"
                suffix += 1

            used_slugs.add(slug)

            row["slug"] = slug

            row["tags_list"] = parse_tags(
                row["tags"]
            )

            row["openers"] = parse_openers(
                row["openers_list"]
            )

            row["sort_date"] = parse_date(
                row["upload_date"]
            )

            if not row["category"]:
                row["category"] = "General"

            if not row["subcategory"]:
                row["subcategory"] = "General"

            if not row["target_keyword"]:
                row["target_keyword"] = row["title"]

            if not row["description"]:
                row["description"] = (
                    f"Explore {row['title']}, featuring "
                    f"creative flirty chat openers and "
                    f"conversation ideas."
                )

            records.append(row)

    if not records:
        raise ValueError(
            "No valid content records found in data.csv."
        )

    return records


# ============================================================
# 9. CONTENT INDEXES
# ============================================================

def build_indexes(records):

    categories = defaultdict(list)
    subcategories = defaultdict(list)
    tags = defaultdict(list)

    tag_display = {}
    subcategory_display = {}

    category_counter = Counter(
        row["category"]
        for row in records
    )

    for row in records:

        categories[row["category"]].append(row)

        subcategories[row["subcategory"]].append(row)

        subcategory_display[
            slugify(row["subcategory"])
        ] = row["subcategory"]

        for tag in row["tags_list"]:

            key = slugify(tag)

            tags[key].append(row)

            tag_display[key] = tag

    return (
        categories,
        subcategories,
        tags,
        tag_display,
        subcategory_display,
        category_counter
    )


# ============================================================
# 10. CONTENT CARDS
# ============================================================

def opener_card(row):

    searchable = " ".join([
        row["title"],
        row["target_keyword"],
        row["tags"],
    ]).lower()

    minutes = reading_time(
        row["description"] + " " + row["openers_list"]
    )

    return f"""
    <article class="card"
             data-search-card="{esc(searchable)}">

      <div class="pills">
        <span class="pill">{esc(row["category"])}</span>
      </div>

      <h3>
        <a href="/lines/{esc(row["slug"])}.html">
          {esc(row["target_keyword"])}
        </a>
      </h3>

      <p>{esc(truncate(row["description"], 145))}</p>

      <div class="metadata">
        <span>{len(row["openers"])} messages</span>
        <span>{minutes} min read</span>
      </div>

      <a class="card-link"
         href="/lines/{esc(row["slug"])}.html">
        Explore openers →
      </a>

    </article>
    """


def category_card(name, items):

    return f"""
    <a class="card"
       href="/category/{slugify(name)}/page-1.html">

      <span class="category-count">
        {len(items)} collections
      </span>

      <h3>{esc(name)}</h3>

      <p>
        Explore conversation starters, thoughtful
        messages and creative ideas.
      </p>

      <span class="card-link">
        Browse category →
      </span>

    </a>
    """


def tag_pill(tag):

    return (
        f'<a class="pill" href="/tag/{slugify(tag)}.html">'
        f'{esc(tag)}</a>'
    )


# ============================================================
# 11. HOMEPAGE
# ============================================================

def build_home(
    records,
    categories,
    tags,
    tag_display,
    subcategories,
    subcategory_display,
    category_counter
):

    newest = sorted(
        records,
        key=lambda row: (
            row["sort_date"],
            row["title"].lower()
        ),
        reverse=True
    )[:HOMEPAGE_ITEMS]

    # Counter guarantees one card per unique category.
    category_html = "".join(
        category_card(
            category,
            categories[category]
        )
        for category, count in sorted(
            category_counter.items(),
            key=lambda item: item[0].lower()
        )
    )

    tag_counts = Counter({
        tag: len(items)
        for tag, items in tags.items()
    })

    popular_tags = sorted(
        tag_counts.items(),
        key=lambda item: (-item[1], item[0])
    )[:25]

    tag_html = "".join(
        tag_pill(tag_display[tag])
        for tag, count in popular_tags
        if tag in tag_display
    )

    popular_subcategories = sorted(
        subcategories.items(),
        key=lambda item: (-len(item[1]), item[0].lower())
    )[:25]

    subcategory_html = "".join(
        f'<a class="pill" href="/topic/{slugify(name)}.html">'
        f'{esc(name)} ({len(items)})</a>'
        for name, items in popular_subcategories
    )

    newest_html = "".join(
        opener_card(row)
        for row in newest
    )

    content = f"""
    <main>

      <section class="hero">

        <div class="container">

          <span class="eyebrow">
            18+ Adults Only · Better Conversations Begin Here
          </span>

          <h1>
            Start Something
            <span class="gradient-text">Worth Talking About.</span>
          </h1>

          <p>
            Discover playful, charming and thoughtful flirty
            chat openers. Find your words, personalize your
            messages and start more meaningful conversations.
          </p>

          <div class="search-box">

            <input
              type="search"
              id="liveSearch"
              placeholder="Search titles, keywords or tags..."
              aria-label="Search flirty chat openers"
              autocomplete="off"
            >

            <div class="search-result" id="searchResult">
              Browse all {len(records)} available collections.
            </div>

          </div>

          <div style="margin-top:24px;display:flex;gap:12px;
                      justify-content:center;flex-wrap:wrap;">

            <button class="btn"
                    type="button"
                    data-random-page>
              🎲 Get a Random Opener
            </button>

            <a class="btn btn-secondary"
               href="#categories">
              Explore Categories
            </a>

          </div>

        </div>

      </section>

      <section class="section" id="categories">

        <div class="container">

          <div class="section-heading">
            <h2>Explore Categories</h2>

            <span class="muted">
              {len(category_counter)} unique categories
            </span>
          </div>

          <div class="grid">
            {category_html}
          </div>

        </div>

      </section>

      <section class="section">

        <div class="container">

          <div class="section-heading">
            <h2>Popular Subcategories</h2>
          </div>

          <div class="pills">
            {subcategory_html}
          </div>

        </div>

      </section>

      <section class="section">

        <div class="container">

          <div class="section-heading">
            <h2>Popular Tags</h2>
          </div>

          <div class="pills">
            {tag_html}
          </div>

        </div>

      </section>

      <!-- AD_SLOT_TOP_BANNER -->

      <section class="section">

        <div class="container">

          <div class="section-heading">

            <h2>Latest Conversation Guides</h2>

            <span class="muted">
              {len(newest)} newest collections
            </span>

          </div>

          <div class="grid">
            {newest_html}
          </div>

          <div id="noSearchResults"
               class="empty-state"
               hidden>
            No matching collections found.
            Try another keyword or tag.
          </div>

        </div>

      </section>

      <!-- AD_SLOT_MID_CONTENT -->

      <section class="section">

        <div class="container">

          <div class="card">

            <h2>
              Good Conversations Start With Genuine Interest
            </h2>

            <p>
              A thoughtful opener is only the beginning.
              Pay attention to the other person's responses,
              ask natural follow-up questions and allow
              conversations to develop at a comfortable pace.
              Respect, honesty and mutual interest matter
              more than any perfect opening line.
            </p>

            <a class="btn"
               href="#categories">
              Discover More Guides
            </a>

          </div>

        </div>

      </section>

    </main>

    <!-- AD_SLOT_POPUNDER -->
    <!-- AD_SLOT_BOTTOM_BANNER -->
    """

    page = page_template(
        f"{SITE_NAME} | Flirty Chat Openers & Conversation Guides",
        "Discover thoughtful, playful and charming flirty chat "
        "openers. Browse conversation guides, personalize messages "
        "and explore creative adult relationship conversation ideas.",
        "",
        content
    )

    write_file("index.html", page)


# ============================================================
# 12. DETAIL PAGE STRUCTURED DATA
# ============================================================

def detail_structured_data(row):

    page_url = canonical(
        f"lines/{row['slug']}.html"
    )

    breadcrumbs = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": 1,
                "name": "Home",
                "item": canonical(),
            },
            {
                "@type": "ListItem",
                "position": 2,
                "name": row["category"],
                "item": canonical(
                    f"category/{slugify(row['category'])}/page-1.html"
                ),
            },
            {
                "@type": "ListItem",
                "position": 3,
                "name": row["title"],
                "item": page_url,
            },
        ],
    }

    article = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": row["target_keyword"],
        "description": truncate(row["description"], 300),
        "mainEntityOfPage": {
            "@type": "WebPage",
            "@id": page_url,
        },
        "url": page_url,
        "datePublished": (
            row["upload_date"][:10]
            if row["upload_date"]
            else TODAY
        ),
        "dateModified": TODAY,
        "author": {
            "@type": "Organization",
            "name": SITE_NAME,
            "url": canonical(),
        },
        "publisher": {
            "@type": "Organization",
            "name": SITE_NAME,
            "url": canonical(),
        },
        "articleSection": row["category"],
        "keywords": ", ".join(
            [row["target_keyword"]] + row["tags_list"]
        ),
        "inLanguage": "en",
    }

    questions = []

    for question, answer in [
        (row["faq_q1"], row["faq_a1"]),
        (row["faq_q2"], row["faq_a2"]),
    ]:

        if question and answer:
            questions.append({
                "@type": "Question",
                "name": question,
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": answer,
                },
            })

    # Ensure every detail page has an FAQPage schema.
    if not questions:
        questions = [
            {
                "@type": "Question",
                "name": "How can I personalize these conversation starters?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": (
                        "Use the name personalizer to replace "
                        "supported name placeholders before "
                        "copying a message."
                    ),
                },
            },
            {
                "@type": "Question",
                "name": "How should I use these openers?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": (
                        "Choose a message that feels natural, "
                        "communicate respectfully and pay attention "
                        "to the other person's comfort and interest."
                    ),
                },
            },
        ]

    faq = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": questions,
    }

    return "\n".join([
        json_ld(article),
        json_ld(breadcrumbs),
        json_ld(faq),
    ])


# ============================================================
# 13. RELATED CONVERSATION GUIDES
# ============================================================

def get_related(row, records):

    current_tags = {
        slugify(tag)
        for tag in row["tags_list"]
    }

    scored = []

    for candidate in records:

        if candidate["slug"] == row["slug"]:
            continue

        score = 0

        if (
            candidate["subcategory"].lower()
            == row["subcategory"].lower()
        ):
            score += 6

        if (
            candidate["category"].lower()
            == row["category"].lower()
        ):
            score += 2

        candidate_tags = {
            slugify(tag)
            for tag in candidate["tags_list"]
        }

        shared_tags = len(
            current_tags & candidate_tags
        )

        score += shared_tags * 3

        if score > 0:
            scored.append((score, candidate))

    scored.sort(
        key=lambda item: (
            -item[0],
            item[1]["title"].lower()
        )
    )

    related = [
        item[1]
        for item in scored[:RELATED_ITEMS]
    ]

    selected = {
        item["slug"]
        for item in related
    }

    if len(related) < RELATED_ITEMS:

        for candidate in records:

            if candidate["slug"] == row["slug"]:
                continue

            if candidate["slug"] in selected:
                continue

            related.append(candidate)
            selected.add(candidate["slug"])

            if len(related) >= RELATED_ITEMS:
                break

    return related


# ============================================================
# 14. DETAIL PAGES
# ============================================================

def build_detail(row, records):

    opener_html = []

    for index, opener in enumerate(row["openers"], start=1):

        opener_id = f"opener-{index}"

        opener_html.append(f"""
        <article class="opener-card">

          <span class="opener-number">
            MESSAGE #{index}
          </span>

          <p class="opener-text"
             id="{opener_id}"
             data-original="{esc(opener)}">{esc(opener)}</p>

          <div class="opener-actions">

            <span class="muted">
              Conversation starter {index}
            </span>

            <button class="copy-btn"
                    type="button"
                    data-copy="{opener_id}">
              Copy Message
            </button>

          </div>

        </article>
        """)

    related = get_related(row, records)

    related_html = "".join(
        f"""
        <article class="card">

          <span class="pill">
            {esc(item["category"])}
          </span>

          <h3>
            <a href="/lines/{esc(item["slug"])}.html">
              {esc(item["title"])}
            </a>
          </h3>

          <p>
            {esc(truncate(item["description"], 110))}
          </p>

          <span class="category-count">
            {len(item["openers"])} messages
          </span>

          <p>
            <a class="card-link"
               href="/lines/{esc(item["slug"])}.html">
              Explore guide →
            </a>
          </p>

        </article>
        """
        for item in related
    )

    tags_html = "".join(
        tag_pill(tag)
        for tag in row["tags_list"]
    )

    category_link = (
        f"/category/{slugify(row['category'])}/page-1.html"
    )

    topic_link = (
        f"/topic/{slugify(row['subcategory'])}.html"
    )

    questions = []

    for question, answer in [
        (row["faq_q1"], row["faq_a1"]),
        (row["faq_q2"], row["faq_a2"]),
    ]:

        if question and answer:
            questions.append((question, answer))

    if not questions:

        questions = [
            (
                "How can I personalize these flirty openers?",
                "Enter the names in the personalizer above. "
                "Supported placeholders update automatically "
                "as you type."
            ),
            (
                "How do I choose the right conversation starter?",
                "Choose a message that matches your personality "
                "and the context of the conversation. Keep your "
                "approach natural, respectful and considerate."
            ),
        ]

    faq_html = "".join(
        f"""
        <details class="faq-item">
          <summary>{esc(question)}</summary>
          <p>{esc(answer)}</p>
        </details>
        """
        for question, answer in questions
    )

    minutes = reading_time(
        row["description"]
        + row["follow_up_tips"]
        + row["openers_list"]
    )

    content = f"""
    <main>

      <section class="detail-hero">

        <div class="container">

          <div class="breadcrumb">

            <a href="/">Home</a>
            /
            <a href="{category_link}">
              {esc(row["category"])}
            </a>
            /
            <a href="{topic_link}">
              {esc(row["subcategory"])}
            </a>
            /
            {esc(row["title"])}

          </div>

          <span class="eyebrow">
            {esc(row["category"])}
          </span>

          <h1>{esc(row["target_keyword"])}</h1>

          <div class="freshness">
            Updated for
            <span class="live-month-year">{MONTH_YEAR}</span>
          </div>

          <div class="metadata">

            <span>
              {len(row["openers"])} individual messages
            </span>

            <span>
              {minutes} min read
            </span>

            <span>
              {esc(row["subcategory"])}
            </span>

          </div>

          <div class="pills">

            <a class="pill" href="{category_link}">
              {esc(row["category"])}
            </a>

            <a class="pill" href="{topic_link}">
              {esc(row["subcategory"])}
            </a>

            {tags_html}

          </div>

        </div>

      </section>

      <div class="container">

        <!-- AD_SLOT_TOP_BANNER -->

        <section class="customizer">

          <h2>💗 Name Personalizer</h2>

          <p class="muted">
            Add names to personalize supported placeholders
            in every message. Your entries are processed
            locally in your browser.
          </p>

          <div class="input-grid">

            <div class="field">

              <label for="crushName">
                Crush Name
              </label>

              <input
                id="crushName"
                type="text"
                maxlength="60"
                placeholder="Enter their name"
                autocomplete="off"
              >

            </div>

            <div class="field">

              <label for="yourName">
                Your Name
              </label>

              <input
                id="yourName"
                type="text"
                maxlength="60"
                placeholder="Enter your name"
                autocomplete="off"
              >

            </div>

          </div>

        </section>

        <section class="section">

          <div class="section-heading">

            <h2>Conversation Starter Collection</h2>

            <span class="muted">
              {len(row["openers"])} messages
            </span>

          </div>

          <div class="spotlight" id="spotlight">

            <span class="eyebrow">
              Random Message Spotlight
            </span>

            <p id="spotlightText">
              Discover a random message from this collection.
            </p>

            <button class="btn"
                    type="button"
                    id="pickRandomLine">
              ✨ Spotlight Random Line
            </button>

          </div>

          <div class="opener-list">
            {"".join(opener_html)}
          </div>

        </section>

        <!-- AD_SLOT_MID_CONTENT -->

        <section class="editorial-content">

          <h2>About This Conversation Guide</h2>

          <p>
            {esc(row["description"])}
          </p>

          <h2>
            Conversation &amp; Follow-Up Guide
          </h2>

          <p>
            {esc(row["follow_up_tips"]) if row["follow_up_tips"]
            else "After sending an opener, give the other person "
            "space to respond naturally. Ask relevant questions, "
            "listen carefully, and let the conversation develop "
            "at a comfortable pace. Genuine interest and mutual "
            "respect are more important than scripted responses."}
          </p>

          <p>
            Remember that a good conversation is a shared
            experience. Avoid sending repeated messages when
            someone does not respond, and respect boundaries
            and personal preferences.
          </p>

        </section>

        <details class="strategy">

          <summary>
            💡 Expand the Follow-Up Strategy
          </summary>

          <div class="editorial-content">

            <p>
              Start by responding naturally to the other
              person's message. Reference something they
              shared instead of immediately changing the
              subject.
            </p>

            <p>
              Keep questions open-ended when appropriate,
              balance talking with listening and allow
              the conversation to develop mutually.
            </p>

            <p>
              If interest is not mutual, respond graciously
              and move on respectfully.
            </p>

          </div>

        </details>

        <section class="affiliate-box">

          <h2>Discover More Conversation Ideas</h2>

          <p class="muted">
            Explore additional resources and ideas for
            making conversations more engaging.
          </p>

          <a class="affiliate-link"
             href="{esc(AFFILIATE_URL)}"
             rel="nofollow sponsored">
            Explore More Resources →
          </a>

        </section>

        <section class="section">

          <div class="section-heading">
            <h2>Frequently Asked Questions</h2>
          </div>

          <div class="faq-list">
            {faq_html}
          </div>

        </section>

        <section class="section">

          <div class="section-heading">
            <h2>Related Conversation Guides</h2>
          </div>

          <div class="grid">
            {related_html}
          </div>

        </section>

      </div>

    </main>

    <!-- AD_SLOT_POPUNDER -->
    <!-- AD_SLOT_BOTTOM_BANNER -->
    """

    schema = detail_structured_data(row)

    page = page_template(
        f"{row['target_keyword']} | {SITE_NAME}",
        truncate(row["description"], 155),
        f"lines/{row['slug']}.html",
        content,
        extra_head=schema,
        page_type="article"
    )

    write_file(
        f"lines/{row['slug']}.html",
        page
    )


# ============================================================
# 15. CATEGORY HUBS AND PAGINATION
# ============================================================

def build_category_pages(categories):

    for category, items in categories.items():

        items = sorted(
            items,
            key=lambda row: row["title"].lower()
        )

        total_pages = max(
            1,
            math.ceil(
                len(items) / ITEMS_PER_CATEGORY_PAGE
            )
        )

        category_slug = slugify(category)

        for page_number in range(1, total_pages + 1):

            start = (
                page_number - 1
            ) * ITEMS_PER_CATEGORY_PAGE

            page_items = items[
                start:start + ITEMS_PER_CATEGORY_PAGE
            ]

            cards = "".join(
                opener_card(row)
                for row in page_items
            )

            pagination = []

            if page_number > 1:

                pagination.append(
                    f'<a href="/category/{category_slug}/'
                    f'page-{page_number - 1}.html">'
                    f'← Previous</a>'
                )

            for number in range(1, total_pages + 1):

                active = (
                    "active"
                    if number == page_number
                    else ""
                )

                pagination.append(
                    f'<a class="{active}" href="/category/'
                    f'{category_slug}/page-{number}.html">'
                    f'{number}</a>'
                )

            if page_number < total_pages:

                pagination.append(
                    f'<a href="/category/{category_slug}/'
                    f'page-{page_number + 1}.html">'
                    f'Next →</a>'
                )

            extra_head = ""

            if page_number > 1:

                extra_head += (
                    '<link rel="prev" href="'
                    + esc(canonical(
                        f"category/{category_slug}/"
                        f"page-{page_number - 1}.html"
                    ))
                    + '">'
                )

            if page_number < total_pages:

                extra_head += (
                    '<link rel="next" href="'
                    + esc(canonical(
                        f"category/{category_slug}/"
                        f"page-{page_number + 1}.html"
                    ))
                    + '">'
                )

            content = f"""
            <main class="container section">

              <div class="breadcrumb">
                <a href="/">Home</a> /
                Categories / {esc(category)}
              </div>

              <span class="eyebrow">
                Conversation Collection
              </span>

              <h1>{esc(category)} Flirty Chat Openers</h1>

              <p class="muted">
                Browse {len(items)} conversation collections
                covering {esc(category)}.
                Page {page_number} of {total_pages}.
              </p>

              <div class="grid">
                {cards}
              </div>

              <nav class="pagination"
                   aria-label="Category pagination">
                {"".join(pagination)}
              </nav>

            </main>
            """

            page = page_template(
                f"{category} Flirty Chat Openers | Page {page_number}",
                f"Browse {len(items)} flirty chat opener collections "
                f"in {category}. Explore messages and conversation "
                f"guides.",
                f"category/{category_slug}/page-{page_number}.html",
                content,
                extra_head=extra_head
            )

            write_file(
                f"category/{category_slug}/page-{page_number}.html",
                page
            )


# ============================================================
# 16. SUBCATEGORY HUBS
# ============================================================

def build_subcategory_pages(subcategories):

    for subcategory, items in subcategories.items():

        cards = "".join(
            opener_card(row)
            for row in items
        )

        content = f"""
        <main class="container section">

          <div class="breadcrumb">
            <a href="/">Home</a> /
            Topics / {esc(subcategory)}
          </div>

          <span class="eyebrow">Topic Collection</span>

          <h1>{esc(subcategory)} Conversation Guides</h1>

          <p class="muted">
            Discover {len(items)} curated collections
            related to {esc(subcategory)}.
          </p>

          <div class="grid">
            {cards}
          </div>

        </main>
        """

        page = page_template(
            f"{subcategory} Conversation Guides | {SITE_NAME}",
            f"Explore {len(items)} collections of "
            f"{subcategory} flirty chat openers.",
            f"topic/{slugify(subcategory)}.html",
            content
        )

        write_file(
            f"topic/{slugify(subcategory)}.html",
            page
        )


# ============================================================
# 17. TAG HUBS
# ============================================================

def build_tag_pages(tags, tag_display):

    for tag_slug, items in tags.items():

        tag = tag_display.get(
            tag_slug,
            tag_slug
        )

        cards = "".join(
            opener_card(row)
            for row in items
        )

        content = f"""
        <main class="container section">

          <div class="breadcrumb">
            <a href="/">Home</a> /
            Tags / {esc(tag)}
          </div>

          <span class="eyebrow">
            Tagged Conversation Collection
          </span>

          <h1>{esc(tag)} Flirty Chat Openers</h1>

          <p class="muted">
            Browse {len(items)} collections related to
            {esc(tag)}.
          </p>

          <div class="grid">
            {cards}
          </div>

        </main>
        """

        page = page_template(
            f"{tag} Flirty Chat Openers | {SITE_NAME}",
            f"Discover {len(items)} conversation starter "
            f"collections about {tag}.",
            f"tag/{tag_slug}.html",
            content
        )

        write_file(
            f"tag/{tag_slug}.html",
            page
        )


# ============================================================
# 18. LEGAL PAGES
# ============================================================

LEGAL_PAGES = {

    "privacy.html": {
        "title": "Privacy Policy",
        "description": "Privacy policy for Flirty Chat Openers.",
        "body": """
        <h1>Privacy Policy</h1>

        <p>Last updated: CURRENT_DATE</p>

        <h2>Introduction</h2>

        <p>
        Flirty Chat Openers respects the privacy of its visitors.
        This policy describes how information may be handled
        when you access this website.
        </p>

        <h2>Website Functionality</h2>

        <p>
        The website provides static informational content.
        Search, random selection and name personalization
        features operate in your browser.
        </p>

        <h2>Age Verification Storage</h2>

        <p>
        The website may store an age-verification approval
        indicator in your browser's local storage.
        This helps remember your decision between visits.
        </p>

        <h2>Cookies and Third Parties</h2>

        <p>
        Third-party advertising, analytics and affiliate
        providers may use cookies or similar technologies.
        Their practices are governed by their respective
        privacy policies.
        </p>

        <h2>External Links</h2>

        <p>
        This website may link to external services.
        We do not control the privacy policies or practices
        of independent third-party websites.
        </p>

        <h2>Contact</h2>

        <p>
        For privacy-related questions, contact:
        CONTACT_EMAIL
        </p>
        """
    },

    "terms.html": {
        "title": "Terms of Use",
        "description": "Terms and conditions of Flirty Chat Openers.",
        "body": """
        <h1>Terms of Use</h1>

        <p>Last updated: CURRENT_DATE</p>

        <h2>Acceptance of Terms</h2>

        <p>
        By accessing this website, you agree to use its
        content responsibly and in accordance with
        applicable laws.
        </p>

        <h2>Intended Audience</h2>

        <p>
        This website is intended strictly for adults
        aged 18 and older.
        </p>

        <h2>Content and Entertainment</h2>

        <p>
        Conversation starters and relationship-oriented
        material are provided for general informational
        and entertainment purposes.
        No particular communication outcome is guaranteed.
        </p>

        <h2>Responsible Communication</h2>

        <p>
        Visitors should respect consent, privacy,
        personal boundaries and individual preferences.
        </p>

        <h2>Intellectual Property</h2>

        <p>
        Website content, branding and original materials
        may not be commercially reproduced without
        appropriate authorization.
        </p>

        <h2>Disclaimer</h2>

        <p>
        The website is provided on an as-is basis.
        We do not guarantee uninterrupted availability
        or error-free operation.
        </p>

        <h2>Contact</h2>

        <p>CONTACT_EMAIL</p>
        """
    },

    "dmca.html": {
        "title": "DMCA and Copyright Policy",
        "description": "Copyright and DMCA information.",
        "body": """
        <h1>DMCA and Copyright Policy</h1>

        <p>
        We respect intellectual property rights and expect
        visitors to respect the rights of other creators.
        </p>

        <h2>Copyright Complaints</h2>

        <p>
        If you believe content on this website infringes
        your copyright, contact us with a sufficiently
        detailed written notice.
        </p>

        <h2>Information to Include</h2>

        <ul>
          <li>Identification of the copyrighted work.</li>
          <li>Identification of the allegedly infringing material.</li>
          <li>Your contact information.</li>
          <li>A statement of good-faith belief.</li>
          <li>A statement that the information is accurate.</li>
          <li>Your physical or electronic signature.</li>
        </ul>

        <h2>Contact</h2>

        <p>
        Copyright notices:
        CONTACT_EMAIL
        </p>
        """
    },

    "2257.html": {
        "title": "18 U.S.C. 2257 Statement",
        "description": "18 U.S.C. 2257 compliance statement.",
        "body": """
        <h1>18 U.S.C. § 2257 Statement</h1>

        <p>
        This website primarily publishes text-based
        conversation starters, relationship-oriented
        informational material and general editorial content.
        </p>

        <p>
        The website does not knowingly publish explicit
        visual depictions of actual sexually explicit conduct.
        </p>

        <p>
        Questions regarding this statement can be sent to:
        CONTACT_EMAIL
        </p>
        """
    },
}


def build_legal_pages():

    for filename, details in LEGAL_PAGES.items():

        body = details["body"]

        body = body.replace(
            "CURRENT_DATE",
            TODAY
        )

        body = body.replace(
            "CONTACT_EMAIL",
            esc(CONTACT_EMAIL)
        )

        content = f"""
        <main class="container content-page">
          {body}
        </main>
        """

        page = page_template(
            f"{details['title']} | {SITE_NAME}",
            details["description"],
            filename,
            content
        )

        write_file(
            filename,
            page
        )


# ============================================================
# 19. STYLED XML SITEMAP XSL
# ============================================================

def build_sitemap_xsl():

    return """<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
xmlns:s="http://www.sitemaps.org/schemas/sitemap/0.9">

<xsl:output method="html" encoding="UTF-8" indent="yes"/>

<xsl:template match="/">

<html lang="en">

<head>

<title>Flirty Chat Openers Sitemap</title>

<meta name="viewport"
content="width=device-width, initial-scale=1"/>

<style>

* {box-sizing:border-box;}

body {
    background:#0b0d14;
    color:#f4f4f8;
    font-family:system-ui,sans-serif;
    margin:0;
    padding:30px 16px;
    line-height:1.7;
}

main {
    max-width:1050px;
    margin:auto;
}

h1 {
    color:#f472b6;
    font-size:32px;
}

p {
    color:#a4a9b8;
}

table {
    width:100%;
    border-collapse:collapse;
    background:#131722;
    border:1px solid #292f40;
    border-radius:13px;
    overflow:hidden;
}

th,td {
    padding:14px;
    text-align:left;
    border-bottom:1px solid #292f40;
    overflow-wrap:anywhere;
}

th {
    color:#c4b5fd;
    background:#191e2c;
}

a {
    color:#f9a8d4;
    text-decoration:none;
}

a:hover {
    color:white;
}

@media(max-width:600px) {
    th,td {padding:9px;font-size:12px;}
}

</style>

</head>

<body>

<main>

<h1>Flirty Chat Openers Sitemap</h1>

<p>
Website URL directory and search engine sitemap.
</p>

<table>

<tr>
<th>Website URL</th>
<th>Last Modified</th>
</tr>

<xsl:for-each select="s:urlset/s:url">

<tr>

<td>
<a href="{s:loc}">
<xsl:value-of select="s:loc"/>
</a>
</td>

<td>
<xsl:value-of select="s:lastmod"/>
</td>

</tr>

</xsl:for-each>

<xsl:for-each select="s:sitemapindex/s:sitemap">

<tr>

<td>
<a href="{s:loc}">
<xsl:value-of select="s:loc"/>
</a>
</td>

<td>
<xsl:value-of select="s:lastmod"/>
</td>

</tr>

</xsl:for-each>

</table>

</main>

</body>
</html>

</xsl:template>

</xsl:stylesheet>
"""


# ============================================================
# 20. XML SITEMAPS AND ROBOTS
# ============================================================

def build_sitemaps(
    records,
    categories,
    subcategories,
    tags
):

    urls = []

    def add_url(path, lastmod=TODAY):
        urls.append((
            canonical(path),
            lastmod
        ))

    add_url("")
    add_url("privacy.html")
    add_url("terms.html")
    add_url("dmca.html")
    add_url("2257.html")

    for row in records:

        lastmod = (
            row["upload_date"][:10]
            if row["upload_date"]
            else TODAY
        )

        add_url(
            f"lines/{row['slug']}.html",
            lastmod
        )

    for category, items in categories.items():

        total_pages = max(
            1,
            math.ceil(
                len(items) / ITEMS_PER_CATEGORY_PAGE
            )
        )

        for number in range(1, total_pages + 1):

            add_url(
                f"category/{slugify(category)}/page-{number}.html"
            )

    for subcategory in subcategories:

        add_url(
            f"topic/{slugify(subcategory)}.html"
        )

    for tag_slug in tags:

        add_url(
            f"tag/{tag_slug}.html"
        )

    sitemap_files = []

    for offset in range(
        0,
        len(urls),
        SITEMAP_URL_LIMIT
    ):

        chunk = urls[
            offset:offset + SITEMAP_URL_LIMIT
        ]

        number = offset // SITEMAP_URL_LIMIT + 1

        filename = f"sitemap-{number}.xml"

        entries = []

        for loc, lastmod in chunk:

            entries.append(f"""
            <url>
              <loc>{html.escape(loc)}</loc>
              <lastmod>{esc(lastmod)}</lastmod>
              <changefreq>weekly</changefreq>
              <priority>0.7</priority>
            </url>
            """)

        xml = """<?xml version="1.0" encoding="UTF-8"?>
<?xml-stylesheet type="text/xsl" href="/sitemap.xsl"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
""" + "\n".join(entries) + """
</urlset>
"""

        write_file(
            filename,
            xml
        )

        sitemap_files.append(filename)

    index_entries = "".join(
        f"""
        <sitemap>
          <loc>{canonical(filename)}</loc>
          <lastmod>{TODAY}</lastmod>
        </sitemap>
        """
        for filename in sitemap_files
    )

    sitemap_index = f"""<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{index_entries}
</sitemapindex>
"""

    write_file(
        "sitemap.xml",
        sitemap_index
    )

    write_file(
        "sitemap.xsl",
        build_sitemap_xsl()
    )

    robots = f"""User-agent: *
Allow: /

Sitemap: {canonical("sitemap.xml")}
"""

    write_file(
        "robots.txt",
        robots
    )


# ============================================================
# 21. PRODUCTION VALIDATION
# ============================================================

def validate_build(records):

    required_files = [
        "index.html",
        "sitemap.xml",
        "sitemap-1.xml",
        "sitemap.xsl",
        "robots.txt",
        "privacy.html",
        "terms.html",
        "dmca.html",
        "2257.html",
    ]

    for filename in required_files:

        path = Path(OUTPUT_DIR) / filename

        if not path.is_file():
            raise RuntimeError(
                f"Build validation failed: missing {filename}"
            )

    html_files = list(
        Path(OUTPUT_DIR).rglob("*.html")
    )

    for path in html_files:

        content = path.read_text(
            encoding="utf-8"
        )

        required_meta = [
            f'content="{RATING_VERIFICATION}"',
            f'content="{GOOGLE_VERIFICATION}"',
            f'content="{BING_VERIFICATION}"',
        ]

        for marker in required_meta:

            if marker not in content:
                raise RuntimeError(
                    f"Missing verification metadata: {path}"
                )

        if 'rel="canonical"' not in content:
            raise RuntimeError(
                f"Missing canonical: {path}"
            )

        if 'id="ageGate"' not in content:
            raise RuntimeError(
                f"Missing age verification: {path}"
            )

        if 'id="ageEnter"' not in content:
            raise RuntimeError(
                f"Missing age approval button: {path}"
            )

        if 'id="ageExit"' not in content:
            raise RuntimeError(
                f"Missing age exit button: {path}"
            )

        if NETWORK_FOOTER.strip() not in content:
            raise RuntimeError(
                f"Missing network footer: {path}"
            )

        if "live-year" not in content:
            raise RuntimeError(
                f"Missing live year: {path}"
            )

    for row in records:

        path = (
            Path(OUTPUT_DIR)
            / "lines"
            / f"{row['slug']}.html"
        )

        if not path.is_file():
            raise RuntimeError(
                f"Missing detail page: {row['slug']}"
            )

        content = path.read_text(
            encoding="utf-8"
        )

        schemas = [
            '"@type":"Article"',
            '"@type":"BreadcrumbList"',
            '"@type":"FAQPage"',
        ]

        for schema in schemas:

            if schema not in content:
                raise RuntimeError(
                    f"Detail validation failed for "
                    f"{row['slug']}: missing {schema}"
                )

        if 'id="crushName"' not in content:
            raise RuntimeError(
                f"Missing crush name input: {row['slug']}"
            )

        if 'id="yourName"' not in content:
            raise RuntimeError(
                f"Missing your name input: {row['slug']}"
            )

        if 'id="pickRandomLine"' not in content:
            raise RuntimeError(
                f"Missing random line button: {row['slug']}"
            )

    print(
        f"Validated HTML pages: {len(html_files)}"
    )

    print(
        f"Validated detail records: {len(records)}"
    )


# ============================================================
# 22. MAIN BUILD PROCESS
# ============================================================

RANDOM_PAGE_URLS = []


def main():

    global RANDOM_PAGE_URLS

    started = datetime.now()

    print("=" * 65)
    print(" FLIRTY CHAT OPENERS")
    print(" Editorial Static Website Generator")
    print("=" * 65)

    print("\nReading CSV...")

    records = load_data()

    print(
        f"Successfully loaded {len(records)} content records."
    )

    (
        categories,
        subcategories,
        tags,
        tag_display,
        subcategory_display,
        category_counter
    ) = build_indexes(records)

    RANDOM_PAGE_URLS = [
        f"/lines/{row['slug']}.html"
        for row in records
    ]

    print("\nContent statistics:")

    print(
        f"  Articles:       {len(records)}"
    )

    print(
        f"  Categories:     {len(categories)}"
    )

    print(
        f"  Subcategories:  {len(subcategories)}"
    )

    print(
        f"  Unique tags:    {len(tags)}"
    )

    print("\nPreparing output directory...")

    output = Path(OUTPUT_DIR)

    if output.exists():
        shutil.rmtree(output)

    output.mkdir(
        parents=True,
        exist_ok=True
    )

    print("\n[1/8] Generating homepage...")

    build_home(
        records,
        categories,
        tags,
        tag_display,
        subcategories,
        subcategory_display,
        category_counter
    )

    print("\n[2/8] Generating detail pages...")

    for index, row in enumerate(records, start=1):

        build_detail(
            row,
            records
        )

        if index % 100 == 0:
            print(
                f"  Generated {index} detail pages..."
            )

    print(
        f"  Generated {len(records)} detail pages."
    )

    print("\n[3/8] Generating category hubs...")

    build_category_pages(
        categories
    )

    print("\n[4/8] Generating subcategory hubs...")

    build_subcategory_pages(
        subcategories
    )

    print("\n[5/8] Generating tag hubs...")

    build_tag_pages(
        tags,
        tag_display
    )

    print("\n[6/8] Generating legal pages...")

    build_legal_pages()

    print("\n[7/8] Generating SEO infrastructure...")

    build_sitemaps(
        records,
        categories,
        subcategories,
        tags
    )

    print("\n[8/8] Running production validation...")

    validate_build(records)

    elapsed = (
        datetime.now() - started
    ).total_seconds()

    total_files = sum(
        1
        for path in output.rglob("*")
        if path.is_file()
    )

    html_count = len(
        list(output.rglob("*.html"))
    )

    print("\n" + "=" * 65)
    print(" BUILD SUCCESSFUL")
    print("=" * 65)

    print(
        f"Website:       {BASE_URL}"
    )

    print(
        f"Articles:      {len(records)}"
    )

    print(
        f"Categories:    {len(categories)}"
    )

    print(
        f"Subcategories: {len(subcategories)}"
    )

    print(
        f"Unique tags:   {len(tags)}"
    )

    print(
        f"HTML pages:    {html_count}"
    )

    print(
        f"Total files:   {total_files}"
    )

    print(
        f"Build time:    {elapsed:.2f} seconds"
    )

    print(
        f"Output folder: {output.resolve()}"
    )

    print("\nGenerated infrastructure:")

    print("  index.html")
    print("  lines/")
    print("  category/")
    print("  topic/")
    print("  tag/")
    print("  sitemap.xml")
    print("  sitemap-1.xml")
    print("  sitemap.xsl")
    print("  robots.txt")
    print("  privacy.html")
    print("  terms.html")
    print("  dmca.html")
    print("  2257.html")

    print("\nCloudflare Workers deployment:")

    print(
        "  Deploy the contents of dist/ as static assets."
    )

    print(
        "  Configure your Workers static asset binding "
        "or Pages deployment."
    )

    print("\nSEO submission:")

    print(
        f"  {BASE_URL}/sitemap.xml"
    )

    print("\nImportant:")

    print(
        "  Keep build.py and data.csv in your repository."
    )

    print(
        "  Run python3 build.py whenever data.csv changes."
    )

    print(
        "  Age verification is a browser-side gate; "
        "it is not identity or age-proof verification."
    )

    print("=" * 65)


# ============================================================
# 23. EXECUTION
# ============================================================

if __name__ == "__main__":

    try:

        main()

    except KeyboardInterrupt:

        print("\nBuild cancelled by user.")
        sys.exit(130)

    except Exception as error:

        print("\n" + "=" * 65)
        print(" BUILD ERROR")
        print("=" * 65)

        print(
            f"{type(error).__name__}: {error}"
        )

        print("=" * 65)

        sys.exit(1)
