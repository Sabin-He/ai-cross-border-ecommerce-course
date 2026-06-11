#!/usr/bin/env python3
"""tools/build_reading_packages.py

重建两个离线 HTML 阅读包（原构建脚本在交付清理时丢失，本脚本按原产物逆向重建）：

  1. 书籍阅读版   -> AI跨境电商效能提升实战课_书籍阅读版.html + book_reading_package/index.html
     按课程顺序阅读：课程导读 + 21 章 + 21 份实操手册 + Skills 教程 + 附录 A/B/C + 库使用说明。
  2. 资料库阅读器 -> AI跨境电商效能提升实战课_资料库阅读器.html + html_reading_package/index.html
     收录资料库全部 Markdown 文件，带搜索和目录。

特性（与原产物对齐）：
  - Mermaid 流程图在构建时转成内嵌 SVG（自研简易渲染器，仅支持本库使用的
    flowchart/graph TD|LR + A[标签] --> B[标签] 语法），不依赖外部 CDN。
  - 本地图片（png/svg）转成 base64 data URI 内嵌。
  - 单文件、零外部依赖，可直接发给别人离线打开。
  - 指向库内 .md 的链接：目标被收录时改写为页内锚点，否则退化为纯文本（原构建保留
    相对路径死链，此处为修复）。

运行：python tools/build_reading_packages.py
依赖：仅 Python 3.9+ 标准库。
"""

from __future__ import annotations

import base64
import html
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

SKIP_DIRS = {
    ".git", ".history", ".qoder", ".playwright-mcp",
    "output", "book_reading_package", "html_reading_package",
    "__pycache__", "tools",
}

MIME = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".svg": "image/svg+xml",
    ".webp": "image/webp",
}

# ---------------------------------------------------------------------------
# Mermaid -> SVG（仅支持本库用到的子集：flowchart/graph + TD/LR + A[label] --> B）
# ---------------------------------------------------------------------------

_NODE_RE = re.compile(r"([A-Za-z0-9_]+)(?:\[([^\]]*)\])?")


def _parse_mermaid(code: str):
    direction = "TD"
    nodes: dict[str, str] = {}
    order: list[str] = []
    edges: list[tuple[str, str]] = []

    def touch(token: str) -> str | None:
        m = _NODE_RE.fullmatch(token.strip())
        if not m:
            return None
        nid, label = m.group(1), m.group(2)
        if nid not in nodes:
            nodes[nid] = label if label is not None else nid
            order.append(nid)
        elif label:
            nodes[nid] = label
        return nid

    for raw in code.splitlines():
        line = raw.strip()
        if not line:
            continue
        m = re.match(r"^(?:flowchart|graph)\s+(TD|TB|LR)", line, re.I)
        if m:
            direction = "LR" if m.group(1).upper() == "LR" else "TD"
            continue
        if "-->" in line:
            parts = [p.strip() for p in line.split("-->")]
            prev = None
            for part in parts:
                nid = touch(part)
                if prev and nid:
                    edges.append((prev, nid))
                prev = nid
        else:
            touch(line)
    return direction, nodes, order, edges


def _wrap_label(label: str, max_units: int = 20) -> list[str]:
    lines, cur, units = [], "", 0
    for ch in label:
        w = 2 if ord(ch) > 0x2E7F else 1
        if units + w > max_units and cur:
            lines.append(cur)
            cur, units = "", 0
        cur += ch
        units += w
    if cur:
        lines.append(cur)
    return lines or [""]


def render_mermaid_svg(code: str) -> str:
    direction, nodes, order, edges = _parse_mermaid(code)
    if not order:
        return ""

    # 分层：从根节点出发的最长路径（带环保护）
    layer = {nid: 0 for nid in order}
    for _ in range(len(order)):
        changed = False
        for s, d in edges:
            if layer[d] < layer[s] + 1 and layer[s] + 1 < len(order) + 1:
                layer[d] = layer[s] + 1
                changed = True
        if not changed:
            break

    layers: dict[int, list[str]] = {}
    for nid in order:
        layers.setdefault(layer[nid], []).append(nid)
    n_layers = max(layers) + 1

    BOX_W, PAD, GAP_MAIN, PITCH = 156, 25, 66, 220
    wrapped = {nid: _wrap_label(nodes[nid]) for nid in order}

    def box_h(nid: str) -> int:
        return 26 + 18 * len(wrapped[nid])

    pos: dict[str, tuple[float, float, float, float]] = {}  # cx, cy_top, w, h

    if direction == "TD":
        row_h = {li: max(box_h(n) for n in row) for li, row in layers.items()}
        max_row = max(len(row) for row in layers.values())
        width = max(772, PAD * 2 + (max_row - 1) * PITCH + BOX_W)
        y = float(PAD)
        for li in range(n_layers):
            row = layers.get(li, [])
            span = (len(row) - 1) * PITCH
            x0 = width / 2 - span / 2
            for j, nid in enumerate(row):
                pos[nid] = (x0 + j * PITCH, y, BOX_W, row_h[li])
            y += row_h[li] + GAP_MAIN
        height = int(y - GAP_MAIN + PAD)
    else:  # LR
        col_w = BOX_W
        col_gap = 92
        v_pitch = 96
        max_col = max(len(col) for col in layers.values())
        height = max(140, PAD * 2 + (max_col - 1) * v_pitch + 80)
        width = int(PAD * 2 + n_layers * col_w + (n_layers - 1) * col_gap)
        width = max(width, 560)
        for li in range(n_layers):
            col = layers.get(li, [])
            span = (len(col) - 1) * v_pitch
            y0 = height / 2 - span / 2
            x = PAD + li * (col_w + col_gap)
            for j, nid in enumerate(col):
                h = box_h(nid)
                pos[nid] = (x + col_w / 2, y0 + j * v_pitch - h / 2, BOX_W, h)

    parts: list[str] = []
    parts.append(
        f'<svg class="diagram-svg" viewBox="0 0 {int(width)} {int(height)}" '
        f'width="100%" height="{int(height)}" role="img" aria-label="课程流程图">'
    )
    parts.append(
        '<defs>\n<marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="3" '
        'orient="auto" markerUnits="strokeWidth"><path d="M0,0 L0,6 L9,3 z" fill="#6b7480"/></marker>\n</defs>'
    )

    for s, d in edges:
        scx, sy, _, sh = pos[s]
        dcx, dy, _, dh = pos[d]
        if direction == "TD":
            x1, y1 = scx, sy + sh
            x2, y2 = dcx, dy
            if y2 <= y1:  # 回环边：从侧面绕
                x1, y1 = scx + BOX_W / 2, sy + sh / 2
                x2, y2 = dcx + BOX_W / 2, dy + dh / 2
        else:
            x1, y1 = scx + BOX_W / 2, sy + sh / 2
            x2, y2 = dcx - BOX_W / 2, dy + dh / 2
            if x2 <= x1:
                x1, y1 = scx, sy + sh
                x2, y2 = dcx, dy + dh
        parts.append(
            f'<line x1="{x1:.0f}" y1="{y1:.0f}" x2="{x2:.0f}" y2="{y2:.0f}" '
            f'stroke="#6b7480" stroke-width="2" marker-end="url(#arrow)"/>'
        )

    for nid in order:
        cx, ty, w, h = pos[nid]
        lines = wrapped[nid]
        parts.append(
            f'<rect x="{cx - w / 2:.0f}" y="{ty:.0f}" width="{w:.0f}" height="{h:.0f}" '
            f'rx="8" fill="#ffffff" stroke="#9aa7b3" stroke-width="1.4"/>'
        )
        text_y = ty + (h - 18 * (len(lines) - 1)) / 2
        tspans = "".join(
            f'<tspan x="{cx:.0f}" dy="{0 if i == 0 else 18}">{html.escape(line)}</tspan>'
            for i, line in enumerate(lines)
        )
        parts.append(
            f'<text x="{cx:.0f}" y="{text_y:.0f}" text-anchor="middle" '
            f'dominant-baseline="middle" class="diagram-text">{tspans}</text>'
        )
    parts.append("</svg>")
    return (
        '<div class="diagram-shell" aria-label="课程图示">' + "\n".join(parts) + "</div>"
    )


# ---------------------------------------------------------------------------
# Markdown 子集渲染器（覆盖本库实际用到的语法）
# ---------------------------------------------------------------------------

class Renderer:
    """把单个 Markdown 文件渲染成 article 内部 HTML。

    link_resolver(href, text) -> 替换后的 HTML 片段或 None（None 表示按默认输出链接）。
    """

    def __init__(self, md_path: Path, anchor_prefix: str, link_resolver=None):
        self.md_path = md_path
        self.anchor_prefix = anchor_prefix
        self.link_resolver = link_resolver
        self.heading_seq = 0
        self.headings: list[tuple[int, str, str]] = []  # level, anchor, text

    # ---------- inline ----------

    def _inline(self, text: str) -> str:
        out: list[str] = []
        pos = 0
        token_re = re.compile(
            r"(?P<code>`[^`]+`)"
            r"|(?P<img>!\[(?P<ialt>[^\]]*)\]\((?P<isrc>[^)\s]+)(?:\s+\"(?P<ititle>[^\"]*)\")?\))"
            r"|(?P<link>\[(?P<ltext>[^\]]+)\]\((?P<lhref>[^)\s]+)(?:\s+\"[^\"]*\")?\))"
            r"|(?P<bold>\*\*(?P<btext>[^*]+)\*\*)"
        )
        for m in token_re.finditer(text):
            out.append(html.escape(text[pos:m.start()]))
            if m.group("code"):
                out.append(f"<code>{html.escape(m.group('code')[1:-1])}</code>")
            elif m.group("img"):
                out.append(self._image(m.group("isrc"), m.group("ialt"), m.group("ititle")))
            elif m.group("link"):
                out.append(self._link(m.group("lhref"), m.group("ltext")))
            elif m.group("bold"):
                out.append(f"<strong>{self._inline(m.group('btext'))}</strong>")
            pos = m.end()
        out.append(html.escape(text[pos:]))
        return "".join(out)

    def _image(self, src: str, alt: str, title: str | None) -> str:
        target = (self.md_path.parent / src).resolve()
        if target.is_file() and target.suffix.lower() in MIME:
            data = base64.b64encode(target.read_bytes()).decode("ascii")
            uri = f"data:{MIME[target.suffix.lower()]};base64,{data}"
            cap = f"<figcaption>{html.escape(title)}</figcaption>" if title else ""
            return (
                f'<figure class="visual-figure"><img src="{uri}" '
                f'alt="{html.escape(alt, quote=True)}">{cap}</figure>'
            )
        return f"<em>[图片缺失：{html.escape(alt or src)}]</em>"

    def _link(self, href: str, text: str) -> str:
        rendered_text = self._inline(text)
        if self.link_resolver:
            replaced = self.link_resolver(href, rendered_text, self.md_path)
            if replaced is not None:
                return replaced
        return f'<a href="{html.escape(href, quote=True)}">{rendered_text}</a>'

    # ---------- block ----------

    def _heading_anchor(self) -> str:
        self.heading_seq += 1
        return f"{self.anchor_prefix}-h{self.heading_seq}"

    def render(self, text: str) -> str:
        return self._blocks(text.splitlines())

    def _blocks(self, lines: list[str]) -> str:
        out: list[str] = []
        i = 0
        n = len(lines)
        while i < n:
            line = lines[i]
            stripped = line.strip()

            if not stripped:
                i += 1
                continue

            # fenced code
            m = re.match(r"^```\s*(\S*)\s*$", stripped)
            if m:
                lang = m.group(1).lower()
                body: list[str] = []
                i += 1
                while i < n and not lines[i].strip().startswith("```"):
                    body.append(lines[i])
                    i += 1
                i += 1  # skip closing fence
                code = "\n".join(body)
                if lang == "mermaid":
                    svg = render_mermaid_svg(code)
                    out.append(svg if svg else f"<pre><code>{html.escape(code)}</code></pre>")
                else:
                    cls = f' class="language-{html.escape(lang)}"' if lang else ""
                    out.append(f"<pre><code{cls}>{html.escape(code)}</code></pre>")
                continue

            # heading
            m = re.match(r"^(#{1,6})\s+(.*)$", stripped)
            if m:
                level = len(m.group(1))
                txt = m.group(2).strip()
                anchor = self._heading_anchor()
                self.headings.append((level, anchor, re.sub(r"\*\*|`", "", txt)))
                out.append(f'<h{level} id="{anchor}">{self._inline(txt)}</h{level}>')
                i += 1
                continue

            # hr
            if re.match(r"^(-{3,}|\*{3,}|_{3,})$", stripped):
                out.append("<hr>")
                i += 1
                continue

            # blockquote（收集连续 > 行，递归解析）
            if stripped.startswith(">"):
                inner: list[str] = []
                while i < n and lines[i].strip().startswith(">"):
                    inner.append(re.sub(r"^\s*>\s?", "", lines[i]))
                    i += 1
                out.append(f"<blockquote>{self._blocks(inner)}</blockquote>")
                continue

            # table
            if stripped.startswith("|") and i + 1 < n and re.match(
                r"^\|?\s*:?-{3,}", lines[i + 1].strip()
            ):
                header = self._split_row(stripped)
                i += 2
                rows: list[list[str]] = []
                while i < n and lines[i].strip().startswith("|"):
                    rows.append(self._split_row(lines[i].strip()))
                    i += 1
                thead = "".join(f"<th>{self._inline(c)}</th>" for c in header)
                body_html = "".join(
                    "<tr>" + "".join(
                        f"<td>{self._inline(c)}</td>"
                        for c in (row + [""] * (len(header) - len(row)))[: len(header)]
                    ) + "</tr>"
                    for row in rows
                )
                out.append(
                    '<div class="table-wrap"><table>'
                    f"<thead><tr>{thead}</tr></thead><tbody>{body_html}</tbody>"
                    "</table></div>"
                )
                continue

            # list（含两级嵌套）
            if re.match(r"^(\s*)([-*+]|\d+[.)])\s+", line):
                block, i = self._collect_list(lines, i)
                out.append(block)
                continue

            # paragraph：聚合到下一个块标记
            para = [stripped]
            i += 1
            while i < n:
                nxt = lines[i].strip()
                if (
                    not nxt
                    or nxt.startswith(("#", ">", "|", "```"))
                    or re.match(r"^(-{3,}|\*{3,})$", nxt)
                    or re.match(r"^([-*+]|\d+[.)])\s+", nxt)
                ):
                    break
                para.append(nxt)
                i += 1
            out.append(f"<p>{self._inline(' '.join(para))}</p>")
        return "\n".join(out)

    @staticmethod
    def _split_row(row: str) -> list[str]:
        row = row.strip().strip("|")
        cells = re.split(r"(?<!\\)\|", row)
        return [c.replace("\\|", "|").strip() for c in cells]

    def _collect_list(self, lines: list[str], i: int) -> tuple[str, int]:
        n = len(lines)
        items: list[tuple[int, str, str]] = []  # indent, marker, text
        while i < n:
            m = re.match(r"^(\s*)([-*+]|\d+[.)])\s+(.*)$", lines[i])
            if not m:
                if lines[i].strip() and re.match(r"^\s{2,}\S", lines[i]) and items:
                    indent, marker, txt = items[-1]
                    items[-1] = (indent, marker, txt + " " + lines[i].strip())
                    i += 1
                    continue
                break
            items.append((len(m.group(1)), m.group(2), m.group(3)))
            i += 1

        def build(idx: int, base_indent: int) -> tuple[str, int]:
            ordered = bool(re.match(r"\d", items[idx][1]))
            tag = "ol" if ordered else "ul"
            start_attr = ""
            if ordered:
                first_num = int(re.match(r"(\d+)", items[idx][1]).group(1))
                if first_num != 1:
                    start_attr = f' start="{first_num}"'
            parts = [f"<{tag}{start_attr}>"]
            k = idx
            while k < len(items):
                ind, _marker, txt = items[k]
                if ind < base_indent:
                    break
                if ind > base_indent:
                    sub, k = build(k, ind)
                    parts[-1] = parts[-1][:-5] + sub + "</li>" if parts[-1].endswith("</li>") else parts[-1] + sub
                    continue
                parts.append(f"<li>{self._inline(txt)}</li>")
                k += 1
            parts.append(f"</{tag}>")
            return "".join(parts), k

        html_block, _ = build(0, items[0][0])
        return html_block, i


# ---------------------------------------------------------------------------
# 文件清单
# ---------------------------------------------------------------------------

def all_markdown_files() -> list[Path]:
    files: list[Path] = []
    for p in sorted(ROOT.rglob("*.md")):
        if any(part in SKIP_DIRS for part in p.relative_to(ROOT).parts):
            continue
        files.append(p)
    readme = ROOT / "README.md"
    files = [f for f in files if f != readme]
    return ([readme] if readme.exists() else []) + files


def first_h1(path: Path) -> str:
    for line in path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^#\s+(.*)$", line.strip())
        if m:
            return re.sub(r"\*\*|`", "", m.group(1)).strip()
    return path.stem


WEEK_NAMES = {
    1: "第 1 周：先认识 AI，学会把问题说清楚",
    2: "第 2 周：把 AI 放进日常工作",
    3: "第 3 周：完成一个小而真实的改进",
}


def book_manifest() -> list[tuple[str, list[tuple[Path, str | None]]]]:
    """返回 [(分组名, [(文件, 自定义id或None)])]，顺序即成书顺序。"""
    g: list[tuple[str, list[tuple[Path, str | None]]]] = []

    intro_files = [
        "00_课程设计说明.md", "01_课程总目录.md", "02_教学方法论_正反馈式训练.md",
        "03_学员画像与适合人群.md", "04_讲师风格指南.md", "05_术语表.md",
        "07_课程阅读与使用指南.md", "08_整体课程设计说明_闭环重构版.md",
        "10_课程通用约定.md",
    ]
    g.append(("课程导读", [(ROOT / "00_课程总纲" / f, None) for f in intro_files]))

    week_dirs = ["01_第1周_AI基础提效周", "02_第2周_AI岗位实战周", "03_第3周_AI落地陪跑周"]
    for w, d in enumerate(week_dirs, 1):
        files = sorted((ROOT / d).glob("Day*.md"))
        g.append((WEEK_NAMES[w], [(f, None) for f in files]))

    manuals = sorted((ROOT / "09_章节实操手册").glob("Day*.md"))
    manual_entries: list[tuple[Path, str | None]] = []
    for f in manuals:
        m = re.match(r"^(Day\d+)", f.name)
        manual_entries.append((f, f"manual-{m.group(1).lower()}" if m else None))
    g.append(("章节实操手册", manual_entries))

    g.append(("AI Agent Skills", [(ROOT / "08_AI_Agent_Skills教程" / "00_AI_Agent_Skills编写入门.md", None)]))

    appendix = [
        ROOT / "11_附录章节" / "00_附录章节说明.md",
        ROOT / "11_附录章节" / "附录A_AI预算与成本意识.md",
        ROOT / "11_附录章节" / "附录B_Agent与工作流.md",
        ROOT / "11_附录章节" / "附录C_跨境电商合规与踩坑.md",
        ROOT / "04_模板库" / "00_模板库使用说明.md",
        ROOT / "05_提示词库" / "00_提示词库使用说明.md",
        ROOT / "06_评分与反馈" / "00_评分反馈使用说明.md",
    ]
    g.append(("附录", [(f, None) for f in appendix]))
    return g


# ---------------------------------------------------------------------------
# 页面模板
# ---------------------------------------------------------------------------

HR_CSS = "hr { border: 0; border-top: 1px solid var(--line); margin: 26px 0; }"

BOOK_CSS = """
    :root {
      --bg: #eef3f6;
      --paper: #ffffff;
      --ink: #1f2933;
      --muted: #657484;
      --line: #d9e1e8;
      --accent: #1f6f78;
      --accent-weak: #e5f4f5;
      --warm: #8a5a2b;
      --code-bg: #101820;
      --code-text: #eef5f8;
    }
    * { box-sizing: border-box; }
    html { scroll-behavior: smooth; }
    body {
      margin: 0;
      color: var(--ink);
      background: var(--bg);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft YaHei", sans-serif;
      line-height: 1.82;
    }
    a { color: var(--accent); text-decoration: none; }
    a:hover { text-decoration: underline; }
    .book-layout {
      display: grid;
      grid-template-columns: 300px minmax(0, 1fr);
      min-height: 100vh;
    }
    .book-sidebar {
      position: sticky;
      top: 0;
      height: 100vh;
      overflow: auto;
      padding: 24px 18px;
      background: #16232d;
      color: #f7fafc;
    }
    .book-title {
      margin: 0 0 8px;
      font-size: 20px;
      line-height: 1.35;
      color: #f7fafc;
    }
    .book-subtitle {
      color: #bed0da;
      font-size: 13px;
      margin-bottom: 18px;
    }
    .book-nav {
      display: grid;
      gap: 3px;
    }
    .book-nav-group {
      margin: 16px 0 5px;
      color: #8dd2d8;
      font-size: 12px;
      font-weight: 700;
      letter-spacing: 0;
    }
    .book-nav-item {
      display: block;
      padding: 7px 8px;
      border-radius: 7px;
      color: #eef6f8;
      font-size: 13px;
      line-height: 1.45;
    }
    .book-nav-item:hover {
      background: rgba(255, 255, 255, 0.09);
      text-decoration: none;
    }
    .book-main {
      padding: 34px 24px 72px;
    }
    .book-cover,
    .book-chapter {
      width: min(920px, 100%);
      margin: 0 auto 28px;
      background: var(--paper);
      border: 1px solid var(--line);
      border-radius: 8px;
      box-shadow: 0 12px 34px rgba(22, 35, 45, 0.08);
    }
    .book-cover {
      min-height: 72vh;
      display: grid;
      align-content: center;
      gap: 18px;
      padding: 64px;
      border-top: 8px solid var(--accent);
    }
    .book-cover h1 {
      margin: 0;
      border: 0;
      padding: 0;
      font-size: 42px;
      line-height: 1.22;
    }
    .book-cover p {
      max-width: 680px;
      margin: 0;
      color: var(--muted);
      font-size: 17px;
    }
    .cover-meta {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 12px;
      color: var(--muted);
      font-size: 14px;
    }
    .cover-pill {
      padding: 6px 10px;
      border-radius: 999px;
      background: var(--accent-weak);
      color: #245d63;
    }
    .book-chapter {
      padding: 44px 54px;
    }
    .chapter-kicker {
      margin-bottom: 14px;
      color: var(--warm);
      font-size: 13px;
      font-weight: 700;
    }
    h1, h2, h3, h4, h5, h6 {
      color: #17212b;
      line-height: 1.35;
      margin: 1.35em 0 0.65em;
      scroll-margin-top: 24px;
    }
    h1 {
      margin-top: 0;
      padding-bottom: 12px;
      border-bottom: 1px solid var(--line);
      font-size: 31px;
    }
    h2 { font-size: 24px; }
    h3 { font-size: 19px; }
    p { margin: 0 0 1em; }
    ul, ol { padding-left: 1.45em; }
    li { margin: 0.22em 0; }
    blockquote {
      margin: 20px 0;
      padding: 13px 16px;
      border-left: 4px solid var(--accent);
      background: var(--accent-weak);
      color: #21484d;
    }
    blockquote p:last-child { margin-bottom: 0; }
    code {
      padding: 2px 5px;
      border-radius: 5px;
      background: #edf2f6;
      font-family: "Cascadia Code", Consolas, monospace;
      font-size: 0.92em;
    }
    pre {
      overflow: auto;
      padding: 16px;
      border-radius: 8px;
      background: var(--code-bg);
      color: var(--code-text);
    }
    pre code {
      padding: 0;
      background: transparent;
      color: inherit;
    }
    .diagram-shell {
      margin: 22px 0;
      padding: 20px;
      overflow-x: auto;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fbfdfe;
    }
    .diagram-svg {
      display: block;
      min-width: 560px;
      margin: 0 auto;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft YaHei", sans-serif;
    }
    .diagram-text {
      fill: #1f2933;
      font-size: 14px;
      font-weight: 600;
    }
    .visual-figure {
      margin: 24px 0;
      padding: 14px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fbfdfe;
    }
    .visual-figure img {
      display: block;
      width: 100%;
      max-width: 100%;
      height: auto;
      border-radius: 6px;
    }
    .visual-figure figcaption {
      margin-top: 10px;
      color: var(--muted);
      font-size: 13px;
      text-align: center;
    }
    .table-wrap {
      overflow-x: auto;
      margin: 20px 0;
      border: 1px solid var(--line);
      border-radius: 8px;
    }
    table {
      width: 100%;
      min-width: 640px;
      border-collapse: collapse;
    }
    th, td {
      padding: 10px 12px;
      border-bottom: 1px solid var(--line);
      text-align: left;
      vertical-align: top;
    }
    th {
      background: #f1f5f8;
      font-weight: 700;
    }
    .mobile-top {
      display: none;
    }
    @media (max-width: 920px) {
      .book-layout { grid-template-columns: 1fr; }
      .book-sidebar {
        position: fixed;
        inset: 0 auto 0 0;
        width: min(88vw, 330px);
        z-index: 20;
        transform: translateX(-105%);
        transition: transform 160ms ease;
      }
      body.nav-open .book-sidebar { transform: translateX(0); }
      .mobile-top {
        position: sticky;
        top: 0;
        z-index: 10;
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 10px 16px;
        background: rgba(238, 243, 246, 0.95);
        border-bottom: 1px solid var(--line);
        backdrop-filter: blur(12px);
      }
      .mobile-top button {
        border: 1px solid var(--line);
        border-radius: 8px;
        background: var(--paper);
        padding: 8px 10px;
      }
      .book-main {
        width: 100%;
        max-width: 100vw;
        overflow-x: hidden;
        padding: 18px 14px 48px;
      }
      .book-cover,
      .book-chapter {
        width: 100%;
        max-width: 100%;
        margin-left: 0;
        margin-right: 0;
      }
      .book-cover { min-height: auto; padding: 36px 26px; }
      .book-cover h1 { font-size: 31px; }
      .book-chapter { padding: 30px 22px; }
      .diagram-shell,
      .table-wrap,
      pre {
        max-width: 100%;
      }
      .diagram-svg {
        min-width: 520px;
      }
      h1 { font-size: 26px; }
    }
    @media print {
      .book-sidebar, .mobile-top { display: none; }
      .book-layout { display: block; }
      .book-main { padding: 0; }
      .book-cover, .book-chapter {
        box-shadow: none;
        border: 0;
        page-break-after: always;
      }
    }
""" + "    " + HR_CSS + "\n"

READER_CSS = """
    :root {
      --bg: #f6f7f9;
      --panel: #ffffff;
      --text: #1f2933;
      --muted: #687383;
      --line: #dfe4ea;
      --accent: #2368a2;
      --accent-weak: #e7f1fa;
      --success: #2f7d5a;
      --code-bg: #101820;
      --code-text: #eef5f8;
      --shadow: 0 10px 30px rgba(31, 41, 51, 0.08);
    }
    * { box-sizing: border-box; }
    html { scroll-behavior: smooth; }
    body {
      margin: 0;
      background: var(--bg);
      color: var(--text);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft YaHei", sans-serif;
      line-height: 1.75;
    }
    a { color: var(--accent); text-decoration: none; }
    a:hover { text-decoration: underline; }
    .layout {
      display: grid;
      grid-template-columns: 320px minmax(0, 1fr);
      min-height: 100vh;
    }
    .sidebar {
      position: sticky;
      top: 0;
      height: 100vh;
      overflow: auto;
      background: var(--panel);
      border-right: 1px solid var(--line);
      padding: 20px;
    }
    .brand {
      display: grid;
      gap: 6px;
      margin-bottom: 18px;
    }
    .brand strong {
      font-size: 18px;
      line-height: 1.35;
    }
    .brand span {
      color: var(--muted);
      font-size: 13px;
    }
    .search {
      position: sticky;
      top: 0;
      background: var(--panel);
      padding-bottom: 14px;
      z-index: 3;
    }
    .search input {
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 10px 12px;
      font-size: 14px;
      outline: none;
    }
    .search input:focus {
      border-color: var(--accent);
      box-shadow: 0 0 0 3px var(--accent-weak);
    }
    .count {
      margin-top: 8px;
      color: var(--muted);
      font-size: 13px;
    }
    .nav {
      display: grid;
      gap: 6px;
    }
    .nav-item {
      display: grid;
      gap: 2px;
      padding: 9px 10px;
      border-radius: 8px;
      color: var(--text);
    }
    .nav-item:hover {
      background: var(--accent-weak);
      text-decoration: none;
    }
    .nav-title {
      font-size: 14px;
      font-weight: 650;
      line-height: 1.45;
    }
    .nav-path {
      color: var(--muted);
      font-size: 12px;
      word-break: break-all;
      line-height: 1.45;
    }
    .content {
      min-width: 0;
      padding: 28px;
    }
    .topbar {
      position: sticky;
      top: 0;
      z-index: 5;
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 12px;
      margin: -28px -28px 24px;
      padding: 14px 28px;
      background: rgba(246, 247, 249, 0.92);
      border-bottom: 1px solid var(--line);
      backdrop-filter: blur(12px);
    }
    .topbar .summary {
      color: var(--muted);
      font-size: 14px;
    }
    .topbar button {
      border: 1px solid var(--line);
      background: var(--panel);
      border-radius: 8px;
      padding: 8px 10px;
      color: var(--text);
      cursor: pointer;
    }
    .topbar button:hover {
      border-color: var(--accent);
      color: var(--accent);
    }
    .doc-section {
      max-width: 980px;
      margin: 0 auto 28px;
      padding: 32px;
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      box-shadow: var(--shadow);
    }
    .doc-meta {
      color: var(--muted);
      font-size: 13px;
      margin-bottom: 16px;
      word-break: break-all;
    }
    .mini-toc {
      display: grid;
      gap: 4px;
      margin: 0 0 24px;
      padding: 14px 16px;
      background: #f8fafc;
      border: 1px solid var(--line);
      border-radius: 8px;
    }
    .mini-toc a {
      color: var(--muted);
      font-size: 13px;
      line-height: 1.5;
    }
    .mini-toc .toc-l2 { padding-left: 12px; }
    .mini-toc .toc-l3 { padding-left: 24px; }
    h1, h2, h3, h4, h5, h6 {
      color: #18212b;
      line-height: 1.35;
      margin: 1.4em 0 0.65em;
      scroll-margin-top: 82px;
    }
    h1 {
      margin-top: 0;
      font-size: 30px;
      border-bottom: 1px solid var(--line);
      padding-bottom: 12px;
    }
    h2 { font-size: 23px; }
    h3 { font-size: 18px; }
    p { margin: 0 0 1em; }
    ul, ol { padding-left: 1.4em; }
    li { margin: 0.2em 0; }
    blockquote {
      margin: 18px 0;
      padding: 12px 16px;
      border-left: 4px solid var(--success);
      background: #f2f8f5;
      color: #244538;
    }
    blockquote p:last-child { margin-bottom: 0; }
    code {
      padding: 2px 5px;
      border-radius: 5px;
      background: #eef2f6;
      font-family: "Cascadia Code", Consolas, monospace;
      font-size: 0.92em;
    }
    pre {
      overflow: auto;
      padding: 16px;
      border-radius: 8px;
      background: var(--code-bg);
      color: var(--code-text);
    }
    pre code {
      padding: 0;
      background: transparent;
      color: inherit;
    }
    .diagram-shell {
      margin: 20px 0;
      padding: 18px;
      overflow-x: auto;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fbfcfd;
    }
    .diagram-svg {
      display: block;
      min-width: 520px;
      margin: 0 auto;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft YaHei", sans-serif;
    }
    .diagram-text {
      fill: #1f2933;
      font-size: 14px;
      font-weight: 600;
    }
    .visual-figure {
      margin: 22px 0;
      padding: 14px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fbfcfd;
    }
    .visual-figure img {
      display: block;
      width: 100%;
      max-width: 100%;
      height: auto;
      border-radius: 6px;
    }
    .visual-figure figcaption {
      margin-top: 10px;
      color: var(--muted);
      font-size: 13px;
      text-align: center;
    }
    .table-wrap {
      overflow-x: auto;
      margin: 18px 0;
      border: 1px solid var(--line);
      border-radius: 8px;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      min-width: 640px;
      background: var(--panel);
    }
    th, td {
      border-bottom: 1px solid var(--line);
      padding: 10px 12px;
      text-align: left;
      vertical-align: top;
    }
    th {
      background: #f2f5f8;
      font-weight: 700;
    }
    tr:last-child td { border-bottom: 0; }
    .hidden { display: none !important; }
    .mobile-menu { display: none; }
    @media (max-width: 900px) {
      .layout { grid-template-columns: 1fr; }
      .sidebar {
        position: fixed;
        inset: 0 auto 0 0;
        width: min(88vw, 340px);
        transform: translateX(-105%);
        transition: transform 160ms ease;
        z-index: 20;
        box-shadow: var(--shadow);
      }
      body.sidebar-open .sidebar { transform: translateX(0); }
      .mobile-menu { display: inline-flex; }
      .content { padding: 18px; }
      .topbar {
        margin: -18px -18px 18px;
        padding: 12px 18px;
      }
      .doc-section { padding: 22px; }
      h1 { font-size: 25px; }
    }
    @media print {
      .sidebar, .topbar, .mini-toc { display: none; }
      .layout { display: block; }
      .content { padding: 0; }
      .doc-section {
        box-shadow: none;
        border: 0;
        page-break-after: always;
      }
    }
""" + "    " + HR_CSS + "\n"

BOOK_SCRIPT = """
    const toggleBookNav = document.getElementById('toggleBookNav');
    if (toggleBookNav) {
      toggleBookNav.addEventListener('click', () => document.body.classList.toggle('nav-open'));
    }
    document.querySelectorAll('.book-nav-item').forEach(item => {
      item.addEventListener('click', () => document.body.classList.remove('nav-open'));
    });
"""

READER_SCRIPT = """
    const input = document.getElementById('searchInput');
    const articles = Array.from(document.querySelectorAll('.doc-section'));
    const navItems = Array.from(document.querySelectorAll('.nav-item'));
    const count = document.getElementById('resultCount');
    const toggle = document.getElementById('toggleSidebar');

    function normalize(value) {
      return value.toLowerCase().trim();
    }

    function applySearch() {
      const query = normalize(input.value);
      let visible = 0;
      for (const article of articles) {
        const haystack = normalize(article.innerText + ' ' + article.dataset.path);
        const matched = !query || haystack.includes(query);
        article.classList.toggle('hidden', !matched);
        if (matched) visible += 1;
      }
      for (const item of navItems) {
        const target = document.getElementById(item.dataset.doc);
        item.classList.toggle('hidden', target.classList.contains('hidden'));
      }
      count.textContent = query
        ? `找到 ${visible} 份相关文档`
        : `共 ${articles.length} 份 Markdown 文档`;
    }

    input.addEventListener('input', applySearch);
    toggle.addEventListener('click', () => document.body.classList.toggle('sidebar-open'));
    navItems.forEach(item => {
      item.addEventListener('click', () => document.body.classList.remove('sidebar-open'));
    });
"""


# ---------------------------------------------------------------------------
# 书籍阅读版
# ---------------------------------------------------------------------------

def build_book(timestamp: str) -> str:
    manifest = book_manifest()

    # 先建立 “文件 -> 章节 id” 映射，供链接改写
    entries: list[tuple[str, Path, str]] = []  # group, path, section_id
    seq = 0
    for group, files in manifest:
        for path, custom_id in files:
            if not path.is_file():
                print(f"  ! 书籍清单缺文件，跳过：{path.relative_to(ROOT)}")
                continue
            seq += 1
            sid = custom_id or f"book-{seq:03d}"
            entries.append((group, path, sid))

    by_relpath = {str(p.relative_to(ROOT)).replace("\\", "/"): sid for _, p, sid in entries}

    def resolver(href: str, text_html: str, md_path: Path):
        if href.startswith("#") or re.match(r"^[a-z]+://", href) or href.startswith("mailto:"):
            return None  # 保持原样
        clean = href.split("#")[0]
        if clean.endswith(".md"):
            target = (md_path.parent / clean).resolve()
            try:
                rel = str(target.relative_to(ROOT)).replace("\\", "/")
            except ValueError:
                rel = None
            if rel and rel in by_relpath:
                return f'<a href="#{by_relpath[rel]}">{text_html}</a>'
            return f"<code>{text_html}</code>" if "<" not in text_html else text_html
        return None

    nav_parts: list[str] = []
    article_parts: list[str] = []
    section_no = 0
    diagram_count = 0
    current_group = None
    for group, path, sid in entries:
        section_no += 1
        if group != current_group:
            nav_parts.append(f'<div class="book-nav-group">{html.escape(group)}</div>')
            current_group = group
        title = first_h1(path)
        nav_parts.append(
            f'<a class="book-nav-item" href="#{sid}">{html.escape(title)}</a>'
        )
        renderer = Renderer(path, sid, link_resolver=resolver)
        body = renderer.render(path.read_text(encoding="utf-8"))
        diagram_count += body.count('class="diagram-svg"')
        kicker = f"第 {section_no:02d} 节 · {html.escape(group)}"
        article_parts.append(
            f'<article class="book-chapter" id="{sid}">'
            f'<div class="chapter-kicker">{kicker}</div>{body}</article>'
        )

    cover = (
        '<section class="book-cover">'
        "<h1>AI 跨境电商效能提升实战课</h1>"
        "<p>一本按课程顺序阅读的版本。它把章节、案例、图示、术语解释、实操手册、"
        "Skills 教程和附录串成一条学习路径，适合分享给学员直接阅读。</p>"
        '<div class="cover-meta">'
        '<span class="cover-pill">21 个实战章节 + 21 份实操手册</span>'
        '<span class="cover-pill">流程图 / 时序图 / 四象限</span>'
        '<span class="cover-pill">AI Agent Skills 入门</span>'
        '<span class="cover-pill">附录：预算 / Agent / 合规</span>'
        "</div></section>"
    )

    doc = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AI 跨境电商效能提升实战课｜书籍阅读版</title>
  <link rel="icon" href="data:,">
  <style>{BOOK_CSS}  </style>
</head>
<body>
  <div class="mobile-top">
    <button type="button" id="toggleBookNav">目录</button>
    <button type="button" onclick="window.print()">打印</button>
  </div>
  <div class="book-layout">
    <aside class="book-sidebar">
      <h2 class="book-title">AI 跨境电商效能提升实战课</h2>
      <div class="book-subtitle">书籍阅读版 · {section_no} 节 · {timestamp}</div>
      <nav class="book-nav" aria-label="书籍目录">
        {chr(10).join(nav_parts)}
      </nav>
    </aside>
    <main class="book-main">
      {cover}
{chr(10).join(article_parts)}
    </main>
  </div>
  <script>{BOOK_SCRIPT}  </script>
</body>
</html>
<!-- generated-timestamp: {timestamp} -->
"""
    print(f"  书籍阅读版：{section_no} 节，{diagram_count} 张内嵌 SVG 图")
    return doc


# ---------------------------------------------------------------------------
# 资料库阅读器
# ---------------------------------------------------------------------------

def build_reader(timestamp: str) -> str:
    files = all_markdown_files()
    ids = {f: f"doc-{i + 1:03d}" for i, f in enumerate(files)}
    by_relpath = {str(f.relative_to(ROOT)).replace("\\", "/"): ids[f] for f in files}

    def resolver(href: str, text_html: str, md_path: Path):
        if href.startswith("#") or re.match(r"^[a-z]+://", href) or href.startswith("mailto:"):
            return None
        clean = href.split("#")[0]
        if clean.endswith(".md") or clean.rstrip("/").endswith((".md",)):
            target = (md_path.parent / clean).resolve()
            try:
                rel = str(target.relative_to(ROOT)).replace("\\", "/")
            except ValueError:
                rel = None
            if rel and rel in by_relpath:
                return f'<a href="#{by_relpath[rel]}">{text_html}</a>'
            return f"<code>{text_html}</code>" if "<" not in text_html else text_html
        return None

    nav_parts: list[str] = []
    article_parts: list[str] = []
    diagram_count = 0
    for f in files:
        did = ids[f]
        rel = str(f.relative_to(ROOT)).replace("\\", "/")
        title = first_h1(f)
        nav_parts.append(
            f'<a class="nav-item" data-doc="{did}" href="#{did}">'
            f'<span class="nav-title">{html.escape(title)}</span>'
            f'<span class="nav-path">{html.escape(rel)}</span></a>'
        )
        renderer = Renderer(f, did, link_resolver=resolver)
        body = renderer.render(f.read_text(encoding="utf-8"))
        diagram_count += body.count('class="diagram-svg"')
        toc_links = [
            f'<a class="toc-l{min(lv, 3)}" href="#{anchor}">{html.escape(text)}</a>'
            for lv, anchor, text in renderer.headings
            if lv <= 3
        ]
        toc = (
            f'<nav class="mini-toc" aria-label="文档目录">{chr(10).join(toc_links)}</nav>'
            if toc_links
            else ""
        )
        article_parts.append(
            f'<article class="doc-section" id="{did}" '
            f'data-title="{html.escape(title, quote=True)}" data-path="{html.escape(rel, quote=True)}">'
            f'<div class="doc-meta">{html.escape(rel)}</div>{toc}{body}</article>'
        )

    doc = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AI 跨境电商效能提升实战课｜离线阅读包</title>
  <link rel="icon" href="data:,">
  <style>{READER_CSS}  </style>
</head>
<body>
  <div class="layout">
    <aside class="sidebar" id="sidebar">
      <div class="brand">
        <strong>AI 跨境电商效能提升实战课</strong>
        <span>离线 HTML 阅读包</span>
        <span>生成时间：{timestamp}</span>
      </div>
      <div class="search">
        <input id="searchInput" type="search" placeholder="搜索标题、正文或文件路径">
        <div class="count" id="resultCount">共 {len(files)} 份 Markdown 文档</div>
      </div>
      <nav class="nav" id="navList" aria-label="文档列表">
        {chr(10).join(nav_parts)}
      </nav>
    </aside>
    <main class="content">
      <div class="topbar">
        <button class="mobile-menu" type="button" id="toggleSidebar">目录</button>
        <div class="summary">共 {len(files)} 份文档。支持搜索、目录跳转和打印。</div>
        <button type="button" onclick="window.print()">打印</button>
      </div>
{chr(10).join(article_parts)}
    </main>
  </div>
  <script>{READER_SCRIPT}  </script>
</body>
</html>
<!-- generated-timestamp: {timestamp} -->
"""
    print(f"  资料库阅读器：{len(files)} 份文档，{diagram_count} 张内嵌 SVG 图")
    return doc


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> int:
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"ROOT = {ROOT}")

    print("构建书籍阅读版 ...")
    book = build_book(timestamp)
    print("构建资料库阅读器 ...")
    reader = build_reader(timestamp)

    outputs = [
        (ROOT / "AI跨境电商效能提升实战课_书籍阅读版.html", book),
        (ROOT / "book_reading_package" / "index.html", book),
        (ROOT / "AI跨境电商效能提升实战课_资料库阅读器.html", reader),
        (ROOT / "html_reading_package" / "index.html", reader),
    ]
    for path, content in outputs:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        print(f"  写出 {path.relative_to(ROOT)}（{len(content.encode('utf-8')) / 1024 / 1024:.2f} MB）")

    # 自检：关键内容必须出现在产物里
    checks = [
        ("书籍版含附录A正文", "没有成本意识" in book),
        ("书籍版含附录C正文", "红线" in book),
        ("书籍版含21章", "第 21 章" in book),
        ("书籍版含实操手册锚点", 'id="manual-day01"' in book),
        ("书籍版含通用约定", "课程通用约定" in book),
        ("阅读器含岗位提效诊断表新版", "试点动作卡" in reader),
        ("阅读器含交付版本索引", "可分享版本清单" in reader),
    ]
    failed = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(f"  [{'OK' if ok else 'FAIL'}] {name}")
    if failed:
        print("自检未通过！", failed)
        return 1
    print("全部完成。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
