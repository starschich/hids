# LaTeX Information

Reference notes and how-tos collected while building the American Terawatt
LaTeX documents (the Beamer presentation and the `atreport`-based reports).
All snippets assume the shared template (`atreport` / `attemplate`), which
already loads `graphicx`, `booktabs`, `array`, `tabularx`, `enumitem`,
`amsmath`, `amssymb`, `makecell`, `caption`, `titlesec`, `fancyhdr` and
`pgfplots`.

---

## 1. Lists

**Bulleted list** — `itemize`. **Numbered list** — `enumerate`:

```latex
\begin{enumerate}
  \item First point
  \item Second point
\end{enumerate}
```

Renders `1.`, `2.`, `3.`; nesting deepens automatically (1 → a → i → A).

- **Change the number format** (via `enumitem`): `\begin{enumerate}[label=\arabic*)]`
  → `1)`; `[label=(\alph*)]` → `(a)`; `[label=\roman*.]` → `i.`.
- **Start at a different number:** `\begin{enumerate}[start=3]`.
- **Tune spacing:** `\begin{itemize}\setlength{\itemsep}{0.3em}`.
- **One-off custom label** in any list: `\item[(i)] ...`.
- **Sub-items:** just open a nested `itemize`/`enumerate` inside an `\item`.

---

## 2. Tables

**Column types** (in the `{...}` preamble): `l` `c` `r` (no wrap), `p{3cm}`
(fixed width, wraps, top-aligned), and `X` (auto-width, wraps) in a
`tabularx{\linewidth}{...}`.

**`@{}` expressions** replace the inter-column space at that position:
`@{}` at the edges removes the default outer padding (`\tabcolsep`) so the table
aligns flush with the margin; `@{\hspace{1cm}}` sets a custom gap between columns.

```latex
\begin{tabularx}{\linewidth}{@{}l X r@{}} ... \end{tabularx}
```

**Booktabs rules:** `\toprule`, `\midrule`, `\bottomrule` (nicer than `\hline`).
**Row height:** `\renewcommand{\arraystretch}{1.3}`.

**Line break inside a cell:**
- In a `p{}`/`X` cell use `\newline` (not `\\`, which ends the row).
- In `l`/`c`/`r` cells use `\makecell{line1\\ line2}` (package `makecell`).

**Centered header over left-aligned rows:** the column type sets the default, so
override just the header cell with `\multicolumn`:

```latex
\multicolumn{1}{c}{\textbf{Heading}} & ...
```

**Label a table** (so it can be `\ref`-enced): wrap it in a `table` float with a
`\caption` and `\label`:

```latex
\begin{table}[htbp]
  \renewcommand{\arraystretch}{1.3}
  \begin{tabularx}{\linewidth}{@{}l X r@{}}
    \toprule ... \bottomrule
  \end{tabularx}
  \caption{My table.}
  \label{tab:my-table}
\end{table}
```

Reference it with `Table~\ref{tab:my-table}`.

---

## 3. Figures

```latex
\begin{figure}[htbp]
  \centering
  \includegraphics[width=\linewidth]{fig/diagram.pdf}
  \caption{My figure.}
  \label{fig:my-figure}
\end{figure}
```

- **Fit an over-large image to the page:** cap both dimensions and keep the
  aspect ratio:
  `\includegraphics[width=\linewidth,height=0.8\textheight,keepaspectratio]{...}`.
- **Reference:** `Figure~\ref{fig:my-figure}`.
- **"Border" around a figure** is almost never LaTeX — it is usually the
  background `<rect>` inside an SVG (delete it or set `fill="none"`), a drawn
  rectangle (`stroke="none"`), or a stray `\fbox{...}`.

---

## 4. Spacing

- **Space before an environment** (e.g. a `columns`/`table`): end the paragraph
  with a blank line, then `\vspace{1em}` — `\\` alone is unreliable there.
- **Horizontal space:** `\quad` (1em), `\qquad` (2em), `\hspace{1cm}`
  (`\hspace*{}` also works at the start of a line); thin space `\,`,
  non-breaking `~`.
- **Tab stops** (aligned text without a table): the `tabbing` environment with
  `\=` (set stop), `\>` (jump), `\\` (end line) — but a `tabular` is usually
  better.
- **`em` unit:** font-relative — `1em` equals the current font size (≈11pt in
  11pt body, larger in a big title). Use it so spacing scales with the text;
  use `pt` when you want a fixed size.

---

## 5. Alignment and centering

- **Center display math:** `\[ I = \frac{P}{\sqrt{3}\,V_{LL}} \]` (centres on the
  text width). Inline `$...$` after `\\` will not center.
- **`\centering` is a switch**, not a one-shot: it affects every paragraph until
  the group/environment ends. To center a single block, either scope it
  `{\centering ... \par}` (note the `\par` — without it the group can close
  before the paragraph ends and centering is lost), or use a `center`
  environment.
- **Move text back to the left after `\centering`:** switch alignment with
  `\raggedright`, or force one flush-left line with `\leftline{...}`.

---

## 6. Sectioning and template behaviour

- **Every section on a new page** (report template): titlesec hook
  `\newcommand{\sectionbreak}{\clearpage}` (already set in `atreport`).
- **Beamer frame-title accent rule spacing:** adjust the `\vspace{...}` between
  the title text and the amber `\rule` in the `\setbeamertemplate{frametitle}`
  block of the theme.
- **Bullet indent / slide text margin (Beamer):** the marker-to-text and
  edge-to-text distances are `\setlength{\leftmargini}{1.4em}` and
  `\setbeamersize{text margin left=0.9cm, text margin right=0.9cm}`.

---

## 7. Images and conversion tools

LaTeX (pdf/xe/lualatex) **cannot include EMF** and only reads PDF/PNG/JPG (EPS
via `epstopdf`). Convert first:

- **EMF/SVG → PDF:** Inkscape (`inkscape drawing.emf --export-type=pdf`),
  LibreOffice headless, or `cairosvg file.svg -o file.pdf` (SVG only).
- **Include SVG directly:** the `svg` package (`\includesvg`) — needs Inkscape
  and `pdflatex -shell-escape`. Embedding a pre-converted PDF is more portable.
- **Crop whitespace from a PDF:** `pdfcrop file.pdf`, or set the MediaBox to the
  Ghostscript bounding box (`gs -sDEVICE=bbox`) with `pypdf`/`pikepdf` (robust),
  e.g. `page.mediabox.lower_left = (x0,y0)` etc.
- **Install Inkscape (macOS):** `brew install inkscape` (puts `inkscape` on the
  PATH; the `.dmg` build hides it inside the app bundle).

---

## 8. Handy reminders

- Run `pdflatex` **twice** for the table of contents, cross-references and
  page numbers to settle.
- A stale/corrupt `*.aux` can abort a build with
  `Undefined control sequence … \@wr…` — delete the `.aux` and recompile.
- `\text{...}` in math needs `amsmath`; symbols like `\lesssim` need `amssymb`
  (both loaded by the template).
