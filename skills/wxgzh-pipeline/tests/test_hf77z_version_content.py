"""77Z 规格 A:version_check 内容口径(version_check.py + install.py 标记)。

全 mock,不真实联网。核心断言=日期粒度误报消除:标记 sha==latest tag sha
但标记日期早于 tag 日期 → current(内容即最新,日期不再参与 behind 判定)。
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

SKILL_ROOT = Path(__file__).resolve().parents[1]


def _load_vcheck():
    """把 scripts/version_check.py 当独立脚本加载(非包内模块,同 77V 测试法)。"""
    spec = importlib.util.spec_from_file_location(
        "wxgzh_version_check_77z", SKILL_ROOT / "scripts" / "version_check.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _make_installed_home(tmp_path: Path, marker: dict | None) -> Path:
    """造一个装机侧 skills-home:wxgzh-pipeline/ 下放 lock/history/VERSION
    与可选 .installed-from 标记。日期口径的基线取 history recorded_at。"""
    pipe = tmp_path / "wxgzh-pipeline"
    pipe.mkdir(parents=True)
    (pipe / "skills.lock.json").write_text(
        json.dumps({"lock_version": 2, "skills": {}}), encoding="utf-8")
    (pipe / "skills.lock.history.json").write_text(
        json.dumps([{"recorded_at": "2026-08-01T00:00:00Z"}]), encoding="utf-8")
    (pipe / "VERSION").write_text(
        "version: 0.1.0-dev2-hotfix9R29\nrelease_date: 2026-08-01\n",
        encoding="utf-8")
    if marker is not None:
        (pipe / ".installed-from").write_text(
            json.dumps(marker, ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8")
    return tmp_path


SHA_NEW = "aaaa1111aaaa1111aaaa1111aaaa1111aaaa1111"  # 最新 tag v2026.09.05 的 sha
SHA_OLD = "bbbb2222bbbb2222bbbb2222bbbb2222bbbb2222"


def _ls_remote_tags_pairs(pairs):
    """mock:返回 ([(tag, sha), ...], None)——77Z 双列返回形状。"""
    return list(pairs), None


# ---------- ① 标记 sha==latest tag sha → current(即便日期早于 tag 日期) ----------

def test_77z_marker_sha_matches_latest_current_despite_older_date(tmp_path, monkeypatch):
    """日期粒度误报消除核心断言:基线 2026-08-01 早于 tag 2026-09-05,
    但标记 source_commit==latest tag sha → current(日期只进 detail)。"""
    vc = _load_vcheck()
    home = _make_installed_home(tmp_path, {
        "source_commit": SHA_NEW, "resolved_tag": "v2026.09.05-77y",
        "recorded_at": "2026-08-01T00:00:00Z"})
    monkeypatch.setattr(vc, "_ls_remote_tags", lambda remote:
                        _ls_remote_tags_pairs([("v2026.09.05-77y", SHA_NEW)]))
    out = vc.check(skills_home=home)
    assert out["status"] == "current", out
    assert out["latest"] == "v2026.09.05-77y"
    assert out["current"]["installed_from"]["source_commit"] == SHA_NEW
    # 日期口径降级为 detail 附加说明,不再参与 behind 判定
    assert "日期口径仅展示" in out["detail"]
    assert "2026-08-01" in out["detail"]


# ---------- ② 标记 sha≠latest → behind(更新路径真实可清除) ----------

def test_77z_marker_sha_differs_from_latest_behind(tmp_path, monkeypatch):
    vc = _load_vcheck()
    home = _make_installed_home(tmp_path, {
        "source_commit": SHA_OLD, "resolved_tag": None,
        "recorded_at": "2026-09-04T00:00:00Z"})
    monkeypatch.setattr(vc, "_ls_remote_tags", lambda remote:
                        _ls_remote_tags_pairs([("v2026.09.05-77y", SHA_NEW)]))
    out = vc.check(skills_home=home)
    assert out["status"] == "behind", out
    assert "更新路径真实可清除" in out["detail"]
    assert SHA_OLD[:12] in out["detail"]
    assert SHA_NEW[:12] in out["detail"]


# ---------- ③ 标记缺失 → 回退既有日期口径(现行为不变) ----------

def test_77z_marker_missing_falls_back_to_date_baseline(tmp_path, monkeypatch):
    """旧装机拷贝无 .installed-from:日期口径照旧——tag 日期>基线 → behind。"""
    vc = _load_vcheck()
    home = _make_installed_home(tmp_path, None)
    monkeypatch.setattr(vc, "_ls_remote_tags", lambda remote:
                        _ls_remote_tags_pairs([("v2026.09.05-77y", SHA_NEW)]))
    out = vc.check(skills_home=home)
    assert out["status"] == "behind", out
    assert "晚于本地构建基线 2026-08-01" in out["detail"]
    assert "installed_from" not in out["current"]


# ---------- ④ 离线/解析失败 → unknown(三态语义不变) ----------

def test_77z_lsremote_failure_unknown_with_marker(tmp_path, monkeypatch):
    vc = _load_vcheck()
    home = _make_installed_home(tmp_path, {
        "source_commit": SHA_NEW, "resolved_tag": None,
        "recorded_at": "2026-09-04T00:00:00Z"})
    monkeypatch.setattr(vc, "_ls_remote_tags",
                        lambda remote: ([], "git ls-remote 失败 rc=1: mock offline"))
    out = vc.check(skills_home=home)
    assert out["status"] == "unknown", out
    assert out["latest"] is None
    assert "rc=1" in out["detail"]


# ---------- install.py 落标记(77Z/OBS-374) ----------

def _load_installer():
    spec = importlib.util.spec_from_file_location(
        "wxgzh_install_77z", SKILL_ROOT / "scripts" / "install.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_77z_install_writes_installed_from_marker(tmp_path):
    """_write_installed_from:单行 JSON(source_commit/resolved_tag/recorded_at),
    路径=target/wxgzh-pipeline/.installed-from(installed 目标推导同源)。"""
    installer = _load_installer()
    src = tmp_path / "repo"
    src.mkdir()
    subprocess.run(["git", "init", "-q", str(src)], check=True)
    subprocess.run(["git", "-C", str(src), "config", "user.email", "t@t"],
                   check=True)
    subprocess.run(["git", "-C", str(src), "config", "user.name", "t"],
                   check=True)
    (src / "f.txt").write_text("x", encoding="utf-8")
    subprocess.run(["git", "-C", str(src), "add", "."], check=True)
    subprocess.run(["git", "-C", str(src), "commit", "-q", "-m", "init"],
                   check=True)
    subprocess.run(["git", "-C", str(src), "tag", "v2026.09.05-77y"],
                   check=True)
    target = tmp_path / "target"
    (target / "wxgzh-pipeline").mkdir(parents=True)
    path = installer._write_installed_from(target, src)
    assert path is not None and path.is_file()
    marker = json.loads(path.read_text(encoding="utf-8"))
    head = subprocess.run(["git", "-C", str(src), "rev-parse", "HEAD"],
                          capture_output=True, text=True).stdout.strip()
    assert marker["source_commit"] == head
    assert marker["resolved_tag"] == "v2026.09.05-77y"
    assert marker["recorded_at"].endswith("Z")
    # 单行 JSON
    assert "\n" not in path.read_text(encoding="utf-8")


def test_77z_install_marker_reader_contract(tmp_path, monkeypatch):
    """_read_installed_marker 与 install.py 写的标记同契:标记在 → 内容口径。"""
    vc = _load_vcheck()
    home = _make_installed_home(tmp_path, {
        "source_commit": SHA_NEW, "resolved_tag": None,
        "recorded_at": "2026-09-04T00:00:00Z"})
    marker = vc._read_installed_marker(home)
    assert marker is not None and marker["source_commit"] == SHA_NEW
    # 损坏标记 → None(回退日期口径)
    (home / "wxgzh-pipeline" / ".installed-from").write_text("not-json",
                                                             encoding="utf-8")
    assert vc._read_installed_marker(home) is None
