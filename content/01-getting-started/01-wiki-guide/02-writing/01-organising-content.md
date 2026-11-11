# Organising content

## Folder layout

```text
content/
  01-getting-started/          <- shelf
    _meta.json
    01-wiki-guide/             <- book
      _meta.json
      01-welcome.md            <- page
      02-writing/              <- chapter
        01-organising-content.md
```

## Ordering

Items are sorted by file name. Prefix a name with a number (`01-`, `02-`, ...) to control
the order; the prefix is removed from titles and web addresses.

## Titles and descriptions

- A **page** takes its title from its first `# Heading`. Without one, the file name is used.
- A **shelf, book or chapter** takes its title from the folder name, or from an optional
  `_meta.json` file inside the folder:

```json
{
  "title": "Wiki Guide",
  "description": "Shown on cards and at the top of the book.",
  "cover": "cover.jpg"
}
```

`cover` is an image file in the same folder. Without one, a coloured cover is generated.

## Links and images

Link to other pages and images with normal relative paths, exactly as they are on disk:

```markdown
[Welcome page](../01-welcome.md)
![Wiring diagram](wiring.png)
```

!!! note
    Files and folders whose name starts with `_` or `.` are ignored.
