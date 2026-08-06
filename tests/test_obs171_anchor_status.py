"""档71C-R5 OBS-173:锚 JSON 状态键五种状态各一条(S49)。

monkeypatch gzh_design._ANCHORS_JSON 指向 tmp 造的 JSON:
缺失 / 损坏 / 缺 sha / sha 漂移 / 正常 -> 断言具体 key 字符串 + detail 非空。
"""
from __future__ import annotations

import json

import pytest
import sys
from pathlib import Path

from conftest import SKILL_ROOT

sys.path.insert(0, str(SKILL_ROOT))
from wxgzh_pipeline.stages import gzh_design as gd


@pytest.fixture(autouse=True)
def _reset_status(monkeypatch):
    monkeypatch.setattr(gd, "_ANCHORS_STATUS_REFRESHED", False)
    yield
    monkeypatch.setattr(gd, "_ANCHORS_STATUS_REFRESHED", False)


def _make_json(tmp_path, content: str, name: str = "anchors.json") -> None:
    p = tmp_path / name
    p.write_text(content, encoding="utf-8")
    return p


def test_obs173_status_missing(tmp_path, monkeypatch):
    """JSON 缺失 -> ANCHORS_JSON_MISSING。"""
    missing = tmp_path / "no-such.json"
    monkeypatch.setattr(gd, "_ANCHORS_JSON", missing)
    st = gd.refresh_anchor_status()
    assert st["key"] == "ANCHORS_JSON_MISSING", st
    assert st["detail"]


def test_obs173_status_corrupt(tmp_path, monkeypatch):
    """JSON 损坏 -> ANCHORS_JSON_CORRUPT。"""
    p = _make_json(tmp_path, "{not valid json")
    monkeypatch.setattr(gd, "_ANCHORS_JSON", p)
    st = gd.refresh_anchor_status()
    assert st["key"] == "ANCHORS_JSON_CORRUPT", st
    assert st["detail"]


def test_obs173_status_sha_absent(tmp_path, monkeypatch):
    """JSON 缺 renderer_sha256 -> ANCHORS_SHA_ABSENT(不抛异常)。"""
    p = _make_json(tmp_path, json.dumps({"anchors": []}))
    monkeypatch.setattr(gd, "_ANCHORS_JSON", p)
    st = gd.refresh_anchor_status()
    assert st["key"] == "ANCHORS_SHA_ABSENT", st
    assert st["detail"]


def test_obs173_status_sha_drift(tmp_path, monkeypatch):
    """JSON sha != 安装侧渲染器 sha -> ANCHORS_SHA_DRIFT。"""
    from tests.test_obs119_visibility import _installed_renderer
    renderer, log = _installed_renderer()
    if renderer is None:
        pytest.skip("安装侧渲染器不可得: " + "|".join(log))
    p = _make_json(tmp_path, json.dumps(
        {"renderer_sha256": "0" * 64, "anchors": []}))
    monkeypatch.setattr(gd, "_ANCHORS_JSON", p)
    st = gd.refresh_anchor_status()
    assert st["key"] == "ANCHORS_SHA_DRIFT", st
    assert st["detail"]


def test_obs173_status_ok(tmp_path, monkeypatch):
    """JSON 正常且 sha 匹配 -> ANCHORS_JSON_OK。"""
    import hashlib
    from tests.test_obs119_visibility import _installed_renderer
    renderer, log = _installed_renderer()
    if renderer is None:
        pytest.skip("安装侧渲染器不可得: " + "|".join(log))
    sha = hashlib.sha256(renderer.read_bytes()).hexdigest()
    p = _make_json(tmp_path, json.dumps({"renderer_sha256": sha, "anchors": []}))
    monkeypatch.setattr(gd, "_ANCHORS_JSON", p)
    st = gd.refresh_anchor_status()
    assert st["key"] == "ANCHORS_JSON_OK", st


# ── 3a/3b(OBS-173,S49/R33/R40):RENDERER_NOT_FOUND + 键全集相等 ──

def test_obs173_status_renderer_not_found(tmp_path, monkeypatch):
    """渲染器路径解析落空 -> ANCHORS_RENDERER_NOT_FOUND(JSON 本身合法)。"""
    import hashlib
    from wxgzh_pipeline import paths as _paths
    from wxgzh_pipeline import skill_discovery as _sd
    # JSON 合法且带 renderer_sha256(排除 MISSING/CORRUPT/SHA_ABSENT 干扰)
    p = _make_json(tmp_path, json.dumps(
        {"renderer_sha256": "1" * 64, "anchors": []}))
    monkeypatch.setattr(gd, "_ANCHORS_JSON", p)
    # skills_home 指向 tmp(无 gzh-design 安装)
    monkeypatch.setattr(_paths, "skills_home", lambda root, env=None: tmp_path / "skills")
    monkeypatch.setattr(_sd, "load_lock",
                        lambda root: {"skills": {"gzh-design": {"entrypoint": "scripts/render_article.py"}}})
    st = gd.refresh_anchor_status()
    assert st["key"] == "ANCHORS_RENDERER_NOT_FOUND", st
    assert st["detail"]


def test_obs173_all_keys_have_tests():
    """refresh_anchor_status 源码里全部 key 常量 == 本文件断言的字面量(全集相等,R33)。"""
    import re as _re
    src = Path(gd.__file__).read_text(encoding="utf-8")
    # 从 refresh_anchor_status 函数体抓 key 常量
    fn = src[src.find("def refresh_anchor_status"):]
    fn = fn[:fn.find("\n\ndef ")] if "\n\ndef " in fn else fn
    impl_keys = set(_re.findall(r'key="(ANCHORS_[A-Z_]+)"', fn))
    test_src = Path(__file__).read_text(encoding="utf-8")
    test_keys = set(_re.findall(r'st\[\"key\"\] == \"(ANCHORS_[A-Z_]+)\"', test_src))
    # 1a(71D,R43/R44):删除 rg 调用 —— 仓外二进制依赖(未装 ripgrep 的机器会
    # FileNotFoundError 直接 error),且 grep 的是本文件自身必然命中(恒真警告)。
    # 键测试执行层覆盖在台账登记为【未覆盖】(不保留假覆盖)。
    assert impl_keys == test_keys, \
        f"键集合不等: 实现={sorted(impl_keys)} 测试={sorted(test_keys)}"
