# ARMOD Wiki

A small file-based wiki with a shelves > books > chapters > pages structure.
Content is plain Markdown in `content/`; there is no database.

## Run it

```bash
pip install -r requirements.txt
python wiki.py
```

Open http://localhost:8000. Edit a file, refresh the page, and the change shows up.
Use `python wiki.py --port 8080` for another port.

## Add content

**In the browser:** use the *Actions* box in the sidebar. *New shelf* is on the home page,
*New book* on a shelf, *New chapter* / *New page* on a book or chapter, and *Edit* on
everything. Pages are written in Markdown with a live preview. Everything is saved as
files in `content/`.

- **Images:** in the page editor use *Insert image*, or paste or drop an image into the
  text. Shelves and books can have a cover image (set it under *Edit*).
- **Equations:** write LaTeX as `$...$` (inline) or `$$...$$` (own line). They are drawn
  by MathJax, which is loaded from a CDN, so equations need an internet connection.
- **Delete:** every shelf, book, chapter and page has a *Delete* action. Deleted items
  are moved to `content/_trash`; move them back to restore, or empty that folder by hand.

Moving items and renaming addresses is done on disk. The server only listens on
this computer (`127.0.0.1`) and has no login, so do not expose it to a network as is.

**On disk:** create folders and files directly:

```text
content/<shelf>/<book>/<page>.md
content/<shelf>/<book>/<chapter>/<page>.md
```

- Prefix names with `01-`, `02-` ... to set the order.
- A page's title is its first `# Heading`.
- Put an optional `_meta.json` (`title`, `description`, `cover`) in a shelf, book or chapter folder.
- Book folder names must be unique across shelves.

The "Wiki Guide" book inside the wiki explains this in more detail.

## Settings

`wiki.json` holds the site name and footer text. Colours and layout are in `theme/style.css`.

## Static export

```bash
python wiki.py build
```

Writes a static copy to `site/` that any web server can host. If it will live in a
sub-folder (for example `https://example.org/wiki`), set `"base_url": "/wiki"` in `wiki.json` first.
