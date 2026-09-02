"""77T/SSRF1: SSRF 守卫回归钉子 — 只补 tests/test_url_security.py 未覆盖的缺口。

与现有 tests/test_url_security.py 的分工（避免重复）：
- 已有覆盖：私网 A/B/C、环回、链路本地、CGN 100.64/10、组播、保留段、
  IPv4-mapped IPv6（_is_blocked_ip 层）、file/ftp/data/javascript scheme 拒、
  userinfo 凭据拒、check_redirect 到私网/环回拒、http(s) 公网放行（monkeypatch DNS）。
- 本文件补缺口：①云元数据 link-local 地址直连 URL（元数据端点地址）；
  ②IPv4-mapped IPv6 环回以 URL 形式进入 is_safe_url；③公网 URL 在
  require_dns=False（hotfix4 离线口径）下放行。
- 77U 卫生新规：内网/元数据 URL 一律分段构造，测试源码不携带完整地址字面量。
"""
from __future__ import annotations

from media_enrichment.url_security import is_safe_url


class TestHf77tGuardPins:
    def test_cloud_metadata_direct_url_blocked(self):
        # 云元数据 link-local 地址：BLOCKED_HOSTS + BLOCKED_RANGES 双层拦截面
        url = "http://" + "169." + "254." + "169." + "254/latest/meta-data/"
        result = is_safe_url(url, require_dns=False)
        assert not result.safe

    def test_ipv4_mapped_ipv6_loopback_blocked_as_url(self):
        # IPv4-mapped IPv6 环回以 URL 形式进入 is_safe_url（现有测试只在 _is_blocked_ip 层覆盖）
        url = "http://[::" + "ffff:127." + "0." + "0." + "1]/x"
        result = is_safe_url(url, require_dns=False)
        assert not result.safe

    def test_public_url_allowed_without_dns(self):
        # require_dns=False（offline_fixture 口径）：静态检查全过 + 免 DNS 放行
        result = is_safe_url("https://example.com/img.jpg", require_dns=False)
        assert result.safe
