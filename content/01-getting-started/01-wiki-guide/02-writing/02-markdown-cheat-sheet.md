# Markdown cheat sheet

## Text

Plain paragraphs, **bold**, *italic*, `inline code` and [links](https://www.markdownguide.org/).

> Block quotes are good for remarks and citations.

## Lists

1. Numbered step
2. Another step
    - A nested bullet
    - Another one

## Code

```python
def checksum(data: bytes) -> int:
    return sum(data) & 0xFF
```

## Tables

| Parameter | Value | Unit |
|-----------|------:|------|
| Voltage   |   3.3 | V    |
| Current   |   120 | mA   |

## Call-outs

!!! note
    Useful background information.

!!! warning
    Something the reader must not miss.

!!! danger
    Risk of damage or injury.

## Definition lists

Term
:   Its explanation.
