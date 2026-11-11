#!/usr/bin/env python3
"""A small file-based wiki: shelves > books > chapters > pages.

    python wiki.py            serve on http://localhost:8000 (live reload of content on refresh)
    python wiki.py build      write a static copy to ./site
"""
import argparse
import html
import json
import mimetypes
import re
import shutil
import unicodedata
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, unquote, urlparse

import markdown

ROOT = Path(__file__).resolve().parent
CONTENT = ROOT / "content"
THEME = ROOT / "theme"
OUT = ROOT / "site"
CONFIG_FILE = ROOT / "wiki.json"

CONFIG = {"name": "Wiki", "base_url": "", "footer": ""}
BASE = ""
EDIT = True  # in-browser creating/editing; switched off for static builds

esc = html.escape

ICONS = {
    "shelf": '<path d="M4 4h3.5v16H4zM9 4h3.5v16H9zM14.3 5.6l3.2-.9 3.9 14.5-3.2.9z"/>',
    "book": '<path d="M7 2h11a1 1 0 0 1 1 1v14H8a1.5 1.5 0 0 0 0 3h11v2H8a3.5 3.5 0 0 1-3.5-3.5V4.5A2.5 2.5 0 0 1 7 2z"/>',
    "chapter": '<path d="M4 5h16v2.5H4zm0 5.75h16v2.5H4zM4 16.5h10V19H4z"/>',
    "page": '<path d="M6 2h8l5 5v15H6zm7.5 1.8V8h4.2z"/>',
    "search": '<path d="M10 3a7 7 0 0 1 5.6 11.2l5.1 5.1-1.4 1.4-5.1-5.1A7 7 0 1 1 10 3zm0 2a5 5 0 1 0 0 10 5 5 0 0 0 0-10z"/>',
    "moon": '<path d="M12 3a9 9 0 1 0 9 9c0-.5 0-.9-.1-1.4A6.5 6.5 0 0 1 12.4 3.100z"/>',
    "list": '<path d="M3 5h2.5v2.5H3zm5 0h13v2.500H8zM3 10.750h2.500v2.500H3zm5 0h13v2.500H8zM3 16.500h2.500V19H3zm5 0h13V19H8z"/>',
    "tag": '<path d="M3 3h8l10 10-8 8L3 11zm4.500 3a1.500 1.500 0 1 0 0 3 1.500 1.500 0 0 0 0-3z"/>',
    "plus": '<path d="M10.75 4h2.5v6.75H20v2.5h-6.75V20h-2.5v-6.75H4v-2.5h6.75z"/>',
    "edit": '<path d="M16.8 3.2l4 4L8.5 19.5l-5 1 1-5zM5.9 16.3l-.4 2.2 2.2-.4z"/>',
    "logo": '<path d="M12 2l9 5v10l-9 5-9-5V7zm0 2.300L5.800 7.700 12 11.200l6.200-3.500zM5 9.400v6.400l6 3.400v-6.400zm14 0l-6 3.400v6.400l6-3.400z"/>',
}


def icon(name):
    return f'<svg class="icon" viewBox="0 0 24 24" aria-hidden="true">{ICONS[name]}</svg>'


def strip_order(name):
    return re.sub(r"^\d+[-_. ]+", "", name)


def slugify(name):
    text = unicodedata.normalize("NFKD", strip_order(name)).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:60].strip("-") or "untitled"


def render_markdown(text):
    md = markdown.Markdown(extensions=["extra", "toc", "sane_lists", "admonition"])
    return md.convert(text), md.toc_tokens


def prettify(name):
    text = re.sub(r"[-_]+", " ", strip_order(name)).strip()
    return text[:1].upper() + text[1:]


def url(path):
    return BASE + path


def when(ts):
    dt = datetime.fromtimestamp(ts)
    return f'<time datetime="{dt.isoformat(timespec="seconds")}" data-rel>{dt:%Y-%m-%d}</time>'


def visible(path):
    return not path.name.startswith(("_", "."))


def entries(folder):
    return sorted((p for p in folder.iterdir() if visible(p)), key=lambda p: p.name.lower())


class Node:
    def __init__(self, kind, path, parent=None):
        self.kind, self.path, self.parent = kind, path, parent
        self.children = []
        name = path.stem if path.is_file() else path.name
        self.slug = slugify(name)
        meta = {}
        meta_file = path / "_meta.json"
        if path.is_dir() and meta_file.exists():
            meta = json.loads(meta_file.read_text("utf-8"))
        self.title = meta.get("title") or prettify(name)
        self.desc = meta.get("description", "")
        self.cover = meta.get("cover")
        st = path.stat()
        self.updated = st.st_mtime
        self.created = getattr(st, "st_birthtime", st.st_ctime)
        self.body = self.html = self.text = ""
        self.toc = []
        if kind == "page":
            raw = path.read_text("utf-8-sig")
            m = re.match(r"\s*#[ \t]+(.+?)[ \t#]*(?:\n|$)", raw)
            if m:
                self.title, raw = m.group(1).strip(), raw[m.end():]
            self.body = raw

    @property
    def book(self):
        node = self
        while node and node.kind != "book":
            node = node.parent
        return node

    @property
    def url(self):
        if self.kind == "shelf":
            return url(f"/shelves/{self.slug}/")
        if self.kind == "book":
            return url(f"/books/{self.slug}/")
        return self.parent.url + self.slug + "/"

    def pages(self):
        for child in self.children:
            if child.kind == "page":
                yield child
            else:
                yield from child.pages()

    def trail(self):
        return (self.parent.trail() if self.parent else []) + [self]


class Site:
    def __init__(self):
        self.shelves, self.by_path = [], {}
        if CONTENT.is_dir():
            for sd in filter(Path.is_dir, entries(CONTENT)):
                shelf = self.add(Node("shelf", sd))
                self.shelves.append(shelf)
                for bd in filter(Path.is_dir, entries(sd)):
                    book = self.add(Node("book", bd, shelf))
                    shelf.children.append(book)
                    for item in entries(bd):
                        if item.is_dir():
                            chapter = self.add(Node("chapter", item, book))
                            book.children.append(chapter)
                            for f in entries(item):
                                if f.suffix.lower() == ".md":
                                    chapter.children.append(self.add(Node("page", f, chapter)))
                        elif item.suffix.lower() == ".md":
                            book.children.append(self.add(Node("page", item, book)))
        self.books = [b for s in self.shelves for b in s.children]
        for shelf in self.shelves:
            for book in shelf.children:
                for chapter in (c for c in book.children if c.kind == "chapter"):
                    self.bubble(chapter)
                self.bubble(book)
            self.bubble(shelf)
        self.all_pages = [p for b in self.books for p in b.pages()]
        for page in self.all_pages:
            self.render_page(page)
        self.by_route = {n.url: n for n in self.by_path.values()}
        self.routes = self.build_routes()

    def add(self, node):
        self.by_path[node.path.resolve()] = node
        return node

    @staticmethod
    def bubble(node):
        if node.children:
            node.updated = max(c.updated for c in node.children)
            node.created = min(c.created for c in node.children)

    # ---------- markdown ----------

    def render_page(self, page):
        out, toc_tokens = render_markdown(page.body)

        def fix(m):
            attr, val = m.group(1), html.unescape(m.group(2))
            if re.match(r"([a-z][a-z0-9+.-]*:|/|#|\?)", val, re.I):
                return m.group(0)
            target, _, frag = val.partition("#")
            dest = (page.path.parent / unquote(target)).resolve()
            frag = "#" + frag if frag else ""
            if dest in self.by_path:
                return f'{attr}="{esc(self.by_path[dest].url + frag)}"'
            if dest.is_file() and dest.is_relative_to(CONTENT):
                return f'{attr}="{esc(url("/files/" + dest.relative_to(CONTENT).as_posix()) + frag)}"'
            return m.group(0)

        page.html = re.sub(r'\b(src|href)="([^"]+)"', fix, out)
        page.text = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", out))).strip()

        def flat(tokens):
            for t in tokens:
                yield t["level"], t["id"], t["name"]
                yield from flat(t["children"])

        page.toc = list(flat(toc_tokens))

    # ---------- fragments ----------

    def file_url(self, node, rel):
        return url("/files/" + (node.path / rel).relative_to(CONTENT).as_posix())

    def card(self, node):
        hue = sum(node.slug.encode()) * 37 % 360
        style = f"--h:{hue}"
        if node.cover:
            style += f";background-image:url('{esc(self.file_url(node, node.cover))}')"
        return (
            f'<a class="card kind-{node.kind}" href="{node.url}">'
            f'<div class="cover" style="{style}">{icon(node.kind)}</div>'
            f'<div class="card-body"><h3>{esc(node.title)}</h3><p>{esc(node.desc)}</p></div>'
            f'<div class="card-meta"><span>Created {when(node.created)}</span>'
            f"<span>Updated {when(node.updated)}</span></div></a>"
        )

    def grid(self, nodes, empty):
        if not nodes:
            return f'<p class="empty">{empty}</p>'
        return '<div class="grid">' + "".join(self.card(n) for n in nodes) + "</div>"

    def row(self, node):
        blurb = node.desc if node.kind != "page" else node.text[:160]
        return (
            f'<a class="row kind-{node.kind}" href="{node.url}">{icon(node.kind)}'
            f"<div><h4>{esc(node.title)}</h4><p>{esc(blurb)}</p></div></a>"
        )

    def rows(self, nodes):
        out = []
        for n in nodes:
            out.append(self.row(n))
            if n.kind == "chapter" and n.children:
                out.append('<div class="row-children">' + "".join(self.row(c) for c in n.children) + "</div>")
        return '<div class="rows">' + "".join(out) + "</div>"

    def mini_list(self, title, nodes):
        items = "".join(
            f'<a class="mini kind-{n.kind}" href="{n.url}">{icon(n.kind)}<span>{esc(n.title)}</span></a>' for n in nodes
        ) or '<p class="empty">Nothing here yet.</p>'
        return f'<section class="side-block"><h5>{title}</h5>{items}</section>'

    @staticmethod
    def act(label, ico, href):
        return f'<a class="mini" href="{esc(href)}">{icon(ico)}<span>{label}</span></a>'

    def new_link(self, kind, parent=None):
        if not EDIT:
            return ""
        where = f"&in={quote(parent.url)}" if parent else ""
        return self.act(f"New {kind}", "plus", url(f"/new/?kind={kind}{where}"))

    def edit_link(self, node):
        return self.act(f"Edit {node.kind}", "edit", url(f"/edit/?at={quote(node.url)}")) if EDIT else ""

    def form_page(self, kind, parent=None, node=None, values=None, error=""):
        v = values or {}
        heading = f"Edit {kind}" if node else f"New {kind}"
        back = node.url if node else parent.url if parent else url("/")
        title = v.get("title", node.title if node else "")
        fields = (f'<label>Title<input name="title" value="{esc(title)}" required autofocus '
                  f'maxlength="120" autocomplete="off"></label>')
        buttons = '<button class="btn" type="submit">Save</button>'
        if kind == "page":
            body = v.get("body", node.body.strip("\n") if node else "")
            fields += ('<label>Content <small>(Markdown)</small>'
                       f'<textarea name="body" id="editor" rows="22">\n{esc(body)}</textarea></label>'
                       '<div id="preview" class="content preview" hidden></div>')
            buttons += '<button type="button" class="btn ghost" data-action="preview">Preview</button>'
        else:
            desc = v.get("description", node.desc if node else "")
            fields += f'<label>Description<textarea name="description" rows="3">\n{esc(desc)}</textarea></label>'
        buttons += f'<a class="btn ghost" href="{back}">Cancel</a>'
        where = f'<p class="lead">In {parent.kind} "{esc(parent.title)}"</p>' if parent and not node else ""
        err = f'<p class="error">{esc(error)}</p>' if error else ""
        anchor = node or parent
        book = anchor.book if anchor else None
        return self.layout(
            heading,
            f'<section class="panel"><h1>{heading}</h1>{where}{err}'
            f'<form class="edit" method="post">{fields}<div class="buttons">{buttons}</div></form></section>',
            left=self.book_nav(book, node) if book else "",
            crumbs=self.crumbs(anchor, extra=heading),
        )

    def actions(self, view_toggle=True, extra=""):
        view = (
            f'<a href="#" class="mini" data-action="view">{icon("list")}<span data-label="view">List view</span></a>'
            if view_toggle else ""
        )
        return (
            f'<section class="side-block"><h5>Actions</h5>{extra}{view}'
            f'<a href="#" class="mini" data-action="theme">{icon("moon")}<span data-label="theme">Dark mode</span></a>'
            f"</section>"
        )

    def details(self, node):
        return (
            f'<section class="side-block"><h5>Details</h5>'
            f'<p class="detail">Created {when(node.created)}</p>'
            f'<p class="detail">Updated {when(node.updated)}</p></section>'
        )

    def book_nav(self, book, current):
        def link(n):
            cls = f"mini kind-{n.kind}" + (" current" if n is current else "")
            return f'<a class="{cls}" href="{n.url}">{icon(n.kind)}<span>{esc(n.title)}</span></a>'

        out = [link(book)]
        for child in book.children:
            out.append(link(child))
            if child.kind == "chapter":
                out.append('<div class="nested">' + "".join(link(p) for p in child.children) + "</div>")
        return f'<section class="side-block booknav"><h5>Book navigation</h5>{"".join(out)}</section>'

    def crumbs(self, node=None, extra=None):
        parts = [f'<a href="{url("/")}">{icon("shelf")}Shelves</a>']
        for n in node.trail() if node else []:
            parts.append(f'<a class="kind-{n.kind}" href="{n.url}">{icon(n.kind)}{esc(n.title)}</a>')
        if extra:
            parts.append(f"<span>{esc(extra)}</span>")
        return '<nav class="crumbs">' + '<span class="sep">›</span>'.join(parts) + "</nav>"

    def layout(self, title, main, left="", right="", crumbs=""):
        name = esc(CONFIG["name"])
        full = name if not title else f"{esc(title)} | {name}"
        footer = f'<footer>{esc(CONFIG["footer"])}</footer>' if CONFIG.get("footer") else ""
        return f"""<!doctype html>
<html lang="en" data-base="{BASE}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{full}</title>
<script>(function(){{var d=document.documentElement,t,v;try{{t=localStorage.getItem('wiki-theme');v=localStorage.getItem('wiki-view')}}catch(e){{}}
if(!t&&window.matchMedia&&matchMedia('(prefers-color-scheme: dark)').matches)t='dark';
if(t==='dark')d.dataset.theme='dark';if(v==='list')d.dataset.view='list'}})()</script>
<link rel="stylesheet" href="{url('/theme/style.css')}">
</head>
<body>
<header class="top">
  <a class="brand" href="{url('/')}">{icon('logo')}<span>{name}</span></a>
  <form class="search" action="{url('/search/')}" method="get" role="search">
    {icon('search')}<input type="search" name="q" placeholder="Search" aria-label="Search" autocomplete="off">
  </form>
  <nav class="links">
    <a href="{url('/')}">{icon('shelf')}<span>Shelves</span></a>
    <a href="{url('/books/')}">{icon('book')}<span>Books</span></a>
  </nav>
</header>
<div class="tri">
  <aside class="left">{left}</aside>
  <main>{crumbs}{main}</main>
  <aside class="right">{right}</aside>
</div>
{footer}
<script src="{url('/theme/app.js')}"></script>
</body>
</html>
"""

    # ---------- pages ----------

    def build_routes(self):
        r = {}
        recent_books = sorted(self.books, key=lambda b: -b.updated)[:8]
        recent_pages = sorted(self.all_pages, key=lambda p: -p.updated)[:8]

        r["/"] = self.layout(
            "",
            '<section class="panel"><h1>Shelves</h1>'
            + self.grid(self.shelves, "No shelves yet.")
            + "</section>",
            left=self.actions(extra=self.new_link("shelf")) + self.mini_list("Recent books", recent_books),
            right=self.mini_list("Recently updated pages", recent_pages),
        )
        r["/books/"] = self.layout(
            "Books",
            '<section class="panel"><h1>Books</h1>'
            + self.grid(sorted(self.books, key=lambda b: b.title.lower()), "No books yet.")
            + "</section>",
            left=self.actions() + self.mini_list("Recently updated pages", recent_pages),
            crumbs=self.crumbs(extra="Books"),
        )
        r["/search/"] = self.layout(
            "Search",
            '<section class="panel"><h1>Search</h1>'
            '<form class="search-big" action="" method="get"><input id="search-input" type="search" name="q" '
            'placeholder="Search shelves, books, chapters and pages" autocomplete="off"></form>'
            '<p id="search-count" class="empty"></p><div id="search-results" class="rows"></div></section>',
            left=self.actions(False),
            crumbs=self.crumbs(extra="Search"),
        )

        for shelf in self.shelves:
            desc = f'<p class="lead">{esc(shelf.desc)}</p>' if shelf.desc else ""
            r[f"/shelves/{shelf.slug}/"] = self.layout(
                shelf.title,
                f'<section class="panel"><h1>{esc(shelf.title)}</h1>{desc}'
                + self.grid(shelf.children, "This shelf has no books yet.")
                + "</section>",
                left=self.actions(extra=self.new_link("book", shelf) + self.edit_link(shelf)) + self.details(shelf),
                right=self.mini_list("Recent books", recent_books),
                crumbs=self.crumbs(shelf),
            )

        for book in self.books:
            key = f"/books/{book.slug}/"
            if key in r:
                print(f"warning: duplicate book slug '{book.slug}' ({book.path})")
            desc = f'<p class="lead">{esc(book.desc)}</p>' if book.desc else ""
            body = self.rows(book.children) if book.children else '<p class="empty">This book has no pages yet.</p>'
            r[key] = self.layout(
                book.title,
                f'<section class="panel"><h1>{esc(book.title)}</h1>{desc}{body}</section>',
                left=self.actions(False, self.new_link("page", book) + self.new_link("chapter", book)
                                  + self.edit_link(book)) + self.details(book),
                right=self.book_nav(book, book),
                crumbs=self.crumbs(book),
            )
            flat = list(book.pages())
            for chapter in (c for c in book.children if c.kind == "chapter"):
                cdesc = f'<p class="lead">{esc(chapter.desc)}</p>' if chapter.desc else ""
                cbody = self.rows(chapter.children) if chapter.children else '<p class="empty">No pages yet.</p>'
                r[f"{key}{chapter.slug}/"] = self.layout(
                    chapter.title,
                    f'<section class="panel"><h1>{esc(chapter.title)}</h1>{cdesc}{cbody}</section>',
                    left=self.book_nav(book, chapter),
                    right=self.actions(False, self.new_link("page", chapter) + self.edit_link(chapter))
                    + self.details(chapter),
                    crumbs=self.crumbs(chapter),
                )
            for i, page in enumerate(flat):
                prev = flat[i - 1] if i else None
                nxt = flat[i + 1] if i + 1 < len(flat) else None
                pager = '<nav class="pager">'
                pager += (f'<a class="prev" href="{prev.url}"><small>Previous</small>{esc(prev.title)}</a>'
                          if prev else "<span></span>")
                pager += (f'<a class="next" href="{nxt.url}"><small>Next</small>{esc(nxt.title)}</a>'
                          if nxt else "<span></span>")
                pager += "</nav>"
                toc = "".join(
                    f'<a class="toc-l{lvl}" href="#{esc(tid)}">{esc(html.unescape(name))}</a>'
                    for lvl, tid, name in page.toc
                )
                toc = f'<section class="side-block toc"><h5>On this page</h5>{toc}</section>' if toc else ""
                route = page.url[len(BASE):]
                r[route] = self.layout(
                    page.title,
                    f'<article class="panel content"><h1>{esc(page.title)}</h1>{page.html}</article>{pager}',
                    left=self.book_nav(book, page),
                    right=self.actions(False, self.edit_link(page) + self.new_link("page", page.parent))
                    + toc + self.details(page),
                    crumbs=self.crumbs(page),
                )
        return r

    def search_index(self):
        items = []
        for shelf in self.shelves:
            items.append({"kind": "shelf", "title": shelf.title, "url": shelf.url, "where": "", "text": shelf.desc})
            for book in shelf.children:
                items.append({"kind": "book", "title": book.title, "url": book.url,
                              "where": shelf.title, "text": book.desc})
                for child in book.children:
                    if child.kind == "chapter":
                        items.append({"kind": "chapter", "title": child.title, "url": child.url,
                                      "where": book.title, "text": child.desc})
        for page in self.all_pages:
            where = " › ".join(n.title for n in page.trail()[1:-1])
            items.append({"kind": "page", "title": page.title, "url": page.url, "where": where, "text": page.text})
        return json.dumps(items, ensure_ascii=False)

    def not_found(self):
        return self.layout(
            "Not found",
            '<section class="panel"><h1>Page not found</h1>'
            f'<p class="lead">Nothing lives at this address. <a href="{url("/")}">Back to the shelves</a>.</p></section>',
        )


# ---------- editing ----------

ALLOWED_PARENT = {"shelf": (None,), "book": ("shelf",), "chapter": ("book",), "page": ("book", "chapter")}


def edit_context(site, path, query):
    """Work out what a /new/ or /edit/ request refers to: (kind, parent, node) or None."""
    def one(key):
        return query.get(key, [""])[0]

    if path == "/edit/":
        node = site.by_route.get(one("at"))
        return (node.kind, node.parent, node) if node else None
    kind, parent = one("kind"), site.by_route.get(one("in"))
    if kind in ALLOWED_PARENT and (parent.kind if parent else None) in ALLOWED_PARENT[kind]:
        return kind, parent, None
    return None


def write_text(path, text):
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def write_meta(folder, title, desc):
    meta_file = folder / "_meta.json"
    meta = json.loads(meta_file.read_text("utf-8")) if meta_file.exists() else {}
    meta.update(title=title, description=desc)
    write_text(meta_file, json.dumps(meta, indent=2, ensure_ascii=False) + "\n")


def save(site, kind, parent, node, title, form):
    """Create or update an item on disk and return its path."""
    body = form.get("body", "").replace("\r\n", "\n").strip("\n")
    desc = " ".join(form.get("description", "").split())
    page_text = f"# {title}\n\n{body}\n" if body else f"# {title}\n"
    if node:
        write_text(node.path, page_text) if kind == "page" else write_meta(node.path, title, desc)
        return node.path
    folder = parent.path if parent else CONTENT
    folder.mkdir(parents=True, exist_ok=True)
    siblings = entries(folder)
    taken = {slugify(p.stem if p.is_file() else p.name) for p in siblings}
    if kind == "book":
        taken |= {b.slug for b in site.books}
    slug = base = slugify(title)
    n = 2
    while slug in taken:
        slug, n = f"{base}-{n}", n + 1
    numbers = [int(m.group(1)) for m in (re.match(r"(\d+)[-_. ]", p.name) for p in siblings) if m]
    name = f"{max(numbers, default=0) + 1:02d}-{slug}"
    if kind == "page":
        dest = folder / f"{name}.md"
        write_text(dest, page_text)
    else:
        dest = folder / name
        dest.mkdir()
        write_meta(dest, title, desc)
    return dest


# ---------- serve ----------

def signature():
    sig = [CONFIG_FILE.stat().st_mtime_ns if CONFIG_FILE.exists() else 0]
    if CONTENT.is_dir():
        sig += sorted((str(p), p.stat().st_mtime_ns) for p in CONTENT.rglob("*"))
    return sig


def load_config():
    if CONFIG_FILE.exists():
        CONFIG.update(json.loads(CONFIG_FILE.read_text("utf-8")))


class Handler(BaseHTTPRequestHandler):
    site, sig = None, None

    @classmethod
    def current(cls):
        sig = signature()
        if sig != cls.sig:
            load_config()
            cls.site, cls.sig = Site(), sig
        return cls.site

    def send(self, status, body, ctype="text/html; charset=utf-8", headers=()):
        data = body if isinstance(body, bytes) else body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        for k, v in headers:
            self.send_header(k, v)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(data)

    def send_file(self, base, rel):
        target = (base / rel).resolve()
        if not target.is_file() or not target.is_relative_to(base.resolve()):
            return self.send(404, "Not found", "text/plain; charset=utf-8")
        ctype = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        if ctype.startswith("text/") or ctype.endswith(("javascript", "json")):
            ctype += "; charset=utf-8"
        self.send(200, target.read_bytes(), ctype)

    def do_GET(self):
        path = unquote(urlparse(self.path).path)
        try:
            site = self.current()
        except Exception as exc:  # broken content should not kill the server
            return self.send(500, f"<pre>Could not load the wiki:\n{esc(repr(exc))}</pre>")
        if path.startswith("/theme/"):
            return self.send_file(THEME, path[7:])
        if path.startswith("/files/"):
            return self.send_file(CONTENT, path[7:])
        if path in ("/new/", "/edit/"):
            ctx = edit_context(site, path, parse_qs(urlparse(self.path).query))
            return self.send(200, site.form_page(*ctx)) if ctx else self.send(404, site.not_found())
        if path == "/search.json":
            return self.send(200, site.search_index(), "application/json; charset=utf-8")
        if path in site.routes:
            return self.send(200, site.routes[path])
        if path + "/" in site.routes:
            return self.send(301, "", headers=[("Location", path + "/")])
        self.send(404, site.not_found())

    do_HEAD = do_GET

    def do_POST(self):
        parsed = urlparse(self.path)
        path = unquote(parsed.path)
        origin = self.headers.get("Origin")
        cross_site = self.headers.get("Sec-Fetch-Site", "same-origin") not in ("same-origin", "none")
        if cross_site or (origin and urlparse(origin).netloc != self.headers.get("Host")):
            return self.send(403, "Forbidden", "text/plain; charset=utf-8")
        length = int(self.headers.get("Content-Length") or 0)
        if length > 5_000_000:
            return self.send(413, "Too large", "text/plain; charset=utf-8")
        raw = self.rfile.read(length).decode("utf-8", "replace")
        form = {k: v[0] for k, v in parse_qs(raw, keep_blank_values=True).items()}
        if path == "/preview":
            return self.send(200, render_markdown(form.get("body", ""))[0])
        site = self.current()
        ctx = edit_context(site, path, parse_qs(parsed.query)) if path in ("/new/", "/edit/") else None
        if not ctx:
            return self.send(404, site.not_found())
        kind, parent, node = ctx
        title = " ".join(form.get("title", "").split())[:120]
        if not title:
            return self.send(400, site.form_page(kind, parent, node, form, "Please enter a title."))
        try:
            dest = save(site, kind, parent, node, title, form)
            saved = self.current().by_path[dest.resolve()]
        except (OSError, KeyError, ValueError) as exc:
            return self.send(500, site.form_page(kind, parent, node, form, f"Could not save: {exc!r}"))
        self.send(303, "", headers=[("Location", saved.url)])

    def log_message(self, fmt, *args):
        pass


def serve(port):
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"{CONFIG['name']} running at http://localhost:{port}  (Ctrl+C to stop)", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


def build():
    global BASE, EDIT
    EDIT = False
    BASE = CONFIG.get("base_url", "").rstrip("/")
    site = Site()
    if OUT.exists():
        shutil.rmtree(OUT)
    for route, page in {**site.routes, "/404.html": site.not_found()}.items():
        dest = OUT / route.strip("/") / "index.html" if route.endswith("/") else OUT / route.strip("/")
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(page, "utf-8")
    (OUT / "search.json").write_text(site.search_index(), "utf-8")
    shutil.copytree(THEME, OUT / "theme")
    if CONTENT.is_dir():
        shutil.copytree(CONTENT, OUT / "files", ignore=shutil.ignore_patterns("*.md", "_meta.json"))
    print(f"Built {len(site.routes)} pages into {OUT}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", nargs="?", default="serve", choices=["serve", "build"])
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    load_config()
    build() if args.command == "build" else serve(args.port)


if __name__ == "__main__":
    main()
