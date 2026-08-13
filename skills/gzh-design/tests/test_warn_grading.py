#!/usr/bin/env python3
"""档54R WARN 分级 + OBS-85 测试。

覆盖:
1. --allow-warnings 关闭时 ①(半角标点/英文引号)仍阻断
2. 开关开启时 ① 放行且留痕完整(allowance_record.json 逐字)
3. 开关开启时 ②(span leaf 未包裹)仍阻断
4. 任何情况下 ③(HTML 解析中断,已升 ERROR)阻断——开关全开也必须拦下
5. 放行记录内容逐字正确(rule/category/text/snippets)
"""
import json
import os
import sys
import tempfile
import unittest
from unittest.mock import patch

SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(SKILL_ROOT, "scripts"))

import validate_gzh_html as vh
import publish_wechat_draft as pub

# ① 触发:两个 leaf 文本节点各含一处 ASCII 引号(模拟正文章节标题 + 目录)
HTML_HALF_PUNCT = (
    '<section style="margin:0 20px;"><p style="font-size:14px;">'
    '<span leaf="">一、把贵模型留给"思考"</span></p></section>'
    '<section style="margin:0 20px;"><p style="font-size:14px;">'
    '<span leaf="">目录·一、把贵模型留给"思考"</span></p></section>'
)

# ② 触发:存在 leaf 包裹,但也有未包裹的中文文本
HTML_UNWRAPPED = (
    '<section style="margin:0 20px;"><span leaf="">已包裹中文</span>'
    '未包裹中文段落</section>'
)

# 完全合规基线(无 ERROR、无 WARN)
HTML_CLEAN = ('<section style="margin:0 20px;"><p style="font-size:14px;">'
              '<span leaf="">完全合规的段落。</span></p></section>')


class TestGradingBasics(unittest.TestCase):
    def test_parse_breakdown_is_error_now(self):
        """OBS-85:解析中断从 WARN 升为 ERROR(validate 层)。"""
        with patch.object(vh.LeafChecker, "feed",
                          side_effect=RuntimeError("boom")):
            errors, warnings, _ = vh.validate(HTML_CLEAN, "x.html")
        self.assertTrue(any("HTML 解析中断" in e for e in errors))
        self.assertFalse(any("HTML 解析中断" in w for w in warnings))

    def test_graded_categories(self):
        """validate_graded 返回结构化类别:①allowable ②blocking。"""
        _, _, _, graded = vh.validate_graded(HTML_HALF_PUNCT, "x.html")
        self.assertTrue(any(g["category"] == vh.WARN_ALLOWABLE
                            and g["rule"] == "half_width_punct" for g in graded))
        _, _, _, graded2 = vh.validate_graded(HTML_UNWRAPPED, "x.html")
        self.assertTrue(any(g["category"] == vh.WARN_BLOCKING
                            and g["rule"] == "unwrapped_leaf" for g in graded2))


class TestAllowSwitch(unittest.TestCase):
    def test_switch_off_half_punct_blocks(self):
        """① 开关关闭 → 阻断。"""
        with self.assertRaises(SystemExit):
            pub.preflight_html(HTML_HALF_PUNCT, "x.html")

    def test_switch_on_half_punct_allows_with_record(self):
        """① 开关开启 → 放行且留痕完整。"""
        with tempfile.TemporaryDirectory() as td:
            # 不抛异常 = 放行
            pub.preflight_html(HTML_HALF_PUNCT, "x.html",
                               audit_dir=td, allow_warnings=True)
            rec_path = os.path.join(td, "allowance_record.json")
            self.assertTrue(os.path.isfile(rec_path), "放行记录必须落盘")
            rec = json.load(open(rec_path, encoding="utf-8"))
            self.assertEqual(rec["schema_version"], "1.0")
            self.assertIs(rec["allow_warnings"], True)
            self.assertEqual(len(rec["entries"]), 1)
            e = rec["entries"][0]
            self.assertEqual(e["rule"], "half_width_punct")
            self.assertEqual(e["category"], "allowable")
            self.assertIn("2 处正文疑似半角标点/英文引号", e["text"])
            self.assertIn('「一、把贵模型留给"思考"」', e["text"])
            self.assertEqual(len(e["snippets"]), 2)
            self.assertIn('一、把贵模型留给"思考"', e["snippets"][0])
            self.assertIn('目录·一、把贵模型留给"思考"', e["snippets"][1])

    def test_switch_on_unwrapped_still_blocks(self):
        """② 开关开启 → 仍阻断(不可放行类别)。"""
        with self.assertRaises(SystemExit):
            pub.preflight_html(HTML_UNWRAPPED, "x.html",
                               allow_warnings=True)

    def test_parse_breakdown_blocks_even_with_switch(self):
        """③ 反证:解析中断 + 开关全开 → 必须阻断。"""
        with patch.object(vh.LeafChecker, "feed",
                          side_effect=RuntimeError("boom")):
            with self.assertRaises(SystemExit):
                pub.preflight_html(HTML_CLEAN, "x.html",
                                   audit_dir=tempfile.gettempdir(),
                                   allow_warnings=True)

    def test_clean_html_no_record_without_allow(self):
        """完全合规 + 开关关闭:不产生放行记录,不阻断。"""
        with tempfile.TemporaryDirectory() as td:
            pub.preflight_html(HTML_CLEAN, "x.html", audit_dir=td)
            self.assertFalse(
                os.path.isfile(os.path.join(td, "allowance_record.json")))


if __name__ == "__main__":
    unittest.main()
