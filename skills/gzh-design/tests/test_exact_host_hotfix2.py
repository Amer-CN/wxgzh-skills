#!/usr/bin/env python3
"""dev2-hotfix2 tests: publish_wechat_draft exact WeChat image-host gate."""
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

import publish_wechat_draft as pub

EVIL_URLS = [
    "https://evil.example/?x=mmbiz.qpic.cn",
    "https://mmbiz.qpic.cn.evil.example/a.png",
    "https://evil.example/mmbiz.qlogo.cn/a.png",
    "https://mmbiz.qpic.cn@evil.example/a.png",
]


def test_http_mmbiz_upgraded():
    assert pub.normalize_wechat_image_url("http://mmbiz.qpic.cn/a/0") == "https://mmbiz.qpic.cn/a/0"


def test_exact_https_hosts_accepted():
    assert pub.normalize_wechat_image_url("https://mmbiz.qpic.cn/a/0") == "https://mmbiz.qpic.cn/a/0"
    assert pub.normalize_wechat_image_url("https://mmbiz.qlogo.cn/a/0") == "https://mmbiz.qlogo.cn/a/0"


def test_evil_urls_rejected():
    for url in EVIL_URLS:
        assert pub.normalize_wechat_image_url(url) is None, url


def test_non_wechat_host_rejected():
    assert pub.normalize_wechat_image_url("https://cdn.example.com/x.png") is None
    assert pub.normalize_wechat_image_url("") is None
    assert pub.normalize_wechat_image_url(None) is None
