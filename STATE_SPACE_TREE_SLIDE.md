# Slide-ready State Space Tree (Compact)

Use this **compact** diagram on slides (it shows the *shape* of the game tree, not the full tree).

```mermaid
flowchart LR
  S0((S_t)) --> E{Eleven action}

  E --> WAI[wait]
  E --> MOV[move]
  E --> SHO[shoot]

  WAI --> D[Demogorgons]
  MOV --> D
  SHO --> D

  D --> T{terminal?}
  T -->|win| WIN((WIN))
  T -->|lose| LOSE((LOSE))
  T -->|no| S1((S_{t+1}))
```

## Export (for PowerPoint / Google Slides)

- Fast option: paste the Mermaid code into https://mermaid.live and export as **SVG** (best quality) or **PNG**.
- VS Code option: open this file and use Markdown Preview (Ctrl+Shift+V). If your Mermaid extension supports export, export as SVG/PNG.
