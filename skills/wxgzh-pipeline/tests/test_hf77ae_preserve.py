"""77AE/OBS-382:installer 生产数据文件保留回归测试（纯 IO + tmp 树，无 subprocess）。"""
from __future__ import annotations

import importlib.util
from pathlib import Path

from conftest import SKILL_ROOT


def _load_installer():
    path = SKILL_ROOT / "scripts" / "install.py"
    spec = importlib.util.spec_from_file_location("hf77ae_installer", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


INSTALLER = _load_installer()

HEADER = "| 日期 | RUN_ID | 标题 | 组 | 五维分 | 风险标记 | 表现回填位 | 验证状态 |"
SEP = "|---|---|---|---|---|---|---|---|"


def _md(*rows: str) -> str:
    return "# 台账\n\n## 台账\n\n" + HEADER + "\n" + SEP + "\n" + "\n".join(rows) + "\n"


def _row(run_id: str, status: str = "待回填", title: str = "标题X") -> str:
    return f"| 2026-09-07 | {run_id} | {title} | 网感点击 | 22 分 | 无 | — | {status} |"


def _run_ids(text: str) -> list[str]:
    return [INSTALLER._production_run_id(line) for line in text.splitlines()
            if line.strip().startswith("|") and INSTALLER._production_run_id(line)]


def test_preserved_list_is_pinned():
    assert INSTALLER.PRESERVED_PRODUCTION_DATA == (
        "audit/quality/title-hits.md",
        "audit/quality/ai-tone-calibration.jsonl",
    )


def test_md_backup_unique_run_preserved(tmp_path: Path):
    """验收 1：装机侧独有 RUN_ID 行在合并后保留。"""
    backup = tmp_path / "backup.md"
    new = tmp_path / "new.md"
    backup.write_text(_md(_row("3bhpi2"), _row("fmq9km")), encoding="utf-8")
    new.write_text(_md(_row("3bhpi2"), _row("m9coc1")), encoding="utf-8")
    word = INSTALLER._merge_production_file(backup, new)
    assert word == "merged"
    merged = new.read_text(encoding="utf-8")
    ids = _run_ids(merged)
    assert "fmq9km" in ids
    assert "m9coc1" in ids
    # new 顺序为底，backup 独有行追加在后。
    assert ids.index("m9coc1") < ids.index("fmq9km")


def test_md_new_unique_distributed_and_new_wins(tmp_path: Path):
    """验收 2：仓侧新行照常分发；同 RUN_ID 取 new 版且不重复。"""
    backup = tmp_path / "backup.md"
    new = tmp_path / "new.md"
    backup.write_text(_md(_row("3bhpi2", "待回填")), encoding="utf-8")
    new.write_text(_md(_row("3bhpi2", "已验证"), _row("newrow1")), encoding="utf-8")
    word = INSTALLER._merge_production_file(backup, new)
    assert word == "merged"
    merged = new.read_text(encoding="utf-8")
    ids = _run_ids(merged)
    assert ids.count("3bhpi2") == 1
    assert "newrow1" in ids
    assert "已验证" in merged
    # backup 旧状态行不得残留为重复行。
    assert merged.count("3bhpi2") == 1


def test_jsonl_union_no_dup(tmp_path: Path):
    """验收 3：jsonl 两边独有行并集，相同行不重复。"""
    backup = tmp_path / "backup.jsonl"
    new = tmp_path / "new.jsonl"
    backup.write_text('{"run_id": "a"}\n{"run_id": "b"}\n', encoding="utf-8")
    new.write_text('{"run_id": "b"}\n{"run_id": "c"}\n', encoding="utf-8")
    word = INSTALLER._merge_production_file(backup, new)
    assert word == "merged"
    lines = new.read_text(encoding="utf-8").splitlines()
    assert lines == ['{"run_id": "a"}', '{"run_id": "b"}', '{"run_id": "c"}']


def test_backup_missing_kept_new(tmp_path: Path):
    """验收 4a：backup 缺失 → 保持 new。"""
    backup = tmp_path / "no-backup.md"
    new = tmp_path / "new.md"
    payload = _md(_row("3bhpi2"))
    new.write_text(payload, encoding="utf-8")
    word = INSTALLER._merge_production_file(backup, new)
    assert word == "kept-new"
    assert new.read_text(encoding="utf-8") == payload


def test_new_missing_restored_backup(tmp_path: Path):
    """验收 4b：new 缺失 → 从 backup 恢复。"""
    backup = tmp_path / "backup.jsonl"
    new = tmp_path / "sub" / "new.jsonl"
    backup.write_text('{"run_id": "a"}\n', encoding="utf-8")
    word = INSTALLER._merge_production_file(backup, new)
    assert word == "restored-backup"
    assert new.read_text(encoding="utf-8") == '{"run_id": "a"}\n'


def test_both_missing_kept_new(tmp_path: Path):
    """验收 4c：两边都不存在 → kept-new 且不建文件。"""
    word = INSTALLER._merge_production_file(
        tmp_path / "b.md", tmp_path / "n.md")
    assert word == "kept-new"
    assert not (tmp_path / "n.md").exists()


def test_identical_returns_identical(tmp_path: Path):
    """验收 4d：两边逐字节一致 → identical 且不改文件。"""
    backup = tmp_path / "backup.md"
    new = tmp_path / "new.md"
    payload = _md(_row("3bhpi2"))
    backup.write_text(payload, encoding="utf-8")
    new.write_text(payload, encoding="utf-8")
    before = new.read_bytes()
    assert INSTALLER._merge_production_file(backup, new) == "identical"
    assert new.read_bytes() == before
    backup_j = tmp_path / "backup.jsonl"
    new_j = tmp_path / "new.jsonl"
    backup_j.write_text('{"run_id": "a"}\n', encoding="utf-8")
    new_j.write_text('{"run_id": "a"}\n', encoding="utf-8")
    assert INSTALLER._merge_production_file(backup_j, new_j) == "identical"
