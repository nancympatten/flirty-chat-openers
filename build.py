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
from datetime import datetime
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

CURRENT_YEAR = datetime.utcnow().year

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
    if not os.path.isfile(DATA_FILE):
        raise FileNotFoundError(
            f"Missing {DATA_FILE}. Put data.csv beside build.py."
        )

    rows = []

    with open(DATA_FILE, "r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        if not reader.fieldnames:
            raise ValueError("data.csv has no header row.")

        missing = [c for c in CSV_COLUMNS if c not in reader.fieldnames]

        if missing:
            raise ValueError(
                "Missing required CSV columns: " + ", ".join(missing)
            )

        used_slugs = set()

        for line_number, raw in enumerate(reader, start=2):
            row = {c: clean(raw.get(c, "")) for c in CSV_COLUMNS}

            if not row["title"]:
                print(f"Skipping row {line_number}: missing title.")
                continue

            original_slug = slugify(row["slug"] or row["title"])
            slug = original_slug
            suffix = 2

            while slug in used_slugs:
                slug = f"{original_slug}-{suffix}"
                suffix += 1

            used_slugs.add(slug)
            row["slug"] = slug

            row["category"] = row["category"] or "General Personas"
            row["subcategory"] = (
                row["subcategory"] or "Character Templates"
            )

            if not row["description"]:
                row["description"] = (
                    row["character_bio"][:250]
                    or f"Explore the {row['title']} character persona."
                )

            row["_tags"] = split_tags(row["tags"])
            row["_traits"] = [
                clean(t)
                for t in row["personality_traits"].split("|")
                if clean(t)
            ]
            row["_date"] = parse_date(row["upload_date"])
            row["_category_slug"] = slugify(row["category"])
            row["_subcategory_slug"] = slugify(row["subcategory"])
            row["_tag_slugs"] = [
                slugify(tag) for tag in row["_tags"]
            ]

            rows.append(row)

    if not rows:
        raise ValueError("data.csv contains no usable character personas.")

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
<div class="network-links">
{network_html}
</div>

<p>
&copy; <span class="live-year">{CURRENT_YEAR}</span>
{esc(SITE_NAME)}. All rights reserved.
</p>
<p>
Independent fictional character-template directory.
All characters and scenarios are fictional.
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
# PERSONA CARDS
# ============================================================

def persona_card(row):
    tags = " ".join(row["_tags"])

    return f"""
<article class="persona-card"
 data-persona-card
 data-title="{esc(row['title'])}"
 data-keyword="{esc(row['target_keyword'])}"
 data-tags="{esc(tags)}">
 <div class="card-category">{esc(row['category'])}</div>
 <h3><a href="{BASE_URL}/persona/{quote(row['slug'])}.html">
 {esc(row['title'])}</a></h3>
 <p>{esc(truncate(row['description'], 135))}</p>
 <div class="card-meta">
 <span class="pill">{esc(row['subcategory'])}</span>
 {''.join(f'<span class="pill">{esc(t)}</span>' for t in row['_tags'][:2])}
 </div>
 <a class="card-link" href="{BASE_URL}/persona/{quote(row['slug'])}.html">
 Explore Character &rarr;
 </a>
</article>
"""


def cards_grid(rows):
    if not rows:
        return '<div class="empty-state">No character personas found.</div>'

    return '<div class="grid">' + "".join(
        persona_card(row) for row in rows
    ) + "</div>"


# ============================================================
# HOMEPAGE
# ============================================================

def build_homepage(rows):
    categories = defaultdict(list)
    subcategories = defaultdict(list)
    tags = defaultdict(list)

    for row in rows:
        categories[row["category"]].append(row)
        subcategories[row["subcategory"]].append(row)

        for tag in row["_tags"]:
            tags[tag].append(row)

    newest = sorted(
        rows, key=lambda r: r["_date"], reverse=True
    )[:NEWEST_LIMIT]

    category_cards = []

    for category in sorted(categories, key=str.lower):
        items = categories[category]
        category_cards.append(f"""
<a class="hub-card"
 href="{BASE_URL}/category/{slugify(category)}/page-1.html">
 <strong>{esc(category)}</strong>
 <span class="count">{len(items)} personas</span>
</a>
""")

    subcategory_cards = []

    for name in sorted(subcategories, key=str.lower):
        items = subcategories[name]
        subcategory_cards.append(f"""
<a class="subcategory-pill"
 href="{BASE_URL}/topic/{slugify(name)}.html">
 {esc(name)} ({len(items)})
</a>
""")

    tag_cards = []

    for tag, items in sorted(
        tags.items(),
        key=lambda item: (-len(item[1]), item[0].lower())
    ):
        tag_cards.append(
            f'<a href="{BASE_URL}/tag/{slugify(tag)}.html">'
            f'{esc(tag)} <span class="count">({len(items)})</span></a>'
        )

    content = f"""
<main>
<section class="hero">
<div class="container">
<span class="eyebrow">The Character Creation Library</span>
<h1>Build Your Next <span class="gradient-text">
Unforgettable AI Character</span></h1>
<p>
Explore fictional AI companion character cards, personality
templates, conversation starters, and interactive persona studios.
Find a character concept and customize it instantly.
</p>
<div class="search-wrap">
<span class="search-icon">&#9906;</span>
<input id="persona-search" class="search-input"
 type="search" placeholder="Search characters, keywords, tags..."
 aria-label="Search character personas">
</div>
<p id="search-count">{len(rows)} personas available</p>
</div>
</section>

<section class="section" id="categories">
<div class="container">
<div class="section-heading">
<div>
<h2>Browse Persona Archetypes</h2>
<p>Explore every character category and its complete collection.</p>
</div>
</div>
<div class="grid">{''.join(category_cards)}</div>
</div>
</section>

<section class="section">
<div class="container">
<div class="section-heading">
<div>
<h2>Explore Character Topics</h2>
<p>Discover specialized character templates.</p>
</div>
</div>
<div class="tag-cloud">{''.join(subcategory_cards)}</div>
</div>
</section>

<section class="section">
<div class="container">
<div class="section-heading">
<div>
<h2>Popular Character Tags</h2>
<p>Browse the library by personality and theme.</p>
</div>
</div>
<div class="tag-cloud">{''.join(tag_cards)}</div>
</div>
</section>

<section class="section" id="newest">
<div class="container">
<div class="section-heading">
<div>
<h2>Discover Character Personas</h2>
<p>Browse the newest {len(newest)} character concepts in the library.</p>
</div>
</div>
{cards_grid(newest)}
</div>
</section>

<section class="section">
<div class="container">
<div class="panel">
<h2>What Is Character Persona Hub?</h2>
<p>
Character Persona Hub is a searchable collection of fictional
character profiles and AI conversation templates. Each character
page provides a customizable biography, personality traits,
opening dialogue, copy-ready system prompt, and synthesized
ambient audio.
</p>
<p>
Customize character names, settings, and interaction partners
to create reusable creative roleplay concepts.
</p>
</div>
</div>
</section>
</main>
"""

    return page_shell(
        f"{SITE_NAME} | AI Companion Character Cards & Persona Templates",
        "Discover and customize fictional AI companion character cards, "
        "personality templates, dialogue hooks and creative persona prompts.",
        absolute_url("/"),
        content
    )


# ============================================================
# STRUCTURED DATA
# ============================================================

def make_detail_schema(row):
    canonical = absolute_url(
        f"/persona/{quote(row['slug'])}.html"
    )

    article = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": row["title"],
        "description": truncate(row["description"], 250),
        "mainEntityOfPage": canonical,
        "author": {"@type": "Organization", "name": SITE_NAME},
        "publisher": {"@type": "Organization", "name": SITE_NAME},
        "datePublished": (
            row["_date"].date().isoformat()
            if row["_date"] != datetime.min else None
        ),
        "dateModified": datetime.utcnow().date().isoformat(),
        "articleSection": row["category"],
        "keywords": row["target_keyword"],
    }

    breadcrumb = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": 1,
                "name": "Home",
                "item": absolute_url("/")
            },
            {
                "@type": "ListItem",
                "position": 2,
                "name": row["category"],
                "item": absolute_url(
                    f"/category/{row['_category_slug']}/page-1.html"
                )
            },
            {
                "@type": "ListItem",
                "position": 3,
                "name": row["title"],
                "item": canonical
            }
        ]
    }

    faq_entities = []

    for question, answer in [
        (row["faq_q1"], row["faq_a1"]),
        (row["faq_q2"], row["faq_a2"])
    ]:
        if question and answer:
            faq_entities.append({
                "@type": "Question",
                "name": question,
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": answer
                }
            })

    schemas = [article, breadcrumb]

    if faq_entities:
        schemas.append({
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": faq_entities
        })

    return "\n".join(
        '<script type="application/ld+json">'
        + safe_json(schema)
        + '</script>'
        for schema in schemas
    )


# ============================================================
# RELATED PERSONAS
# ============================================================

def get_related(row, rows):
    candidates = []
    current_tags = set(row["_tag_slugs"])

    for other in rows:
        if other["slug"] == row["slug"]:
            continue

        same_subcategory = (
            other["_subcategory_slug"] == row["_subcategory_slug"]
        )
        shared_tags = len(
            current_tags.intersection(set(other["_tag_slugs"]))
        )
        same_category = (
            other["_category_slug"] == row["_category_slug"]
        )

        score = (
            shared_tags * 4
            + (5 if same_subcategory else 0)
            + (2 if same_category else 0)
        )

        candidates.append((score, other["_date"], other))

    candidates.sort(
        key=lambda item: (item[0], item[1]),
        reverse=True
    )

    return [item[2] for item in candidates[:RELATED_LIMIT]]


# ============================================================
# DETAIL PAGES
# ============================================================

def build_detail_page(row, rows):
    related = get_related(row, rows)

    traits = row["_traits"] or [
        "Creative", "Expressive", "Thoughtful",
        "Adaptable", "Imaginative"
    ]

    traits_html = "".join(
        f'<span class="trait-pill">{esc(trait)}</span>'
        for trait in traits
    )

    tags_html = "".join(
        f'<a class="pill" href="{BASE_URL}/tag/{slugify(tag)}.html">'
        f'{esc(tag)}</a>'
        for tag in row["_tags"]
    )

    faq_html = ""

    for question, answer in [
        (row["faq_q1"], row["faq_a1"]),
        (row["faq_q2"], row["faq_a2"])
    ]:
        if question and answer:
            faq_html += f"""
<div class="faq-item">
<h3>{esc(question)}</h3>
<p>{esc(answer)}</p>
</div>
"""

    title = row["title"]
    description = row["description"]
    canonical = absolute_url(
        f"/persona/{quote(row['slug'])}.html"
    )

    studio_attributes = (
        f'data-bio="{esc(row["character_bio"])}" '
        f'data-opening="{esc(row["opening_line"])}" '
        f'data-title="{esc(title)}"'
    )

    content = f"""
<main class="container">
<div class="breadcrumbs">
<a href="{BASE_URL}/">Home</a> /
<a href="{BASE_URL}/category/{row['_category_slug']}/page-1.html">
{esc(row['category'])}</a> / {esc(title)}
</div>

<section class="detail-hero">
<span class="eyebrow">{esc(row['category'])}</span>
<h1>{esc(title)}</h1>
<p>{esc(description)}</p>
<div class="card-meta">
<span class="pill">{esc(row['subcategory'])}</span>
{tags_html}
</div>
<p><span class="status-badge compatibility-status">
Compatibility Verified: {datetime.utcnow().strftime("%B %Y")}
</span></p>
</section>

<div class="detail-grid">
<div>

<section class="panel" id="persona-studio" {studio_attributes}>
<h2>Interactive Persona Customizer</h2>
<p>
Personalize this character's identity, interaction partner,
and fictional environment. Your changes update the character
profile and opening dialogue instantly.
</p>

<div class="customizer-grid">
<div class="field">
<label for="character-name">Character Name</label>
<input id="character-name" type="text"
 value="{esc(title)}" maxlength="100">
</div>
<div class="field">
<label for="user-name">User Name</label>
<input id="user-name" type="text"
 placeholder="Your name" maxlength="100">
</div>
<div class="field">
<label for="character-setting">Setting</label>
<input id="character-setting" type="text"
 placeholder="Enter a fictional setting" maxlength="200">
</div>
</div>

<h3>Customized Character Biography</h3>
<div class="prompt-output" id="custom-bio"></div>
<h3>Customized Opening Line</h3>
<div class="prompt-output" id="custom-opening"></div>
</section>

<section class="panel">
<h2>Trait Badge Matrix</h2>
<div class="traits">{traits_html}</div>
<div class="button-row">
<button class="action-btn" id="randomize-quirk">
Randomize Bonus Quirk
</button>
</div>
<p><strong>Bonus Quirk:</strong>
<span id="bonus-quirk">Discover a surprise character detail.</span></p>
</section>

<section class="panel">
<h2>Copy-Ready Character System Prompt</h2>
<p>
Use the generated system prompt in a compatible AI conversation
platform. Customize the profile before copying.
</p>
<div class="button-row">
<button class="primary-btn" id="copy-system">Copy System Prompt</button>
<button class="action-btn" id="copy-greeting">Copy Opening Greeting</button>
<span class="token-badge" id="token-count">Calculating...</span>
</div>
<h3>System Prompt Preview</h3>
<div class="prompt-output" id="system-prompt"></div>
<h3>Opening Greeting Preview</h3>
<div class="prompt-output" id="greeting-prompt"></div>
</section>

<section class="panel">
<h2>Character Mood Ambience</h2>
<p>
Generate lightweight atmospheric background audio directly
in your browser using the Web Audio API.
</p>
<div class="audio-controls">
<button class="action-btn" id="ambience-toggle">▶ Play Ambience</button>
<select id="sound-mode" aria-label="Sound mode">
<option value="rain">Midnight Rain</option>
<option value="velvet">Soft Velvet Hum</option>
<option value="cafe">Cozy Cafe Murmur</option>
</select>
<label for="sound-volume">Volume</label>
<input type="range" id="sound-volume" min="0" max="100" value="25">
</div>
</section>

<!-- AD_SLOT_MID_CONTENT -->

<section class="panel">
<h2>About This Character Persona</h2>
<p>{esc(description)}</p>
<h3>Character Background</h3>
<p>{esc(row['character_bio'])}</p>
<h3>Personality Characteristics</h3>
<div class="traits">{traits_html}</div>
<h3>Opening Dialogue</h3>
<p>{esc(row['opening_line'])}</p>
</section>

<section class="panel">
<h2>Frequently Asked Questions</h2>
{faq_html if faq_html else '<p>Explore the character sheet to learn more about this fictional persona.</p>'}
</section>

</div>

<aside>
<section class="panel">
<h2>Character Information</h2>
<p><strong>Category:</strong><br>{esc(row['category'])}</p>
<p><strong>Subcategory:</strong><br>{esc(row['subcategory'])}</p>
<p><strong>Primary Keyword:</strong><br>{esc(row['target_keyword'])}</p>
<p><strong>Published:</strong><br>{esc(row['upload_date'] or 'Evergreen collection')}</p>
<p><strong>Traits:</strong><br>{len(traits)}</p>
<p><strong>Tags:</strong><br>{len(row['_tags'])}</p>
</section>

<section class="affiliate-card">
<h2>Bring This Character to Life</h2>
<p>
Take this customized character concept into a compatible
AI voice companion platform and explore voice-enabled
character interactions.
</p>
<a class="primary-btn" href="{esc(AFFILIATE_URL)}"
 rel="nofollow sponsored noopener" target="_blank">
{esc(AFFILIATE_CTA_TEXT)}
</a>
</section>
</aside>
</div>

<section class="section">
<div class="section-heading">
<div>
<h2>Related Character Personas</h2>
<p>Explore similar characters based on shared themes and traits.</p>
</div>
</div>
{cards_grid(related)}
</section>
</main>
"""

    content += make_detail_schema(row)

    return page_shell(
        f"{title} | Character Persona Template | {SITE_NAME}",
        description,
        canonical,
        content,
        "article"
    )


# ============================================================
# CATEGORY HUBS WITH PAGINATION
# ============================================================

def build_category_hubs(rows):
    groups = defaultdict(list)

    for row in rows:
        groups[row["category"]].append(row)

    for category, items in groups.items():
        items.sort(key=lambda r: r["_date"], reverse=True)

        total_pages = max(1, math.ceil(len(items) / ITEMS_PER_PAGE))
        category_slug = slugify(category)

        for page_number in range(1, total_pages + 1):
            start = (page_number - 1) * ITEMS_PER_PAGE
            page_items = items[start:start + ITEMS_PER_PAGE]

            current_path = (
                f"/category/{category_slug}/page-{page_number}.html"
            )
            canonical = absolute_url(current_path)

            title = (
                f"{category} Character Personas"
                + (f" | Page {page_number}" if page_number > 1 else "")
            )

            description = (
                f"Browse {len(items)} fictional {category.lower()} "
                f"character personas, AI companion templates, "
                f"personality profiles, and dialogue starters."
            )

            navigation = []
            extra_links = ""

            # Compute URLs separately to avoid nested f-string issues.
            prev_url = None
            next_url = None

            if page_number > 1:
                prev_url = absolute_url(
                    f"/category/{category_slug}/page-{page_number - 1}.html"
                )
                navigation.append(
                    f'<a href="{esc(prev_url)}" rel="prev">Previous</a>'
                )
                extra_links += (
                    f'<link rel="prev" href="{esc(prev_url)}">'
                )

            if page_number < total_pages:
                next_url = absolute_url(
                    f"/category/{category_slug}/page-{page_number + 1}.html"
                )
                navigation.append(
                    f'<a href="{esc(next_url)}" rel="next">Next</a>'
                )
                extra_links += (
                    f'<link rel="next" href="{esc(next_url)}">'
                )

            pagination = (
                '<div class="pagination">'
                + "".join(navigation)
                + "</div>"
            )

            content = f"""
<main class="container section">
<div class="breadcrumbs">
<a href="{BASE_URL}/">Home</a> / {esc(category)}
</div>
<span class="eyebrow">Persona Archetype</span>
<h1>{esc(title)}</h1>
<p>{esc(description)}</p>
<p class="count">{len(items)} total character personas</p>
{cards_grid(page_items)}
{pagination}
</main>
"""

            page = page_shell(
                f"{title} | {SITE_NAME}",
                description,
                canonical,
                content
            )

            page = page.replace("</head>", extra_links + "\n</head>")

            write_file(
                os.path.join(
                    OUTPUT_DIR, "category", category_slug,
                    f"page-{page_number}.html"
                ),
                page
            )


# ============================================================
# SUBCATEGORY HUBS
# ============================================================

def build_topic_hubs(rows):
    groups = defaultdict(list)

    for row in rows:
        groups[row["subcategory"]].append(row)

    for name, items in groups.items():
        items.sort(key=lambda r: r["_date"], reverse=True)
        topic_slug = slugify(name)

        description = (
            f"Explore {len(items)} fictional character templates "
            f"in the {name} collection, including AI companion "
            f"personas and reusable dialogue prompts."
        )

        content = f"""
<main class="container section">
<div class="breadcrumbs">
<a href="{BASE_URL}/">Home</a> / Topics / {esc(name)}
</div>
<span class="eyebrow">Character Topic</span>
<h1>{esc(name)} Character Templates</h1>
<p>{esc(description)}</p>
{cards_grid(items)}
</main>
"""

        write_file(
            os.path.join(OUTPUT_DIR, "topic", topic_slug + ".html"),
            page_shell(
                f"{name} Character Templates | {SITE_NAME}",
                description,
                absolute_url(f"/topic/{topic_slug}.html"),
                content
            )
        )


# ============================================================
# TAG HUBS
# ============================================================

def build_tag_hubs(rows):
    groups = defaultdict(list)

    for row in rows:
        for tag in row["_tags"]:
            groups[tag].append(row)

    for tag, items in groups.items():
        items.sort(key=lambda r: r["_date"], reverse=True)
        tag_slug = slugify(tag)

        description = (
            f"Browse {len(items)} character personas tagged "
            f"{tag}, including fictional personality templates "
            f"and conversation starters."
        )

        content = f"""
<main class="container section">
<div class="breadcrumbs">
<a href="{BASE_URL}/">Home</a> / Tags / {esc(tag)}
</div>
<span class="eyebrow">Character Tag</span>
<h1>{esc(tag)} Character Personas</h1>
<p>{esc(description)}</p>
{cards_grid(items)}
</main>
"""

        write_file(
            os.path.join(OUTPUT_DIR, "tag", tag_slug + ".html"),
            page_shell(
                f"{tag} Character Personas | {SITE_NAME}",
                description,
                absolute_url(f"/tag/{tag_slug}.html"),
                content
            )
        )


# ============================================================
# LEGAL PAGES
# ============================================================

def build_legal_pages():
    dmca_content = f"""
<main class="container section">
<span class="eyebrow">Copyright Information</span>
<h1>DMCA Copyright Policy</h1>
<div class="panel">
<h2>Copyright Respect</h2>
<p>
{esc(SITE_NAME)} respects the intellectual property rights
of creators and expects users and contributors to do the same.
</p>
<h2>Submitting a Copyright Notice</h2>
<p>
If you believe material published on this website infringes
your copyright, send a written notice to:
</p>
<p><a href="mailto:{esc(CONTACT_EMAIL)}">{esc(CONTACT_EMAIL)}</a></p>
<p>Your notice should include:</p>
<ul>
<li>Identification of the copyrighted work.</li>
<li>Identification of the allegedly infringing material and its URL.</li>
<li>Your contact information.</li>
<li>A statement of good-faith belief that the use is unauthorized.</li>
<li>A statement that the information is accurate and that you are
authorized to act on behalf of the rights holder.</li>
<li>Your physical or electronic signature.</li>
</ul>
<h2>Review and Response</h2>
<p>
Valid notices will be reviewed. Where appropriate, material may
be restricted or removed while the matter is investigated.
</p>
<h2>Contact</h2>
<p>{esc(CONTACT_EMAIL)}</p>
</div>
</main>
"""

    write_file(
        os.path.join(OUTPUT_DIR, "dmca.html"),
        page_shell(
            f"DMCA Copyright Policy | {SITE_NAME}",
            "Copyright and DMCA policy for Character Persona Hub.",
            absolute_url("/dmca.html"),
            dmca_content
        )
    )

    section_content = f"""
<main class="container section">
<span class="eyebrow">Compliance Information</span>
<h1>18 U.S.C. §2257 Statement</h1>
<div class="panel">
<h2>Nature of Website Content</h2>
<p>
{esc(SITE_NAME)} is a fictional character-template and
creative writing resource. The website publishes text-based
fictional character descriptions, personality profiles,
dialogue prompts, and AI companion concepts.
</p>
<h2>Nature of Materials</h2>
<p>
The website does not intentionally publish actual visual
depictions of sexually explicit conduct. Character profiles
and dialogue templates are fictional textual materials.
</p>
<h2>Age Requirement</h2>
<p>
Access to the website is intended for adults aged 18 or older.
A browser-based age confirmation is displayed to visitors.
</p>
<h2>Contact</h2>
<p>
For questions about website content or compliance, contact
<a href="mailto:{esc(CONTACT_EMAIL)}">{esc(CONTACT_EMAIL)}</a>.
</p>
</div>
</main>
"""

    write_file(
        os.path.join(OUTPUT_DIR, "2257.html"),
        page_shell(
            f"18 U.S.C. §2257 Statement | {SITE_NAME}",
            "Compliance information and statement for Character Persona Hub.",
            absolute_url("/2257.html"),
            section_content
        )
    )


# ============================================================
# XML SITEMAP STYLESHEET
# ============================================================

SITEMAP_XSL = r"""<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
 xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
 xmlns:s="http://www.sitemaps.org/schemas/sitemap/0.9">
<xsl:output method="html" encoding="UTF-8" indent="yes"/>
<xsl:template match="/">
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Character Persona Hub — XML Sitemap</title>
<style>
*{box-sizing:border-box}
body{margin:0;padding:35px 20px;background:#0a080d;color:#f8f2fa;font-family:Arial,sans-serif}
main{max-width:1100px;margin:auto}
h1{color:#fb7185}
p{color:#aa9eaf}
table{width:100%;border-collapse:collapse;background:#16111d;border-radius:12px;overflow:hidden}
th,td{text-align:left;padding:13px;border-bottom:1px solid #302536;font-size:13px}
th{color:#c4a4ff}
a{color:#fb8196;text-decoration:none;overflow-wrap:anywhere}
a:hover{text-decoration:underline}
</style>
</head>
<body>
<main>
<h1>Character Persona Hub Sitemap</h1>
<p>Index of published pages.</p>
<table>
<tr><th>URL</th><th>Last Modified</th></tr>
<xsl:for-each select="s:urlset/s:url">
<tr>
<td><a href="{s:loc}"><xsl:value-of select="s:loc"/></a></td>
<td><xsl:value-of select="s:lastmod"/></td>
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
                f"<lastmod>{datetime.utcnow().date().isoformat()}</lastmod>"
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
                f"<lastmod>{datetime.utcnow().date().isoformat()}</lastmod>"
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
            "BreadcrumbList",
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
