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


BASE_MD = Path("examples/mingli_5agents/reports/linfan_20260624_user_plain_zh.report.md")
ANALYSIS_JSON = Path("examples/mingli_5agents/reports/linfan_20260624_clean.analysis.json")
OUT_MD = Path("examples/mingli_5agents/reports/linfan_20260624_age_aware_v2_zh.report.md")
OUT_PDF = OUT_MD.with_suffix(".pdf")


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
CATEGORY = {
    "wealth": "资源与家庭责任",
    "authority": "规则与约束",
    "expression": "表达与活动",
    "learning": "学习与吸收",
    "friends": "同伴与合作",
    "relationship": "关系与情绪",
}
INTENSITY = {
    "high-volatility": "波动偏高",
    "constructive": "较有建设性",
    "active": "较活跃",
    "moderate": "中等",
    "symbolic": "参考",
}
MESSAGE = {
    "stronger money-management and asset-allocation theme; avoid leverage.": "资源管理意识增强，成年后表现为财务和资产安排；未成年时主要看家庭资源分配。",
    "cash flow can move quickly; require budgets and written terms.": "成年后现金流变化较快，未成年时则看家庭安排和花销节奏。",
    "steady finances favor planning over speculation.": "适合重计划、重积累，不适合冒进。",
    "keep compliance and reporting rhythm clear.": "要重视规则、汇报和边界。",
    "rules, title, audits, leadership, or institutional pressure become central.": "规则、师长、单位或制度要求会更明显。",
    "authority relationships can improve through preparation and evidence.": "面对师长、领导或制度，准备充分更有利。",
    "career choices are tied to revenue, assets, operations, or family duties.": "成年后事业容易和收入、资产、运营或家庭责任绑定。",
    "career improves through consistent execution.": "靠稳定执行和持续交付改善局面。",
    "career advancement depends on discipline, contracts, and role clarity.": "事业推进要靠纪律、合同和角色边界。",
    "career push is strong but should be paced to avoid conflict.": "推动力较强，但节奏要放慢，避免冲突。",
    "study should support immediate work needs.": "学习要服务当前阶段的现实需要。",
    "learning is useful when converted into a practical system.": "学习能转成方法和习惯时更有用。",
    "best suited for study, credentials, research, travel, or strategic review.": "适合学习、考证、研究、出行规划或复盘。",
    "marriage and romantic issues may connect with money, home, or duty.": "成年后感情容易和金钱、家庭或责任相连。",
    "relationships benefit from predictable communication.": "关系经营受益于稳定、清楚的沟通。",
    "direct speech can heat up conflict; slow down before decisions.": "说话太直容易升温冲突，重大决定前要慢。",
    "friends and partners are active; choose collaborators carefully.": "朋友和合作对象较活跃，选择伙伴要谨慎。",
    "networking is useful when roles are explicit.": "人际合作在角色清楚时更有用。",
    "competition and comparison can increase.": "竞争和比较感可能增加，要避免无谓消耗。",
    "visibility can attract support if communication stays measured.": "表达有分寸时，更容易获得支持。",
    "leadership ties improve through reliability.": "和领导、客户或机构的关系，靠可靠执行改善。",
    "leaders, managers, clients, or regulators carry more weight.": "领导、客户、管理者或规则要求分量提高。",
    "children, students, juniors, or creative outputs require attention.": "子女、学生、晚辈或创作输出需要更多关注。",
    "family responsibility and practical support are highlighted.": "家庭责任和实际支持会被强调。",
    "family ties need steady time and clear expectations.": "家庭关系需要稳定投入和清楚期待。",
}


def ganzhi(value: str) -> str:
    for key, label in sorted(STEM.items(), key=lambda item: -len(item[0])):
        if value.startswith(key):
            return label + BRANCH.get(value[len(key) :], value[len(key) :])
    return value


def message(value: str) -> str:
    return MESSAGE.get(value, "以稳定、谨慎、看现实条件为主。")


def child_lines(row: dict[str, object]) -> list[str]:
    return [
        f"- 年龄：{row['age']}岁；主调：{CATEGORY.get(row.get('category'), '成长主题')}；强度：{INTENSITY.get(row.get('intensity'), '中等')}。",
        "- 这一阶段不按财运、事业、婚恋来判断，重点看身体、父母照顾、家庭环境和早期性格。",
        "- 健康作息：注意睡眠、饮食、运动安全和情绪稳定。",
        "- 父母家庭：父母的照顾方式、家庭稳定度和规矩感，对孩子影响更大。",
        "- 学业启蒙：重点是兴趣、习惯、专注力和表达能力，不宜过早用成人成败标准评价。",
    ]


def teen_lines(row: dict[str, object]) -> list[str]:
    return [
        f"- 年龄：{row['age']}岁；主调：{CATEGORY.get(row.get('category'), '成长主题')}；强度：{INTENSITY.get(row.get('intensity'), '中等')}。",
        "- 这一阶段重点看学业、身体发育、父母关系、同学朋友和自我管理。",
        f"- 学业：{message(str(row.get('study', '')))}",
        "- 健康：注意作息、运动损伤、情绪波动和压力消化。",
        "- 父母家庭：适合用清楚规则和稳定陪伴来减少冲突。",
        f"- 同学朋友：{message(str(row.get('friends', '')))}",
    ]


def young_lines(row: dict[str, object]) -> list[str]:
    return [
        f"- 年龄：{row['age']}岁；主调：{CATEGORY.get(row.get('category'), '阶段主题')}；强度：{INTENSITY.get(row.get('intensity'), '中等')}。",
        "- 这一阶段从学习走向社会，重点看专业能力、方向选择、人际边界和感情萌芽。",
        f"- 学业与技能：{message(str(row.get('study', '')))}",
        f"- 事业准备：{message(str(row.get('career', '')))}",
        f"- 朋友人际：{message(str(row.get('friends', '')))}",
        f"- 感情：{message(str(row.get('relationship', '')))}",
    ]


def adult_lines(row: dict[str, object]) -> list[str]:
    return [
        f"- 年龄：{row['age']}岁；主调：{CATEGORY.get(row.get('category'), '阶段主题')}；强度：{INTENSITY.get(row.get('intensity'), '中等')}。",
        f"- 财运：{message(str(row.get('finance', '')))}",
        f"- 官运与规则：{message(str(row.get('official_career', '')))}",
        f"- 事业：{message(str(row.get('career', '')))}",
        f"- 学习：{message(str(row.get('study', '')))}",
        f"- 婚恋感情：{message(str(row.get('relationship', '')))}",
        f"- 朋友人际：{message(str(row.get('friends', '')))}",
        f"- 领导客户：{message(str(row.get('leadership', '')))}",
        f"- 子女家庭：{message(str(row.get('children_family', '')))}",
    ]


def lines_for(row: dict[str, object]) -> list[str]:
    age = int(row["age"])
    if age <= 6:
        return child_lines(row)
    if age <= 17:
        return teen_lines(row)
    if age <= 24:
        return young_lines(row)
    return adult_lines(row)


def build_markdown() -> str:
    analysis = json.loads(ANALYSIS_JSON.read_text(encoding="utf-8-sig"))
    rows = analysis["result"]["final_report"]["annual_luck"]["rows"]
    base = BASE_MD.read_text(encoding="utf-8-sig")
    cut = base.find("## 年度流年表")
    prefix = base[:cut].rstrip() if cut != -1 else base.rstrip()
    xuanze_start = prefix.find("## 择日参考")
    phase_start = prefix.find("## 年度阶段摘要")
    if xuanze_start != -1 and phase_start != -1 and phase_start > xuanze_start:
        prefix = prefix[:xuanze_start].rstrip() + "\n\n" + prefix[phase_start:].lstrip()
    parts = [
        prefix,
        "",
        "## 年度流年表（按年龄阶段调整）",
        "",
        "说明：小时候不看财运、事业和婚恋，主要看健康、学业启蒙、父母家庭和成长环境；成年后才逐步加入事业、财务、婚恋、领导客户等主题。",
        "",
    ]
    for row in rows:
        parts.append(f"### {row['year']}年（{ganzhi(str(row['ganzhi']))}）")
        parts.extend(lines_for(row))
        parts.append("")
    return "\n".join(parts).strip() + "\n"


def escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build_pdf(markdown: str) -> None:
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
    h1 = ParagraphStyle("H1", parent=base, fontSize=17, leading=22, spaceAfter=8, textColor=colors.HexColor("#222222"))
    h2 = ParagraphStyle(
        "H2", parent=base, fontSize=13.5, leading=18, spaceBefore=8, spaceAfter=5, textColor=colors.HexColor("#333333")
    )
    h3 = ParagraphStyle(
        "H3", parent=base, fontSize=11.5, leading=15.5, spaceBefore=5, spaceAfter=3, textColor=colors.HexColor("#444444")
    )
    bullet = ParagraphStyle("Bullet", parent=base, leftIndent=9, firstLineIndent=-7)
    story = []
    for line in markdown.splitlines():
        if not line.strip():
            story.append(Spacer(1, 3))
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
    markdown = build_markdown()
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
