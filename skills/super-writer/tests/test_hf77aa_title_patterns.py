"""77AA 规格:标题生成端语料升级锚点测试(OBS-377)。

五组断言:六范式名在册 / 禁用词清单在册 / 关键词正负向在册 /
hits schema 锚点在册 / 原榜标题零命中(防抄袭——lengyi-title 原榜标题
原文不得出现在 title-patterns.md,自写措辞+自写示例)。

简报附录 A 仅含 1 条完整原榜标题串(#6 案例标题),以该条做零命中断言;
其余原榜标题未随简报提供,无法逐条断言(执行报告已如实登记)。
"""
from __future__ import annotations

from pathlib import Path

REF_DIR = Path(__file__).resolve().parents[1] / "references"
PATTERNS = (REF_DIR / "title-patterns.md").read_text(encoding="utf-8")
PLAYBOOK = (REF_DIR / "title-playbook.md").read_text(encoding="utf-8")
# 77AC/OBS-380:title-hits.md 移出 sw 锁面,真身居 pipeline audit/quality/(生产数据归位)。
HITS = (Path(__file__).resolve().parents[2] / "wxgzh-pipeline" / "audit" / "quality" / "title-hits.md").read_text(encoding="utf-8")

# lengyi-title 原榜已知完整标题串(附录 A #6 案例原文)——零命中防抄袭
ORIGINAL_BANGUMI_TITLES = [
    "40年没变过的Email，被腾讯重新定义了",
    "中国版Codex来了，Qwen3.7-Max免费用！",
    "最值得推荐的20个宝藏Skills，小众但真香",
]

# 简报允许在册的六范式名(自写配方,非原榜标题)
PARADIGM_NAMES = ["新品速报", "保姆级干货", "清单盘点", "第一人称战绩", "横评实测", "行业观点"]


def test_hf77aa_six_paradigms_present():
    """六范式名在册,且各有定义/生成公式/适用场景/自写示例骨架。"""
    for name in PARADIGM_NAMES:
        assert name in PATTERNS, f"六范式缺 {name}"
    assert PATTERNS.count("生成公式") >= 6, "六范式生成公式骨架不全"
    assert PATTERNS.count("适用场景") >= 6, "六范式适用场景骨架不全"
    assert PATTERNS.count("自写示例") >= 6, "六范式自写示例骨架不全"


def test_hf77aa_banned_words_present():
    """禁用词清单在册:揭秘/震惊/颠覆认知 0 命中纪律。"""
    assert "禁用清单" in PATTERNS
    assert "揭秘" in PATTERNS and "震惊" in PATTERNS and "颠覆认知" in PATTERNS
    # 结构统计关键约束锚点
    assert "22–27" in PATTERNS and "Top10 均值 25.7" in PATTERNS
    assert "≤1" in PATTERNS and "80%" in PATTERNS and "92%" in PATTERNS


def test_hf77aa_keyword_signal_table_present():
    """关键词实证表正负向在册(正向 GitHub/Star 3.84× 等,负向 DeepSeek 0.30× 等)。"""
    assert "GitHub/Star" in PATTERNS and "3.84×" in PATTERNS
    assert "Skill" in PATTERNS and "3.23×" in PATTERNS
    assert "一键/直接用" in PATTERNS and "3.16×" in PATTERNS
    assert "DeepSeek" in PATTERNS and "0.30×" in PATTERNS
    assert "免费/白嫖" in PATTERNS and "0.26×" in PATTERNS
    # 过期警告与使用规则
    assert "关键词价值会过期" in PATTERNS
    # 四任务规则(playbook §6 与 patterns §3 同锚)
    assert "指向高关注对象" in PATTERNS and "帮助目标读者快速识别主题" in PATTERNS
    assert "禁堆叠只描述技术却无读者结果的词" in PATTERNS
    assert "指向高关注对象" in PLAYBOOK and "禁堆叠只描述技术却无读者结果的词" in PLAYBOOK


def test_hf77aa_playbook_cyber_recipe_anchors():
    """playbook 网感组配方锚点:双目标选择 + 指向 title-patterns.md。"""
    assert "阅读量 or 分享率" in PLAYBOOK
    assert "title-patterns.md" in PLAYBOOK
    assert "网感点击组配方" in PLAYBOOK
    # 77D 语义零回退:原一句话要素仍在
    assert "有冲突/悬念/反差，允许口语，不准说谎" in PLAYBOOK


def test_hf77aa_hits_ledger_schema_present():
    """hits 台账 schema+三态+种子行在册。"""
    for col in ("日期", "RUN_ID", "标题", "组", "五维分", "风险标记", "表现回填位"):
        assert col in HITS, f"hits schema 缺列 {col}"
    for state in ("待回填", "已验证", "已证伪"):
        assert state in HITS, f"hits 三态缺 {state}"
    # 种子行(3bhpi2)
    assert "3bhpi2" in HITS
    assert "全网最强公文写作 Skill 开源了，数据都在这篇文章里" in HITS
    assert "只追加不删改" in HITS and "只收本号真实数据" in HITS


def test_hf77aa_no_original_bangumi_title_in_patterns():
    """原榜标题零命中:lengyi-title 原榜已知完整标题串不得出现在语料库。"""
    for title in ORIGINAL_BANGUMI_TITLES:
        assert title not in PATTERNS, f"疑似抄袭原榜标题: {title}"
        assert title not in PLAYBOOK
        assert title not in HITS


def test_hf77aa_pipeline_instruction_hits_duty():
    """sw Phase 6 指令面含 hits 回填义务(轻义务措辞在册)。"""
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "wxgzh-pipeline"))
    import wxgzh_pipeline.producers as PR  # noqa: E402

    instr = PR.AGENT_INSTRUCTIONS["super_writer"]
    assert "77AA/OBS-377" in instr
    assert "title-hits.md" in instr
    assert "不阻断流水线" in instr
    assert len(instr) <= 3000, "sw 指令超 3000 上限(test_hf76r 长度门)"
