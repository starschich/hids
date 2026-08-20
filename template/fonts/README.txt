American Terawatt brand typography — font files
===============================================

The templates pick up Untitled Sans automatically when BOTH of these
are true:

  1. the document is compiled with  lualatex  or  xelatex
     (pdflatex cannot load .otf/.ttf files at all), and
  2. the files below are present in this folder.

Otherwise every template silently falls back to Helvetica, which is
what they used before, so nothing breaks. See ../atfonts.sty.

Files to place here
-------------------
    UntitledSans-Light.otf      (or .ttf)
    UntitledSans-Regular.otf
    UntitledSans-Medium.otf
    UntitledSans-Bold.otf

.otf is preferred; .ttf is accepted. The names must match exactly --
atfonts.sty looks for "UntitledSans-Regular" and derives the rest.

Italic files are optional but recommended:

    UntitledSans-RegularItalic.otf

The document does use italics (\emph / \textit). Without an italic
file, atfonts.sty falls back to AutoFakeSlant, which shears the
upright letterforms. That is a stand-in, not a substitute -- a real
italic should be dropped in when available. If you add one, set
ItalicFont = *-RegularItalic in atfonts.sty.

Why the trial files cannot be used
----------------------------------
The "americanterawattuntitledsans.zip" trial set is NOT usable for a
real document, for two independent reasons:

  1. Licence. They are Klim *test* fonts -- internal family name
     "Test Untitled Sans", licence https://klim.co.nz/licences/test-fonts/
     -- which covers evaluation and mockups, not a published document
     issued to suppliers.

  2. Character set. They are subsetted to 67 characters:
     space , - . 0-9 A-Z a-z  and nothing else.

     This document needs 27 more characters that the trial files do
     not contain, over ~160 occurrences:

        : ( ) / + = % ; < > [ ] _ ° ± · ϕ – — ’ “ ” • − ∼ ≤ ≥

     Compiling with them drops every caption colon ("Table 2 AC
     voltage"), every parenthesis ("207 0.9 p.u."), the apostrophe in
     "AMERICA'S PRIVATE INDUSTRIAL POWER GRID", and the ± in the
     voltage tables.

Retail (licensed, full-character-set) files are needed before the brand
face can actually set this document. Until then, leave this folder
empty -- Helvetica is used and the output is unchanged.
