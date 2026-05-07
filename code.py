#!/usr/bin/env python3
from __future__ import annotations
import argparse, logging, re, sys
from datetime import datetime, timezone
from pathlib import Path

VERSION = "2.0.0"
BAR_WIDTH = 20
TOP_REPOS_COUNT = 5
BEAUTY_MARKERS = ["nexus-STARS-sync", "At a Glance", "Browse by Language", "Auto-synced with"]
MARKER_THRESHOLD = 3
LANG_EMOJI = {"Bicep":"🏗️","C":"🔧","C#":"🟪","C++":"⚡","Cuda":"🟢","CSS":"🎨","Dart":"🎯","Dockerfile":"🐳","Elixir":"🧪","Erlang":"📡","Go":"🐹","HCL":"☁️","HTML":"🌐","Haskell":"📐","Java":"☕","JavaScript":"✨","Jupyter Notebook":"📓","Kotlin":"🟣","Lua":"🌙","Makefile":"🔨","Markdown":"📝","Nix":"❄️","Objective-C":"🍎","Others":"📦","PDDL":"🧩","Perl":"🐪","PHP":"🐘","PowerShell":"💠","Python":"🐍","R":"📊","Ruby":"💎","Rust":"🦀","SCSS":"🎨","Scala":"🔴","Shell":"🐚","Swift":"🦅","TSQL":"🗄️","TeX":"📄","TypeScript":"🔷","Vue":"💚","Zig":"⚡"}
CATEGORIES = [("🧠 AI & Machine Learning",["Python","Jupyter Notebook","Cuda","R"]),("🌐 Web Development",["JavaScript","TypeScript","HTML","CSS","Vue","SCSS","Dart"]),("⚙️ Systems Programming",["C","C++","Rust","Go","Shell","Makefile","Dockerfile","HCL","Nix"]),("📱 App Development",["Swift","Kotlin","Java","Objective-C","C#"]),("🔧 Infrastructure",["PowerShell","TSQL","Bicep","PDDL"]),("📚 Documentation",["Markdown","TeX","Others"]),("🧪 Experimental",["Elixir","Erlang","Haskell","Lua","Perl","PHP","Ruby","Scala","Zig"])]
SKIP_SECTIONS = {"contents","license","table of contents"}
log = logging.getLogger("beautify-stars")

def parse_stars_md(content):
    languages = {}
    current_lang = None
    for line in content.split("\n"):
        lang_match = re.match(r"^## (.+?)\s*$", line)
        if lang_match:
            current_lang = lang_match.group(1).strip().rstrip("#").strip()
            if current_lang.lower() in SKIP_SECTIONS:
                current_lang = None
                continue
            if current_lang not in languages:
                languages[current_lang] = []
            continue
        star_match = re.match(r"^\- $$([^$$]+)\]$$([^$$]+)\)\s*\-\s*(.+)$", line)
        if star_match and current_lang:
            repo, url, desc = star_match.groups()
            languages[current_lang].append({"repo":repo,"url":url,"desc":desc.strip()})
    return languages

def count_stars(languages):
    return sum(len(repos) for repos in languages.values())

def truncate_desc(desc, max_len=90):
    if len(desc) <= max_len: return desc
    return desc[:max_len].rsplit(" ",1)[0] + "…"

def make_bar(value, max_value, width=BAR_WIDTH):
    if max_value == 0: return "░" * width
    filled = round(value / max_value * width)
    filled = max(0, min(width, filled))
    return "█" * filled + "░" * (width - filled)

def make_pct(value, total):
    if total == 0: return "0.0%"
    return f"{value / total * 100:.1f}%"

def build_header(total_stars, lang_count):
    now = datetime.now(timezone.utc).strftime("%b %d, %Y")
    date_slug = now.replace(" ","%20").replace(",","")
    return f'''<div align="center">
<img src="https://raw.githubusercontent.com/specimba/nexus-STARS-sync/main/assets/logo.png" width="80" alt="nexus logo" onerror="this.style.display='none'">
# ⭐ nexus-STARS-sync
### A curated archive of {total_stars} repositories across {lang_count} languages
<br>
![Last synced](https://img.shields.io/badge/last%20synced-{date_slug}-3b82f6?style=flat-square&logo=github&logoColor=white)
![Repositories](https://img.shields.io/badge/repos-{total_stars}-eab308?style=flat-square)
![Languages](https://img.shields.io/badge/languages-{lang_count}-22c55e?style=flat-square)
<br>
> *These are the projects that shaped how I think about software.*
> *Curated from years of starring — now searchable, shareable, and always in sync.*
<br>
</div>
'''

def build_stats_overview(languages):
    total = count_stars(languages)
    lines = ['<div align="center">\n',"### 📊 At a Glance\n","<table><tr>"]
    for cat_name, cat_langs in CATEGORIES:
        matching = {l:languages[l] for l in cat_langs if l in languages}
        if not matching: continue
        repo_count = sum(len(r) for r in matching.values())
        lang_n = len(matching)
        pct = make_pct(repo_count, total)
        lines.append(f'<td align="center"><b>{cat_name}</b><br><sub>{repo_count} repos · {lang_n} lang · {pct}</sub></td>')
    lines.append("</tr></table>\n")
    lines.append("<details>")
    lines.append("<summary><b>📈 Distribution by Category</b></summary>\n")
    max_cat = 0
    cat_data = []
    for cat_name, cat_langs in CATEGORIES:
        matching = {l:languages[l] for l in cat_langs if l in languages}
        if not matching: continue
        repo_count = sum(len(r) for r in matching.values())
        max_cat = max(max_cat, repo_count)
        cat_data.append((cat_name, repo_count))
    for cat_name, repo_count in cat_data:
        bar = make_bar(repo_count, max_cat, 25)
        pct = make_pct(repo_count, total)
        lines.append(f"- {cat_name} `{bar}` {repo_count} ({pct})")
    lines.append("")
    lines.append("</details>\n")
    lines.append("</div>\n")
    return "\n".join(lines)

def build_toc(languages):
    total = count_stars(languages)
    max_count = max(len(repos) for repos in languages.values()) if languages else 1
    lines = ["---\n","### 📑 Browse by Language\n","<details open>",f"<summary><b>Languages A–Z</b> · {total} total</summary>\n"]
    for lang in sorted(languages.keys(), key=str.lower):
        emoji = LANG_EMOJI.get(lang, "📄")
        count = len(languages[lang])
        anchor = lang.lower().replace(" ","-").replace("#","sharp").replace("+","plus")
        bar = make_bar(count, max_count)
        pct = make_pct(count, total)
        lines.append(f"- {emoji} **[{lang}](#{anchor})** `{bar}` {count} ({pct})")
    lines.append("")
    lines.append("</details>\n")
    return "\n".join(lines)

def build_highlighted_repos(languages):
    lines = ["---\n","### 🏆 Highlighted Repos\n","<details>","<summary><b>Top picks per language</b></summary>\n"]
    has_content = False
    for lang in sorted(languages.keys(), key=str.lower):
        repos = languages[lang]
        if not repos: continue
        emoji = LANG_EMOJI.get(lang, "📄")
        has_content = True
        lines.append(f"#### {emoji} {lang}\n")
        shown = repos[:TOP_REPOS_COUNT]
        for r in shown:
            desc = truncate_desc(r["desc"], 70)
            lines.append(f"- [{r['repo']}]({r['url']}) — {desc}")
        remaining = len(repos) - TOP_REPOS_COUNT
        if remaining > 0:
            lines.append(f"- *…and {remaining} more*")
        lines.append("")
    if not has_content: lines.append("*No repos found.*\n")
    lines.append("</details>\n")
    return "\n".join(lines)

def build_language_section(lang, repos):
    emoji = LANG_EMOJI.get(lang, "📄")
    lines = [f"### {emoji} {lang}","","| Repository | Description |","|:-----------|:------------|"]
    for r in repos:
        desc = truncate_desc(r["desc"])
        lines.append(f"| [{r['repo']}]({r['url']}) | {desc} |")
    lines.append("")
    return "\n".join(lines)

def build_footer():
    return '''---
<div align="center">
<br>
**nexus-STARS-sync** — because GitHub's starred page doesn't paginate
<br>
<sub>Auto-synced with <a href="https://github.com/maguowei/starred">starred</a> · Built for <a href="https://github.com/specimba">@specimba</a></sub>
<br><br>
</div>
'''

def is_already_beautified(content):
    hits = sum(1 for m in BEAUTY_MARKERS if m in content)
    return hits >= MARKER_THRESHOLD

def build_parser():
    parser = argparse.ArgumentParser(prog="beautify-stars", description="Transform starred README into a beautiful page.")
    parser.add_argument("-V","--version",action="version",version=f"%(prog)s {VERSION}")
    parser.add_argument("-i","--input",default="README.md",help="Input file")
    parser.add_argument("-o","--output",default=None,help="Output file")
    parser.add_argument("-f","--force",action="store_true",help="Re-beautify even if already processed")
    parser.add_argument("-v","--verbose",action="store_true",help="Enable debug logging")
    return parser

def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    level = logging.DEBUG if args.verbose else logging.INFO
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter("  %(levelname)s: %(message)s"))
    log.addHandler(handler)
    log.setLevel(level)
    input_path = Path(args.input)
    output_path = Path(args.output) if args.output else input_path
    if not input_path.exists():
        log.error(f"Input file not found: {input_path}")
        return 1
    try:
        content = input_path.read_text(encoding="utf-8")
    except UnicodeDecodeError as e:
        log.error(f"Failed to read {input_path}: {e}")
        return 1
    if not args.force and is_already_beautified(content):
        log.info("README already beautified. Use --force to re-process.")
        return 0
    languages = parse_stars_md(content)
    if not languages:
        log.error("No language sections found. Is this a starred-generated README?")
        return 1
    total = count_stars(languages)
    lang_count = len(languages)
    log.info(f"Parsed {total} repos across {lang_count} languages")
    parts = [build_header(total, lang_count)]
    parts.append(build_stats_overview(languages))
    parts.append(build_toc(languages))
    parts.append(build_highlighted_repos(languages))
    for lang in sorted(languages.keys(), key=str.lower):
        parts.append(build_language_section(lang, languages[lang]))
    parts.append(build_footer())
    new_content = "\n".join(parts)
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(new_content, encoding="utf-8")
    except OSError as e:
        log.error(f"Failed to write {output_path}: {e}")
        return 1
    log.info(f"✨ Beautified {output_path} — {total} repos, {lang_count} languages")
    return 0

if __name__ == "__main__":
    sys.exit(main())
