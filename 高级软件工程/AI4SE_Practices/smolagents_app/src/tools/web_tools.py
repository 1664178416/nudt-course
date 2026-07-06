import json
import re
from pathlib import Path
from typing import List

from ..smolagents_compat import tool

from .base import resolve_artifact_write_path, resolve_read_path


def _split_items(raw_items: str) -> List[str]:
    if not raw_items:
        return []
    normalized = raw_items.replace("，", ",").replace("、", ",").replace("\n", ",")
    return [item.strip() for item in normalized.split(",") if item.strip()]


def _safe_slug(name: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_-]+", "-", name.strip().lower()).strip("-")
    return cleaned or "web-showcase"


def build_static_web_app_bundle(
    project_name: str,
    summary: str,
    feature_list: str = "",
    output_dir: str = "artifacts/web",
) -> dict:
    """构建静态网页交付物并返回生成的文件信息。"""
    features = _split_items(feature_list) or [
        "冒泡排序可视化",
        "快速排序对比",
        "二分查找交互演示",
        "图遍历过程展示",
    ]
    project_slug = _safe_slug(project_name)
    target_dir = resolve_artifact_write_path(output_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    cards_html = "\n".join(
        f"""
        <article class="algorithm-card" data-name="{item}">
            <div class="algorithm-card__badge">Algorithm</div>
            <h3>{item}</h3>
            <p>交互式演示 {item} 的关键过程、时间复杂度与适用场景，便于课堂展示与原理理解。</p>
            <button class="ghost-button" data-algorithm="{item}">查看讲解</button>
        </article>
        """.strip()
        for item in features
    )

    spotlight_items = "\n".join(
        f'<li><span class="spotlight-dot"></span><strong>{item}</strong><span>支持动画演示、复杂度说明和步骤解读</span></li>'
        for item in features[:4]
    )

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{project_name}</title>
    <meta name="description" content="{summary}" />
    <link rel="stylesheet" href="./styles.css" />
</head>
<body>
    <div class="page-shell">
        <header class="hero">
            <nav class="topbar">
                <span class="brand">{project_name}</span>
                <a href="#algorithms">算法展厅</a>
                <a href="#highlights">亮点</a>
                <a href="#learn">学习建议</a>
            </nav>
            <div class="hero__content">
                <div class="hero__copy">
                    <p class="eyebrow">Software Engineering Demo</p>
                    <h1>{project_name}</h1>
                    <p class="hero__summary">{summary}</p>
                    <div class="hero__actions">
                        <a class="primary-button" href="#algorithms">开始浏览</a>
                        <button class="secondary-button" id="shuffle-button">随机聚焦一个算法</button>
                    </div>
                </div>
                <div class="hero__panel">
                    <div class="metric-card">
                        <span>演示算法数</span>
                        <strong>{len(features)}</strong>
                    </div>
                    <div class="metric-card">
                        <span>输出目录</span>
                        <strong>{target_dir.as_posix()}</strong>
                    </div>
                    <div class="metric-card">
                        <span>交付形式</span>
                        <strong>静态前端网页</strong>
                    </div>
                </div>
            </div>
            <div class="hero__backdrop"></div>
        </header>

        <main>
            <section class="section section--dark" id="algorithms">
                <div class="section__header">
                    <p class="section__eyebrow">Interactive Gallery</p>
                    <h2>算法展厅</h2>
                    <p>页面内置筛选、聚焦与讲解面板，适合作为课堂展示页、课程作业前端原型或技术汇报页面。</p>
                </div>
                <div class="toolbar">
                    <input id="filter-input" type="search" placeholder="搜索算法名称..." />
                    <span class="toolbar__hint">支持按名称快速筛选卡片</span>
                </div>
                <div class="algorithm-grid">
                    {cards_html}
                </div>
            </section>

            <section class="section" id="highlights">
                <div class="section__header">
                    <p class="section__eyebrow">Project Highlights</p>
                    <h2>页面亮点</h2>
                </div>
                <div class="highlight-layout">
                    <div class="spotlight-card">
                        <h3>为什么适合作为演示任务</h3>
                        <ul class="spotlight-list">
                            {spotlight_items}
                        </ul>
                    </div>
                    <aside class="explain-panel" id="explain-panel">
                        <h3>算法讲解面板</h3>
                        <p>点击左侧卡片中的“查看讲解”，这里会动态展示当前算法的说明、复杂度和展示建议。</p>
                    </aside>
                </div>
            </section>

            <section class="section section--accent" id="learn">
                <div class="section__header">
                    <p class="section__eyebrow">For Learning</p>
                    <h2>建议的展示方式</h2>
                </div>
                <div class="timeline">
                    <div class="timeline__item"><span>01</span><p>先讲问题背景，再切到页面快速浏览整体结构。</p></div>
                    <div class="timeline__item"><span>02</span><p>聚焦一个算法，结合讲解面板说明复杂度与适用场景。</p></div>
                    <div class="timeline__item"><span>03</span><p>最后强调该网页是通过多角色智能体流程自动生成并输出到任务目录。</p></div>
                </div>
            </section>
        </main>
    </div>

    <script src="./app.js"></script>
</body>
</html>
"""

    css = """:root {
    --bg: #f4efe6;
    --paper: rgba(255, 250, 242, 0.86);
    --ink: #1f2430;
    --muted: #5f6876;
    --accent: #bc5f3d;
    --accent-2: #1e6d72;
    --line: rgba(31, 36, 48, 0.08);
    --shadow: 0 20px 60px rgba(44, 34, 24, 0.14);
}

* {
    box-sizing: border-box;
}

html {
    scroll-behavior: smooth;
}

body {
    margin: 0;
    font-family: "Trebuchet MS", "Segoe UI", sans-serif;
    color: var(--ink);
    background:
        radial-gradient(circle at top left, rgba(188, 95, 61, 0.22), transparent 28%),
        radial-gradient(circle at top right, rgba(30, 109, 114, 0.18), transparent 24%),
        linear-gradient(180deg, #f6f1ea, #efe3d1);
}

.page-shell {
    min-height: 100vh;
}

.hero {
    position: relative;
    overflow: hidden;
    padding: 28px 28px 40px;
}

.hero__backdrop {
    position: absolute;
    inset: 14% -10% auto auto;
    width: 340px;
    height: 340px;
    background: linear-gradient(135deg, rgba(188, 95, 61, 0.28), rgba(30, 109, 114, 0.12));
    filter: blur(10px);
    border-radius: 48px;
    transform: rotate(18deg);
}

.topbar,
.hero__content,
.section,
.highlight-layout,
.timeline {
    position: relative;
    z-index: 1;
}

.topbar {
    display: flex;
    gap: 18px;
    align-items: center;
    flex-wrap: wrap;
    margin-bottom: 36px;
}

.topbar a,
.brand {
    text-decoration: none;
    color: var(--ink);
}

.brand {
    margin-right: auto;
    font-weight: 800;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}

.hero__content {
    display: grid;
    grid-template-columns: minmax(0, 1.3fr) minmax(280px, 0.7fr);
    gap: 22px;
}

.hero__copy,
.hero__panel,
.section,
.spotlight-card,
.explain-panel,
.timeline__item,
.algorithm-card {
    background: var(--paper);
    border: 1px solid var(--line);
    backdrop-filter: blur(10px);
    box-shadow: var(--shadow);
}

.hero__copy {
    padding: 28px;
    border-radius: 28px;
}

.hero__copy h1,
.section__header h2 {
    font-family: Georgia, "Times New Roman", serif;
    letter-spacing: -0.03em;
}

.hero__copy h1 {
    margin: 0 0 12px;
    font-size: clamp(2.5rem, 6vw, 4.8rem);
    line-height: 0.95;
}

.eyebrow,
.section__eyebrow {
    text-transform: uppercase;
    letter-spacing: 0.12em;
    font-size: 0.75rem;
    color: var(--accent-2);
    margin-bottom: 12px;
}

.hero__summary,
.section__header p,
.algorithm-card p,
.explain-panel p,
.timeline__item p,
.toolbar__hint {
    color: var(--muted);
    line-height: 1.7;
}

.hero__actions {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    margin-top: 24px;
}

.primary-button,
.secondary-button,
.ghost-button {
    border-radius: 999px;
    border: none;
    cursor: pointer;
    font: inherit;
    transition: transform 180ms ease, box-shadow 180ms ease, background 180ms ease;
}

.primary-button,
.secondary-button {
    padding: 12px 18px;
}

.primary-button {
    background: var(--ink);
    color: #fff;
    text-decoration: none;
}

.secondary-button {
    background: rgba(188, 95, 61, 0.1);
    color: var(--accent);
}

.ghost-button {
    padding: 10px 14px;
    background: transparent;
    color: var(--accent-2);
    border: 1px solid rgba(30, 109, 114, 0.2);
}

.primary-button:hover,
.secondary-button:hover,
.ghost-button:hover {
    transform: translateY(-2px);
}

.hero__panel {
    border-radius: 28px;
    padding: 18px;
    display: grid;
    gap: 14px;
}

.metric-card {
    border-radius: 22px;
    padding: 18px;
    background: rgba(255, 255, 255, 0.72);
}

.metric-card span {
    display: block;
    color: var(--muted);
    margin-bottom: 8px;
}

.metric-card strong {
    font-size: 1.2rem;
}

.section {
    border-radius: 28px;
    margin: 22px 28px;
    padding: 28px;
}

.section--dark {
    background: rgba(28, 35, 45, 0.92);
    color: #f6f0e8;
}

.section--dark .section__header p,
.section--dark .algorithm-card p,
.section--dark .toolbar__hint {
    color: rgba(246, 240, 232, 0.74);
}

.section--accent {
    background: linear-gradient(135deg, rgba(188, 95, 61, 0.16), rgba(30, 109, 114, 0.12));
}

.toolbar {
    display: flex;
    gap: 14px;
    flex-wrap: wrap;
    align-items: center;
    margin: 20px 0 26px;
}

.toolbar input {
    flex: 1 1 240px;
    min-width: 200px;
    padding: 12px 14px;
    border-radius: 14px;
    border: 1px solid rgba(255, 255, 255, 0.12);
    background: rgba(255, 255, 255, 0.08);
    color: inherit;
}

.algorithm-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 18px;
}

.algorithm-card {
    border-radius: 22px;
    padding: 18px;
    background: rgba(255, 248, 241, 0.12);
}

.algorithm-card__badge {
    display: inline-flex;
    padding: 6px 10px;
    border-radius: 999px;
    background: rgba(188, 95, 61, 0.18);
    color: #ffd7c8;
    font-size: 0.72rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}

.highlight-layout {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 18px;
}

.spotlight-card,
.explain-panel {
    border-radius: 24px;
    padding: 22px;
}

.spotlight-list {
    list-style: none;
    padding: 0;
    margin: 0;
    display: grid;
    gap: 14px;
}

.spotlight-list li {
    display: grid;
    grid-template-columns: auto 1fr;
    gap: 10px 12px;
    align-items: center;
}

.spotlight-dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background: var(--accent);
    box-shadow: 0 0 0 6px rgba(188, 95, 61, 0.14);
}

.timeline {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 16px;
}

.timeline__item {
    border-radius: 22px;
    padding: 18px;
}

.timeline__item span {
    display: inline-flex;
    width: 38px;
    height: 38px;
    align-items: center;
    justify-content: center;
    border-radius: 12px;
    background: rgba(30, 109, 114, 0.14);
    color: var(--accent-2);
    font-weight: 700;
}

@media (max-width: 900px) {
    .hero__content,
    .highlight-layout {
        grid-template-columns: 1fr;
    }

    .section,
    .hero {
        padding-left: 18px;
        padding-right: 18px;
        margin-left: 0;
        margin-right: 0;
    }
}
"""

    js = f"""const explanations = {json.dumps({
        item: {
            "summary": f"{item} 适合在课堂或汇报中用于展示核心步骤与复杂度变化。",
            "complexity": "时间复杂度和空间复杂度可根据具体实现进一步补充。",
            "tip": "建议配合动画或示意图展示关键步骤。"
        }
        for item in features
    }, ensure_ascii=False, indent=2)};

const filterInput = document.getElementById("filter-input");
const explainPanel = document.getElementById("explain-panel");
const cards = Array.from(document.querySelectorAll(".algorithm-card"));
const shuffleButton = document.getElementById("shuffle-button");

function renderExplanation(name) {{
    const info = explanations[name];
    if (!info) {{
        return;
    }}

    explainPanel.innerHTML = `
        <h3>${{name}}</h3>
        <p>${{info.summary}}</p>
        <p><strong>复杂度说明：</strong>${{info.complexity}}</p>
        <p><strong>展示建议：</strong>${{info.tip}}</p>
    `;
}}

document.addEventListener("click", (event) => {{
    const button = event.target.closest("[data-algorithm]");
    if (!button) {{
        return;
    }}
    renderExplanation(button.dataset.algorithm);
}});

filterInput?.addEventListener("input", (event) => {{
    const keyword = event.target.value.trim().toLowerCase();
    cards.forEach((card) => {{
        const name = (card.dataset.name || "").toLowerCase();
        card.style.display = !keyword || name.includes(keyword) ? "" : "none";
    }});
}});

shuffleButton?.addEventListener("click", () => {{
    const visibleCards = cards.filter((card) => card.style.display !== "none");
    const candidates = visibleCards.length ? visibleCards : cards;
    const randomCard = candidates[Math.floor(Math.random() * candidates.length)];
    const name = randomCard?.dataset.name;
    if (name) {{
        renderExplanation(name);
        randomCard.scrollIntoView({{ behavior: "smooth", block: "center" }});
    }}
}});

renderExplanation({json.dumps(features[0], ensure_ascii=False)});
"""

    files = {
        "index": target_dir / "index.html",
        "styles": target_dir / "styles.css",
        "script": target_dir / "app.js",
    }

    files["index"].write_text(html, encoding="utf-8")
    files["styles"].write_text(css, encoding="utf-8")
    files["script"].write_text(js, encoding="utf-8")

    return {
        "project_name": project_name,
        "slug": project_slug,
        "output_dir": str(target_dir),
        "entrypoint": str(files["index"]),
        "files": [str(path) for path in files.values()],
    }


def validate_static_web_app_bundle(entry_file: str = "artifacts/web/index.html") -> dict:
    """对静态网页交付物做基础结构校验。"""
    index_path = resolve_read_path(entry_file)
    if not index_path.exists():
        return {"passed": False, "issues": [f"入口文件不存在: {index_path}"], "checked_files": []}

    html = index_path.read_text(encoding="utf-8")
    issues = []
    checked_files = [str(index_path)]

    required_snippets = [
        "<meta name=\"viewport\"",
        "<main",
        "styles.css",
        "app.js",
    ]
    for snippet in required_snippets:
        if snippet not in html:
            issues.append(f"index.html 缺少关键片段: {snippet}")

    asset_matches = re.findall(r"""(?:href|src)=["'](.+?)["']""", html)
    for relative_asset in asset_matches:
        if relative_asset.startswith(("http://", "https://", "#", "data:")):
            continue
        asset_path = (index_path.parent / relative_asset).resolve()
        if not asset_path.exists():
            issues.append(f"缺少被引用的资源文件: {relative_asset}")
        else:
            checked_files.append(str(asset_path))

    if "algorithm-card" not in html:
        issues.append("页面未检测到算法展示卡片结构")

    return {
        "passed": not issues,
        "issues": issues,
        "checked_files": checked_files,
        "entrypoint": str(index_path),
    }


@tool
def scaffold_static_web_app(
    project_name: str,
    summary: str,
    feature_list: str = "",
    output_dir: str = "artifacts/web",
) -> str:
    """
    快速生成一个结构完整、视觉效果较好的静态前端网页交付物。
    特别适合课程展示页、算法展示页、产品原型页等任务。

    Args:
        project_name: 页面或项目名称
        summary: 页面简介或展示目标
        feature_list: 需要展示的功能或主题，逗号分隔
        output_dir: 输出目录，默认写入 artifacts/web
    """
    bundle = build_static_web_app_bundle(project_name, summary, feature_list, output_dir)
    return json.dumps(bundle, ensure_ascii=False, indent=2)


@tool
def validate_static_web_app(entry_file: str = "artifacts/web/index.html") -> str:
    """
    校验静态网页交付物是否具备入口文件、资源引用和基础页面结构。

    Args:
        entry_file: 入口 HTML 文件路径
    """
    return json.dumps(validate_static_web_app_bundle(entry_file), ensure_ascii=False, indent=2)
