"""Generate local mingli book-derived Codex skills.

The generated skills follow the book-to-skill idea: extract usable method
structure, keep SKILL.md concise, and put school details in references.
"""

from __future__ import annotations

from pathlib import Path


SKILLS_HOME = Path.home() / ".codex" / "skills"


BAZI_BOOKS = [
    {
        "slug": "mingli-bazi-yuanhai-ziping",
        "title": "渊海子平",
        "school": "子平格局与十神源流",
        "source": "Wikimedia Commons / National Library of China scan: https://commons.wikimedia.org/wiki/File:NLC416-15jh007754-99036_%E6%B7%B5%E6%B5%B7%E5%AD%90%E5%B9%B3_%E5%AD%90%E5%B9%B3%E7%9C%9F%E8%A9%AE.pdf",
        "local": "external/mingli_books/bazi/yuanhai_ziping_ziping_zhenquan.pdf",
        "frameworks": [
            "先以月令立纲，再看天干透出和地支根气。",
            "十神不是标签，要看是否得令、透干、通根、成局。",
            "格局成立重在清纯；混杂、冲破、失令会使同一十神转为反面。",
            "大运流年只承接或破坏原局主线，不能脱离原局另造命局。",
        ],
        "layers": [
            "一层：月令定主气，识别财、官、印、食伤、比劫的基本结构。",
            "二层：透干通根定真假，分清显性力量和暗藏力量。",
            "三层：看成格、破格、救应，判断人生主线是否稳定。",
            "四层：用大运流年验证格局是否被承接、冲破或转化。",
        ],
    },
    {
        "slug": "mingli-bazi-ziping-zhenquan",
        "title": "子平真诠",
        "school": "格局成败与用神纯杂",
        "source": "same NLC scan bundled with Yuanhai Ziping above; use independent textual verification before quoting.",
        "local": "external/mingli_books/bazi/yuanhai_ziping_ziping_zhenquan.pdf",
        "frameworks": [
            "论命先看格局成败，不先陷入日主强弱的单点判断。",
            "用神要清，忌神要制，喜神要护；混杂则层次下降。",
            "成格不等于一生顺，破格也不等于一生败，要看运来成败转换。",
            "判断职业、权力、财运、婚姻时，先问该主题是否属于原局主线。",
        ],
        "layers": [
            "一层：定格局名称和格局条件。",
            "二层：判用神是否得令、得地、得助。",
            "三层：找破格点、救应点和混杂点。",
            "四层：把大运流年放入成败链条，而不是逐年套吉凶词。",
        ],
    },
    {
        "slug": "mingli-bazi-sanming-tonghui",
        "title": "三命通会",
        "school": "百科型古法综合",
        "source": "Chinese classics catalogues and Wikisource/CTEXT references; download source still requires stricter public-domain verification.",
        "local": "",
        "frameworks": [
            "把格局、神煞、纳音、刑冲合害、岁运并看，但主次必须分明。",
            "古诀用于提出假设，不可直接替代原局结构和事实校准。",
            "特殊格局、神煞、纳音只在与主线同向时加权。",
            "适合做广谱检查：查漏补缺、发现异常配置、提出反例。",
        ],
        "layers": [
            "一层：先用常规格局和十神主线定骨架。",
            "二层：以三命通会类目检查特殊格、神煞、纳音和宫位。",
            "三层：用岁运刑冲合害验证是否应事。",
            "四层：所有古诀必须回到真实事件或可解释的人生主题。",
        ],
    },
    {
        "slug": "mingli-bazi-ditiansui",
        "title": "滴天髓",
        "school": "气势、体用、流通",
        "source": "public-domain classical text references; verify edition before direct quotation.",
        "local": "",
        "frameworks": [
            "不把五行当静态数量，而看气势如何流动。",
            "先辨体，再辨用，再看保护链和流通断点。",
            "清浊、寒暖、燥湿、顺逆会改变十神表现。",
            "事件判断重在气势被引发、被阻断、被转化的年份。",
        ],
        "layers": [
            "一层：识别全局气势和主导五行。",
            "二层：画出体、用、保护、流通链。",
            "三层：找冲断点、过旺点、枯竭点和转化点。",
            "四层：大运流年按修复、承接、破坏、反噬四类判断。",
        ],
    },
    {
        "slug": "mingli-bazi-qiongtong-baojian",
        "title": "穷通宝鉴",
        "school": "调候月令",
        "source": "public-domain classical text references; verify edition before direct quotation.",
        "local": "",
        "frameworks": [
            "月令气候优先，先看寒暖燥湿，再谈格局发挥。",
            "同一日主在不同月份取用不同，不能固定套喜忌。",
            "调候不是全部吉凶，但决定人能否稳定发挥。",
            "学业、健康、状态、贵人环境常先从调候失衡处显现。",
        ],
        "layers": [
            "一层：按出生月识别寒暖燥湿和季节偏性。",
            "二层：定第一调候用神和辅助用神。",
            "三层：看调候之神是否透出、通根、受伤。",
            "四层：流年流月重点看是否补足或破坏气候平衡。",
        ],
    },
    {
        "slug": "mingli-bazi-shenfeng-tongkao",
        "title": "神峰通考",
        "school": "病药与实践校验",
        "source": "public-domain classical text references; verify edition before direct quotation.",
        "local": "",
        "frameworks": [
            "先找命局之病，再找药；没有病药链，喜忌容易空泛。",
            "强弱判断要服务于病药，不是最终结论。",
            "对古法格局保持批判，重视实际应验和反证。",
            "流年应事看药到病除、病重药轻、药被冲破。",
        ],
        "layers": [
            "一层：列出命局主要病点。",
            "二层：确定药神、辅药和忌药。",
            "三层：看大运是否送药或加病。",
            "四层：流年流月按病药变化落到健康、学业、事业、婚姻等主题。",
        ],
    },
    {
        "slug": "mingli-bazi-hengmen",
        "title": "格局横门断",
        "school": "横门格局断法",
        "source": "local examples document requested by user; original DOCX not currently present in repository scan, use prior extracted method notes only.",
        "local": "",
        "frameworks": [
            "重视格局横向比较：同一命盘由多个流派分别下断，再看哪条线最能解释事实。",
            "语言输出要有指向性，少套话，多给可验证断言。",
            "年龄阶段要合逻辑：儿童重点看健康、学业、父母，不乱谈财运。",
            "年度和月度必须独立推演，不能复制固定句式。",
        ],
        "layers": [
            "一层：定命盘主格和可疑格。",
            "二层：列出每一格对人生主题的具体断言。",
            "三层：用事实年份筛掉解释力弱的格。",
            "四层：输出强断言、弱断言和待校准点。",
        ],
    },
]


ZIWEI = {
    "slug": "mingli-ziwei",
    "title": "紫微斗数综合",
    "source": "Archive.org metadata: https://archive.org/metadata/20210924_20210924_0431 ; candidate text PDF local file requires completion check.",
    "local": "external/mingli_books/ziwei/ziwei_doushu_quanshu_text.pdf",
}


XINGZUO = {
    "slug": "mingli-xingzuo",
    "title": "西方星座占星综合",
    "source": "William Lilly, Christian Astrology, Archive.org: https://archive.org/download/b30338724/b30338724.pdf",
    "local": "external/mingli_books/xingzuo/william_lilly_christian_astrology_1647.pdf",
}


def main() -> int:
    for book in BAZI_BOOKS:
        write_bazi_book_skill(book)
    write_bazi_all_skill()
    write_ziwei_skill()
    write_xingzuo_skill()
    return 0


def write_bazi_book_skill(book: dict[str, object]) -> None:
    root = SKILLS_HOME / str(book["slug"])
    (root / "references").mkdir(parents=True, exist_ok=True)
    (root / "agents").mkdir(parents=True, exist_ok=True)
    title = str(book["title"])
    slug = str(book["slug"])
    skill = f"""---
name: {slug}
description: 使用《{title}》对应的八字命理流派进行分析。适用于八字排盘、格局判断、用神取法、大运流年流月研判、命理报告校验、与其他八字流派辩论时调用。
---

# {title} 八字流派

## 使用原则

- 先读取 `references/method.md`，再下判断。
- 只把本流派作为一个子智能体，不要替代其他流派。
- 所有断语必须落到命盘证据：四柱、月令、十神、格局、用神、大运、流年或流月。
- 遇到事实校准信息，事实优先；本流派负责修正假设，不强压事实。
- 输出必须是中文、通俗、少套话，有明确判断强弱。

## 分层流程

1. 原局层：定本书流派最重视的结构。
2. 大运层：判断主结构被承接、破坏、修复还是转化。
3. 流年层：逐年独立分析刑冲合害、十神引动和主题落点。
4. 流月层：逐月独立分析五行流通和用神喜忌，不复制年度模板。
5. 校准层：列出命中、矛盾、待查三类证据。

## 输出格式

- 本流派主断
- 支持证据
- 反对证据
- 与其他流派可能冲突之处
- 需要用户补充的事实年份
"""
    method = method_text(book)
    write(root / "SKILL.md", skill)
    write(root / "references" / "method.md", method)
    write_openai_yaml(root, f"{title}八字", "八字流派子智能体", f"Use ${slug} to analyze a BaZi chart with the {title} school.")


def method_text(book: dict[str, object]) -> str:
    frameworks = "\n".join(f"- {item}" for item in book["frameworks"])  # type: ignore[index]
    layers = "\n".join(f"- {item}" for item in book["layers"])  # type: ignore[index]
    return f"""# {book['title']} 方法结构

## 来源

- 书名：{book['title']}
- 流派定位：{book['school']}
- 来源线索：{book['source']}
- 本地文件：{book['local'] or '未确认完整本地文件'}

## 核心框架

{frameworks}

## 层次化分析

{layers}

## 事件判断

- 财运：先看财星是否属于原局主线，再看大运流年是否保护财星；儿童和学生阶段不把财运作为主断。
- 官运/事业：看官杀、印、格局成败、权力规则是否形成闭环。
- 学业：看印星、食伤、调候、月令承接和考试年份的稳定性。
- 婚姻感情：看日支、财官、夫妻宫冲合刑害和大运是否引动。
- 父母子女：父母看年月与印财，子女看食伤、时柱和对应宫位。
- 健康：看五行偏枯、调候失衡、日支时柱受冲和岁运压力。

## 冲突处理

- 本书流派给出强结论时，仍要接受其他流派反驳。
- 如果本流派只给出象意而无结构证据，降为辅助。
- 如果事实年份与本流派冲突，记录为校准点，不删除。

## 版权和引用边界

本 skill 保存的是方法结构和学习笔记，不保存完整原文。引用原书时只给短句或转述，并标注版本来源。
"""


def write_bazi_all_skill() -> None:
    root = SKILLS_HOME / "mingli-bazi-all"
    (root / "references").mkdir(parents=True, exist_ok=True)
    (root / "agents").mkdir(parents=True, exist_ok=True)
    skill = """---
name: mingli-bazi-all
description: 综合多个八字命理流派进行群体智能分析。适用于需要同时调用渊海子平、子平真诠、三命通会、滴天髓、穷通宝鉴、神峰通考、横门断等子智能体，对命盘、大运、流年、流月进行辩论、投票和综合判断的场景。
---

# 八字综合流派评估

## 必须调用的子智能体

- `mingli-bazi-yuanhai-ziping`
- `mingli-bazi-ziping-zhenquan`
- `mingli-bazi-sanming-tonghui`
- `mingli-bazi-ditiansui`
- `mingli-bazi-qiongtong-baojian`
- `mingli-bazi-shenfeng-tongkao`
- `mingli-bazi-hengmen`

## 工作流

1. 先排四柱，确认出生资料、时区、历法和时辰不确定性。
2. 每个子智能体独立给出原局、大运、流年、流月判断。
3. 每个子智能体必须列出支持证据和反对证据。
4. 裁判层把结论分为：一致强支持、二对一冲突、多流派分裂、证据不足。
5. 对用户报告只输出综合结论，不堆砌术语。

## 决策规则

- 八字原局主线优先于单个神煞。
- 调候可否定状态发挥，但不能单独决定富贵贫贱。
- 格局可定人生主线，但必须被大运和事实校准。
- 体用流通可解释成败机制，必须指出保护链是否断裂。
- 横门断法负责提出强断言，但强断言必须被其他流派检查。

## 输出要求

- 不要套模板。
- 每一年、每个月都要独立计算，不复制固定句式。
- 儿童阶段重点看健康、学业、父母和环境，不乱谈财运。
- 所有结论标注置信度：高、中、低。
- 出现冲突时先写冲突，不要假装一致。
"""
    debate = """# 八字群体智能辩论规则

## 子智能体角色

| 子智能体 | 主责 | 典型反驳 |
|---|---|---|
| 渊海子平 | 月令、格局、十神源流 | 反驳只看强弱、不看格局 |
| 子平真诠 | 格局清纯、成败、用神 | 反驳用神混杂和破格误判 |
| 三命通会 | 古法广谱检查 | 反驳遗漏特殊格和辅助符号 |
| 滴天髓 | 气势、体用、流通 | 反驳静态五行数量化 |
| 穷通宝鉴 | 调候、月份、寒暖燥湿 | 反驳忽略季节状态 |
| 神峰通考 | 病药、实践校验 | 反驳空泛喜忌 |
| 横门断 | 强断言、事实筛选 | 反驳语言含糊和套话 |

## 投票

- 原局主线：格局类、体用类、调候类至少两方支持才可定为高置信。
- 流年事件：必须有原局触发、大运背景、流年刑冲合害三项中的两项。
- 流月事件：必须逐月列出干支、五行、十神和合冲刑害，不得套用年度结论。
- 事实校准：真实事件优先，所有流派必须能解释已知事实，否则降权。
"""
    write(root / "SKILL.md", skill)
    write(root / "references" / "debate.md", debate)
    write_openai_yaml(root, "八字综合评估", "多流派辩论综合", "Use $mingli-bazi-all to synthesize a BaZi chart through multiple school sub-agents.")


def write_ziwei_skill() -> None:
    root = SKILLS_HOME / ZIWEI["slug"]
    (root / "references").mkdir(parents=True, exist_ok=True)
    (root / "agents").mkdir(parents=True, exist_ok=True)
    skill = f"""---
name: {ZIWEI['slug']}
description: 使用紫微斗数进行命盘分析。适用于紫微排盘、命宫身宫、十二宫、四化、大限、流年、婚姻子女事业财帛疾厄迁移等宫位分析，以及与八字、星座进行交叉验证。
---

# 紫微斗数综合

## 使用原则

- 先读取 `references/method.md`。
- 紫微以宫位网络为主，不用单星孤断。
- 命宫、身宫、三方四正、大限、流年必须同看。
- 当前本地 PDF 来源需要完整性复核，未完成前不要长引原文。

## 分层流程

1. 命身层：看命宫、身宫和主星组合，定人格和主线。
2. 宫位层：十二宫分别看事业、夫妻、子女、财帛、疾厄、迁移等主题。
3. 三方四正层：看核心宫位的支援、冲照和牵连。
4. 四化层：禄、权、科、忌分别解释资源、权力、名声、阻滞。
5. 限运层：大限定十年主题，流年定具体引动。
6. 交叉层：与八字的十神和流年互相验证。
"""
    method = f"""# 紫微斗数方法结构

## 来源

- 参考书：紫微斗数全书等传统紫微资料。
- 来源线索：{ZIWEI['source']}
- 本地文件：{ZIWEI['local']}，当前需检查是否完整下载。

## 决策规则

- 不能只看命宫主星，要看三方四正。
- 夫妻宫判断婚姻，要同时看福德、迁移、官禄和大限流年。
- 子女宫判断子女，要看子女宫、田宅、疾厄、父母宫和流年触发。
- 官禄宫判断事业，要看命宫、财帛、迁移和四化权科。
- 疾厄宫判断健康，只能做风险提示，不做医学诊断。
- 流年落宫只说明主题被点亮，必须结合大限和四化才可下断。

## 与八字协同

- 八字给时间和五行机制，紫微给宫位场景。
- 八字说“财星动”，紫微要查财帛、夫妻、田宅是否同动。
- 八字说“官杀压身”，紫微要查官禄、迁移、疾厄是否有压力。
- 两者冲突时输出冲突，要求事实年份校准。
"""
    write(root / "SKILL.md", skill)
    write(root / "references" / "method.md", method)
    write_openai_yaml(root, "紫微斗数综合", "紫微宫位限运分析", "Use $mingli-ziwei to analyze a Zi Wei Dou Shu chart with palace and limit logic.")


def write_xingzuo_skill() -> None:
    root = SKILLS_HOME / XINGZUO["slug"]
    (root / "references").mkdir(parents=True, exist_ok=True)
    (root / "agents").mkdir(parents=True, exist_ok=True)
    skill = f"""---
name: {XINGZUO['slug']}
description: 使用西方星座占星进行本命盘和运势分析。适用于太阳、月亮、上升、行星、宫位、相位、年度过境、推运、关系与事业分析，并可与八字和紫微斗数交叉验证。
---

# 西方星座占星综合

## 使用原则

- 先读取 `references/method.md`。
- 不只看太阳星座，必须看上升、月亮、行星、宫位和相位。
- 没有精确出生时间时，所有宫位和上升判断降权。
- 与八字、紫微合参时，星座只做另一套象征语言和时间触发参考。

## 分层流程

1. 本命层：太阳、月亮、上升和个人行星定性格与驱动力。
2. 宫位层：第十宫看事业地位，第七宫看婚姻合作，第五宫看恋爱子女，第八宫看危机转化。
3. 相位层：合、冲、刑、拱、六合解释力量配合或冲突。
4. 过境层：木星土星火星等年度触发对应机会、压力和行动。
5. 合参层：与八字流年、紫微流年宫位对照。
"""
    method = f"""# 西方占星方法结构

## 来源

- 参考书：William Lilly, Christian Astrology.
- 来源线索：{XINGZUO['source']}
- 本地文件：{XINGZUO['local']}，当前文件需检查完整性后再做全文引用。

## 决策规则

- 太阳看核心生命方向，月亮看情绪习惯，上升看外在反应和身体节律。
- 第十宫和中天看事业、名望、权力位置。
- 第七宫看婚姻、合作、公开对手。
- 第五宫看恋爱、子女、创作和表现。
- 第八宫看死亡、危机、共享资源和深层转化。
- 土星、火星、冥王星触发时偏压力、冲突和结构重整；木星、金星、太阳触发时偏扩张、曝光和资源。

## 与东方命理协同

- 八字强在干支时间和五行机制。
- 紫微强在宫位场景。
- 星座强在心理动力、关系模式和过境节奏。
- 三者一致时提高置信度；三者冲突时保留分歧，不强行平均。
"""
    write(root / "SKILL.md", skill)
    write(root / "references" / "method.md", method)
    write_openai_yaml(root, "西方星座占星", "本命盘和过境分析", "Use $mingli-xingzuo to analyze natal astrology and transit timing.")


def write(path: Path, text: str) -> None:
    path.write_text(text.strip() + "\n", encoding="utf-8")


def write_openai_yaml(root: Path, display_name: str, short_description: str, default_prompt: str) -> None:
    content = f"""interface:
  display_name: "{display_name}"
  short_description: "{short_description}"
  default_prompt: "{default_prompt}"
policy:
  allow_implicit_invocation: true
"""
    write(root / "agents" / "openai.yaml", content)


if __name__ == "__main__":
    raise SystemExit(main())
