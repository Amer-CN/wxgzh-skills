"""档71C-R4 OBS-161 样本覆盖闭环(R33)。

断言:sentinels_for 全集 == 样本出现集 | EXEMPT_SENTINELS(显式豁免表)。
差集非空且不在 EXEMPT -> FAIL 并打印差集(S44)。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from conftest import SKILL_ROOT

sys.path.insert(0, str(SKILL_ROOT))
import validators.validate_component_visibility as vcv


def _sample_sentinel_set() -> set[str]:
    """所有 SLOT_SAMPLES block 中出现的哨兵(按 S_ 前缀提取)。"""
    out = set()
    for samples in vcv.SLOT_SAMPLES.values():
        for smp in samples:
            out.update(re.findall(r"S_[A-Z0-9_]+", smp["block"]))
    return out


def test_obs161_full_coverage_no_unexempted_gap():
    """sentinels_for 全集 == 样本出现集 | EXEMPT;差集非空且未豁免 -> FAIL。"""
    all_sentinels = set()
    for comp in vcv.REQUIRED_SENTINELS | vcv.OPTIONAL_SENTINELS | vcv.URL_SENTINELS:
        all_sentinels.update(vcv.sentinels_for(comp))
    sampled = _sample_sentinel_set()
    exempt = set(vcv.EXEMPT_SENTINELS)
    gap = all_sentinels - sampled - exempt
    assert not gap, f"S44: 未触达且未豁免的哨兵: {sorted(gap)}"
    # 豁免表每项必须带 OBS 号(理由格式校验)
    for sent, (reason, obs) in vcv.EXEMPT_SENTINELS.items():
        assert obs.startswith("OBS-"), f"{sent}: 豁免缺 OBS 号"
        assert reason, f"{sent}: 豁免缺理由"


def test_obs161_exempt_sentinels_are_real_generated():
    """豁免表里的哨兵必须确实存在于生成全集(防豁免幽灵条目)。"""
    all_sentinels = set()
    for comp in vcv.REQUIRED_SENTINELS | vcv.OPTIONAL_SENTINELS | vcv.URL_SENTINELS:
        all_sentinels.update(vcv.sentinels_for(comp))
    for sent in vcv.EXEMPT_SENTINELS:
        assert sent in all_sentinels, f"{sent}: 豁免条目不在生成全集"
        assert sent not in _sample_sentinel_set(), \
            f"{sent}: 已在样本中却仍豁免(冗余豁免)"
