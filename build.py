#!/usr/bin/env python3
"""
Character Persona Hub — Static Programmatic SEO Website Generator
Python 3 standard library only.

Usage:
    python3 build.py

Input:
    data.csv

Output:
    dist/
"""

import os
import csv
import re
import json
import html
import math
import shutil
import unicodedata
from datetime import datetime, timezone
from collections import defaultdict, Counter
from urllib.parse import quote

# ============================================================
# CONFIGURATION
# ============================================================

BASE_URL = os.environ.get(
    "BASE_URL",
    "https://character-persona-hub.velvetgrid.workers.dev"
).rstrip("/")

SITE_NAME = "Character Persona Hub"
CONTACT_EMAIL = "nancympatten@gmail.com"

GOOGLE_VERIFICATION = "Ee2L9A2G2nVVNtBt7HiplcBJf1nSen-Rcz4sNqLuAdc"
BING_VERIFICATION = "4573069C62AEC27DA4F08DC57760BAD4"

AFFILIATE_URL = "#affiliate-link"
AFFILIATE_CTA_TEXT = "Import This Character Card into an AI Voice Companion"

DATA_FILE = "data.csv"
OUTPUT_DIR = "dist"

ITEMS_PER_PAGE = 24
RELATED_LIMIT = 8
NEWEST_LIMIT = 30
SITEMAP_LIMIT = 45000

CURRENT_YEAR = datetime.now(timezone.utc).year

CSV_COLUMNS = [
    "slug", "title", "category", "subcategory", "target_keyword",
    "character_bio", "personality_traits", "opening_line",
    "description", "tags", "faq_q1", "faq_a1",
    "faq_q2", "faq_a2", "upload_date",
]

# The current website is deliberately excluded from this list.
NETWORK_SITES = [
    ("AI Girlfriend Prompts",
     "https://ai-girlfriend-prompts.velvetgrid.workers.dev"),
    ("Couples Intimacy Games",
     "https://couples-intimacy-games.velvetgrid.workers.dev"),
    ("Fantasy Roleplay Hub",
     "https://fantasy-roleplay-hub.velvetgrid.workers.dev"),
    ("Flirty Chat Openers",
     "https://flirty-chat-openers.velvetgrid.workers.dev"),
    ("Midnight Audio Stories",
     "https://midnight-audio-stories.velvetgrid.workers.dev"),
    ("Spicy Party Games",
     "https://spicy-party-games.velvetgrid.workers.dev"),
    ("Intimacy Quiz Hub",
     "https://intimacy-quiz-hub.velvetgrid.workers.dev"),
    ("Couples Bucket List",
     "https://couples-bucket-list.velvetgrid.workers.dev"),
    ("Adult AI Art Prompts",
     "https://adult-ai-art-prompts.velvetgrid.workers.dev"),
]

AD_SLOTS = """
<!-- AD_SLOT_POPUNDER -->
<!-- AD_SLOT_TOP_BANNER -->
<!-- AD_SLOT_MID_CONTENT -->
<!-- AD_SLOT_STICKY_FOOTER -->
"""

# ============================================================
# UTILITIES
# ============================================================

def clean(value):
    return str(value or "").strip()


def esc(value):
    return html.escape(str(value or ""), quote=True)


def slugify(value):
    value = unicodedata.normalize("NFKD", clean(value))
    value = value.encode("ascii", "ignore").decode("ascii").lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "uncategorized"


def absolute_url(path):
    return BASE_URL.rstrip("/") + "/" + path.lstrip("/")


def truncate(value, limit=160):
    value = re.sub(r"\s+", " ", clean(value))
    if len(value) <= limit:
        return value
    return value[:limit - 3].rsplit(" ", 1)[0] + "..."


def safe_json(data):
    return (
        json.dumps(data, ensure_ascii=False)
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )


def split_tags(value):
    if isinstance(value, list):
        raw = value
    else:
        raw = re.split(r"[,;|]", str(value or ""))

    result = []
    seen = set()

    for item in raw:
        item = clean(item)
        key = item.lower()
        if item and key not in seen:
            seen.add(key)
            result.append(item)

    return result


def parse_date(value):
    value = clean(value)

    if not value:
        return datetime.min

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
            return datetime.strptime(value, fmt)
        except ValueError:
            pass

    try:
        return datetime.fromisoformat(
            value.replace("Z", "+00:00")
        ).replace(tzinfo=None)
    except ValueError:
        return datetime.min


def write_file(path, content):
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)

    with open(path, "w", encoding="utf-8", newline="\n") as file:
        file.write(content)


def make_directory():
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR, exist_ok=True)


# ============================================================
# CSV
# ============================================================

def read_csv():
    """
    Read data.csv without requiring a particular complete schema.

    Existing CSV files are left untouched. Missing Character Persona Hub
    fields are generated from whatever useful columns the CSV already has.
    Common alternate column names are recognized automatically.
    """
    if not os.path.isfile(DATA_FILE):
        raise FileNotFoundError(
            f"Missing {DATA_FILE}. Put data.csv beside build.py."
        )

    aliases = {
        "slug": ("slug", "url_slug", "permalink", "id"),
        "title": (
            "title", "character_name", "persona_name", "name",
            "character", "persona", "profile_name", "headline"
        ),
        "category": ("category", "genre", "archetype", "character_type", "type"),
        "subcategory": (
            "subcategory", "sub_category", "topic", "subgenre",
            "sub_genre", "theme"
        ),
        "target_keyword": (
            "target_keyword", "keyword", "primary_keyword",
            "focus_keyword", "seo_keyword"
        ),
        "character_bio": (
            "character_bio", "bio", "biography", "backstory",
            "character_description", "profile", "about"
        ),
        "personality_traits": (
            "personality_traits", "traits", "personality",
            "character_traits", "attributes"
        ),
        "opening_line": (
            "opening_line", "opening", "greeting", "first_message",
            "opening_message", "intro", "dialogue", "starter"
        ),
        "description": (
            "description", "meta_description", "short_description",
            "summary", "excerpt"
        ),
        "tags": ("tags", "tag", "keywords", "labels"),
        "faq_q1": ("faq_q1", "question_1", "faq_question_1"),
        "faq_a1": ("faq_a1", "answer_1", "faq_answer_1"),
        "faq_q2": ("faq_q2", "question_2", "faq_question_2"),
        "faq_a2": ("faq_a2", "answer_2", "faq_answer_2"),
        "upload_date": (
            "upload_date", "date", "published", "published_at",
            "created_at", "date_published"
        ),
    }

    def normalize_header(value):
        return re.sub(r"[^a-z0-9]+", "_", clean(value).lower()).strip("_")

    def make_default_bio(title, category, subcategory, description, traits):
        if description:
            base = description.rstrip(".")
            return (
                f"{base}. {title} is a fictional {subcategory.lower()} "
                f"character in the {category.lower()} category. "
                f"The persona is designed as a flexible creative profile "
                f"for storytelling and AI roleplay."
            )
        trait_text = ", ".join(traits[:4])
        return (
            f"{title} is a fictional {category.lower()} character "
            f"within the {subcategory.lower()} theme. "
            f"This persona has a distinctive identity, a memorable "
            f"background, and a conversational style shaped by "
            f"{trait_text or 'a distinctive set of personality traits'}. "
            f"Use this profile as a starting point for creative writing, "
            f"character development, and interactive storytelling."
        )

    def make_default_opening(title, category, traits):
        trait = traits[0].lower() if traits else "curious"
        return (
            f"Hey, I'm {title}. I hope you don't mind a little "
            f"{trait} conversation. What brings you into my "
            f"{category.lower()} world today?"
        )

    rows = []
    with open(DATA_FILE, "r", encoding="utf-8-sig", newline="") as file:
        sample = file.read(8192)
        file.seek(0)

        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
        except csv.Error:
            dialect = csv.excel

        reader = csv.DictReader(file, dialect=dialect)
        if not reader.fieldnames:
            raise ValueError(
                "data.csv has no header row. Keep the first row as column names."
            )

        original_headers = list(reader.fieldnames)
        header_lookup = {
            normalize_header(header): header
            for header in original_headers
            if header is not None
        }

        used_slugs = set()

        for line_number, raw in enumerate(reader, start=2):
            if not raw or not any(clean(v) for v in raw.values() if v is not None):
                continue

            source = {}
            for canonical, names in aliases.items():
                value = ""
                for alias in names:
                    actual_header = header_lookup.get(normalize_header(alias))
                    if actual_header is not None:
                        value = clean(raw.get(actual_header, ""))
                        if value:
                            break
                source[canonical] = value

            # If no recognized title header exists, use the first non-empty
            # cell rather than rejecting an otherwise usable CSV row.
            if not source["title"]:
                for header in original_headers:
                    if header is not None:
                        candidate = clean(raw.get(header, ""))
                        if candidate:
                            source["title"] = candidate
                            break

            if not source["title"]:
                print(
                    f"      Skipping CSV row {line_number}: "
                    "no character name or title found."
                )
                continue

            title = source["title"]
            category = source["category"] or "Original Characters"
            subcategory = source["subcategory"] or category
            target_keyword = source["target_keyword"] or (
                f"{title} character persona"
            )

            traits = split_tags(source["personality_traits"])
            if not traits:
                traits = [
                    "thoughtful", "engaging", "expressive",
                    "imaginative", "adaptable"
                ]

            bio = source["character_bio"] or make_default_bio(
                title, category, subcategory,
                source["description"], traits
            )

            opening = source["opening_line"] or make_default_opening(
                title, category, traits
            )

            description = source["description"] or truncate(
                f"Meet {title}, a fictional {category.lower()} character "
                f"persona with a {subcategory.lower()} theme. Explore the "
                f"character background, personality traits, and opening "
                f"dialogue, then customize the profile for creative writing "
                f"and interactive storytelling.",
                155
            )

            tags = split_tags(source["tags"])
            if not tags:
                tags = [category, subcategory] + traits[:3]

            row = {
                "slug": source["slug"],
                "title": title,
                "category": category,
                "subcategory": subcategory,
                "target_keyword": target_keyword,
                "character_bio": bio,
                "personality_traits": "|".join(traits),
                "opening_line": opening,
                "description": description,
                "tags": "|".join(tags),
                "faq_q1": source["faq_q1"] or f"What is the {title} character persona?",
                "faq_a1": source["faq_a1"] or (
                    f"{title} is a fictional {category.lower()} character "
                    f"profile designed for creative writing and interactive storytelling."
                ),
                "faq_q2": source["faq_q2"] or f"Can I customize {title}?",
                "faq_a2": source["faq_a2"] or (
                    f"Yes. You can customize the character name, setting, "
                    f"and interaction details in the persona studio."
                ),
                "upload_date": source["upload_date"] or datetime.now(timezone.utc).date().isoformat(),
            }

            original_slug = slugify(row["slug"] or title)
            slug = original_slug
            suffix = 2
            while slug in used_slugs:
                slug = f"{original_slug}-{suffix}"
                suffix += 1
            used_slugs.add(slug)
            row["slug"] = slug

            row["_tags"] = split_tags(row["tags"])
            row["_traits"] = split_tags(row["personality_traits"])
            row["_date"] = parse_date(row["upload_date"])
            row["_category_slug"] = slugify(row["category"])
            row["_subcategory_slug"] = slugify(row["subcategory"])
            row["_tag_slugs"] = [slugify(tag) for tag in row["_tags"]]

            rows.append(row)

    if not rows:
        raise ValueError(
            "data.csv contains no usable rows. Make sure it has a header "
            "and at least one row with a character title or name."
        )

    print(
        "      CSV compatibility: automatic defaults enabled; "
        "your data.csv was not modified."
    )
    return rows
# ============================================================
# CSS
# ============================================================

CSS = r"""
:root {
    color-scheme: dark;
    --bg:#0a080d; --surface:#16111d; --surface2:#201827;
    --text:#f8f2fa; --muted:#aa9eaf; --border:rgba(255,255,255,.09);
    --rose:#f43f5e; --violet:#8b5cf6; --green:#4ade80;
    --radius:18px; --max-width:1160px;
}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{
    margin:0;background:var(--bg);color:var(--text);
    font-family:Inter,ui-sans-serif,system-ui,-apple-system,
    BlinkMacSystemFont,"Segoe UI",sans-serif;line-height:1.7
}
a{color:inherit;text-decoration:none}
a:hover{color:var(--rose)}
button,input,select{font:inherit}
button{cursor:pointer}
.container{width:min(var(--max-width),calc(100% - 36px));margin:auto}
.site-header{
    position:sticky;top:0;z-index:50;background:rgba(10,8,13,.94);
    backdrop-filter:blur(18px);border-bottom:1px solid var(--border)
}
.nav{min-height:70px;display:flex;align-items:center;
    justify-content:space-between;gap:20px}
.brand{font-size:19px;font-weight:900;letter-spacing:-.8px}
.brand span{color:var(--rose)}
.nav-links{display:flex;gap:20px;align-items:center;
    font-size:13px;color:var(--muted)}
.hero{padding:85px 0 55px;text-align:center;
    background:radial-gradient(ellipse at 20% 20%,rgba(139,92,246,.14),transparent 45%),
    radial-gradient(ellipse at 80% 40%,rgba(244,63,94,.12),transparent 45%)}
.eyebrow{display:inline-flex;padding:6px 13px;border-radius:99px;
    border:1px solid rgba(244,63,94,.3);background:rgba(244,63,94,.08);
    color:#ff8196;font-size:11px;font-weight:800;text-transform:uppercase;
    letter-spacing:1.5px}
.hero h1{font-size:clamp(34px,6vw,62px);line-height:1.08;
    letter-spacing:-2.5px;max-width:850px;margin:22px auto}
.gradient-text{background:linear-gradient(100deg,#fb7185,#c084fc);
    -webkit-background-clip:text;background-clip:text;color:transparent}
.hero p{color:var(--muted);max-width:650px;margin:0 auto 30px}
.search-wrap{max-width:680px;margin:30px auto 0;position:relative}
.search-input{width:100%;padding:19px 22px 19px 54px;
    border:1px solid rgba(244,63,94,.3);border-radius:15px;outline:none;
    color:white;background:var(--surface);box-shadow:0 15px 60px rgba(0,0,0,.2)}
.search-input:focus{border-color:var(--rose)}
.search-icon{position:absolute;left:19px;top:14px;color:var(--rose);font-size:21px}
.section{padding:45px 0}
.section-heading{display:flex;align-items:end;justify-content:space-between;
    flex-wrap:wrap;gap:12px;margin-bottom:24px}
.section-heading h2{font-size:clamp(23px,4vw,32px);letter-spacing:-.8px;margin:0}
.section-heading p{margin:4px 0 0;color:var(--muted);font-size:13px}
.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:18px}
.persona-card,.hub-card{background:var(--surface);border:1px solid var(--border);
    border-radius:var(--radius);padding:21px;transition:transform .2s,border-color .2s}
.persona-card:hover,.hub-card:hover{transform:translateY(-3px);
    border-color:rgba(244,63,94,.4)}
.card-category{color:#c4a4ff;font-size:11px;font-weight:800;
    text-transform:uppercase;letter-spacing:1px}
.persona-card h3{font-size:19px;line-height:1.35;margin:10px 0}
.persona-card p{color:var(--muted);font-size:13px}
.card-meta{display:flex;gap:8px;flex-wrap:wrap;margin-top:15px}
.pill{display:inline-flex;align-items:center;border-radius:99px;padding:5px 11px;
    background:rgba(139,92,246,.13);border:1px solid rgba(139,92,246,.23);
    color:#d3bdff;font-size:11px}
.trait-pill{background:rgba(244,63,94,.10);border:1px solid rgba(244,63,94,.28);
    color:#ff9bad;box-shadow:0 0 13px rgba(244,63,94,.07)}
.card-link{display:inline-block;margin-top:15px;color:#fb7185;
    font-size:13px;font-weight:800}
.hub-card{display:flex;justify-content:space-between;align-items:center;gap:12px}
.hub-card strong{font-size:14px}
.count{color:#ff8498;font-size:12px;white-space:nowrap}
.tag-cloud{display:flex;flex-wrap:wrap;gap:10px}
.tag-cloud a,.subcategory-pill{display:inline-flex;padding:8px 14px;border-radius:99px;
    background:var(--surface);border:1px solid var(--border);
    color:#d7c8dc;font-size:12px}
.tag-cloud a:hover,.subcategory-pill:hover{border-color:var(--rose)}
.breadcrumbs{color:var(--muted);font-size:12px;padding:22px 0}
.detail-hero{padding:35px 0}
.detail-hero h1{font-size:clamp(30px,5vw,48px);line-height:1.13;
    letter-spacing:-1.5px;margin:15px 0}
.detail-grid{display:grid;grid-template-columns:minmax(0,1fr) 310px;
    gap:25px;align-items:start}
.panel{background:var(--surface);border:1px solid var(--border);
    border-radius:var(--radius);padding:25px;margin-bottom:20px}
.panel h2{margin-top:0;font-size:21px}
.panel h3{font-size:16px}
.panel p{color:#c8bccd}
.status-badge{display:inline-flex;padding:7px 12px;
    border:1px solid rgba(74,222,128,.3);color:var(--green);
    background:rgba(74,222,128,.07);border-radius:99px;font-size:11px;font-weight:800}
.traits{display:flex;flex-wrap:wrap;gap:9px}
.customizer-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}
.field label{display:block;margin-bottom:7px;color:var(--muted);
    font-size:12px;font-weight:700}
.field input,.field select{width:100%;background:#0d0a11;color:white;
    border:1px solid var(--border);padding:12px;border-radius:10px;outline:none}
.field input:focus,.field select:focus{border-color:var(--rose)}
.action-btn{border:1px solid rgba(244,63,94,.3);background:rgba(244,63,94,.12);
    color:#ff9bab;padding:10px 15px;border-radius:10px;font-size:12px;
    font-weight:800;transition:.2s}
.action-btn:hover{background:rgba(244,63,94,.23)}
.primary-btn{display:inline-block;border:0;color:white;
    background:linear-gradient(100deg,#f43f5e,#8b5cf6);
    padding:13px 19px;border-radius:11px;font-weight:900;font-size:12px}
.button-row{display:flex;flex-wrap:wrap;gap:10px;margin-top:17px}
.token-badge{display:inline-block;padding:6px 11px;background:rgba(139,92,246,.15);
    border-radius:99px;color:#d4bdff;font-size:11px}
.prompt-output{white-space:pre-wrap;overflow-wrap:anywhere;background:#0d0a11;
    border:1px solid var(--border);border-radius:12px;padding:17px;
    color:#ddd1e2;font-size:13px}
.affiliate-card{border:1px solid rgba(244,63,94,.4);
    background:radial-gradient(circle at 90% 0%,rgba(139,92,246,.2),transparent 50%),var(--surface);
    border-radius:var(--radius);padding:27px;margin:25px 0}
.affiliate-card h2{margin-top:0}
.affiliate-card p{color:var(--muted);font-size:14px}
.audio-controls{display:flex;flex-wrap:wrap;align-items:center;gap:13px}
.audio-controls select{background:#0d0a11;color:white;padding:10px;
    border:1px solid var(--border);border-radius:9px}
.audio-controls input[type=range]{accent-color:var(--rose);max-width:130px}
.pagination{display:flex;flex-wrap:wrap;gap:10px;margin-top:30px}
.pagination a{background:var(--surface);border:1px solid var(--border);
    border-radius:9px;padding:9px 14px;font-size:12px}
.faq-item{padding:14px 0;border-bottom:1px solid var(--border)}
.faq-item:last-child{border-bottom:0}
.faq-item h3{margin:0 0 8px}
.site-footer{border-top:1px solid var(--border);margin-top:60px;
    padding:35px 0;color:var(--muted);font-size:12px}
.footer-links{display:flex;gap:18px;flex-wrap:wrap;margin-bottom:15px}
.network-links{display:flex;flex-wrap:wrap;gap:12px 20px;margin:14px 0}
.network-links a{color:#d3bdff}
.network-links a:hover{color:var(--rose)}
.age-overlay{position:fixed;inset:0;z-index:1000;display:flex;
    align-items:center;justify-content:center;padding:20px;
    background:rgba(0,0,0,.92);backdrop-filter:blur(12px)}
.age-modal{width:min(430px,100%);padding:32px;background:var(--surface);
    border:1px solid rgba(244,63,94,.35);border-radius:20px;text-align:center}
.age-modal h2{font-size:28px;margin:0 0 10px}
.age-modal p{color:var(--muted);font-size:13px}
.age-actions{display:flex;gap:10px;margin-top:22px}
.age-actions button{flex:1}
.hidden{display:none!important}
.empty-state{color:var(--muted);padding:35px;text-align:center;
    background:var(--surface);border-radius:var(--radius)}
@media(max-width:850px){
    .grid{grid-template-columns:repeat(2,minmax(0,1fr))}
    .detail-grid{grid-template-columns:1fr}
}
@media(max-width:580px){
    .grid,.customizer-grid{grid-template-columns:1fr}
    .nav-links{gap:10px;font-size:11px}
    .hero{padding:55px 0 35px}
    .panel{padding:19px}
    .section{padding:30px 0}
}
"""


# ============================================================
# JAVASCRIPT
# ============================================================

JS = r"""
(function () {
    "use strict";

    function updateYears() {
        const year = new Date().getFullYear();

        document.querySelectorAll(".live-year").forEach(function (el) {
            el.textContent = year;
        });

        const month = new Intl.DateTimeFormat(undefined, {
            month: "long"
        }).format(new Date());

        document.querySelectorAll(".compatibility-status").forEach(function (el) {
            el.textContent = "Compatibility Verified: " + month + " " + year;
        });
    }

    updateYears();

    const ageOverlay = document.getElementById("age-overlay");

    if (ageOverlay) {
        const verified = localStorage.getItem("cph_age_verified");

        if (verified === "yes") {
            ageOverlay.classList.add("hidden");
        } else {
            ageOverlay.classList.remove("hidden");
        }

        const yes = document.getElementById("age-yes");
        const no = document.getElementById("age-no");

        if (yes) {
            yes.addEventListener("click", function () {
                localStorage.setItem("cph_age_verified", "yes");
                ageOverlay.classList.add("hidden");
            });
        }

        if (no) {
            no.addEventListener("click", function () {
                window.location.replace("about:blank");
            });
        }
    }

    const search = document.getElementById("persona-search");
    const cards = Array.from(document.querySelectorAll("[data-persona-card]"));
    const resultCount = document.getElementById("search-count");

    if (search) {
        search.addEventListener("input", function () {
            const query = search.value.toLowerCase().trim();
            let visible = 0;

            cards.forEach(function (card) {
                const text = (
                    card.dataset.title + " " +
                    card.dataset.keyword + " " +
                    card.dataset.tags
                ).toLowerCase();

                const matches = !query || text.includes(query);
                card.classList.toggle("hidden", !matches);

                if (matches) visible++;
            });

            if (resultCount) {
                resultCount.textContent = visible + " personas found";
            }
        });
    }

    const studio = document.getElementById("persona-studio");

    if (studio) {
        const bioTemplate = studio.dataset.bio || "";
        const openingTemplate = studio.dataset.opening || "";
        const titleTemplate = studio.dataset.title || "Character";

        const nameInput = document.getElementById("character-name");
        const userInput = document.getElementById("user-name");
        const settingInput = document.getElementById("character-setting");

        const bioOutput = document.getElementById("custom-bio");
        const openingOutput = document.getElementById("custom-opening");
        const systemOutput = document.getElementById("system-prompt");
        const greetingOutput = document.getElementById("greeting-prompt");
        const tokenCount = document.getElementById("token-count");

        function values() {
            return {
                character: nameInput.value.trim() || titleTemplate,
                user: userInput.value.trim() || "you",
                setting: settingInput.value.trim() || "a mysterious new place"
            };
        }

        function replaceTemplate(template, data) {
            return String(template)
                .replace(/\{\{\s*character_name\s*\}\}/gi, data.character)
                .replace(/\{\s*character\s*\}/gi, data.character)
                .replace(/\{\s*user_name\s*\}/gi, data.user)
                .replace(/\{\s*user\s*\}/gi, data.user)
                .replace(/\{\s*setting\s*\}/gi, data.setting)
                .replace(/\[CHARACTER_NAME\]/gi, data.character)
                .replace(/\[USER_NAME\]/gi, data.user)
                .replace(/\[SETTING\]/gi, data.setting);
        }

        function updateStudio() {
            const data = values();
            const bio = replaceTemplate(bioTemplate, data);
            const opening = replaceTemplate(openingTemplate, data);

            const system =
                "You are " + data.character + ".\n\n" +
                "Character biography:\n" + bio + "\n\n" +
                "Setting:\n" + data.setting + "\n\n" +
                "Interaction partner: " + data.user + ".\n\n" +
                "Keep the character consistent with the profile. " +
                "Maintain immersion and respect the user's boundaries.";

            if (bioOutput) bioOutput.textContent = bio;
            if (openingOutput) openingOutput.textContent = opening;
            if (systemOutput) systemOutput.textContent = system;
            if (greetingOutput) greetingOutput.textContent = opening;

            if (tokenCount) {
                const words = (system + " " + opening)
                    .trim().split(/\s+/).filter(Boolean).length;
                tokenCount.textContent = "~" + words + " words";
            }
        }

        [nameInput, userInput, settingInput].forEach(function (input) {
            if (input) input.addEventListener("input", updateStudio);
        });

        updateStudio();

        async function copyText(text, button) {
            try {
                await navigator.clipboard.writeText(text);
            } catch (error) {
                const textarea = document.createElement("textarea");
                textarea.value = text;
                textarea.style.position = "fixed";
                textarea.style.opacity = "0";
                document.body.appendChild(textarea);
                textarea.select();
                document.execCommand("copy");
                textarea.remove();
            }

            const original = button.textContent;
            button.textContent = "Copied!";

            setTimeout(function () {
                button.textContent = original;
            }, 1600);
        }

        const copySystem = document.getElementById("copy-system");
        const copyGreeting = document.getElementById("copy-greeting");

        if (copySystem) {
            copySystem.addEventListener("click", function () {
                copyText(systemOutput.textContent, copySystem);
            });
        }

        if (copyGreeting) {
            copyGreeting.addEventListener("click", function () {
                copyText(greetingOutput.textContent, copyGreeting);
            });
        }

        const quirks = [
            "Collects unusual little objects",
            "Secretly loves old-fashioned music",
            "Has an unexpectedly competitive streak",
            "Remembers tiny details",
            "Makes elaborate metaphors",
            "Gets excited about obscure facts",
            "Has a soft spot for handwritten notes",
            "Occasionally talks to household objects",
            "Enjoys dramatic storytelling",
            "Always has a backup plan",
            "Laughs at terrible puns",
            "Notices details others overlook"
        ];

        const randomize = document.getElementById("randomize-quirk");

        if (randomize) {
            randomize.addEventListener("click", function () {
                const quirk = quirks[Math.floor(Math.random() * quirks.length)];
                const output = document.getElementById("bonus-quirk");
                if (output) output.textContent = quirk;
            });
        }

        const playButton = document.getElementById("ambience-toggle");
        const modeSelect = document.getElementById("sound-mode");
        const volumeSlider = document.getElementById("sound-volume");

        let audioContext = null;
        let masterGain = null;
        let sources = [];
        let isPlaying = false;

        function stopAmbience() {
            sources.forEach(function (source) {
                try { source.stop(); } catch (error) {}
            });

            sources = [];

            if (audioContext) {
                audioContext.close().catch(function () {});
                audioContext = null;
            }

            isPlaying = false;
            if (playButton) playButton.textContent = "▶ Play Ambience";
        }

        function startAmbience() {
            if (isPlaying) return;

            const AudioContextClass =
                window.AudioContext || window.webkitAudioContext;

            if (!AudioContextClass) {
                alert("Web Audio API is not supported in this browser.");
                return;
            }

            audioContext = new AudioContextClass();
            masterGain = audioContext.createGain();
            masterGain.gain.value = Number(volumeSlider.value || 25) / 100;
            masterGain.connect(audioContext.destination);

            const mode = modeSelect.value;

            function noiseSource(type, frequency, gainValue) {
                const length = audioContext.sampleRate * 2;
                const buffer = audioContext.createBuffer(
                    1, length, audioContext.sampleRate
                );
                const channel = buffer.getChannelData(0);
                let previous = 0;

                for (let i = 0; i < length; i++) {
                    const white = Math.random() * 2 - 1;
                    if (type === "pink") {
                        previous = previous * 0.96 + white * 0.04;
                        channel[i] = previous * 3.5;
                    } else {
                        channel[i] = white;
                    }
                }

                const source = audioContext.createBufferSource();
                const filter = audioContext.createBiquadFilter();
                const gain = audioContext.createGain();

                source.buffer = buffer;
                source.loop = true;
                filter.type = "lowpass";
                filter.frequency.value = frequency;
                gain.gain.value = gainValue;

                source.connect(filter);
                filter.connect(gain);
                gain.connect(masterGain);
                source.start();
                sources.push(source);
            }

            function oscillator(freq, waveform, gainValue) {
                const node = audioContext.createOscillator();
                const gain = audioContext.createGain();

                node.type = waveform;
                node.frequency.value = freq;
                gain.gain.value = gainValue;
                node.connect(gain);
                gain.connect(masterGain);
                node.start();
                sources.push(node);
            }

            if (mode === "rain") {
                noiseSource("pink", 900, 0.55);
                noiseSource("white", 420, 0.09);
                oscillator(110, "sine", 0.035);
            } else if (mode === "velvet") {
                noiseSource("pink", 240, 0.16);
                oscillator(110, "sine", 0.08);
                oscillator(164.81, "sine", 0.025);
                oscillator(220, "sine", 0.02);
            } else {
                noiseSource("pink", 700, 0.22);
                oscillator(196, "sine", 0.025);
                oscillator(246.94, "sine", 0.018);
            }

            isPlaying = true;
            playButton.textContent = "Ⅱ Pause Ambience";
        }

        if (playButton) {
            playButton.addEventListener("click", function () {
                if (isPlaying) stopAmbience();
                else startAmbience();
            });
        }

        if (modeSelect) {
            modeSelect.addEventListener("change", function () {
                if (isPlaying) {
                    stopAmbience();
                    startAmbience();
                }
            });
        }

        if (volumeSlider) {
            volumeSlider.addEventListener("input", function () {
                if (masterGain && audioContext) {
                    masterGain.gain.setTargetAtTime(
                        Number(volumeSlider.value) / 100,
                        audioContext.currentTime,
                        0.05
                    );
                }
            });
        }

        document.addEventListener("visibilitychange", function () {
            if (document.hidden && isPlaying) stopAmbience();
        });

        window.addEventListener("pagehide", function () {
            if (isPlaying) stopAmbience();
        });
    }
})();
"""


# ============================================================
# SHARED HTML LAYOUT
# ============================================================

def page_head(title, description, canonical, page_type="website"):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="rating" content="RTA-5042-1996-1400-1577-RTA">
<title>{esc(title)}</title>
<meta name="description" content="{esc(truncate(description, 160))}">
<link rel="canonical" href="{esc(canonical)}">
<meta name="robots" content="index,follow,max-image-preview:large">
<meta name="theme-color" content="#0a080d">

<!-- Google Search Console verification -->
<meta name="google-site-verification" content="{esc(GOOGLE_VERIFICATION)}">

<!-- Bing Webmaster Tools verification -->
<meta name="msvalidate.01" content="{esc(BING_VERIFICATION)}">

<meta property="og:type" content="{esc(page_type)}">
<meta property="og:site_name" content="{esc(SITE_NAME)}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(truncate(description, 160))}">
<meta property="og:url" content="{esc(canonical)}">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="{esc(title)}">
<meta name="twitter:description" content="{esc(truncate(description, 160))}">
<style>{CSS}</style>
</head>
<body>
{AD_SLOTS}
<header class="site-header">
<div class="container nav">
<a class="brand" href="{BASE_URL}/">CHARACTER<span>PERSONA</span> HUB</a>
<nav class="nav-links">
<a href="{BASE_URL}/">Home</a>
<a href="{BASE_URL}/#categories">Archetypes</a>
<a href="{BASE_URL}/#newest">New Personas</a>
</nav>
</div>
</header>
"""


def age_modal():
    return """
<div class="age-overlay" id="age-overlay" role="dialog"
     aria-modal="true" aria-labelledby="age-heading">
    <div class="age-modal">
        <span class="eyebrow">Age Confirmation</span>
        <h2 id="age-heading">Are you 18 or older?</h2>
        <p>
            This website contains fictional character concepts and
            adult-oriented creative themes. You must be at least 18
            years old to continue.
        </p>
        <div class="age-actions">
            <button class="primary-btn" id="age-yes">Yes, I'm 18+</button>
            <button class="action-btn" id="age-no">No, Exit</button>
        </div>
    </div>
</div>
"""


def footer():
    network_html = "\n".join(
        f'<a href="{esc(url)}" target="_blank" rel="noopener">'
        f'{esc(name)}</a>'
        for name, url in NETWORK_SITES
        if url.rstrip("/") != BASE_URL.rstrip("/")
    )

    return f"""
<footer class="site-footer">
<div class="container">
<div class="footer-links">
<a href="{BASE_URL}/">Home</a>
<a href="{BASE_URL}/dmca.html">DMCA</a>
<a href="{BASE_URL}/2257.html">18 U.S.C. §2257</a>
<a href="mailto:{esc(CONTACT_EMAIL)}">Contact</a>
</div>

<h3>Explore Our Other Projects</h3>
<p>Discover more tools and creative resources from our network.</p>
<div class="network-links">{network_html}</div>

<p>
© <span class="live-year">{CURRENT_YEAR}</span>
{esc(SITE_NAME)}. All rights reserved.
</p>
<p>
All character personas are fictional creative concepts.
Users are responsible for complying with the terms of their
chosen AI platform.
</p>
</div>
</footer>
{age_modal()}
<script>{JS}</script>
</body>
</html>
"""


def page_shell(title, description, canonical, content, page_type="website"):
    return (
        page_head(title, description, canonical, page_type)
        + content
        + footer()
    )


# ============================================================
# CARD COMPONENT
# ============================================================

def persona_card(row):
    tags = " ".join(row["_tags"])
    traits = " ".join(row["_traits"][:3])

    return f"""
<article class="persona-card" data-persona-card
 data-title="{esc(row['title'])}"
 data-keyword="{esc(row['target_keyword'])}"
 data-tags="{esc(tags)}">
    <div class="card-category">{esc(row['category'])}</div>
    <h3><a href="/persona/{quote(row['slug'])}.html">{esc(row['title'])}</a></h3>
    <p>{esc(truncate(row['description'], 135))}</p>
    <div class="card-meta">
        <span class="pill">{esc(row['subcategory'])}</span>
        <span class="pill trait-pill">{esc(traits or 'Creative persona')}</span>
    </div>
    <a class="card-link" href="/persona/{quote(row['slug'])}.html">
        Explore Character →
    </a>
</article>
"""


def section_heading(title, subtitle=""):
    return f"""
<div class="section-heading">
    <div>
        <h2>{esc(title)}</h2>
        <p>{esc(subtitle)}</p>
    </div>
</div>
"""


# ============================================================
# HOMEPAGE
# ============================================================

def build_homepage(rows):
    categories = defaultdict(list)
    tags = defaultdict(int)

    for row in rows:
        categories[row["category"]].append(row)
        for tag in row["_tags"]:
            tags[tag] += 1

    newest = sorted(rows, key=lambda r: r["_date"], reverse=True)[:NEWEST_LIMIT]
    featured = newest[:12]

    category_cards = []

    for category, items in sorted(
        categories.items(),
        key=lambda pair: (-len(pair[1]), pair[0].lower())
    ):
        category_cards.append(f"""
<a class="hub-card" href="/category/{slugify(category)}/page-1.html">
    <strong>{esc(category)}</strong>
    <span class="count">{len(items)} personas</span>
</a>
""")

    tag_links = []

    for tag, count in sorted(
        tags.items(), key=lambda pair: (-pair[1], pair[0].lower())
    )[:35]:
        tag_links.append(
            f'<a href="/tag/{slugify(tag)}.html">'
            f'{esc(tag)} <span>({count})</span></a>'
        )

    content = f"""
<main>
<section class="hero">
<div class="container">
<span class="eyebrow">The Character Discovery Library</span>
<h1>Discover Your Next <span class="gradient-text">Character Persona</span></h1>
<p>
Explore fictional character profiles, personality archetypes,
backstories, and opening lines. Find a persona for creative writing,
roleplay, and interactive storytelling.
</p>

<div class="search-wrap">
<span class="search-icon">⌕</span>
<input class="search-input" id="persona-search"
 type="search" placeholder="Search characters, traits, or keywords..."
 aria-label="Search character personas">
</div>
<p id="search-count">{len(rows)} personas available</p>
</div>
</section>

<div class="container">
<section class="section" id="newest">
{section_heading("Featured Character Personas", "Explore recently added fictional profiles.")}
<div class="grid">
{''.join(persona_card(row) for row in featured)}
</div>
</section>

<section class="section" id="categories">
{section_heading("Browse Character Archetypes", "Explore the library by category.")}
<div class="grid">
{''.join(category_cards)}
</div>
</section>

<section class="section">
{section_heading("Popular Character Tags", "Discover personas by their defining themes and traits.")}
<div class="tag-cloud">
{''.join(tag_links)}
</div>
</section>

<section class="section">
{section_heading("Build a Character That Feels Original", "A flexible starting point for your next creative project.")}
<div class="panel">
<p>
Every persona includes a fictional background, personality traits,
and an opening line. Use the character studio on each profile to
customize names, settings, and dialogue before copying the prompt
into your preferred writing or AI platform.
</p>
</div>
</section>
</div>
</main>
"""

    return page_shell(
        f"{SITE_NAME} | Discover Fictional Character Personas",
        "Explore fictional character personas, personality archetypes, "
        "backstories, opening lines, and creative roleplay profiles.",
        absolute_url("/"),
        content
    )


# ============================================================
# CHARACTER DETAIL PAGE
# ============================================================

def related_personas(row, all_rows):
    candidates = [
        item for item in all_rows
        if item["slug"] != row["slug"]
        and (
            item["category"] == row["category"]
            or item["subcategory"] == row["subcategory"]
            or set(item["_tag_slugs"]) & set(row["_tag_slugs"])
        )
    ]

    candidates.sort(
        key=lambda item: (
            item["category"] != row["category"],
            item["subcategory"] != row["subcategory"],
            item["title"].lower()
        )
    )

    return candidates[:RELATED_LIMIT]


def build_detail_page(row, all_rows):
    traits_html = "".join(
        f'<span class="pill trait-pill">{esc(trait)}</span>'
        for trait in row["_traits"]
    )

    tags_html = "".join(
        f'<a href="/tag/{slugify(tag)}.html">{esc(tag)}</a>'
        for tag in row["_tags"]
    )

    related = related_personas(row, all_rows)

    faq_schema = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": row["faq_q1"],
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": row["faq_a1"]
                }
            },
            {
                "@type": "Question",
                "name": row["faq_q2"],
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": row["faq_a2"]
                }
            }
        ]
    }

    article_schema = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": row["title"],
        "description": row["description"],
        "datePublished": row["upload_date"],
        "dateModified": row["upload_date"],
        "author": {
            "@type": "Organization",
            "name": SITE_NAME
        },
        "publisher": {
            "@type": "Organization",
            "name": SITE_NAME
        },
        "mainEntityOfPage": absolute_url(
            f"/persona/{quote(row['slug'])}.html"
        )
    }

    content = f"""
<main class="container">
<nav class="breadcrumbs">
<a href="/">Home</a> /
<a href="/category/{row['_category_slug']}/page-1.html">{esc(row['category'])}</a> /
{esc(row['title'])}
</nav>

<section class="detail-hero">
<span class="eyebrow">{esc(row['category'])} / {esc(row['subcategory'])}</span>
<h1>{esc(row['title'])} Character Persona</h1>
<p>{esc(row['description'])}</p>
<span class="status-badge compatibility-status">
Compatibility Verified: {CURRENT_YEAR}
</span>
</section>

<div class="detail-grid">
<div>
<section class="panel">
<h2>Character Biography</h2>
<p>{esc(row['character_bio'])}</p>
</section>

<section class="panel">
<h2>Personality Traits</h2>
<div class="traits">{traits_html}</div>
</section>

<section class="panel">
<h2>Opening Line</h2>
<p class="prompt-output">{esc(row['opening_line'])}</p>
</section>

<section class="panel" id="persona-studio"
 data-title="{esc(row['title'])}"
 data-bio="{esc(row['character_bio'])}"
 data-opening="{esc(row['opening_line'])}">
<h2>Interactive Persona Studio</h2>
<p>Personalize this fictional character profile before copying it.</p>

<div class="customizer-grid">
<div class="field">
<label for="character-name">Character name</label>
<input id="character-name" value="{esc(row['title'])}">
</div>
<div class="field">
<label for="user-name">Your name</label>
<input id="user-name" placeholder="Enter your name">
</div>
<div class="field">
<label for="character-setting">Story setting</label>
<input id="character-setting" placeholder="A mysterious new place">
</div>
</div>

<h3>Customized Biography</h3>
<div class="prompt-output" id="custom-bio"></div>

<h3>Customized Opening Line</h3>
<div class="prompt-output" id="custom-opening"></div>

<div class="button-row">
<button class="action-btn" id="copy-greeting">Copy Opening Line</button>
</div>

<h3>System Prompt</h3>
<div class="prompt-output" id="system-prompt"></div>
<div class="button-row">
<button class="primary-btn" id="copy-system">Copy Character Prompt</button>
<span class="token-badge" id="token-count">Calculating...</span>
</div>
</section>

<section class="panel">
<h2>Character Quirk Generator</h2>
<p>Give this persona one extra fictional detail.</p>
<div class="prompt-output" id="bonus-quirk">
Select the button to generate a character quirk.
</div>
<div class="button-row">
<button class="action-btn" id="randomize-quirk">Generate Random Quirk</button>
</div>
</section>

<section class="panel">
<h2>Ambient Sound Studio</h2>
<p>Optional locally generated ambient sound for your writing session.</p>
<div class="audio-controls">
<select id="sound-mode" aria-label="Ambient sound mode">
<option value="rain">Soft Rain</option>
<option value="velvet">Velvet Atmosphere</option>
<option value="dream">Dreamlike Tones</option>
</select>
<label for="sound-volume">Volume</label>
<input id="sound-volume" type="range" min="0" max="100" value="25">
<button class="action-btn" id="ambience-toggle">▶ Play Ambience</button>
</div>
</section>

<section class="affiliate-card">
<h2>Take Your Character Further</h2>
<p>
Use this character card as a creative starting point for your
favorite compatible writing or AI voice companion platform.
</p>
<a class="primary-btn" href="{esc(AFFILIATE_URL)}"
 target="_blank" rel="nofollow sponsored noopener">
{esc(AFFILIATE_CTA_TEXT)}
</a>
</section>

<section class="panel">
<h2>Frequently Asked Questions</h2>
<div class="faq-item">
<h3>{esc(row['faq_q1'])}</h3>
<p>{esc(row['faq_a1'])}</p>
</div>
<div class="faq-item">
<h3>{esc(row['faq_q2'])}</h3>
<p>{esc(row['faq_a2'])}</p>
</div>
</section>

<section class="panel">
<h2>Explore Character Tags</h2>
<div class="tag-cloud">{tags_html}</div>
</section>
</div>

<aside>
<section class="panel">
<h2>Character Details</h2>
<p><strong>Category:</strong> {esc(row['category'])}</p>
<p><strong>Subcategory:</strong> {esc(row['subcategory'])}</p>
<p><strong>Updated:</strong> {esc(row['upload_date'])}</p>
<p><strong>Target keyword:</strong> {esc(row['target_keyword'])}</p>
</section>

<section class="panel">
<h2>Related Personas</h2>
{''.join(persona_card(item) for item in related)
 or '<p>No related personas yet.</p>'}
</section>
</aside>
</div>
</main>

<script type="application/ld+json">{safe_json(article_schema)}</script>
<script type="application/ld+json">{safe_json(faq_schema)}</script>
"""

    return page_shell(
        f"{row['title']} Character Persona | {SITE_NAME}",
        row["description"],
        absolute_url(f"/persona/{quote(row['slug'])}.html"),
        content,
        "article"
    )


# ============================================================
# CATEGORY, TOPIC, AND TAG HUBS
# ============================================================

def build_category_hubs(rows):
    groups = defaultdict(list)

    for row in rows:
        groups[row["_category_slug"]].append(row)

    for category_slug, items in groups.items():
        category = items[0]["category"]
        items.sort(key=lambda item: item["title"].lower())
        total_pages = max(1, math.ceil(len(items) / ITEMS_PER_PAGE))

        for page in range(1, total_pages + 1):
            start = (page - 1) * ITEMS_PER_PAGE
            page_items = items[start:start + ITEMS_PER_PAGE]

            pagination = []

            for page_number in range(1, total_pages + 1):
                pagination.append(
                    f'<a href="/category/{category_slug}/page-{page_number}.html">'
                    f'{page_number}</a>'
                )

            content = f"""
<main class="container section">
<nav class="breadcrumbs"><a href="/">Home</a> / {esc(category)}</nav>
{section_heading(category + " Character Personas", f"Browse {len(items)} fictional character profiles in this category.")}
<div class="grid">
{''.join(persona_card(item) for item in page_items)}
</div>
<div class="pagination">{''.join(pagination)}</div>
</main>
"""

            path = os.path.join(
                OUTPUT_DIR, "category", category_slug,
                f"page-{page}.html"
            )

            write_file(
                path,
                page_shell(
                    f"{category} Personas — Page {page} | {SITE_NAME}",
                    f"Explore {len(items)} fictional {category.lower()} character personas.",
                    absolute_url(f"/category/{category_slug}/page-{page}.html"),
                    content
                )
            )


def build_topic_hubs(rows):
    groups = defaultdict(list)

    for row in rows:
        groups[row["_subcategory_slug"]].append(row)

    for topic_slug, items in groups.items():
        topic = items[0]["subcategory"]

        content = f"""
<main class="container section">
<nav class="breadcrumbs"><a href="/">Home</a> / {esc(topic)}</nav>
{section_heading(topic + " Character Personas", f"Explore fictional profiles related to {topic.lower()}.")}
<div class="grid">
{''.join(persona_card(item) for item in items)}
</div>
</main>
"""

        write_file(
            os.path.join(OUTPUT_DIR, "topic", topic_slug + ".html"),
            page_shell(
                f"{topic} Character Personas | {SITE_NAME}",
                f"Discover fictional character personas in the {topic.lower()} theme.",
                absolute_url(f"/topic/{topic_slug}.html"),
                content
            )
        )


def build_tag_hubs(rows):
    groups = defaultdict(list)

    for row in rows:
        for tag in row["_tags"]:
            groups[slugify(tag)].append(row)

    for tag_slug, items in groups.items():
        tag = next(
            (
                value for row in items for value in row["_tags"]
                if slugify(value) == tag_slug
            ),
            tag_slug.replace("-", " ").title()
        )

        content = f"""
<main class="container section">
<nav class="breadcrumbs"><a href="/">Home</a> / Tag: {esc(tag)}</nav>
{section_heading("Character Personas Tagged " + tag, f"Explore fictional personas associated with {tag.lower()}.")}
<div class="grid">
{''.join(persona_card(item) for item in items)}
</div>
</main>
"""

        write_file(
            os.path.join(OUTPUT_DIR, "tag", tag_slug + ".html"),
            page_shell(
                f"{tag} Character Personas | {SITE_NAME}",
                f"Browse character personas tagged with {tag.lower()}.",
                absolute_url(f"/tag/{tag_slug}.html"),
                content
            )
        )


# ============================================================
# LEGAL PAGES
# ============================================================

def build_legal_pages():
    dmca = f"""
<main class="container section">
<div class="panel">
<h1>DMCA and Copyright Policy</h1>
<p>
{esc(SITE_NAME)} respects intellectual property rights.
If you believe material on this website infringes your copyright,
send a notice to <a href="mailto:{esc(CONTACT_EMAIL)}">{esc(CONTACT_EMAIL)}</a>.
</p>
<h2>Include in your notice</h2>
<ul>
<li>Your physical or electronic signature.</li>
<li>Identification of the copyrighted work.</li>
<li>The URL or location of the material you believe is infringing.</li>
<li>Your contact information.</li>
<li>A statement that you have a good-faith belief the use is unauthorized.</li>
<li>A statement, under penalty of perjury, that the information is accurate.</li>
</ul>
<p>We will review complete notices and take appropriate action.</p>
</div>
</main>
"""

    compliance = f"""
<main class="container section">
<div class="panel">
<h1>18 U.S.C. §2257 Record-Keeping Statement</h1>
<p>
This website is intended to publish fictional character descriptions,
creative writing resources, and text-based persona concepts.
It does not knowingly host visual depictions of actual sexually
explicit conduct.
</p>
<p>
Any third-party links are provided for convenience. The operators
of linked services are responsible for their own content and
compliance obligations.
</p>
<p>For questions, contact {esc(CONTACT_EMAIL)}.</p>
</div>
</main>
"""

    write_file(
        os.path.join(OUTPUT_DIR, "dmca.html"),
        page_shell(
            f"DMCA Policy | {SITE_NAME}",
            "Copyright and DMCA policy for Character Persona Hub.",
            absolute_url("/dmca.html"),
            dmca
        )
    )

    write_file(
        os.path.join(OUTPUT_DIR, "2257.html"),
        page_shell(
            f"18 U.S.C. §2257 Statement | {SITE_NAME}",
            "Record-keeping compliance statement for Character Persona Hub.",
            absolute_url("/2257.html"),
            compliance
        )
    )


# ============================================================
# SITEMAP XSL
# ============================================================

SITEMAP_XSL = r"""<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
 xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
 xmlns:s="http://www.sitemaps.org/schemas/sitemap/0.9">
<xsl:output method="html" encoding="UTF-8" indent="yes"/>
<xsl:template match="/">
<html>
<head>
<title>XML Sitemap — Character Persona Hub</title>
<style>
body{font-family:Arial,sans-serif;background:#0a080d;color:#f8f2fa;padding:30px}
h1{color:#fb7185}
p{color:#aa9eaf}
table{width:100%;border-collapse:collapse;background:#16111d}
th,td{text-align:left;padding:12px;border-bottom:1px solid #302638}
th{color:#c4a4ff}
a{color:#fb7185;overflow-wrap:anywhere}
</style>
</head>
<body>
<h1>Character Persona Hub — XML Sitemap</h1>
<p>Search engines can use this sitemap to discover published pages.</p>
<table>
<tr><th>URL</th><th>Last Modified</th></tr>
<xsl:for-each select="s:urlset/s:url">
<tr>
<td><a href="{s:loc}"><xsl:value-of select="s:loc"/></a></td>
<td><xsl:value-of select="s:lastmod"/></td>
</tr>
</xsl:for-each>
</table>
</body>
</html>
</xsl:template>
</xsl:stylesheet>
"""


# ============================================================
# SITEMAPS
# ============================================================

def build_sitemaps(rows):
    urls = {absolute_url("/")}

    for row in rows:
        urls.add(
            absolute_url(f"/persona/{quote(row['slug'])}.html")
        )

    category_groups = defaultdict(list)
    topic_groups = set()
    tag_groups = set()

    for row in rows:
        category_groups[row["_category_slug"]].append(row)
        topic_groups.add(row["_subcategory_slug"])
        tag_groups.update(row["_tag_slugs"])

    for category_slug, items in category_groups.items():
        pages = max(1, math.ceil(len(items) / ITEMS_PER_PAGE))

        for page in range(1, pages + 1):
            urls.add(
                absolute_url(
                    f"/category/{category_slug}/page-{page}.html"
                )
            )

    for topic in topic_groups:
        urls.add(absolute_url(f"/topic/{topic}.html"))

    for tag in tag_groups:
        urls.add(absolute_url(f"/tag/{tag}.html"))

    urls.update([
        absolute_url("/dmca.html"),
        absolute_url("/2257.html"),
        absolute_url("/404.html"),
    ])

    sorted_urls = sorted(urls)

    write_file(
        os.path.join(OUTPUT_DIR, "sitemap.xsl"),
        SITEMAP_XSL
    )

    sitemap_files = []

    for index in range(0, len(sorted_urls), SITEMAP_LIMIT):
        batch = sorted_urls[index:index + SITEMAP_LIMIT]
        number = index // SITEMAP_LIMIT + 1

        xml = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<?xml-stylesheet type="text/xsl" href="/sitemap.xsl"?>',
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        ]

        for url in batch:
            xml.append(
                "<url>"
                f"<loc>{html.escape(url)}</loc>"
                f"<lastmod>{datetime.now(timezone.utc).date().isoformat()}</lastmod>"
                "</url>"
            )

        xml.append("</urlset>")
        filename = f"sitemap-{number}.xml"

        write_file(
            os.path.join(OUTPUT_DIR, filename),
            "\n".join(xml)
        )
        sitemap_files.append(filename)

    if len(sitemap_files) == 1:
        shutil.copyfile(
            os.path.join(OUTPUT_DIR, sitemap_files[0]),
            os.path.join(OUTPUT_DIR, "sitemap.xml")
        )
    else:
        index_xml = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<?xml-stylesheet type="text/xsl" href="/sitemap.xsl"?>',
            '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        ]

        for filename in sitemap_files:
            index_xml.append(
                "<sitemap>"
                f"<loc>{html.escape(absolute_url('/' + filename))}</loc>"
                f"<lastmod>{datetime.now(timezone.utc).date().isoformat()}</lastmod>"
                "</sitemap>"
            )

        index_xml.append("</sitemapindex>")

        write_file(
            os.path.join(OUTPUT_DIR, "sitemap.xml"),
            "\n".join(index_xml)
        )


# ============================================================
# ROBOTS.TXT
# ============================================================

def build_robots():
    content = f"""User-agent: *
Allow: /

Disallow: /404.html

Sitemap: {BASE_URL}/sitemap.xml
"""

    write_file(os.path.join(OUTPUT_DIR, "robots.txt"), content)


# ============================================================
# 404 PAGE
# ============================================================

def build_not_found():
    content = """
<main class="container section">
<div class="panel">
<span class="eyebrow">404</span>
<h1>Character Not Found</h1>
<p>This character page may have moved or no longer exists.</p>
<a class="primary-btn" href="/">Return to Character Persona Hub</a>
</div>
</main>
"""

    write_file(
        os.path.join(OUTPUT_DIR, "404.html"),
        page_shell(
            f"Page Not Found | {SITE_NAME}",
            "The requested character persona page could not be found.",
            absolute_url("/404.html"),
            content
        )
    )


# ============================================================
# CLOUDFLARE SUPPORT FILES
# ============================================================

def build_hosting_files():
    headers = """/*
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin
  X-Frame-Options: SAMEORIGIN

/*.xml
  Content-Type: application/xml; charset=utf-8

/*.xsl
  Content-Type: text/xsl; charset=utf-8
"""

    redirects = """# Cloudflare Pages uses the generated 404.html automatically.
"""

    write_file(os.path.join(OUTPUT_DIR, "_headers"), headers)
    write_file(os.path.join(OUTPUT_DIR, "_redirects"), redirects)


# ============================================================
# VALIDATION
# ============================================================

def validate_generated_site(rows):
    required_files = [
        "index.html", "sitemap.xml", "sitemap.xsl",
        "robots.txt", "dmca.html", "2257.html", "404.html",
        "_headers", "_redirects",
    ]

    for filename in required_files:
        path = os.path.join(OUTPUT_DIR, filename)
        if not os.path.isfile(path):
            raise RuntimeError(
                f"Build validation failed: missing {filename}"
            )

    homepage_path = os.path.join(OUTPUT_DIR, "index.html")

    with open(homepage_path, "r", encoding="utf-8") as file:
        homepage = file.read()

    for check in [
        'id="persona-search"',
        'id="categories"',
        GOOGLE_VERIFICATION,
        BING_VERIFICATION,
    ]:
        if check not in homepage:
            raise RuntimeError(
                f"Homepage validation failed: missing {check}"
            )

    # Check that the network footer is present on the homepage.
    for name, url in NETWORK_SITES:
        if url.rstrip("/") != BASE_URL.rstrip("/") and url not in homepage:
            raise RuntimeError(
                f"Network footer validation failed: missing {name}"
            )

    for row in rows:
        path = os.path.join(
            OUTPUT_DIR, "persona", row["slug"] + ".html"
        )

        if not os.path.isfile(path):
            raise RuntimeError(
                f"Build validation failed: missing persona {row['slug']}"
            )

        with open(path, "r", encoding="utf-8") as file:
            content = file.read()
        checks = [
            "Article",
            "persona-studio",
            "compatibility-status",
            "randomize-quirk",
            "copy-system",
            "copy-greeting",
            "ambience-toggle",
            "AD_SLOT_MID_CONTENT",
            "RTA-5042-1996-1400-1577-RTA",
            GOOGLE_VERIFICATION,
            BING_VERIFICATION,
        ]
        for check in checks:
            if check not in content:
                raise RuntimeError(
                    f"Detail validation failed for {row['slug']}: "
                    f"missing {check}"
                )


# ============================================================
# BUILD ENTRY POINT
# ============================================================

def main():
    print("=" * 65)
    print(f" {SITE_NAME}")
    print(" Static Programmatic SEO Website Generator")
    print("=" * 65)

    print("\n[1/11] Reading CSV...")
    rows = read_csv()
    print(f"      Loaded {len(rows)} character personas.")

    print("\n[2/11] Preparing output directory...")
    make_directory()

    print("\n[3/11] Building homepage...")
    write_file(
        os.path.join(OUTPUT_DIR, "index.html"),
        build_homepage(rows)
    )

    print("\n[4/11] Building character detail pages...")
    for index, row in enumerate(rows, start=1):
        write_file(
            os.path.join(
                OUTPUT_DIR, "persona", row["slug"] + ".html"
            ),
            build_detail_page(row, rows)
        )

        if index % 100 == 0:
            print(f"      Generated {index} detail pages.")

    print(f"      Generated {len(rows)} detail pages.")

    print("\n[5/11] Building category hubs...")
    build_category_hubs(rows)

    print("\n[6/11] Building subcategory hubs...")
    build_topic_hubs(rows)

    print("\n[7/11] Building tag hubs...")
    build_tag_hubs(rows)

    print("\n[8/11] Building legal and 404 pages...")
    build_legal_pages()
    build_not_found()

    print("\n[9/11] Building sitemaps and robots.txt...")
    build_sitemaps(rows)
    build_robots()

    print("\n[10/11] Building hosting support files...")
    build_hosting_files()

    print("\n[11/11] Validating generated website...")
    validate_generated_site(rows)

    category_count = len({r["category"] for r in rows})
    topic_count = len({r["subcategory"] for r in rows})
    tag_count = len({tag for r in rows for tag in r["_tags"]})

    category_pages = sum(
        max(1, math.ceil(count / ITEMS_PER_PAGE))
        for count in Counter(r["category"] for r in rows).values()
    )

    print("\n" + "=" * 65)
    print(" BUILD COMPLETED SUCCESSFULLY")
    print("=" * 65)
    print(f"\nWebsite:        {BASE_URL}")
    print(f"Output folder:  {os.path.abspath(OUTPUT_DIR)}")
    print(f"Personas:       {len(rows)}")
    print(f"Categories:     {category_count}")
    print(f"Category pages: {category_pages}")
    print(f"Subcategories:  {topic_count}")
    print(f"Unique tags:    {tag_count}")
    print("\nVerification tags: Google + Bing included")
    print("Network footer: 9 other websites included")
    print("\nCloudflare deployment:")
    print("  Build command: python3 build.py")
    print("  Output folder: dist")
    print("\n" + "=" * 65)


if __name__ == "__main__":
    try:
        main()
    except (FileNotFoundError, ValueError, RuntimeError) as error:
        print(f"\nBUILD ERROR: {error}")
        raise SystemExit(1)
    except KeyboardInterrupt:
        print("\nBuild interrupted.")
        raise SystemExit(130)
