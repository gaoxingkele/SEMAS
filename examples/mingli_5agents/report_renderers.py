"""Human-readable report renderers for mingli final reports."""

from __future__ import annotations

import re
from typing import Any


TOPIC_TITLES_ZH = {
    "finance": "财运",
    "official_career": "官运与规则压力",
    "career": "事业",
    "study": "学业与学习",
    "relationship": "婚恋与感情",
    "friends": "朋友与团队",
    "leadership": "领导、客户与机构关系",
    "children_family": "子女、家庭与创作输出",
}

CATEGORY_ZH = {
    "wealth": "财务资源",
    "authority": "官运规则",
    "expression": "表达输出",
    "learning": "学习迁移",
    "friends": "同辈协作",
    "relationship": "关系经营",
}

INTENSITY_ZH = {
    "high-volatility": "波动偏高",
    "constructive": "建设性较强",
    "active": "活跃",
    "moderate": "中等",
    "symbolic": "象征性",
}

MESSAGE_ZH = {
    "stronger money-management and asset-allocation theme; avoid leverage.": "财务管理和资产配置主题增强，避免杠杆和冲动承诺。",
    "cash flow can move quickly; require budgets and written terms.": "现金流变化较快，预算和书面条款要先行。",
    "steady finances favor planning over speculation.": "财务宜稳，重计划胜过投机。",
    "rules, title, audits, leadership, or institutional pressure become central.": "规则、头衔、审查、领导或机构压力成为中心议题。",
    "authority relationships can improve through preparation and evidence.": "与权威、制度和上级相关的关系，可通过准备和证据改善。",
    "keep compliance and reporting rhythm clear.": "合规、汇报节奏和流程边界要清楚。",
    "output, visibility, sales, teaching, or public delivery are emphasized.": "输出、曝光、销售、教学或公开交付被强调。",
    "career advancement depends on discipline, contracts, and role clarity.": "事业推进依赖纪律、合同和角色清晰。",
    "career choices are tied to revenue, assets, operations, or family duties.": "事业选择容易和收入、资产、运营或家庭责任绑定。",
    "career push is strong but should be paced to avoid conflict.": "事业推动力较强，但节奏需放缓以避免冲突。",
    "career improves through consistent execution.": "事业靠持续执行和稳定节奏改善。",
    "best suited for study, credentials, research, travel, or strategic review.": "适合学习、证照、研究、出行或战略复盘。",
    "learning is useful when converted into a practical system.": "学习若能转成可执行系统更有用。",
    "study should support immediate work needs.": "学习宜服务当前工作需要。",
    "marriage and romantic issues may connect with money, home, or duty.": "婚恋议题可能与金钱、家庭或责任相连。",
    "peer influence is strong; protect couple boundaries from outside noise.": "同辈影响较强，伴侣边界需避免外界噪音干扰。",
    "direct speech can heat up conflict; slow down before decisions.": "直接表达容易升温冲突，重大决定前要放慢。",
    "relationships benefit from predictable communication.": "关系经营受益于稳定、可预期的沟通。",
    "friends and partners are active; choose collaborators carefully.": "朋友和合作对象更活跃，需谨慎选择伙伴。",
    "competition and comparison can increase.": "竞争和比较感可能增加。",
    "networking is useful when roles are explicit.": "人脉合作在角色清楚时更有用。",
    "leaders, managers, clients, or regulators carry more weight.": "领导、客户、管理者或监管因素权重上升。",
    "visibility can attract support if communication stays measured.": "曝光度提升时，克制表达更容易换来支持。",
    "leadership ties improve through reliability.": "与领导/客户的关系靠可靠执行而改善。",
    "children, students, juniors, or creative outputs require attention.": "子女、学生、晚辈或创作输出需要更多关注。",
    "family responsibility and practical support are highlighted.": "家庭责任和实际支持被强调。",
    "family ties need steady time and clear expectations.": "家庭关系需要稳定投入和清晰期待。",
}

RISK_BOUNDARY_ZH = {
    "Do not treat symbolic finance language as investment advice.": "不要把象征性财务语言当作现实投资依据。",
    "Do not treat symbolic relationship or family language as a decision rule.": "不要把象征性的感情或家庭语言当作决策规则。",
    "Verify contracts, policy, and workplace obligations through ordinary channels.": "合同、制度和职场义务必须通过现实渠道核验。",
    "Use as a reflective prompt, not as a deterministic prediction.": "仅作反思提示，不作确定性预测。",
}

ZIWEI_PALACE_ZH = {
    "Ming": "命宫",
    "Siblings": "兄弟宫",
    "Spouse": "夫妻宫",
    "Children": "子女宫",
    "Wealth": "财帛宫",
    "Health": "疾厄宫",
    "Travel": "迁移宫",
    "Friends": "交友宫",
    "Career": "官禄宫",
    "Property": "田宅宫",
    "Fortune": "福德宫",
    "Parents": "父母宫",
}

ZIWEI_STAR_ZH = {
    "Ziwei": "紫微",
    "Tianfu": "天府",
    "Taiyang": "太阳",
    "Taiyin": "太阴",
    "Wuqu": "武曲",
    "Tiantong": "天同",
    "Lianzhen": "廉贞",
    "Tianji": "天机",
}

ZIWEI_TRANSFORMATION_ZH = {
    "lu": "禄",
    "quan": "权",
    "ke": "科",
    "ji": "忌",
}

QIMEN_PATTERN_ZH = {
    "stable planning": "稳定谋划",
    "active transition": "主动转换",
}

QIMEN_DOOR_ZH = {
    "Open": "开门",
    "Rest": "休门",
    "Life": "生门",
    "Harm": "伤门",
    "Delusion": "杜门",
    "View": "景门",
    "Death": "死门",
    "Fear": "惊门",
}

QIMEN_STAR_ZH = {
    "Tianpeng": "天蓬",
    "Tianrui": "天芮",
    "Tianchong": "天冲",
    "Tianfu": "天辅",
    "Tianqin": "天禽",
    "Tianxin": "天心",
    "Tianzhu": "天柱",
    "Tianren": "天任",
}

QIMEN_SPIRIT_ZH = {
    "Chief": "值符",
    "Snake": "螣蛇",
    "Moon": "太阴",
    "Six Harmony": "六合",
    "White Tiger": "白虎",
    "Black Tortoise": "玄武",
    "Nine Earth": "九地",
    "Nine Heaven": "九天",
}

QIMEN_PALACE_ZH = {
    "Kan": "坎宫",
    "Kun": "坤宫",
    "Zhen": "震宫",
    "Xun": "巽宫",
    "Center": "中宫",
    "Qian": "乾宫",
    "Dui": "兑宫",
    "Gen": "艮宫",
    "Li": "离宫",
}

QIMEN_DIRECTION_ZH = {
    "North": "北",
    "Southwest": "西南",
    "East": "东",
    "Southeast": "东南",
    "Center": "中",
    "Northwest": "西北",
    "West": "西",
    "Northeast": "东北",
    "South": "南",
}

QIMEN_JUDGMENT_ZH = {
    "constructive": "建设性",
    "supportive": "有支持",
    "mixed": "平杂",
    "cautious": "宜谨慎",
    "provider": "外部提供",
}

QIMEN_TOPIC_ZH = {
    "career": "事业",
    "wealth": "财务",
    "relationship": "关系",
    "study": "学习",
    "health": "身心节律",
}

ASTRO_SIGN_ZH = {
    "Aries": "白羊座",
    "Taurus": "金牛座",
    "Gemini": "双子座",
    "Cancer": "巨蟹座",
    "Leo": "狮子座",
    "Virgo": "处女座",
    "Libra": "天秤座",
    "Scorpio": "天蝎座",
    "Sagittarius": "射手座",
    "Capricorn": "摩羯座",
    "Aquarius": "水瓶座",
    "Pisces": "双鱼座",
}

ELEMENT_ZH = {
    "Wood": "木",
    "Fire": "火",
    "Earth": "土",
    "Metal": "金",
    "Water": "水",
}

TEN_GOD_ZH = {
    "peer": "比劫/同类",
    "expression": "食伤/表达",
    "wealth": "财星/资源",
    "authority": "官杀/规则",
    "resource": "印星/支持",
}

BAZI_STRUCTURE_ZH = {
    "balanced": "五行分布较均衡",
    "element-skewed": "五行分布偏斜",
}

STEM_ZH = {
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

BRANCH_ZH = {
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

ANNUAL_TOPIC_LABELS_ZH = {
    "finance": "财运",
    "official_career": "官运",
    "career": "事业",
    "study": "学业",
    "relationship": "婚恋感情",
    "friends": "朋友团队",
    "leadership": "领导客户",
    "children_family": "子女家庭",
}

WEEKDAY_ZH = {
    "Monday": "周一",
    "Tuesday": "周二",
    "Wednesday": "周三",
    "Thursday": "周四",
    "Friday": "周五",
    "Saturday": "周六",
    "Sunday": "周日",
}

RATING_ZH = {
    "favorable": "偏吉",
    "mixed": "平稳",
    "cautious": "慎用",
}

TWELVE_OFFICER_ZH = {
    "Establish": "建日",
    "Remove": "除日",
    "Full": "满日",
    "Balance": "平日",
    "Settle": "定日",
    "Hold": "执日",
    "Break": "破日",
    "Danger": "危日",
    "Complete": "成日",
    "Receive": "收日",
    "Open": "开日",
    "Close": "闭日",
}

MANSION_ZH = {
    "Horn": "角宿",
    "Neck": "亢宿",
    "Root": "氐宿",
    "Room": "房宿",
    "Heart": "心宿",
    "Tail": "尾宿",
    "Winnowing Basket": "箕宿",
    "Dipper": "斗宿",
    "Ox": "牛宿",
    "Girl": "女宿",
    "Emptiness": "虚宿",
    "Rooftop": "危宿",
    "Encampment": "室宿",
    "Wall": "壁宿",
    "Stride": "奎宿",
    "Mound": "娄宿",
    "Stomach": "胃宿",
    "Hairy Head": "昴宿",
    "Net": "毕宿",
    "Turtle Beak": "觜宿",
    "Three Stars": "参宿",
    "Well": "井宿",
    "Ghost": "鬼宿",
    "Willow": "柳宿",
    "Star": "星宿",
    "Extended Net": "张宿",
    "Wings": "翼宿",
    "Chariot": "轸宿",
}

ACTIVITY_ZH = {
    "planning": "规划",
    "starting routines": "建立日常节奏",
    "setting direction": "确定方向",
    "clearing blockers": "清理阻碍",
    "repairs": "修整修补",
    "decluttering": "整理清理",
    "gathering resources": "整合资源",
    "social contact": "社交往来",
    "inventory": "盘点",
    "negotiation": "沟通谈判",
    "contracts review": "合同复核",
    "mediation": "协调调停",
    "stabilizing work": "稳定工作",
    "family duties": "家庭事务",
    "documentation": "文书归档",
    "implementation": "执行落实",
    "maintenance": "维护",
    "keeping commitments": "守成履约",
    "ending stale patterns": "结束旧模式",
    "risk review": "风险复盘",
    "caution": "谨慎检查",
    "inspection": "检查",
    "contingency planning": "预案准备",
    "delivery": "交付",
    "public output": "公开输出",
    "closing milestones": "收尾里程碑",
    "collection": "回收整理",
    "learning review": "学习复盘",
    "resource intake": "资源吸收",
    "launches": "发布启动",
    "meetings": "会议会面",
    "travel planning": "出行规划",
    "rest": "休整",
    "private review": "内部复盘",
    "avoid major launches": "避免重大启动",
}

AVOID_ZH = {
    "major launches": "重大启动",
    "large irreversible commitments": "大额或不可逆承诺",
    "high-stakes decisions": "高风险事项",
    "overexpansion": "过度扩张",
    "unclear financial promises": "不清晰的金钱承诺",
    "treating symbolic timing as certainty": "把象征择时当成确定结果",
}


def render_chinese_markdown(final_report: dict[str, Any]) -> str:
    """Render a concise Chinese Markdown report from a structured final report."""
    return _postprocess_chinese_markdown("\n".join(_clean_chinese_report_lines(final_report)), final_report)


_GANZHI_STEM_ZH = {
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
_GANZHI_BRANCH_ZH = {
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

_CHINESE_REPORT_REPLACEMENTS = {
    "CLI Person": "案例对象",
    "Safety Case": "安全边界案例",
    "Suzhou, Jiangsu, China": "中国江苏苏州",
    "China/Jiangsu/Suzhou": "中国/江苏/苏州",
    "Suzhou": "苏州",
    "Jiangsu": "江苏",
    "Nanjing": "南京",
    "Taurus": "金牛座",
    "Death": "死门",
    "Zhen": "震宫",
    "Siblings": "兄弟宫",
    "Taiyang": "太阳",
    "Mingli five-agent report for Reference Provider Case": "命理五智能体研判报告：参考来源案例",
    "Reference Provider Case": "参考来源案例",
    "Cancer": "巨蟹座",
    "production_ready": "生产就绪",
    "external_structured": "外部结构化来源",
    "external_bazi": "外部八字",
    "external_ziwei": "外部紫微",
    "external_qimen": "外部奇门",
    "external_astrology": "外部西占",
    "external_xuanze": "外部择日",
    "Well": "井宿",
    "reference launch": "参考启动事项",
    "reference avoid": "参考避忌事项",
    "Mingli five-agent report for Demo Person": "命理五智能体研判报告：演示案例",
    "Mingli five-agent report for Chinese Topic Case": "命理五智能体研判报告：中文主题案例",
    "Demo Person": "演示案例",
    "Chinese Topic Case": "中文主题案例",
    "unspecified": "未说明",
    "male": "男",
    "female": "女",
    "Sanming, Fujian, 中国": "中国福建三明",
    "中国/Fujian/Sanming": "中国/福建/三明",
    "Sanming": "三明",
    "Fujian": "福建",
    "Hangzhou, Zhejiang, China": "中国浙江杭州",
    "China/Zhejiang/Hangzhou": "中国/浙江/杭州",
    "Hangzhou": "杭州",
    "Zhejiang": "浙江",
    "China": "中国",
    "auto": "自动",
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
    "Metal": "金",
    "Wood": "木",
    "Water": "水",
    "Fire": "火",
    "Earth": "土",
    "Parents": "父母宫",
    "Fortune": "福德宫",
    "Children": "子女宫",
    "Spouse": "夫妻宫",
    "Friends": "交友宫",
    "Career": "事业宫",
    "Wealth": "财帛宫",
    "Rest": "休门",
    "Open": "开门",
    "Close": "闭门",
    "Establish": "建日",
    "Remove": "除日",
    "Full": "满日",
    "Balance": "平日",
    "Gen": "艮宫",
    "Dui": "兑宫",
    "Aries": "白羊座",
    "Libra": "天秤座",
    "Virgo": "处女座",
    "Leo": "狮子座",
    "Neck": "亢宿",
    "Root": "氐宿",
    "Room": "房宿",
    "Heart": "心宿",
    "Tail": "尾宿",
    "Winnowing Basket": "箕宿",
    "Dipper": "斗宿",
    "pass": "通过",
    "True": "是",
    "ready_with_provider_gaps": "存在来源缺口",
    "professional": "专业来源",
    "lunar_python": "本地历法库",
    "symbolic_scaffold": "符号脚手架",
    "symbolic": "符号级",
    "fallback": "备用",
    "xuanze_offline": "离线择日规则",
    "offline_rule_scaffold": "离线规则脚手架",
    "ziping_pattern": "子平格局",
    "strength_support": "旺衰扶抑",
    "blind_school_workflow": "盲派流程",
    "shensha_nayin": "神煞纳音",
    "tiaohou": "调候",
    "image_symbol_reading": "象法读法",
    "new_school_simplified": "新派简化",
    "data_validation_boundary": "资料校验边界",
    "yang5": "阳五",
    "yang7": "阳七",
    "mixed": "平中有杂",
    "cautious": "谨慎",
    "favorable": "较有利",
    "launches": "启动事项",
    "meetings": "会面",
    "travel planning": "出行规划",
    "treating symbolic timing as certainty": "把象征性时机当作确定结果",
    "rest": "休整",
    "private review": "私下复盘",
    "avoid major launches": "避免重大启动",
    "major launches": "重大启动",
    "large irreversible commitments": "大额或不可逆承诺",
    "high-stakes decisions": "高风险决策",
    "planning": "规划",
    "starting routines": "建立日常节奏",
    "setting direction": "确定方向",
    "clearing blockers": "清理阻碍",
    "repairs": "修补",
    "decluttering": "整理",
    "gathering resources": "聚集资源",
    "social contact": "社交接触",
    "inventory": "盘点",
    "overexpansion": "过度扩张",
    "unclear financial promises": "不清楚的金钱承诺",
    "negotiation": "谈判",
    "contracts review": "合同复核",
    "mediation": "协调",
    "career entry": "事业起步",
    "responsibility growth": "责任增长",
    "wealth": "财务",
    "career": "事业",
    "study": "学习",
    "relationship": "关系",
    "health": "健康",
}


def _postprocess_chinese_markdown(text: str, final_report: dict[str, Any]) -> str:
    """Remove code-like provider instructions and translate common symbolic tokens."""
    lines: list[str] = []
    skipped_command = False
    for raw_line in text.splitlines():
        line = raw_line
        if line.startswith("- 环境变量：") or line.startswith("- 认证命令：") or line.startswith("- 就绪检查："):
            if not skipped_command:
                lines.append("- 生产接入：需要配置经审查的外部排盘来源，并在生产就绪检查中记录来源证明。")
                skipped_command = True
            continue
        skipped_command = False
        lines.append(_translate_common_chinese_report_tokens(_translate_ganzhi_tokens(line)))
    processed = "\n".join(lines)
    name = final_report.get("birth_profile", {}).get("name") if isinstance(final_report.get("birth_profile"), dict) else ""
    if name and name != "Demo Person":
        processed = processed.replace("# Mingli five-agent report for " + str(name), f"# 命理五智能体研判报告：{name}")
    return _replace_untranslated_latin_tokens(processed)


def _translate_common_chinese_report_tokens(text: str) -> str:
    for source, target in sorted(_CHINESE_REPORT_REPLACEMENTS.items(), key=lambda item: len(item[0]), reverse=True):
        text = text.replace(source, target)
    text = text.replace("、", "、")
    return text


def _replace_untranslated_latin_tokens(text: str) -> str:
    """Keep Chinese reports free of raw English while leaving structured data untouched."""
    return re.sub(r"[A-Za-z][A-Za-z0-9_+-]*(?: [A-Za-z][A-Za-z0-9_+-]*)*", "未译项", text)


def _translate_ganzhi_tokens(text: str) -> str:
    def repl(match: re.Match[str]) -> str:
        stem = _GANZHI_STEM_ZH.get(match.group(1), match.group(1))
        branch = _GANZHI_BRANCH_ZH.get(match.group(2), match.group(2))
        return stem + branch

    return re.sub(
        r"\b(Jia|Yi|Bing|Ding|Wu|Ji|Geng|Xin|Ren|Gui)"
        r"(Zi|Chou|Yin|Mao|Chen|Si|Wu|Wei|Shen|You|Xu|Hai)\b",
        repl,
        text,
    )


CLEAN_TOPIC_TITLES_ZH = {
    "finance": "财运",
    "official_career": "官运与规则压力",
    "career": "事业",
    "study": "学业与学习",
    "relationship": "婚恋与感情",
    "friends": "朋友与团队",
    "leadership": "领导、客户与机构关系",
    "children_family": "子女、家庭与创作输出",
}

CLEAN_CATEGORY_ZH = {
    "wealth": "财务资源",
    "authority": "官运规则",
    "expression": "表达输出",
    "learning": "学习迁移",
    "friends": "同辈协作",
    "relationship": "关系经营",
}

CLEAN_INTENSITY_ZH = {
    "high-volatility": "波动偏高",
    "constructive": "建设性较强",
    "active": "活跃",
    "moderate": "中等",
    "symbolic": "象征性",
}

CLEAN_MESSAGE_ZH = {
    "stronger money-management and asset-allocation theme; avoid leverage.": "财务管理和资产配置主题增强，避免杠杆和冲动承诺。",
    "cash flow can move quickly; require budgets and written terms.": "现金流变化较快，预算和书面条款要先行。",
    "steady finances favor planning over speculation.": "财务宜稳，重计划胜过投机。",
    "rules, title, audits, leadership, or institutional pressure become central.": "规则、头衔、审查、领导或机构压力成为中心议题。",
    "authority relationships can improve through preparation and evidence.": "与权威、制度和上级相关的关系，可通过准备和证据改善。",
    "keep compliance and reporting rhythm clear.": "合规、汇报节奏和流程边界要清楚。",
    "output, visibility, sales, teaching, or public delivery are emphasized.": "输出、曝光、销售、教学或公开交付被强调。",
    "career advancement depends on discipline, contracts, and role clarity.": "事业推进依赖纪律、合同和角色清晰。",
    "career choices are tied to revenue, assets, operations, or family duties.": "事业选择容易和收入、资产、运营或家庭责任绑定。",
    "career push is strong but should be paced to avoid conflict.": "事业推动力较强，但节奏需放缓以避免冲突。",
    "career improves through consistent execution.": "事业靠持续执行和稳定节奏改善。",
    "best suited for study, credentials, research, travel, or strategic review.": "适合学习、证照、研究、出行或战略复盘。",
    "learning is useful when converted into a practical system.": "学习若能转成可执行系统更有用。",
    "study should support immediate work needs.": "学习宜服务当前工作需要。",
    "marriage and romantic issues may connect with money, home, or duty.": "婚恋议题可能与金钱、家庭或责任相连。",
    "peer influence is strong; protect couple boundaries from outside noise.": "同辈影响较强，伴侣边界需避免外界噪音干扰。",
    "direct speech can heat up conflict; slow down before decisions.": "直接表达容易升温冲突，重大决定前要放慢。",
    "relationships benefit from predictable communication.": "关系经营受益于稳定、可预期的沟通。",
    "friends and partners are active; choose collaborators carefully.": "朋友和合作对象更活跃，需要谨慎选择伙伴。",
    "competition and comparison can increase.": "竞争和比较感可能增加。",
    "networking is useful when roles are explicit.": "人脉合作在角色清楚时更有用。",
    "leaders, managers, clients, or regulators carry more weight.": "领导、客户、管理者或监管因素权重上升。",
    "visibility can attract support if communication stays measured.": "曝光度提升时，克制表达更容易换来支持。",
    "leadership ties improve through reliability.": "与领导、客户的关系靠可靠执行而改善。",
    "children, students, juniors, or creative outputs require attention.": "子女、学生、晚辈或创作输出需要更多关注。",
    "family responsibility and practical support are highlighted.": "家庭责任和实际支持被强调。",
    "family ties need steady time and clear expectations.": "家庭关系需要稳定投入和清晰期待。",
}


def _clean_chinese_report_lines(final_report: dict[str, Any]) -> list[str]:
    lines = [
        f"# {final_report['title']}",
        "",
        "## 出生资料核对",
        *_clean_birth_profile_lines(final_report.get("birth_profile", {})),
        "",
        "## 使用边界",
        "- 本报告仅用于文化研究、娱乐参考和算法演示。",
        "- 不应用于医疗、投资、婚姻、法律等重大决策。",
        "- 所有结论都是象征性解释，必须保留不确定性。",
        "",
        "## 四系统摘要",
        f"- 八字：{_clean_bazi_summary(final_report.get('bazi_profile', {}))}",
        f"- 紫微：{_clean_ziwei_summary(final_report.get('ziwei_profile', {}))}",
        f"- 奇门：{_clean_qimen_summary(final_report.get('qimen_profile', {}))}",
        f"- 西占：{_clean_astrology_summary(final_report.get('astrology_profile', {}))}",
    ]
    lines.extend(_clean_topic_synthesis_lines(final_report))
    lines.extend(_clean_data_overview_lines(final_report))
    lines.extend(_clean_provider_summary_lines(final_report.get("provider_summary", {})))
    lines.extend(_clean_bazi_profile_lines(final_report.get("bazi_profile", {})))
    lines.extend(_clean_ziwei_profile_lines(final_report.get("ziwei_profile", {})))
    lines.extend(_clean_qimen_profile_lines(final_report.get("qimen_profile", {})))
    lines.extend(_clean_xuanze_lines(final_report.get("auspicious_calendar", {})))
    lines.extend(_clean_annual_phase_lines(final_report.get("annual_luck", {})))
    lines.extend(_clean_annual_luck_lines(final_report.get("annual_luck", {})))
    lines.extend(_clean_monthly_luck_lines(final_report.get("monthly_luck", {})))
    return lines


def _clean_birth_profile_lines(birth_profile: Any) -> list[str]:
    if not isinstance(birth_profile, dict):
        return ["- 出生资料：未提供。"]
    minute = int(birth_profile.get("minute") or 0)
    annual_start = birth_profile.get("annual_start_year")
    annual_end = birth_profile.get("annual_end_year")
    annual_range = f"{annual_start}-{annual_end}" if annual_start and annual_end else "默认范围"
    return [
        (
            f"- 姓名：{birth_profile.get('name', '')}；性别：{birth_profile.get('gender', '')}；"
            f"出生地：{birth_profile.get('birthplace', '')}。"
        ),
        (
            f"- 公历时间：{birth_profile.get('birth_date', '')} {birth_profile.get('birth_time', '')}；"
            f"归一化时刻：{birth_profile.get('year', '')}-{birth_profile.get('month', '')}-"
            f"{birth_profile.get('day', '')} {birth_profile.get('hour', '')}:{minute:02d}。"
        ),
        (
            f"- 历法来源：{birth_profile.get('calendar_provider', '')}；"
            f"年度分析范围：{annual_range}。"
        ),
        (
            f"- 地理归一化：{birth_profile.get('birthplace_normalized', '')}；"
            f"区域：{birth_profile.get('birthplace_region', '')}；"
            f"经纬度：{birth_profile.get('latitude', '')}, {birth_profile.get('longitude', '')}；"
            f"时区：{birth_profile.get('timezone_offset', '')}。"
        ),
    ]


def _clean_topic_synthesis_lines(final_report: dict[str, Any]) -> list[str]:
    lines = ["", "## 主题综合"]
    for topic_key, topic in final_report.get("topic_synthesis", {}).items():
        annual = topic.get("annual_focus", {})
        monthly = topic.get("monthly_focus", {})
        lines.extend(
            [
                f"### {CLEAN_TOPIC_TITLES_ZH.get(topic_key, topic_key)}",
                f"- 年度焦点：{annual.get('year', '')}，{_clean_message(annual.get('message'))}",
                f"- 月度焦点：{monthly.get('year', '')}-{monthly.get('month', '')}，{_clean_message(monthly.get('message'))}",
                f"- 交叉证据：{_clean_evidence_summary(topic.get('evidence_summary', []))}",
                f"- 边界：{_clean_boundary(topic.get('risk_boundary'))}",
            ]
        )
    return lines


def _clean_data_overview_lines(final_report: dict[str, Any]) -> list[str]:
    annual_range = final_report.get("annual_luck", {}).get("range", {})
    monthly_range = final_report.get("monthly_luck", {}).get("range", {})
    return [
        "",
        "## 结构化数据概览",
        f"- 年度流年行数：{annual_range.get('count', 0)}",
        f"- 年度阶段摘要数：{len(final_report.get('annual_luck', {}).get('phase_summary', []))}",
        f"- 月度流月行数：{monthly_range.get('count', 0)}",
        f"- 主题综合数：{len(final_report.get('topic_synthesis', {}))}",
        f"- 文献审查：{final_report.get('source_review', {}).get('status')}",
        f"- 投票通过：{final_report.get('votes', {}).get('_summary', {}).get('passed')}",
    ]


def _clean_provider_summary_lines(summary: dict[str, Any]) -> list[str]:
    domains = summary.get("domains", {}) if isinstance(summary, dict) else {}
    labels = {"bazi": "八字/历法", "ziwei": "紫微斗数", "qimen": "奇门遁甲", "astrology": "西方占星", "xuanze": "择日/黄历"}
    lines = [
        "",
        "## 计算来源与生产就绪度",
        f"- 总体状态：{summary.get('status', '') if isinstance(summary, dict) else ''}",
        f"- 生产就绪：{'是' if isinstance(summary, dict) and summary.get('production_ready') is True else '否'}",
    ]
    if isinstance(domains, dict):
        for key, label in labels.items():
            item = domains.get(key, {})
            if isinstance(item, dict):
                lines.append(
                    f"- {label}：来源 {item.get('provider', '')}；质量 {item.get('provider_quality', '')}；"
                    f"状态 {item.get('status', '')}；生产就绪 {'是' if item.get('production_ready') else '否'}。"
                )
    lines.extend(_clean_provider_action_plan_lines(summary.get("action_plan", []) if isinstance(summary, dict) else []))
    return lines


def _clean_provider_action_plan_lines(action_plan: Any) -> list[str]:
    if not isinstance(action_plan, list) or not action_plan:
        return []
    labels = {"bazi": "八字/历法", "ziwei": "紫微斗数", "qimen": "奇门遁甲", "astrology": "西方占星", "xuanze": "择日/黄历"}
    lines = ["", "## 专业来源接入计划"]
    for item in action_plan:
        if not isinstance(item, dict):
            continue
        domain = str(item.get("domain", ""))
        lines.extend(
            [
                f"### {labels.get(domain, domain)}",
                f"- 当前质量：{item.get('provider_quality', '')}；原因：{_provider_gap_reason_zh(item.get('reason', ''))}",
                f"- 环境变量：{item.get('env_var') or '不适用'}；来源证明变量：{item.get('provenance_env_var') or '不适用'}",
                f"- 认证命令：{item.get('certification_command_template') or '不适用'}",
                f"- 就绪检查：{item.get('production_readiness_command_template') or '不适用'}",
            ]
        )
    return lines


def _clean_bazi_profile_lines(profile: dict[str, Any]) -> list[str]:
    pillars = profile.get("pillars", {}) if isinstance(profile, dict) else {}
    lines = ["", "## 八字结构与大运"]
    if isinstance(pillars, dict):
        lines.append(
            f"- 四柱：年 {pillars.get('year', '')}，月 {pillars.get('month', '')}，"
            f"日 {pillars.get('day', '')}，时 {pillars.get('hour', '')}。"
        )
    lines.append(f"- 日主：{profile.get('day_master', '')}；用神倾向：{profile.get('useful_element', '')}。")
    method_matrix = profile.get("method_matrix", [])
    if isinstance(method_matrix, list) and method_matrix:
        methods = [
            str(item.get("method"))
            for item in method_matrix
            if isinstance(item, dict) and item.get("method")
        ]
        if methods:
            lines.append(f"- 八字方法覆盖：{', '.join(methods)}。")
    major_luck = profile.get("major_luck", [])
    if isinstance(major_luck, list) and major_luck:
        lines.append("- 大运表：" + "；".join(_clean_luck_period(item) for item in major_luck[:4] if isinstance(item, dict)))
    return lines


def _clean_ziwei_profile_lines(profile: dict[str, Any]) -> list[str]:
    return [
        "",
        "## 紫微命盘摘要",
        f"- 命宫：{profile.get('ming_palace', '')}；身宫：{profile.get('body_palace', '')}。",
        f"- 四化：{_clean_ziwei_transformations(profile.get('four_transformations', {}))}。",
        f"- 大限数量：{len(profile.get('major_limits', [])) if isinstance(profile.get('major_limits'), list) else 0}。",
    ]


def _clean_qimen_profile_lines(profile: dict[str, Any]) -> list[str]:
    duty = profile.get("duty", {}) if isinstance(profile, dict) else {}
    return [
        "",
        "## 奇门九宫摘要",
        f"- 局式：{profile.get('yin_yang', '')}{profile.get('ju_number', '')}局。",
        f"- 值门：{duty.get('door', '')}；落宫：{duty.get('door_palace', '')}。",
        f"- 流年时机数量：{len(profile.get('annual_timing', [])) if isinstance(profile.get('annual_timing'), list) else 0}。",
    ]


def _clean_xuanze_lines(calendar: dict[str, Any]) -> list[str]:
    rows = calendar.get("rows", []) if isinstance(calendar, dict) else []
    lines = ["", "## 择日参考"]
    for row in rows[:7]:
        if isinstance(row, dict):
            lines.extend(
                [
                    f"### {row.get('date', '')}",
                    f"- 评级：{row.get('rating', '')}；十二值：{row.get('twelve_officer', '')}；二十八宿：{row.get('twenty_eight_mansion', '')}。",
                    f"- 宜：{_clean_list(row.get('suitable', []))}",
                    f"- 忌：{_clean_list(row.get('avoid', []))}",
                ]
            )
    return lines


def _clean_annual_phase_lines(annual_luck: dict[str, Any]) -> list[str]:
    summaries = annual_luck.get("phase_summary", []) if isinstance(annual_luck, dict) else []
    if not isinstance(summaries, list) or not summaries:
        return []
    lines = ["", "## 年度阶段摘要"]
    for item in summaries:
        if not isinstance(item, dict):
            continue
        lines.extend(
            [
                f"### {item.get('phase', '')}（{item.get('start_year', '')}-{item.get('end_year', '')}）",
                f"- 年龄范围：{item.get('start_age', '')}-{item.get('end_age', '')}；年度数：{item.get('year_count', '')}。",
                f"- 主导主题：{CLEAN_CATEGORY_ZH.get(str(item.get('dominant_category', '')), item.get('dominant_category', ''))}。",
                f"- 高波动年份：{_clean_list(item.get('high_volatility_years', []))}；建设性年份：{_clean_list(item.get('constructive_years', []))}。",
                f"- 源年度行：{_clean_list(item.get('source_row_indexes', []))}；阶段摘要是年度行压缩，不是确定性预测。",
            ]
        )
        highlights = item.get("topic_highlights", {})
        if isinstance(highlights, dict):
            for key, label in [("finance", "财运主线"), ("career", "事业主线"), ("relationship", "感情主线")]:
                topic = highlights.get(key, {})
                if isinstance(topic, dict):
                    lines.append(f"- {label}：{_clean_message(topic.get('dominant_message'))}")
    return lines


def _clean_annual_luck_lines(annual_luck: dict[str, Any]) -> list[str]:
    rows = annual_luck.get("rows", []) if isinstance(annual_luck, dict) else []
    lines = ["", "## 年度流年表"]
    for row in rows:
        if isinstance(row, dict):
            lines.extend(_clean_luck_row_lines(row, include_month=False))
    return lines if len(lines) > 2 else []


def _clean_monthly_luck_lines(monthly_luck: dict[str, Any]) -> list[str]:
    rows = monthly_luck.get("rows", []) if isinstance(monthly_luck, dict) else []
    lines = ["", "## 月度流月表"]
    for row in rows:
        if isinstance(row, dict):
            lines.extend(_clean_luck_row_lines(row, include_month=True))
    return lines if len(lines) > 2 else []


def _clean_luck_row_lines(row: dict[str, Any], *, include_month: bool) -> list[str]:
    title = f"{row.get('year', '')}-{int(row.get('month', 0)):02d}" if include_month else str(row.get("year", ""))
    pillar = _ganzhi_zh(str(row.get("ganzhi", "")))
    lines = [
        f"### {title}（{row.get('ganzhi', '')}）",
        (
            f"- 主轴：{title}{pillar}，"
            f"{CLEAN_CATEGORY_ZH.get(str(row.get('category', '')), row.get('category', ''))}；"
            f"强度：{CLEAN_INTENSITY_ZH.get(str(row.get('intensity', '')), row.get('intensity', ''))}。"
        ),
    ]
    lines.extend(_clean_bazi_evidence_lines(row, monthly=include_month))
    for field, label in [
        ("finance", "财运"),
        ("official_career", "官运"),
        ("career", "事业"),
        ("study", "学业"),
        ("relationship", "婚恋感情"),
        ("friends", "朋友团队"),
        ("leadership", "领导客户"),
        ("children_family", "子女家庭"),
    ]:
        lines.append(_clean_contextual_topic_line(label, row.get(field), row, monthly=include_month))
    return lines


def _clean_contextual_topic_line(label: str, message: Any, row: dict[str, Any], *, monthly: bool) -> str:
    evidence = row.get("bazi_evidence") if isinstance(row.get("bazi_evidence"), dict) else {}
    ten_god_key = "monthly_ten_gods" if monthly else "annual_ten_gods"
    ten_gods = evidence.get(ten_god_key) if isinstance(evidence.get(ten_god_key), dict) else {}
    active_luck = evidence.get("active_major_luck") if isinstance(evidence.get("active_major_luck"), dict) else {}
    matches = evidence.get("natal_pillar_matches") if isinstance(evidence.get("natal_pillar_matches"), list) else []
    title = f"{row.get('year', '')}-{int(row.get('month', 0)):02d}" if monthly else str(row.get("year", ""))
    pillar = _ganzhi_zh(str(row.get("ganzhi", "")))
    stem_ten = _ten_god_zh(ten_gods.get("stem", ""))
    branch_ten = _ten_god_zh(ten_gods.get("branch", ""))
    useful_state = _useful_state_zh(evidence.get("useful_state", ""))
    luck_label = _ganzhi_zh(active_luck.get("ganzhi", "")) if active_luck.get("ganzhi") else "未匹配"
    match_text = "、".join(
        _pillar_name_zh(str(item.get("pillar", ""))) for item in matches if isinstance(item, dict) and item.get("pillar")
    ) or "无"
    scope = "本月" if monthly else "本年"
    return (
        f"- {label}：判断：{_clean_message(message)}；"
        f"依据：{scope}{title}{pillar}，天干{stem_ten}、地支{branch_ten}，"
        f"大运{luck_label}，用神{useful_state}，原局同柱{match_text}。"
    )


def _clean_bazi_evidence_lines(row: dict[str, Any], *, monthly: bool = False) -> list[str]:
    evidence = row.get("bazi_evidence")
    if not isinstance(evidence, dict) or not evidence:
        return []
    ten_god_key = "monthly_ten_gods" if monthly else "annual_ten_gods"
    ten_gods = evidence.get(ten_god_key) if isinstance(evidence.get(ten_god_key), dict) else {}
    active_luck = evidence.get("active_major_luck") if isinstance(evidence.get("active_major_luck"), dict) else {}
    matches = evidence.get("natal_pillar_matches") if isinstance(evidence.get("natal_pillar_matches"), list) else []
    luck_label = _ganzhi_zh(active_luck.get("ganzhi", "")) if active_luck.get("ganzhi") else "未匹配"
    match_text = "、".join(
        _pillar_name_zh(str(item.get("pillar", ""))) for item in matches if isinstance(item, dict) and item.get("pillar")
    ) or "无"
    label = "流月依据" if monthly else "八字依据"
    title = f"{row.get('year', '')}-{int(row.get('month', 0)):02d}" if monthly else str(row.get("year", ""))
    pillar = _ganzhi_zh(str(row.get("ganzhi", "")))
    return [
        (
            f"- {label}：{title}{pillar}，十神 天干={_ten_god_zh(ten_gods.get('stem', ''))}、"
            f"地支={_ten_god_zh(ten_gods.get('branch', ''))}；大运={luck_label}；"
            f"用神状态={_useful_state_zh(evidence.get('useful_state', ''))}；原局同柱={match_text}。"
        )
    ]


def _clean_bazi_summary(profile: dict[str, Any]) -> str:
    return f"日主 {profile.get('day_master', '')}，用神倾向 {profile.get('useful_element', '')}，重视五行结构与大运节奏。"


def _clean_ziwei_summary(profile: dict[str, Any]) -> str:
    return f"命宫 {profile.get('ming_palace', '')}，身宫 {profile.get('body_palace', '')}，用于观察宫位主题和四化牵动。"


def _clean_ziwei_transformations(transformations: Any) -> str:
    if not isinstance(transformations, dict) or not transformations:
        return "未提供"
    labels = {"lu": "禄", "quan": "权", "ke": "科", "ji": "忌"}
    star_names = {
        "Ziwei": "紫微",
        "Tianfu": "天府",
        "Taiyang": "太阳",
        "Taiyin": "太阴",
        "Wuqu": "武曲",
        "Tiantong": "天同",
        "Lianzhen": "廉贞",
        "Tianji": "天机",
    }
    palace_names = {
        "Ming": "命宫",
        "Siblings": "兄弟宫",
        "Spouse": "夫妻宫",
        "Children": "子女宫",
        "Wealth": "财帛宫",
        "Health": "疾厄宫",
        "Travel": "迁移宫",
        "Friends": "交友宫",
        "Career": "官禄宫",
        "Property": "田宅宫",
        "Fortune": "福德宫",
        "Parents": "父母宫",
    }
    parts = []
    for key in ("lu", "quan", "ke", "ji"):
        item = transformations.get(key)
        if not isinstance(item, dict):
            continue
        star = star_names.get(str(item.get("star", "")), str(item.get("star", "")))
        palace = palace_names.get(str(item.get("palace", "")), str(item.get("palace", "")))
        parts.append(f"{labels.get(key, key)}：{star}入{palace}")
    return "；".join(parts) if parts else "未提供"


def _clean_qimen_summary(profile: dict[str, Any]) -> str:
    duty = profile.get("duty", {}) if isinstance(profile, dict) else {}
    return f"值门 {duty.get('door', '')}，落宫 {duty.get('door_palace', '')}，用于观察时机和行动节奏。"


def _clean_astrology_summary(profile: dict[str, Any]) -> str:
    return f"太阳 {profile.get('sun', '')}，月亮 {profile.get('moon', '')}，上升 {profile.get('ascendant', '')}，用于补充性格和周期视角。"


def _clean_message(value: Any) -> str:
    return CLEAN_MESSAGE_ZH.get(value, value if isinstance(value, str) else "")


def _clean_boundary(value: Any) -> str:
    if not isinstance(value, str):
        return "仅作反思提示，不作确定性预测。"
    if "finance" in value:
        return "不把象征性财务语言当作投资建议。"
    if "relationship" in value or "family" in value:
        return "不把象征性的感情或家庭语言当作决策规则。"
    if "contracts" in value or "workplace" in value:
        return "合同、制度和职场义务必须通过现实渠道核验。"
    return "仅作反思提示，不作确定性预测。"


def _clean_evidence_summary(value: Any) -> str:
    if not isinstance(value, list) or not value:
        return "未列明"
    return "；".join(_evidence_item_zh(item) for item in value[:6])


def _evidence_summary_zh(value: Any) -> str:
    return _clean_evidence_summary(value)


def _evidence_item_zh(value: Any) -> str:
    text = str(value)
    if text.startswith("BaZi annual "):
        return _bazi_summary_item_zh(text, "年度")
    if text.startswith("BaZi monthly "):
        return _bazi_summary_item_zh(text, "流月")
    return (
        text.replace("bazi:", "八字：")
        .replace("ziwei:", "紫微：")
        .replace("qimen:", "奇门：")
        .replace("astrology:", "西占：")
        .replace("day master", "日主")
        .replace("with useful element", "用神")
        .replace("palace", "宫")
        .replace("useful god", "用神")
        .replace("houses", "宫位")
    )


def _bazi_summary_item_zh(text: str, label: str) -> str:
    parts = text.split()
    pillar = _ganzhi_zh(parts[2]) if len(parts) > 2 else ""
    useful_state = text.rsplit("useful-state ", 1)[-1] if "useful-state " in text else ""
    return f"八字{label}{pillar}，用神状态{_useful_state_zh(useful_state)}"


def _clean_list(value: Any) -> str:
    if not isinstance(value, list) or not value:
        return "无"
    return "、".join(str(item) for item in value)


def _clean_luck_period(item: dict[str, Any]) -> str:
    return f"{item.get('start_year')}-{item.get('end_year')} {item.get('ganzhi')}"
    lines = [
        f"# {final_report['title']}",
        "",
        "## 使用边界",
        "- 本报告仅用于文化研究、娱乐参考和算法演示。",
        "- 不应用于医疗、投资、婚姻、法律等重大决策。",
        "- 所有结论都是象征性解释，必须保留不确定性。",
        "",
        "## 四系统摘要",
    ]
    lines.extend(f"- {_summary_zh(item)}" for item in final_report.get("summary", []))
    lines.extend(
        [
            "",
            "## 主题综合",
        ]
    )
    for topic_key, topic in final_report.get("topic_synthesis", {}).items():
        title = TOPIC_TITLES_ZH.get(topic_key, topic.get("label", topic_key))
        annual = topic.get("annual_focus", {})
        monthly = topic.get("monthly_focus", {})
        lines.extend(
            [
                f"### {title}",
                _topic_headline_zh(topic_key, topic),
                f"- 年度焦点：{annual.get('year', '')}，{_message_zh(annual.get('message', ''))}",
                f"- 月度焦点：{monthly.get('year', '')}-{monthly.get('month', '')}，{_message_zh(monthly.get('message', ''))}",
                f"- 交叉证据：{_evidence_summary_zh(topic.get('evidence_summary', []))}",
                f"- 边界：{_risk_boundary_zh(topic.get('risk_boundary', ''))}",
            ]
        )
    lines.extend(
        [
            "",
            "## 结构化数据概览",
            f"- 年度流年行数：{final_report['annual_luck']['range']['count']}",
            f"- 月度流年行数：{final_report['monthly_luck']['range']['count']}",
            f"- 主题综合数：{len(final_report.get('topic_synthesis', {}))}",
            f"- 文献审查：{final_report['source_review']['status']}",
            f"- 投票通过：{final_report['votes']['_summary']['passed']}",
        ]
    )
    if final_report.get("conflicts"):
        lines.extend(["", "## 冲突与保留意见"])
        lines.extend(f"- {item}" for item in final_report["conflicts"])
    lines.extend(_provider_summary_lines_zh(final_report.get("provider_summary", {})))
    lines.extend(_bazi_profile_lines_zh(final_report.get("bazi_profile", {})))
    lines.extend(_ziwei_profile_lines_zh(final_report.get("ziwei_profile", {})))
    lines.extend(_qimen_profile_lines_zh(final_report.get("qimen_profile", {})))
    lines.extend(_xuanze_lines_zh(final_report.get("auspicious_calendar", {})))
    lines.extend(_annual_phase_summary_lines_zh(final_report.get("annual_luck", {})))
    lines.extend(_annual_luck_lines_zh(final_report.get("annual_luck", {})))
    lines.extend(_monthly_luck_lines_zh(final_report.get("monthly_luck", {})))
    return "\n".join(lines)


def _provider_summary_lines_zh(summary: dict[str, Any]) -> list[str]:
    if not isinstance(summary, dict) or not summary:
        return []
    domains = summary.get("domains", {})
    if not isinstance(domains, dict) or not domains:
        return []
    labels = {
        "bazi": "八字/历法",
        "ziwei": "紫微斗数",
        "qimen": "奇门遁甲",
        "astrology": "西方占星",
        "xuanze": "择日/黄历",
    }
    lines = [
        "",
        "## 计算来源与生产就绪度",
        f"- 总体状态：{_provider_status_zh(summary.get('status'))}；生产就绪：{_yes_no_zh(summary.get('production_ready'))}。",
    ]
    blockers = summary.get("production_blockers", [])
    if isinstance(blockers, list):
        blocker_text = "、".join(labels.get(str(item), str(item)) for item in blockers) if blockers else "无"
        lines.append(f"- 生产阻塞项：{blocker_text}。")
    for key in ("bazi", "ziwei", "qimen", "astrology", "xuanze"):
        item = domains.get(key, {})
        if not isinstance(item, dict):
            continue
        boundary = "已接入专业来源" if item.get("production_ready") else "生产需替换为验证来源"
        lines.append(
            "- "
            f"{labels.get(key, key)}：来源 {item.get('provider', '')}；质量 {item.get('provider_quality', '')}；"
            f"状态 {_provider_status_zh(item.get('status'))}；生产就绪 {_yes_no_zh(item.get('production_ready'))}；"
            f"{boundary}"
        )
    if summary.get("boundary"):
        lines.append("- 边界：符号化后备适合研究演示；正式生产需接入并验证专业排盘/黄历来源。")
    lines.extend(_provider_action_plan_lines_zh(summary.get("action_plan", [])))
    return lines


def _provider_action_plan_lines_zh(action_plan: Any) -> list[str]:
    if not isinstance(action_plan, list) or not action_plan:
        return []
    labels = {
        "bazi": "八字/历法",
        "ziwei": "紫微斗数",
        "qimen": "奇门遁甲",
        "astrology": "西方占星",
        "xuanze": "择日/黄历",
    }
    lines = ["", "## 专业来源接入计划"]
    for item in action_plan:
        if not isinstance(item, dict):
            continue
        domain = str(item.get("domain", ""))
        lines.extend(
            [
                f"### {labels.get(domain, domain)}",
                f"- 当前质量：{item.get('provider_quality', '')}；原因：{_provider_gap_reason_zh(item.get('reason', ''))}",
                f"- 环境变量：{item.get('env_var') or '不适用'}；来源证明变量：{item.get('provenance_env_var') or '不适用'}",
                f"- 认证命令：{item.get('certification_command_template') or '不适用'}",
                f"- 就绪检查：{item.get('production_readiness_command_template') or '不适用'}",
            ]
        )
    return lines


def _provider_gap_reason_zh(value: Any) -> str:
    text = str(value or "")
    if "verified almanac provider" in text or "tongshu" in text:
        return "生产级择日需要替换为经审查的通书/黄历专业来源。"
    if "verified provider" in text or "Production reports" in text:
        return "生产级报告需要接入经审查的专业排盘来源。"
    if not text:
        return "生产级使用需要补齐专业来源。"
    return text


def _provider_status_zh(value: Any) -> str:
    return {
        "production_ready": "生产就绪",
        "ready_with_provider_gaps": "存在来源缺口",
        "professional": "专业来源",
        "fallback": "后备/脚手架",
    }.get(str(value), str(value))


def _yes_no_zh(value: Any) -> str:
    return "是" if value is True else "否"


def _topic_headline_zh(topic_key: str, topic: dict[str, Any]) -> str:
    title = TOPIC_TITLES_ZH.get(topic_key, topic.get("label", topic_key))
    annual = topic.get("annual_focus", {})
    category = CATEGORY_ZH.get(str(annual.get("category", "")), "综合主题")
    intensity = INTENSITY_ZH.get(str(annual.get("intensity", "")), "象征性")
    year = annual.get("year", "所选年份")
    return f"{title}：{year} 年主轴为{category}，强度为{intensity}；以下综合八字、紫微、奇门和西占信号，仅作文化参考。"


def _message_zh(message: Any) -> str:
    if not isinstance(message, str):
        return ""
    return MESSAGE_ZH.get(message, message)


def _risk_boundary_zh(message: Any) -> str:
    if not isinstance(message, str):
        return "仅作反思提示，不作确定性预测。"
    return RISK_BOUNDARY_ZH.get(message, message)


def _annual_luck_lines_zh(annual_luck: dict[str, Any]) -> list[str]:
    rows = annual_luck.get("rows", [])
    if not rows:
        return []
    lines = ["", "## 年度流年表"]
    for row in rows:
        lines.extend(
            [
                f"### {row.get('year', '')}（{_ganzhi_zh(row.get('ganzhi', ''))}）",
                f"- 主轴：{CATEGORY_ZH.get(str(row.get('category', '')), row.get('category', ''))}；强度：{INTENSITY_ZH.get(str(row.get('intensity', '')), row.get('intensity', ''))}。",
                *_bazi_evidence_lines_zh(row),
                *_topic_detail_lines_zh(row),
            ]
        )
    return lines


def _bazi_evidence_lines_zh(row: dict[str, Any], *, monthly: bool = False) -> list[str]:
    evidence = row.get("bazi_evidence")
    if not isinstance(evidence, dict) or not evidence:
        return []
    ten_god_key = "monthly_ten_gods" if monthly else "annual_ten_gods"
    ten_gods = evidence.get(ten_god_key) if isinstance(evidence.get(ten_god_key), dict) else {}
    active_luck = evidence.get("active_major_luck") if isinstance(evidence.get("active_major_luck"), dict) else {}
    matches = evidence.get("natal_pillar_matches") if isinstance(evidence.get("natal_pillar_matches"), list) else []
    luck_label = _ganzhi_zh(active_luck.get("ganzhi", "")) if active_luck.get("ganzhi") else "未匹配"
    match_text = "、".join(_pillar_name_zh(str(item.get("pillar", ""))) for item in matches if isinstance(item, dict)) or "无"
    label = "流月依据" if monthly else "八字依据"
    return [
        f"- {label}：十神 天干={_ten_god_zh(ten_gods.get('stem', ''))}、地支={_ten_god_zh(ten_gods.get('branch', ''))}；大运={luck_label}；用神状态={_useful_state_zh(evidence.get('useful_state', ''))}；原局同柱={match_text}。"
    ]


def _ten_god_zh(value: Any) -> str:
    return TEN_GOD_ZH.get(str(value), str(value or ""))


def _useful_state_zh(value: Any) -> str:
    return {
        "dominant_element_reinforced": "忌偏重/主导五行被强化",
        "useful_element_activated": "用神被激活",
        "useful_element_present": "用神出现",
        "neutral_or_indirect": "中性或间接",
    }.get(str(value), str(value or ""))


def _pillar_name_zh(value: str) -> str:
    return {
        "year": "年柱",
        "month": "月柱",
        "day": "日柱",
        "hour": "时柱",
    }.get(value, value)


def _annual_phase_summary_lines_zh(annual_luck: dict[str, Any]) -> list[str]:
    summaries = annual_luck.get("phase_summary", [])
    if not isinstance(summaries, list) or not summaries:
        return []
    lines = ["", "## 年度阶段摘要"]
    for item in summaries:
        if not isinstance(item, dict):
            continue
        dominant = CATEGORY_ZH.get(str(item.get("dominant_category", "")), str(item.get("dominant_category", "")))
        high_volatility = _year_list_text(item.get("high_volatility_years", []))
        constructive = _year_list_text(item.get("constructive_years", []))
        lines.extend(
            [
                f"### {item.get('phase', '')}（{item.get('start_year', '')}-{item.get('end_year', '')}）",
                f"- 年龄范围：{item.get('start_age', '')}-{item.get('end_age', '')}；年度数：{item.get('year_count', '')}。",
                f"- 主导主题：{dominant}。",
                f"- 高波动年份：{high_volatility}；建设性年份：{constructive}。",
                f"- 源年度行：{_year_list_text(item.get('source_row_indexes', []))}；边界：阶段摘要是年度行压缩，不是确定性预测。",
            ]
        )
        highlights = item.get("topic_highlights", {})
        if isinstance(highlights, dict):
            career = highlights.get("career", {})
            relationship = highlights.get("relationship", {})
            finance = highlights.get("finance", {})
            if isinstance(finance, dict):
                lines.append(f"- 财运主线：{_message_zh(finance.get('dominant_message', ''))}")
            if isinstance(career, dict):
                lines.append(f"- 事业主线：{_message_zh(career.get('dominant_message', ''))}")
            if isinstance(relationship, dict):
                lines.append(f"- 感情主线：{_message_zh(relationship.get('dominant_message', ''))}")
    return lines


def _year_list_text(value: Any) -> str:
    if not isinstance(value, list) or not value:
        return "无"
    return "、".join(str(item) for item in value)


def _monthly_luck_lines_zh(monthly_luck: dict[str, Any]) -> list[str]:
    rows = monthly_luck.get("rows", [])
    if not rows:
        return []
    lines = ["", "## 月度流月表"]
    for row in rows:
        lines.extend(
            [
                f"### {row.get('year', '')}-{int(row.get('month', 0)):02d}（{_ganzhi_zh(row.get('ganzhi', ''))}）",
                f"- 主轴：{CATEGORY_ZH.get(str(row.get('category', '')), row.get('category', ''))}；强度：{INTENSITY_ZH.get(str(row.get('intensity', '')), row.get('intensity', ''))}。",
                *_bazi_evidence_lines_zh(row, monthly=True),
                *_topic_detail_lines_zh(row),
            ]
        )
    return lines


def _topic_detail_lines_zh(row: dict[str, Any]) -> list[str]:
    return [
        f"- {label}：{_message_zh(row.get(key, ''))}"
        for key, label in ANNUAL_TOPIC_LABELS_ZH.items()
    ]


def _xuanze_lines_zh(calendar: dict[str, Any]) -> list[str]:
    rows = calendar.get("rows", [])
    if not rows:
        return []
    basis = calendar.get("basis", {})
    lines = [
        "",
        "## 择日参考",
        f"- 范围：{calendar.get('range', {}).get('start_date', '')} 至 {calendar.get('range', {}).get('end_date', '')}；来源：{basis.get('provider', '')}。",
    ]
    for row in rows:
        lines.extend(
            [
                f"### {row.get('date', '')}（{WEEKDAY_ZH.get(str(row.get('weekday', '')), row.get('weekday', ''))}，{_ganzhi_zh(row.get('ganzhi', ''))}）",
                (
                    f"- 评级：{RATING_ZH.get(str(row.get('rating', '')), row.get('rating', ''))}；"
                    f"{'黄道' if row.get('huangdao') else '非黄道'}；"
                    f"值日：{TWELVE_OFFICER_ZH.get(str(row.get('twelve_officer', '')), row.get('twelve_officer', ''))}；"
                    f"二十八宿：{MANSION_ZH.get(str(row.get('twenty_eight_mansion', '')), row.get('twenty_eight_mansion', ''))}。"
                ),
                f"- 宜：{_list_zh(row.get('suitable', []), ACTIVITY_ZH)}",
                f"- 忌：{_list_zh(row.get('avoid', []), AVOID_ZH)}",
                f"- 推荐时辰：{_recommended_hours_zh(row.get('recommended_hours', []))}",
            ]
        )
    caution = calendar.get("caution")
    if caution:
        lines.append("- 边界：择日结果仅作文化参考，现实安排仍需核验天气、交通、合同和个人条件。")
    return lines


def _bazi_profile_lines_zh(profile: dict[str, Any]) -> list[str]:
    if not isinstance(profile, dict) or not profile:
        return []
    pillars = profile.get("pillars", {})
    luck_start = profile.get("luck_start", {})
    major_luck = profile.get("major_luck", [])
    lines = [
        "",
        "## 八字结构与大运",
        (
            f"- 结构：{BAZI_STRUCTURE_ZH.get(str(profile.get('structure', '')), profile.get('structure', ''))}；"
            f"日主：{STEM_ZH.get(str(profile.get('day_master', '')), profile.get('day_master', ''))}；"
            f"旺势：{ELEMENT_ZH.get(str(profile.get('dominant_element', '')), profile.get('dominant_element', ''))}；"
            f"用神倾向：{ELEMENT_ZH.get(str(profile.get('useful_element', '')), profile.get('useful_element', ''))}。"
        ),
        f"- 四柱：{_pillars_zh(pillars)}",
        (
            f"- 起运：{luck_start.get('years', 0)}年{luck_start.get('months', 0)}月"
            f"{luck_start.get('days', 0)}日；方向：{'顺行' if luck_start.get('forward', True) else '逆行'}。"
        ),
    ]
    strength = profile.get("strength_analysis", {})
    pattern = profile.get("pattern_analysis", {})
    useful = profile.get("useful_god_analysis", {})
    tiaohou = profile.get("tiaohou_analysis", {})
    method_matrix = profile.get("method_matrix", [])
    if isinstance(strength, dict) and isinstance(pattern, dict) and isinstance(useful, dict):
        adjustment = tiaohou.get("adjustment", "") if isinstance(tiaohou, dict) else ""
        lines.append(
            "- BaZi method check: "
            f"strength={strength.get('strength', '')}; "
            f"pattern={pattern.get('pattern', '')}; "
            f"useful={useful.get('useful_element', '')}; "
            f"tiaohou={adjustment}."
        )
    if isinstance(method_matrix, list) and method_matrix:
        methods = [
            str(item.get("method"))
            for item in method_matrix
            if isinstance(item, dict) and item.get("method")
        ]
        lines.append(f"- Method coverage: {', '.join(methods)}.")
    school_debate = profile.get("school_debate", {})
    if isinstance(school_debate, dict) and school_debate.get("votes"):
        consensus = school_debate.get("consensus", {})
        if isinstance(consensus, dict):
            primary = "、".join(str(item) for item in consensus.get("primary_schools", [])[:4])
            auxiliary = "、".join(str(item) for item in consensus.get("auxiliary_schools", [])[:4])
            lines.append(
                "- 八字流派辩论："
                f"主断流派为{primary or '待校准'}；"
                f"辅助流派为{auxiliary or '无'}；"
                f"{school_debate.get('agent_count', 0)}个子智能体参与，"
                f"保留{len(school_debate.get('conflicts', []))}处争议。"
            )
    if isinstance(major_luck, list) and major_luck:
        lines.append("- 大运表：")
        for item in major_luck:
            if not isinstance(item, dict):
                continue
            lines.append(
                "  - "
                f"{item.get('start_year', '')}-{item.get('end_year', '')}："
                f"{_ganzhi_zh(item.get('ganzhi', ''))}，"
                f"{item.get('start_age', '')}-{item.get('end_age', '')}岁"
            )
    caution = profile.get("caution")
    if caution:
        lines.append("- 边界：大运与用神为象征性结构分析，需结合现实经历校验。")
    return lines


def _ziwei_profile_lines_zh(profile: dict[str, Any]) -> list[str]:
    if not isinstance(profile, dict) or not profile:
        return []
    lines = [
        "",
        "## 紫微命盘摘要",
        (
            f"- 命宫：{_ziwei_palace_zh(str(profile.get('ming_palace', '')))}；"
            f"身宫：{_ziwei_palace_zh(str(profile.get('body_palace', '')))}；"
            f"主星：{_stars_zh(profile.get('major_stars', []))}。"
        ),
    ]
    highlighted = profile.get("highlighted_palaces", [])
    if isinstance(highlighted, list) and highlighted:
        lines.append("- 重点宫位：")
        for palace in highlighted:
            if not isinstance(palace, dict):
                continue
            markers = "、".join(_ziwei_marker_zh(item) for item in palace.get("markers", [])) or "参考"
            lines.append(
                "  - "
                f"{_ziwei_palace_zh(str(palace.get('name', '')))}（{markers}）："
                f"主星{_stars_zh(palace.get('primary_stars', []))}；"
                f"强度{_ziwei_strength_zh(str(palace.get('strength', '')))}。"
            )
    transformations = profile.get("four_transformations", {})
    if isinstance(transformations, dict) and transformations:
        lines.append("- 四化：")
        for key in ("lu", "quan", "ke", "ji"):
            item = transformations.get(key, {})
            if isinstance(item, dict):
                lines.append(
                    "  - "
                    f"{ZIWEI_TRANSFORMATION_ZH.get(key, key)}："
                    f"{_ziwei_star_zh(str(item.get('star', '')))}入"
                    f"{_ziwei_palace_zh(str(item.get('palace', '')))}"
                )
    major_limits = profile.get("major_limits", [])
    if isinstance(major_limits, list) and major_limits:
        lines.append("- 大限表：")
        for item in major_limits[:6]:
            if not isinstance(item, dict):
                continue
            lines.append(
                "  - "
                f"{item.get('start_year', '')}-{item.get('end_year', '')}："
                f"{_ziwei_palace_zh(str(item.get('palace', '')))}，"
                f"{item.get('start_age', '')}-{item.get('end_age', '')}岁"
            )
    annual = profile.get("annual_activation", [])
    if isinstance(annual, list) and annual:
        lines.append("- 流年宫位：")
        for item in annual[:5]:
            if isinstance(item, dict):
                lines.append(
                    "  - "
                    f"{item.get('year', '')}：{_ziwei_palace_zh(str(item.get('palace', '')))}"
                )
    if profile.get("caution"):
        lines.append("- 边界：紫微宫位与四化为象征性结构分析，需结合现实经历校验。")
    return lines


def _qimen_profile_lines_zh(profile: dict[str, Any]) -> list[str]:
    if not isinstance(profile, dict) or not profile:
        return []
    duty = profile.get("duty", {})
    lines = [
        "",
        "## 奇门九宫摘要",
        (
            f"- 局式：{'阳遁' if profile.get('yin_yang') == 'yang' else '阴遁'}"
            f"{profile.get('ju_number', '')}局；"
            f"值门：{QIMEN_DOOR_ZH.get(str(duty.get('door', '')), duty.get('door', ''))}"
            f"落{QIMEN_PALACE_ZH.get(str(duty.get('door_palace', '')), duty.get('door_palace', ''))}；"
            f"值星：{QIMEN_STAR_ZH.get(str(duty.get('star', '')), duty.get('star', ''))}"
            f"落{QIMEN_PALACE_ZH.get(str(duty.get('star_palace', '')), duty.get('star_palace', ''))}；"
            f"神：{QIMEN_SPIRIT_ZH.get(str(duty.get('spirit', '')), duty.get('spirit', ''))}。"
        ),
    ]
    useful = profile.get("useful_gods", {})
    if isinstance(useful, dict) and useful:
        lines.append("- 用神落宫：")
        for key in ("career", "wealth", "relationship", "study", "health"):
            item = useful.get(key, {})
            if not isinstance(item, dict):
                continue
            lines.append(
                "  - "
                f"{QIMEN_TOPIC_ZH.get(key, key)}："
                f"{QIMEN_PALACE_ZH.get(str(item.get('palace', '')), item.get('palace', ''))}"
                f"（{QIMEN_DIRECTION_ZH.get(str(item.get('direction', '')), item.get('direction', ''))}），"
                f"{QIMEN_DOOR_ZH.get(str(item.get('door', '')), item.get('door', ''))}/"
                f"{QIMEN_STAR_ZH.get(str(item.get('star', '')), item.get('star', ''))}/"
                f"{QIMEN_SPIRIT_ZH.get(str(item.get('spirit', '')), item.get('spirit', ''))}，"
                f"判断：{QIMEN_JUDGMENT_ZH.get(str(item.get('judgment', '')), item.get('judgment', ''))}"
            )
    palaces = profile.get("highlighted_palaces", [])
    if isinstance(palaces, list) and palaces:
        lines.append("- 重点宫位：")
        for palace in palaces:
            if not isinstance(palace, dict):
                continue
            lines.append(
                "  - "
                f"{QIMEN_PALACE_ZH.get(str(palace.get('name', '')), palace.get('name', ''))}"
                f"（{QIMEN_DIRECTION_ZH.get(str(palace.get('direction', '')), palace.get('direction', ''))}，"
                f"{ELEMENT_ZH.get(str(palace.get('element', '')), palace.get('element', ''))}）："
                f"{QIMEN_DOOR_ZH.get(str(palace.get('door', '')), palace.get('door', ''))}/"
                f"{QIMEN_STAR_ZH.get(str(palace.get('star', '')), palace.get('star', ''))}/"
                f"{QIMEN_SPIRIT_ZH.get(str(palace.get('spirit', '')), palace.get('spirit', ''))}，"
                f"天盘{STEM_ZH.get(str(palace.get('heaven_stem', '')), palace.get('heaven_stem', ''))}，"
                f"地盘{STEM_ZH.get(str(palace.get('earth_stem', '')), palace.get('earth_stem', ''))}。"
            )
    flags = profile.get("pattern_flags", [])
    if isinstance(flags, list) and flags:
        lines.append("- 格局提示：")
        for item in flags:
            if isinstance(item, dict):
                lines.append(
                    "  - "
                    f"{QIMEN_PATTERN_ZH.get(str(item.get('name', '')), item.get('name', ''))}："
                    f"{QIMEN_PALACE_ZH.get(str(item.get('palace', '')), item.get('palace', ''))}"
                )
    timing = profile.get("annual_timing", [])
    if isinstance(timing, list) and timing:
        lines.append("- 流年时机：")
        for item in timing[:5]:
            if isinstance(item, dict):
                lines.append(
                    "  - "
                    f"{item.get('year', '')}：{QIMEN_PALACE_ZH.get(str(item.get('palace', '')), item.get('palace', ''))}，"
                    f"{QIMEN_DOOR_ZH.get(str(item.get('door', '')), item.get('door', ''))}，"
                    f"{QIMEN_JUDGMENT_ZH.get(str(item.get('judgment', '')), item.get('judgment', ''))}"
                )
    if profile.get("caution"):
        lines.append("- 边界：奇门盘为象征性时机与方位结构，不替代现实计划与验证。")
    return lines


def _stars_zh(values: Any) -> str:
    if not isinstance(values, list):
        return "未列明"
    rendered = [_ziwei_star_zh(str(item)) for item in values]
    return "、".join(rendered) if rendered else "未列明"


def _ziwei_marker_zh(value: Any) -> str:
    return {"ming": "命宫", "body": "身宫"}.get(str(value), str(value))


def _ziwei_strength_zh(value: str) -> str:
    return {
        "primary": "主轴",
        "supporting": "辅助",
        "variable": "变动",
        "latent": "潜伏",
        "provider": "外部提供",
    }.get(value, value)


def _pillars_zh(pillars: Any) -> str:
    if not isinstance(pillars, dict):
        return "未列明"
    labels = [("年", "year"), ("月", "month"), ("日", "day"), ("时", "hour")]
    return "；".join(f"{label}柱{_ganzhi_zh(pillars.get(key, ''))}" for label, key in labels)


def _list_zh(values: Any, mapping: dict[str, str]) -> str:
    if not isinstance(values, list):
        return ""
    rendered = [mapping.get(str(item), str(item)) for item in values]
    return "、".join(rendered) if rendered else "未列明"


def _recommended_hours_zh(values: Any) -> str:
    if not isinstance(values, list) or not values:
        return "未列明"
    rendered = []
    for item in values:
        if isinstance(item, dict):
            branch = BRANCH_ZH.get(str(item.get("branch", "")), str(item.get("branch", "")))
            element = ELEMENT_ZH.get(str(item.get("element", "")), str(item.get("element", "")))
            rendered.append(f"{item.get('start', '')}-{item.get('end', '')}（{branch}时，{element}）")
        else:
            rendered.append(str(item))
    return "、".join(rendered)


def _ganzhi_zh(value: Any) -> str:
    text = str(value or "")
    for stem, stem_zh in STEM_ZH.items():
        if text.startswith(stem):
            branch = text[len(stem):]
            return stem_zh + BRANCH_ZH.get(branch, branch)
    return text


def _summary_zh(item: Any) -> str:
    if not isinstance(item, str):
        return str(item)
    if item.startswith("BaZi structure is ") and " with " in item:
        body = item.removeprefix("BaZi structure is ").removesuffix(".")
        structure, _, element_part = body.partition(" with ")
        element = element_part.removesuffix(" emphasis")
        structure_zh = BAZI_STRUCTURE_ZH.get(structure, structure)
        element_zh = ELEMENT_ZH.get(element, element)
        return f"八字结构显示{structure_zh}，{element_zh}元素较突出。"
    if item.startswith("Zi Wei Ming palace sits at "):
        body = item.removeprefix("Zi Wei Ming palace sits at ").removesuffix(".")
        palace, _, star = body.partition(" with ")
        star = star.removesuffix(" emphasis")
        return f"紫微命宫落在{_ziwei_palace_zh(palace)}，主星侧重{_ziwei_star_zh(star) or '未列明'}。"
    if item.startswith("Qi Men pattern suggests "):
        body = item.removeprefix("Qi Men pattern suggests ").removesuffix(".")
        pattern, _, door_part = body.partition(" through ")
        door = door_part.removesuffix(" door")
        return f"奇门格局提示{QIMEN_PATTERN_ZH.get(pattern, pattern)}，值门为{QIMEN_DOOR_ZH.get(door, door)}。"
    if item.startswith("Western chart highlights "):
        body = item.removeprefix("Western chart highlights ").removesuffix(".")
        if body.startswith("Sun ") and " and Ascendant " in body:
            sun, ascendant = body.removeprefix("Sun ").split(" and Ascendant ", 1)
            return f"西占命盘重点为太阳{ASTRO_SIGN_ZH.get(sun, sun)}、上升{ASTRO_SIGN_ZH.get(ascendant, ascendant)}。"
        return f"西占命盘重点为 {body}。"
    return item


def _ziwei_palace_zh(value: str) -> str:
    return ZIWEI_PALACE_ZH.get(value, value)


def _ziwei_star_zh(value: str) -> str:
    return ZIWEI_STAR_ZH.get(value, value)
