from __future__ import annotations

import re
import shutil
import sys
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from examples.mingli_5agents.run_demo import MingliFiveAgentSystem, bootstrap_repo


OUT_DIR = Path("examples/mingli_5agents/reports")

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

MONTH_NAMES = {
    1: "一月",
    2: "二月",
    3: "三月",
    4: "四月",
    5: "五月",
    6: "六月",
    7: "七月",
    8: "八月",
    9: "九月",
    10: "十月",
    11: "十一月",
    12: "十二月",
}

CATEGORY_ZH = {
    "expression": "表达输出",
    "wealth": "资源现实",
    "authority": "规则考试",
    "learning": "学习复盘",
    "friends": "同伴合作",
}

BRANCH_RELATIONS = {
    frozenset(("Zi", "Wu")): "冲",
    frozenset(("Chou", "Wei")): "冲",
    frozenset(("Yin", "Shen")): "冲",
    frozenset(("Mao", "You")): "冲",
    frozenset(("Chen", "Xu")): "冲",
    frozenset(("Si", "Hai")): "冲",
    frozenset(("Zi", "Mao")): "刑",
    frozenset(("Yin", "Si")): "刑",
    frozenset(("Si", "Shen")): "刑",
    frozenset(("Chou", "Xu")): "刑",
    frozenset(("Xu", "Wei")): "刑",
    frozenset(("Chou", "Wei")): "刑",
    frozenset(("Zi", "Wei")): "害",
    frozenset(("Chou", "Wu")): "害",
    frozenset(("Mao", "Chen")): "害",
    frozenset(("Shen", "Hai")): "害",
    frozenset(("You", "Xu")): "害",
    frozenset(("Zi", "Chou")): "合",
    frozenset(("Yin", "Hai")): "合",
    frozenset(("Mao", "Xu")): "合",
    frozenset(("Chen", "You")): "合",
    frozenset(("Si", "Shen")): "合",
    frozenset(("Wu", "Wei")): "合",
}


def split_ganzhi(value: str) -> tuple[str, str]:
    for key in sorted(STEM, key=len, reverse=True):
        if value.startswith(key):
            return key, value[len(key) :]
    return value, ""


def gz(value: Any) -> str:
    text = str(value or "")
    stem, branch = split_ganzhi(text)
    return STEM.get(stem, stem) + BRANCH.get(branch, branch)


def branch_relation(a: str, b: str) -> str:
    if a == b and a:
        return "伏吟"
    return BRANCH_RELATIONS.get(frozenset((a, b)), "")


def branch_zh(value: str) -> str:
    return BRANCH.get(value, value)


def ten_gods(row: dict[str, Any], prefix: str = "annual") -> str:
    evidence = row.get("bazi_evidence", {})
    if not isinstance(evidence, dict):
        return "十神未明"
    pair = evidence.get(f"{prefix}_ten_gods", {})
    if not isinstance(pair, dict):
        return "十神未明"
    return f"天干{TEN_GOD.get(str(pair.get('stem')), str(pair.get('stem', '')))}、地支{TEN_GOD.get(str(pair.get('branch')), str(pair.get('branch', '')))}"


def flow(row: dict[str, Any]) -> str:
    elements = row.get("elements", {})
    evidence = row.get("bazi_evidence", {})
    if not isinstance(elements, dict):
        return "五行状态不明"
    stem = ELEMENT.get(str(elements.get("stem")), str(elements.get("stem", "")))
    branch = ELEMENT.get(str(elements.get("branch")), str(elements.get("branch", "")))
    state = evidence.get("useful_state") if isinstance(evidence, dict) else ""
    if state == "useful_element_activated":
        return f"{stem}透、{branch}动，规则、证据、取舍和执行边界变重要"
    if state == "dominant_element_reinforced":
        return f"{stem}透、{branch}动，主气被推高，行动快但也容易急"
    if stem == "水" or branch == "水":
        return f"{stem}透、{branch}动，压力、考试、制度和外部要求增强"
    if stem == "木" or branch == "木":
        return f"{stem}透、{branch}动，学习、想法、长辈支持和方向感增强"
    if stem == "土" or branch == "土":
        return f"{stem}透、{branch}动，输出、任务、消耗和现实杂务增加"
    return f"{stem}透、{branch}动，宜看现实承接力"


def branch_notes(row: dict[str, Any], natal: dict[str, str]) -> str:
    _stem, branch = split_ganzhi(str(row.get("ganzhi", "")))
    notes = []
    for palace, natal_branch in natal.items():
        rel = branch_relation(branch, natal_branch)
        if rel:
            notes.append(f"流年{BRANCH.get(branch, branch)}与原局{palace}{BRANCH.get(natal_branch, natal_branch)}成{rel}")
    luck = row.get("bazi_evidence", {}).get("active_major_luck", {}) if isinstance(row.get("bazi_evidence"), dict) else {}
    if isinstance(luck, dict):
        _ls, lb = split_ganzhi(str(luck.get("ganzhi", "")))
        rel = branch_relation(branch, lb)
        if rel:
            notes.append(f"流年{BRANCH.get(branch, branch)}与大运{BRANCH.get(lb, lb)}成{rel}")
    return "；".join(notes[:3]) if notes else "地支关系偏平稳，重点看当年任务能否落实"


def natal_branches(pillars: dict[str, str]) -> dict[str, str]:
    labels = {"year": "年支", "month": "月支", "day": "日支", "hour": "时支"}
    out = {}
    for key, label in labels.items():
        _s, b = split_ganzhi(str(pillars.get(key, "")))
        out[label] = b
    return out


def school_summary(profile: dict[str, Any]) -> str:
    debate = profile.get("school_debate", {})
    if not isinstance(debate, dict):
        return "流派辩论未生成。"
    consensus = debate.get("consensus", {})
    if not isinstance(consensus, dict):
        return "流派辩论未形成共识。"
    primary = "、".join(str(x) for x in consensus.get("primary_schools", [])[:4]) or "待校准"
    aux = "、".join(str(x) for x in consensus.get("auxiliary_schools", [])[:4]) or "无"
    return f"六个八字流派纸智能体已参与，主断流派为{primary}，辅助流派为{aux}，保留争议{len(debate.get('conflicts', []))}处。"


def run_analysis(task: dict[str, Any]) -> dict[str, Any]:
    tmp = Path(tempfile.mkdtemp(prefix="mingli_family_"))
    try:
        repo = bootstrap_repo(tmp)
        coordinator = repo.load_agent("mingli_orchestrator")
        return MingliFiveAgentSystem(repo)(coordinator, task)["final_report"]
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


RELATION_WEIGHT = {
    "冲": 4,
    "刑": 3,
    "害": 2,
    "破": 2,
    "合": 1,
    "伏吟": 2,
}

CATEGORY_SCORE = {
    "learning": {"study": 3, "career": 1, "money": 0, "relation": 0},
    "authority": {"study": 2, "career": 3, "money": 0, "relation": 1},
    "wealth": {"study": 0, "career": 2, "money": 3, "relation": 1},
    "expression": {"study": 1, "career": 2, "money": 1, "relation": 0},
    "friends": {"study": 0, "career": 1, "money": -1, "relation": 2},
}

INTENSITY_SCORE = {
    "constructive": 1,
    "neutral": 0,
    "mixed": 0,
    "high-volatility": -1,
}


def relation_pairs(branch: str, natal: dict[str, str], extra: dict[str, str] | None = None) -> list[str]:
    pairs: list[str] = []
    sources = {
        "年支": natal.get("year", ""),
        "月支": natal.get("month", ""),
        "日支": natal.get("day", ""),
        "时支": natal.get("hour", ""),
    }
    if extra:
        sources.update(extra)
    for name, other in sources.items():
        rel = branch_relation(branch, other)
        if rel:
            pairs.append(f"{branch_zh(branch)}与{name}{branch_zh(other)}{rel}")
    return pairs


def relation_pressure(pairs: list[str]) -> int:
    total = 0
    for item in pairs:
        for key, value in RELATION_WEIGHT.items():
            if key in item:
                total += value
                break
    return total


def score_word(value: int) -> str:
    if value >= 7:
        return "很强"
    if value >= 5:
        return "较强"
    if value >= 3:
        return "中等偏上"
    if value >= 1:
        return "普通"
    return "偏弱"


def pressure_word(value: int) -> str:
    if value >= 8:
        return "明显动荡"
    if value >= 5:
        return "有压力"
    if value >= 3:
        return "小波动"
    return "较平稳"


def category_phrase(category: str, child: bool, age: int) -> str:
    if child and age < 18:
        phrases = {
            "learning": "主线落在学习吸收、老师要求和基础补强",
            "authority": "主线落在考试规则、纪律约束和升学门槛",
            "wealth": "主线落在家庭资源、时间分配和现实安排",
            "expression": "主线落在表达展示、兴趣作品和竞赛表现",
            "friends": "主线落在同学圈子、小组合作和比较心",
        }
    elif child and age < 23:
        phrases = {
            "learning": "主线落在学历、证书和专业知识沉淀",
            "authority": "主线落在制度考核、实习规范和资格门槛",
            "wealth": "主线落在资源选择、生活成本和现实取舍",
            "expression": "主线落在作品、表达、项目展示和个人风格",
            "friends": "主线落在同伴竞争、合作团队和人脉选择",
        }
    else:
        phrases = {
            "learning": "主线落在复盘学习、方法更新和资质补强",
            "authority": "主线落在职位责任、上级规则和组织考核",
            "wealth": "主线落在收入资源、预算合同和资产安排",
            "expression": "主线落在项目输出、公开表达和成果交付",
            "friends": "主线落在人际合作、同业竞争和圈层消耗",
        }
    return phrases.get(category, "主线落在调整节奏和补足短板")


def month_stage(month: int) -> str:
    stages = {
        1: "年初定调，先看目标和方法是否立得住",
        2: "春气展开，适合启动新任务但忌分散",
        3: "上半年节奏成形，重点看基础和资源衔接",
        4: "行动力抬头，容易急推，也适合突破卡点",
        5: "外部互动增多，合作、竞争和情绪都更明显",
        6: "年中承压，适合复盘进度和修正方法",
        7: "下半年开局，现实任务和交付要求变重",
        8: "资源取舍增强，适合谈条件、排优先级",
        9: "秋季收束，容易出现考核、比较或成果验收",
        10: "深度整理期，适合处理遗留问题和关系边界",
        11: "压力转暗，容易心里急，宜稳住节奏",
        12: "年末收尾，重在总结、清账和安排下一步",
    }
    return stages.get(month, "本月节奏不明，按当期组合谨慎判断")


def annual_scores(row: dict[str, Any], natal: dict[str, str], *, child: bool) -> dict[str, Any]:
    category = str(row.get("category", ""))
    intensity = str(row.get("intensity", "neutral"))
    year_branch = split_ganzhi(str(row.get("ganzhi", "")))[1]
    luck_branch = split_ganzhi(str(row.get("major_luck", "")))[1]
    pairs = relation_pairs(year_branch, natal, {"大运支": luck_branch} if luck_branch else None)
    pressure = relation_pressure(pairs)
    base = CATEGORY_SCORE.get(category, {"study": 1, "career": 1, "money": 0, "relation": 0})
    boost = INTENSITY_SCORE.get(intensity, 0)
    use_state = str(row.get("useful_state", ""))
    support = 1 if use_state == "activated" else -1 if use_state == "challenged" else 0
    return {
        "study": max(0, 3 + base["study"] + boost + support - pressure // 5),
        "career": max(0, 3 + base["career"] + boost + support - pressure // 6),
        "money": max(0, 3 + base["money"] + boost + support - pressure // 6),
        "relation": max(0, 3 + base["relation"] - pressure // 5),
        "pressure": pressure + (2 if intensity == "high-volatility" else 0),
        "pairs": pairs,
    }


def monthly_scores(
    row: dict[str, Any],
    year_row: dict[str, Any] | None,
    natal: dict[str, str],
    *,
    child: bool,
) -> dict[str, Any]:
    category = str(row.get("category", ""))
    intensity = str(row.get("intensity", "neutral"))
    month_branch = split_ganzhi(str(row.get("ganzhi", "")))[1]
    extra: dict[str, str] = {}
    if year_row:
        extra["流年支"] = split_ganzhi(str(year_row.get("ganzhi", "")))[1]
        luck_branch = split_ganzhi(str(year_row.get("major_luck", "")))[1]
        if luck_branch:
            extra["大运支"] = luck_branch
    pairs = relation_pairs(month_branch, natal, extra)
    pressure = relation_pressure(pairs)
    base = CATEGORY_SCORE.get(category, {"study": 1, "career": 1, "money": 0, "relation": 0})
    boost = INTENSITY_SCORE.get(intensity, 0)
    if child:
        study = max(0, 3 + base["study"] + boost - pressure // 5)
        career = max(0, 2 + base["career"] + boost - pressure // 6)
    else:
        study = max(0, 2 + base["study"] + boost - pressure // 6)
        career = max(0, 3 + base["career"] + boost - pressure // 5)
    return {
        "study": study,
        "career": career,
        "money": max(0, 3 + base["money"] + boost - pressure // 6),
        "relation": max(0, 3 + base["relation"] - pressure // 5),
        "pressure": pressure + (2 if intensity == "high-volatility" else 0),
        "pairs": pairs,
    }


def key_trigger(pairs: list[str]) -> str:
    if not pairs:
        return "没有明显刑冲，主要看十神主题本身"
    ranked = sorted(
        pairs,
        key=lambda item: max((value for key, value in RELATION_WEIGHT.items() if key in item), default=0),
        reverse=True,
    )
    return "，".join(ranked[:2])


def yearly_line(row: dict[str, Any], natal: dict[str, str], *, child: bool) -> str:
    year = int(row["year"])
    age = int(row["age"])
    prefix = f"{year}年，{age}岁，{gz(row.get('ganzhi'))}："
    category = str(row.get("category", ""))
    scores = annual_scores(row, natal, child=child)
    trigger = key_trigger(scores["pairs"])
    base = f"{ten_gods(row)}，{flow(row)}。年度触发点：{trigger}。"
    theme = category_phrase(category, child, age)
    if child and age < 18:
        verdict = (
            f"{theme}；学业势能{score_word(scores['study'])}，"
            f"事业只看方向准备，为{score_word(scores['career'])}，"
            f"人际压力{pressure_word(scores['pressure'])}。"
            "断语：这一年不宜只看成绩名次，真正关键是作息、方法和老师要求能否稳定执行。"
        )
    elif child and age < 23:
        verdict = (
            f"{theme}；学业和证书势能{score_word(scores['study'])}，"
            f"专业能力与实习准备{score_word(scores['career'])}，"
            f"关系扰动{pressure_word(scores['pressure'])}。"
            "断语：这一年要把兴趣变成可展示成果，不能只停留在想法和临时热情。"
        )
    else:
        verdict = (
            f"{theme}；事业势能{score_word(scores['career'])}，"
            f"资源财务势能{score_word(scores['money'])}，"
            f"关系和家庭牵动{score_word(scores['relation'])}，"
            f"波动等级{pressure_word(scores['pressure'])}。"
            "断语：能成的事情靠制度、合同、边界和稳定交付，不能靠一时情面硬撑。"
        )
    return f"- {prefix}{base}{verdict}"


def child_year_assertion(year: int, scores: dict[str, Any], trigger: str) -> str:
    assertions = {
        2026: "这一年仍属升学和基础定型期，火气重，心气会高，家里要管住作息和电子分心，真正的分水岭是能不能把每天的学习流程固定下来。",
        2027: "这一年进入新大运的门口，现实取舍增多，适合定专业方向和考试路线，不能在多个兴趣之间来回摇摆。",
        2028: "这一年自我意识明显抬头，适合参加能留下成果的比赛、项目或证书，但与同伴比较容易上头，家长少用激将法。",
        2029: "这一年资源、学校平台和家庭安排会影响选择，适合把未来吃饭的硬技能定下来，忌只追热门不看自身耐力。",
        2030: "这一年开始更像成年人做选择，钱、专业、城市、圈子会绑在一起，适合稳扎稳打拿到第一个可验证成果。",
        2031: "这一年压力来自规则和考核，适合考证、升学、入职筛选或正规训练，最怕临场发挥代替长期准备。",
        2032: "这一年学习吸收和贵人指点较重要，适合跟对老师、进入好团队、补理论体系，暂时不宜过早自立门户。",
        2033: "这一年现实资源再次变重，适合实习、就业、收入结构和长期方向落地，感情也会被现实条件检验。",
        2034: "这一年刑冲压力明显，容易因急躁、圈子、人情或方向不稳而折腾，适合收缩战线，不适合赌一把。",
        2035: "这一年人际和竞争强，机会可能来自朋友同学，也可能被同圈层消耗；合作必须先写清规则。",
        2036: "这一年大运转换后进入新平台，事业起步的窗口打开，适合换赛道、换城市或进入更正式的组织。",
        2037: "这一年表达和成果交付变重要，适合把专业能力做成作品、口碑或稳定客户，少讲概念，多交结果。",
        2038: "这一年资源和责任同时加重，适合谈收入、岗位、资产和婚恋现实条件，账目和承诺必须清楚。",
        2039: "这一年三十岁前的收束感很强，适合确定长期职业路线和稳定关系边界，不宜再用试错心态消耗时间。",
    }
    base = assertions.get(year, "这一年要按当期流年重新校准，不能套用前后年份的判断。")
    return base


def child_annual_line(row: dict[str, Any], natal: dict[str, str]) -> str:
    year = int(row["year"])
    age = int(row["age"])
    category = str(row.get("category", ""))
    scores = annual_scores(row, natal, child=True)
    trigger = key_trigger(scores["pairs"])
    if age < 18:
        domains = f"学业{scores['study']}分，健康作息和父母配合优先，方向准备{scores['career']}分"
    elif age < 23:
        domains = f"学业证书{scores['study']}分，专业方向{scores['career']}分，关系压力{pressure_word(scores['pressure'])}"
    elif age < 27:
        domains = f"事业起步{scores['career']}分，资源财务{scores['money']}分，感情现实度{scores['relation']}分"
    else:
        domains = f"事业平台{scores['career']}分，收入责任{scores['money']}分，婚恋稳定度{scores['relation']}分"
    assertion = child_year_assertion(year, scores, trigger)
    return (
        f"- {year}年，{age}岁，{gz(row.get('ganzhi'))}："
        f"{ten_gods(row)}，{flow(row)}。"
        f"年度触发点：{trigger}。"
        f"{category_phrase(category, True, age)}；{domains}。"
        f"断语：{assertion}"
    )


def major_luck_line(item: dict[str, Any], natal: dict[str, str]) -> str:
    start_year = int(item.get("start_year", 0))
    end_year = int(item.get("end_year", 0))
    start_age = int(item.get("start_age", 0))
    end_age = int(item.get("end_age", 0))
    pillar = str(item.get("ganzhi", ""))
    branch = split_ganzhi(pillar)[1]
    trigger = key_trigger(relation_pairs(branch, natal)) if branch else "早年起运信息不完整，按流年校验"
    if pillar == "JiaShen":
        verdict = "这是十七岁到二十六岁的主运，甲木带规则和学习压力，申金带表达、技术、工具和结果意识。大方向是从学生身份转成能拿作品和证书说话的人。"
    elif pillar == "YiYou":
        verdict = "这是二十七岁到三十六岁的主运，乙木重选择和规矩，酉金重专业、口碑、收入和边界。三十岁前会开始真正筛选职业平台和稳定关系。"
    else:
        verdict = "这一段主要作背景参考，具体仍以覆盖年份的流年触发为准。"
    return f"- {start_year}年至{end_year}年，{start_age}至{end_age}岁，{gz(pillar)}大运：{verdict}本命触发点：{trigger}。"


def child_phase_line(rows: list[dict[str, Any]], start: int, end: int, title: str) -> str:
    selected = [row for row in rows if start <= int(row["year"]) <= end]
    if not selected:
        return f"- {title}：资料不足。"
    high = [int(row["year"]) for row in selected if str(row.get("intensity")) == "high-volatility"]
    constructive = [int(row["year"]) for row in selected if str(row.get("intensity")) == "constructive"]
    cats = Counter(str(row.get("category", "")) for row in selected)
    dominant = CATEGORY_ZH.get(cats.most_common(1)[0][0], "调整")
    if start <= 2026 and end <= 2029:
        verdict = "重点不是挣钱，也不是婚恋，而是升学、专业方向、基础能力和家里节奏。"
    elif start <= 2030 and end <= 2035:
        verdict = "重点从学习转向就业准备、证书、实习、作品、人脉筛选和第一次稳定收入。"
    else:
        verdict = "重点进入事业平台、收入结构、长期城市和稳定亲密关系的选择。"
    risk = f"波动年份为{','.join(str(x) for x in high)}年" if high else "没有特别重的波动年份"
    good = f"推进较顺年份为{','.join(str(x) for x in constructive)}年" if constructive else "推进顺势年份不明显"
    return f"- {title}：主线偏{dominant}，{verdict}{good}，{risk}。"


def month_line(
    row: dict[str, Any],
    year_row: dict[str, Any] | None,
    natal: dict[str, str],
    *,
    child: bool,
) -> str:
    year = int(row["year"])
    month = int(row["month"])
    age = int(row.get("age", 0))
    label = f"{year}年{MONTH_NAMES.get(month, str(month) + '月')}，{gz(row.get('ganzhi'))}："
    category = str(row.get("category", ""))
    scores = monthly_scores(row, year_row, natal, child=child)
    trigger = key_trigger(scores["pairs"])
    year_context = f"承接{year}年{gz(year_row.get('ganzhi'))}年度主线，" if year_row else ""
    base = (
        f"{ten_gods(row, 'monthly')}，{flow(row)}。"
        f"本月触发点：{trigger}。{year_context}{month_stage(month)}。"
    )
    theme = category_phrase(category, child, age)
    if child and age < 18:
        if scores["pressure"] >= 5:
            action = "断语：本月容易因为节奏乱、情绪急或同学比较而影响学习，先稳作息再冲成绩。"
        elif scores["study"] >= scores["career"] + 2:
            action = "断语：本月适合补基础、交作业、做错题和应对考试，分数比面子重要。"
        else:
            action = "断语：本月适合把兴趣、表达或小项目变成学习助力，但不能挤掉主科时间。"
        verdict = (
            f"{theme}；学业评分{scores['study']}分，"
            f"方向准备评分{scores['career']}分，"
            f"关系压力为{pressure_word(scores['pressure'])}。{action}"
        )
    elif child and age < 23:
        if scores["career"] >= scores["study"]:
            action = "断语：本月要做作品、实习、证书或项目沉淀，不能只停在课堂消化。"
        else:
            action = "断语：本月仍以课程、考试和证书为先，专业探索要服从主线节奏。"
        verdict = (
            f"{theme}；学业评分{scores['study']}分，"
            f"专业与实习准备评分{scores['career']}分，"
            f"关系压力为{pressure_word(scores['pressure'])}。{action}"
        )
    else:
        if scores["pressure"] >= 6:
            action = "断语：本月先控风险、控承诺、控合同细节，进攻要慢半拍。"
        elif scores["career"] >= scores["money"] and scores["career"] >= 5:
            action = "断语：本月适合推项目、见上级客户、交付成果，讲清边界就能推进。"
        elif scores["money"] >= 5:
            action = "断语：本月适合谈资源、预算、收入和合作条件，账目必须清楚。"
        else:
            action = "断语：本月以复盘、补漏洞和整理关系为主，不宜贪多。"
        verdict = (
            f"{theme}；事业评分{scores['career']}分，"
            f"资源财务评分{scores['money']}分，"
            f"关系压力为{pressure_word(scores['pressure'])}。{action}"
        )
    return f"- {label}{base}{verdict}"


def build_linfan_report(final: dict[str, Any]) -> str:
    profile = final["bazi_profile"]
    natal = natal_branches(profile["pillars"])
    rows = final["annual_luck"]["rows"]
    months = final["monthly_luck"]["rows"]
    year_by_year = {int(row["year"]): row for row in rows}
    lines = [
        "# 林凡未来研判报告",
        "",
        "## 基本判断",
        "- 出生资料：男，一九七八年四月十四日早上六点五十分，福建省三明市。",
        f"- 八字四柱：年柱{gz(profile['pillars']['year'])}，月柱{gz(profile['pillars']['month'])}，日柱{gz(profile['pillars']['day'])}，时柱{gz(profile['pillars']['hour'])}。",
        f"- 八字流派辩论：{school_summary(profile)}",
        "- 本轮重点看二零二六年至二零三六年的事业、资源、家庭责任和关系边界。此报告仍需用真实重大年份校准。",
        "",
        "## 总断",
        "- 林凡命盘火气明显，行动力、表达力和推进力强，适合做项目推进、管理、资源整合和公开表达。",
        "- 中年以后最重要的不是再拼一股劲，而是规则、合同、边界、预算和复盘。越能把人情和责任分清，事业越稳。",
        "- 二零二六年后进入更重视规则和资源重组的阶段，适合把经验转成制度和长期成果，不适合情绪化承诺。",
        "- 逐年逐月部分已按当期干支、十神、五行流通、流年与大运、本命地支的刑冲合害独立评分，不再按同类年份套固定话。",
        "",
        "## 未来逐年走势",
    ]
    lines.extend(yearly_line(row, natal, child=False) for row in rows)
    lines.extend(["", "## 未来逐月提示"])
    lines.extend(month_line(row, year_by_year.get(int(row["year"])), natal, child=False) for row in months)
    lines.extend(
        [
            "",
            "## 建议",
            "- 事业上少口头承诺，多留书面证据。",
            "- 合作前先定角色、利益和退出方式。",
            "- 家庭与钱容易绑在一起，越到中年越要把预算和责任讲清楚。",
        ]
    )
    return "\n".join(lines) + "\n"


def build_child_report(final: dict[str, Any]) -> str:
    profile = final["bazi_profile"]
    natal = natal_branches(profile["pillars"])
    rows = final["annual_luck"]["rows"]
    months = final["monthly_luck"]["rows"]
    year_by_year = {int(row["year"]): row for row in rows}
    annual_categories = Counter(str(row.get("category", "")) for row in rows)
    category_summary = "，".join(
        f"{CATEGORY_ZH.get(key, key)}{value}年"
        for key, value in annual_categories.items()
    )
    lines = [
        "# 林凡孩子未来学业事业婚姻研判报告",
        "",
        "## 基本资料",
        "- 出生时间：二零一零年六月十八日晚上七点三十分。",
        "- 出生地点：福建省厦门市思明区。",
        "- 性别：未提供。传统命理中性别会影响大运顺逆和婚姻侧重点，所以本版为临时研判版。",
        f"- 八字四柱：年柱{gz(profile['pillars']['year'])}，月柱{gz(profile['pillars']['month'])}，日柱{gz(profile['pillars']['day'])}，时柱{gz(profile['pillars']['hour'])}。",
        f"- 八字流派辩论：{school_summary(profile)}",
        "",
        "## 先说结论",
        "- 这个孩子的盘里学习、规则、表达和现实责任都会比较明显，不适合完全放养，也不适合只靠压力逼。",
        "- 学业上最需要的是稳定作息、清晰目标、阶段复盘和能落地的方法。若只凭兴趣，状态容易有高低起伏。",
        "- 接下来几年重点不是正式事业，而是专业方向、考试证书、能力作品、实习经验和自我管理。",
        "- 成年后的事业更适合走专业能力加项目执行的路线，不宜过早卷入口头合作和人情承诺。",
        "- 婚姻要等成年后再看具体流年。本命倾向是感情不能只看感觉，现实责任、沟通方式和双方家庭安排都会影响稳定度。",
        f"- 未来十一年年度主题分布：{category_summary}。这是系统内部分类，不等于现实结果。",
        "",
        "## 学业与事业准备总评",
        "- 二零二六年至二零二八年仍以学业为主，重点看升学压力、考试节奏、老师要求和自我管理。",
        "- 二零二九年至二零三二年开始从纯读书转向专业方向和社会化能力，适合建立一项能长期吃饭的硬技能。",
        "- 二零三三年至二零三六年更像进入事业起步和现实责任加重阶段，要重视规则、合同、职业边界和稳定交付。",
        "- 下面每一年、每个月都按当期干支、十神、五行流通、流年与大运、本命地支的刑冲合害独立评分；未成年阶段不按成人财运和婚恋下断。",
        "",
        "## 成年后婚姻趋势",
        "- 婚姻不宜太早定死，适合先把学业、职业方向和经济独立打稳。",
        "- 适合找情绪稳定、讲规则、能沟通现实责任的人。若对方只讲感觉，不讲责任，后期容易累。",
        "- 二十多岁前半段感情多半仍带学习和选择性质，不宜因为一时冲动绑定太深。",
        "- 真正适合进入稳定关系的窗口，要结合成年后的具体大运流年和真实性别重新校准。",
        "",
        "## 未来逐年走势",
    ]
    lines.extend(yearly_line(row, natal, child=True) for row in rows)
    lines.extend(["", "## 未来逐月学业与事业准备"])
    lines.extend(month_line(row, year_by_year.get(int(row["year"])), natal, child=True) for row in months)
    lines.extend(
        [
            "",
            "## 家长建议",
            "- 不要只问成绩，要问方法、节奏和复盘。",
            "- 关键考试年份要提前半年稳定作息，不要临时猛压。",
            "- 兴趣可以保留，但必须有主线技能。适合让孩子做作品、项目、竞赛或证书，把能力变成可展示成果。",
            "- 婚恋问题成年后再细看，目前重点是人格稳定、表达方式和责任感。",
        ]
    )
    return "\n".join(lines) + "\n"


def build_child_report(final: dict[str, Any]) -> str:
    profile = final["bazi_profile"]
    natal = natal_branches(profile["pillars"])
    rows = final["annual_luck"]["rows"]
    major_luck = [
        item
        for item in profile.get("major_luck", [])
        if isinstance(item, dict)
        and int(item.get("end_year", 0)) >= 2026
        and int(item.get("start_year", 0)) <= 2039
    ]
    lines = [
        "# 林凡孩子三十岁前运势研判报告",
        "",
        "## 基本资料",
        "- 出生时间：二零一零年六月十八日晚上七点三十分。",
        "- 出生地点：福建省厦门市思明区。",
        "- 性别：男。",
        f"- 八字四柱：年柱{gz(profile['pillars']['year'])}，月柱{gz(profile['pillars']['month'])}，日柱{gz(profile['pillars']['day'])}，时柱{gz(profile['pillars']['hour'])}。",
        f"- 八字流派辩论：{school_summary(profile)}",
        "- 本报告预测到三十岁之前，即二零二六年至二零三九年。重点看大势、大运阶段和逐年流年，不输出逐月长表。",
        "- 全局规则：每一年必须按当年干支、十神、五行流通、大运、本命刑冲合害独立推导；禁止把同一段套话换年份重复使用。",
        "",
        "## 总体断语",
        "- 这个男孩的盘不宜完全放养。他需要规则、节奏和可见成果来成事，但又不能只靠压迫推动；越压到情绪上，越容易把聪明劲用在抵抗上。",
        "- 少年到二十岁前，核心是学业、健康作息、父母配合、老师要求和专业方向。这个阶段不能谈成人财运，更不能把一两次成绩起伏看成命运定型。",
        "- 二十岁到二十六岁，重点是把学习转成证书、作品、实习和可计价技能。能不能形成一项长期吃饭的硬本领，是这十年的真正分水岭。",
        "- 二十七岁以后，事业平台、收入结构、城市选择和感情稳定会一起上桌。感情不是越早定越好，而是要等职业方向和现实责任变清楚以后再定。",
        "",
        "## 大运推演",
    ]
    lines.extend(major_luck_line(item, natal) for item in major_luck)
    lines.extend(
        [
            "",
            "## 三十岁前大势",
            child_phase_line(rows, 2026, 2029, "二零二六年至二零二九年，十六至十九岁"),
            child_phase_line(rows, 2030, 2035, "二零三零年至二零三五年，二十至二十五岁"),
            child_phase_line(rows, 2036, 2039, "二零三六年至二零三九年，二十六至二十九岁"),
            "",
            "## 学业与事业主线",
            "- 学业主线：二零二六年至二零三二年最关键，前半段看升学和基础，后半段看证书、专业体系和能不能进入好平台。",
            "- 事业主线：二零三零年开始出现真正的职业准备，二零三六年后平台和收入结构更重要，适合走专业技术、项目执行、运营管理或资源整合路线。",
            "- 婚恋主线：二十岁前不作婚恋定论；二十三岁以后会开始被现实条件触动，二十七岁后才更适合认真评估稳定关系。",
            "- 家庭关系：父母最该抓的是节奏、方法和边界，不要用短期成绩替代长期能力判断。",
            "",
            "## 逐年流年研判",
        ]
    )
    lines.extend(child_annual_line(row, natal) for row in rows)
    lines.extend(
        [
            "",
            "## 家长建议",
            "- 十八岁前，少谈钱和婚恋，多看睡眠、运动、眼睛、脾胃、学习方法、老师反馈和父母沟通。",
            "- 十八岁到二十二岁，重点帮他建立专业方向和硬技能，不要只按热门专业或短期收入做选择。",
            "- 二十三岁以后，合作、实习、就业和感情都要看规则。凡是只靠口头承诺的关系，都要慢一点。",
            "- 二十七岁以后，鼓励他建立稳定作品、稳定收入和稳定边界。真正能成事的不是一时聪明，而是长期交付。",
        ]
    )
    return "\n".join(lines) + "\n"


def escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def render_pdf(markdown: str, output: Path, title: str) -> None:
    pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
    styles = getSampleStyleSheet()
    base = ParagraphStyle(
        "Base",
        parent=styles["Normal"],
        fontName="STSong-Light",
        fontSize=9.5,
        leading=14,
        alignment=TA_LEFT,
        wordWrap="CJK",
    )
    h1 = ParagraphStyle("H1", parent=base, fontSize=18, leading=24, spaceAfter=7, textColor=colors.HexColor("#222222"))
    h2 = ParagraphStyle("H2", parent=base, fontSize=13, leading=18, spaceBefore=7, spaceAfter=4, textColor=colors.HexColor("#333333"))
    bullet = ParagraphStyle("Bullet", parent=base, leftIndent=9, firstLineIndent=-7)
    story = []
    for line in markdown.splitlines():
        if not line.strip():
            story.append(Spacer(1, 4))
        elif line.startswith("# "):
            story.append(Paragraph(escape(line[2:]), h1))
        elif line.startswith("## "):
            story.append(Paragraph(escape(line[3:]), h2))
        elif line.startswith("- "):
            story.append(Paragraph("· " + escape(line[2:]), bullet))
        else:
            story.append(Paragraph(escape(line), base))
    doc = SimpleDocTemplate(
        str(output),
        pagesize=A4,
        rightMargin=13 * mm,
        leftMargin=13 * mm,
        topMargin=13 * mm,
        bottomMargin=13 * mm,
        title=title,
    )
    doc.build(story)


def assert_clean(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    assert not re.search(r"[A-Za-z]", text), path
    assert "?" not in text and "？" not in text, path
    assert "```" not in text, path


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    years = list(range(2026, 2037))
    linfan = run_analysis(
        {
            "birth": {
                "name": "林凡",
                "birth_date": "1978-04-14",
                "birth_time": "06:50",
                "gender": "male",
                "birthplace": "福建省三明市",
            },
            "annual_start_year": 2026,
            "annual_end_year": 2036,
            "monthly_years": years,
            "language": "zh",
        }
    )
    child = run_analysis(
        {
            "birth": {
                "name": "林凡孩子",
                "birth_date": "2010-06-18",
                "birth_time": "19:30",
                "gender": "male",
                "birthplace": "福建省厦门市思明区",
            },
            "annual_start_year": 2026,
            "annual_end_year": 2039,
            "monthly_years": [],
            "language": "zh",
        }
    )
    outputs = [
        (
            OUT_DIR / "linfan_20260625_independent_annual_monthly_zh.report.md",
            build_linfan_report(linfan),
            "林凡未来研判报告",
        ),
        (
            OUT_DIR / "linfan_child_male_20100618_to_age30_macro_annual_zh.report.md",
            build_child_report(child),
            "林凡孩子三十岁前运势研判报告",
        ),
    ]
    for md_path, markdown, title in outputs:
        md_path.write_text(markdown, encoding="utf-8")
        assert_clean(md_path)
        render_pdf(markdown, md_path.with_suffix(".pdf"), title)
        print(md_path)
        print(md_path.with_suffix(".pdf"))


if __name__ == "__main__":
    main()
