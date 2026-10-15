"""Prepare a copied Staatic export for Cloudflare Workers Static Assets.

Usage: python scripts/prepare_export.py site PATH_TO_WORDPRESS_DATA
Never run this on the WordPress source or Staatic's staging directory.
"""

from pathlib import Path
import json
import re
import shutil
import sys


site = Path(sys.argv[1]).resolve()
wordpress = Path(sys.argv[2]).resolve()
if not (site / "index.html").is_file() or not (wordpress / "wp-content").is_dir():
    raise SystemExit("Expected a copied Staatic site and a WordPress source directory")
if site == wordpress or wordpress in site.parents:
    raise SystemExit("The copied site must be outside the WordPress source")

not_found = site / "404_not_found" / "index.html"
if not not_found.is_file():
    raise SystemExit("The full export has no 404 page")
shutil.copy2(not_found, site / "404.html")

# Static hosting has no WordPress search endpoint. Give visitors a useful exit
# from the not-found page instead of a search form that silently shows home.
for page in (not_found, site / "404.html"):
    content = page.read_text(encoding="utf-8", errors="replace")
    content, replacements = re.subn(
        r"<p>\s*It looks like nothing was found at this location\. Maybe try a search\?\s*</p>\s*<form\b.*?</form>",
        '<p>It looks like nothing was found at this location. <a href="/">Return to the home page</a>.</p>',
        content,
        count=1,
        flags=re.I | re.S,
    )
    if replacements:
        page.write_text(content, encoding="utf-8")

removed_tags = re.compile(r"<link\b[^>]*(?:/wp-json/|/xmlrpc\.php)[^>]*>", re.I)
protected_tags = re.compile(
    r"<(?:link|meta)\b[^>]*(?:rel=['\"]canonical['\"]|property=['\"]og:url['\"])[^>]*>",
    re.I,
)
own_origin = re.compile(r"https?://blog\.shipwatcher\.com(?=/|[\"'\s<]|$)", re.I)
html_files_changed = 0
for path in site.rglob("*.html"):
    original = path.read_text(encoding="utf-8", errors="replace")
    content = removed_tags.sub("", original)
    protected = []

    def hold_tag(match):
        protected.append(match.group(0))
        return f"__SHIPWATCHER_CANONICAL_{len(protected) - 1}__"

    content = protected_tags.sub(hold_tag, content)
    content = own_origin.sub(
        lambda match: "" if content[match.end() : match.end() + 1] == "/" else "/",
        content,
    )
    for number, tag in enumerate(protected):
        content = content.replace(f"__SHIPWATCHER_CANONICAL_{number}__", tag)
    if content != original:
        path.write_text(content, encoding="utf-8")
        html_files_changed += 1

font_files_copied = 0
for path in site.rglob("*.css"):
    original = path.read_text(encoding="utf-8", errors="replace")
    content = original.replace("/:8084/wp-content/fonts/", "/wp-content/fonts/")
    if content != original:
        path.write_text(content, encoding="utf-8")
    for relative in set(re.findall(r"/wp-content/fonts/[^)'\"\s]+\.woff2?", content, re.I)):
        source = wordpress / relative.lstrip("/")
        target = site / relative.lstrip("/")
        if not source.is_file():
            raise SystemExit(f"Referenced font is absent from WordPress: {source}")
        if not target.is_file():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            font_files_copied += 1

portrait = Path("wp-content/gallery/neil/neilsmall2.jpg")
source = wordpress / portrait
if not source.is_file():
    raise SystemExit(f"Referenced sidebar portrait is absent: {source}")
target = site / portrait
target.parent.mkdir(parents=True, exist_ok=True)
shutil.copy2(source, target)

# These crawler results are not useful public site assets. The PHP-named item
# is a rendered security-plugin probe and should never be served as a download.
for relative in (
    "wp-content/uploads/code-execution.php",
    "wp-json/index.html",
):
    path = site / relative
    if path.is_file():
        path.unlink()
api_directory = site / "wp-json"
if api_directory.is_dir() and not any(api_directory.iterdir()):
    api_directory.rmdir()

# WordPress's original postmap contains plain slugs. Some published pages use
# Page Links To or have a parent page, so their numeric shortlinks need these
# actual destinations. Post IDs were checked against the local WordPress DB.
postmap = site / "postmap.json"
data = json.loads(postmap.read_text(encoding="utf-8"))
mapping = data.get("map", data)
mapping.update(
    {
        "3": "/about/",
        "5": "/about/image-credits/",
        "8": "http://ShipWatcher.com/",
        "13": "http://ShipWatcher.com/photos/",
        "19": "http://vqe2.com/",
        "22": "http://www.youtube.com/MagicTyger/",
        "25": "http://blog.NeilEnnis.com/",
        "27": "http://tech.neilennis.com/",
        "29": "http://pol.neilennis.com/",
        "32": "http://blog.neilennis.com/",
        "538": "https://blog.neilennis.com/index.php/contact/",
        "542": "/",
    }
)
postmap.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")

resolver = site / "p" / "index.html"
content = resolver.read_text(encoding="utf-8")
old_redirect = 'const dest = "/" + slug.replace(/^\\/+/, "").replace(/\\/?$/, "/");'
new_redirect = (
    'const dest = /^https?:\\/\\//i.test(slug) ? slug : '
    '"/" + slug.replace(/^\\/+/, "").replace(/\\/?$/, "/");'
)
if old_redirect in content:
    resolver.write_text(content.replace(old_redirect, new_redirect), encoding="utf-8")
elif new_redirect not in content:
    raise SystemExit("Unrecognized numeric shortlink resolver")

# WordPress query-style links still occur in sidebar content and old bookmarks.
home = site / "index.html"
content = home.read_text(encoding="utf-8")
legacy_query_redirect = (
    "<script>"
    "(function(){const q=new URLSearchParams(location.search);"
    "const id=q.get('p')||q.get('page_id');"
    "if(id&&/^\\d+$/.test(id))location.replace('/p/?id='+id);})()"
    "</script>"
)
if legacy_query_redirect not in content:
    if "<head>" not in content:
        raise SystemExit("Home page has no head element for query-style links")
    home.write_text(content.replace("<head>", "<head>" + legacy_query_redirect, 1), encoding="utf-8")

print(
    f"Prepared {html_files_changed} HTML files, copied {font_files_copied} "
    "fonts and the sidebar portrait."
)
