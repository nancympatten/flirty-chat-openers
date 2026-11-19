#!/usr/bin/env python3
"""
Flirty Chat Openers — Production Static pSEO Website Builder
============================================================

Python 3 | Zero external dependencies | Cloudflare Pages / Workers

Usage:
    python3 build.py

Input:
    data.csv

Output:
    dist/
      index.html
      lines/
      category/
      topic/
      tag/
      sitemap.xml
      sitemap-1.xml
      sitemap.xsl
      robots.txt
      dmca.html
      2257.html

Features:
    - Evergreen dynamic year and freshness engine
    - Responsive dark-mode electric-magenta design
    - Interactive opener generator and individual copy buttons
    - Live name personalization
    - Random opener selector
    - Follow-up conversation coach
    - Native affiliate CTA
    - Age verification
    - SEO metadata and JSON-LD
    - Category, subcategory and tag hubs
    - Pagination
    - Related content recommendations
    - XML sitemap and stylesheet
    - CSV validation and HTML escaping
    - Zero external JavaScript or CSS dependencies
"""

import os
import re
import csv
import json
import html
import shutil
import hashlib
from collections import Counter, defaultdict
from datetime import datetime
from urllib.parse import quote


# ============================================================
# CONFIGURATION
# ============================================================

BASE_URL = os.environ.get(
    "BASE_URL",
    "https://flirty-chat-openers.velvetgrid.workers.dev"
).rstrip("/")

SITE_NAME = "Flirty Chat Openers"

NICHE_TOPIC = (
    "Flirty Text Starters, Spicy Pick-Up Lines & Late Night Replies"
)

CONTACT_EMAIL = "nancympatten@gmail.com"

AFFILIATE_URL = "#affiliate-link"

AFFILIATE_CTA_TEXT = (
    "Practice Flirting 24/7 with an AI Companion (Free Chat)"
)

CURRENT_YEAR = datetime.utcnow().year

INPUT_FILE = "data.csv"
OUTPUT_DIR = "dist"

ITEMS_PER_PAGE = 24
RELATED_ITEMS = 8
NEWEST_ITEMS = 30

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

# ============================================================
# UTILITIES
# ============================================================


def esc(value):
    """Safely escape HTML content."""
    return html.escape(str(value or ""), quote=True)


def clean(value):
    """Normalize CSV values."""
    return str(value or "").strip()


def slugify(value):
    """Create URL-safe slugs."""
    value = clean(value).lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "uncategorized"


def safe_slug(value):
    """Prevent unsafe filesystem paths."""
    value = slugify(value)
    return value[:150] or "untitled"


def absolute_url(path):
    """Create an absolute canonical URL."""
    path = str(path).lstrip("/")
    return BASE_URL + "/" + path


def json_ld(data):
    """Serialize JSON-LD safely."""
    return (
        json.dumps(data, ensure_ascii=False, separators=(",", ":"))
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
    )


def split_tags(value):
    """Parse comma-separated tags."""
    if not value:
        return []

    tags = []

    for item in re.split(r"[,|]", clean(value)):
        item = item.strip()

        if item and item.lower() not in [x.lower() for x in tags]:
            tags.append(item)

    return tags


def split_openers(value):
    """Split individual flirty lines using the pipe delimiter."""
    if not value:
        return []

    return [
        line.strip()
        for line in str(value).split("|")
        if line.strip()
    ]


def date_value(value):
    """Parse common CSV date formats."""
    value = clean(value)

    if not value:
        return datetime(2000, 1, 1)

    formats = [
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%d-%m-%Y",
        "%m/%d/%Y",
        "%Y-%m-%d %H:%M:%S",
        "%d/%m/%Y",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            pass

    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(
            tzinfo=None
        )
    except ValueError:
        return datetime(2000, 1, 1)


def unique_filename(value):
    """Generate collision-resistant filename components."""
    base = safe_slug(value)

    digest = hashlib.sha1(
        clean(value).encode("utf-8")
    ).hexdigest()[:7]

    return f"{base}-{digest}"


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def write_file(path, content):
    ensure_dir(os.path.dirname(path) or OUTPUT_DIR)

    with open(path, "w", encoding="utf-8", newline="") as file:
        file.write(content)


def page_url(page):
    return absolute_url(page)


# ============================================================
# CSV LOADER
# ============================================================


def load_data():
    """Read and validate the source CSV."""

    if not os.path.isfile(INPUT_FILE):
        raise FileNotFoundError(
            f"Missing {INPUT_FILE}. Place data.csv beside build.py."
        )

    rows = []

    with open(
        INPUT_FILE,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as file:

        reader = csv.DictReader(file)

        if not reader.fieldnames:
            raise ValueError("The CSV file is empty or has no header.")

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
                key: clean(value)
                for key, value in original.items()
                if key is not None
            }

            if not row.get("title"):
                print(
                    f"Skipping CSV line {line_number}: missing title."
                )
                continue

            original_slug = row.get("slug") or row["title"]
            slug = safe_slug(original_slug)

            if slug in used_slugs:
                slug = f"{slug}-{hashlib.sha1(str(line_number).encode()).hexdigest()[:6]}"

            used_slugs.add(slug)

            row["slug"] = slug

            row["category"] = row.get("category") or "General Flirting"

            row["subcategory"] = (
                row.get("subcategory") or "General Openers"
            )

            row["tags_list"] = split_tags(row.get("tags", ""))

            row["openers"] = split_openers(
                row.get("openers_list", "")
            )

            row["date_object"] = date_value(
                row.get("upload_date", "")
            )

            row["category_slug"] = safe_slug(row["category"])

            row["subcategory_slug"] = safe_slug(
                row["subcategory"]
            )

            row["tag_slugs"] = [
                safe_slug(tag)
                for tag in row["tags_list"]
            ]

            row["detail_path"] = (
                f"lines/{row['slug']}.html"
            )

            row["canonical"] = absolute_url(
                row["detail_path"]
            )

            rows.append(row)

    return rows


# ============================================================
# GLOBAL CONTENT INDEXES
# ============================================================


def build_indexes(rows):

    categories = defaultdict(list)
    subcategories = defaultdict(list)
    tags = defaultdict(list)

    category_names = {}
    subcategory_names = {}
    tag_names = {}

    for row in rows:

        category_key = row["category_slug"]

        subcategory_key = row["subcategory_slug"]

        category_names[category_key] = row["category"]

        subcategory_names[subcategory_key] = row["subcategory"]

        categories[category_key].append(row)

        subcategories[subcategory_key].append(row)

        for tag, tag_slug in zip(
            row["tags_list"],
            row["tag_slugs"]
        ):
            tags[tag_slug].append(row)
            tag_names[tag_slug] = tag

    return {
        "categories": categories,
        "subcategories": subcategories,
        "tags": tags,
        "category_names": category_names,
        "subcategory_names": subcategory_names,
        "tag_names": tag_names,
    }


# ============================================================
# SHARED DESIGN SYSTEM
# ============================================================


def shared_css():

    return r"""
:root {
    color-scheme: dark;
    --bg: #09080f;
    --surface: #151221;
    --surface2: #1c182b;
    --pink: #ec4899;
    --pink2: #f472b6;
    --indigo: #6366f1;
    --text: #f8f5ff;
    --muted: #a8a1b8;
    --border: rgba(255,255,255,.09);
    --radius: 18px;
    --shadow: 0 12px 40px rgba(0,0,0,.28);
}

* {
    box-sizing: border-box;
}

html {
    scroll-behavior: smooth;
}

body {
    margin: 0;
    background: var(--bg);
    color: var(--text);
    font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont,
                 "Segoe UI", sans-serif;
    line-height: 1.7;
}

a {
    color: var(--pink2);
    text-decoration: none;
}

a:hover {
    color: white;
}

button, input {
    font: inherit;
}

button {
    cursor: pointer;
}

.container {
    width: min(1120px, calc(100% - 36px));
    margin: auto;
}

header {
    position: sticky;
    top: 0;
    z-index: 50;
    background: rgba(9,8,15,.94);
    border-bottom: 1px solid var(--border);
    backdrop-filter: blur(15px);
}

.nav {
    min-height: 72px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 20px;
}

.logo {
    font-size: 20px;
    font-weight: 900;
    letter-spacing: -.7px;
    color: white;
}

.logo span {
    color: var(--pink);
}

.nav-links {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 18px;
    font-size: 13px;
}

.hero {
    padding: 75px 0 50px;
    text-align: center;
}

.hero h1 {
    max-width: 900px;
    margin: 12px auto 18px;
    font-size: clamp(35px, 6vw, 65px);
    line-height: 1.08;
    letter-spacing: -2.4px;
}

.gradient-text {
    background: linear-gradient(100deg, #ec4899, #a78bfa, #6366f1);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
}

.hero p {
    max-width: 700px;
    margin: 0 auto;
    color: var(--muted);
}

.eyebrow {
    display: inline-flex;
    padding: 7px 13px;
    border-radius: 100px;
    background: rgba(236,72,153,.12);
    color: var(--pink2);
    border: 1px solid rgba(236,72,153,.25);
    font-size: 12px;
    font-weight: 800;
}

.section {
    padding: 35px 0;
}

.section-heading {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 12px;
    margin-bottom: 22px;
}

.section-heading h2 {
    font-size: clamp(23px, 4vw, 32px);
    margin: 0;
    letter-spacing: -.8px;
}

.muted {
    color: var(--muted);
}

.grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0,1fr));
    gap: 16px;
}

.card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 21px;
    box-shadow: var(--shadow);
    transition: transform .2s, border-color .2s;
    min-width: 0;
}

.card:hover {
    transform: translateY(-3px);
    border-color: rgba(236,72,153,.45);
}

.card h3 {
    margin: 8px 0;
    line-height: 1.35;
}

.card p {
    color: var(--muted);
    font-size: 14px;
}

.card-meta {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    font-size: 12px;
    color: var(--muted);
}

.pill {
    display: inline-flex;
    align-items: center;
    border: 1px solid var(--border);
    border-radius: 50px;
    padding: 6px 12px;
    background: var(--surface2);
    color: var(--pink2);
    font-size: 12px;
    margin: 3px;
}

.search-box {
    max-width: 720px;
    margin: 32px auto 0;
    position: relative;
}

.search-box input,
.customizer input {
    width: 100%;
    padding: 16px 18px;
    background: var(--surface);
    border: 1px solid var(--border);
    color: white;
    outline: none;
    border-radius: 13px;
}

.search-box input:focus,
.customizer input:focus {
    border-color: var(--pink);
}

.search-results {
    text-align: left;
    display: none;
    margin-top: 12px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 15px;
}

.button {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    border: 0;
    border-radius: 11px;
    padding: 11px 17px;
    background: linear-gradient(110deg, #ec4899, #9333ea);
    color: white;
    font-weight: 800;
    font-size: 13px;
    transition: opacity .2s, transform .2s;
}

.button:hover {
    color: white;
    opacity: .9;
    transform: translateY(-1px);
}

.button.secondary {
    background: var(--surface2);
    border: 1px solid var(--border);
}

.button.small {
    padding: 8px 12px;
    font-size: 12px;
}

.badge {
    display: inline-block;
    padding: 5px 10px;
    border-radius: 50px;
    background: rgba(99,102,241,.13);
    color: #a5b4fc;
    font-size: 11px;
    font-weight: 800;
}

.count {
    color: var(--muted);
    font-size: 12px;
}

.detail-hero {
    padding: 55px 0 30px;
}

.detail-hero h1 {
    font-size: clamp(32px, 5vw, 52px);
    line-height: 1.12;
    letter-spacing: -1.5px;
}

.breadcrumbs {
    font-size: 12px;
    color: var(--muted);
    margin-bottom: 18px;
}

.breadcrumbs a {
    color: var(--pink2);
}

.opener-list {
    display: grid;
    gap: 13px;
}

.opener-card {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 15px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 15px;
    padding: 17px;
}

.opener-text {
    font-size: 15px;
    overflow-wrap: anywhere;
}

.opener-actions {
    flex-shrink: 0;
}

.customizer {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 14px;
    margin: 20px 0;
}

.customizer label {
    display: block;
    margin-bottom: 7px;
    color: var(--muted);
    font-size: 12px;
    font-weight: 700;
}

.spotlight {
    background: linear-gradient(120deg, #31122e, #211b48);
    border: 1px solid rgba(236,72,153,.3);
    border-radius: var(--radius);
    padding: 24px;
    margin: 20px 0;
}

.spotlight h3 {
    margin-top: 0;
}

.spotlight-line {
    font-size: 21px;
    line-height: 1.5;
    font-weight: 750;
    margin: 16px 0;
}

.affiliate {
    margin: 27px 0;
    padding: 27px;
    border-radius: var(--radius);
    background: linear-gradient(125deg, #3b123b, #1c1b43);
    border: 1px solid rgba(236,72,153,.38);
    text-align: center;
}

.affiliate h2 {
    margin-top: 0;
}

.strategy {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 15px;
    padding: 20px;
}

.strategy summary {
    cursor: pointer;
    color: var(--pink2);
    font-weight: 800;
}

.strategy-content {
    color: var(--muted);
    white-space: pre-wrap;
    margin-top: 14px;
}

.tag-cloud {
    display: flex;
    flex-wrap: wrap;
    gap: 7px;
}

.pagination {
    display: flex;
    justify-content: center;
    align-items: center;
    flex-wrap: wrap;
    gap: 14px;
    margin: 35px 0;
}

.empty {
    padding: 35px;
    border-radius: var(--radius);
    text-align: center;
    color: var(--muted);
    background: var(--surface);
}

footer {
    border-top: 1px solid var(--border);
    margin-top: 70px;
    padding: 38px 0;
    color: var(--muted);
    font-size: 13px;
}

.footer-grid {
    display: grid;
    grid-template-columns: 2fr 1fr 1fr;
    gap: 30px;
}

footer a {
    display: block;
    margin: 7px 0;
}

.age-overlay {
    position: fixed;
    inset: 0;
    z-index: 9999;
    display: none;
    align-items: center;
    justify-content: center;
    padding: 20px;
    background: rgba(0,0,0,.94);
    backdrop-filter: blur(15px);
}

.age-box {
    max-width: 440px;
    width: 100%;
    padding: 32px;
    background: var(--surface);
    border: 1px solid rgba(236,72,153,.4);
    border-radius: 22px;
    text-align: center;
}

.age-box h2 {
    font-size: 28px;
}

.age-box p {
    color: var(--muted);
    font-size: 14px;
}

.age-buttons {
    display: grid;
    gap: 10px;
    margin-top: 22px;
}

.no-results {
    display: none;
    color: var(--muted);
    padding: 20px;
}

.ad-slot {
    width: 100%;
    min-height: 0;
}

@media(max-width:800px) {
    .grid {
        grid-template-columns: repeat(2,minmax(0,1fr));
    }

    .footer-grid {
        grid-template-columns: 1fr 1fr;
    }
}

@media(max-width:560px) {
    .container {
        width: calc(100% - 28px);
    }

    .nav {
        padding: 12px 0;
        align-items: flex-start;
    }

    .nav-links {
        gap: 9px;
        font-size: 11px;
    }

    .logo {
        font-size: 16px;
    }

    .hero {
        padding: 48px 0 30px;
    }

    .hero h1 {
        letter-spacing: -1.4px;
    }

    .grid {
        grid-template-columns: 1fr;
    }

    .customizer {
        grid-template-columns: 1fr;
    }

    .opener-card {
        align-items: flex-start;
        flex-direction: column;
    }

    .footer-grid {
        grid-template-columns: 1fr;
    }

    .spotlight-line {
        font-size: 18px;
    }
}
"""


# ============================================================
# SHARED CLIENT-SIDE JAVASCRIPT
# ============================================================


def shared_js():

    return r"""
<script>
(function() {
    "use strict";

    // Evergreen visitor-local year.
    function updateLiveYear() {
        var year = new Date().getFullYear();

        document.querySelectorAll(".live-year").forEach(function(el) {
            el.textContent = year;
        });

        var month = new Intl.DateTimeFormat("en", {
            month: "long"
        }).format(new Date());

        document.querySelectorAll(".live-freshness").forEach(function(el) {
            el.textContent = "Tested & Trending: " + month + " " + year;
        });
    }

    updateLiveYear();

    // Age verification.
    var ageOverlay = document.getElementById("ageOverlay");

    if (ageOverlay) {
        try {
            var verified = localStorage.getItem("flirty18Verified");

            if (verified !== "yes") {
                ageOverlay.style.display = "flex";
            }
        } catch(e) {
            ageOverlay.style.display = "flex";
        }

        var yes = document.getElementById("ageYes");
        var no = document.getElementById("ageNo");

        if (yes) {
            yes.addEventListener("click", function() {
                try {
                    localStorage.setItem("flirty18Verified", "yes");
                } catch(e) {}

                ageOverlay.style.display = "none";
            });
        }

        if (no) {
            no.addEventListener("click", function() {
                document.body.innerHTML =
                    '<main style="padding:40px;text-align:center;font-family:system-ui">' +
                    '<h1>Access Restricted</h1>' +
                    '<p>You must be 18 or older to access this website.</p>' +
                    '</main>';
            });
        }
    }

    // Homepage live search.
    var search = document.getElementById("liveSearch");
    var searchResults = document.getElementById("searchResults");

    if (search && searchResults) {
        var entries = Array.from(
            document.querySelectorAll("[data-search-entry]")
        );

        search.addEventListener("input", function() {
            var query = search.value.trim().toLowerCase();

            searchResults.innerHTML = "";
            searchResults.style.display = query ? "block" : "none";

            if (!query) return;

            var matches = entries.filter(function(entry) {
                return (entry.dataset.search || "").includes(query);
            }).slice(0, 15);

            if (!matches.length) {
                searchResults.textContent = "No matching collections found.";
                return;
            }

            matches.forEach(function(entry) {
                var link = document.createElement("a");
                link.href = entry.dataset.href;
                link.textContent = entry.dataset.title;
                link.style.display = "block";
                link.style.padding = "9px 0";
                link.style.borderBottom = "1px solid rgba(255,255,255,.08)";
                searchResults.appendChild(link);
            });
        });
    }

    // Personalized opener generator.
    var nameInputs = document.querySelectorAll("[data-name-input]");
    var openerElements = document.querySelectorAll("[data-opener-template]");

    function personalized(template) {
        var crush = document.getElementById("crushName");
        var sender = document.getElementById("yourName");

        var crushName = crush ? crush.value.trim() : "";
        var yourName = sender ? sender.value.trim() : "";

        return template
            .replace(/\{\{crush\}\}/gi, crushName || "you")
            .replace(/\{\{your\}\}/gi, yourName || "me");
    }

    function refreshOpeners() {
        openerElements.forEach(function(element) {
            element.textContent = personalized(
                element.dataset.openerTemplate || ""
            );
        });

        var spotlightTemplate = document.getElementById("spotlightTemplate");
        var spotlightText = document.getElementById("spotlightText");

        if (spotlightTemplate && spotlightText) {
            spotlightText.textContent = personalized(
                spotlightTemplate.value
            );
        }
    }

    nameInputs.forEach(function(input) {
        input.addEventListener("input", refreshOpeners);
    });

    // Clipboard with fallback.
    function copyText(text, button) {
        function success() {
            if (!button) return;

            var old = button.textContent;
            button.textContent = "Copied!";

            setTimeout(function() {
                button.textContent = old;
            }, 1500);
        }

        if (navigator.clipboard && window.isSecureContext) {
            navigator.clipboard.writeText(text).then(success).catch(function() {
                fallbackCopy(text, success);
            });
        } else {
            fallbackCopy(text, success);
        }
    }

    function fallbackCopy(text, callback) {
        var textarea = document.createElement("textarea");

        textarea.value = text;
        textarea.style.position = "fixed";
        textarea.style.opacity = "0";

        document.body.appendChild(textarea);
        textarea.select();

        try {
            document.execCommand("copy");
            callback();
        } catch(e) {}

        textarea.remove();
    }

    document.querySelectorAll("[data-copy]").forEach(function(button) {
        button.addEventListener("click", function() {
            var target = document.getElementById(button.dataset.copy);

            if (!target) return;

            copyText(target.textContent, button);
        });
    });

    // Random opener spotlight.
    var randomButton = document.getElementById("randomOpener");

    if (randomButton) {
        randomButton.addEventListener("click", function() {
            var templates = Array.from(openerElements);

            if (!templates.length) return;

            var selected = templates[
                Math.floor(Math.random() * templates.length)
            ];

            var spotlight = document.getElementById("spotlightText");
            var hidden = document.getElementById("spotlightTemplate");

            if (spotlight && hidden) {
                hidden.value = selected.dataset.openerTemplate || "";
                spotlight.textContent = personalized(hidden.value);
            }

            var area = document.getElementById("randomSpotlight");

            if (area) {
                area.scrollIntoView({
                    behavior: "smooth",
                    block: "center"
                });
            }
        });
    }

    // Category/topic client-side filter.
    document.querySelectorAll("[data-filter-input]").forEach(function(input) {
        var target = input.dataset.filterInput;
        var items = document.querySelectorAll(
            "[" + target + "]"
        );

        input.addEventListener("input", function() {
            var value = input.value.toLowerCase().trim();

            items.forEach(function(item) {
                var text = item.getAttribute(target).toLowerCase();

                item.style.display = text.includes(value) ? "" : "none";
            });
        });
    });

})();
</script>
"""


# ============================================================
# SHARED HTML COMPONENTS
# ============================================================


def header_html():

    return """
<header>
    <div class="container nav">
        <a class="logo" href="/">FLIRTY<span>CHAT</span></a>
        <nav class="nav-links">
            <a href="/">Home</a>
            <a href="/#categories">Categories</a>
            <a href="/#newest">Latest Openers</a>
            <a href="/dmca.html">DMCA</a>
        </nav>
    </div>
</header>
"""


def age_modal():

    return """
<div class="age-overlay" id="ageOverlay" role="dialog"
     aria-modal="true" aria-labelledby="ageTitle">
    <div class="age-box">
        <div class="eyebrow">18+ ADULT CONTENT</div>
        <h2 id="ageTitle">Before You Enter...</h2>
        <p>
            Flirty Chat Openers is intended exclusively for adults
            aged 18 and older. By continuing, you confirm that you
            meet the legal age requirement in your location.
        </p>
        <div class="age-buttons">
            <button class="button" id="ageYes">
                Yes, I am 18 or older
            </button>
            <button class="button secondary" id="ageNo">
                No, take me back
            </button>
        </div>
    </div>
</div>
"""


def footer_html():

    return f"""
<footer>
    <div class="container footer-grid">
        <div>
            <a class="logo" href="/">FLIRTY<span>CHAT</span></a>
            <p>
                Your destination for flirty text starters, playful
                conversation ideas, and creative message inspiration.
            </p>
            <p>© <span class="live-year">{CURRENT_YEAR}</span>
               {SITE_NAME}. All rights reserved.</p>
        </div>

        <div>
            <strong>Explore</strong>
            <a href="/">Home</a>
            <a href="/#categories">Categories</a>
            <a href="/#newest">Latest collections</a>
        </div>

        <div>
            <strong>Information</strong>
            <a href="/dmca.html">DMCA Policy</a>
            <a href="/2257.html">18 U.S.C. § 2257</a>
            <a href="mailto:{CONTACT_EMAIL}">Contact</a>
        </div>
    </div>
</footer>
"""


def freshness_badge():

    return """
<div class="eyebrow live-freshness">
    Tested & Trending
</div>
"""


def ad_slot(name):

    return f"""
<div class="ad-slot">
    <!-- AD_SLOT_{name} -->
</div>
"""


def page_shell(title, description, canonical, content, extra_head="",
               body_class=""):

    safe_title = esc(title)
    safe_description = esc(description)
    safe_canonical = esc(canonical)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">

<title>{safe_title}</title>

<meta name="description" content="{safe_description}">
<meta name="robots" content="index, follow, max-image-preview:large">
<meta name="rating" content="RTA-5042-1996-1400-1577-RTA">
<meta name="theme-color" content="#09080f">

<link rel="canonical" href="{safe_canonical}">

<meta property="og:type" content="website">
<meta property="og:site_name" content="{esc(SITE_NAME)}">
<meta property="og:title" content="{safe_title}">
<meta property="og:description" content="{safe_description}">
<meta property="og:url" content="{safe_canonical}">
<meta property="og:locale" content="en_US">

<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="{safe_title}">
<meta name="twitter:description" content="{safe_description}">

{extra_head}

<style>
{shared_css()}
</style>
</head>

<body class="{esc(body_class)}">

{header_html()}

{ad_slot("TOP_BANNER")}

{content}

{ad_slot("STICKY_FOOTER")}

{footer_html()}

{age_modal()}

{shared_js()}

</body>
</html>
"""


# ============================================================
# REUSABLE CONTENT CARDS
# ============================================================


def opener_card(row):

    description = row.get("description") or (
        "Explore creative flirty messages and conversation starters."
    )

    return f"""
<article class="card">
    <div class="card-meta">
        <span class="badge">{esc(row["category"])}</span>
    </div>

    <h3>
        <a href="/{esc(row["detail_path"])}">
            {esc(row["title"])}
        </a>
    </h3>

    <p>{esc(description[:180])}</p>

    <div class="card-meta">
        <span>{len(row["openers"])} messages</span>
        <span>•</span>
        <span>{esc(row["subcategory"])}</span>
    </div>

    <p>
        <a class="button small" href="/{esc(row["detail_path"])}">
            Explore Openers →
        </a>
    </p>
</article>
"""


def category_card(name, slug, count):

    return f"""
<a class="card" href="/category/{esc(slug)}/page-1.html">
    <h3>{esc(name)}</h3>
    <span class="count">{count} collections</span>
</a>
"""


def hub_pagination(base_path, current, total):

    if total <= 1:
        return ""

    previous = ""
    following = ""

    if current > 1:
        previous = (
            f'<a class="button secondary" href="/{base_path}'
            f'/page-{current - 1}.html">← Previous</a>'
        )

    if current < total:
        following = (
            f'<a class="button" href="/{base_path}'
            f'/page-{current + 1}.html">Next →</a>'
        )

    return f"""
<nav class="pagination" aria-label="Pagination">
    {previous}
    <span class="count">Page {current} of {total}</span>
    {following}
</nav>
"""


# ============================================================
# HOMEPAGE
# ============================================================


def build_homepage(rows, indexes):

    category_items = []

    for slug, items in sorted(
        indexes["categories"].items(),
        key=lambda pair: pair[0]
    ):
        name = indexes["category_names"][slug]

        category_items.append(
            category_card(name, slug, len(items))
        )

    subcategory_items = []

    for slug, items in sorted(
        indexes["subcategories"].items(),
        key=lambda pair: pair[0]
    ):
        name = indexes["subcategory_names"][slug]

        subcategory_items.append(f"""
<a class="pill" href="/topic/{esc(slug)}.html">
    {esc(name)} ({len(items)})
</a>
""")

    tag_items = []

    for slug, items in sorted(
        indexes["tags"].items(),
        key=lambda pair: (-len(pair[1]), pair[0])
    ):
        name = indexes["tag_names"][slug]

        tag_items.append(f"""
<a class="pill" href="/tag/{esc(slug)}.html">
    #{esc(name)} ({len(items)})
</a>
""")

    newest = sorted(
        rows,
        key=lambda row: row["date_object"],
        reverse=True
    )[:NEWEST_ITEMS]

    newest_cards = "".join(
        opener_card(row) for row in newest
    )

    search_entries = []

    for row in rows:
        searchable = " ".join([
            row["title"],
            row["target_keyword"],
            row["category"],
            row["subcategory"],
            " ".join(row["tags_list"]),
        ]).lower()

        search_entries.append(f"""
<div data-search-entry
     data-title="{esc(row["title"])}"
     data-href="/{esc(row["detail_path"])}"
     data-search="{esc(searchable)}"
     hidden></div>
""")

    content = f"""
<main>

<section class="hero">
    <div class="container">
        {freshness_badge()}

        <h1>
            Find Your Next
            <span class="gradient-text">Perfect Flirty Opener</span>
        </h1>

        <p>
            Discover clever flirty text starters, playful pick-up
            lines, late-night replies, and conversation ideas.
            Personalize messages and find the perfect words to
            start something interesting.
        </p>

        <div class="search-box">
            <input
                type="search"
                id="liveSearch"
                placeholder="Search flirty openers, keywords, and tags..."
                aria-label="Search flirty openers"
                autocomplete="off"
            >
            <div class="search-results" id="searchResults"></div>
        </div>

        <p style="margin-top:18px">
            <span class="badge">
                Updated <span class="live-year">{CURRENT_YEAR}</span>
            </span>
            <span class="badge">Instant Message Inspiration</span>
            <span class="badge">Personalizable Openers</span>
        </p>
    </div>
</section>

<section class="section" id="categories">
    <div class="container">
        <div class="section-heading">
            <h2>Browse Flirting Categories</h2>
            <span class="count">
                {len(indexes["categories"])} unique categories
            </span>
        </div>

        <div class="grid">
            {''.join(category_items) if category_items else '<div class="empty">Categories will appear when content is added.</div>'}
        </div>
    </div>
</section>

<section class="section">
    <div class="container">
        <div class="section-heading">
            <h2>Explore Subcategories</h2>
        </div>

        <div class="tag-cloud">
            {''.join(subcategory_items) if subcategory_items else '<span class="muted">No subcategories available.</span>'}
        </div>
    </div>
</section>

<section class="section">
    <div class="container">
        <div class="section-heading">
            <h2>Discover Popular Tags</h2>
        </div>

        <div class="tag-cloud">
            {''.join(tag_items) if tag_items else '<span class="muted">No tags available.</span>'}
        </div>
    </div>
</section>

{ad_slot("MID_CONTENT")}

<section class="section" id="newest">
    <div class="container">
        <div class="section-heading">
            <h2>Latest Flirty Opener Collections</h2>
            <span class="count">
                Newest {len(newest)} collections
            </span>
        </div>

        <div class="grid">
            {newest_cards if newest_cards else '<div class="empty">Your first collection will appear here.</div>'}
        </div>
    </div>
</section>

<section class="section">
    <div class="container card">
        <h2>Better Conversations Start With Better Openers</h2>

        <p class="muted">
            Explore different conversation styles, personalize
            your favorite messages, and discover new ways to
            make your conversations more engaging. Whether
            you prefer playful banter, confident compliments,
            or thoughtful late-night messages, there is always
            a new conversation starter to explore.
        </p>

        <p>
            Browse our growing library of flirty text starters
            and find a message that matches your personality.
        </p>
    </div>
</section>

</main>

<div hidden>
    {''.join(search_entries)}
</div>
"""

    description = (
        "Discover flirty text starters, playful pick-up lines, "
        "personalized conversation openers, and late-night replies."
    )

    return page_shell(
        f"{SITE_NAME} - Flirty Text Starters & Conversation Openers",
        description,
        absolute_url("index.html"),
        content,
    )


# ============================================================
# DETAIL PAGE JSON-LD
# ============================================================


def detail_schema(row):

    canonical = row["canonical"]

    description = row.get("description") or (
        f"Explore {row['title']}, a collection of flirty "
        "conversation starters and message ideas."
    )

    article = {
        "@context": "https://schema.org",
        "@type": "Article",
        "mainEntityOfPage": {
            "@type": "WebPage",
            "@id": canonical,
        },
        "headline": row["title"],
        "description": description,
        "datePublished": row["date_object"].strftime("%Y-%m-%d"),
        "dateModified": row["date_object"].strftime("%Y-%m-%d"),
        "author": {
            "@type": "Organization",
            "name": SITE_NAME,
        },
        "publisher": {
            "@type": "Organization",
            "name": SITE_NAME,
        },
        "keywords": ", ".join(
            [row["target_keyword"]] + row["tags_list"]
        ),
    }

    breadcrumb = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": 1,
                "name": "Home",
                "item": absolute_url("index.html"),
            },
            {
                "@type": "ListItem",
                "position": 2,
                "name": row["category"],
                "item": absolute_url(
                    f"category/{row['category_slug']}/page-1.html"
                ),
            },
            {
                "@type": "ListItem",
                "position": 3,
                "name": row["title"],
                "item": canonical,
            },
        ],
    }

    questions = []

    for q, a in [
        (row.get("faq_q1"), row.get("faq_a1")),
        (row.get("faq_q2"), row.get("faq_a2")),
    ]:
        if q and a:
            questions.append({
                "@type": "Question",
                "name": q,
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": a,
                },
            })

    schemas = [
        article,
        breadcrumb,
    ]

    if questions:
        schemas.append({
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": questions,
        })

    return "\n".join(
        '<script type="application/ld+json">'
        + json_ld(schema)
        + '</script>'
        for schema in schemas
    )


# ============================================================
# DETAIL PAGE
# ============================================================


def related_content(row, rows):

    candidates = []

    for other in rows:

        if other["slug"] == row["slug"]:
            continue

        same_subcategory = (
            other["subcategory_slug"] == row["subcategory_slug"]
        )

        shared_tags = (
            set(other["tag_slugs"]) & set(row["tag_slugs"])
        )

        same_category = (
            other["category_slug"] == row["category_slug"]
        )

        score = (
            (5 if same_subcategory else 0)
            + (len(shared_tags) * 3)
            + (2 if same_category else 0)
        )

        if score > 0:
            candidates.append((score, other))

    candidates.sort(
        key=lambda pair: (
            -pair[0],
            pair[1]["title"].lower()
        )
    )

    selected = [item for score, item in candidates[:RELATED_ITEMS]]

    # Fill remaining positions if fewer related matches exist.
    if len(selected) < RELATED_ITEMS:
        selected_slugs = {
            item["slug"] for item in selected
        }

        for other in rows:
            if other["slug"] == row["slug"]:
                continue

            if other["slug"] not in selected_slugs:
                selected.append(other)
                selected_slugs.add(other["slug"])

            if len(selected) >= RELATED_ITEMS:
                break

    return selected


def build_detail_page(row, rows):

    opener_cards = []

    for index, opener in enumerate(row["openers"], start=1):

        element_id = f"opener-{index}"

        opener_cards.append(f"""
<div class="opener-card">
    <div
        class="opener-text"
        id="{element_id}"
        data-opener-template="{esc(opener)}"
    >{esc(opener)}</div>

    <div class="opener-actions">
        <button
            class="button small"
            data-copy="{element_id}"
            type="button"
        >Copy Line</button>
    </div>
</div>
""")

    related = related_content(row, rows)

    related_html = "".join(
        opener_card(item)
        for item in related
    )

    tags_html = "".join(
        f'<a class="pill" href="/tag/{esc(tag_slug)}.html">#{esc(tag)}</a>'
        for tag, tag_slug in zip(
            row["tags_list"],
            row["tag_slugs"]
        )
    )

    description = row.get("description") or (
        f"Explore {row['title']} and discover creative "
        "flirty conversation starters."
    )

    follow_up = row.get("follow_up_tips") or (
        "Keep your conversation natural and relaxed. "
        "Pay attention to the other person's responses, "
        "ask thoughtful questions, and let the exchange "
        "develop at a comfortable pace."
    )

    faq_html = ""

    for question, answer in [
        (row.get("faq_q1"), row.get("faq_a1")),
        (row.get("faq_q2"), row.get("faq_a2")),
    ]:
        if question and answer:
            faq_html += f"""
<div class="card" style="margin-top:12px">
    <h3>{esc(question)}</h3>
    <p>{esc(answer)}</p>
</div>
"""

    content = f"""
<main>

<div class="container">

<section class="detail-hero">
    <div class="breadcrumbs">
        <a href="/">Home</a> /
        <a href="/category/{esc(row["category_slug"])}/page-1.html">
            {esc(row["category"])}
        </a> /
        <span>{esc(row["title"])}</span>
    </div>

    {freshness_badge()}

    <h1>
        <span class="gradient-text">{esc(row["title"])}</span>
    </h1>

    <p class="muted">{esc(description)}</p>

    <div class="card-meta">
        <span class="badge">{esc(row["category"])}</span>
        <span class="badge">{esc(row["subcategory"])}</span>
        <span>{len(row["openers"])} message ideas</span>
    </div>

    <p class="muted">
        Updated <span class="live-year">{CURRENT_YEAR}</span>
    </p>
</section>

{ad_slot("MID_CONTENT")}

<section class="section">
    <div class="section-heading">
        <h2>Your Flirty Message Studio</h2>
    </div>

    <div class="card">
        <h3>Personalize Your Messages</h3>

        <p class="muted">
            Add names below to customize supported placeholders
            in your message templates.
        </p>

        <div class="customizer">
            <div>
                <label for="crushName">Crush Name</label>
                <input
                    id="crushName"
                    data-name-input
                    type="text"
                    placeholder="Enter their name"
                    maxlength="50"
                >
            </div>

            <div>
                <label for="yourName">Your Name</label>
                <input
                    id="yourName"
                    data-name-input
                    type="text"
                    placeholder="Enter your name"
                    maxlength="50"
                >
            </div>
        </div>
    </div>

    <div class="spotlight" id="randomSpotlight">
        <span class="badge">RANDOM MESSAGE PICKER</span>

        <h3>Your Next Conversation Starter</h3>

        <div class="spotlight-line" id="spotlightText">
            Pick a random line to discover your next opener.
        </div>

        <input
            type="hidden"
            id="spotlightTemplate"
            value=""
        >

        <button class="button" id="randomOpener" type="button">
            ✨ Pick Random Line
        </button>

        <button
            class="button secondary"
            data-copy="spotlightText"
            type="button"
        >
            Copy Random Line
        </button>
    </div>

    <div class="section-heading">
        <h2>Message List & Copy Studio</h2>
        <span class="count">{len(row["openers"])} messages</span>
    </div>

    <div class="opener-list">
        {''.join(opener_cards) if opener_cards else '<div class="empty">No individual messages have been supplied for this collection yet.</div>'}
    </div>

    <div class="affiliate">
        <span class="badge">CONVERSATION PRACTICE</span>

        <h2>Want to Practice Your Flirting Skills?</h2>

        <p>
            Explore an AI companion experience and practice
            conversations whenever inspiration strikes.
        </p>

        <a
            class="button"
            href="{esc(AFFILIATE_URL)}"
            target="_blank"
            rel="nofollow sponsored noopener"
        >
            {esc(AFFILIATE_CTA_TEXT)} →
        </a>
    </div>

    <div class="section-heading">
        <h2>Follow-Up Coach</h2>
    </div>

    <details class="strategy">
        <summary>
            💬 Expand Your Conversation Strategy
        </summary>

        <div class="strategy-content">{esc(follow_up)}</div>
    </details>
</section>

<section class="section">
    <div class="section-heading">
        <h2>About These Flirty Openers</h2>
    </div>

    <div class="card">
        <p>{esc(description)}</p>

        <p>
            Use these messages as inspiration rather than rigid
            scripts. Personalize your approach, respect boundaries,
            and allow the conversation to develop naturally.
        </p>

        <div class="tag-cloud">
            {tags_html}
        </div>
    </div>
</section>

<section class="section">
    <div class="section-heading">
        <h2>Frequently Asked Questions</h2>
    </div>

    {faq_html if faq_html else '<div class="empty">More frequently asked questions will be added as this collection grows.</div>'}
</section>

<section class="section">
    <div class="section-heading">
        <h2>Related Flirty Openers & Replies</h2>
    </div>

    <div class="grid">
        {related_html if related_html else '<div class="empty">Explore more collections from the homepage.</div>'}
    </div>
</section>

</div>
</main>
"""

    extra_head = detail_schema(row)

    return page_shell(
        f"{row['title']} - Flirty Chat Openers",
        description[:155],
        row["canonical"],
        content,
        extra_head=extra_head,
    )


# ============================================================
# PAGINATED CATEGORY HUBS
# ============================================================


def build_category_hubs(indexes):

    for slug, items in indexes["categories"].items():

        items = sorted(
            items,
            key=lambda row: row["date_object"],
            reverse=True
        )

        total_pages = max(
            1,
            (len(items) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
        )

        name = indexes["category_names"][slug]

        for page_number in range(1, total_pages + 1):

            start = (page_number - 1) * ITEMS_PER_PAGE

            page_items = items[
                start:start + ITEMS_PER_PAGE
            ]

            cards = "".join(
                opener_card(row)
                for row in page_items
            )

            base_path = f"category/{slug}"

            relative_path = (
                f"{base_path}/page-{page_number}.html"
            )

            canonical = absolute_url(relative_path)

            prev_next = ""

            if page_number > 1:
                prev_url = absolute_url(
                    f"{base_path}/page-{page_number - 1}.html"
                )

                prev_next += (
                    f'<link rel="prev" href="{esc(prev_url)}">'
                )

            if page_number < total_pages:
                next_url = absolute_url(
                    f"{base_path}/page-{page_number + 1}.html"
                )

                prev_next += (
                    f'<link rel="next" href="{esc(next_url)}">'
                )

            content = f"""
<main>
<div class="container">

<section class="detail-hero">
    {freshness_badge()}

    <div class="breadcrumbs">
        <a href="/">Home</a> / {esc(name)}
    </div>

    <h1>
        <span class="gradient-text">{esc(name)}</span>
    </h1>

    <p class="muted">
        Explore {len(items)} flirty message collections
        in this category.
    </p>

    <span class="badge">
        Page {page_number} of {total_pages}
    </span>
</section>

<section class="section">
    <div class="grid">
        {cards if cards else '<div class="empty">No collections found.</div>'}
    </div>

    {hub_pagination(base_path, page_number, total_pages)}
</section>

</div>
</main>
"""

            html_page = page_shell(
                f"{name} - Flirty Chat Openers | Page {page_number}",
                f"Browse {len(items)} flirty message collections in {name}.",
                canonical,
                content,
                extra_head=prev_next,
            )

            write_file(
                os.path.join(
                    OUTPUT_DIR,
                    relative_path
                ),
                html_page,
            )


# ============================================================
# SUBCATEGORY AND TAG HUBS
# ============================================================


def build_collection_hub(
    slug,
    name,
    items,
    hub_type,
):

    items = sorted(
        items,
        key=lambda row: row["date_object"],
        reverse=True
    )

    if hub_type == "topic":
        relative_path = f"topic/{slug}.html"
        label = "Flirting Topic"
        title_prefix = "Explore"
    else:
        relative_path = f"tag/{slug}.html"
        label = "Topic Tag"
        title_prefix = "Discover"

    cards = "".join(
        opener_card(row)
        for row in items
    )

    content = f"""
<main>
<div class="container">

<section class="detail-hero">
    {freshness_badge()}

    <div class="breadcrumbs">
        <a href="/">Home</a> / {esc(name)}
    </div>

    <span class="badge">{label}</span>

    <h1>
        {title_prefix}
        <span class="gradient-text">{esc(name)}</span>
    </h1>

    <p class="muted">
        Browse {len(items)} collections related to {esc(name)}.
    </p>
</section>

<section class="section">
    <div class="grid">
        {cards if cards else '<div class="empty">No matching collections yet.</div>'}
    </div>
</section>

</div>
</main>
"""

    canonical = absolute_url(relative_path)

    description = (
        f"Discover {len(items)} flirty message collections "
        f"related to {name}."
    )

    write_file(
        os.path.join(OUTPUT_DIR, relative_path),
        page_shell(
            f"{name} - {SITE_NAME}",
            description,
            canonical,
            content,
        ),
    )


def build_topic_and_tag_hubs(indexes):

    for slug, items in indexes["subcategories"].items():

        name = indexes["subcategory_names"][slug]

        build_collection_hub(
            slug,
            name,
            items,
            "topic",
        )

    for slug, items in indexes["tags"].items():

        name = indexes["tag_names"][slug]

        build_collection_hub(
            slug,
            name,
            items,
            "tag",
        )


# ============================================================
# LEGAL AND INFORMATION PAGES
# ============================================================


def build_legal_pages():

    dmca_content = f"""
<main>
<div class="container">

<section class="detail-hero">
    {freshness_badge()}
    <h1>DMCA & Copyright Policy</h1>

    <p class="muted">
        Information about copyright concerns and content removal.
    </p>
</section>

<section class="section">
<div class="card">

<h2>Copyright Complaints</h2>

<p>
{esc(SITE_NAME)} respects intellectual property rights.
If you believe that material published on this website
infringes your copyright, you may submit a written notice
requesting review and removal of the allegedly infringing
material.
</p>

<h2>Required Information</h2>

<ul>
<li>Your physical or electronic signature.</li>
<li>Identification of the copyrighted work.</li>
<li>Identification of the allegedly infringing material.</li>
<li>Your contact information.</li>
<li>A statement of good-faith belief that the use is unauthorized.</li>
<li>A statement that the information in your notice is accurate.</li>
</ul>

<h2>Submit a Notice</h2>

<p>
Email your complaint to:
<a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a>
</p>

<h2>Review Process</h2>

<p>
We review properly submitted copyright complaints and
may remove or restrict access to material where appropriate.
Please include sufficient details to help identify the
relevant content.
</p>

<p>
Submitting a false or misleading copyright complaint
may have legal consequences.
</p>

</div>
</section>

</div>
</main>
"""

    write_file(
        os.path.join(OUTPUT_DIR, "dmca.html"),
        page_shell(
            f"DMCA Copyright Policy - {SITE_NAME}",
            "Read the copyright and DMCA policy for Flirty Chat Openers.",
            absolute_url("dmca.html"),
            dmca_content,
        ),
    )

    section_2257 = f"""
<main>
<div class="container">

<section class="detail-hero">
    {freshness_badge()}
    <h1>18 U.S.C. § 2257 Statement</h1>
</section>

<section class="section">
<div class="card">

<h2>Website Content Statement</h2>

<p>
{esc(SITE_NAME)} is an informational website providing
text-based conversation starters, fictional message
examples, creative writing, and relationship-oriented
communication ideas.
</p>

<p>
This website does not produce or host explicit visual
depictions of actual sexually explicit conduct.
</p>

<h2>Content and Compliance</h2>

<p>
The website is intended for adults aged 18 and older.
An age confirmation mechanism is provided to restrict
access to visitors who indicate that they are under 18.
</p>

<p>
For questions about this statement or website content,
contact:
<a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a>
</p>

<p>
This informational statement is not a legal opinion
or a substitute for an independent legal compliance review.
</p>

</div>
</section>

</div>
</main>
"""

    write_file(
        os.path.join(OUTPUT_DIR, "2257.html"),
        page_shell(
            f"2257 Compliance Statement - {SITE_NAME}",
            "Read the 18 U.S.C. Section 2257 website content statement.",
            absolute_url("2257.html"),
            section_2257,
        ),
    )


# ============================================================
# XML SITEMAP STYLESHEET
# ============================================================


def build_sitemap_xsl():

    xsl = r"""<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="2.0"
xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
xmlns:s="http://www.sitemaps.org/schemas/sitemap/0.9">

<xsl:output method="html" encoding="UTF-8" indent="yes"/>

<xsl:template match="/">
<html>
<head>
<title>Website Sitemap</title>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<style>
body {
    background:#09080f;
    color:#f8f5ff;
    font-family:system-ui,sans-serif;
    margin:0;
    padding:35px 18px;
}
main {
    max-width:1000px;
    margin:auto;
}
h1 {color:#ec4899}
p {color:#aaa1b8}
table {
    width:100%;
    border-collapse:collapse;
    background:#151221;
    border-radius:12px;
    overflow:hidden;
}
td,th {
    padding:13px;
    text-align:left;
    border-bottom:1px solid #30283c;
}
a {color:#f472b6;overflow-wrap:anywhere}
th {color:#a5b4fc}
</style>
</head>

<body>
<main>
<h1>Flirty Chat Openers Sitemap</h1>
<p>Explore the indexed website URLs below.</p>

<table>
<thead>
<tr>
<th>URL</th>
<th>Last Modified</th>
<th>Priority</th>
</tr>
</thead>
<tbody>

<xsl:for-each select="s:urlset/s:url">
<tr>
<td>
<a>
<xsl:attribute name="href">
<xsl:value-of select="s:loc"/>
</xsl:attribute>
<xsl:value-of select="s:loc"/>
</a>
</td>
<td><xsl:value-of select="s:lastmod"/></td>
<td><xsl:value-of select="s:priority"/></td>
</tr>
</xsl:for-each>

</tbody>
</table>
</main>
</body>
</html>
</xsl:template>
</xsl:stylesheet>
"""

    write_file(
        os.path.join(OUTPUT_DIR, "sitemap.xsl"),
        xsl,
    )


# ============================================================
# XML SITEMAP GENERATION
# ============================================================


def build_sitemaps(rows, indexes):

    urls = []

    def add_url(path, priority="0.7", frequency="monthly"):

        urls.append({
            "loc": absolute_url(path),
            "lastmod": datetime.utcnow().strftime("%Y-%m-%d"),
            "priority": priority,
            "frequency": frequency,
        })

    add_url("index.html", "1.0", "weekly")

    for row in rows:
        add_url(
            row["detail_path"],
            "0.8",
            "monthly",
        )

    for slug, items in indexes["categories"].items():

        total_pages = max(
            1,
            (len(items) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
        )

        for page_number in range(1, total_pages + 1):

            add_url(
                f"category/{slug}/page-{page_number}.html",
                "0.8" if page_number == 1 else "0.6",
                "weekly",
            )

    for slug in indexes["subcategories"]:
        add_url(
            f"topic/{slug}.html",
            "0.7",
            "weekly",
        )

    for slug in indexes["tags"]:
        add_url(
            f"tag/{slug}.html",
            "0.6",
            "weekly",
        )

    add_url("dmca.html", "0.2", "yearly")
    add_url("2257.html", "0.2", "yearly")

    # XML sitemap protocol maximum: 50,000 URLs per file.
    chunk_size = 45000

    chunks = [
        urls[i:i + chunk_size]
        for i in range(0, len(urls), chunk_size)
    ]

    if not chunks:
        chunks = [[]]

    def xml_escape(value):
        return (
            str(value)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&apos;")
        )

    for number, chunk in enumerate(chunks, start=1):

        entries = []

        for item in chunk:

            entries.append(f"""
    <url>
        <loc>{xml_escape(item["loc"])}</loc>
        <lastmod>{item["lastmod"]}</lastmod>
        <changefreq>{item["frequency"]}</changefreq>
        <priority>{item["priority"]}</priority>
    </url>""")

        sitemap = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<?xml-stylesheet type="text/xsl" href="/sitemap.xsl"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            + "\n".join(entries)
            + "\n</urlset>\n"
        )

        write_file(
            os.path.join(
                OUTPUT_DIR,
                f"sitemap-{number}.xml"
            ),
            sitemap,
        )

    sitemap_index_entries = []

    for number in range(1, len(chunks) + 1):

        sitemap_index_entries.append(f"""
    <sitemap>
        <loc>{xml_escape(absolute_url(f"sitemap-{number}.xml"))}</loc>
        <lastmod>{datetime.utcnow().strftime("%Y-%m-%d")}</lastmod>
    </sitemap>""")

    sitemap_index = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<?xml-stylesheet type="text/xsl" href="/sitemap.xsl"?>\n'
        '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(sitemap_index_entries)
        + "\n</sitemapindex>\n"
    )

    write_file(
        os.path.join(OUTPUT_DIR, "sitemap.xml"),
        sitemap_index,
    )

    build_sitemap_xsl()


# ============================================================
# ROBOTS.TXT
# ============================================================


def build_robots():

    content = f"""# Robots policy for {SITE_NAME}

User-agent: *
Allow: /

Disallow: /404.html

Sitemap: {absolute_url("sitemap.xml")}
"""

    write_file(
        os.path.join(OUTPUT_DIR, "robots.txt"),
        content,
    )


# ============================================================
# BUILD INDIVIDUAL DETAIL PAGES
# ============================================================


def build_detail_pages(rows):

    for index, row in enumerate(rows, start=1):

        output = os.path.join(
            OUTPUT_DIR,
            row["detail_path"]
        )

        html_page = build_detail_page(row, rows)

        write_file(output, html_page)

        if index % 100 == 0:
            print(
                f"Generated {index}/{len(rows)} detail pages..."
            )


# ============================================================
# BUILD ERROR PAGE
# ============================================================


def build_404():

    content = """
<main>
<div class="container hero">
    <div class="eyebrow">404 - NOT FOUND</div>
    <h1>Oops! <span class="gradient-text">Wrong Conversation.</span></h1>
    <p>
        This page may have moved or no longer exists.
        Let's find a better opener.
    </p>
    <p>
        <a href="/" class="button">Back to Homepage</a>
    </p>
</div>
</main>
"""

    write_file(
        os.path.join(OUTPUT_DIR, "404.html"),
        page_shell(
            f"404 - Page Not Found | {SITE_NAME}",
            "The requested page could not be found.",
            absolute_url("404.html"),
            content,
        ),
    )


# ============================================================
# BUILD SUMMARY
# ============================================================


def print_summary(rows, indexes):

    total_categories = len(indexes["categories"])
    total_topics = len(indexes["subcategories"])
    total_tags = len(indexes["tags"])

    total_openers = sum(
        len(row["openers"])
        for row in rows
    )

    print("\n" + "=" * 58)
    print(f" {SITE_NAME} - BUILD COMPLETED")
    print("=" * 58)

    print(f" Website URL:       {BASE_URL}")
    print(f" Build year:        {CURRENT_YEAR}")
    print(f" Detail pages:      {len(rows)}")
    print(f" Total messages:    {total_openers}")
    print(f" Categories:        {total_categories}")
    print(f" Subcategories:     {total_topics}")
    print(f" Unique tags:       {total_tags}")
    print(f" Output directory:  {OUTPUT_DIR}/")

    print("-" * 58)

    print(" Generated files:")
    print("   index.html")
    print("   lines/*.html")
    print("   category/*/page-*.html")
    print("   topic/*.html")
    print("   tag/*.html")
    print("   sitemap.xml")
    print("   sitemap-1.xml")
    print("   sitemap.xsl")
    print("   robots.txt")
    print("   dmca.html")
    print("   2257.html")
    print("   404.html")

    print("=" * 58)


# ============================================================
# MAIN BUILD PIPELINE
# ============================================================


def main():

    print("\nStarting Flirty Chat Openers website builder...\n")

    # Load and validate CSV.
    rows = load_data()

    print(f"Loaded {len(rows)} content collections.")

    # Build unique category/topic/tag indexes.
    indexes = build_indexes(rows)

    # Clean previous generated output.
    if os.path.isdir(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)

    ensure_dir(OUTPUT_DIR)

    # Generate homepage.
    print("Generating homepage...")

    homepage = build_homepage(rows, indexes)

    write_file(
        os.path.join(OUTPUT_DIR, "index.html"),
        homepage,
    )

    # Generate collection detail pages.
    print("Generating detail pages...")

    build_detail_pages(rows)

    # Generate category pagination.
    print("Generating category hubs...")

    build_category_hubs(indexes)

    # Generate topic and tag hubs.
    print("Generating subcategory and tag hubs...")

    build_topic_and_tag_hubs(indexes)

    # Generate legal pages.
    print("Generating information pages...")

    build_legal_pages()

    # Generate 404.
    print("Generating 404 page...")

    build_404()

    # Generate sitemap and robots.
    print("Generating XML sitemaps...")

    build_sitemaps(rows, indexes)

    print("Generating robots.txt...")

    build_robots()

    # Report.
    print_summary(rows, indexes)

    print("\nBuild successful!")
    print(
        "Deploy the contents of the dist/ directory "
        "to Cloudflare Pages or Workers Static Assets."
    )


if __name__ == "__main__":

    try:
        main()

    except KeyboardInterrupt:
        print("\nBuild interrupted.")
        raise SystemExit(130)

    except Exception as error:
        print(f"\nBUILD ERROR: {error}")
        raise
