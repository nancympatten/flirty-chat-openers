
#!/usr/bin/env python3
"""
FLIRTY CHAT OPENERS — COMPLETE STATIC WEBSITE BUILDER

Run:
    python3 build.py

Output:
    dist/

Features:
- Automatic starter content (no manual CSV required)
- Flexible CSV column handling
- Homepage, categories, tags and detail pages
- Copy opener buttons
- Random opener generator
- Responsive design
- SEO titles, descriptions and canonical URLs
- Article and FAQ structured data
- XML sitemap and robots.txt
- Privacy, terms and disclaimer pages
- 404 page
- Cloudflare Pages compatible

Python standard library only.
"""

import csv
import html
import json
import os
import re
import shutil
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import quote
from xml.sax.saxutils import escape as xml_escape

# ============================================================
# CONFIGURATION
# ============================================================

SITE_NAME = "Flirty Chat Openers"
BASE_URL = "https://flirty-chat-openers.velvetgrid.workers.dev"
SITE_DESCRIPTION = (
    "Discover playful conversation starters, flirty text messages, "
    "cute openers and follow-up ideas for better conversations."
)

CONTACT_EMAIL = "hello@example.com"

ROOT = Path(__file__).resolve().parent
DATA_FILE = ROOT / "data.csv"
DIST = ROOT / "dist"

YEAR = datetime.now(timezone.utc).year

CSV_COLUMNS = [
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
# STARTER CONTENT
# ============================================================

STARTER_TOPICS = [
    (
        "Cute Text Openers",
        "cute-text-openers",
        "cute",
        [
            "I was going to wait for you to text first, but I got impatient.",
            "Quick question: are you always this easy to think about?",
            "I just found a reason to smile. It reminded me of you.",
            "What's one little thing that always makes your day better?",
        ],
    ),
    (
        "Funny Flirty Openers",
        "funny-flirty-openers",
        "funny",
        [
            "Are you a notification? Because you just improved my day.",
            "I need your opinion on something very important: coffee or more coffee?",
            "I was trying to think of a clever opener. This is my best attempt.",
            "Do you believe in accidental crushes, or should I try again?",
        ],
    ),
    (
        "First Message Ideas",
        "first-message-ideas",
        "first-message",
        [
            "Hey! What's something interesting that happened to you today?",
            "Your profile caught my attention. What's the story behind it?",
            "I have a feeling you have excellent music recommendations.",
            "Let's skip the boring introductions. What's your ideal weekend?",
        ],
    ),
    (
        "Playful Conversation Starters",
        "playful-conversation-starters",
        "playful",
        [
            "Important question: spontaneous adventure or cozy movie night?",
            "You get to plan our imaginary perfect day. What's first?",
            "What's your most harmless unpopular opinion?",
            "I challenge you to make me laugh in one message.",
        ],
    ),
    (
        "Good Morning Messages",
        "good-morning-messages",
        "good-morning",
        [
            "Good morning! Hope today gives you plenty of reasons to smile.",
            "Just sending a little sunshine your way this morning.",
            "Morning! What's the first thing you're looking forward to today?",
            "I hope your coffee is strong and your day is wonderful.",
        ],
    ),
    (
        "Late Night Text Starters",
        "late-night-text-starters",
        "late-night",
        [
            "Are you still awake, or am I the only night owl here?",
            "What's something you've been wanting to talk about lately?",
            "Late-night question: what's your favorite memory this year?",
            "I hope I'm not interrupting, but I wanted to say hi.",
        ],
    ),
    (
        "Dating App Openers",
        "dating-app-openers",
        "dating-app",
        [
            "What's one destination you'd love to visit someday?",
            "Your profile made me curious. What's something I should know?",
            "What's your perfect first-date atmosphere?",
            "Let's settle an important debate: beach holiday or mountain escape?",
        ],
    ),
    (
        "Sweet Compliment Openers",
        "sweet-compliment-openers",
        "compliments",
        [
            "You have a way of making ordinary conversations interesting.",
            "I like your energy. It makes talking feel effortless.",
            "You seem like someone with a great story to tell.",
            "Your smile deserves its own appreciation message.",
        ],
    ),
    (
        "Conversation Restart Messages",
        "conversation-restart-messages",
        "conversation-restart",
        [
            "Hey stranger! How has life been treating you?",
            "I just remembered our conversation and wanted to check in.",
            "It's been a little while. What's new in your world?",
            "Random hello! Hope everything is going well with you.",
        ],
    ),
    (
        "Confident Flirty Messages",
        "confident-flirty-messages",
        "confident",
        [
            "I enjoy talking with you. We should do it more often.",
            "I was hoping we'd get another chance to chat.",
            "You have my attention. What should I know about you?",
            "I think we'd have a great conversation over coffee.",
        ],
    ),
]

def slugify(value):
    value = str(value or "").lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "conversation-starter"

def clean(value):
    return html.escape(str(value or "").strip())

def split_values(value):
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]

    value = str(value or "")
    return [
        x.strip()
        for x in re.split(r"[\n|;]+", value)
        if x.strip()
    ]

def make_starter_content():
    items = []

    for category, category_slug, subcategory, openers in STARTER_TOPICS:
        for index, opener in enumerate(openers, start=1):
            title = f"{category}: Idea {index}"

            items.append({
                "slug": slugify(
                    f"{category_slug}-idea-{index}"
                ),
                "title": title,
                "category": category,
                "subcategory": subcategory,
                "target_keyword": (
                    f"{category.lower()} idea {index}"
                ),
                "openers_list": [opener],
                "follow_up_tips": [
                    "Keep your message natural and genuine.",
                    "Ask an open-ended question to continue the conversation.",
                    "Respect the other person's comfort and response.",
                ],
                "description": (
                    f"Explore this {category.lower()} idea and "
                    "discover a natural way to begin an engaging conversation."
                ),
                "tags": [
                    subcategory,
                    "conversation starters",
                    "flirty messages",
                ],
                "faq_q1": "How do I use this conversation opener?",
                "faq_a1": (
                    "Adapt the wording to your personality and the "
                    "conversation. Keep it respectful and natural."
                ),
                "faq_q2": "What should I say after the first message?",
                "faq_a2": (
                    "Respond to what the other person says and ask "
                    "a relevant follow-up question."
                ),
                "upload_date": date.today().isoformat(),
            })

    return items

# ============================================================
# CSV READER
# ============================================================

ALIASES = {
    "slug": ["slug", "url", "permalink"],
    "title": ["title", "name", "headline"],
    "category": ["category", "type"],
    "subcategory": ["subcategory", "sub_category", "topic"],
    "target_keyword": ["target_keyword", "keyword", "primary_keyword"],
    "openers_list": [
        "openers_list", "openers", "messages", "opening_lines"
    ],
    "follow_up_tips": [
        "follow_up_tips", "followup_tips", "tips", "advice"
    ],
    "description": ["description", "summary", "meta_description"],
    "tags": ["tags", "labels"],
    "faq_q1": ["faq_q1", "question_1"],
    "faq_a1": ["faq_a1", "answer_1"],
    "faq_q2": ["faq_q2", "question_2"],
    "faq_a2": ["faq_a2", "answer_2"],
    "upload_date": ["upload_date", "date", "published"],
}

def get_value(row, column):
    for alias in ALIASES.get(column, [column]):
        if alias in row and row[alias] not in (None, ""):
            return row[alias]
    return ""

def normalize_row(row, index):
    result = {}

    for column in CSV_COLUMNS:
        result[column] = get_value(row, column)

    result["title"] = (
        str(result["title"]).strip()
        or f"Flirty Conversation Idea {index}"
    )

    result["slug"] = (
        slugify(result["slug"] or result["title"])
    )

    result["category"] = (
        str(result["category"]).strip()
        or "Flirty Conversation Starters"
    )

    result["subcategory"] = (
        str(result["subcategory"]).strip()
        or slugify(result["category"])
    )

    result["target_keyword"] = (
        str(result["target_keyword"]).strip()
        or result["title"].lower()
    )

    result["openers_list"] = split_values(
        result["openers_list"]
    )

    if not result["openers_list"]:
        result["openers_list"] = [
            "Hey! What's something interesting about your day?"
        ]

    result["follow_up_tips"] = split_values(
        result["follow_up_tips"]
    )

    if not result["follow_up_tips"]:
        result["follow_up_tips"] = [
            "Be yourself and keep the conversation natural.",
            "Ask a thoughtful follow-up question.",
            "Respect the other person's boundaries.",
        ]

    result["description"] = (
        str(result["description"]).strip()
        or f"Explore {result['title']} and find natural "
           "conversation starters for your next chat."
    )

    result["tags"] = split_values(result["tags"])

    if not result["tags"]:
        result["tags"] = [
            slugify(result["category"]),
            "conversation starters",
        ]

    result["faq_q1"] = (
        str(result["faq_q1"]).strip()
        or "How can I use these flirty openers?"
    )

    result["faq_a1"] = (
        str(result["faq_a1"]).strip()
        or "Choose a message that feels natural and adapt it to your personality."
    )

    result["faq_q2"] = (
        str(result["faq_q2"]).strip()
        or "How do I keep the conversation going?"
    )

    result["faq_a2"] = (
        str(result["faq_a2"]).strip()
        or "Listen to the response and ask a relevant follow-up question."
    )

    result["upload_date"] = (
        str(result["upload_date"]).strip()
        or date.today().isoformat()
    )

    return result

def load_content():
    if not DATA_FILE.exists():
        items = make_starter_content()
        print("data.csv not found. Using automatic starter content.")
        return items

    try:
        with DATA_FILE.open(
            "r", encoding="utf-8-sig", newline=""
        ) as file:
            reader = csv.DictReader(file)
            rows = list(reader)

        if not rows:
            print("CSV is empty. Using starter content.")
            return make_starter_content()

        items = [
            normalize_row(row, index)
            for index, row in enumerate(rows, start=1)
        ]

        return items

    except Exception as error:
        print(f"CSV could not be read: {error}")
        print("Using automatic starter content.")
        return make_starter_content()

# ============================================================
# HTML HELPERS
# ============================================================

def url(path=""):
    return BASE_URL.rstrip("/") + "/" + path.lstrip("/")

def page_head(title, description, canonical, schema=None):
    schema_html = ""

    if schema:
        schema_html = (
            '<script type="application/ld+json">'
            + json.dumps(schema, ensure_ascii=False)
            + '</script>'
        )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{clean(title)}</title>
<meta name="description" content="{clean(description)}">
<link rel="canonical" href="{clean(canonical)}">
<meta name="robots" content="index,follow">
<meta name="theme-color" content="#7c3aed">
<meta property="og:type" content="website">
<meta property="og:title" content="{clean(title)}">
<meta property="og:description" content="{clean(description)}">
<meta property="og:url" content="{clean(canonical)}">
<link rel="stylesheet" href="/assets/style.css">
{schema_html}
</head>
<body>
"""

def header():
    return """
<header class="site-header">
<div class="nav-wrap">
<a class="brand" href="/">💜 Flirty Chat Openers</a>
<nav>
<a href="/">Home</a>
<a href="/categories/">Categories</a>
<a href="/random.html">Random Opener</a>
</nav>
</div>
</header>
"""

def footer():
    return f"""
<footer class="footer">
<div class="container">
<p><strong>Flirty Chat Openers</strong></p>
<p>Conversation inspiration for genuine connections.</p>
<div class="footer-links">
<a href="/privacy.html">Privacy Policy</a>
<a href="/terms.html">Terms</a>
<a href="/disclaimer.html">Disclaimer</a>
<a href="/contact.html">Contact</a>
</div>
<p>© {YEAR} Flirty Chat Openers. All rights reserved.</p>
</div>
</footer>
<script src="/assets/app.js" defer></script>
</body>
</html>
"""

def card(item):
    return f"""
<article class="item-card">
<span class="category-label">{clean(item['category'])}</span>
<h3><a href="/openers/{quote(item['slug'])}/">{clean(item['title'])}</a></h3>
<p>{clean(item['description'])}</p>
<a class="read-link" href="/openers/{quote(item['slug'])}/">Explore openers →</a>
</article>
"""

def write_page(path, content):
    target = DIST / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")

# ============================================================
# ASSETS
# ============================================================

def build_assets():
    css = r"""
:root {
 --purple:#7c3aed;
 --dark:#24143d;
 --muted:#6b6475;
 --bg:#faf8ff;
 --card:#ffffff;
 --border:#eee7f7;
}
*{box-sizing:border-box}
body{
 margin:0;
 font-family:system-ui,-apple-system,Segoe UI,sans-serif;
 background:var(--bg);
 color:var(--dark);
 line-height:1.7;
}
a{color:var(--purple);text-decoration:none}
a:hover{text-decoration:underline}
.site-header{
 background:#fff;
 border-bottom:1px solid var(--border);
 position:sticky;top:0;z-index:5;
}
.nav-wrap{
 max-width:1120px;margin:auto;padding:14px 20px;
 display:flex;align-items:center;justify-content:space-between;
 gap:20px;flex-wrap:wrap;
}
.brand{font-size:20px;font-weight:800;color:var(--dark)}
nav{display:flex;gap:20px;flex-wrap:wrap}
nav a{color:var(--dark);font-weight:600}
.container{max-width:1120px;margin:auto;padding:35px 20px}
.hero{
 background:linear-gradient(135deg,#f1e8ff,#fff0f5);
 padding:65px 25px;text-align:center;border-radius:24px;
}
.hero h1{font-size:clamp(32px,5vw,54px);line-height:1.15}
.hero p{max-width:720px;margin:15px auto;color:var(--muted)}
.search{
 display:flex;max-width:600px;margin:25px auto 0;gap:8px;
}
.search input{
 flex:1;min-width:0;padding:14px;border:1px solid var(--border);
 border-radius:12px;font-size:16px;
}
button,.button{
 background:var(--purple);color:white;border:0;
 padding:12px 18px;border-radius:10px;font-weight:700;
 cursor:pointer;display:inline-block;
}
button:hover,.button:hover{opacity:.88}
.section-title{margin:40px 0 18px}
.grid{
 display:grid;grid-template-columns:repeat(3,minmax(0,1fr));
 gap:18px;
}
.item-card,.content-card{
 background:var(--card);border:1px solid var(--border);
 border-radius:17px;padding:22px;
 box-shadow:0 5px 20px rgba(50,20,90,.035);
}
.item-card h3{margin:8px 0}
.item-card p{color:var(--muted)}
.category-label{
 font-size:12px;color:var(--purple);font-weight:800;
 text-transform:uppercase;letter-spacing:.05em;
}
.read-link{font-weight:700}
.opener{
 padding:18px;margin:15px 0;border:1px solid var(--border);
 background:#fff;border-radius:14px;
 display:flex;align-items:center;justify-content:space-between;
 gap:15px;
}
.opener p{margin:0;font-size:17px}
.opener button{flex-shrink:0}
.breadcrumb{font-size:14px;color:var(--muted);margin-bottom:20px}
.content-card{margin:20px 0}
.content-card li{margin:8px 0}
.faq{border-bottom:1px solid var(--border);padding:15px 0}
.footer{
 margin-top:60px;background:#24143d;color:#eee;
 padding:35px 20px;text-align:center;
}
.footer-links{display:flex;justify-content:center;gap:18px;flex-wrap:wrap}
.footer a{color:#e7d8ff}
.small{color:var(--muted);font-size:14px}
@media(max-width:800px){
 .grid{grid-template-columns:repeat(2,minmax(0,1fr))}
}
@media(max-width:560px){
 .grid{grid-template-columns:1fr}
 .opener{align-items:flex-start;flex-direction:column}
 .search{flex-direction:column}
 .hero{padding:40px 18px}
}
"""
    js = r"""
document.addEventListener("click", async function(event) {
 const button = event.target.closest("[data-copy]");
 if (button) {
  const text = button.getAttribute("data-copy");
  try {
   await navigator.clipboard.writeText(text);
   button.textContent = "Copied!";
   setTimeout(() => button.textContent = "Copy", 1400);
  } catch(e) {
   button.textContent = "Select text to copy";
  }
 }
});
const search = document.querySelector("#site-search");
if(search){
 search.addEventListener("input",function(){
  const q=this.value.toLowerCase();
  document.querySelectorAll("[data-search]").forEach(card=>{
   card.hidden=!card.innerText.toLowerCase().includes(q);
  });
 });
}
const randomButton=document.querySelector("#random-opener");
if(randomButton){
 randomButton.addEventListener("click",()=>{
  const items=window.OPENER_DATA||[];
  if(!items.length)return;
  const item=items[Math.floor(Math.random()*items.length)];
  document.querySelector("#random-result").textContent=item;
 });
}
"""
    write_page("assets/style.css", css)
    write_page("assets/app.js", js)

# ============================================================
# HOMEPAGE
# ============================================================

def build_home(items):
    cards = "".join(card(item) for item in items[:30])

    categories = sorted(set(x["category"] for x in items))

    category_links = "".join(
        f'<a class="button" href="/categories/{quote(slugify(c))}/">{clean(c)}</a> '
        for c in categories
    )

    schema = {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": SITE_NAME,
        "url": url(),
        "description": SITE_DESCRIPTION,
    }

    content = page_head(
        SITE_NAME + " | Cute, Funny & Flirty Conversation Starters",
        SITE_DESCRIPTION,
        url(),
        schema,
    )

    content += header()
    content += f"""
<main class="container">
<section class="hero">
<h1>Find the Perfect Flirty Chat Opener 💜</h1>
<p>Make the first move easier with cute messages, playful conversation
starters, funny openers and thoughtful follow-up ideas.</p>
<div class="search">
<input id="site-search" type="search"
placeholder="Search conversation starters..." aria-label="Search">
</div>
<p><a class="button" href="/random.html">Get a Random Opener</a></p>
</section>

<h2 class="section-title">Explore Categories</h2>
<div class="content-card">{category_links}</div>

<h2 class="section-title">Popular Flirty Chat Openers</h2>
<div class="grid">{cards}</div>

<section class="content-card">
<h2>Make Conversations Feel Natural</h2>
<p>A good opener does not need to be complicated. Start with something
genuine, show curiosity, and give the other person room to respond.
The best conversations grow from mutual interest and respect.</p>
<p>Use these ideas as inspiration and make every message sound like you.</p>
</section>
</main>
"""

    content += footer()
    write_page("index.html", content)

# ============================================================
# DETAIL PAGES
# ============================================================

def build_detail(item, all_items):
    title = item["title"] + " | Flirty Chat Openers"
    canonical = url("openers/" + item["slug"] + "/")

    faq_entities = []

    for q, a in [
        (item["faq_q1"], item["faq_a1"]),
        (item["faq_q2"], item["faq_a2"]),
    ]:
        faq_entities.append({
            "@type": "Question",
            "name": q,
            "acceptedAnswer": {
                "@type": "Answer",
                "text": a,
            },
        })

    schema = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "Article",
                "headline": item["title"],
                "description": item["description"],
                "datePublished": item["upload_date"],
                "dateModified": item["upload_date"],
                "mainEntityOfPage": canonical,
                "author": {
                    "@type": "Organization",
                    "name": SITE_NAME,
                },
                "publisher": {
                    "@type": "Organization",
                    "name": SITE_NAME,
                },
            },
            {
                "@type": "FAQPage",
                "mainEntity": faq_entities,
            },
        ],
    }

    content = page_head(
        title,
        item["description"],
        canonical,
        schema,
    )

    content += header()

    opener_html = ""

    for opener in item["openers_list"]:
        opener_html += f"""
<div class="opener">
<p>{clean(opener)}</p>
<button data-copy="{clean(opener)}">Copy</button>
</div>
"""

    tips = "".join(
        f"<li>{clean(tip)}</li>"
        for tip in item["follow_up_tips"]
    )

    tags = "".join(
        f'<a href="/tags/{quote(slugify(tag))}/">{clean(tag)}</a> '
        for tag in item["tags"]
    )

    related = [
        x for x in all_items
        if x["slug"] != item["slug"]
        and x["category"] == item["category"]
    ][:4]

    if not related:
        related = [
            x for x in all_items
            if x["slug"] != item["slug"]
        ][:4]

    related_html = "".join(card(x) for x in related)

    content += f"""
<main class="container">
<div class="breadcrumb">
<a href="/">Home</a> / {clean(item['category'])} / {clean(item['title'])}
</div>

<h1>{clean(item['title'])}</h1>
<p>{clean(item['description'])}</p>

<section class="content-card">
<h2>Try These Openers</h2>
{opener_html}
</section>

<section class="content-card">
<h2>Follow-Up Tips</h2>
<ul>{tips}</ul>
</section>

<section class="content-card">
<h2>Frequently Asked Questions</h2>
<div class="faq">
<h3>{clean(item['faq_q1'])}</h3>
<p>{clean(item['faq_a1'])}</p>
</div>
<div class="faq">
<h3>{clean(item['faq_q2'])}</h3>
<p>{clean(item['faq_a2'])}</p>
</div>
</section>

<p><strong>Tags:</strong> {tags}</p>

<h2 class="section-title">You May Also Like</h2>
<div class="grid">{related_html}</div>
</main>
"""

    content += footer()

    write_page(
        "openers/" + item["slug"] + "/index.html",
        content,
    )

# ============================================================
# CATEGORY AND TAG PAGES
# ============================================================

def build_collection_page(name, items, kind, slug):
    cards = "".join(card(item) for item in items)

    title = f"{name} | {SITE_NAME}"
    description = (
        f"Explore {name.lower()} with useful conversation starters, "
        "message ideas and follow-up tips."
    )

    content = page_head(
        title,
        description,
        url(f"{kind}/{slug}/"),
    )

    content += header()
    content += f"""
<main class="container">
<div class="breadcrumb"><a href="/">Home</a> / {clean(name)}</div>
<h1>{clean(name)}</h1>
<p>{clean(description)}</p>
<div class="grid">{cards}</div>
</main>
"""
    content += footer()

    write_page(
        f"{kind}/{slug}/index.html",
        content,
    )

def build_collections(items):
    categories = {}

    for item in items:
        categories.setdefault(item["category"], []).append(item)

    for name, group in categories.items():
        build_collection_page(
            name,
            group,
            "categories",
            slugify(name),
        )

    tag_groups = {}

    for item in items:
        for tag in item["tags"]:
            tag_groups.setdefault(tag, []).append(item)

    for name, group in tag_groups.items():
        build_collection_page(
            name,
            group,
            "tags",
            slugify(name),
        )

    links = "".join(
        f'<li><a href="/categories/{quote(slugify(name))}/">'
        f'{clean(name)}</a> ({len(group)} articles)</li>'
        for name, group in categories.items()
    )

    content = page_head(
        "All Categories | " + SITE_NAME,
        "Browse all conversation starter categories.",
        url("categories/"),
    )

    content += header()
    content += f"""
<main class="container">
<h1>All Categories</h1>
<ul>{links}</ul>
</main>
"""
    content += footer()

    write_page("categories/index.html", content)

# ============================================================
# RANDOM OPENER PAGE
# ============================================================

def build_random_page(items):
    all_openers = []

    for item in items:
        all_openers.extend(item["openers_list"])

    data = json.dumps(all_openers, ensure_ascii=False)

    content = page_head(
        "Random Flirty Opener Generator | " + SITE_NAME,
        "Generate a random conversation opener.",
        url("random.html"),
    )

    content += header()
    content += f"""
<main class="container">
<section class="hero">
<h1>Random Flirty Opener Generator</h1>
<p>Need inspiration? Generate a conversation starter.</p>
<div class="content-card">
<h2 id="random-result">Click below to discover an opener.</h2>
<button id="random-opener">Generate Opener</button>
</div>
</section>
</main>
<script>window.OPENER_DATA={data};</script>
"""
    content += footer()

    write_page("random.html", content)

# ============================================================
# STATIC PAGES
# ============================================================

def build_static_pages():
    pages = {
        "privacy.html": (
            "Privacy Policy",
            """
<p>We respect your privacy. This website may collect basic technical
information through hosting providers and analytics services.</p>
<p>We do not ask visitors to submit sensitive personal information.</p>
<p>Third-party services may use cookies according to their own policies.</p>
<p>For privacy questions, contact the website owner.</p>
""",
        ),
        "terms.html": (
            "Terms and Conditions",
            """
<p>By using this website, you agree to use its content responsibly.</p>
<p>Conversation starters are provided for informational and
entertainment purposes.</p>
<p>You are responsible for how you communicate with other people.
Always respect consent, privacy and personal boundaries.</p>
""",
        ),
        "disclaimer.html": (
            "Disclaimer",
            """
<p>All content is provided for general informational and
entertainment purposes.</p>
<p>Messages are suggestions, not guarantees of any particular
response or relationship outcome.</p>
<p>Be respectful and considerate in every interaction.</p>
""",
        ),
        "contact.html": (
            "Contact",
            f"""
<p>For questions or feedback, contact:</p>
<p><a href="mailto:{clean(CONTACT_EMAIL)}">{clean(CONTACT_EMAIL)}</a></p>
""",
        ),
    }

    for filename, (title, body) in pages.items():
        content = page_head(
            title + " | " + SITE_NAME,
            title + " for " + SITE_NAME,
            url(filename),
        )
        content += header()
        content += f"""
<main class="container">
<section class="content-card">
<h1>{clean(title)}</h1>
{body}
</section>
</main>
"""
        content += footer()

        write_page(filename, content)

    write_page(
        "404.html",
        page_head(
            "Page Not Found | " + SITE_NAME,
            "The requested page could not be found.",
            url("404.html"),
        )
        + header()
        + """
<main class="container">
<h1>Page not found</h1>
<p>Sorry, this page does not exist.</p>
<a class="button" href="/">Return Home</a>
</main>
"""
        + footer(),
    )

# ============================================================
# SITEMAP AND ROBOTS
# ============================================================

def build_sitemap(items):
    paths = [
        "",
        "categories/",
        "random.html",
        "privacy.html",
        "terms.html",
        "disclaimer.html",
        "contact.html",
    ]

    for item in items:
        paths.append("openers/" + item["slug"] + "/")

    categories = sorted(set(x["category"] for x in items))

    for category in categories:
        paths.append("categories/" + slugify(category) + "/")

    tags = sorted(set(
        tag for item in items for tag in item["tags"]
    ))

    for tag in tags:
        paths.append("tags/" + slugify(tag) + "/")

    unique_paths = list(dict.fromkeys(paths))

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]

    for path in unique_paths:
        lines.append(
            "<url><loc>"
            + xml_escape(url(path))
            + "</loc><lastmod>"
            + date.today().isoformat()
            + "</lastmod></url>"
        )

    lines.append("</urlset>")

    write_page("sitemap.xml", "\n".join(lines))

    write_page(
        "robots.txt",
        "User-agent: *\n"
        "Allow: /\n\n"
        "Sitemap: " + url("sitemap.xml") + "\n",
    )

# ============================================================
# BUILD VALIDATION
# ============================================================

def validate_site(items):
    errors = []

    if not (DIST / "index.html").exists():
        errors.append("Homepage missing.")

    if not (DIST / "sitemap.xml").exists():
        errors.append("Sitemap missing.")

    for item in items:
        detail = DIST / "openers" / item["slug"] / "index.html"

        if not detail.exists():
            errors.append(f"Missing detail page: {item['slug']}")
            continue

        source = detail.read_text(encoding="utf-8")

        for required in [
            "<title>",
            'rel="canonical"',
            "FAQPage",
            "Article",
        ]:
            if required not in source:
                errors.append(
                    f"{item['slug']}: missing {required}"
                )

    if errors:
        for error in errors:
            print("VALIDATION ERROR:", error)

        raise RuntimeError(
            f"Validation failed with {len(errors)} error(s)."
        )

# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 55)
    print("FLIRTY CHAT OPENERS — WEBSITE BUILDER")
    print("=" * 55)

    items = load_content()

    if not items:
        raise RuntimeError("No content available.")

    # Ensure slugs are unique.
    seen = set()

    for index, item in enumerate(items, start=1):
        base = item["slug"]
        slug = base
        suffix = 2

        while slug in seen:
            slug = f"{base}-{suffix}"
            suffix += 1

        item["slug"] = slug
        seen.add(slug)

    if DIST.exists():
        shutil.rmtree(DIST)

    DIST.mkdir(parents=True, exist_ok=True)

    build_assets()
    build_home(items)

    for item in items:
        build_detail(item, items)

    build_collections(items)
    build_random_page(items)
    build_static_pages()
    build_sitemap(items)

    validate_site(items)

    print()
    print("BUILD SUCCESSFUL")
    print(f"Website: {BASE_URL}")
    print(f"Content pages: {len(items)}")
    print(f"Output folder: {DIST}")
    print("Validation: PASSED")
    print()
    print("Deploy with:")
    print("npx wrangler pages deploy dist")
    print()

if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print()
        print("BUILD ERROR:", error)
        raise
