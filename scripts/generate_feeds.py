#!/usr/bin/env python3
"""Build feed.xml, sitemap.xml and robots.txt, and keep every page's head in sync.

Everything is derived from metadata the pages already carry, so a new post
only needs its normal head block:

    python3 scripts/generate_feeds.py

Re-running is idempotent. Pass a different analytics code with --code.
"""
from __future__ import annotations

import argparse
import html
import re
from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://juancopi81.github.io"
AUTHOR = "Juan Carlos"
FEED_TITLE = "Juan Carlos — Research Log"
FEED_DESC = ("Research logs, derivations, and tutorials from personal machine "
             "learning projects, including an ongoing series rebuilding "
             "diffusion models from first principles.")

# The GoatCounter site code; the script is cookieless, so no consent banner.
GOATCOUNTER = "juancopi81"

ANALYTICS_MARK = "data-goatcounter"
FEED_LINK_MARK = 'rel="alternate"'


def pages() -> list[Path]:
    return ([ROOT / n for n in ("index.html", "about.html", "projects.html", "writing.html")]
            + sorted((ROOT / "posts").glob("*.html")))


def meta(text: str, key: str) -> str:
    m = re.search(rf'<meta (?:name|property)="{re.escape(key)}" content="([^"]*)" />', text)
    return html.unescape(m.group(1)) if m else ""


def posts() -> list[dict]:
    out = []
    for path in sorted((ROOT / "posts").glob("*.html"), reverse=True):
        text = path.read_text()
        published = meta(text, "article:published_time")
        if not published:
            continue
        out.append({
            "title": meta(text, "og:title"),
            "description": meta(text, "og:description"),
            "url": f"{SITE}/posts/{path.name}",
            "image": meta(text, "og:image"),
            "date": datetime.strptime(published, "%Y-%m-%d").replace(tzinfo=timezone.utc),
            "path": path,
        })
    return out


def write_feed(items: list[dict]) -> None:
    # Descriptions only, not full text: these posts are mostly MathJax, which
    # feed readers render as raw TeX.
    built = max((i["date"] for i in items), default=datetime.now(timezone.utc))
    entries = "\n".join(f"""    <item>
      <title>{escape(i['title'])}</title>
      <link>{i['url']}</link>
      <guid isPermaLink="true">{i['url']}</guid>
      <pubDate>{i['date'].strftime('%a, %d %b %Y %H:%M:%S +0000')}</pubDate>
      <description>{escape(i['description'])}</description>
      <media:thumbnail url="{i['image']}" />
    </item>""" for i in items)

    (ROOT / "feed.xml").write_text(f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom" xmlns:media="http://search.yahoo.com/mrss/">
  <channel>
    <title>{escape(FEED_TITLE)}</title>
    <link>{SITE}/writing.html</link>
    <description>{escape(FEED_DESC)}</description>
    <language>en-us</language>
    <lastBuildDate>{built.strftime('%a, %d %b %Y %H:%M:%S +0000')}</lastBuildDate>
    <atom:link href="{SITE}/feed.xml" rel="self" type="application/rss+xml" />
{entries}
  </channel>
</rss>
""")


def write_sitemap(items: list[dict]) -> None:
    rows = []
    for path in pages():
        rel = path.relative_to(ROOT).as_posix()
        loc = f"{SITE}/" if rel == "index.html" else f"{SITE}/{rel}"
        published = meta(path.read_text(), "article:published_time")
        lastmod = published or datetime.now(timezone.utc).strftime("%Y-%m-%d")
        rows.append(f"  <url>\n    <loc>{loc}</loc>\n    <lastmod>{lastmod}</lastmod>\n  </url>")
    (ROOT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(rows) + "\n</urlset>\n")


def write_robots() -> None:
    (ROOT / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n")


def sync_heads(code: str) -> int:
    """Ensure every page carries feed autodiscovery and the analytics script."""
    feed_link = ('<link rel="alternate" type="application/rss+xml" '
                 f'title="{html.escape(FEED_TITLE, quote=True)}" href="{SITE}/feed.xml" />')
    analytics = ('<script data-goatcounter="https://'
                 f'{code}.goatcounter.com/count" async src="https://gc.zgo.at/count.js"></script>')
    touched = 0
    for path in pages():
        text = original = path.read_text()
        anchor = re.search(r'^([ \t]*)<link rel="canonical"[^>]*/>\n', text, re.M)
        indent = anchor.group(1)

        if FEED_LINK_MARK not in text:
            text = text[:anchor.end()] + f"{indent}{feed_link}\n" + text[anchor.end():]
        if ANALYTICS_MARK in text:  # replace so the code can be changed in one command
            text = re.sub(r'[ \t]*<script data-goatcounter=.*?</script>\n',
                          f"{indent}{analytics}\n", text, flags=re.S)
        else:
            close = re.search(r'^([ \t]*)</head>', text, re.M)
            text = text[:close.start()] + f"{indent}{analytics}\n" + text[close.start():]

        if text != original:
            path.write_text(text)
            touched += 1
    return touched


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--code", default=GOATCOUNTER, help="GoatCounter site code")
    args = ap.parse_args()

    items = posts()
    write_feed(items)
    write_sitemap(items)
    write_robots()
    touched = sync_heads(args.code)

    print(f"feed.xml      {len(items)} posts")
    print(f"sitemap.xml   {len(pages())} urls")
    print(f"robots.txt    -> {SITE}/sitemap.xml")
    print(f"head sync     {touched} pages updated (analytics code: {args.code})")


if __name__ == "__main__":
    main()
