#!/usr/bin/env python3
"""
Build a high-quality, browseable static website for the PRAXIS specification.

Usage:
    uv run build_site.py

Requires (installed automatically by uv):
    - markdown
    - pygments
    - jinja2

Outputs:
    _site/           - Static website ready to serve
"""
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "markdown>=3.5",
#   "pygments>=2.17",
#   "jinja2>=3.1",
# ]
# ///

import shutil
import re
from pathlib import Path
from textwrap import dedent

import markdown
from markdown.extensions.toc import TocExtension
from markdown.extensions.tables import TableExtension
from markdown.extensions.fenced_code import FencedCodeExtension
from markdown.extensions.codehilite import CodeHiliteExtension
from pygments.formatters import HtmlFormatter
from jinja2 import Template


# ── Configuration ─────────────────────────────────────────────────────────────

ROOT = Path(__file__).parent
SPEC_DIR = ROOT / "spec"
PAPER_DIR = ROOT / "paper"
SITE_DIR = ROOT / "_site"

SPEC_FILES = [
    ("01-introduction.md", "Introduction", "1"),
    ("02-notation.md", "Notation & Conventions", "2"),
    ("03-abstract-syntax.md", "Abstract Syntax", "3"),
    ("04-type-system.md", "Type System", "4"),
    ("05-operational-semantics.md", "Operational Semantics", "5"),
    ("06-petri-net-semantics.md", "Petri Net Semantics", "6"),
    ("07-queueing-semantics.md", "Queueing Semantics", "7"),
    ("08-well-formedness.md", "Well-Formedness", "8"),
    ("09-standard-library.md", "Standard Library", "9"),
    ("10-examples.md", "Examples", "10"),
    ("appendix-a-proofs.md", "Appendix A: Proofs", "A"),
    ("appendix-b-equivalences.md", "Appendix B: Equivalences", "B"),
]


# ── Templates ─────────────────────────────────────────────────────────────────

BASE_TEMPLATE = Template(dedent("""\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{{ title }} — PRAXIS Specification</title>
  <style>
    :root {
      --bg: #ffffff;
      --fg: #1a1a2e;
      --accent: #0f3460;
      --accent-light: #e8eef6;
      --border: #d0d7de;
      --code-bg: #f6f8fa;
      --nav-bg: #f0f3f6;
      --nav-hover: #d8e0e8;
      --link: #0969da;
      --sidebar-w: 280px;
      --max-content: 860px;
    }
    @media (prefers-color-scheme: dark) {
      :root {
        --bg: #0d1117;
        --fg: #e6edf3;
        --accent: #58a6ff;
        --accent-light: #161b22;
        --border: #30363d;
        --code-bg: #161b22;
        --nav-bg: #161b22;
        --nav-hover: #21262d;
        --link: #58a6ff;
      }
    }
    *, *::before, *::after { box-sizing: border-box; }
    html { font-size: 16px; scroll-behavior: smooth; }
    body {
      margin: 0; padding: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
      color: var(--fg); background: var(--bg);
      line-height: 1.6;
    }
    /* ── Layout ────────────────────── */
    .layout { display: flex; min-height: 100vh; }
    .sidebar {
      width: var(--sidebar-w); flex-shrink: 0;
      background: var(--nav-bg); border-right: 1px solid var(--border);
      position: sticky; top: 0; height: 100vh; overflow-y: auto;
      padding: 1.5rem 0;
    }
    .sidebar-header {
      padding: 0 1.25rem 1rem;
      border-bottom: 1px solid var(--border);
      margin-bottom: 0.75rem;
    }
    .sidebar-header h1 {
      margin: 0; font-size: 1.25rem; color: var(--accent);
      font-variant: small-caps; letter-spacing: 0.05em;
    }
    .sidebar-header .version {
      font-size: 0.75rem; color: var(--fg); opacity: 0.6;
    }
    .sidebar nav a {
      display: block;
      padding: 0.35rem 1.25rem;
      color: var(--fg); text-decoration: none;
      font-size: 0.875rem;
      border-left: 3px solid transparent;
      transition: background 0.15s, border-color 0.15s;
    }
    .sidebar nav a:hover { background: var(--nav-hover); }
    .sidebar nav a.active {
      background: var(--accent-light);
      border-left-color: var(--accent);
      font-weight: 600;
    }
    .sidebar nav .nav-group {
      font-size: 0.7rem; font-weight: 700; text-transform: uppercase;
      letter-spacing: 0.08em; color: var(--fg); opacity: 0.5;
      padding: 0.75rem 1.25rem 0.25rem; margin: 0;
    }
    .content {
      flex: 1; max-width: var(--max-content);
      padding: 2rem 3rem;
      margin: 0 auto;
    }
    /* ── Typography ────────────────── */
    h1, h2, h3, h4 { color: var(--accent); margin-top: 2rem; }
    h1 { font-size: 1.75rem; border-bottom: 2px solid var(--border); padding-bottom: 0.5rem; }
    h2 { font-size: 1.4rem; border-bottom: 1px solid var(--border); padding-bottom: 0.3rem; }
    h3 { font-size: 1.15rem; }
    h4 { font-size: 1rem; }
    a { color: var(--link); }
    p { margin: 0.75rem 0; }
    /* ── Code ──────────────────────── */
    code {
      background: var(--code-bg); padding: 0.15em 0.35em;
      border-radius: 3px; font-size: 0.875em;
      font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
    }
    pre {
      background: var(--code-bg); border: 1px solid var(--border);
      border-radius: 6px; padding: 1rem 1.25rem;
      overflow-x: auto; line-height: 1.45;
      font-size: 0.85rem;
    }
    pre code {
      background: none; padding: 0; border-radius: 0;
      font-size: inherit;
    }
    /* ── Tables ────────────────────── */
    table {
      border-collapse: collapse; width: 100%;
      margin: 1rem 0; font-size: 0.9rem;
    }
    th, td {
      border: 1px solid var(--border);
      padding: 0.5rem 0.75rem; text-align: left;
    }
    th { background: var(--code-bg); font-weight: 600; }
    tr:nth-child(even) { background: var(--accent-light); }
    /* ── Blockquote ────────────────── */
    blockquote {
      border-left: 4px solid var(--accent);
      margin: 1rem 0; padding: 0.5rem 1rem;
      background: var(--accent-light);
    }
    /* ── Navigation links ──────────── */
    .page-nav {
      display: flex; justify-content: space-between;
      margin-top: 3rem; padding-top: 1.5rem;
      border-top: 1px solid var(--border);
      font-size: 0.9rem;
    }
    .page-nav a {
      padding: 0.5rem 1rem; border-radius: 6px;
      background: var(--code-bg); text-decoration: none;
      border: 1px solid var(--border);
      transition: background 0.15s;
    }
    .page-nav a:hover { background: var(--nav-hover); }
    /* ── Footer ────────────────────── */
    .footer {
      margin-top: 3rem; padding: 1.5rem 0;
      border-top: 1px solid var(--border);
      font-size: 0.8rem; opacity: 0.6; text-align: center;
    }
    /* ── Responsive ────────────────── */
    @media (max-width: 900px) {
      .sidebar { display: none; }
      .content { padding: 1.5rem; max-width: 100%; }
    }
    /* ── Pygments ──────────────────── */
    {{ pygments_css }}
  </style>
</head>
<body>
  <div class="layout">
    <aside class="sidebar">
      <div class="sidebar-header">
        <h1>PRAXIS</h1>
        <div class="version">v0.1.0 — Specification</div>
      </div>
      <nav>
        <a href="index.html" {{ 'class="active"' if active == 'index' else '' }}>Overview</a>
        <a href="whitepaper.html" {{ 'class="active"' if active == 'whitepaper' else '' }}>White Paper</a>
        <p class="nav-group">Part I: Foundations</p>
        {% for fname, label, num in files[:3] %}
        <a href="{{ fname.replace('.md', '.html') }}" {{ 'class="active"' if active == fname else '' }}>{{ num }}. {{ label }}</a>
        {% endfor %}
        <p class="nav-group">Part II: Semantics</p>
        {% for fname, label, num in files[3:7] %}
        <a href="{{ fname.replace('.md', '.html') }}" {{ 'class="active"' if active == fname else '' }}>{{ num }}. {{ label }}</a>
        {% endfor %}
        <p class="nav-group">Part III: Verification & Library</p>
        {% for fname, label, num in files[7:10] %}
        <a href="{{ fname.replace('.md', '.html') }}" {{ 'class="active"' if active == fname else '' }}>{{ num }}. {{ label }}</a>
        {% endfor %}
        <p class="nav-group">Appendices</p>
        {% for fname, label, num in files[10:] %}
        <a href="{{ fname.replace('.md', '.html') }}" {{ 'class="active"' if active == fname else '' }}>{{ num }}. {{ label }}</a>
        {% endfor %}
      </nav>
    </aside>
    <main class="content">
      {{ content }}
      {% if prev or next %}
      <div class="page-nav">
        {% if prev %}<a href="{{ prev }}">&larr; Previous</a>{% else %}<span></span>{% endif %}
        {% if next %}<a href="{{ next }}">Next &rarr;</a>{% else %}<span></span>{% endif %}
      </div>
      {% endif %}
      <div class="footer">
        PRAXIS Specification v0.1.0 &mdash; Process Algebra for eXtensible Industrial Systems
      </div>
    </main>
  </div>
</body>
</html>
"""))


INDEX_CONTENT = dedent("""\
# PRAXIS: Process Algebra for eXtensible Industrial Systems

**Version 0.1.0** — Draft Specification

---

## What is PRAXIS?

PRAXIS is a formal specification language for describing production systems in which
workstations are LLM-based agents, deterministic computations, or human task queues,
and jobs are software artifacts flowing through a queueing network.

Every PRAXIS program has two formal interpretations:

- **Control-flow** via Coloured Generalized Stochastic Petri Nets (CGSPNs)
- **Performance** via queueing network extraction (Jackson, BCMP, VUT)

## Five Primitive Declarations

| Declaration | ORIE Concept | Petri Net | Queueing |
|-------------|-------------|-----------|----------|
| `type` | Job/work item type | Token color set | Job class |
| `channel` | Queue/buffer | Place | Queue |
| `station` | Workstation/server | Transition subnet | Service center |
| `resource` | Shared finite resource | Resource place | — |
| `arrival` | Arrival process | Source transition | External arrival |

## Specification Structure

### Part I: Foundations
1. [Introduction](01-introduction.html) — Motivation and design philosophy
2. [Notation & Conventions](02-notation.html) — Meta-variables and judgment forms
3. [Abstract Syntax](03-abstract-syntax.html) — Complete EBNF grammar (~540 lines)

### Part II: Semantics
4. [Type System](04-type-system.html) — Kinds, types, subtyping, typing judgments
5. [Operational Semantics](05-operational-semantics.html) — LTS, structural congruence, reduction rules
6. [Petri Net Semantics](06-petri-net-semantics.html) — Translation to CGSPNs
7. [Queueing Semantics](07-queueing-semantics.html) — Network extraction and VUT equation

### Part III: Verification & Library
8. [Well-Formedness](08-well-formedness.html) — Eight well-formedness conditions
9. [Standard Library](09-standard-library.html) — Distributions, patterns, functions
10. [Examples](10-examples.html) — CI/CD pipeline, incident response, Kanban

### Appendices
- [Appendix A: Proof Sketches](appendix-a-proofs.html)
- [Appendix B: Equivalences & Algebraic Laws](appendix-b-equivalences.html)

## White Paper

The [PRAXIS white paper](whitepaper.html) provides a concise academic introduction
with full references to the foundational literature.

## Quick Example

```praxis
type PullRequest = { id: Int, author: String, status: PRStatus }

channel pr_queue    : Chan<PullRequest>
channel review_queue: Chan<BuildResult>

station CodeReview : review_queue -> test_queue {
  servers: 3
  discipline: fifo
  service_time: LogNormal(log(45m), 0.8)
  yield: Bernoulli(0.70)
  rework: { probability: 0.30, target: rework_queue }
  human {
    role: "senior_engineer"
    sla: 4h
    service_time: LogNormal(log(45m), 0.8)
  }
}

arrival PRArrivals : {
  channel: pr_queue
  distribution: Exponential(10/d)
  job: { id: 0, author: "dev", status: Pending }
}

assert throughput(Pipeline) >= 9.5/d
assert cycle_time(Pipeline).p95 <= 2d
assert bottleneck(Pipeline) == CodeReview
assert deadlock_free(Pipeline)
```
""")


WHITEPAPER_PAGE = dedent("""\
# PRAXIS White Paper

The PRAXIS white paper provides a concise academic introduction to the language,
covering its formal foundations, design decisions, and relationship to existing work
in process algebra, Petri nets, and queueing theory.

## Download

- [Download PDF](whitepaper.pdf) (9 pages)

## Abstract

We introduce PRAXIS (Process Algebra for eXtensible Industrial Systems), a formal
specification language for describing production systems in which workstations are
LLM-based agents, deterministic computations, or human task queues, and jobs are
software artifacts flowing through a queueing network. PRAXIS provides a unified
formal model: every program has both a control-flow interpretation via Coloured
Generalized Stochastic Petri Nets and a performance interpretation via queueing
network extraction. The language inherits compositional reasoning from CSP and the
pi-calculus, while its performance semantics draws on Jackson networks, the BCMP
theorem, and the VUT equation from Factory Physics.

## Contents

1. Introduction and Design Principles
2. Background and Foundations (Process Algebra, Petri Nets, Queueing Theory, Factory Physics)
3. Abstract Syntax (Five Primitives, Process Operators, Station Types, Distributions)
4. Type System (Kinds, Dimensional Types, Resource Environments)
5. Operational Semantics (Plotkin-style SOS, Stochastic Extensions)
6. Petri Net Semantics (CGSPN Translation, Behavioral Equivalence)
7. Queueing Semantics (Jackson/BCMP/VUT, Performance Assertions)
8. Well-Formedness Conditions (8 conditions bridging type safety and performance)
9. Worked Examples (CI/CD, Incident Response, Kanban)
10. Related Work and Conclusion

## References

The paper cites foundational works including Hoare (CSP), Milner (pi-calculus),
Hopp & Spearman (Factory Physics), Jackson (queueing networks), Baskett et al. (BCMP theorem),
Little (L = lambda W), Murata (Petri nets), Plotkin (SOS), and others.
""")


# ── Build Logic ───────────────────────────────────────────────────────────────

def build():
    # Clean and create output directory
    if SITE_DIR.exists():
        shutil.rmtree(SITE_DIR)
    SITE_DIR.mkdir(parents=True)

    # Pygments CSS
    formatter = HtmlFormatter(style="default")
    pygments_css = formatter.get_style_defs(".codehilite")

    # Markdown converter
    md = markdown.Markdown(
        extensions=[
            TocExtension(permalink=True, toc_depth=3),
            TableExtension(),
            FencedCodeExtension(),
            CodeHiliteExtension(guess_lang=False, css_class="codehilite"),
            "md_in_html",
        ],
        output_format="html",
    )

    def render_md(text: str) -> str:
        md.reset()
        return md.convert(text)

    def render_page(
        content_html: str,
        title: str,
        active: str,
        prev_url: str | None = None,
        next_url: str | None = None,
    ) -> str:
        return BASE_TEMPLATE.render(
            title=title,
            content=content_html,
            active=active,
            files=SPEC_FILES,
            prev=prev_url,
            next=next_url,
            pygments_css=pygments_css,
        )

    # ── Build index page ──
    index_html = render_page(
        render_md(INDEX_CONTENT),
        "Home",
        "index",
        next_url="01-introduction.html",
    )
    (SITE_DIR / "index.html").write_text(index_html)
    print("  index.html")

    # ── Build white paper page ──
    wp_html = render_page(
        render_md(WHITEPAPER_PAGE),
        "White Paper",
        "whitepaper",
    )
    (SITE_DIR / "whitepaper.html").write_text(wp_html)
    print("  whitepaper.html")

    # Copy white paper PDF if it exists
    wp_pdf = PAPER_DIR / "whitepaper.pdf"
    if wp_pdf.exists():
        shutil.copy2(wp_pdf, SITE_DIR / "whitepaper.pdf")
        print("  whitepaper.pdf (copied)")

    # ── Build spec pages ──
    for i, (fname, label, num) in enumerate(SPEC_FILES):
        src = SPEC_DIR / fname
        if not src.exists():
            print(f"  SKIP {fname} (not found)")
            continue

        text = src.read_text()

        # Fix internal markdown links to point to .html
        text = re.sub(
            r"\[([^\]]+)\]\((\d{2}-[^)]+)\.md\)",
            r"[\1](\2.html)",
            text,
        )
        text = re.sub(
            r"\[([^\]]+)\]\((appendix-[^)]+)\.md\)",
            r"[\1](\2.html)",
            text,
        )

        content_html = render_md(text)
        out_name = fname.replace(".md", ".html")

        prev_url = None
        next_url = None
        if i > 0:
            prev_url = SPEC_FILES[i - 1][0].replace(".md", ".html")
        else:
            prev_url = "index.html"
        if i < len(SPEC_FILES) - 1:
            next_url = SPEC_FILES[i + 1][0].replace(".md", ".html")

        page_html = render_page(content_html, f"Ch. {num}: {label}", fname, prev_url, next_url)
        (SITE_DIR / out_name).write_text(page_html)
        print(f"  {out_name}")

    print(f"\nSite built: {SITE_DIR}/")
    print(f"Serve with: python -m http.server -d {SITE_DIR} 8000")


if __name__ == "__main__":
    build()
