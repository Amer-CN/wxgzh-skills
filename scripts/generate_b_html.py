#!/usr/bin/env python3
"""Stage B 高级组件 HTML 生成器

10 个 B 层组件 × 6 主题 = 60 份独立组件 HTML
3 类整篇文章 × 6 主题 = 18 份文章 HTML

所有 HTML 遵守公众号平台限制：
- 只用内联 style
- 所有中文文本用 <span leaf=""> 包裹
- 不用 class/id/div/style/script/grid/float/@media
- compare 在移动端转为纵向对照卡，不用横向表格
- annotated-image 不用 position:absolute，用图片+编号注释清单
- checklist 以视觉状态呈现，不输出原始 - [ ] 文本
"""
import os, sys

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(SKILL, "tests", "advanced-components", "expected")
os.makedirs(OUT, exist_ok=True)

# 导入 Stage 1 的主题配置和辅助函数
sys.path.insert(0, os.path.join(SKILL, "scripts"))
from generate_advanced_html import T, ORDER, s

# ============================================================
# B 层组件生成器
# ============================================================

def facts(tid, title="核心数据", items=None):
    if items is None:
        items = [("月活用户","120 万"),("同比增长","42%"),("数据来源","2026 Q2 财报")]
    t = T[tid]
    rows = ""
    for label, value in items:
        if t["style"] in ("minimal", "zen"):
            rows += f'''<p style="margin:0 0 10px;padding:8px 0;border-bottom:1px solid {t["dv"]};font-size:14px;color:{t["tx"]};line-height:1.7;">
      <span style="font-weight:600;color:{t["st"]};margin-right:8px;">{s(label)}</span>{s(value)}
    </p>\n'''
        else:
            rows += f'''<section style="margin:0 0 8px;padding:10px 14px;background:{t["lb"]};border-radius:{t["r"]};border-left:3px solid {t["p"]};">
      <p style="margin:0;font-size:13px;color:{t["st"]};font-weight:600;">{s(label)}</p>
      <p style="margin:2px 0 0;font-size:15px;color:{t["tc"]};font-weight:700;">{s(value)}</p>
    </section>\n'''
    return f'''<section style="margin:0 0 24px;">
  <p style="margin:0 0 12px;font-size:15px;font-weight:700;color:{t["tc"]};line-height:1.5;">{s(title)}</p>
  {rows.strip()}
</section>'''


def decision(tid, title="技术选型", recommended="Docker 多阶段构建", options=None):
    if options is None:
        options = [("单阶段构建","上手快，但镜像体积大",False),("多阶段构建","构建稍复杂，但运行镜像更小",True)]
    t = T[tid]
    rec_html = ""
    if recommended:
        if t["style"] in ("minimal", "zen"):
            rec_html = f'<p style="margin:0 0 12px;font-size:14px;color:{t["p"]};font-weight:600;">{s("推荐方案：" + recommended)}</p>'
        elif t["style"] == "ticket":
            rec_html = f'<p style="margin:0 0 12px;font-size:14px;color:{t["bd"]};font-weight:800;">{s("推荐：" + recommended)}</p>'
        else:
            rec_html = f'<p style="margin:0 0 12px;font-size:14px;color:{t["p"]};font-weight:700;">{s("推荐方案：" + recommended)}</p>'
    opts = ""
    for name, desc, is_rec in options:
        badge = "推荐" if is_rec else "备选"
        bc = t["p"] if is_rec else t["st"]
        if t["style"] in ("minimal", "zen"):
            opts += f'''<section style="margin:0 0 10px;padding:10px 14px;border-left:2px solid {bc};background:{t["lb"]};">
      <p style="margin:0 0 4px;font-size:11px;font-weight:700;color:{bc};">{s(badge)}</p>
      <p style="margin:0 0 4px;font-size:14px;font-weight:600;color:{t["tc"]};">{s(name)}</p>
      <p style="margin:0;font-size:13px;color:{t["tx"]};line-height:1.7;">{s(desc)}</p>
    </section>\n'''
        else:
            opts += f'''<section style="margin:0 0 10px;padding:10px 14px;border-radius:0 {t["r"]} {t["r"]} 0;border-left:3px solid {bc};background:{t["lb"] if is_rec else t["bg"]};">
      <p style="margin:0 0 4px;font-size:11px;font-weight:700;color:{bc};">{s(badge)}</p>
      <p style="margin:0 0 4px;font-size:14px;font-weight:600;color:{t["tc"]};">{s(name)}</p>
      <p style="margin:0;font-size:13px;color:{t["tx"]};line-height:1.7;">{s(desc)}</p>
    </section>\n'''
    return f'''<section style="margin:0 0 24px;">
  <p style="margin:0 0 12px;font-size:15px;font-weight:700;color:{t["tc"]};line-height:1.5;">{s(title)}</p>
  {rec_html}
  {opts.strip()}
</section>'''


def steps(tid, title="部署流程", items=None):
    if items is None:
        items = ["拉取镜像","配置环境变量","启动容器","验证健康检查"]
    t = T[tid]
    rows = ""
    for i, step in enumerate(items, 1):
        if t["style"] in ("minimal", "zen"):
            rows += f'''<p style="margin:0 0 10px;padding:8px 0;border-bottom:1px solid {t["dv"]};font-size:14px;color:{t["tx"]};line-height:1.7;">
      <span style="font-weight:700;color:{t["p"]};margin-right:8px;">{s(str(i))}</span>{s(step)}
    </p>\n'''
        elif t["style"] == "ticket":
            rows += f'''<section style="margin:0 0 8px;padding:10px 14px;background:{t["lb"]};border:2px solid {t["bd"]};box-shadow:{t["sh"]};">
      <p style="margin:0;font-size:14px;color:{t["tx"]};line-height:1.7;"><span style="font-weight:800;color:{t["bd"]};margin-right:8px;">{s(str(i))}</span>{s(step)}</p>
    </section>\n'''
        else:
            rows += f'''<section style="margin:0 0 8px;padding:10px 14px;background:{t["lb"]};border-radius:0 {t["r"]} {t["r"]} 0;border-left:3px solid {t["p"]};">
      <p style="margin:0;font-size:14px;color:{t["tx"]};line-height:1.7;"><span style="font-weight:700;color:{t["p"]};margin-right:8px;">{s(str(i))}</span>{s(step)}</p>
    </section>\n'''
    return f'''<section style="margin:0 0 24px;">
  <p style="margin:0 0 12px;font-size:15px;font-weight:700;color:{t["tc"]};line-height:1.5;">{s(title)}</p>
  {rows.strip()}
</section>'''


def compare(tid, title="两种方案对比", cols=None, rows=None):
    """移动端安全：转为逐维度纵向对照卡，不用横向表格"""
    if cols is None:
        cols = ["维度", "单阶段构建", "多阶段构建"]
    if rows is None:
        rows = [("镜像体积","大","小"),("构建复杂度","低","中"),("生产适用性","一般","高")]
    t = T[tid]
    cards = ""
    for row in rows:
        dim = row[0]
        vals = row[1:]
        if t["style"] in ("minimal", "zen"):
            vals_html = ""
            for ci, v in enumerate(vals):
                vals_html += f'<span style="margin-right:16px;font-size:13px;color:{t["tx"]};"><span style="font-weight:600;color:{t["st"]};">{s(cols[ci+1])}</span> {s(v)}</span>'
            cards += f'''<p style="margin:0 0 10px;padding:8px 0;border-bottom:1px solid {t["dv"]};font-size:14px;line-height:1.7;">
      <span style="font-weight:600;color:{t["tc"]};margin-right:8px;">{s(dim)}</span>{vals_html}
    </p>\n'''
        else:
            vals_html = ""
            for ci, v in enumerate(vals):
                vals_html += f'<p style="margin:0 0 4px;font-size:13px;color:{t["tx"]};"><span style="font-weight:600;color:{t["st"]};margin-right:4px;">{s(cols[ci+1])}</span>{s(v)}</p>'
            cards += f'''<section style="margin:0 0 8px;padding:10px 14px;background:{t["lb"]};border-radius:{t["r"]};border-left:3px solid {t["p"]};">
      <p style="margin:0 0 6px;font-size:14px;font-weight:700;color:{t["tc"]};">{s(dim)}</p>
      {vals_html}
    </section>\n'''
    return f'''<section style="margin:0 0 24px;">
  <p style="margin:0 0 12px;font-size:15px;font-weight:700;color:{t["tc"]};line-height:1.5;">{s(title)}</p>
  {cards.strip()}
</section>'''


def annotated_image(tid, url="../assets/annotated-dashboard.png", caption="控制台关键区域", notes=None):
    """不用 position:absolute 覆盖层，用图片+下方编号注释清单"""
    if notes is None:
        notes = [("1","左侧导航用于切换工作区"),("2","中央区域显示实时状态"),("3","右上角用于发布和导出")]
    t = T[tid]
    if t["style"] in ("minimal", "zen"):
        img_sec = f'<section style="margin:0 0 10px;"><span leaf=""><img src="{url}" style="max-width:100%;height:auto;display:block;margin:0 auto;"></span></section>'
        cap = f'<p style="margin:0 0 12px;font-size:12px;color:{t["st"]};text-align:center;">{s(caption)}</p>'
        notes_html = ""
        for num, text in notes:
            notes_html += f'<p style="margin:0 0 8px;font-size:13px;color:{t["tx"]};line-height:1.7;"><span style="font-weight:700;color:{t["p"]};margin-right:6px;">{s(num)}</span>{s(text)}</p>'
        notes_sec = f'<section style="padding:12px 0;border-top:1px solid {t["bd"]};">{notes_html.strip()}</section>'
        return f'<section style="margin:0 0 24px;">{img_sec}{cap}{notes_sec}</section>'
    else:
        img_sec = f'<section style="margin:0 0 10px;background:{t["bg"]};border-radius:{t["r"]};padding:6px;border:1px solid {t["bd"]};box-shadow:{t["sh"]};"><span leaf=""><img src="{url}" style="max-width:100%;height:auto;display:block;margin:0 auto;"></span></section>'
        cap = f'<p style="margin:0 0 12px;font-size:12px;color:{t["st"]};text-align:center;">{s(caption)}</p>'
        notes_html = ""
        for num, text in notes:
            notes_html += f'<section style="margin:0 0 6px;padding:8px 12px;background:{t["lb"]};border-radius:{t["r"]};border-left:3px solid {t["p"]};"><p style="margin:0;font-size:13px;color:{t["tx"]};line-height:1.7;"><span style="font-weight:700;color:{t["p"]};margin-right:6px;">{s(num)}</span>{s(text)}</p></section>'
        return f'<section style="margin:0 0 24px;">{img_sec}{cap}{notes_html.strip()}</section>'


def faq(tid, title="常见问题", items=None):
    if items is None:
        items = [("多阶段构建会拖慢 CI 吗？","构建阶段可能略长，但最终镜像更小，拉取与部署通常更快。"),("是否适合所有项目？","不适合极简脚本项目；当运行依赖明显少于构建依赖时更有价值。")]
    t = T[tid]
    qa_html = ""
    for q, a in items:
        if t["style"] in ("minimal", "zen"):
            qa_html += f'''<section style="margin:0 0 14px;padding:12px 14px;border-top:1px solid {t["bd"]};border-bottom:1px solid {t["bd"]};">
      <p style="margin:0 0 6px;font-size:14px;font-weight:700;color:{t["tc"]};line-height:1.6;">{s("Q: " + q)}</p>
      <p style="margin:0;font-size:13px;color:{t["tx"]};line-height:1.8;">{s("A: " + a)}</p>
    </section>\n'''
        else:
            qa_html += f'''<section style="margin:0 0 14px;padding:12px 14px;border-radius:0 {t["r"]} {t["r"]} 0;border-left:3px solid {t["p"]};background:{t["lb"]};">
      <p style="margin:0 0 6px;font-size:14px;font-weight:700;color:{t["tc"]};line-height:1.6;">{s("Q: " + q)}</p>
      <p style="margin:0;font-size:13px;color:{t["tx"]};line-height:1.8;">{s("A: " + a)}</p>
    </section>\n'''
    return f'''<section style="margin:0 0 24px;">
  <p style="margin:0 0 12px;font-size:15px;font-weight:700;color:{t["tc"]};line-height:1.5;">{s(title)}</p>
  {qa_html.strip()}
</section>'''


def timeline(tid, title="项目演进", items=None):
    if items is None:
        items = [("2026-01","完成原型验证"),("2026-03","启动灰度测试"),("2026-06","正式上线")]
    t = T[tid]
    events = ""
    for date, event in items:
        if t["style"] in ("minimal", "zen"):
            events += f'''<section style="margin:0 0 12px;padding:8px 0;border-bottom:1px solid {t["dv"]};">
      <p style="margin:0 0 4px;font-size:12px;font-weight:700;color:{t["p"]};">{s(date)}</p>
      <p style="margin:0;font-size:14px;color:{t["tx"]};line-height:1.7;">{s(event)}</p>
    </section>\n'''
        else:
            events += f'''<section style="margin:0 0 10px;padding:10px 14px;border-radius:0 {t["r"]} {t["r"]} 0;border-left:3px solid {t["p"]};background:{t["lb"]};">
      <p style="margin:0 0 4px;font-size:12px;font-weight:700;color:{t["p"]};">{s(date)}</p>
      <p style="margin:0;font-size:14px;color:{t["tx"]};line-height:1.7;">{s(event)}</p>
    </section>\n'''
    return f'''<section style="margin:0 0 24px;">
  <p style="margin:0 0 12px;font-size:15px;font-weight:700;color:{t["tc"]};line-height:1.5;">{s(title)}</p>
  {events.strip()}
</section>'''


def checklist(tid, title="发布前检查", items=None):
    """以视觉状态呈现，不输出原始 - [ ] 文本"""
    if items is None:
        items = [("完成单元测试",True),("完成灰度验证",True),("准备回滚预案",False),("通知相关负责人",False)]
    t = T[tid]
    rows = ""
    for text, done in items:
        check = "✓" if done else "○"
        if t["style"] in ("minimal", "zen"):
            cc = t["p"] if done else t["st"]
            tc_color = t["tx"] if done else t["st"]
            td = "line-through" if done else "none"
            rows += f'''<p style="margin:0 0 8px;font-size:14px;color:{tc_color};line-height:1.7;text-decoration:{td};">
      <span style="font-weight:700;color:{cc};margin-right:8px;">{s(check)}</span>{s(text)}
    </p>\n'''
        else:
            cc = t["p"] if done else t["st"]
            bg = t["lb"] if done else t["bg"]
            td = "line-through" if done else "none"
            tc_color = t["tx"] if done else t["st"]
            rows += f'''<section style="margin:0 0 6px;padding:8px 12px;background:{bg};border-radius:{t["r"]};border-left:3px solid {cc};">
      <p style="margin:0;font-size:14px;color:{tc_color};line-height:1.7;text-decoration:{td};"><span style="font-weight:700;color:{cc};margin-right:8px;">{s(check)}</span>{s(text)}</p>
    </section>\n'''
    return f'''<section style="margin:0 0 24px;">
  <p style="margin:0 0 12px;font-size:15px;font-weight:700;color:{t["tc"]};line-height:1.5;">{s(title)}</p>
  {rows.strip()}
</section>'''


def case(tid, title="镜像瘦身实践", context=None, challenge=None, action=None, result=None):
    if context is None: context = "一个 Node.js 服务的生产镜像初始体积为 1.2GB。"
    if challenge is None: challenge = "部署慢，安全扫描耗时长。"
    if action is None: action = "改用多阶段构建，并移除开发依赖。"
    if result is None: result = "镜像降至 180MB，部署时间缩短约 60%。"
    t = T[tid]
    labels = [("背景", context),("挑战", challenge),("行动", action),("结果", result)]
    cards = ""
    for label, content in labels:
        bc = t["p"] if label == "结果" else t["st"]
        if t["style"] in ("minimal", "zen"):
            cards += f'''<p style="margin:0 0 10px;padding:8px 0;border-bottom:1px solid {t["dv"]};font-size:14px;color:{t["tx"]};line-height:1.7;">
      <span style="font-weight:700;color:{bc};margin-right:8px;">{s(label)}</span>{s(content)}
    </p>\n'''
        else:
            cards += f'''<section style="margin:0 0 8px;padding:10px 14px;border-radius:0 {t["r"]} {t["r"]} 0;border-left:3px solid {bc};background:{t["lb"]};">
      <p style="margin:0 0 4px;font-size:11px;font-weight:700;color:{bc};">{s(label)}</p>
      <p style="margin:0;font-size:13px;color:{t["tx"]};line-height:1.7;">{s(content)}</p>
    </section>\n'''
    return f'''<section style="margin:0 0 24px;">
  <p style="margin:0 0 12px;font-size:15px;font-weight:700;color:{t["tc"]};line-height:1.5;">{s(title)}</p>
  {cards.strip()}
</section>'''


def cta(tid, title="下一步", text=None, action=None, url=None):
    if text is None: text = "先用本文的 Dockerfile 对照你的镜像构建流程。"
    if action is None: action = "查看 Docker 官方构建指南"
    if url is None: url = "https://docs.docker.com/build/"
    t = T[tid]
    if t["style"] in ("minimal", "zen"):
        return f'''<section style="margin:0 0 24px;padding:20px;border-top:1px solid {t["bd"]};border-bottom:1px solid {t["bd"]};text-align:center;">
  <p style="margin:0 0 12px;font-size:14px;color:{t["tx"]};line-height:1.8;">{s(text)}</p>
  <p style="margin:0;font-size:14px;font-weight:700;color:{t["p"]};">{s(action + " → " + url)}</p>
</section>'''
    elif t["style"] == "ticket":
        return f'''<section style="margin:0 0 24px;background:{t["lb"]};border:2px solid {t["bd"]};box-shadow:{t["sh"]};padding:20px;text-align:center;">
  <p style="margin:0 0 10px;font-size:14px;color:{t["tx"]};line-height:1.8;">{s(text)}</p>
  <p style="margin:0;font-size:14px;font-weight:800;color:{t["bd"]};">{s(action + " → " + url)}</p>
</section>'''
    else:
        return f'''<section style="margin:0 0 24px;background:{t["lb"]};border-radius:{t["r"]};padding:20px;text-align:center;box-shadow:{t["sh"]};">
  <p style="margin:0 0 10px;font-size:14px;color:{t["tx"]};line-height:1.8;">{s(text)}</p>
  <p style="margin:0;font-size:14px;font-weight:700;color:{t["p"]};">{s(action + " → " + url)}</p>
</section>'''


# 组件映射
B_COMPONENTS = {
    "facts": facts,
    "decision": decision,
    "steps": steps,
    "compare": compare,
    "annotated-image": annotated_image,
    "faq": faq,
    "timeline": timeline,
    "checklist": checklist,
    "case": case,
    "cta": cta,
}


def generate_b_components():
    """生成 10 组件 × 6 主题 = 60 份独立 HTML"""
    for comp_id, gen_func in B_COMPONENTS.items():
        for tid in ORDER:
            html = gen_func(tid)
            fname = f"{comp_id}-{tid}.html"
            fpath = os.path.join(OUT, fname)
            with open(fpath, "w", encoding="utf-8") as f:
                f.write(html)
    print(f"OK: {len(B_COMPONENTS) * len(ORDER)} B-layer component HTML files generated")


if __name__ == "__main__":
    generate_b_components()
