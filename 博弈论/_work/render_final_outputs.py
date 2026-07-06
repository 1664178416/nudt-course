from __future__ import annotations

import html
import re
from datetime import date
from pathlib import Path

import markdown
from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[1]
FINAL = ROOT / "最终输出"

DETAIL_MD = FINAL / "博弈论题库官方中文详解.md"
INDEX_MD = FINAL / "博弈论题库题源与答案位置索引.md"
SOLUTIONS_OCR = ROOT / "_work" / "ocr" / "Solutions.pdf.paddleocr-vl.md"

DETAIL_HTML = FINAL / "博弈论题库官方中文详解_精排版.html"
INDEX_HTML = FINAL / "博弈论题库题源与答案位置索引_精排版.html"
AUDIT_MD = FINAL / "官方题解核对报告.md"
STUDY_MD = FINAL / "博弈论题库官方校订满分解析.md"
STUDY_HTML = FINAL / "博弈论题库官方校订满分解析_精排版.html"


MD_EXTENSIONS = ["tables", "fenced_code", "sane_lists"]


CSS = r"""
:root {
  --bg: #f6f7f9;
  --paper: #ffffff;
  --ink: #172033;
  --muted: #657184;
  --line: #d9dee7;
  --soft: #edf1f6;
  --primary: #245b74;
  --primary-soft: #e3f1f5;
  --accent: #9a6a13;
  --ok: #216e4e;
  --warn: #8a4b16;
  --shadow: 0 12px 32px rgba(23, 32, 51, 0.08);
}

* {
  box-sizing: border-box;
}

html {
  scroll-behavior: smooth;
}

body {
  margin: 0;
  background: var(--bg);
  color: var(--ink);
  font-family: "Noto Sans SC", "Microsoft YaHei", "PingFang SC", Arial, sans-serif;
  font-size: 16px;
  line-height: 1.68;
}

a {
  color: var(--primary);
  text-decoration: none;
}

a:hover {
  text-decoration: underline;
}

.layout {
  display: grid;
  grid-template-columns: 280px minmax(0, 1fr);
  gap: 28px;
  max-width: 1440px;
  margin: 0 auto;
  padding: 28px;
}

.toc {
  position: sticky;
  top: 20px;
  align-self: start;
  max-height: calc(100vh - 40px);
  overflow: auto;
  background: var(--paper);
  border: 1px solid var(--line);
  border-radius: 8px;
  box-shadow: var(--shadow);
  padding: 18px;
}

.toc-title {
  margin: 0 0 12px;
  font-size: 14px;
  color: var(--muted);
  letter-spacing: 0;
}

.toc ol {
  margin: 0;
  padding-left: 22px;
}

.toc li {
  margin: 7px 0;
  color: var(--muted);
  font-size: 14px;
  line-height: 1.45;
}

.document {
  min-width: 0;
}

.hero,
.problem,
.content-card {
  background: var(--paper);
  border: 1px solid var(--line);
  border-radius: 8px;
  box-shadow: var(--shadow);
}

.hero {
  padding: 28px 32px;
  margin-bottom: 18px;
}

.hero h1 {
  margin: 0 0 10px;
  font-size: 30px;
  line-height: 1.25;
  letter-spacing: 0;
}

.meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 16px;
}

.pill {
  display: inline-flex;
  align-items: center;
  min-height: 28px;
  padding: 3px 10px;
  border-radius: 999px;
  background: var(--primary-soft);
  color: #17485d;
  border: 1px solid #c6e1ea;
  font-size: 13px;
  font-weight: 600;
}

.pill.warn {
  background: #fff2db;
  color: var(--warn);
  border-color: #f1d39c;
}

.problem {
  padding: 26px 30px;
  margin: 18px 0;
  break-inside: avoid;
}

.problem h2,
.content-card h2 {
  margin: 0 0 18px;
  padding-bottom: 10px;
  border-bottom: 2px solid var(--soft);
  font-size: 22px;
  line-height: 1.35;
  letter-spacing: 0;
}

h3 {
  margin: 24px 0 10px;
  font-size: 17px;
  color: var(--primary);
  letter-spacing: 0;
}

p {
  margin: 10px 0;
}

ul,
ol {
  padding-left: 24px;
}

li {
  margin: 5px 0;
}

blockquote {
  margin: 14px 0;
  padding: 10px 14px;
  border-left: 4px solid var(--primary);
  background: var(--primary-soft);
}

code {
  font-family: "Cascadia Mono", Consolas, "SFMono-Regular", monospace;
  background: var(--soft);
  border: 1px solid var(--line);
  border-radius: 5px;
  padding: 1px 5px;
}

pre {
  overflow: auto;
  padding: 14px;
  background: #111827;
  color: #f8fafc;
  border-radius: 8px;
}

pre code {
  background: transparent;
  border: 0;
  padding: 0;
}

.MathJax,
mjx-container {
  font-size: 108% !important;
}

table {
  width: 100%;
  border-collapse: collapse;
  margin: 14px 0;
  font-size: 14px;
}

th,
td {
  border: 1px solid var(--line);
  padding: 8px 10px;
  vertical-align: top;
}

th {
  background: #eef4f7;
  color: #18384a;
  font-weight: 700;
}

tr:nth-child(even) td {
  background: #fbfcfd;
}

.table-wrap {
  overflow-x: auto;
  margin: 14px 0;
}

.content-card {
  padding: 26px 30px;
  margin: 18px 0;
}

.study-paper {
  background: var(--paper);
  border: 1px solid var(--line);
  border-radius: 8px;
  box-shadow: var(--shadow);
  padding: 30px 38px;
}

.study-paper h1 {
  margin: 30px 0 16px;
  padding-top: 8px;
  font-size: 25px;
  line-height: 1.35;
  border-top: 2px solid var(--soft);
  letter-spacing: 0;
}

.study-paper h2 {
  margin: 30px 0 14px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--line);
  font-size: 21px;
  line-height: 1.4;
  letter-spacing: 0;
}

.study-paper h4 {
  margin: 20px 0 8px;
  font-size: 16px;
  line-height: 1.45;
  color: var(--primary);
  letter-spacing: 0;
}

.study-paper > h1:first-child {
  margin-top: 0;
  border-top: 0;
}

.callout {
  margin: 18px 0;
  padding: 12px 14px;
  border-radius: 8px;
  border: 1px solid #b9dacd;
  background: #edf8f3;
  color: var(--ok);
}

.source-list {
  display: grid;
  gap: 8px;
  margin: 12px 0 18px;
  padding: 12px 14px;
  background: #fbfcfd;
  border: 1px solid var(--line);
  border-radius: 8px;
}

.source-list li {
  margin: 0;
}

.footer-note {
  color: var(--muted);
  font-size: 13px;
  margin: 24px 0 0;
}

@media (max-width: 980px) {
  .layout {
    display: block;
    padding: 16px;
  }

  .toc {
    position: static;
    max-height: none;
    margin-bottom: 16px;
  }

  .hero,
  .problem,
  .content-card,
  .study-paper {
    padding: 20px;
  }

  .hero h1 {
    font-size: 24px;
  }
}

@media print {
  body {
    background: #ffffff;
    font-size: 12pt;
  }

  .layout {
    display: block;
    max-width: none;
    padding: 0;
  }

  .toc {
    display: none;
  }

  .hero,
  .problem,
  .content-card,
  .study-paper {
    box-shadow: none;
    border: 0;
    padding: 0;
    margin: 0 0 18pt;
  }

  .problem {
    page-break-inside: avoid;
  }

  a {
    color: #000000;
    text-decoration: none;
  }
}
"""


def protect_math(text: str) -> tuple[str, list[str]]:
    math_chunks: list[str] = []

    def stash(match: re.Match[str]) -> str:
        math_chunks.append(match.group(0))
        return f"@@MATH{len(math_chunks) - 1}@@"

    protected = re.sub(r"\$\$[\s\S]*?\$\$", stash, text)
    protected = re.sub(r"(?<!\$)\$(?!\$)(?:\\.|[^$])+\$(?!\$)", stash, protected)
    return protected, math_chunks


def restore_math(fragment: str, math_chunks: list[str]) -> str:
    for idx, chunk in enumerate(math_chunks):
        fragment = fragment.replace(f"@@MATH{idx}@@", html.escape(chunk, quote=False))
    return fragment


def md_to_html(text: str) -> str:
    protected, math_chunks = protect_math(text)
    fragment = markdown.markdown(protected, extensions=MD_EXTENSIONS, output_format="html5")
    return restore_math(fragment, math_chunks)


def wrap_tables(fragment: str) -> str:
    soup = BeautifulSoup(fragment, "html.parser")
    for table in soup.find_all("table"):
        if table.parent and "table-wrap" in table.parent.get("class", []):
            continue
        wrapper = soup.new_tag("div")
        wrapper["class"] = "table-wrap"
        table.wrap(wrapper)
    return str(soup)


def mathjax_script() -> str:
    return """
<script>
window.MathJax = {
  tex: {
    inlineMath: [['$', '$'], ['\\\\(', '\\\\)']],
    displayMath: [['$$', '$$'], ['\\\\[', '\\\\]']],
    processEscapes: true
  },
  options: { skipHtmlTags: ['script', 'noscript', 'style', 'textarea', 'pre', 'code'] }
};
</script>
<script defer src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
"""


def page_shell(title: str, toc: str, body: str, generated: str) -> str:
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <style>{CSS}</style>
  {mathjax_script()}
</head>
<body>
  <div class="layout">
    <nav class="toc" aria-label="目录">
      <p class="toc-title">目录</p>
      {toc}
    </nav>
    <main class="document">
      {body}
      <p class="footer-note">生成日期：{generated}；公式由 MathJax 渲染，离线时仍保留 LaTeX 原文。</p>
    </main>
  </div>
</body>
</html>
"""


def render_detail(text: str) -> str:
    parts = re.split(r"(?m)^## ", text)
    intro = parts[0]
    sections = ["## " + part for part in parts[1:] if part.strip()]

    h1_match = re.search(r"^#\s+(.+)$", intro, flags=re.M)
    title = h1_match.group(1).strip() if h1_match else "博弈论题库官方中文详解"

    toc_items: list[str] = []
    rendered_sections: list[str] = []
    for idx, section in enumerate(sections, start=1):
        first_line, _, body = section.partition("\n")
        heading = first_line.removeprefix("## ").strip()
        section_id = f"q{idx:02d}"
        toc_items.append(f'<li><a href="#{section_id}">{html.escape(heading)}</a></li>')
        body_html = wrap_tables(md_to_html(body))
        body_html = body_html.replace("<ul>\n<li>题库位置", '<ul class="source-list">\n<li>题库位置', 1)
        rendered_sections.append(
            f'<section class="problem" id="{section_id}">\n'
            f"<h2>{html.escape(heading)}</h2>\n{body_html}\n</section>"
        )

    intro_text = re.sub(r"^#\s+.+$", "", intro, count=1, flags=re.M).strip()
    intro_html = wrap_tables(md_to_html(intro_text)) if intro_text else ""
    toc = "<ol>" + "\n".join(toc_items) + "</ol>"
    hero = f"""
<section class="hero">
  <h1>{html.escape(title)}</h1>
  <p>按题库一、题库二逐题整理题源、题目、官方中文解答和核对说明。直接对应 Solutions.pdf 的题目已按 PaddleOCR-VL 识别结果重新核对。</p>
  <div class="meta">
    <span class="pill">50 道题</span>
    <span class="pill">9 道直接对应 Solutions.pdf</span>
    <span class="pill warn">7.3 已按官方反例修正</span>
  </div>
  {intro_html}
</section>
"""
    return page_shell(title, toc, hero + "\n".join(rendered_sections), date.today().isoformat())


def render_index(text: str) -> str:
    html_body = wrap_tables(md_to_html(text))
    soup = BeautifulSoup(html_body, "html.parser")
    first_h1 = soup.find("h1")
    if first_h1:
        first_h1.decompose()
    toc_items: list[str] = []
    for idx, heading in enumerate(soup.find_all(["h2", "h3"]), start=1):
        heading_id = f"idx{idx:02d}"
        heading["id"] = heading_id
        toc_items.append(f'<li><a href="#{heading_id}">{html.escape(heading.get_text(" ", strip=True))}</a></li>')

    title = "博弈论题库题源与答案位置索引"
    toc = "<ol>" + "\n".join(toc_items) + "</ol>"
    body = f"""
<section class="hero">
  <h1>{title}</h1>
  <p>用于手动核查题源：优先看“主定位”，再按“补充定位”和 Solutions.pdf 页码复核。</p>
  <div class="meta">
    <span class="pill">表格索引</span>
    <span class="pill">教材P + PDF页</span>
    <span class="pill warn">题库一/题库二分开</span>
  </div>
</section>
<section class="content-card">
{soup}
</section>
"""
    return page_shell(title, toc, body, date.today().isoformat())


def split_problem_sections(detail_text: str) -> list[tuple[str, str, str]]:
    parts = re.split(r"(?m)^## ", detail_text)
    sections: list[tuple[str, str, str]] = []
    for part in parts[1:]:
        if not part.strip():
            continue
        header, _, body = part.partition("\n")
        m = re.match(r"(题库[一二])-习题(\d+\.\d+)\s+(?:\d+\.\d+\s+)?(.+)", header.strip())
        if not m:
            continue
        bank, number, title = m.groups()
        sections.append((bank, f"习题 {number} {title.strip()}", body.strip()))
    return sections


def extract_subsections(body: str) -> dict[str, str]:
    matches = list(re.finditer(r"(?m)^### (题源定位|题目|官方中文解答|核对说明)\s*$", body))
    result: dict[str, str] = {}
    for idx, match in enumerate(matches):
        key = match.group(1)
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(body)
        result[key] = body[start:end].strip()
    return result


def clean_study_text(text: str) -> str:
    replacements = {
        "`f_k`": "$f_k$",
        "`v(S)=(sum a_i)^2`": "$v(S)=(\\sum_i a_i)^2$",
        "`N={1,2},{3}`": "$N=\\{1,2\\},\\{3\\}$",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def build_study_md(detail_text: str) -> str:
    sections = split_problem_sections(detail_text)
    lines: list[str] = [
        "# 研究生课程《博弈论》题库官方校订满分解析",
        "",
        "> 本稿按旧版“题目 / 答案（满分版） / 解析（思路与易错点）”的阅读结构重排，并保留每题题源定位。题目来自 PaddleOCR-VL；有直接对应条目时，以 `Solutions.pdf` 的 PaddleOCR-VL 识别结果为准；无直接对应条目时，按教材正文定义、定理、例题或题库数据推导。",
        "",
        "## 覆盖说明",
        "",
        "- 题库二：`26春研究生课程《博弈论》练习题库（6-9章内容）.pdf`，共 5 题。",
        "- 题库一：`研究生课程《博弈论》练习题库(1).pdf`，共 45 题。",
        "- 全文共 50 题；每题包含题源定位、题目、答案和解析。",
        "",
        "## 核对口径",
        "",
        "- `教材P` 为书内印刷页码，括号内 `PDF` 为 PDF 阅读器页码。",
        "- `Solutions.pdf` 页码专指英文答案 PDF 的 PDF 阅读器页码，已用 PaddleOCR-VL 重新核对。",
        "- 旧版 AI 解析只作为中文表达和步骤组织参考；若与官方答案或教材正文冲突，以官方答案和教材为准。",
        "",
    ]

    current_bank = ""
    for bank, title, body in sections:
        if bank != current_bank:
            current_bank = bank
            if bank == "题库二":
                lines.extend(["# 一、26 春第 6-9 章题库解析", ""])
            else:
                lines.extend(["# 二、综合作业题库解析", ""])

        subs = extract_subsections(body)
        source = clean_study_text(subs.get("题源定位", ""))
        problem = clean_study_text(subs.get("题目", ""))
        answer = clean_study_text(subs.get("官方中文解答", ""))
        note = clean_study_text(subs.get("核对说明", ""))

        lines.extend([f"## {title}", ""])
        if source:
            lines.extend(["#### 题源定位", "", source, ""])
        if problem:
            lines.extend(["#### 题目", "", problem, ""])
        if answer:
            lines.extend(["#### 答案（官方校订版）", "", answer, ""])
        if note:
            lines.extend(["#### 解析（思路与易错点）", "", note, ""])

    return "\n".join(lines).rstrip() + "\n"


def render_study(text: str, title: str) -> str:
    body_html = wrap_tables(md_to_html(text))
    soup = BeautifulSoup(body_html, "html.parser")
    first_h1 = soup.find("h1")
    if first_h1:
        first_h1.decompose()

    toc_items: list[str] = []
    for idx, heading in enumerate(soup.find_all(["h1", "h2"]), start=1):
        heading_id = f"study{idx:02d}"
        heading["id"] = heading_id
        toc_items.append(f'<li><a href="#{heading_id}">{html.escape(heading.get_text(" ", strip=True))}</a></li>')

    toc = "<ol>" + "\n".join(toc_items) + "</ol>"
    body = f"""
<section class="hero">
  <h1>{html.escape(title)}</h1>
  <p>按旧版满分答案的结构重排：题源定位、题目、答案、解析。LaTeX 在生成 HTML 前已做保护，避免公式和下标被 Markdown 吃掉。</p>
  <div class="meta">
    <span class="pill">50 道题</span>
    <span class="pill">官方校订版</span>
    <span class="pill warn">公式保护渲染</span>
  </div>
</section>
<article class="study-paper">
{soup}
</article>
"""
    return page_shell(title, toc, body, date.today().isoformat())


def build_audit(detail_text: str, index_text: str, solutions_text: str) -> str:
    section_count = len(re.findall(r"^## 题库[一二]-习题\d+\.\d+", detail_text, flags=re.M))
    index_rows = len(re.findall(r"^\| 习题\d+\.\d+\s*\|", index_text, flags=re.M))
    refs = re.findall(r"官方答案位置：Solutions\.pdf Ex\. ([0-9]+\.[0-9]+)，PDF第(\d+)页", detail_text)

    direct_rows = [
        ("题库二-习题1.3", "Ex.7.35", "PDF168", "采用官方的扰动行为策略构造。"),
        ("题库一-习题2.3", "Ex.2.21", "PDF11", "正仿射变换证明与官方三类情形一致，中文表述更紧凑。"),
        ("题库一-习题4.1", "Ex.4.18", "PDF54", "官方矩阵结论为无纯策略纳什均衡，最终答案一致。"),
        ("题库一-习题4.3", "Ex.4.15", "PDF53", "纳什均衡等价于每个参与人采取最佳反应。"),
        ("题库一-习题7.2", "Ex.18.8", "PDF464", "按 k=n、k=n-1、0<k<n-1、k=0 四种情形给出核心。"),
        ("题库一-习题7.3", "Ex.18.9", "PDF464", "已改为官方两个反例：四人非单调反例、三人去掉非负性反例。"),
        ("题库一-习题8.2", "Ex.19.14", "PDF505", "边际贡献与随机排列平均一致；最终保留代数形式 a_i sum_j a_j。"),
        ("题库一-习题10.1", "Ex.21.2", "PDF538", "官方重点证明传递性；最终按题目补足自反性和完备性。"),
        ("题库一-习题10.4", "Ex.21.3", "PDF538", "官方为紧集上连续函数极小点集非空紧致；最终用于核原有限步最小化。"),
    ]

    missing = []
    for ex, page in refs:
        if not re.search(r"(?m)^" + re.escape(ex) + r"\b", solutions_text):
            missing.append(f"Ex.{ex} PDF{page}")

    lines = [
        "# 官方题解核对报告",
        "",
        "本报告用于说明最终详解与官方 `Solutions.pdf` 的贴合情况。`Solutions.pdf` 依据 PaddleOCR-VL 结果 `_work/ocr/Solutions.pdf.paddleocr-vl.md` 核对，不使用普通纯文本抽取作为公式依据。",
        "",
        "## 结构检查",
        "",
        f"- 最终详解题目节数：{section_count}。",
        f"- 题源索引表格题目行数：{index_rows}。",
        f"- 直接引用 `Solutions.pdf` 的题目数：{len(refs)}。",
        f"- 官方 OCR 中缺失的引用编号：{'无' if not missing else '、'.join(missing)}。",
        "",
        "## 直接对应 Solutions.pdf 的题目",
        "",
        "| 题目 | 官方位置 | 核对结论 |",
        "|---|---|---|",
    ]
    lines.extend(f"| {q} | {ex}，{page} | {note} |" for q, ex, page, note in direct_rows)
    lines.extend(
        [
            "",
            "## 与旧版 AI 解析的关系",
            "",
            "- 旧版 `博弈论题库详细解析.md` / `博弈论题库逐题深度解析_全题完美版.pdf` 仅作为中文表达和步骤组织参考。",
            "- 遇到旧版解析与官方 Solutions 或教材定位不一致时，以官方 Solutions 和教材正文为准。",
            "- 本轮明确修正了题库一-习题7.3：旧版反例已替换为 Solutions.pdf Ex.18.9 的官方反例。",
            "",
            "## 保留说明",
            "",
            "- 对没有直接 Solutions 条目的题，最终详解按教材中的定义、定理、例题或题库给定数据推导，并在每题“题源定位”中给出教材页码。",
            "- `题库一-习题8.2` 中官方 OCR 末尾出现 `a_i\\sqrt{v(N)}`，最终答案保留更一般且与推导相同的代数形式 `a_i\\sum_{j\\in N}a_j`。",
            "- 索引和详解均保留具体 PDF 阅读器页码，便于回到原 PDF 手动核查。",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    detail_text = DETAIL_MD.read_text(encoding="utf-8")
    index_text = INDEX_MD.read_text(encoding="utf-8")
    solutions_text = SOLUTIONS_OCR.read_text(encoding="utf-8")
    study_text = build_study_md(detail_text)

    STUDY_MD.write_text(study_text, encoding="utf-8")
    DETAIL_HTML.write_text(render_study(study_text, "博弈论题库官方中文详解"), encoding="utf-8")
    STUDY_HTML.write_text(render_study(study_text, "博弈论题库官方校订满分解析"), encoding="utf-8")
    INDEX_HTML.write_text(render_index(index_text), encoding="utf-8")
    AUDIT_MD.write_text(build_audit(detail_text, index_text, solutions_text), encoding="utf-8")

    print(f"wrote {STUDY_MD}")
    print(f"wrote {DETAIL_HTML}")
    print(f"wrote {STUDY_HTML}")
    print(f"wrote {INDEX_HTML}")
    print(f"wrote {AUDIT_MD}")


if __name__ == "__main__":
    main()
