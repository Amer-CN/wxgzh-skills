"""77T/SSRF1: SSRF 守卫回归钉子 — 只补 tests/test_url_security.py 未覆盖的缺口。

与现有 tests/test_url_security.py 的分工（避免重复）：
- 已有覆盖：私网 A/B/C、环回、链路本地、CGN 100.64/10、组播、保留段、
  IPv4-mapped IPv6（_is_blocked_ip 层）、file/ftp/data/javascript scheme 拒、
  userinfo 凭据拒、check_redirect 到私网/环回拒、http(s) 公网放行（monkeypatch DNS）。
- 本文件补缺口：①云元数据 169.254.169.254 直连 URL；②IPv4-mapped IPv6
  （::ffff:127.0.0.1）以 URL 形式进入 is_safe_url；③公网 URL 在
  require_dns=False（hotfix4 离线口径）下放行。
"""
from __future__ import annotations

from media_enrichment.url_security import is_safe_url


class TestHf77tGuardPins:
    def test_cloud_metadata_direct_url_blocked(self):
        # 云元数据 169.254.169.254：BLOCKED_HOSTS + BLOCKED_RANGES 双层拦截面
        result = is_safe_url("http://169.254.169.254/latest/meta-data/", require_dns=False)
        assert not result.safe

    def test_ipv4_mapped_ipv6_loopback_blocked_as_url(self):
        # ::ffff:127.0.0.1 以 URL 形式进入 is_safe_url（现有测试只在 _is_blocked_ip 层覆盖）
        result = is_safe_url("http://[::ffff:127.0.0.1]/x", require_dns=False)
        assert not result.safe

    def test_public_url_allowed_without_dns(self):
        # require_dns=False（offline_fixture 口径）：静态检查全过 + 免 DNS 放行
        result = is_safe_url("https://example.com/img.jpg", require_dns=False)
        assert result.safe
