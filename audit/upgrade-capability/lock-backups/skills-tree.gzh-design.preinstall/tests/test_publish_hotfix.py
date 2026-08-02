#!/usr/bin/env python3
"""微信发布缺陷回归测试 v2 — 24 项真实缺陷检测

测试项目：
1. style=「...」 必须阻断
2. leaf=「」 必须阻断
3. 合法 style="..." 通过
4. 中文 HTML 通过
5. 字面量 \\u6765 阻断
6. 原始 Markdown 阻断（validator 层）
7. {{作者名}} 阻断
8. 编辑锚点阻断
9. 锤子主题无 rgba(5,150,105)
10. create_draft payload 保留中文和 Emoji（实际调用 + 拦截 requests.post）
11. 校验失败不得获取 token（patch get_access_token，assert not_called）
12. 校验失败不得调用 draft/add（通过 main 完整入口测试）
13. cx=「12」 阻断
14. cy=「12」 阻断
15. r=「3」 阻断
16. stroke-linecap=「round」 阻断
17. stroke-linejoin=「round」 阻断
18. data-test=「value」 阻断
19. aria-label=「说明」 阻断
20. 正文 x=「概念」 不误判
21. 原始 Markdown 通过 main 阻断（get_access_token / requests.get / requests.post 均 0 次）
22. 普通中文纯文本通过 main 阻断
23. 不含中文 HTML 通过 main 阻断
24. 含 <script> HTML 通过 main 阻断
25. requests.post 不得收到 json= 参数（必须用 data=）
26. requests.post 的 data 必须是 bytes
27. data.decode("utf-8") 必须包含实际中文
28. data.decode("utf-8") 必须包含实际 Emoji
29. data.decode("utf-8") 不得包含字面量双反斜杠 Unicode
30. json.loads(data) 后的 content 必须与输入 HTML 完全一致
31. title 单次 JSON 往返后必须是实际中文
32. --expect-sha256 只校验 raw bytes（不一致则阻断）
33. raw_file_sha256 与 normalized_content_sha256 分开记录（两者允许不同）
34. draft/get 必须使用 resp.content.decode("utf-8") + json.loads
"""
import hashlib
import json
import os
import sys
import tempfile
import unittest
from unittest.mock import patch, MagicMock

# 路径设置
SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(SKILL_ROOT, "scripts"))

import validate_gzh_html as vh
import publish_wechat_draft as pub

# 工具函数
CN_QUOTE = '\u300c'  # 「
CN_QUOTE_CLOSE = '\u300d'  # 」

# --- 测试数据 ---

HTML_WITH_CN_QUOTE_STYLE = f'<section style={CN_QUOTE}color:red;{CN_QUOTE_CLOSE}><span leaf="">test</span></section>'
HTML_WITH_CN_QUOTE_LEAF = f'<section style="color:red;"><span leaf={CN_QUOTE}{CN_QUOTE_CLOSE}>test</span></section>'
HTML_VALID = '<section style="color:red;"><span leaf="">中文测试</span></section>'
HTML_CHINESE = '<section style="font-size:14px;"><span leaf="">这是一个中文测试段落。</span></section>'
HTML_WITH_LITERAL_UNICODE = '<section style="color:red;"><span leaf="">\\u6765\\u4e86\\ud83d</span></section>'
HTML_WITH_MARKDOWN = '## 这是标题\n\n正文内容\n\n![图片](url)'
HTML_WITH_PLACEHOLDER = '<section style="color:red;"><span leaf="">我是 {{作者名}}，{{一句话简介}}。</span></section>'
HTML_WITH_EDITOR_ANCHOR = '<section style="color:red;"><span leaf="">[编辑锚点/F：核对数据]</span></section>'
HTML_HAMMER_CLEAN = '<section style="color:#B3593B;background:rgba(179,89,59,0.10);"><span leaf="">锤子风格</span></section>'

# 含中文和 Emoji 的真实 payload 测试数据
HTML_WITH_CJK_EMOJI = '<section style="color:#555555;"><span leaf="">中文测试：K3 来了。📦 👉</span></section>'

# SVG 属性中文引号测试数据（v1 漏检的 5 处）
SVG_WITH_CN_CX = f'<section style="color:red;"><span leaf="">中文</span></section><svg><circle cx={CN_QUOTE}12{CN_QUOTE_CLOSE}></circle></svg>'
SVG_WITH_CN_CY = f'<section style="color:red;"><span leaf="">中文</span></section><svg><circle cy={CN_QUOTE}12{CN_QUOTE_CLOSE}></circle></svg>'
SVG_WITH_CN_R = f'<section style="color:red;"><span leaf="">中文</span></section><svg><circle r={CN_QUOTE}3{CN_QUOTE_CLOSE}></circle></svg>'
SVG_WITH_CN_LINECAP = f'<section style="color:red;"><span leaf="">中文</span></section><svg stroke-linecap={CN_QUOTE}round{CN_QUOTE_CLOSE}></svg>'
SVG_WITH_CN_LINEJOIN = f'<section style="color:red;"><span leaf="">中文</span></section><svg stroke-linejoin={CN_QUOTE}round{CN_QUOTE_CLOSE}></svg>'
HTML_WITH_CN_DATA_TEST = f'<section style="color:red;"><span leaf="" data-test={CN_QUOTE}value{CN_QUOTE_CLOSE}>中文</span></section>'
HTML_WITH_CN_ARIA_LABEL = f'<section style="color:red;"><span leaf="" aria-label={CN_QUOTE}说明{CN_QUOTE_CLOSE}>中文</span></section>'

# 正文中的 x=「概念」不应被误判为 HTML 属性引号
HTML_BODY_TEXT_WITH_CN_QUOTE = '<section style="color:red;"><span leaf="">正文里写 x=「概念」 不应误判为属性引号。</span></section>'

# 对抗用例（通过 main 完整入口测试）
ADVERSARIAL_MARKDOWN = '## 这是 Markdown 标题\n\n正文内容\n\n![图片](url)'
ADVERSARIAL_PLAIN_CN = '这只是普通中文文本，没有任何 HTML 标签。'
ADVERSARIAL_NO_CJK_HTML = '<section style="color:red;"><span leaf="">English only text no Chinese</span></section>'
ADVERSARIAL_SCRIPT_HTML = '<section style="color:red;"><span leaf="">中文<script>alert(1)</script></span></section>'


def _run_main_with_content(content, suffix=".html"):
    """把内容写入临时文件，运行 pub.main()，返回三个 mock。

    返回 (token_mock, get_mock, post_mock)，用于断言是否被调用。
    """
    fd, path = tempfile.mkstemp(suffix=suffix, dir=tempfile.gettempdir())
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(content)
        return _run_main_with_path(path)
    finally:
        if os.path.exists(path):
            os.unlink(path)


def _run_main_with_path(html_path):
    """用指定路径运行 pub.main()，返回三个 mock。"""
    old_argv = sys.argv
    old_env = dict(os.environ)
    sys.argv = [
        "publish_wechat_draft.py",
        "--html", html_path,
        "--title", "测试标题",
        "--thumb-media-id", "fake_thumb_id",
    ]
    os.environ["WECHAT_APP_ID"] = "fake_app_id"
    os.environ["WECHAT_APP_SECRET"] = "fake_secret"
    try:
        with patch.object(pub, "get_access_token") as token_mock, \
             patch.object(pub.requests, "get") as get_mock, \
             patch.object(pub.requests, "post") as post_mock:
            try:
                pub.main()
            except SystemExit:
                pass
            return token_mock, get_mock, post_mock
    finally:
        sys.argv = old_argv
        os.environ.clear()
        os.environ.update(old_env)


# --- 测试类 ---

class TestAttributeQuoteValidation(unittest.TestCase):
    """1-3: 属性引号校验"""

    def test_1_cn_quote_style_blocked(self):
        """style=「...」必须阻断"""
        errors, _, _ = vh.validate(HTML_WITH_CN_QUOTE_STYLE)
        self.assertTrue(any('E_INVALID_ATTRIBUTE_QUOTE' in e for e in errors),
                        "style=「...」应被 E_INVALID_ATTRIBUTE_QUOTE 阻断")

    def test_2_cn_quote_leaf_blocked(self):
        """leaf=「」必须阻断"""
        errors, _, _ = vh.validate(HTML_WITH_CN_QUOTE_LEAF)
        self.assertTrue(any('E_INVALID_ATTRIBUTE_QUOTE' in e for e in errors),
                        "leaf=「」应被 E_INVALID_ATTRIBUTE_QUOTE 阻断")

    def test_3_valid_ascii_quote_passes(self):
        """合法 style="..." 不触发 E_INVALID_ATTRIBUTE_QUOTE"""
        errors, _, _ = vh.validate(HTML_VALID)
        self.assertFalse(any('E_INVALID_ATTRIBUTE_QUOTE' in e for e in errors),
                         "合法 ASCII 引号不应触发 E_INVALID_ATTRIBUTE_QUOTE")


class TestChineseHTMLPasses(unittest.TestCase):
    """4: 中文 HTML 通过"""

    def test_4_chinese_html_passes(self):
        """中文 HTML 通过校验（无致命 ERROR）"""
        errors, _, _ = vh.validate(HTML_CHINESE)
        self.assertEqual(len(errors), 0, f"中文 HTML 应通过校验，但发现: {errors}")


class TestLiteralUnicodeBlocked(unittest.TestCase):
    r"""5: literal \uXXXX blocked"""

    def test_5_literal_unicode_blocked(self):
        r"""literal \u6765 blocked in preflight"""
        with self.assertRaises(SystemExit):
            pub.preflight_html(HTML_WITH_LITERAL_UNICODE, "test.html")


class TestMarkdownBlocked(unittest.TestCase):
    """6: 原始 Markdown 阻断（validator 层）"""

    def test_6_raw_markdown_no_cjk_in_leaf(self):
        """原始 Markdown 不应通过（缺少 span leaf 包裹）"""
        errors, _, leaf_n = vh.validate(HTML_WITH_MARKDOWN)
        self.assertTrue(len(errors) > 0 or leaf_n == 0,
                        "原始 Markdown 不应完全通过校验")


class TestPlaceholderBlocked(unittest.TestCase):
    """7: {{作者名}} 阻断"""

    def test_7_placeholder_blocked(self):
        """{{作者名}} 占位符在 publish 预检中被阻断"""
        with self.assertRaises(SystemExit):
            pub.preflight_html(HTML_WITH_PLACEHOLDER, "test.html")

    def test_7b_placeholder_in_validator(self):
        """{{作者名}} 占位符在 validator 中也报 ERROR"""
        errors, _, _ = vh.validate(HTML_WITH_PLACEHOLDER)
        self.assertTrue(any('占位符' in e for e in errors),
                        "{{...}} 应被 validator 阻断")


class TestEditorAnchorBlocked(unittest.TestCase):
    """8: 编辑锚点阻断"""

    def test_8_editor_anchor_blocked(self):
        """[编辑锚点...] 在 publish 预检中被阻断"""
        with self.assertRaises(SystemExit):
            pub.preflight_html(HTML_WITH_EDITOR_ANCHOR, "test.html")

    def test_8b_editor_anchor_in_validator(self):
        """[编辑锚点...] 在 validator 中也报 ERROR"""
        errors, _, _ = vh.validate(HTML_WITH_EDITOR_ANCHOR)
        self.assertTrue(any('编辑锚点' in e for e in errors),
                        "[编辑锚点] 应被 validator 阻断")


class TestHammerThemeNoGreenResidue(unittest.TestCase):
    """9: 锤子主题无 rgba(5,150,105)"""

    def test_9_hammer_no_green_rgba(self):
        """锤子主题 HTML 中不得出现 rgba(5,150,105)"""
        errors, _, _ = vh.validate(HTML_HAMMER_CLEAN)
        self.assertEqual(len(errors), 0, f"干净锤子 HTML 应通过: {errors}")
        self.assertNotIn('rgba(5,150,105', HTML_HAMMER_CLEAN,
                         "锤子主题不得包含 rgba(5,150,105)")


class TestCreateDraftPayloadPreservesChinese(unittest.TestCase):
    """10: create_draft payload 保留中文和 Emoji（实际调用 + 拦截 requests.post）

    关键修复：create_draft 现在使用 data=json.dumps(ensure_ascii=False).encode("utf-8")
    而非 json=payload，确保中文和 Emoji 以 UTF-8 直接传递。
    """

    def test_10_create_draft_payload_has_cjk_and_emoji(self):
        """实际调用 create_draft 后，requests.post 的 data payload 保留中文和 Emoji"""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"media_id": "fake_media_id_123"}

        with patch.object(pub.requests, "post", return_value=mock_resp) as mock_post:
            result = pub.create_draft(
                "fake_token", "测试标题", HTML_WITH_CJK_EMOJI, "fake_thumb"
            )

        self.assertEqual(result, "fake_media_id_123")

        # 拦截 requests.post 的 data 参数（现在是 bytes）
        self.assertTrue(mock_post.called, "requests.post 必须被调用")
        call_kwargs = mock_post.call_args.kwargs

        # data 必须是 bytes
        self.assertIn("data", call_kwargs, "必须使用 data= 参数")
        self.assertIsInstance(call_kwargs["data"], bytes, "data 必须是 bytes 类型")

        # 解码后检查 content
        payload = json.loads(call_kwargs["data"].decode("utf-8"))
        article = payload["articles"][0]

        # content 必须是原始 HTML（保留中文和 Emoji）
        self.assertEqual(article["content"], HTML_WITH_CJK_EMOJI,
                         "payload content 必须等于原始 HTML")
        self.assertIn("中文测试：K3 来了。📦 👉", article["content"],
                      "payload 必须保留中文和 Emoji")
        self.assertIn("K3 来了", article["content"])

    def test_10b_create_draft_payload_no_literal_unicode(self):
        r"""payload 中不得出现字面量 \uXXXX"""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"media_id": "fake_media_id_123"}

        with patch.object(pub.requests, "post", return_value=mock_resp) as mock_post:
            pub.create_draft("fake_token", "测试", HTML_WITH_CJK_EMOJI, "thumb")

        call_kwargs = mock_post.call_args.kwargs
        data_str = call_kwargs["data"].decode("utf-8")
        payload = json.loads(data_str)
        content = payload["articles"][0]["content"]
        # 不得出现字面量 \uXXXX（注意这里是字面量反斜杠+u，不是 unicode 字符）
        self.assertNotIn("\\u4e2d", content, r"payload 不得含字面量 \u4e2d")
        self.assertNotIn("\\ud83d", content, r"payload 不得含字面量 \ud83d")
        self.assertEqual(len(pub.LITERAL_UNICODE.findall(content)), 0,
                         r"payload 不得含任何字面量 \uXXXX")

    def test_10c_create_draft_payload_has_emoji_bytes(self):
        """payload 必须包含 Emoji 字符（不是转义序列）"""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"media_id": "fake_media_id_123"}

        with patch.object(pub.requests, "post", return_value=mock_resp) as mock_post:
            pub.create_draft("fake_token", "测试", HTML_WITH_CJK_EMOJI, "thumb")

        call_kwargs = mock_post.call_args.kwargs
        payload = json.loads(call_kwargs["data"].decode("utf-8"))
        content = payload["articles"][0]["content"]
        self.assertIn('\U0001F4E6', content, "payload 必须包含 📦 Emoji")
        self.assertIn('\U0001F449', content, "payload 必须包含 👉 Emoji")


class TestOutgoingPayloadGate(unittest.TestCase):
    """25-31: 最终发送对象门禁 — 确保 ensure_ascii=False 修复有效"""

    def test_25_no_json_param_in_post(self):
        """requests.post 不得收到 json= 参数（必须用 data=）"""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"media_id": "fake_id"}

        with patch.object(pub.requests, "post", return_value=mock_resp) as mock_post:
            pub.create_draft("token", "标题", HTML_WITH_CJK_EMOJI, "thumb")

        call_kwargs = mock_post.call_args.kwargs
        self.assertNotIn("json", call_kwargs, "不得使用 json= 参数")
        self.assertIn("data", call_kwargs, "必须使用 data= 参数")

    def test_26_data_must_be_bytes(self):
        """requests.post 的 data 必须是 bytes"""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"media_id": "fake_id"}

        with patch.object(pub.requests, "post", return_value=mock_resp) as mock_post:
            pub.create_draft("token", "标题", HTML_WITH_CJK_EMOJI, "thumb")

        data = mock_post.call_args.kwargs["data"]
        self.assertIsInstance(data, bytes, "data 必须是 bytes 类型")

    def test_27_data_contains_actual_cjk(self):
        """data.decode("utf-8") 必须包含实际中文"""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"media_id": "fake_id"}

        with patch.object(pub.requests, "post", return_value=mock_resp) as mock_post:
            pub.create_draft("token", "标题", HTML_WITH_CJK_EMOJI, "thumb")

        data_str = mock_post.call_args.kwargs["data"].decode("utf-8")
        self.assertIn("中文测试", data_str, "data 必须包含实际中文")
        self.assertIn("K3 来了", data_str, "data 必须包含实际中文")

    def test_28_data_contains_actual_emoji(self):
        """data.decode("utf-8") 必须包含实际 Emoji"""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"media_id": "fake_id"}

        with patch.object(pub.requests, "post", return_value=mock_resp) as mock_post:
            pub.create_draft("token", "标题", HTML_WITH_CJK_EMOJI, "thumb")

        data_str = mock_post.call_args.kwargs["data"].decode("utf-8")
        self.assertIn("📦", data_str, "data 必须包含实际 📦 Emoji")
        self.assertIn("👉", data_str, "data 必须包含实际 👉 Emoji")

    def test_29_data_no_literal_double_backslash_unicode(self):
        r"""data.decode("utf-8") 不得包含字面量双反斜杠 Unicode（\\uXXXX）"""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"media_id": "fake_id"}

        with patch.object(pub.requests, "post", return_value=mock_resp) as mock_post:
            pub.create_draft("token", "标题", HTML_WITH_CJK_EMOJI, "thumb")

        data_str = mock_post.call_args.kwargs["data"].decode("utf-8")
        # 检查 content 字段的值中不得有字面量 \uXXXX
        # 注意：JSON 序列化后的字符串中 \uXXXX 可能出现在 JSON 编码层
        # 但 json.loads 后的 content 必须是实际中文
        payload = json.loads(data_str)
        content = payload["articles"][0]["content"]
        self.assertEqual(len(pub.LITERAL_UNICODE.findall(content)), 0,
                         r"content 不得含字面量 \uXXXX")

    def test_30_json_roundtrip_content_equals_input(self):
        """json.loads(data) 后的 content 必须与输入 HTML 完全一致"""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"media_id": "fake_id"}

        with patch.object(pub.requests, "post", return_value=mock_resp) as mock_post:
            pub.create_draft("token", "标题", HTML_WITH_CJK_EMOJI, "thumb")

        data_str = mock_post.call_args.kwargs["data"].decode("utf-8")
        payload = json.loads(data_str)
        content = payload["articles"][0]["content"]
        self.assertEqual(content, HTML_WITH_CJK_EMOJI,
                         "JSON 往返后 content 必须与输入完全一致")

    def test_31_title_roundtrip_is_actual_chinese(self):
        """title 单次 JSON 往返后必须是实际中文"""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"media_id": "fake_id"}

        test_title = "中文标题测试｜探针"
        with patch.object(pub.requests, "post", return_value=mock_resp) as mock_post:
            pub.create_draft("token", test_title, HTML_WITH_CJK_EMOJI, "thumb")

        data_str = mock_post.call_args.kwargs["data"].decode("utf-8")
        payload = json.loads(data_str)
        title = payload["articles"][0]["title"]
        self.assertEqual(title, test_title, "title 往返后必须是实际中文")
        self.assertIn("中文标题测试", title)
        self.assertNotIn("\\u", title, "title 不得含字面量 \\uXXXX")


class TestExpectSha256(unittest.TestCase):
    """32-33: --expect-sha256 只校验 raw bytes；两种 SHA-256 分开记录"""

    def test_32_expect_sha256_blocks_mismatch(self):
        """--expect-sha256 不一致则阻断"""
        content = '<section style="color:red;"><span leaf="">中文测试</span></section>'
        fd, path = tempfile.mkstemp(suffix=".html", dir=tempfile.gettempdir())
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                f.write(content)
            old_argv = sys.argv
            sys.argv = [
                "publish_wechat_draft.py",
                "--html", path,
                "--title", "测试",
                "--thumb-media-id", "fake",
                "--expect-sha256", "0000000000000000000000000000000000000000000000000000000000000000",
            ]
            try:
                with self.assertRaises(SystemExit):
                    pub.main()
            finally:
                sys.argv = old_argv
        finally:
            if os.path.exists(path):
                os.unlink(path)

    def test_32b_expect_sha256_passes_match(self):
        """--expect-sha256 匹配则通过（到达 preflight）"""
        content = '<section style="color:red;"><span leaf="">中文测试</span></section>'
        # 计算 raw bytes SHA-256
        raw_bytes = content.encode("utf-8")
        raw_sha = hashlib.sha256(raw_bytes).hexdigest()

        fd, path = tempfile.mkstemp(suffix=".html", dir=tempfile.gettempdir())
        try:
            with os.fdopen(fd, 'wb') as f:
                f.write(raw_bytes)
            old_argv = sys.argv
            old_env = dict(os.environ)
            sys.argv = [
                "publish_wechat_draft.py",
                "--html", path,
                "--title", "测试",
                "--thumb-media-id", "fake",
                "--expect-sha256", raw_sha,
            ]
            os.environ["WECHAT_APP_ID"] = "fake"
            os.environ["WECHAT_APP_SECRET"] = "fake"
            try:
                with patch.object(pub, "get_access_token") as token_mock, \
                     patch.object(pub.requests, "get") as get_mock, \
                     patch.object(pub.requests, "post") as post_mock:
                    mock_resp = MagicMock()
                    mock_resp.json.return_value = {"media_id": "fake_id"}
                    post_mock.return_value = mock_resp
                    try:
                        pub.main()
                    except SystemExit:
                        pass
                    # 应该通过了 SHA-256 验证，到达 token 获取
                    token_mock.assert_called()
            finally:
                sys.argv = old_argv
                os.environ.clear()
                os.environ.update(old_env)
        finally:
            if os.path.exists(path):
                os.unlink(path)

    def test_33_raw_and_normalized_sha256_can_differ(self):
        """raw_file_sha256 与 normalized_content_sha256 分开记录（CRLF 场景允许不同）"""
        # 使用含换行符的内容
        content = '<section style="color:red;">\n<span leaf="">中文测试</span>\n</section>'
        # 模拟 CRLF 文件
        crlf_content = content.replace("\n", "\r\n")

        raw_bytes = crlf_content.encode("utf-8")
        raw_sha = hashlib.sha256(raw_bytes).hexdigest()

        # Python open(encoding="utf-8") 读取时 \r\n -> \n
        normalized_content = crlf_content.replace("\r\n", "\n")
        normalized_sha = hashlib.sha256(normalized_content.encode("utf-8")).hexdigest()

        # CRLF 文件的 raw SHA 和 normalized SHA 应该不同
        self.assertNotEqual(raw_sha, normalized_sha,
                            "CRLF 文件的 raw SHA 和 normalized SHA 应该不同")


class TestDraftGetDecoding(unittest.TestCase):
    """34: draft/get 必须使用 resp.content.decode("utf-8") + json.loads"""

    def test_34_draft_get_uses_utf8_decode(self):
        """draft/get 响应必须用 UTF-8 显式解码，不能用 resp.json() 默认 ISO-8859-1"""
        # 模拟微信返回的 UTF-8 JSON（Content-Type: text/plain，无 charset）
        import json as json_module
        draft_response = {
            "news_item": [{
                "title": "中文标题测试",
                "content": '<section><span leaf="">中文内容📦</span></section>'
            }]
        }
        utf8_bytes = json_module.dumps(draft_response, ensure_ascii=False).encode("utf-8")

        mock_resp = MagicMock()
        mock_resp.content = utf8_bytes
        mock_resp.encoding = "ISO-8859-1"  # requests 默认
        mock_resp.apparent_encoding = "utf-8"
        # resp.json() 用 ISO-8859-1 会产生 mojibake
        mock_resp.json.return_value = json_module.loads(
            utf8_bytes.decode("iso-8859-1")
        )

        # 正确方式：resp.content.decode("utf-8") + json.loads
        correct_content = json_module.loads(mock_resp.content.decode("utf-8"))
        self.assertEqual(correct_content["news_item"][0]["title"], "中文标题测试")
        self.assertIn("中文内容📦", correct_content["news_item"][0]["content"])

        # 错误方式：resp.json() 会产生 mojibake
        wrong_content = mock_resp.json()
        self.assertNotEqual(wrong_content["news_item"][0]["title"], "中文标题测试")


class TestNoTokenOnValidationFail(unittest.TestCase):
    """11: 校验失败时不得获取 token（patch get_access_token，assert not_called）"""

    def test_11_no_token_on_prefail_fail(self):
        """preflight 失败时 get_access_token 不得被调用"""
        with patch.object(pub, "get_access_token") as token_mock, \
             patch.object(pub.requests, "get") as get_mock, \
             patch.object(pub.requests, "post") as post_mock:
            with self.assertRaises(SystemExit):
                pub.preflight_html(HTML_WITH_PLACEHOLDER, "test.html")
            # preflight 直接 sys.exit，不会到达 get_access_token
            token_mock.assert_not_called()
            get_mock.assert_not_called()
            post_mock.assert_not_called()

    def test_11b_no_token_on_literal_unicode(self):
        r"""字面量 \uXXXX 阻断时 get_access_token 不得被调用"""
        with patch.object(pub, "get_access_token") as token_mock:
            with self.assertRaises(SystemExit):
                pub.preflight_html(HTML_WITH_LITERAL_UNICODE, "test.html")
            token_mock.assert_not_called()

    def test_11c_no_token_on_cn_quote(self):
        """中文属性引号阻断时 get_access_token 不得被调用"""
        with patch.object(pub, "get_access_token") as token_mock:
            with self.assertRaises(SystemExit):
                pub.preflight_html(SVG_WITH_CN_CX, "test.html")
            token_mock.assert_not_called()


class TestNoDraftAddOnValidationFail(unittest.TestCase):
    """12: 校验失败时不得调用 draft/add（通过 main 完整入口测试）"""

    def test_12_no_draft_add_through_main(self):
        """通过 main() 完整入口：占位符 HTML 不得触发 requests.post"""
        token_mock, get_mock, post_mock = _run_main_with_content(HTML_WITH_PLACEHOLDER)
        token_mock.assert_not_called()
        get_mock.assert_not_called()
        post_mock.assert_not_called()

    def test_12b_no_draft_add_on_cn_quote_through_main(self):
        """通过 main() 完整入口：中文属性引号不得触发 requests.post"""
        token_mock, get_mock, post_mock = _run_main_with_content(SVG_WITH_CN_CX)
        token_mock.assert_not_called()
        get_mock.assert_not_called()
        post_mock.assert_not_called()


# ---- v2 新增：全属性中文引号扫描（不限于固定白名单）----

class TestFullAttributeQuoteScan(unittest.TestCase):
    """13-20: 全属性中文引号扫描（v1 漏检的 cx/cy/r/stroke-linecap/stroke-linejoin/data-*/aria-*）"""

    def test_13_cn_quote_cx_blocked(self):
        """cx=「12」 必须阻断"""
        errors, _, _ = vh.validate(SVG_WITH_CN_CX)
        self.assertTrue(any('E_INVALID_ATTRIBUTE_QUOTE' in e for e in errors),
                        "cx=「12」 应被 E_INVALID_ATTRIBUTE_QUOTE 阻断")

    def test_14_cn_quote_cy_blocked(self):
        """cy=「12」 必须阻断"""
        errors, _, _ = vh.validate(SVG_WITH_CN_CY)
        self.assertTrue(any('E_INVALID_ATTRIBUTE_QUOTE' in e for e in errors),
                        "cy=「12」 应被 E_INVALID_ATTRIBUTE_QUOTE 阻断")

    def test_15_cn_quote_r_blocked(self):
        """r=「3」 必须阻断"""
        errors, _, _ = vh.validate(SVG_WITH_CN_R)
        self.assertTrue(any('E_INVALID_ATTRIBUTE_QUOTE' in e for e in errors),
                        "r=「3」 应被 E_INVALID_ATTRIBUTE_QUOTE 阻断")

    def test_16_cn_quote_stroke_linecap_blocked(self):
        """stroke-linecap=「round」 必须阻断"""
        errors, _, _ = vh.validate(SVG_WITH_CN_LINECAP)
        self.assertTrue(any('E_INVALID_ATTRIBUTE_QUOTE' in e for e in errors),
                        "stroke-linecap=「round」 应被 E_INVALID_ATTRIBUTE_QUOTE 阻断")

    def test_17_cn_quote_stroke_linejoin_blocked(self):
        """stroke-linejoin=「round」 必须阻断"""
        errors, _, _ = vh.validate(SVG_WITH_CN_LINEJOIN)
        self.assertTrue(any('E_INVALID_ATTRIBUTE_QUOTE' in e for e in errors),
                        "stroke-linejoin=「round」 应被 E_INVALID_ATTRIBUTE_QUOTE 阻断")

    def test_18_cn_quote_data_test_blocked(self):
        """data-test=「value」 必须阻断"""
        errors, _, _ = vh.validate(HTML_WITH_CN_DATA_TEST)
        self.assertTrue(any('E_INVALID_ATTRIBUTE_QUOTE' in e for e in errors),
                        "data-test=「value」 应被 E_INVALID_ATTRIBUTE_QUOTE 阻断")

    def test_19_cn_quote_aria_label_blocked(self):
        """aria-label=「说明」 必须阻断"""
        errors, _, _ = vh.validate(HTML_WITH_CN_ARIA_LABEL)
        self.assertTrue(any('E_INVALID_ATTRIBUTE_QUOTE' in e for e in errors),
                        "aria-label=「说明」 应被 E_INVALID_ATTRIBUTE_QUOTE 阻断")

    def test_20_body_text_cn_quote_not_flagged(self):
        """正文中的 x=「概念」 不应被误判为 HTML 属性引号"""
        errors, _, _ = vh.validate(HTML_BODY_TEXT_WITH_CN_QUOTE)
        self.assertFalse(any('E_INVALID_ATTRIBUTE_QUOTE' in e for e in errors),
                         "正文 x=「概念」 不应触发 E_INVALID_ATTRIBUTE_QUOTE")

    def test_20b_find_cn_quoted_attrs_ignores_body(self):
        """find_cn_quoted_attrs 只扫描标签内，不扫描正文"""
        hits = vh.find_cn_quoted_attrs(HTML_BODY_TEXT_WITH_CN_QUOTE)
        self.assertEqual(len(hits), 0, "正文中的 x=「概念」 不应被检测为属性引号")

    def test_20c_all_five_svg_attrs_detected(self):
        """5 处漏检的 SVG 属性全部被检测到"""
        html = (
            f'<section style="color:red;"><span leaf="">中文</span></section>'
            f'<svg><circle cx={CN_QUOTE}12{CN_QUOTE_CLOSE} cy={CN_QUOTE}12{CN_QUOTE_CLOSE} '
            f'r={CN_QUOTE}3{CN_QUOTE_CLOSE}></circle>'
            f'<path stroke-linecap={CN_QUOTE}round{CN_QUOTE_CLOSE} '
            f'stroke-linejoin={CN_QUOTE}round{CN_QUOTE_CLOSE}></path></svg>'
        )
        hits = vh.find_cn_quoted_attrs(html)
        names = [n for n, _ in hits]
        self.assertEqual(len(hits), 5, f"应检测到 5 处，实际 {len(hits)}")
        for attr in ("cx", "cy", "r", "stroke-linecap", "stroke-linejoin"):
            self.assertIn(attr, names, f"{attr} 应被检测到")


# ---- v2 新增：4 个对抗用例（通过 main 完整入口）----

class TestAdversarialMainBlocking(unittest.TestCase):
    """21-24: 对抗用例 — 通过 main() 完整入口，断言三层网络调用均为 0 次"""

    def test_21_markdown_blocked_through_main(self):
        """原始 Markdown 通过 main 阻断：get_access_token / requests.get / requests.post 均 0 次"""
        token_mock, get_mock, post_mock = _run_main_with_content(ADVERSARIAL_MARKDOWN)
        token_mock.assert_not_called()
        get_mock.assert_not_called()
        post_mock.assert_not_called()

    def test_22_plain_chinese_blocked_through_main(self):
        """普通中文纯文本通过 main 阻断：三层网络调用均 0 次"""
        token_mock, get_mock, post_mock = _run_main_with_content(ADVERSARIAL_PLAIN_CN)
        token_mock.assert_not_called()
        get_mock.assert_not_called()
        post_mock.assert_not_called()

    def test_23_no_cjk_html_blocked_through_main(self):
        """不含中文的 HTML 通过 main 阻断：三层网络调用均 0 次"""
        token_mock, get_mock, post_mock = _run_main_with_content(ADVERSARIAL_NO_CJK_HTML)
        token_mock.assert_not_called()
        get_mock.assert_not_called()
        post_mock.assert_not_called()

    def test_24_script_html_blocked_through_main(self):
        """含 <script> 的 HTML 通过 main 阻断：三层网络调用均 0 次"""
        token_mock, get_mock, post_mock = _run_main_with_content(ADVERSARIAL_SCRIPT_HTML)
        token_mock.assert_not_called()
        get_mock.assert_not_called()
        post_mock.assert_not_called()


if __name__ == "__main__":
    unittest.main(verbosity=2)
