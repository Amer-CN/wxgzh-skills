#!/usr/bin/env python3
"""Stage 1 整篇文章 HTML 生成器

生成 3 类文章 × 6 主题 = 18 份完整 HTML：
1. 全组件样稿（9 个高级组件全塞）
2. 真实文章（3-6 个组件自然选择）
3. 短资讯（0-2 个组件，克制使用）

每份 HTML 是完整的 <section> 正文片段，包含封面/章节/正文/高级组件/签名区。
公开 HTML 不得残留编辑锚点/TODO/待补/占位符。
"""
import os, sys

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(SKILL, "tests", "advanced-components", "articles")
os.makedirs(OUT, exist_ok=True)

# 导入组件生成函数和主题配置
sys.path.insert(0, os.path.join(SKILL, "scripts"))
from generate_advanced_html import *

THEME_ORDER = ["moyu-green", "red-white", "graphite-minimal", "zen-whitespace", "moyu-ticket", "olive-journal"]

# 全局容器
def container(theme_id, inner_html):
    t = T[theme_id]
    return f'''<section style="max-width:677px;margin:0 auto;background:{t["bg"] if t["style"]!="ticket" else "#ffffff"};font-family:-apple-system,BlinkMacSystemFont,'PingFang SC','Hiragino Sans GB','Microsoft YaHei',sans-serif;color:{t["tx"]};line-height:1.75;letter-spacing:0.5px;overflow-x:hidden;">
{inner_html}
</section>'''

# 章节标题
def chapter(theme_id, num, title, en_label=""):
    t = T[theme_id]
    if t["style"] in ("minimal", "zen"):
        return f'''<section style="margin:48px 0 20px;padding-bottom:12px;border-bottom:1px solid {t["bd"]};">
  <p style="margin:0 0 6px;font-size:11px;font-weight:700;letter-spacing:2px;color:{t["st"]};">{s(en_label or num)}</p>
  <p style="margin:0;font-size:18px;font-weight:700;color:{t["tc"]};line-height:1.4;">{s(title)}</p>
</section>'''
    elif t["style"] == "ticket":
        return f'''<section style="margin:32px 0 16px;padding:10px 16px;background:{t["bd"]};box-shadow:{t["sh"]};">
  <p style="margin:0;font-size:11px;color:{t["bg"]};letter-spacing:2px;font-weight:600;">{s(num)}</p>
  <p style="margin:4px 0 0;font-size:18px;font-weight:800;color:{t["bg"]};line-height:1.3;">{s(title)}</p>
</section>'''
    else:
        return f'''<section style="margin:36px 0 16px;display:flex;align-items:baseline;gap:10px;">
  <span style="font-size:24px;font-weight:900;color:{t["p"]};line-height:1;">{s(num)}</span>
  <p style="margin:0;font-size:18px;font-weight:800;color:{t["tc"]};line-height:1.4;">{s(title)}</p>
</section>'''

# 正文段落
def para(theme_id, text, keywords=None):
    t = T[theme_id]
    # 关键词下划线
    if keywords:
        parts = text.split(keywords[0])
        if len(parts) > 1:
            kw_style = t["p"]
            inner = f'{s(parts[0])}<span style="border-bottom:2px solid {kw_style};font-weight:600;">{s(keywords[0])}</span>'
            if len(parts) > 1 and parts[1]:
                inner += s(parts[1])
            if len(keywords) > 1 and keywords[1]:
                inner2 = inner.split(keywords[1])
                if len(inner2) > 1:
                    inner = f'{inner2[0]}<span style="border-bottom:2px solid {kw_style};font-weight:600;">{s(keywords[1])}</span>{s(inner2[1])}'
            text_html = inner
        else:
            text_html = s(text)
    else:
        text_html = s(text)
    return f'<p style="margin:0 0 16px;font-size:14px;color:{t["tx"]};line-height:1.9;">{text_html}</p>'

# 引言卡（简化版）
def intro_card(theme_id, text, author=None):
    t = T[theme_id]
    author_line = f'\n  <p style="margin:8px 0 0;font-size:12px;color:{t["st"]};text-align:right;">{s(f"—— {author}")}</p>' if author else ""
    if t["style"] in ("minimal", "zen"):
        return f'''<section style="margin:10px 10px 32px;padding:32px 24px 24px;border-top:1px solid {t["bd"]};border-bottom:1px solid {t["bd"]};text-align:center;">
  <p style="font-family:'Noto Serif SC',Georgia,serif;font-size:18px;font-weight:600;color:{t["tc"]};margin:0;line-height:1.7;">{s(text)}</p>{author_line}
</section>'''
    elif t["style"] == "ticket":
        return f'''<section style="margin:0 0 32px;background:{t["lb"]};border:2px solid {t["bd"]};box-shadow:{t["sh"]};padding:24px 20px;">
  <p style="font-size:16px;font-weight:800;color:{t["tc"]};margin:0;line-height:1.7;">{s(text)}</p>{author_line}
</section>'''
    else:
        return f'''<section style="margin:10px 10px 32px;background:{t["bg"]};border-radius:{t["r"]};box-shadow:{t["sh"]};padding:24px 20px;">
  <p style="font-size:16px;font-weight:800;color:{t["tc"]};margin:0;line-height:1.7;">{s(text)}</p>{author_line}
</section>'''

# 签名区
def signature(theme_id):
    t = T[theme_id]
    if t["style"] in ("minimal", "zen"):
        return f'''<section style="margin:48px 0 0;padding:24px 20px;border-top:1px solid {t["bd"]};text-align:center;">
  <p style="margin:0 0 8px;font-size:14px;font-weight:600;color:{t["tc"]};line-height:1.7;">{s("我是甲木，热衷于分享 AI 观察与干货")}</p>
  <p style="margin:0;font-size:13px;color:{t["st"]};line-height:1.7;">{s("如果你觉得今天这篇有收获，欢迎点赞、在看、转发三连，我们下篇见")}</p>
</section>'''
    elif t["style"] == "ticket":
        return f'''<section style="margin:32px 0 0;background:{t["lb"]};border:2px solid {t["bd"]};box-shadow:{t["sh"]};padding:20px;text-align:center;">
  <p style="margin:0 0 8px;font-size:14px;font-weight:700;color:{t["tc"]};line-height:1.7;">{s("我是甲木，热衷于分享 AI 观察与干货")}</p>
  <p style="margin:0;font-size:13px;color:{t["tx"]};line-height:1.7;">{s("如果你觉得今天这篇有收获，欢迎点赞、在看、转发三连，我们下篇见")}</p>
</section>'''
    else:
        return f'''<section style="margin:32px 0 0;padding:20px;background:{t["lb"]};border-radius:{t["r"]};text-align:center;">
  <p style="margin:0 0 8px;font-size:14px;font-weight:600;color:{t["tc"]};line-height:1.7;">{s("我是甲木，热衷于分享 AI 观察与干货")}</p>
  <p style="margin:0;font-size:13px;color:{t["st"]};line-height:1.7;">{s("如果你觉得今天这篇有收获，欢迎点赞、在看、转发三连，我们下篇见")}</p>
</section>'''


def gen_all_components_article(theme_id):
    """全组件样稿：9 个高级组件全塞进一篇文章"""
    parts = []
    parts.append(intro_card(theme_id, "「公众号排版的终极目标不是好看，而是让读者真正读完。」", "甲木"))
    parts.append(chapter(theme_id, "01", "为什么需要高级组件", "WHY"))
    parts.append(para(theme_id, "传统排版只能处理标题、正文和图片。当文章需要提示风险、对照代码、展示对话时，普通 Markdown 语法力不从心。高级组件解决了这个问题。", keywords=["高级组件", "普通 Markdown"]))
    parts.append(alert(theme_id, typ="warning", title="组件不是越多越好", body="默认每篇文章 3-6 个重点高级组件；短资讯通常 0-2 个。全塞只在验收时使用。"))
    parts.append(chapter(theme_id, "02", "金句与引用", "QUOTE"))
    parts.append(para(theme_id, "好的排版会让核心观点自然跳出来。", keywords=["核心观点"]))
    parts.append(quote(theme_id, qt="highlight", text="「排版的核心不是好看，而是可读。」"))
    parts.append(quote(theme_id, qt="sourced", text="公众号编辑器会清洗 class 和外部 CSS，所有样式必须内联。", source="微信公众号开发文档"))
    parts.append(chapter(theme_id, "03", "代码对照", "CODE"))
    parts.append(code_compare(theme_id, title="改前与改后", bc="pool = connect(maxconn=200)", ac="pool = connect(maxconn=200, retry=True)"))
    parts.append(chapter(theme_id, "04", "媒体组件", "MEDIA"))
    parts.append(media_text(theme_id, url="../assets/media-demo.png", cap="微服务架构示意图", exp="该架构采用微服务拆分，每个服务独立部署，通过 API 网关统一入口。"))
    parts.append(gallery(theme_id, title="部署流程", imgs=[("../assets/gallery-01.png","下载安装包"),("../assets/gallery-02.png","配置环境变量"),("../assets/gallery-03.png","运行服务")]))
    parts.append(long_image(theme_id, url="../assets/long-flow.png", cap="完整 CI/CD 流程图"))
    parts.append(chapter(theme_id, "05", "资源与脚注", "RESOURCES"))
    parts.append(resources(theme_id, title="延伸阅读", links=[("官方文档","https://example.com/docs"),("项目仓库","https://github.com/example/repo")]))
    parts.append(footnotes(theme_id, fns=[("1","数据来源：example/benchmark v3.14.2 release notes"),("2","测试环境：8 核 CPU、32GB 内存")]))
    parts.append(chapter(theme_id, "06", "对话与排障", "DIALOGUE"))
    parts.append(dialogue(theme_id, title="常见问题", turns=[
        ("assistant","粘贴后代码高亮丢失，是因为公众号会清洗 class 与外部 CSS。"),
        ("user","那怎么保留样式？"),
        ("assistant","必须使用内联 style 属性，所有样式写死在标签上。"),
        ("user","明白了，谢谢！"),
    ]))
    parts.append(signature(theme_id))
    return container(theme_id, "\n".join(parts))


def gen_real_article(theme_id):
    """真实文章：只自然使用 3-6 个组件"""
    parts = []
    parts.append(intro_card(theme_id, "「AI 工具的效率提升只在特定任务类型中显著，多数用户总产出并未增加。」", "甲木"))
    parts.append(chapter(theme_id, "01", "效率提升的真相", "FINDINGS"))
    parts.append(para(theme_id, "我们对 200 位用户进行了为期 3 个月的跟踪测试。结果显示，使用 AI 工具后，代码生成任务的效率提升了 30%，但文档撰写和设计任务的提升不到 5%。", keywords=["30%", "5%"]))
    parts.append(alert(theme_id, typ="warning", title="数据局限", body="样本量为 200 人，均为技术岗位，不代表全行业水平。"))
    parts.append(chapter(theme_id, "02", "核心发现", "CORE"))
    parts.append(quote(theme_id, qt="highlight", text="「AI 工具不是万能加速器，而是特定场景的杠杆。」"))
    parts.append(para(theme_id, "效率提升集中在模板化、重复性高的任务上。需要创造性判断的任务几乎不受影响。", keywords=["模板化", "创造性判断"]))
    parts.append(chapter(theme_id, "03", "改进建议", "SOLUTION"))
    parts.append(code_compare(theme_id, title="提示词优化对照", bc="result = llm.generate(prompt)", ac="result = llm.generate(prompt, context=True, retry=2)"))
    parts.append(resources(theme_id, title="参考资料", links=[("效率测试方法论","https://example.com/method"),("完整数据集","https://github.com/example/ai-efficiency")]))
    parts.append(footnotes(theme_id, fns=[("1","调查样本：200 名开发者，来自 5 家公司，2026 年 6-8 月")]))
    parts.append(signature(theme_id))
    return container(theme_id, "\n".join(parts))


def gen_short_news(theme_id):
    """短资讯：最多 2 个高级组件，克制使用"""
    parts = []
    parts.append(intro_card(theme_id, "「OpenAI 发布 GPT-5，上下文窗口扩展至 200 万 token。」"))
    parts.append(para(theme_id, "2026 年 7 月 17 日，OpenAI 正式发布 GPT-5 模型，上下文窗口从 128 万扩展至 200 万 token，定价为每百万 token 输入 15 美元、输出 75 美元。", keywords=["GPT-5", "200 万 token"]))
    parts.append(para(theme_id, "新模型在代码生成和多语言推理任务上均有显著提升，但在创意写作任务上表现与前代持平。"))
    parts.append(alert(theme_id, typ="tip", title="试用建议", body="GPT-5 API 已开放，开发者可在 OpenAI Platform 注册体验。"))
    parts.append(signature(theme_id))
    return container(theme_id, "\n".join(parts))


ARTICLES = {
    "all-components": ("全组件样稿", gen_all_components_article),
    "real-article": ("真实文章", gen_real_article),
    "short-news": ("短资讯", gen_short_news),
}


def main():
    for art_id, (art_name, gen_func) in ARTICLES.items():
        for tid in THEME_ORDER:
            html = gen_func(tid)
            fname = f"{art_id}-{tid}.html"
            fpath = os.path.join(OUT, fname)
            with open(fpath, "w", encoding="utf-8") as f:
                f.write(html)
    print(f"OK: {len(ARTICLES) * len(THEME_ORDER)} article HTML files generated in {OUT}")


if __name__ == "__main__":
    main()
