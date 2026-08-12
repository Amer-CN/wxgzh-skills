"""76D/OBS-259:WebP→JPEG 自动转码(微信 40005 实证)。"""
from __future__ import annotations

import io

from media_enrichment.uploader import transcode_webp_to_jpeg
from media_enrichment.manifest_builder import ManifestBuilder


def _make_webp(tmp_path, name="a.webp", size=(64, 48), color=(200, 30, 30)) -> str:
    from PIL import Image
    im = Image.new("RGB", size, color)
    p = tmp_path / name
    im.save(p, "WEBP")
    return str(p)


def _make_png(tmp_path, name="b.png") -> str:
    from PIL import Image
    im = Image.new("RGB", (64, 48), (10, 200, 10))
    p = tmp_path / name
    im.save(p, "PNG")
    return str(p)


def test_webp_transcoded_to_jpeg(tmp_path):
    src = _make_webp(tmp_path)
    path, record, err = transcode_webp_to_jpeg(src)
    assert err is None
    assert record is not None and record["from_format"] == "webp"
    assert record["to_format"] == "jpeg"
    assert record["original_bytes"] > 0 and record["converted_bytes"] > 0
    assert path.endswith(".jpg")
    from PIL import Image
    with Image.open(path) as im:
        assert im.format == "JPEG"
    # 原文件不动
    with open(src, "rb") as f:
        assert f.read(4) == b"RIFF"


def test_non_webp_untouched(tmp_path):
    src = _make_png(tmp_path)
    path, record, err = transcode_webp_to_jpeg(src)
    assert err is None and record is None and path == src


def test_corrupt_webp_fails_closed(tmp_path):
    p = tmp_path / "bad.webp"
    p.write_bytes(b"RIFF\x10\x00\x00\x00WEBP" + b"\x00" * 64)
    path, record, err = transcode_webp_to_jpeg(str(p))
    assert record is None
    assert err is not None and "transcode failed" in err
    # 转码失败返回原路径,由调用方 fail-closed 决定是否上传
    assert path == str(p)


def test_manifest_transcodes_field(tmp_path):
    b = ManifestBuilder(run_id="r", request_sha256="a" * 64,
                        article_sha256="b" * 64, claims_total=1, materials_total=1)
    b.transcodes.append({"asset_id": "A-1", "from_format": "webp",
                         "to_format": "jpeg", "original_bytes": 10,
                         "converted_bytes": 8})
    man = b.build()
    assert man["transcodes"] == [{"asset_id": "A-1", "from_format": "webp",
                                  "to_format": "jpeg", "original_bytes": 10,
                                  "converted_bytes": 8}]
    b2 = ManifestBuilder(run_id="r", request_sha256="a" * 64,
                         article_sha256="b" * 64, claims_total=1, materials_total=1)
    assert b2.build()["transcodes"] == []
