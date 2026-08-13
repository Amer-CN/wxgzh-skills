#!/usr/bin/env python3
"""生成 dialogue 热修复视觉验收样稿（6 主题）"""
import os, sys

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(SKILL, "scripts"))
from generate_advanced_html import dialogue, T, s

OUT = os.path.join(SKILL, "tests", "advanced-components", "dialogue-hotfix")
os.makedirs(OUT, exist_ok=True)

TURNS = [
    ("assistant", "你好，我是排版助手，可以帮你解决公众号排版问题。"),
    ("user", "粘贴后代码高亮全丢了？"),
    ("assistant", "这是因为公众号编辑器会清洗 class 属性和外部 CSS。所有样式必须使用内联 style 属性，写在标签的 style=\"...\" 里面。不能依赖外部样式表或 class 选择器，否则粘贴后样式会完全丢失。"),
    ("user", "原来如此，那图片的圆角和阴影也必须内联吗？"),
    ("user", "还有，表格的边框怎么处理？"),
    ("assistant", "是的，图片圆角和阴影都必须内联。表格边框同样写在 td/th 的 style 属性里。"),
    ("assistant", "总之记住一个原则：公众号里所有视觉效果，只能靠内联 style 实现。"),
    ("user", "明白了，谢谢！"),
]

for theme_id in T:
    t = T[theme_id]
    inner = dialogue(theme_id, title="公众号排版常见问题", turns=TURNS)
    # 包一层 430px 容器模拟手机宽度
    wrapper = f'''<section style="max-width:430px;margin:0 auto;background:{t["bg"] if t["style"]!="ticket" else "#ffffff"};padding:16px 12px;font-family:-apple-system,BlinkMacSystemFont,'PingFang SC','Hiragino Sans GB','Microsoft YaHei',sans-serif;color:{t["tx"]};line-height:1.75;overflow-x:hidden;">
{inner}
</section>'''
    fp = os.path.join(OUT, f"dialogue-{theme_id}.html")
    with open(fp, "w", encoding="utf-8") as f:
        f.write(wrapper)

print(f"OK: 6 dialogue hotfix HTML files generated in {OUT}")
