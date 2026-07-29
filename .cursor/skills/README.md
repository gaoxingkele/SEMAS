# Project Agent Skills

Project-scoped skills for Cursor (and, via junction, cross-agent hosts).

| Skill | Path | Upstream |
|-------|------|----------|
| `book-to-skill` | `.cursor/skills/book-to-skill/` | [virgiliojr94/book-to-skill](https://github.com/virgiliojr94/book-to-skill) |

Cross-agent discovery path (Windows junction to the same tree):

- `.agents/skills/book-to-skill` → `.cursor/skills/book-to-skill`

## book-to-skill

Turn a PDF / EPUB / DOCX / Markdown / HTML book into a structured agent skill
(frameworks, principles, techniques — not a summary dump).

```bash
# From an agent session that loads this skill:
# /book-to-skill path/to/book.pdf

# Or run the extractor CLI directly:
python .cursor/skills/book-to-skill/scripts/extract.py path/to/book.pdf --check
python .cursor/skills/book-to-skill/scripts/extract.py path/to/book.pdf
```

Optional extractors (reproducible via project extra):

```bash
pip install -e ".[book_to_skill]"
# or: python -m pip install pypdf pdfminer.six ebooklib beautifulsoup4 python-docx striprtf
python .cursor/skills/book-to-skill/scripts/extract.py --check
```

Current check status: PDF / EPUB / DOCX / RTF ready. MOBI/AZW needs system
Calibre. Technical PDF tables/formulas optionally need `docling`.

Vendored at commit `92b248fa` (upstream `master`, 2026-07). Re-sync by
re-cloning into this directory and removing the nested `.git`.
