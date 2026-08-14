"""76S/OBS-292:upgrade-chain 查找遇残缺记录(空 old/new)→ 跳过不短路。

- 残缺的「非目标 skill」记录不得阻断其他 skill 的链验证(先按 skill 过滤);
- 目标 skill 的残缺记录仍严格要求(缺失即 None=TAMPERED);
- 正常链仍找得到(回归)。
"""
from __future__ import annotations

import json
from pathlib import Path

from wxgzh_pipeline.receipts import _find_upgrade_chain


def _write_history(tmp_path: Path, records: list[dict]) -> Path:
    p = tmp_path / "skills.lock.history.json"
    p.write_text(json.dumps(records, ensure_ascii=False), encoding="utf-8")
    return p


def _rec(skill: str, old: str, new: str, entry_id: str) -> dict:
    return {"skill": skill, "old_root_sha256": old, "new_root_sha256": new,
            "entry_id": entry_id}


def test_broken_non_target_record_skipped_not_shortcircuit(tmp_path):
    """残缺的非目标 skill 记录(空 old/new)跳过,目标 skill 正常链仍找到。"""
    h = _write_history(tmp_path, [
        # 残缺的 media 早期记录(空 old/new)——正是 20260804T050125Z 形态
        {"skill": "media-enrichment", "old_root_sha256": "",
         "new_root_sha256": "", "entry_id": "relock-media-enrichment-20260804T050125Z"},
        # 目标 skill 正常两跳链
        _rec("super-writer", "old-1", "mid-1", "r1"),
        _rec("super-writer", "mid-1", "cur-1", "r2"),
    ])
    chain = _find_upgrade_chain("super-writer", "old-1", "cur-1", h)
    assert chain is not None, "残缺非目标记录不得阻断目标链"
    assert [r["entry_id"] for r in chain] == ["r1", "r2"]


def test_other_skill_records_do_not_interfere(tmp_path):
    """非目标 skill 的正常记录不参与目标链(不误入、不干扰)。"""
    h = _write_history(tmp_path, [
        _rec("media-enrichment", "m-old", "m-cur", "m1"),
        _rec("zh-human-writing", "z-old", "z-cur", "z1"),
        _rec("super-writer", "s-old", "s-cur", "s1"),
    ])
    chain = _find_upgrade_chain("super-writer", "s-old", "s-cur", h)
    assert chain is not None and [r["entry_id"] for r in chain] == ["s1"]


def test_target_skill_broken_record_still_fails(tmp_path):
    """目标 skill 自身的残缺记录仍严格要求(缺失即 None=TAMPERED)。"""
    h = _write_history(tmp_path, [
        {"skill": "super-writer", "old_root_sha256": "", "new_root_sha256": "",
         "entry_id": "relock-super-writer-broken"},
    ])
    chain = _find_upgrade_chain("super-writer", "old-1", "cur-1", h)
    assert chain is None, "目标 skill 残缺记录必须 None(TAMPERED)"


def test_normal_chain_regression(tmp_path):
    """正常链(多跳、无残缺)→ 仍找得到(回归)。"""
    h = _write_history(tmp_path, [
        _rec("super-writer", "a", "b", "r1"),
        _rec("super-writer", "b", "c", "r2"),
        _rec("super-writer", "c", "d", "r3"),
    ])
    chain = _find_upgrade_chain("super-writer", "a", "d", h)
    assert chain is not None and [r["entry_id"] for r in chain] == ["r1", "r2", "r3"]
