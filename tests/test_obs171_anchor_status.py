"""档71C-R5 OBS-173:锚 JSON 状态键五种状态各一条(S49)。

monkeypatch gzh_design._ANCHORS_JSON 指向 tmp 造的 JSON:
缺失 / 损坏 / 缺 sha / sha 漂移 / 正常 -> 断言具体 key 字符串 + detail 非空。
"""
from __future__ import annotations

import json

import pytest
import sys

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
