# HIDS — HVDC Information Documentation System

Welcome to **HIDS**, the **HVDC Information Documentation System**.

## What this is

HIDS is a new, shared structure for collecting, organizing, and maintaining the
company's technical information on HVDC systems. It replaces scattered, ad-hoc
files with a single, consistent home so that specifications, reference
documentation, and presentation material live together and stay in sync.

The goals are simple:

- **One source of truth** — a predictable place for every kind of HVDC information.
- **Reusable content** — figures, definitions, and modules that can be shared
  across documents rather than duplicated.
- **Easy contribution** — a clear folder layout so anyone can find where content
  belongs and add to it.

## Structure

The repository is organized into three top-level areas:

- **`specification/`** — formal specifications and requirements: the defining
  parameters, ratings, and design bases for our HVDC systems.
- **`documentation/`** — reference and background documentation: standards,
  methodology notes, and supporting material.
- **`presentation/`** — the LaTeX (Beamer) presentation deck built on the
  American Terawatt template, with per-topic chapters and their figures. This is
  the training / communication layer that draws on the specification and
  documentation content.

## Getting started

Browse to the area that matches what you need. To build the presentation, open
`presentation/` and compile `presentation.tex` (run `pdflatex` twice for
navigation and references). Each chapter lives in its own folder under
`presentation/chapters/`, with its figures in a local `fig/` (or `figures/`)
subfolder.

## Contributing

Add new content in the area it belongs to, keep figures alongside the document
that uses them, and follow the existing folder conventions so the collection
stays consistent and easy to navigate.
