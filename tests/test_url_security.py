"""Tests for SSRF: manual redirect, IPv4-mapped IPv6, comprehensive blocking."""

import pytest
from media_enrichment.url_security import is_safe_url, _is_blocked_ip
import ipaddress


class TestComprehensiveBlocking:
    def test_loopback_blocked(self):
        assert not is_safe_url("http://127.0.0.1/x").safe

    def test_private_a_blocked(self):
        assert not is_safe_url("http://10.0.0.1/x").safe

    def test_private_b_blocked(self):
        assert not is_safe_url("http://172.16.0.1/x").safe

    def test_private_c_blocked(self):
        assert not is_safe_url("http://192.168.1.1/x").safe

    def test_link_local_blocked(self):
        assert not is_safe_url("http://169.254.1.1/x").safe

    def test_multicast_blocked(self):
        assert not is_safe_url("http://224.0.0.1/x").safe

    def test_reserved_blocked(self):
        assert not is_safe_url("http://240.0.0.1/x").safe

    def test_unspecified_blocked(self):
        assert not is_safe_url("http://0.0.0.0/x").safe

    def test_documentation_net1_blocked(self):
        assert not is_safe_url("http://192.0.2.1/x").safe

    def test_documentation_net2_blocked(self):
        assert not is_safe_url("http://198.51.100.1/x").safe

    def test_documentation_net3_blocked(self):
        assert not is_safe_url("http://203.0.113.1/x").safe

    def test_carrier_grade_nat_blocked(self):
        assert not is_safe_url("http://100.64.0.1/x").safe

    def test_ipv6_loopback_blocked(self):
        assert not is_safe_url("http://[::1]/x").safe

    def test_ipv6_link_local_blocked(self):
        assert not is_safe_url("http://[fe80::1]/x").safe

    def test_ipv6_unique_local_blocked(self):
        assert not is_safe_url("http://[fc00::1]/x").safe

    def test_ipv6_multicast_blocked(self):
        assert not is_safe_url("http://[ff02::1]/x").safe

    def test_ipv6_documentation_blocked(self):
        assert not is_safe_url("http://[2001:db8::1]/x").safe


class TestIPv4MappedIPv6:
    def test_ipv4_mapped_loopback_blocked(self):
        ip = ipaddress.ip_address("::ffff:127.0.0.1")
        assert _is_blocked_ip(ip)

    def test_ipv4_mapped_private_blocked(self):
        ip = ipaddress.ip_address("::ffff:192.168.1.1")
        assert _is_blocked_ip(ip)

    def test_ipv4_mapped_link_local_blocked(self):
        ip = ipaddress.ip_address("::ffff:169.254.169.254")
        assert _is_blocked_ip(ip)


class TestRedirectInterception:
    """Test that redirect targets are checked BEFORE the request is made."""

    def test_redirect_to_localhost_blocked_before_request(self):
        from media_enrichment.url_security import check_redirect
        result = check_redirect("https://example.com/a", "http://localhost:8080/secret", 0)
        assert not result.safe

    def test_redirect_to_private_blocked_before_request(self):
        from media_enrichment.url_security import check_redirect
        result = check_redirect("https://example.com/a", "http://10.0.0.1/secret", 0)
        assert not result.safe

    def test_max_redirects_enforced(self):
        from media_enrichment.url_security import check_redirect, MAX_REDIRECTS
        result = check_redirect("https://example.com/a", "https://example.com/b", MAX_REDIRECTS)
        assert not result.safe


class TestProtocolSecurity:
    def test_file_protocol_blocked(self):
        assert not is_safe_url("file:///etc/passwd").safe

    def test_ftp_protocol_blocked(self):
        assert not is_safe_url("ftp://example.com/file").safe

    def test_data_protocol_blocked(self):
        assert not is_safe_url("data:text/html,<script>").safe

    def test_javascript_protocol_blocked(self):
        assert not is_safe_url("javascript:alert(1)").safe

    def test_http_allowed(self):
        assert is_safe_url("http://example.com/img.jpg").safe

    def test_https_allowed(self):
        assert is_safe_url("https://example.com/img.jpg").safe


class TestURLCredentials:
    def test_credentials_blocked(self):
        assert not is_safe_url("http://user:pass@example.com/img.jpg").safe
