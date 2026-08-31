#!/usr/bin/env python3
"""生成锤子升级验收的双主题对照 HTML 样例。

使用完全相同的测试文章，分别生成摸鱼绿和锤子两份 HTML。
两份文章文案、组件选择、组件顺序完全相同，只允许主题颜色不同。

覆盖组件：
- 封面 cover-breaking
- 横向目录 toc-scroll
- 金句 oneliner-card
- 4 个章节标题 chapter-title
- 正文段落 paragraph
- 强调与下划线（行内样式）
- pill-list
- ordered-list
- quote-box
- green-info / 砖红信息框
- timeline
- table
- 5 个高级组件：alert, facts, steps, checklist, dialogue
- fixed-signature（固定结尾署名）
- footer-cta
"""
import os
import sys

SKILL = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(SKILL, "tests", "hammer-upgrade")
os.makedirs(OUT, exist_ok=True)

# 两套配色 Token
PALETTES = {
    "moyu-green": {
        "name": "摸鱼绿",
        "primary": "#059669",
        "secondary": "#10B981",
        "dark": "#047857",
        "light_decor": "#34D399",
        "lighter_decor": "#6EE7B7",
        "lightest_decor": "#A7F3D0",
        "border_light": "#BBF7D0",
        "bg_light_green": "#ECFDF5",
        "bg_lightest_green": "#F0FDF4",
        "yellow_highlight": "#FDE68A",
        "yellow_bg": "#FFFBEB",
        "yellow_text": "#92400E",
        "red_underline": "#FECACA",
        "title_color": "#111827",
        "body_color": "#374151",
        "secondary_text": "#4B5563",
        "label_text": "#6B7280",
        "strike_text": "#4B5563",
        "aux_text": "#9CA3AF",
        "divider": "#D1D5DB",
        "border_gray": "#E5E7EB",
        "bg_light_gray": "#F3F4F6",
        "bg_extreme_light": "#F9FAFB",
        "dark_label_bg": "#111827",
        "rgba_primary_015": "rgba(5,150,105,0.15)",
        "rgba_primary_012": "rgba(5,150,105,0.12)",
        "rgba_primary_010": "rgba(5,150,105,0.1)",
        "rgba_primary_008": "rgba(5,150,105,0.08)",
        "rgba_primary_020": "rgba(5,150,105,0.2)",
        "rgba_primary_010_shadow": "rgba(5,150,105,0.12)",
        "rgba_primary_015_shadow": "rgba(5,150,105,0.15)",
        "highlight_word": "绿色高亮词",
        "color_desc": "绿色",
        "underline_desc": "绿色",
    },
    "hammer": {
        "name": "锤子风格",
        "primary": "#B3593B",
        "secondary": "#C86442",
        "dark": "#8A4530",
        "light_decor": "#DAB1A1",
        "lighter_decor": "#E3C6B9",
        "lightest_decor": "#EAD6CC",
        "border_light": "#DAB1A1",
        "bg_light_green": "#FAF9F5",
        "bg_lightest_green": "#F7F7F7",
        "yellow_highlight": "#E3C6B9",
        "yellow_bg": "#FAF9F5",
        "yellow_text": "#B3593B",
        "red_underline": "#FECACA",
        "title_color": "#555555",
        "body_color": "#555555",
        "secondary_text": "#555555",
        "label_text": "#737373",
        "strike_text": "#555555",
        "aux_text": "#737373",
        "divider": "rgba(202,202,199,0.35)",
        "border_gray": "rgba(202,202,199,0.18)",
        "bg_light_gray": "#F7F7F7",
        "bg_extreme_light": "#FAF9F5",
        "dark_label_bg": "#555555",
        "rgba_primary_015": "rgba(179,89,59,0.15)",
        "rgba_primary_012": "rgba(179,89,59,0.10)",
        "rgba_primary_010": "rgba(179,89,59,0.10)",
        "rgba_primary_008": "rgba(179,89,59,0.08)",
        "rgba_primary_020": "rgba(179,89,59,0.18)",
        "rgba_primary_010_shadow": "rgba(179,89,59,0.10)",
        "rgba_primary_015_shadow": "rgba(179,89,59,0.15)",
        "highlight_word": "砖红高亮词",
        "color_desc": "砖红",
        "underline_desc": "砖红",
    },
}


def s(x):
    return f'<span leaf="">{x}</span>'


def generate_article(theme_key):
    """生成完整文章 HTML"""
    t = PALETTES[theme_key]
    p = t["primary"]

    html_parts = []

    # === 全局容器 ===
    html_parts.append(
        f'<section style="max-width:677px;margin:0 auto;background:#ffffff;'
        f"font-family:-apple-system,BlinkMacSystemFont,'PingFang SC','Hiragino Sans GB',"
        f"'Microsoft YaHei',sans-serif;color:{t['body_color']};"
        f'line-height:1.75;letter-spacing:0.5px;overflow-x:hidden;">'
    )

    # === 1. 封面（无图版）===
    html_parts.append(
        f'''<section style="margin:0 0 32px;background:#fff;border:1.5px solid {t['rgba_primary_015']};border-radius:20px;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,0.06);width:100%;">
  <section style="padding:32px 28px 28px;">
    <section style="display:flex;align-items:center;gap:8px;margin-bottom:28px;">
      <span style="width:6px;height:6px;background:{p};border-radius:50%;"><span leaf=""><br></span></span>
      <span style="font-size:11px;font-weight:700;letter-spacing:3px;color:{p};"><span leaf="">TUTORIAL · 结构同构测试</span></span>
      <section style="flex:1;height:1px;overflow:hidden;background:linear-gradient(to right,{t['rgba_primary_012']},transparent);"><span leaf=""><br></span></section>
      <span style="font-size:10px;color:{t['divider']};font-weight:600;"><span leaf="">2026.07</span></span>
    </section>
    <section>
      <p style="font-size:15px;color:{t['strike_text']};margin:0 0 6px;text-decoration:line-through;letter-spacing:0.5px;">
        <span leaf="">排版只是换颜色？</span>
      </p>
      <p style="font-size:24px;font-weight:900;color:{t['title_color']};margin:0;line-height:1.05;letter-spacing:-2px;">
        <span leaf="">结构同构</span>
        <span style="color:{p};"><span leaf="">验收测试</span></span>
      </p>
      <p style="font-size:24px;font-weight:900;color:{p};margin:0 0 16px;line-height:1.05;letter-spacing:-2px;">
        <span leaf="">双主题对照</span>
      </p>
      <section style="width:48px;height:3px;background:linear-gradient(to right,{p},{t['light_decor']});border-radius:2px;margin-bottom:12px;">
        <span leaf=""><br></span>
      </section>
      <p style="font-size:13px;color:{t['aux_text']};margin:0;line-height:1.7;letter-spacing:0.5px;">
        <span leaf="">封面 · 目录 · 章节标题 · 正文 · 标签 · 列表 · 引用 · 提示 · 时间线 · 表格 · 高级组件 · 署名 · CTA</span>
      </p>
    </section>
  </section>
  <section style="background:linear-gradient(135deg,{p},{t['secondary']});padding:12px 28px;display:flex;align-items:center;justify-content:space-between;">
    <p style="font-size:12px;color:rgba(255,255,255,0.9);margin:0;font-weight:600;letter-spacing:0.5px;">
      <span leaf="">给自己造把锤子</span>
    </p>
    <section style="display:flex;gap:4px;">
      <span style="background:rgba(255,255,255,0.2);padding:1px 6px;border-radius:3px;font-size:8px;color:#fff;font-weight:600;"><span leaf="">结构测试</span></span>
      <span style="background:rgba(255,255,255,0.2);padding:1px 6px;border-radius:3px;font-size:8px;color:#fff;font-weight:600;"><span leaf="">双主题</span></span>
    </section>
  </section>
</section>'''
    )

    # === 2. 横向目录 ===
    html_parts.append(
        f'''<section style="margin:0 20px 32px;">
  <section style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px;">
    <p style="font-size:10px;color:{t['aux_text']};margin:0;text-transform:uppercase;letter-spacing:2px;font-weight:600;">
      <span leaf="">📦 4 Parts + Conclusion</span>
    </p>
    <p style="font-size:10px;color:{t['aux_text']};margin:0;">
      <span leaf="">👉 滑动</span>
    </p>
  </section>
  <section style="overflow-x:scroll;-webkit-overflow-scrolling:touch;white-space:nowrap;padding-bottom:8px;">
    <section style="display:inline-block;white-space:normal;vertical-align:top;width:110px;background:linear-gradient(135deg,{p},{t['secondary']});border-radius:12px;padding:12px;margin-right:8px;">
      <p style="font-size:9px;font-weight:700;color:rgba(255,255,255,0.7);letter-spacing:1px;margin:0 0 5px;">
        <span leaf="">PART 01</span>
      </p>
      <p style="font-size:13px;font-weight:800;color:#fff;margin:0 0 3px;">
        <span leaf="">封面与目录</span>
      </p>
      <p style="font-size:10px;color:rgba(255,255,255,0.7);margin:0;">
        <span leaf="">结构基准</span>
      </p>
    </section>
    <section style="display:inline-block;white-space:normal;vertical-align:top;width:110px;background:#fff;border:1px solid {t['border_gray']};border-radius:12px;padding:12px;margin-right:8px;box-shadow:0 2px 6px rgba(0,0,0,0.04);">
      <p style="font-size:9px;font-weight:700;color:{t['aux_text']};letter-spacing:1px;margin:0 0 5px;">
        <span leaf="">PART 02</span>
      </p>
      <p style="font-size:13px;font-weight:800;color:{t['title_color']};margin:0 0 3px;">
        <span leaf="">正文与标签</span>
      </p>
      <p style="font-size:10px;color:{t['aux_text']};margin:0;">
        <span leaf="">行内样式</span>
      </p>
    </section>
    <section style="display:inline-block;white-space:normal;vertical-align:top;width:110px;background:#fff;border:1px solid {t['border_gray']};border-radius:12px;padding:12px;margin-right:8px;box-shadow:0 2px 6px rgba(0,0,0,0.04);">
      <p style="font-size:9px;font-weight:700;color:{t['aux_text']};letter-spacing:1px;margin:0 0 5px;">
        <span leaf="">PART 03</span>
      </p>
      <p style="font-size:13px;font-weight:800;color:{t['title_color']};margin:0 0 3px;">
        <span leaf="">布局组件</span>
      </p>
      <p style="font-size:10px;color:{t['aux_text']};margin:0;">
        <span leaf="">列表与表格</span>
      </p>
    </section>
    <section style="display:inline-block;white-space:normal;vertical-align:top;width:110px;background:#fff;border:1px solid {t['border_gray']};border-radius:12px;padding:12px;margin-right:8px;box-shadow:0 2px 6px rgba(0,0,0,0.04);">
      <p style="font-size:9px;font-weight:700;color:{t['aux_text']};letter-spacing:1px;margin:0 0 5px;">
        <span leaf="">PART 04</span>
      </p>
      <p style="font-size:13px;font-weight:800;color:{t['title_color']};margin:0 0 3px;">
        <span leaf="">高级组件</span>
      </p>
      <p style="font-size:10px;color:{t['aux_text']};margin:0;">
        <span leaf="">5 个示例</span>
      </p>
    </section>
    <section style="display:inline-block;white-space:normal;vertical-align:top;width:110px;background:#fff;border:1px solid {t['border_gray']};border-radius:12px;padding:12px;box-shadow:0 2px 6px rgba(0,0,0,0.04);">
      <p style="font-size:9px;font-weight:700;color:{t['aux_text']};letter-spacing:1px;margin:0 0 5px;">
        <span leaf="">PART ///</span>
      </p>
      <p style="font-size:13px;font-weight:800;color:{t['title_color']};margin:0 0 3px;">
        <span leaf="">写在最后</span>
      </p>
      <p style="font-size:10px;color:{t['aux_text']};margin:0;">
        <span leaf="">署名与 CTA</span>
      </p>
    </section>
  </section>
</section>'''
    )

    # === 3. 开头金句 ===
    html_parts.append(
        f'''<section style="background:#FFF;border:1px dashed {t['border_light']};border-radius:8px;padding:14px 16px;margin:0 20px 24px;text-align:center;">
  <p style="margin:0;line-height:1.6;">
    <span style="font-size:15px;color:{p};font-weight:bold;border-bottom:3px solid {t['yellow_highlight']};padding-bottom:2px;"><span leaf="">结构同构 = 相同的骨架，不同的肤色</span></span>
  </p>
</section>'''
    )

    # === 4. 前言正文 ===
    html_parts.append(
        f'<section style="margin:0 20px;">'
        f'<p style="margin-bottom:16px;font-size:14px;line-height:1.9;text-align:justify;">'
        f'{s("本文使用完全相同的文案和组件顺序，分别用摸鱼绿和锤子两套配色渲染。除了颜色，所有结构属性——字号、行高、间距、圆角、flex 布局——必须完全一致。")}'
        f'</p>'
        f'<p style="margin-bottom:16px;font-size:14px;line-height:1.9;text-align:justify;">'
        f'{s("这是")}'
        f'<strong style="color:{p};">{s("结构同构测试")}</strong>'
        f'{s("，验证锤子主题已完全对齐摸鱼绿原版结构。")}'
        f'</p>'
        f'</section>'
    )

    # === 5. 第一章 ===
    html_parts.append(
        f'''<section style="margin-top:16px;margin-bottom:32px;padding:0 20px;">
  <section style="display:flex;align-items:center;gap:16px;margin-bottom:24px;">
    <section style="text-align:center;flex-shrink:0;">
      <p style="margin:0;font-size:28px;font-weight:900;color:{p};line-height:1;letter-spacing:-2px;">
        <span leaf="">01</span>
      </p>
      <p style="margin:0;font-size:8px;font-weight:700;color:{t['divider']};letter-spacing:2px;">
        <span leaf="">PART</span>
      </p>
    </section>
    <span style="width:1px;height:36px;background:{t['border_gray']};flex-shrink:0;"><span leaf=""><br></span></span>
    <section>
      <p style="margin:0 0 1px;font-size:17px;font-weight:900;color:{t['title_color']};letter-spacing:0.3px;">
        <span leaf="">封面与目录结构</span>
      </p>
      <p style="margin:0;font-size:11px;font-weight:600;color:{t['aux_text']};letter-spacing:1.5px;">
        <span leaf="">COVER & TOC STRUCTURE</span>
      </p>
    </section>
  </section>
  <p style="margin-bottom:16px;font-size:14px;line-height:1.9;text-align:justify;">
    {s("封面包含顶部标签、日期、分隔线、划线旧认知、两行主标题、装饰短线、副标题和底部品牌条。目录使用横向滚动，第一卡片高亮，后续白底，最后为 PART ///。")}
  </p>
  <p style="margin-bottom:16px;font-size:14px;line-height:1.9;text-align:justify;">
    {s("正文使用 ")}
    <span style="background:{t['bg_light_gray']};color:{t['title_color']};padding:2px 6px;border-radius:4px;font-size:13px;font-weight:600;">{s("14px")}</span>
    {s(" 字号，")}
    <span style="border-bottom:2px solid {t['lightest_decor']};font-weight:600;">{s("line-height 1.9")}</span>
    {s(" 行高，")}
    <span style="color:{t['title_color']};font-weight:bold;border-bottom:3px solid {t['yellow_highlight']};">{s("justify")}</span>
    {s(" 对齐。")}
  </p>
</section>'''
    )

    # === 6. 第二章 ===
    html_parts.append(
        f'''<section style="margin-top:48px;margin-bottom:32px;padding:0 20px;">
  <section style="display:flex;align-items:center;gap:16px;margin-bottom:24px;">
    <section style="text-align:center;flex-shrink:0;">
      <p style="margin:0;font-size:28px;font-weight:900;color:{p};line-height:1;letter-spacing:-2px;">
        <span leaf="">02</span>
      </p>
      <p style="margin:0;font-size:8px;font-weight:700;color:{t['divider']};letter-spacing:2px;">
        <span leaf="">PART</span>
      </p>
    </section>
    <span style="width:1px;height:36px;background:{t['border_gray']};flex-shrink:0;"><span leaf=""><br></span></span>
    <section>
      <p style="margin:0 0 1px;font-size:17px;font-weight:900;color:{t['title_color']};letter-spacing:0.3px;">
        <span leaf="">行内样式与标签</span>
      </p>
      <p style="margin:0;font-size:11px;font-weight:600;color:{t['aux_text']};letter-spacing:1.5px;">
        <span leaf="">INLINE STYLES & LABELS</span>
      </p>
    </section>
  </section>
  <p style="margin-bottom:16px;font-size:14px;line-height:1.9;text-align:justify;">
    {s("本节展示 9 种行内样式和内容标签组的结构。")}
  </p>

  <!-- pill-list -->
  <section style="margin-bottom:14px;">
    <p style="margin:0 0 6px;">
      <span style="display:inline-block;font-size:13px;font-weight:700;color:{p};background:{t['rgba_primary_008']};padding:3px 10px;border-radius:999px;"><span style="display:inline-block;width:6px;height:6px;background:{p};border-radius:50%;margin-right:5px;vertical-align:middle;"><span leaf=""><br></span></span><span leaf="">胶囊列表项 A</span></span>
    </p>
    <p style="font-size:13px;color:{t['secondary_text']};margin:0;line-height:1.7;text-align:justify;">
      <span leaf="">这是胶囊列表项的描述文字，结构与摸鱼绿一致。</span>
    </p>
  </section>
  <section style="margin-bottom:14px;">
    <p style="margin:0 0 6px;">
      <span style="display:inline-block;font-size:13px;font-weight:700;color:{p};background:{t['rgba_primary_008']};padding:3px 10px;border-radius:999px;"><span style="display:inline-block;width:6px;height:6px;background:{p};border-radius:50%;margin-right:5px;vertical-align:middle;"><span leaf=""><br></span></span><span leaf="">胶囊列表项 B</span></span>
    </p>
  </section>

  <!-- ordered-list -->
  <section style="margin-bottom:24px;">
    <section style="display:flex;align-items:flex-start;gap:10px;margin-bottom:12px;">
      <span style="display:inline-flex;align-items:center;justify-content:center;width:22px;height:22px;background:{p};color:#fff;font-size:11px;font-weight:700;border-radius:50%;flex-shrink:0;margin-top:2px;"><span leaf="">1</span></span>
      <p style="font-size:14px;color:{t['body_color']};margin:0;line-height:1.9;flex:1;">
        <span leaf="">编号列表第一项，圆点 22px，gap 10px。</span>
      </p>
    </section>
    <section style="display:flex;align-items:flex-start;gap:10px;margin-bottom:12px;">
      <span style="display:inline-flex;align-items:center;justify-content:center;width:22px;height:22px;background:{p};color:#fff;font-size:11px;font-weight:700;border-radius:50%;flex-shrink:0;margin-top:2px;"><span leaf="">2</span></span>
      <p style="font-size:14px;color:{t['body_color']};margin:0;line-height:1.9;flex:1;">
        <span leaf="">编号列表第二项，结构与摸鱼绿一致。</span>
      </p>
    </section>
    <section style="display:flex;align-items:flex-start;gap:10px;margin-bottom:12px;">
      <span style="display:inline-flex;align-items:center;justify-content:center;width:22px;height:22px;background:{p};color:#fff;font-size:11px;font-weight:700;border-radius:50%;flex-shrink:0;margin-top:2px;"><span leaf="">3</span></span>
      <p style="font-size:14px;color:{t['body_color']};margin:0;line-height:1.9;flex:1;">
        <span leaf="">编号列表第三项。</span>
      </p>
    </section>
  </section>

  <!-- quote-box -->
  <section style="background:{t['bg_extreme_light']};border:1px dashed {t['divider']};border-radius:8px;padding:12px 16px;margin-bottom:24px;text-align:justify;">
    <p style="font-size:13px;color:{t['body_color']};margin:0;line-height:1.6;">
      {s("引用框使用虚线边框，结构与摸鱼绿完全一致，仅背景色和边框色不同。")}
    </p>
  </section>

  <!-- green-info / 砖红信息框 -->
  <section style="background:{t['bg_lightest_green']};padding:12px 16px;border-radius:8px;border:1px solid {t['border_light']};margin-bottom:20px;">
    <p style="font-size:13px;color:{t['body_color']};margin:0;line-height:1.7;text-align:justify;">
      {s("信息框：浅底 + 1px 边框 + 8px 圆角 + 12px 16px 内边距。结构与摸鱼绿一致。")}
    </p>
  </section>
</section>'''
    )

    # === 7. 第三章 ===
    html_parts.append(
        f'''<section style="margin-top:48px;margin-bottom:32px;padding:0 20px;">
  <section style="display:flex;align-items:center;gap:16px;margin-bottom:24px;">
    <section style="text-align:center;flex-shrink:0;">
      <p style="margin:0;font-size:28px;font-weight:900;color:{p};line-height:1;letter-spacing:-2px;">
        <span leaf="">03</span>
      </p>
      <p style="margin:0;font-size:8px;font-weight:700;color:{t['divider']};letter-spacing:2px;">
        <span leaf="">PART</span>
      </p>
    </section>
    <span style="width:1px;height:36px;background:{t['border_gray']};flex-shrink:0;"><span leaf=""><br></span></span>
    <section>
      <p style="margin:0 0 1px;font-size:17px;font-weight:900;color:{t['title_color']};letter-spacing:0.3px;">
        <span leaf=">布局组件</span>
      </p>
      <p style="margin:0;font-size:11px;font-weight:600;color:{t['aux_text']};letter-spacing:1.5px;">
        <span leaf="">LAYOUT COMPONENTS</span>
      </p>
    </section>
  </section>

  <!-- timeline -->
  <section style="display:flex;margin-bottom:28px;">
    <section style="display:flex;flex-direction:column;align-items:center;margin-right:16px;flex-shrink:0;">
      <section style="width:14px;height:14px;border-radius:50%;border:3px solid {p};background:#fff;margin-top:4px;box-shadow:0 0 0 2px #fff;">
        <span leaf=""><br></span>
      </section>
      <section style="width:2px;background:{t['border_gray']};flex:1;margin-top:4px;min-height:48px;">
        <span leaf=""><br></span>
      </section>
    </section>
    <section style="flex:1;padding-bottom:12px;">
      <section style="display:flex;align-items:center;gap:8px;margin-bottom:10px;flex-wrap:wrap;">
        <span style="display:inline-block;background:{t['dark_label_bg']};color:#fff;font-size:10px;font-weight:700;padding:2px 8px;border-radius:12px;"><span leaf="">CASE 01</span></span>
        <h4 style="font-size:15px;font-weight:800;color:{t['title_color']};margin:0;">
          <span leaf="">时间线节点一</span>
        </h4>
      </section>
      <p style="font-size:11px;font-weight:600;color:{t['aux_text']};letter-spacing:1px;margin:0 0 12px;">
        <span leaf="">TIMELINE NODE ONE</span>
      </p>
      <p style="font-size:14px;margin:0 0 16px;color:{t['secondary_text']};line-height:1.7;text-align:justify;">
        {s("时间线圆点 14px，竖线 2px，间距与摸鱼绿一致。")}
      </p>
    </section>
  </section>

  <!-- table -->
  <section style="margin-bottom:24px;overflow-x:auto;">
    <table style="width:100%;border-collapse:collapse;font-size:13px;">
      <thead>
        <tr>
          <th style="background:{p};color:#fff;font-weight:700;padding:8px 12px;text-align:left;"><span leaf="">属性</span></th>
          <th style="background:{p};color:#fff;font-weight:700;padding:8px 12px;text-align:left;"><span leaf="">摸鱼绿</span></th>
          <th style="background:{p};color:#fff;font-weight:700;padding:8px 12px;text-align:left;"><span leaf="">锤子</span></th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td style="padding:8px 12px;border-bottom:1px solid {t['border_gray']};color:{t['body_color']};"><span leaf="">字号</span></td>
          <td style="padding:8px 12px;border-bottom:1px solid {t['border_gray']};color:{t['body_color']};"><span leaf="">14px</span></td>
          <td style="padding:8px 12px;border-bottom:1px solid {t['border_gray']};color:{t['body_color']};"><span leaf="">14px</span></td>
        </tr>
        <tr>
          <td style="padding:8px 12px;border-bottom:1px solid {t['border_gray']};color:{t['body_color']};background:{t['bg_extreme_light']};"><span leaf="">行高</span></td>
          <td style="padding:8px 12px;border-bottom:1px solid {t['border_gray']};color:{t['body_color']};background:{t['bg_extreme_light']};"><span leaf="">1.9</span></td>
          <td style="padding:8px 12px;border-bottom:1px solid {t['border_gray']};color:{t['body_color']};background:{t['bg_extreme_light']};"><span leaf="">1.9</span></td>
        </tr>
        <tr>
          <td style="padding:8px 12px;border-bottom:1px solid {t['border_gray']};color:{t['body_color']};"><span leaf="">圆角</span></td>
          <td style="padding:8px 12px;border-bottom:1px solid {t['border_gray']};color:{t['body_color']};"><span leaf="">12px</span></td>
          <td style="padding:8px 12px;border-bottom:1px solid {t['border_gray']};color:{t['body_color']};"><span leaf="">12px</span></td>
        </tr>
      </tbody>
    </table>
  </section>
</section>'''
    )

    # === 8. 第四章（高级组件）===
    html_parts.append(
        f'''<section style="margin-top:48px;margin-bottom:32px;padding:0 20px;">
  <section style="display:flex;align-items:center;gap:16px;margin-bottom:24px;">
    <section style="text-align:center;flex-shrink:0;">
      <p style="margin:0;font-size:28px;font-weight:900;color:{p};line-height:1;letter-spacing:-2px;">
        <span leaf="">04</span>
      </p>
      <p style="margin:0;font-size:8px;font-weight:700;color:{t['divider']};letter-spacing:2px;">
        <span leaf="">PART</span>
      </p>
    </section>
    <span style="width:1px;height:36px;background:{t['border_gray']};flex-shrink:0;"><span leaf=""><br></span></span>
    <section>
      <p style="margin:0 0 1px;font-size:17px;font-weight:900;color:{t['title_color']};letter-spacing:0.3px;">
        <span leaf="">高级组件示例</span>
      </p>
      <p style="margin:0;font-size:11px;font-weight:600;color:{t['aux_text']};letter-spacing:1.5px;">
        <span leaf="">ADVANCED COMPONENTS</span>
      </p>
    </section>
  </section>
  <p style="margin-bottom:16px;font-size:14px;line-height:1.9;text-align:justify;">
    {s("以下展示 5 个高级组件，均统一到当前主题设计语言。")}
  </p>

  <!-- 高级组件 1: alert -->
  <section style="margin:0 0 24px;background:{t['yellow_bg']};border-radius:0 12px 12px 0;border-left:4px solid {t['yellow_highlight']};padding:16px 20px;">
    <p style="margin:0 0 6px;"><span style="display:inline-block;background:{t['yellow_highlight']};color:{t['bg_lightest_green']};font-size:11px;font-weight:700;padding:2px 10px;border-radius:4px;letter-spacing:1px;"><span leaf="">WARNING</span></span></p>
    <p style="margin:0 0 8px;font-size:15px;font-weight:700;color:{t['yellow_text']};line-height:1.5;"><span leaf="">风险提示</span></p>
    <p style="margin:0;font-size:14px;color:{t['yellow_text']};line-height:1.8;">{s("此版本在 430px 视口下可能存在横向溢出风险。")}</p>
  </section>

  <!-- 高级组件 2: facts -->
  <section style="margin:0 0 24px;background:{t['bg_light_green']};border-radius:12px;border:1px solid {t['border_light']};padding:16px 20px;">
    <p style="margin:0 0 12px;font-size:15px;font-weight:700;color:{t['title_color']};">{s("参数信息")}</p>
    <section style="display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid {t['border_gray']};">
      <span style="font-size:13px;color:{t['aux_text']};">{s("主题")}</span>
      <span style="font-size:13px;font-weight:600;color:{t['title_color']};">{s(t["name"])}</span>
    </section>
    <section style="display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid {t['border_gray']};">
      <span style="font-size:13px;color:{t['aux_text']};">{s("主色")}</span>
      <span style="font-size:13px;font-weight:600;color:{p};">{s(p)}</span>
    </section>
    <section style="display:flex;justify-content:space-between;padding:6px 0;">
      <span style="font-size:13px;color:{t['aux_text']};">{s("圆角")}</span>
      <span style="font-size:13px;font-weight:600;color:{t['title_color']};">{s("12px")}</span>
    </section>
  </section>

  <!-- 高级组件 3: steps -->
  <section style="margin:0 0 24px;background:{t['bg_extreme_light']};border-radius:12px;border:1px solid {t['border_gray']};padding:16px 20px;">
    <p style="margin:0 0 12px;font-size:15px;font-weight:700;color:{t['title_color']};">{s("部署步骤")}</p>
    <section style="display:flex;align-items:flex-start;gap:10px;margin-bottom:10px;">
      <span style="display:inline-flex;align-items:center;justify-content:center;width:20px;height:20px;background:{p};color:#fff;font-size:11px;font-weight:700;border-radius:50%;flex-shrink:0;"><span leaf="">1</span></span>
      <p style="font-size:14px;color:{t['body_color']};margin:0;line-height:1.8;flex:1;">{s("读取主题 Markdown 文件")}</p>
    </section>
    <section style="display:flex;align-items:flex-start;gap:10px;margin-bottom:10px;">
      <span style="display:inline-flex;align-items:center;justify-content:center;width:20px;height:20px;background:{p};color:#fff;font-size:11px;font-weight:700;border-radius:50%;flex-shrink:0;"><span leaf="">2</span></span>
      <p style="font-size:14px;color:{t['body_color']};margin:0;line-height:1.8;flex:1;">{s("提取组件 HTML 代码块")}</p>
    </section>
    <section style="display:flex;align-items:flex-start;gap:10px;">
      <span style="display:inline-flex;align-items:center;justify-content:center;width:20px;height:20px;background:{p};color:#fff;font-size:11px;font-weight:700;border-radius:50%;flex-shrink:0;"><span leaf="">3</span></span>
      <p style="font-size:14px;color:{t['body_color']};margin:0;line-height:1.8;flex:1;">{s("对比结构属性")}</p>
    </section>
  </section>

  <!-- 高级组件 4: checklist -->
  <section style="margin:0 0 24px;background:{t['bg_light_green']};border-radius:12px;border:1px solid {t['border_light']};padding:16px 20px;">
    <p style="margin:0 0 12px;font-size:15px;font-weight:700;color:{t['title_color']};">{s("发布前检查")}</p>
    <section style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">
      <span style="display:inline-flex;align-items:center;justify-content:center;width:18px;height:18px;background:{p};color:#fff;border-radius:4px;font-size:11px;font-weight:700;"><span leaf="">✓</span></span>
      <span style="font-size:14px;color:{t['body_color']};">{s("13 个组件结构一致")}</span>
    </section>
    <section style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">
      <span style="display:inline-flex;align-items:center;justify-content:center;width:18px;height:18px;background:{p};color:#fff;border-radius:4px;font-size:11px;font-weight:700;"><span leaf="">✓</span></span>
      <span style="font-size:14px;color:{t['body_color']};">{s("无摸鱼绿色值残留")}</span>
    </section>
    <section style="display:flex;align-items:center;gap:8px;">
      <span style="display:inline-flex;align-items:center;justify-content:center;width:18px;height:18px;background:{t['border_gray']};color:{t['aux_text']};border-radius:4px;font-size:11px;font-weight:700;"><span leaf="">○</span></span>
      <span style="font-size:14px;color:{t['aux_text']};">{s("430px 无溢出")}</span>
    </section>
  </section>

  <!-- 高级组件 5: dialogue -->
  <section style="margin:0 0 24px;background:{t['bg_extreme_light']};border-radius:12px;padding:16px 20px;">
    <p style="margin:0 0 12px;font-size:15px;font-weight:700;color:{t['title_color']};">{s("对话示例")}</p>
    <section style="margin-bottom:12px;">
      <span style="display:inline-block;background:{t['lightest_decor']};color:{t['dark']};font-size:12px;font-weight:700;padding:3px 10px;border-radius:12px;margin-bottom:6px;"><span leaf="">用户</span></span>
      <p style="font-size:14px;color:{t['body_color']};margin:0;line-height:1.8;">{s("锤子主题结构是否与摸鱼绿一致？")}</p>
    </section>
    <section>
      <span style="display:inline-block;background:{t['bg_light_green']};color:{p};font-size:12px;font-weight:700;padding:3px 10px;border-radius:12px;margin-bottom:6px;"><span leaf="">助手</span></span>
      <p style="font-size:14px;color:{t['body_color']};margin:0;line-height:1.8;">{s("是的，13 个组件结构完全同构，仅颜色不同。")}</p>
    </section>
  </section>
</section>'''
    )

    # === 9. 结语章 ===
    html_parts.append(
        f'''<section style="margin-top:48px;margin-bottom:32px;padding:0 20px;">
  <section style="display:flex;align-items:center;gap:16px;margin-bottom:24px;">
    <section style="text-align:center;flex-shrink:0;">
      <p style="margin:0;font-size:28px;font-weight:900;color:{p};line-height:1;letter-spacing:-2px;">
        <span leaf="">///</span>
      </p>
      <p style="margin:0;font-size:8px;font-weight:700;color:{t['divider']};letter-spacing:2px;">
        <span leaf="">LAST</span>
      </p>
    </section>
    <span style="width:1px;height:36px;background:{t['border_gray']};flex-shrink:0;"><span leaf=""><br></span></span>
    <section>
      <p style="margin:0 0 1px;font-size:17px;font-weight:900;color:{t['title_color']};letter-spacing:0.3px;">
        <span leaf="">写在最后</span>
      </p>
      <p style="margin:0;font-size:11px;font-weight:600;color:{t['aux_text']};letter-spacing:1.5px;">
        <span leaf="">CONCLUSION</span>
      </p>
    </section>
  </section>
  <p style="font-size:14px;margin-bottom:20px;text-align:center;color:{p};font-weight:700;letter-spacing:1px;border-top:1px solid {t['bg_lightest_green']};border-bottom:1px solid {t['bg_lightest_green']};padding:12px 0;">
    <span leaf="">结构同构，只换肤色</span>
  </p>
</section>'''
    )

    # === 固定结尾署名组件 ===
    html_parts.append(
        f'''<section style="margin:0 20px 24px;padding:16px 20px;background:{t['lightest_decor']};border-left:3px solid {p};border-radius:0 8px 8px 0;">
  <p style="margin:0 0 4px;font-size:14px;font-weight:600;color:{t['dark']};line-height:1.7;">
    <span leaf="">作者：给自己造把锤子</span>
  </p>
  <p style="margin:0;font-size:13px;color:{t['aux_text']};line-height:1.7;">
    <span leaf="">邮箱：cd.hyxc.jz@foxmail.com</span>
  </p>
</section>'''
    )

    # === footer-cta ===
    html_parts.append(
        f'''<section style="background:radial-gradient(circle at center,{t['bg_extreme_light']} 0%,#FFFFFF 100%);border:1px solid {t['border_gray']};border-radius:16px;padding:32px 20px;text-align:center;box-shadow:0 4px 12px rgba(0,0,0,0.03);margin:0 20px 24px;">
  <p style="font-size:13px;font-weight:bold;color:{t['title_color']};margin-bottom:20px;line-height:1.6;">
    <span leaf="">既然看到这里了，如果觉得有用，随手点个赞、在看、转发三连吧。</span>
  </p>
  <section style="display:flex;justify-content:center;gap:24px;margin-bottom:16px;">
    <section style="text-align:center;cursor:pointer;color:{t['secondary_text']};">
      <section style="width:40px;height:40px;display:flex;align-items:center;justify-content:center;margin:0 auto 6px;background:#fff;border-radius:12px;box-shadow:0 2px 4px rgba(0,0,0,0.05);border:1px solid {t['bg_lightest_green']};">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"></path></svg>
      </section>
      <span style="font-size:10px;font-weight:600;"><span leaf="">点赞</span></span>
    </section>
    <section style="text-align:center;cursor:pointer;color:{t['secondary_text']};">
      <section style="width:40px;height:40px;display:flex;align-items:center;justify-content:center;margin:0 auto 6px;background:#fff;border-radius:12px;box-shadow:0 2px 4px rgba(0,0,0,0.05);border:1px solid {t['bg_lightest_green']};">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="12" r="3"></circle><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path></svg>
      </section>
      <span style="font-size:10px;font-weight:600;"><span leaf="">在看</span></span>
    </section>
    <section style="text-align:center;cursor:pointer;color:{p};">
      <section style="width:40px;height:40px;display:flex;align-items:center;justify-content:center;margin:0 auto 6px;background:{t['bg_light_green']};border-radius:12px;box-shadow:0 2px 4px {t['rgba_primary_015_shadow']};border:1px solid {t['lightest_decor']};">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 18v-4a8 8 0 0 1 8-8h8"></path><polyline points="16 2 20 6 16 10"></polyline></svg>
      </section>
      <span style="font-size:10px;font-weight:600;"><span leaf="">转发</span></span>
    </section>
  </section>
  <p style="font-size:10px;color:{t['aux_text']};letter-spacing:1px;margin:0;">
    <span leaf="">THANKS FOR READING</span>
  </p>
</section>'''
    )

    html_parts.append("</section>")
    return "\n".join(html_parts)


# ── Reusable article-level official component builders (dev2-hotfix1) ─────────
# These expose the SAME official hammer components used by generate_article()
# above, parameterized so scripts/render_article.py can typeset an ARBITRARY
# article with the OFFICIAL components — no hand-written hammer HTML anywhere
# downstream. generate_article() is intentionally left untouched (its sample
# output stays byte-identical); these builders are the single reusable surface.

def hammer_container(theme_key, inner):
    t = PALETTES[theme_key]
    return (f'<section style="max-width:677px;margin:0 auto;background:#ffffff;'
            f"font-family:-apple-system,BlinkMacSystemFont,'PingFang SC','Hiragino Sans GB',"
            f"'Microsoft YaHei',sans-serif;color:{t['body_color']};"
            f'line-height:1.75;letter-spacing:0.5px;overflow-x:hidden;">\n'
            + inner + '\n</section>')


def hammer_cover(theme_key, kicker, strike, title_line1, title_line2, subtitle,
                 date="2026.07", brand="给自己造把锤子", tags=("深度", "观察")):
    t = PALETTES[theme_key]; p = t["primary"]
    # 76T/OBS-293:划线句槽——strike(即 strike_assumption)为空时整行不渲染,
    # 不再用 hook_line/默认文案填充(消灭语义冲突)。
    strike_html = (
        f'<p style="font-size:15px;color:{t["strike_text"]};margin:0 0 6px;text-decoration:line-through;'
        f'text-decoration-color:{t["strike_text"]};text-decoration-thickness:1px;letter-spacing:0.5px;'
        f'white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">'
        f'<span leaf="">{strike}</span></p>'
        if strike else ''
    )
    tag_html = "".join(
        f'<span style="background:rgba(255,255,255,0.2);padding:1px 6px;border-radius:3px;'
        f'font-size:8px;color:#fff;font-weight:600;"><span leaf="">{tg}</span></span>' for tg in tags)
    return f'''<section style="margin:0 0 32px;background:#fff;border:1.5px solid {t['rgba_primary_015']};border-radius:20px;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,0.06);width:100%;">
  <section style="padding:32px 28px 28px;">
    <section style="display:flex;align-items:center;gap:8px;margin-bottom:28px;">
      <span style="width:6px;height:6px;background:{p};border-radius:50%;"><span leaf=""><br></span></span>
      <span style="font-size:11px;font-weight:700;letter-spacing:3px;color:{p};"><span leaf="">{kicker}</span></span>
      <section style="flex:1;height:1px;overflow:hidden;background:linear-gradient(to right,{t['rgba_primary_012']},transparent);"><span leaf=""><br></span></section>
      <span style="font-size:10px;color:{t['divider']};font-weight:600;"><span leaf="">{date}</span></span>
    </section>
    <section>
      {strike_html}
      <p style="font-size:24px;font-weight:900;color:{t['title_color']};margin:0;line-height:1.05;letter-spacing:-2px;">
        <span leaf="">{title_line1}</span>
      </p>
      <p style="font-size:24px;font-weight:900;color:{p};margin:0 0 16px;line-height:1.05;letter-spacing:-2px;">
        <span leaf="">{title_line2}</span>
      </p>
      <section style="width:48px;height:3px;background:linear-gradient(to right,{p},{t['light_decor']});border-radius:2px;margin-bottom:12px;">
        <span leaf=""><br></span>
      </section>
      <p style="font-size:13px;color:{t['aux_text']};margin:0;line-height:1.7;letter-spacing:0.5px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">
        <span leaf="">{subtitle}</span>
      </p>
    </section>
  </section>
  <section style="background:linear-gradient(135deg,{p},{t['secondary']});padding:12px 28px;display:flex;align-items:center;justify-content:space-between;">
    <p style="font-size:12px;color:rgba(255,255,255,0.9);margin:0;font-weight:600;letter-spacing:0.5px;">
      <span leaf="">{brand}</span>
    </p>
    <section style="display:flex;gap:4px;">
      {tag_html}
    </section>
  </section>
</section>'''


def _toc_card(t, part_label, title, subtitle, highlight):
    p = t["primary"]
    if highlight:
        return f'''<section style="display:inline-block;white-space:normal;vertical-align:top;width:110px;background:linear-gradient(135deg,{p},{t['secondary']});border-radius:12px;padding:12px;margin-right:8px;">
      <p style="font-size:9px;font-weight:700;color:rgba(255,255,255,0.7);letter-spacing:1px;margin:0 0 5px;"><span leaf="">{part_label}</span></p>
      <p style="font-size:13px;font-weight:800;color:#fff;margin:0 0 3px;"><span leaf="">{title}</span></p>
      <p style="font-size:10px;color:rgba(255,255,255,0.7);margin:0;"><span leaf="">{subtitle}</span></p>
    </section>'''
    return f'''<section style="display:inline-block;white-space:normal;vertical-align:top;width:110px;background:#fff;border:1px solid {t['border_gray']};border-radius:12px;padding:12px;margin-right:8px;box-shadow:0 2px 6px rgba(0,0,0,0.04);">
      <p style="font-size:9px;font-weight:700;color:{t['aux_text']};letter-spacing:1px;margin:0 0 5px;"><span leaf="">{part_label}</span></p>
      <p style="font-size:13px;font-weight:800;color:{t['title_color']};margin:0 0 3px;"><span leaf="">{title}</span></p>
      <p style="font-size:10px;color:{t['aux_text']};margin:0;"><span leaf="">{subtitle}</span></p>
    </section>'''


def hammer_toc(theme_key, chapter_titles):
    """Horizontal scroll TOC. One card per chapter (PART 01..0N) + a PART /// card."""
    t = PALETTES[theme_key]
    n = len(chapter_titles)
    cards = []
    for i, title in enumerate(chapter_titles, 1):
        cards.append(_toc_card(t, f"PART {i:02d}", title, "", highlight=(i == 1)))
    cards.append(_toc_card(t, "PART ///", "写在最后", "署名与 CTA", highlight=False))
    return f'''<section style="margin:0 20px 32px;">
  <section style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px;">
    <p style="font-size:10px;color:{t['aux_text']};margin:0;text-transform:uppercase;letter-spacing:2px;font-weight:600;"><span leaf="">📦 {n} Parts + Conclusion</span></p>
    <p style="font-size:10px;color:{t['aux_text']};margin:0;"><span leaf="">👉 滑动</span></p>
  </section>
  <section style="overflow-x:scroll;-webkit-overflow-scrolling:touch;white-space:nowrap;padding-bottom:8px;">
    {''.join(cards)}
  </section>
</section>'''


def hammer_oneliner(theme_key, text):
    t = PALETTES[theme_key]; p = t["primary"]
    return f'''<section style="background:#FFF;border:1px dashed {t['border_light']};border-radius:8px;padding:14px 16px;margin:0 20px 24px;text-align:center;">
  <p style="margin:0;line-height:1.6;">
    <span style="font-size:15px;color:{p};font-weight:bold;border-bottom:3px solid {t['yellow_highlight']};padding-bottom:2px;"><span leaf="">{text}</span></span>
  </p>
</section>'''


def hammer_chapter(theme_key, num, title, en_label):
    t = PALETTES[theme_key]; p = t["primary"]
    return f'''<section style="margin-top:48px;margin-bottom:32px;padding:0 20px;">
  <section style="display:flex;align-items:center;gap:16px;margin-bottom:24px;">
    <section style="text-align:center;flex-shrink:0;">
      <p style="margin:0;font-size:28px;font-weight:900;color:{p};line-height:1;letter-spacing:-2px;"><span leaf="">{num}</span></p>
      <p style="margin:0;font-size:8px;font-weight:700;color:{t['divider']};letter-spacing:2px;"><span leaf="">PART</span></p>
    </section>
    <span style="width:1px;height:36px;background:{t['border_gray']};flex-shrink:0;"><span leaf=""><br></span></span>
    <section>
      <p style="margin:0 0 1px;font-size:17px;font-weight:900;color:{t['title_color']};letter-spacing:0.3px;"><span leaf="">{title}</span></p>
      <p style="margin:0;font-size:11px;font-weight:600;color:{t['aux_text']};letter-spacing:1.5px;"><span leaf="">{en_label}</span></p>
    </section>
  </section>
</section>'''


def hammer_para(theme_key, text):
    return (f'<section style="margin:0 20px;">'
            f'<p style="margin-bottom:16px;font-size:14px;line-height:1.9;text-align:justify;color:{PALETTES[theme_key]["body_color"]};">'
            f'{s(text)}</p></section>')


def hammer_table(theme_key, header, rows):
    """76J/OBS-271:Markdown 表格 -> 官方 11f 表格样式(references/theme-hammer.md 11f)。

    结构与 theme-hammer.md 11f 逐字一致:外层 section overflow-x:auto;table
    width:100%;border-collapse:collapse;font-size:13px;th 背景 primary 白字;td
    border-bottom border_gray + 偶数行 bg_extreme_light 斑马。单元格文本用
    <p style="margin:0;font-size:13px;line-height:1.6;color:{...}"> 承载(微信
    支持 td>p,视觉与 11f 的 span 直挂一致;该 p 样式即语法门锚可测样式,由
    component_anchors.json 注册)。"""
    t = PALETTES[theme_key]
    p = t["primary"]
    bg = t["border_gray"]
    bc = t["body_color"]
    zebra_bg = t["bg_extreme_light"]
    cells = []
    if header:
        cells.append('    <tr>' + ''.join(
            f'<th style="background:{p};color:#fff;font-weight:700;padding:8px 12px;'
            f'text-align:left;"><p style="margin:0;font-size:13px;line-height:1.6;'
            f'color:#fff;"><span leaf="">{s(c)}</span></p></th>' for c in header)
            + '</tr>')
    for i, row in enumerate(rows):
        zebra = f"background:{zebra_bg};" if i % 2 == 0 else ""
        cells.append('    <tr>' + ''.join(
            f'<td style="padding:8px 12px;border-bottom:1px solid {bg};'
            f'color:{bc};{zebra}">'
            f'<p style="margin:0;font-size:13px;line-height:1.6;'
            f'color:{bc};">'
            f'<span leaf="">{s(c)}</span></p></td>' for c in row)
            + '</tr>')
    thead_html = "\n".join(cells[:1]) if header else ""
    tbody_html = "\n".join(cells[1:])
    return (f'<section style="margin-bottom:24px;overflow-x:auto;">'
            f'<table style="width:100%;border-collapse:collapse;font-size:13px;">'
            f'<thead>{thead_html}</thead>'
            f'<tbody>{tbody_html}</tbody></table></section>')


def hammer_list(theme_key, items, ordered=False):
    """76J/OBS-271:Markdown 列表 -> 官方主题样式——无序 = 11a pill-list 基本版,
    有序 = 11g ordered-list(references/theme-hammer.md 11a/11g)。

    无序项 p 在 11a 的 margin:0 0 6px 基础上补 font-size/line-height/color(视觉
    由 pill span 自身样式决定,补位仅为语法门锚可测样式);有序项 p 与 11g 逐字
    一致(唯一差异=颜色走主题 token)。"""
    t = PALETTES[theme_key]; p = t["primary"]
    parts = []
    if ordered:
        for i, item in enumerate(items, 1):
            parts.append(
                f'<section style="display:flex;align-items:flex-start;gap:10px;margin-bottom:12px;">'
                f'<span style="display:inline-flex;align-items:center;justify-content:center;width:22px;'
                f'height:22px;background:{p};color:#fff;font-size:11px;font-weight:700;'
                f'border-radius:50%;flex-shrink:0;margin-top:2px;"><span leaf="">{i}</span></span>'
                f'<p style="font-size:14px;color:{t["body_color"]};margin:0;line-height:1.9;flex:1;">'
                f'<span leaf="">{s(item)}</span></p></section>')
    else:
        for item in items:
            parts.append(
                f'<section style="margin-bottom:14px;">'
                f'<p style="margin:0 0 6px;font-size:13px;line-height:1.6;color:{t["body_color"]};">'
                f'<span style="display:inline-block;font-size:13px;font-weight:700;color:{p};'
                f'background:{t["rgba_primary_008"]};padding:3px 10px;border-radius:999px;">'
                f'<span style="display:inline-block;width:6px;height:6px;background:{p};border-radius:50%;'
                f'margin-right:5px;vertical-align:middle;"><span leaf=""><br></span></span>'
                f'<span leaf="">{s(item)}</span></span></p></section>')
    return "\n".join(parts)


def hammer_code_block(language: str, text: str) -> str:
    """1a 深色代码块(common-components.md)——所有主题共用,不做主题变色。

    逐字对应 references/common-components.md「1a. 深色代码块(默认)」:
    外层 background:#1E293B + border-radius:8px + overflow:hidden + box-shadow;
    顶栏 background:#0F172A + display:flex,三色圆点
    #FF5F56/#FFBD2E/#27C93F(10px 圆,font-size:0 隐藏占位字符);
    语言标签 color:#64748B、Consolas 等宽、letter-spacing:1px(无语言则删该 span);
    代码行每行一个 <p style="margin:0;font-family:'SF Mono',…;color:#E2E8F0;">。
    缩进:行首前导空白转全角空格 U+3000(规范③);行内空格一字不动(规范⑤)。
    """
    lines = (text or "").splitlines()
    body = []
    for line in lines:
        escaped = (line.replace("&", "&amp;").replace("<", "&lt;")
                   .replace(">", "&gt;"))
        stripped = escaped.lstrip(" \t")
        leading = escaped[: len(escaped) - len(stripped)]
        leading_fw = "".join("\u3000" if c in (" ", "\t") else c for c in leading)
        safe = leading_fw + stripped
        body.append(
            '<p style="margin:0;font-family:\'SF Mono\',Consolas,Monaco,monospace;'
            'font-size:13px;line-height:1.6;color:#E2E8F0;"><span leaf="">'
            + safe + '</span></p>')
    lang_span = ""
    if language:
        lang = (language.replace("&", "&amp;").replace("<", "&lt;")
                .replace(">", "&gt;"))
        lang_span = ('<span style="margin-left:12px;font-size:12px;color:#64748B;'
                     'font-family:Consolas,Monaco,monospace;letter-spacing:1px;">'
                     '<span leaf="">' + lang + '</span></span>')
    return (f'<section style="margin:0 0 20px;border-radius:8px;overflow:hidden;'
            f'background:#1E293B;box-shadow:0 4px 16px -8px rgba(15,23,42,0.4);">'
            f'<section style="display:flex;align-items:center;padding:9px 14px;background:#0F172A;">'
            f'<span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:#FF5F56;margin-right:7px;font-size:0;line-height:0;overflow:hidden;">.</span>'
            f'<span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:#FFBD2E;margin-right:7px;font-size:0;line-height:0;overflow:hidden;">.</span>'
            f'<span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:#27C93F;font-size:0;line-height:0;overflow:hidden;">.</span>'
            + lang_span
            + '</section>'
            + '<section style="padding:11px 14px;">' + "".join(body) + '</section>'
            + '</section>')


def hammer_image_2a(theme_key, url, caption=""):
    """Official common-components 2a standard image, hammer-toned."""
    t = PALETTES[theme_key]
    cap = (f'<p style="font-size:12px;color:{t["aux_text"]};text-align:center;margin:0 0 24px;">'
           f'<span leaf="">— {caption}</span></p>') if caption else ""
    return f'''<section style="background:#FFF;border-radius:12px;padding:6px;border:1px solid {t['border_gray']};box-shadow:0 4px 12px -2px rgba(0,0,0,0.08);margin-bottom:8px;">
  <section style="margin:0;border-radius:8px;overflow:hidden;">
    <span leaf=""><img src="{url}" style="max-width:100%;height:auto;display:block;margin:0 auto;"></span>
  </section>
</section>
{cap}'''


def hammer_media_text(theme_key, url, caption, exp):
    """Official media+text card, hammer-toned (image_media_text fingerprint)."""
    t = PALETTES[theme_key]
    return f'''<section style="margin:0 0 8px;background:{t['bg_lightest_green']};border-radius:12px;padding:6px;border:1px solid {t['border_gray']};box-shadow:0 4px 16px -4px {t['rgba_primary_010_shadow']};">
  <section style="margin:0;border-radius:12px;overflow:hidden;"><span leaf=""><img src="{url}" style="max-width:100%;height:auto;display:block;margin:0 auto;"></span></section>
</section>
<p style="margin:0 0 8px;font-size:12px;color:{t['aux_text']};text-align:center;"><span leaf="">{caption}</span></p>
<p style="margin:0 0 24px;font-size:14px;color:{t['body_color']};line-height:1.8;"><span leaf="">{exp}</span></p>'''


def hammer_fixed_signature(theme_key):
    """Official fixed end-signature (common-components §4a), hammer color mapping.
    文案 is authoritative and verbatim; brand-sentence color #8A4530 for contrast."""
    t = PALETTES[theme_key]; p = t["primary"]
    return f'''<section style="padding:0 20px 24px;">
  <p style="margin:0 0 16px;font-size:15px;line-height:1.8;color:{t['body_color']};">
    <span leaf="">好了，今天就先聊到这儿。</span>
  </p>
  <section style="margin:0 0 16px;padding:10px 14px;border-left:3px solid {p};background:{t['lightest_decor']};border-radius:0 6px 6px 0;">
    <p style="margin:0;font-size:14px;line-height:1.8;color:{t['dark']};font-weight:600;">
      <span leaf="">热闹是 AI 的，淡定可以是我们的。</span>
    </p>
    <p style="margin:8px 0 0;font-size:14px;line-height:1.8;color:{t['dark']};font-weight:600;">
      <span leaf="">用克制的语言讲清楚AI前沿正在发生的事。</span>
    </p>
  </section>
  <p style="margin:0 0 4px;font-size:12px;line-height:1.7;color:{t['aux_text']};">
    <span leaf="">/ 作者 给自己造把锤子</span>
  </p>
  <p style="margin:0;font-size:12px;line-height:1.7;color:{t['aux_text']};">
    <span leaf="">/ 投稿或反馈，请联系邮箱：cd.hyxc.jz@foxmail.com</span>
  </p>
</section>'''


def hammer_footer_cta(theme_key):
    """Official footer-cta (like/watch/share + THANKS FOR READING)."""
    t = PALETTES[theme_key]; p = t["primary"]
    return f'''<section style="background:radial-gradient(circle at center,{t['bg_extreme_light']} 0%,#FFFFFF 100%);border:1px solid {t['border_gray']};border-radius:16px;padding:32px 20px;text-align:center;box-shadow:0 4px 12px rgba(0,0,0,0.03);margin:0 20px 24px;">
  <p style="font-size:13px;font-weight:bold;color:{t['title_color']};margin-bottom:20px;line-height:1.6;">
    <span leaf="">既然看到这里了，如果觉得有用，随手点个赞、在看、转发三连吧。</span>
  </p>
  <section style="display:flex;justify-content:center;gap:24px;margin-bottom:16px;">
    <section style="text-align:center;cursor:pointer;color:{t['secondary_text']};">
      <section style="width:40px;height:40px;display:flex;align-items:center;justify-content:center;margin:0 auto 6px;background:#fff;border-radius:12px;box-shadow:0 2px 4px rgba(0,0,0,0.05);border:1px solid {t['bg_lightest_green']};">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"></path></svg>
      </section>
      <span style="font-size:10px;font-weight:600;"><span leaf="">点赞</span></span>
    </section>
    <section style="text-align:center;cursor:pointer;color:{t['secondary_text']};">
      <section style="width:40px;height:40px;display:flex;align-items:center;justify-content:center;margin:0 auto 6px;background:#fff;border-radius:12px;box-shadow:0 2px 4px rgba(0,0,0,0.05);border:1px solid {t['bg_lightest_green']};">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="12" r="3"></circle><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path></svg>
      </section>
      <span style="font-size:10px;font-weight:600;"><span leaf="">在看</span></span>
    </section>
    <section style="text-align:center;cursor:pointer;color:{p};">
      <section style="width:40px;height:40px;display:flex;align-items:center;justify-content:center;margin:0 auto 6px;background:{t['bg_light_green']};border-radius:12px;box-shadow:0 2px 4px {t['rgba_primary_015_shadow']};border:1px solid {t['lightest_decor']};">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 18v-4a8 8 0 0 1 8-8h8"></path><polyline points="16 2 20 6 16 10"></polyline></svg>
      </section>
      <span style="font-size:10px;font-weight:600;"><span leaf="">转发</span></span>
    </section>
  </section>
  <p style="font-size:10px;color:{t['aux_text']};letter-spacing:1px;margin:0;">
    <span leaf="">THANKS FOR READING</span>
  </p>
</section>'''


def wrap_html(body, title):
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=430, initial-scale=1.0">
<title>{title}</title>
</head>
<body style="margin:0;padding:0;background:#f5f5f5;">
{body}
</body>
</html>"""


if __name__ == "__main__":
    for theme_key, filename in [
        ("moyu-green", "reference-moyu-green.html"),
        ("hammer", "target-hammer.html"),
    ]:
        body = generate_article(theme_key)
        html = wrap_html(body, f"{PALETTES[theme_key]['name']} - 结构同构测试")
        outpath = os.path.join(OUT, filename)
        with open(outpath, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"Generated: {outpath} ({len(html)} bytes)")
