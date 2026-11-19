# Markdown cheat sheet

## Sections

The `# Heading` at the top is the page title. Split the page into sections with `##`, and
into subsections with `###` and `####`. Sections are numbered automatically (1, 1.1,
1.1.1 ...) on the page and in *On this page*, so do not type the numbers yourself:

```markdown
## Power System
### Battery
### Voltage regulators
```

shows up as *1 Power System*, *1.1 Battery* and *1.2 Voltage regulators*.

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

## Images

In the page editor, click **Insert image**, or paste or drop an image into the text. The
file is stored next to the page in an `_images` folder and a line like this is added:

```markdown
![Wiring diagram](_images/wiring-diagram.png){: .center }
```

Add `{ width=300 }` right after the closing bracket to set a size.

To centre an image, add `{: .center }` right after it. A caption is centred the same way,
by putting `{: .center }` on the line right after it. Both can be combined with a size:

```markdown
![Wiring diagram](_images/wiring-diagram.png){: .center width=300 }

*Figure 1: Wiring diagram of the robot.*
{: .center }
```

Images added with **Insert image** are centred by default.

## Equations

Write LaTeX between dollar signs. Inline: $E = mc^2$ and $v_{orb} = \sqrt{\mu / r}$.

On its own line, with double dollar signs:

$$
\Delta v = I_{sp} \, g_0 \ln\!\left(\frac{m_0}{m_f}\right)
$$

```markdown
Inline: $E = mc^2$

$$
\Delta v = I_{sp} \, g_0 \ln\!\left(\frac{m_0}{m_f}\right)
$$
```

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
