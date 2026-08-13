"""档71C-2 OBS-121:图片白名单三处硬伤 —— 3e 三条 pytest + 3d 自洽断言。"""
from __future__ import annotations

from pathlib import Path

from validators import validate_img_src_whitelist as w


def _validate(tmp_path, html: str):
    p = tmp_path / "t.html"
    p.write_text(html, encoding="utf-8")
    return w.validate(p, enforce=True)


def test_obs121_single_quoted_src_parsed(tmp_path):
    """3e-1:单引号 src 被解析 —— https 放行,file:// 报 bad prefix。"""
    code, rep = _validate(tmp_path, "<img src='https://x.com/1.png'>")
    assert code == 0 and rep["hits"] == [] and rep["img_src_total"] == 1
    code, rep = _validate(tmp_path, "<img src='file:///C:/x.png'>")
    assert code == 1 and rep["hits"][0]["reason"] == "bad prefix"


def test_obs121_unquoted_src_parsed(tmp_path):
    """3e-2:无引号 src 被解析 —— https 放行,../ 报 bad prefix。"""
    code, rep = _validate(tmp_path, "<img src=https://x.com/1.png>")
    assert code == 0 and rep["hits"] == [] and rep["img_src_total"] == 1
    code, rep = _validate(tmp_path, "<img src=../a.png>")
    assert code == 1 and rep["hits"][0]["reason"] == "bad prefix"


def test_obs121_file_proto_reports_bad_prefix(tmp_path):
    """3e-3:file:// 报「bad prefix」而非「not https://」(3b 死分支已去)。"""
    code, rep = _validate(tmp_path, '<img src="file:///C:/x.png">')
    assert code == 1
    assert rep["hits"][0]["reason"] == "bad prefix"
    # not https:// 分支仍可达(普通 http 协议)
    code, rep = _validate(tmp_path, '<img src="http://x.com/1.png">')
    assert code == 1
    assert rep["hits"][0]["reason"] == "not https://"


def test_obs121_parse_gap_fail_closed(tmp_path):
    """3d:无 src 的 <img 标签 -> 解析数 != 标签总数 -> IMG_SRC_PARSE_GAP。"""
    code, rep = _validate(tmp_path, '<p><img alt="no src"></p>')
    assert code == 1
    assert rep["reason"] == "IMG_SRC_PARSE_GAP"
    assert rep["parsed_count"] == 0 and rep["img_count"] == 1
    assert rep["unparsed_fragments"] and "<img" in rep["unparsed_fragments"][0]
