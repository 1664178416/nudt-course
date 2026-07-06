from __future__ import annotations

import json
import re
from pathlib import Path

import fitz


ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "_work"
OCR = WORK / "ocr"
FINAL = ROOT / "最终输出"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def norm(s: str) -> str:
    return re.sub(r"\s+", "", s)


def print_page_from_title(title: str) -> int | None:
    if "／" not in title:
        return None
    tail = title.rsplit("／", 1)[1]
    digits = "".join(ch for ch in tail if ch.isdigit())
    return int(digits) if digits else None


def get_textbook_toc():
    textbook = max(
        [p for p in ROOT.glob("*.pdf") if p.name != "Solutions.pdf"],
        key=lambda p: p.stat().st_size,
    )
    doc = fitz.open(str(textbook))
    entries = []
    for _level, title, page in doc.get_toc():
        clean = title.replace("\u3000", " ").strip()
        entries.append(
            {
                "title": clean,
                "pdf_page": page,
                "print_page": print_page_from_title(clean),
            }
        )
    return entries


TOC = get_textbook_toc()


def find_toc(*subs: str):
    nsubs = [norm(s) for s in subs]
    for entry in TOC:
        title = norm(entry["title"])
        if all(s in title for s in nsubs):
            return entry
    raise KeyError(f"TOC entry not found: {subs}")


def toc_by_print(print_page: int, contains: str | None = None):
    for entry in TOC:
        if entry["print_page"] != print_page:
            continue
        if contains and norm(contains) not in norm(entry["title"]):
            continue
        return entry
    raise KeyError(f"TOC print page not found: {print_page}, {contains}")


def find_chapter_exercises(chapter: int):
    start = norm(f"{chapter} ")
    seen_chapter = False
    for entry in TOC:
        title = norm(entry["title"])
        if title.startswith(start):
            seen_chapter = True
        elif seen_chapter and title.startswith("练习题"):
            return entry
    raise KeyError(f"exercise TOC not found for chapter {chapter}")


def source_question_pages():
    pages = {i: None for i in range(1, 51)}
    offsets = {1: 5, 2: 7, 3: 11, 4: 15, 5: 20, 6: 26, 7: 31, 8: 36, 9: 41, 10: 46}
    for fp in OCR.glob("*.paddleocr-vl.blocks.json"):
        blocks = load_json(fp)
        is_second = "26春" in fp.name
        for block in blocks:
            content = block.get("block_content") or ""
            if not content.startswith("习题"):
                continue
            content = content.replace("．", ".").replace("\\.", ".").replace(" ", "")
            match = re.match(r"习题(\d+)\.(\d+)", content)
            if not match:
                match = re.match(r"习题(\d)(\d)\.", content)
            if not match:
                continue
            chapter = int(match.group(1))
            number = int(match.group(2))
            idx = number if is_second else offsets.get(chapter, 0) + number
            if 1 <= idx <= 50 and pages[idx] is None:
                pages[idx] = block.get("page")
    pages[5] = pages[5] or 1
    # OCR puts the tail of 6.1 and the start of 6.2 in the same text block after
    # the page marker, so the generic "block starts with 习题" rule misses 6.2.
    pages[28] = 5
    return pages


def ref(key, src, no, tb, loc, loc2=None, exloc=None, sol=None, notes=""):
    return {
        "key": key,
        "src": src,
        "no": no,
        "tb": tb,
        "loc": loc,
        "loc2": loc2,
        "exloc": exloc,
        "sol": sol,
        "notes": notes,
    }


def build_refs():
    ex1 = find_chapter_exercises(1)
    ex2 = find_chapter_exercises(2)
    ex4 = find_chapter_exercises(4)
    ex7 = find_chapter_exercises(7)
    ex17 = find_chapter_exercises(17)
    return {
        1: ref("题库二-习题1.1", "题库二", "习题1.1", "第6章 6.3 行为策略均衡；定理6.16", find_toc("6.3"), notes="教材正文定理；用 Nash 存在性定理 + Kuhn 定理证明。"),
        2: ref("题库二-习题1.2", "题库二", "习题1.2", "第7章 7.1 子博弈完美均衡；定理7.5", find_toc("7.1"), notes="不对应 Solutions 7.5；Solutions 7.5 是另一个讨价还价例题。"),
        3: ref("题库二-习题1.3", "题库二", "习题1.3", "第7章 7.3 完美均衡；定理7.34；教材练习7.34", find_toc("7.3"), exloc=ex7, sol="7.35", notes="英文 Solutions 编号与中文练习编号有偏移，内容匹配扰动行为策略逼近。"),
        4: ref("题库二-习题1.4", "题库二", "习题1.4", "第9章 9.1 不完全信息的奥曼模型以及知识；第11章 11.1 信念层级", find_toc("9.1"), loc2=find_toc("11.1"), notes="正文定义整理。"),
        5: ref("题库二-习题1.5", "题库二", "习题1.5", "第9章 9.4 不完全信息博弈的海萨伊模型", find_toc("9.4"), notes="题库给定两状态收益表，按 Harsanyi 转换直接作答。"),
        6: ref("题库一-习题1.1", "题库一", "习题1.1", "第1章 1.1 国际象棋博弈的简要描述；1.2 分析和结果；定理1.4", find_toc("1.1"), loc2=find_toc("1.2"), notes="题干是构建模型并证明三择一定理，不是教材练习1.1。"),
        7: ref("题库一-习题1.2", "题库一", "习题1.2", "第3章 3.4 大卫·盖尔博弈(Chomp)；定理3.16", find_toc("3.4"), notes="正文策略窃取证明。"),
        8: ref("题库一-习题2.1", "题库一", "习题2.1", "第2章 2.5 效用函数和仿射变换", find_toc("2.5")),
        9: ref("题库一-习题2.2", "题库一", "习题2.2", "第2章 2.3 效用理论的公理；2.4 效用函数的特征定理", find_toc("2.3"), loc2=find_toc("2.4")),
        10: ref("题库一-习题2.3", "题库一", "习题2.3", "第2章 2.5 效用函数和仿射变换；教材练习2.21/2.22同型", find_toc("2.5"), exloc=ex2, sol="2.21"),
        11: ref("题库一-习题2.4", "题库一", "习题2.4", "第2章 2.7 风险态度", find_toc("2.7")),
        12: ref("题库一-习题3.1", "题库一", "习题3.1", "第3章 3.3 博弈树：无随机行动、完美信息扩展式模型", find_toc("3.3")),
        13: ref("题库一-习题3.2", "题库一", "习题3.2", "第3章 3.5 包含随机行动的博弈；结合3.3模型", find_toc("3.5"), loc2=find_toc("3.3")),
        14: ref("题库一-习题3.3", "题库一", "习题3.3", "第3章 3.6 不完全信息博弈；结合3.3模型", find_toc("3.6"), loc2=find_toc("3.3")),
        15: ref("题库一-习题3.4", "题库一", "习题3.4", "第3章 3.5 包含随机行动的博弈；3.6 不完全信息博弈", find_toc("3.5"), loc2=find_toc("3.6")),
        16: ref("题库一-习题4.1", "题库一", "习题4.1", "第4章练习4.18 三人博弈", ex4, sol="4.18", notes="Solutions 4.18 内容匹配该三人矩阵，结论无纯策略纳什均衡。"),
        17: ref("题库一-习题4.2", "题库一", "习题4.2", "第4章 4.8 稳定性：纳什均衡；有利偏离集 Prof_i", find_toc("4.8")),
        18: ref("题库一-习题4.3", "题库一", "习题4.3", "第4章 4.8 稳定性：纳什均衡；最佳反应定义；教材练习4.15", find_toc("4.8"), exloc=ex4, sol="4.15"),
        19: ref("题库一-习题4.4", "题库一", "习题4.4", "第4章 4.11 剔除劣策略的效果；推论4.36", find_toc("4.11")),
        20: ref("题库一-习题4.5", "题库一", "习题4.5", "第4章 4.9 纳什均衡的特征；Cournot 双寡头例", find_toc("4.9")),
        21: ref("题库一-习题5.1", "题库一", "习题5.1", "第4章 4.14 单位正方形博弈；连续策略计算", find_toc("4.14")),
        22: ref("题库一-习题5.2", "题库一", "习题5.2", "第5章 5.2 计算混合策略均衡", find_toc("5.2"), notes="不对应 Solutions 5.27；该条是另一道2×4支持枚举题。本题按题库矩阵直接求解。"),
        23: ref("题库一-习题5.3", "题库一", "习题5.3", "第5章 5.2 计算混合策略均衡；支持枚举法", find_toc("5.2")),
        24: ref("题库一-习题5.4", "题库一", "习题5.4", "第4章 4.14.2 方格二人非零和博弈", find_toc("4.14"), notes="教材正文例题，函数与题库一致；不用 Solutions 4.42。"),
        25: ref("题库一-习题5.5", "题库一", "习题5.5", "第4章 4.14.1 单位正方形二人零和博弈", find_toc("4.14"), notes="教材正文例题，函数与题库一致；不用 Solutions 4.41。"),
        26: ref("题库一-习题5.6", "题库一", "习题5.6", "第5章 5.8 演化稳定策略；定义5.50及ESS性质", find_toc("5.8")),
        27: ref("题库一-习题6.1", "题库一", "习题6.1", "第16章 16.2 策略等价", find_toc("16.2")),
        28: ref("题库一-习题6.2", "题库一", "习题6.2", "第16章 16.4 一类特殊的博弈；0-1规范化", find_toc("16.4"), notes="题库是一般证明；Solutions 17.16 是具体数值例，不作为主答案。"),
        29: ref("题库一-习题6.3", "题库一", "习题6.3", "第16章 16.4 一类特殊的博弈；0-0规范化", find_toc("16.4")),
        30: ref("题库一-习题6.4", "题库一", "习题6.4", "第16章 16.4 一类特殊的博弈；0规范博弈", find_toc("16.4")),
        31: ref("题库一-习题6.5", "题库一", "习题6.5", "第16章 16.2 策略等价；16.4 规范化与单调化", find_toc("16.2"), loc2=find_toc("16.4")),
        32: ref("题库一-习题7.1", "题库一", "习题7.1", "第17章 17.1 核的定义；17.2 平衡联盟的组合；17.3 Bondareva-Shapley定理", find_toc("17.1"), loc2=find_toc("17.3")),
        33: ref("题库一-习题7.2", "题库一", "习题7.2", "第17章 核；教材练习/英文Solutions第18章 18.8", find_toc("17  核"), exloc=ex17, sol="18.8"),
        34: ref("题库一-习题7.3", "题库一", "习题7.3", "第17章 核；三人0标准化博弈；教材练习/英文Solutions第18章 18.9", find_toc("17.1"), exloc=ex17, sol="18.9"),
        35: ref("题库一-习题7.4", "题库一", "习题7.4", "第17章 17.7 凸博弈；定理17.55/17.58", find_toc("17.7")),
        36: ref("题库一-习题7.5", "题库一", "习题7.5", "第17章 核在策略等价下的协变；16.2策略等价", find_toc("17.6"), loc2=find_toc("16.2"), notes="Solutions 18.38 不直接匹配本题。"),
        37: ref("题库一-习题8.1", "题库一", "习题8.1", "第18章 18.1-18.3 沙普利值公理与定义", find_toc("18.1"), loc2=find_toc("18.3")),
        38: ref("题库一-习题8.2", "题库一", "习题8.2", "第18章 沙普利值；英文Solutions第19章 19.14", find_toc("18.3"), sol="19.14"),
        39: ref("题库一-习题8.3", "题库一", "习题8.3", "第18章 18.3 沙普利值的定义和刻画；18.4例子", find_toc("18.3"), loc2=find_toc("18.4")),
        40: ref("题库一-习题8.4", "题库一", "习题8.4", "第18章 18.3 沙普利值定义；承载子博弈/基底博弈", find_toc("18.3"), notes="题库定义题直接由承载博弈公式求；Solutions 19.7 是另一道数值分解题。"),
        41: ref("题库一-习题8.5", "题库一", "习题8.5", "第18章 18.7 凸博弈；Shapley值属于核心", find_toc("18.7")),
        42: ref("题库一-习题9.1", "题库一", "习题9.1", "第19章 19.1 谈判集的定义", find_toc("19.1")),
        43: ref("题库一-习题9.2", "题库一", "习题9.2", "第19章 19.1 谈判集定义；单人联盟结构情形", find_toc("19.1")),
        44: ref("题库一-习题9.3", "题库一", "习题9.3", "第19章 19.2 二人博弈中的谈判集", find_toc("19.2")),
        45: ref("题库一-习题9.4", "题库一", "习题9.4", "第19章 19.3 三人博弈中的谈判集", find_toc("19.3")),
        46: ref("题库一-习题9.5", "题库一", "习题9.5", "第19章 谈判集；单人联盟结构定理", find_toc("19.1"), loc2=find_toc("19.3")),
        47: ref("题库一-习题10.1", "题库一", "习题10.1", "第20章 20.1 核仁的定义；字典顺序", find_toc("20.1"), sol="21.2"),
        48: ref("题库一-习题10.2", "题库一", "习题10.2", "第20章 20.1 核仁的定义；核仁/准核仁", find_toc("20.1")),
        49: ref("题库一-习题10.3", "题库一", "习题10.3", "第20章 20.4 计算核仁；事前核仁/准核仁", find_toc("20.4"), notes="不要直接用 Solutions 21.20：其讨论imputation集为空；本题要求在预分配集上求PN/QN。"),
        50: ref("题库一-习题10.4", "题库一", "习题10.4", "第20章 20.1 核仁定义；紧集上字典最小集", find_toc("20.1"), sol="21.3"),
    }


def build_source_map():
    maps = load_json(WORK / "source_mapping_first_pass.json")
    items = load_json(WORK / "ai_md_items.json")
    refs = build_refs()
    question_pages = source_question_pages()
    solutions = load_json(WORK / "solutions_entries.json")
    solution_map = {entry["id"]: entry for entry in solutions}

    out = []
    source_names = {
        "题库二": "题库二：26春研究生课程《博弈论》练习题库（6-9章内容）.pdf",
        "题库一": "题库一：研究生课程《博弈论》练习题库(1).pdf",
    }
    for idx in range(1, 51):
        base = maps[idx - 1]
        item = items[idx - 1]
        data = refs[idx]
        locations = []
        for field, label in [
            ("loc", "教材主位置"),
            ("loc2", "教材辅助位置"),
            ("exloc", "教材练习起始"),
        ]:
            entry = data.get(field)
            if entry:
                locations.append({**entry, "label": label})
        sol_id = data.get("sol")
        sol_entry = solution_map.get(sol_id) if sol_id else None
        out.append(
            {
                "idx": idx,
                "key": data["key"],
                "source": source_names[data["src"]],
                "source_short": data["src"],
                "question_no": data["no"],
                "question_pdf_page": question_pages.get(idx),
                "title": item["title"],
                "question": item["question"],
                "textbook_reference": data["tb"],
                "textbook_locations": locations,
                "textbook_ocr_line": base.get("ocr_line"),
                "solution_id": sol_id,
                "solutions_pdf_page": sol_entry.get("pdf_page") if sol_entry else None,
                "solutions_chapter": sol_entry.get("chapter") if sol_entry else None,
                "solution_text_en": sol_entry.get("text") if sol_entry else None,
                "notes": data.get("notes", ""),
            }
        )
    write_json(WORK / "final_source_map.json", out)
    return out


def location_text(locations):
    parts = []
    for loc in locations:
        page = f"教材PDF第{loc['pdf_page']}页"
        if loc.get("print_page") is not None:
            page += f"/印刷第{loc['print_page']}页"
        parts.append(f"{loc['label']}：{loc['title']}（{page}）")
    return "；".join(parts)


def build_index(source_map):
    lines = [
        "# 博弈论题库题源与答案位置索引",
        "",
        "说明：本索引只服务于手动核查。题库页来自 PaddleOCR-VL 识别结果；教材 PDF 页来自中文教材 PDF 书签，括号内为印刷页；答案页来自 `Solutions.pdf`。两个题库都有 `习题1.1`，所以按“题库一/题库二”分表列出。",
        "",
    ]

    groups = [
        ("题库二：26春研究生课程《博弈论》练习题库（6-9章内容）.pdf", "题库二"),
        ("题库一：研究生课程《博弈论》练习题库(1).pdf", "题库一"),
    ]
    for title, short in groups:
        lines.extend(
            [
                f"## {title}",
                "",
                "| 题号 | 题库PDF页 | 题名 | 教材PDF页 | 教材标题 | Solutions.pdf |",
                "|---|---:|---|---|---|---|",
            ]
        )
        for item in [x for x in source_map if x["source_short"] == short]:
            qpage = item["question_pdf_page"]
            sol = "无"
            if item.get("solution_id"):
                sol = f"Ex. {item['solution_id']}，PDF第{item['solutions_pdf_page']}页"
            lines.append(
                "| "
                + " | ".join(
                    [
                        item["question_no"],
                        f"第{qpage}页",
                        clean_cell(item["title"]),
                        compact_location_pages(item),
                        compact_location_titles(item),
                        sol,
                    ]
                )
                + " |"
            )
        lines.append("")

    notes = [item for item in source_map if item.get("notes")]
    if notes:
        lines.extend(
            [
                "## 特别核查备注",
                "",
                "| 题目 | 备注 |",
                "|---|---|",
            ]
        )
        for item in notes:
            lines.append(f"| {item['key']} | {clean_cell(item['notes'])} |")
        lines.append("")

    FINAL.mkdir(exist_ok=True)
    (FINAL / "博弈论题库题源与答案位置索引.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def clean_cell(text):
    return str(text).replace("|", "\\|").replace("\n", "<br>")


def compact_location_pages(item):
    parts = []
    for loc in item["textbook_locations"]:
        page = f"PDF第{loc['pdf_page']}页"
        if loc.get("print_page") is not None:
            page += f"（印刷第{loc['print_page']}页）"
        if loc["label"] == "教材练习起始":
            page = "练习：" + page
        elif loc["label"] == "教材辅助位置":
            page = "另见：" + page
        parts.append(page)
    return "<br>".join(parts)


def compact_location_titles(item):
    parts = []
    for loc in item["textbook_locations"]:
        title = loc["title"]
        if loc["label"] == "教材练习起始":
            title = "练习题起始：" + title
        elif loc["label"] == "教材辅助位置":
            title = "另见：" + title
        parts.append(clean_cell(title))
    return "<br>".join(parts)


def compact_location_text(item):
    parts = []
    for loc in item["textbook_locations"]:
        page = f"PDF第{loc['pdf_page']}页"
        if loc.get("print_page") is not None:
            page += f"/印刷第{loc['print_page']}页"
        title = loc["title"]
        if loc["label"] == "教材练习起始":
            title = "练习题起始：" + title
        elif loc["label"] == "教材辅助位置":
            title = "另见：" + title
        parts.append(f"{title}（{page}）")
    return "<br>".join(parts)


def strip_old_tail(text: str) -> str:
    text = text.strip()
    match = re.search(r"\n#{1,3}\s+", text)
    if match:
        text = text[: match.start()]
    return text.strip()


def split_ai_block(block: str):
    answer_marker = "#### 答案（满分版）"
    analysis_marker = "#### 解析（思路与易错点）"
    if answer_marker not in block:
        return block.strip(), ""
    answer_part = block.split(answer_marker, 1)[1]
    analysis_part = ""
    if analysis_marker in answer_part:
        answer_part, analysis_part = answer_part.split(analysis_marker, 1)
    return strip_old_tail(answer_part), strip_old_tail(analysis_part)


def build_detail(source_map):
    ai_items = load_json(WORK / "ai_md_items.json")
    lines = [
        "# 博弈论题库官方中文详解",
        "",
        "说明：本文件按 `题库二/题库一 + 原题号` 唯一编号，避免两个 PDF 中的 `习题1.1` 混淆。每题题干以 PaddleOCR-VL 识别结果为准；教材页码来自中文教材 PDF 书签；有真正匹配的英文官方答案时标注 `Solutions.pdf` 页码。对不匹配的英文条目（如 Solutions 7.5、5.27、21.20）不作为答案来源。",
        "",
    ]
    for item, ai in zip(source_map, ai_items):
        answer, analysis = split_ai_block(ai["block"])
        lines.append(f"## {item['key']} {item['title']}")
        lines.append("")
        lines.append("### 题源定位")
        lines.append("")
        qpage = item["question_pdf_page"]
        lines.append(f"- 题库位置：{item['source']} PDF第{qpage}页")
        lines.append(f"- 教材对应：{item['textbook_reference']}")
        for loc in item["textbook_locations"]:
            page = f"教材PDF第{loc['pdf_page']}页"
            if loc.get("print_page") is not None:
                page += f"/印刷第{loc['print_page']}页"
            lines.append(f"- {loc['label']}：{loc['title']}（{page}）")
        if item.get("solution_id"):
            lines.append(f"- 官方答案位置：Solutions.pdf Ex. {item['solution_id']}，PDF第{item['solutions_pdf_page']}页")
        else:
            lines.append("- 官方答案位置：无直接对应的 Solutions 条目；按教材正文定理、定义或题库给定数据推导。")
        if item.get("notes"):
            lines.append(f"- 校勘备注：{item['notes']}")
        lines.append("")
        lines.append("### 题目")
        lines.append("")
        lines.append(item["question"].strip())
        lines.append("")
        lines.append("### 官方中文解答")
        lines.append("")
        lines.append(answer)
        if analysis:
            lines.append("")
            lines.append("### 核对说明")
            lines.append("")
            lines.append(analysis)
        lines.append("")
    FINAL.mkdir(exist_ok=True)
    (FINAL / "博弈论题库官方中文详解.md").write_text(
        "\n".join(lines).rstrip() + "\n", encoding="utf-8"
    )
    write_json(FINAL / "final_source_map.json", source_map)


def main():
    source_map = build_source_map()
    build_index(source_map)
    build_detail(source_map)
    missing_locations = [item["key"] for item in source_map if not item["textbook_locations"]]
    missing_question_pages = [item["key"] for item in source_map if item["question_pdf_page"] is None]
    missing_textbook_pages = [
        item["key"]
        for item in source_map
        if any(loc.get("pdf_page") is None for loc in item["textbook_locations"])
    ]
    print(f"source_map={len(source_map)}")
    print(f"missing_locations={missing_locations}")
    print(f"missing_question_pages={missing_question_pages}")
    print(f"missing_textbook_pages={missing_textbook_pages}")
    for item in source_map[:8]:
        print(
            item["key"],
            "题库PDF页",
            item["question_pdf_page"],
            "教材",
            [(loc["title"], loc["pdf_page"], loc.get("print_page")) for loc in item["textbook_locations"]],
            "Solutions",
            item.get("solution_id"),
            item.get("solutions_pdf_page"),
        )


if __name__ == "__main__":
    main()
