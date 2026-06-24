from __future__ import annotations

import json
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


ANALYSIS_JSON = Path("examples/mingli_5agents/reports/linfan_20260624_clean.analysis.json")
OUT_MD = Path("examples/mingli_5agents/reports/linfan_20260624_interpreted_annual_zh.report.md")
OUT_PDF = OUT_MD.with_suffix(".pdf")
KNOWN_EVENTS_JSON = Path("examples/mingli_5agents/reports/linfan_major_events.json")

STEM = {
    "Jia": "甲",
    "Yi": "乙",
    "Bing": "丙",
    "Ding": "丁",
    "Wu": "戊",
    "Ji": "己",
    "Geng": "庚",
    "Xin": "辛",
    "Ren": "壬",
    "Gui": "癸",
}
BRANCH = {
    "Zi": "子",
    "Chou": "丑",
    "Yin": "寅",
    "Mao": "卯",
    "Chen": "辰",
    "Si": "巳",
    "Wu": "午",
    "Wei": "未",
    "Shen": "申",
    "You": "酉",
    "Xu": "戌",
    "Hai": "亥",
}

TEN_GOD = {
    "peer": "比劫",
    "resource": "印星",
    "expression": "食伤",
    "wealth": "财星",
    "authority": "官杀",
}

ELEMENT = {
    "Wood": "木",
    "Fire": "火",
    "Earth": "土",
    "Metal": "金",
    "Water": "水",
}

BRANCH_ELEMENT = {
    "Zi": "Water",
    "Chou": "Earth",
    "Yin": "Wood",
    "Mao": "Wood",
    "Chen": "Earth",
    "Si": "Fire",
    "Wu": "Fire",
    "Wei": "Earth",
    "Shen": "Metal",
    "You": "Metal",
    "Xu": "Earth",
    "Hai": "Water",
}

NATAL_BRANCHES = {
    "年支": "Wu",
    "月支": "Chen",
    "日支": "Wu",
    "时支": "Mao",
}

PILLAR_LABEL = {
    "year": "年",
    "month": "月",
    "day": "日",
    "hour": "时",
}


MONTH_BRANCHES = [
    ("正月", "Yin"),
    ("二月", "Mao"),
    ("三月", "Chen"),
    ("四月", "Si"),
    ("五月", "Wu"),
    ("六月", "Wei"),
    ("七月", "Shen"),
    ("八月", "You"),
    ("九月", "Xu"),
    ("十月", "Hai"),
    ("冬月", "Zi"),
    ("腊月", "Chou"),
]

CLASH = {
    frozenset(("Zi", "Wu")): "冲",
    frozenset(("Chou", "Wei")): "冲",
    frozenset(("Yin", "Shen")): "冲",
    frozenset(("Mao", "You")): "冲",
    frozenset(("Chen", "Xu")): "冲",
    frozenset(("Si", "Hai")): "冲",
}

COMBINE = {
    frozenset(("Zi", "Chou")): "合",
    frozenset(("Yin", "Hai")): "合",
    frozenset(("Mao", "Xu")): "合",
    frozenset(("Chen", "You")): "合",
    frozenset(("Si", "Shen")): "合",
    frozenset(("Wu", "Wei")): "合",
}

HARM = {
    frozenset(("Zi", "Wei")): "害",
    frozenset(("Chou", "Wu")): "害",
    frozenset(("Yin", "Si")): "害",
    frozenset(("Mao", "Chen")): "害",
    frozenset(("Shen", "Hai")): "害",
    frozenset(("You", "Xu")): "害",
}

PUNISH = {
    frozenset(("Zi", "Mao")): "刑",
    frozenset(("Yin", "Si")): "刑",
    frozenset(("Si", "Shen")): "刑",
    frozenset(("Chou", "Xu")): "刑",
    frozenset(("Xu", "Wei")): "刑",
    frozenset(("Chou", "Wei")): "刑",
}

MESSAGE = {
    "stronger money-management and asset-allocation theme; avoid leverage.": "资源、钱财和家庭责任被放大，宜稳住预算，不宜贪快。",
    "cash flow can move quickly; require budgets and written terms.": "现金流和支出节奏容易变快，凡事要留书面凭据。",
    "steady finances favor planning over speculation.": "财务宜稳，靠计划和积累，不靠投机。",
    "keep compliance and reporting rhythm clear.": "规则、汇报和流程要讲清楚，不能含糊。",
    "rules, title, audits, leadership, or institutional pressure become central.": "规矩、师长、领导或制度压力会变明显。",
    "authority relationships can improve through preparation and evidence.": "面对权威人物，准备充分就容易过关。",
    "career choices are tied to revenue, assets, operations, or family duties.": "事业选择会和收入、资产、运营、家庭责任绑在一起。",
    "career improves through consistent execution.": "事业靠稳定执行改善，不靠一时冲劲。",
    "career advancement depends on discipline, contracts, and role clarity.": "事业推进要靠纪律、合同和角色边界。",
    "career push is strong but should be paced to avoid conflict.": "推动力强，但要放慢节奏，避免硬碰硬。",
    "study should support immediate work needs.": "学习要服务当前阶段的现实需要。",
    "learning is useful when converted into a practical system.": "学习能变成方法和习惯时最有用。",
    "best suited for study, credentials, research, travel, or strategic review.": "适合学习、考证、研究、出行规划或复盘。",
    "marriage and romantic issues may connect with money, home, or duty.": "感情容易和金钱、家庭、责任牵连在一起。",
    "relationships benefit from predictable communication.": "关系要靠稳定、清楚、可预期的沟通维持。",
    "direct speech can heat up conflict; slow down before decisions.": "说话太直会激化矛盾，重大决定前要慢。",
    "friends and partners are active; choose collaborators carefully.": "朋友和合作对象活跃，但必须慎选。",
    "networking is useful when roles are explicit.": "人际合作有用，但角色要先说清楚。",
    "competition and comparison can increase.": "竞争和比较感增加，容易消耗心力。",
    "visibility can attract support if communication stays measured.": "表达有分寸时，更容易获得支持。",
    "leadership ties improve through reliability.": "和领导、客户、机构的关系，靠可靠执行改善。",
    "leaders, managers, clients, or regulators carry more weight.": "领导、客户、管理者或规则要求的分量会提高。",
    "children, students, juniors, or creative outputs require attention.": "子女、学生、晚辈或创作输出需要更多关注。",
    "family responsibility and practical support are highlighted.": "家庭责任和实际支持被强调。",
    "family ties need steady time and clear expectations.": "家庭关系需要稳定投入，也需要把期待说清楚。",
}


def ganzhi(value: str) -> str:
    for key, label in sorted(STEM.items(), key=lambda item: -len(item[0])):
        if value.startswith(key):
            return label + BRANCH.get(value[len(key) :], value[len(key) :])
    return value


def split_ganzhi(value: str) -> tuple[str, str]:
    for key in sorted(STEM, key=len, reverse=True):
        if value.startswith(key):
            return key, value[len(key) :]
    return value, ""


def branch_label(value: str) -> str:
    return BRANCH.get(value, value)


def element_label(value: str) -> str:
    return ELEMENT.get(value, value)


def ten_god_label(value: str) -> str:
    return TEN_GOD.get(value, value)


def branch_relation(a: str, b: str) -> str:
    key = frozenset((a, b))
    if key in CLASH:
        return CLASH[key]
    if key in PUNISH:
        return PUNISH[key]
    if key in HARM:
        return HARM[key]
    if key in COMBINE:
        return COMBINE[key]
    if a == b:
        return "伏吟"
    return ""


def relation_notes(annual_branch: str, luck_branch: str = "") -> list[str]:
    notes: list[str] = []
    for palace, natal_branch in NATAL_BRANCHES.items():
        rel = branch_relation(annual_branch, natal_branch)
        if rel:
            notes.append(f"流年{branch_label(annual_branch)}与原局{palace}{branch_label(natal_branch)}成{rel}")
    if luck_branch:
        rel = branch_relation(annual_branch, luck_branch)
        if rel:
            notes.append(f"流年{branch_label(annual_branch)}与大运{branch_label(luck_branch)}成{rel}")
    return notes


def flow_note(row: dict[str, object]) -> str:
    elements = row.get("elements", {})
    evidence = row.get("bazi_evidence", {})
    if not isinstance(elements, dict) or not isinstance(evidence, dict):
        return "五行流通以年度干支为主，仍需结合事实复盘。"
    stem_el = element_label(str(elements.get("stem", "")))
    branch_el = element_label(str(elements.get("branch", "")))
    useful_state = str(evidence.get("useful_state", ""))
    if useful_state == "useful_element_activated":
        return f"{stem_el}透、{branch_el}动，金的规则和财务意识被带出来，做事宜立规矩、留凭据。"
    if useful_state == "dominant_element_reinforced":
        return f"{stem_el}透、{branch_el}动，火势被推高，行动力强，但也容易急、硬、冲。"
    if stem_el == "水" or branch_el == "水":
        return f"{stem_el}透、{branch_el}动，水来制火，压力、考试、制度或上级要求会变得明显。"
    if stem_el == "木" or branch_el == "木":
        return f"{stem_el}透、{branch_el}动，木生火，学习、想法、长辈助力会增加，也会让主观性变强。"
    if stem_el == "土" or branch_el == "土":
        return f"{stem_el}透、{branch_el}动，火生土，表达、输出、消耗和家庭杂务会被放大。"
    return f"{stem_el}透、{branch_el}动，年度重点要看现实条件如何承接。"


def month_relation_notes(annual_branch: str, luck_branch: str = "") -> list[str]:
    scored: list[tuple[int, str]] = []
    for month_name, month_branch in MONTH_BRANCHES:
        pieces: list[str] = []
        rel_year = branch_relation(month_branch, annual_branch)
        if rel_year:
            pieces.append(f"与流年{branch_label(annual_branch)}成{rel_year}")
        rel_day = branch_relation(month_branch, "Wu")
        if rel_day:
            pieces.append(f"触动日支午火为{rel_day}")
        if luck_branch:
            rel_luck = branch_relation(month_branch, luck_branch)
            if rel_luck:
                pieces.append(f"牵动大运{branch_label(luck_branch)}为{rel_luck}")
        if pieces:
            severity = 3 if any(("冲" in p or "刑" in p) for p in pieces) else 2
            scored.append((severity, f"{month_name}{branch_label(month_branch)}月" + "、".join(pieces)))
    scored.sort(key=lambda item: item[0], reverse=True)
    return [note for _, note in scored[:3]]


def domain_sentence(age: int, category: str, intensity: str, tg_stem: str, tg_branch: str) -> str:
    gods = f"天干{ten_god_label(tg_stem)}、地支{ten_god_label(tg_branch)}"
    if age <= 6:
        return f"{gods}。落到童年，就是看体质、脾气、父母照顾和家庭稳定，不作成人成败判断。"
    if age <= 17:
        return f"{gods}。落到读书阶段，重点看学习方法、纪律、身体发育和同伴影响。"
    if age <= 24:
        return f"{gods}。这是从读书转入社会的阶段，重点看专业方向、技能、考试证书、人际边界和早期感情。"
    if category == "wealth":
        return f"{gods}，财务和资源主题明显，适合谈收入结构、资产安排、家庭责任，但忌口头承诺和冲动担保。"
    if category == "authority":
        return f"{gods}，规则、职级、上级、资质和制度压力是主线，做得稳会有位置，顶得硬则容易冲突。"
    if category == "expression":
        return f"{gods}，表达、输出、名声和项目推进被放大，适合主动做事，但要防急躁失言。"
    if category == "friends":
        return f"{gods}，朋友、同业、合作与竞争同时增强，能成事，也容易因边界不清而消耗。"
    return f"{gods}，更偏学习、复盘、移动和方向调整，适合补方法、补证据、补系统。"


def msg(value: str) -> str:
    return MESSAGE.get(value, "这一年宜稳住节奏，先看现实条件，再做决定。")


def annual_by_year(rows: list[dict[str, object]]) -> dict[int, dict[str, object]]:
    return {int(row["year"]): row for row in rows}


def load_known_events() -> list[dict[str, object]]:
    if not KNOWN_EVENTS_JSON.exists():
        return []
    try:
        data = json.loads(KNOWN_EVENTS_JSON.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return []
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if isinstance(data, dict) and isinstance(data.get("events"), list):
        return [item for item in data["events"] if isinstance(item, dict)]
    return []


def event_calibration_section(events: list[dict[str, object]]) -> list[str]:
    if not events:
        return [
            "## 事实校准状态",
            "- 当前版本尚未写入真实重大事件，所以以下逐年判断仍属于命盘推演版。",
            "- 等用户提供年份、月份、事件类型和结果后，应回到格局、大运、流年三层重新校准，不能用理论压过事实。",
            "",
        ]
    lines = [
        "## 事实校准记录",
        "- 下列真实事件已作为校准依据。校准原则是事实优先，若事实与原断语冲突，应回头修正格局判断和用神保护链。",
    ]
    for item in events:
        year = item.get("year", "")
        month = item.get("month", "")
        event = item.get("event", "")
        impact = item.get("impact", "")
        month_text = f"{month}月" if month else "月份不详"
        impact_text = f"，结果为{impact}" if impact else ""
        lines.append(f"- {year}年，{month_text}，{event}{impact_text}。")
    lines.append("")
    return lines


def compact_year(row: dict[str, object]) -> str:
    age = int(row["age"])
    year = int(row["year"])
    stem, branch = split_ganzhi(str(row["ganzhi"]))
    gz = ganzhi(str(row["ganzhi"]))
    evidence = row.get("bazi_evidence", {})
    if not isinstance(evidence, dict):
        evidence = {}
    ten_gods = evidence.get("annual_ten_gods", {})
    if not isinstance(ten_gods, dict):
        ten_gods = {}
    luck = evidence.get("active_major_luck", {})
    if not isinstance(luck, dict):
        luck = {}
    luck_stem, luck_branch = split_ganzhi(str(luck.get("ganzhi", "")))
    luck_text = "幼年起运前后"
    if luck.get("ganzhi"):
        luck_text = f"行{ganzhi(str(luck.get('ganzhi')))}大运"
    relations = relation_notes(branch, luck_branch)
    relation_text = "；".join(relations[:2]) if relations else "地支未见强烈刑冲，主线较偏渐进"
    months = month_relation_notes(branch, luck_branch)
    month_text = "；".join(months) if months else "关键月令以火旺和金旺月份观察状态起伏"
    category = str(row.get("category", "learning"))
    intensity = str(row.get("intensity", "moderate"))
    domain = domain_sentence(
        age,
        category,
        intensity,
        str(ten_gods.get("stem", "")),
        str(ten_gods.get("branch", "")),
    )
    flow = flow_note(row)
    if age <= 17:
        flow = flow.replace("金的规则和财务意识", "金的规矩感和自我管理")
    match = ""
    matches = evidence.get("natal_pillar_matches", [])
    if isinstance(matches, list) and matches:
        pillars = "、".join(
            PILLAR_LABEL.get(str(item.get("pillar", "")), str(item.get("pillar", "")))
            for item in matches
            if isinstance(item, dict)
        )
        if pillars:
            match = f"原局{pillars}柱被同柱触发，事情容易落到本人状态或家庭旧模式上。"
    caution = ""
    if intensity == "high-volatility":
        caution = "此年波动偏高，宜慢签约、慢承诺、慢表态。"
    elif intensity == "constructive":
        caution = "此年有建设性，越按规则做，越容易留下成果。"
    else:
        caution = "此年不宜求快，适合顺势调整。"
    pieces = [
        f"{year}年（{age}岁，{gz}）：{luck_text}。",
        flow,
        domain,
        relation_text + "。",
        f"关键月份看：{month_text}。",
    ]
    if match:
        pieces.append(match)
    pieces.append(caution)
    return "- " + "".join(pieces)


def build_report() -> str:
    analysis = json.loads(ANALYSIS_JSON.read_text(encoding="utf-8-sig"))
    final = analysis["result"]["final_report"]
    bazi = final["bazi_profile"]
    rows = final["annual_luck"]["rows"]
    by_year = annual_by_year(rows)
    known_events = load_known_events()

    parts: list[str] = []
    parts.extend(
        [
            "# 林凡命理研判报告（叙述版）",
            "",
            "## 基本资料",
            "- 姓名：林凡。",
            "- 性别：男。",
            "- 出生时间：一九七八年四月十四日早上六点五十分。",
            "- 出生地点：福建省三明市。",
            "- 本报告覆盖一九七八年至二零二六年。",
            "",
            "## 先说结论",
            "- 这个命盘火气明显，性格底色不是慢吞吞、被动型，而是有冲劲、要表达、要推动事情的人。",
            "- 优点是行动快、热度足、遇事不太愿意长期拖着。缺点也明显，容易急，容易凭一股劲先做，后面再补规则。",
            "- 命盘最需要补的是金的气质，也就是规则、边界、合同、证据、冷静判断。越到中年，越不能只靠热情，要靠制度和复盘。",
            "- 此人一生不是单纯求安稳的路数，适合在输出、管理、项目推进、公开表达、资源整合中找位置。",
            "- 真正的压力点在关系和责任：夫妻家庭、合作边界、领导客户、钱和责任经常会绑在一起，不能只讲情面。",
            "",
        ]
    )
    parts.extend(event_calibration_section(known_events))
    parts.extend(
        [
            "## 命盘总断",
            f"- 八字四柱为：年柱{ganzhi(bazi['pillars']['year'])}，月柱{ganzhi(bazi['pillars']['month'])}，日柱{ganzhi(bazi['pillars']['day'])}，时柱{ganzhi(bazi['pillars']['hour'])}。",
            "- 日主为丙火。丙火像太阳，重视存在感、表达感和推动力。这样的人不怕做事，但怕事情没有规则、没有边界。",
            "- 火旺则人容易有主见，也容易不服软。若能用规则约束自己，反而能把冲劲变成执行力；若缺少约束，就容易急躁、顶撞、消耗人际。",
            "- 用神偏金。通俗讲，金代表规矩、专业、合同、取舍、财务纪律。此人越重视这些，运势越容易走稳。",
            "",
            "## 人生阶段判断",
            "",
            "### 童年阶段：零岁至六岁",
            "- 童年阶段主要看健康、父母照顾、家庭环境和早期性格。判断重点应落在照顾是否稳定、作息是否规律、孩子是否容易急躁。",
            "- 早年火气不弱，孩子会比较有反应、有脾气，不是特别安静顺从的类型。父母越用稳定规则引导，越容易养成好习惯。",
            "- 这个阶段最怕作息乱、照顾方式忽冷忽热。家里如果节奏稳定，孩子的安全感会更好。",
            "",
            "### 学龄阶段：七岁至十七岁",
            "- 学龄期重点在学业习惯、身体发育、父母管教和同学关系。这个阶段最该看规矩感、专注力和学习方法。",
            "- 十二岁前后规则感会变重要，适合培养纪律、作息和学习方法。若只靠兴趣，不靠方法，成绩和状态容易波动。",
            "- 这一阶段容易受同学朋友影响，父母需要管住边界，但不能只压制，要讲清楚规则和原因。",
            "",
            "### 青年阶段：十八岁至二十四岁",
            "- 青年期开始从读书转向社会化，重点是专业技能、方向选择、人际边界和感情萌芽。",
            "- 这段时间不宜太早被情绪和人情牵着走。越能把技能练扎实，后面的事业越有底。",
            "- 二十二岁前后规则和现实压力会增强，适合明确专业路线、资格能力和工作纪律。",
            "",
            "### 成年成事阶段：二十五岁至四十四岁",
            "- 这二十年是事业、人际、家庭责任逐步加重的阶段。此人不是完全靠贵人托举的命，更像靠持续输出和实际执行积累位置。",
            "- 三十岁以后，钱、事业和家庭责任会互相牵连。很多选择不是单纯喜欢不喜欢，而是要看收益、责任、家庭和长期稳定。",
            "- 关系上要特别注意边界。朋友、合作、伴侣、客户之间不能混成一团，否则容易出现误会和压力。",
            "",
            "### 当前阶段：四十五岁以后",
            "- 四十五岁以后进入责任加重、资源重整的阶段。过去靠冲劲能解决的事，现在更需要规则、合同、团队和财务纪律。",
            "- 二零二五到二零三四这步运，重点会落到资源、规则、合作和长期资产。此阶段做对了，能把经验变成稳定成果；做急了，则容易被财务、人情和合同拖住。",
            "- 二零二六年是波动偏高的一年。要少做情绪化承诺，尤其是钱、合作、家庭责任和公开表达方面，要先写清楚、讲清楚。",
            "",
            "## 主题判断",
            "",
            "### 财运",
            "- 此人财运不是靠侥幸横财，而是靠资源管理、项目执行、专业能力和长期积累。",
            "- 财务上最忌冲动加杠杆、替人背责任、口头承诺太多。越到中年，越要把账、合同、权限分清。",
            "- 二零二六年现金流变化会比较快，宜保守预算，不宜大进大出。",
            "",
            "### 事业",
            "- 事业适合走输出型、管理型、项目型路线。能讲、能推、能交付，是优势。",
            "- 但这个命盘不能长期靠热情做事，必须建立制度。只要流程清楚、角色清楚，事业就能稳住。",
            "- 二零二六年适合展示能力、推进项目、整理资源，但不适合和领导客户硬碰硬。",
            "",
            "### 官运与规则",
            "- 官运在这里更像规则、职级、制度、领导关系和组织压力。",
            "- 此人遇到规则并不一定差，反而需要规则来成事。怕的是心里不服、嘴上太直，导致本来能过的关变成冲突。",
            "- 面对上级、客户、机构，证据越清楚，话越克制，结果越好。",
            "",
            "### 婚恋与家庭",
            "- 感情不是轻飘飘的桃花型，而是容易和责任、钱、家庭安排绑在一起。",
            "- 夫妻或亲密关系中，最怕一方只讲情绪，另一方只讲道理。此人要学会放慢语气，不要用强表达压人。",
            "- 中年后家庭责任感会更重，子女、晚辈、家庭支持会成为绕不开的主题。",
            "",
            "### 朋友与合作",
            "- 朋友和合作机会不少，但不能谁来都接。合作前必须讲角色、利益、退出方式。",
            "- 此人容易因为讲义气或一时热情答应太多，后面反而被拖累。",
            "- 真正适合的伙伴，是能守规则、能按约定交付的人。",
            "",
            "## 逐年流年研判",
            "",
            "### 童年与读书期",
        ]
    )
    for year in range(1978, 1996):
        parts.append(compact_year(by_year[year]))
    parts.extend(["", "### 青年到事业起步期"])
    for year in range(1996, 2008):
        parts.append(compact_year(by_year[year]))
    parts.extend(["", "### 事业与家庭责任加重期"])
    for year in range(2008, 2027):
        parts.append(compact_year(by_year[year]))
    parts.extend(
        [
            "",
            "## 最后提醒",
            "- 这份报告可以作为复盘和提醒，但不能替代现实调查和专业意见。",
            "- 凡涉及投资、医疗、法律、婚姻等重大事项，请以事实、合同、检查结果和专业人士意见为准。",
        ]
    )
    return "\n".join(parts) + "\n"


def escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build_pdf(markdown: str) -> None:
    pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
    styles = getSampleStyleSheet()
    base = ParagraphStyle(
        "Base",
        parent=styles["Normal"],
        fontName="STSong-Light",
        fontSize=10,
        leading=15,
        alignment=TA_LEFT,
        wordWrap="CJK",
    )
    h1 = ParagraphStyle("H1", parent=base, fontSize=18, leading=24, spaceAfter=8, textColor=colors.HexColor("#222222"))
    h2 = ParagraphStyle("H2", parent=base, fontSize=14, leading=19, spaceBefore=8, spaceAfter=5, textColor=colors.HexColor("#333333"))
    h3 = ParagraphStyle("H3", parent=base, fontSize=12, leading=16, spaceBefore=5, spaceAfter=3, textColor=colors.HexColor("#444444"))
    bullet = ParagraphStyle("Bullet", parent=base, leftIndent=9, firstLineIndent=-7)
    story = []
    for line in markdown.splitlines():
        if not line.strip():
            story.append(Spacer(1, 4))
        elif line.startswith("# "):
            story.append(Paragraph(escape(line[2:]), h1))
        elif line.startswith("## "):
            story.append(Paragraph(escape(line[3:]), h2))
        elif line.startswith("### "):
            story.append(Paragraph(escape(line[4:]), h3))
        elif line.startswith("- "):
            story.append(Paragraph("· " + escape(line[2:]), bullet))
        else:
            story.append(Paragraph(escape(line), base))
    doc = SimpleDocTemplate(
        str(OUT_PDF),
        pagesize=A4,
        rightMargin=14 * mm,
        leftMargin=14 * mm,
        topMargin=14 * mm,
        bottomMargin=14 * mm,
        title="林凡命理研判报告",
    )
    doc.build(story)


def main() -> None:
    markdown = build_report()
    OUT_MD.write_text(markdown, encoding="utf-8")
    build_pdf(markdown)
    print(OUT_MD.resolve())
    print(OUT_PDF.resolve())
    print(
        "letters",
        len(re.findall(r"[A-Za-z]", markdown)),
        "half_question",
        markdown.count("?"),
        "full_question",
        markdown.count("？"),
        "code_fences",
        markdown.count("```"),
    )


if __name__ == "__main__":
    main()
