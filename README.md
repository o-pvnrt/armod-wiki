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
