#!/usr/bin/env python3
"""B 层整篇文章 HTML 生成器

3 类文章 × 6 主题 = 18 份完整 HTML：
1. b-all-components: 10 个 B 层组件全塞（验收用）
2. b-structured-article: facts + decision + steps + compare + checklist（结构化）
3. b-story-article: timeline + case + faq + annotated-image + cta（叙事型）
"""
import os, sys

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(SKILL, "tests", "advanced-components", "expected")

sys.path.insert(0, os.path.join(SKILL, "scripts"))
from generate_advanced_html import T, ORDER, s
from generate_article_html import container, chapter, para, intro_card, signature
from generate_b_html import facts, decision, steps, compare, annotated_image, faq, timeline, checklist, case, cta


def gen_b_all_components(tid):
    """B 全组件样稿：10 个组件全塞"""
    p = []
    p.append(intro_card(tid, "「结构化表达让技术文章更易读、更易执行。」", "甲木"))
    p.append(chapter(tid, "01", "事实数据卡", "FACTS"))
    p.append(para(tid, "核心指标用数据卡呈现，比埋在正文里更醒目。"))
    p.append(facts(tid))
    p.append(chapter(tid, "02", "决策说明卡", "DECISION"))
    p.append(para(tid, "方案选择需要清晰的推荐和理由。"))
    p.append(decision(tid))
    p.append(chapter(tid, "03", "步骤流程", "STEPS"))
    p.append(steps(tid))
    p.append(chapter(tid, "04", "结构化对比", "COMPARE"))
    p.append(compare(tid))
    p.append(chapter(tid, "05", "注释图片", "ANNOTATED"))
    p.append(annotated_image(tid))
    p.append(chapter(tid, "06", "问答组", "FAQ"))
    p.append(faq(tid))
    p.append(chapter(tid, "07", "时间线", "TIMELINE"))
    p.append(timeline(tid))
    p.append(chapter(tid, "08", "清单", "CHECKLIST"))
    p.append(checklist(tid))
    p.append(chapter(tid, "09", "案例复盘", "CASE"))
    p.append(case(tid))
    p.append(chapter(tid, "10", "行动引导", "CTA"))
    p.append(cta(tid))
    p.append(signature(tid))
    return container(tid, "\n".join(p))


def gen_b_structured_article(tid):
    """B 结构化文章：facts + decision + steps + compare + checklist（5 个组件）"""
    p = []
    p.append(intro_card(tid, "「从 1.2GB 到 180MB，Docker 镜像优化的完整决策路径。」", "甲木"))
    p.append(chapter(tid, "01", "现状数据", "DATA"))
    p.append(para(tid, "先看当前镜像的体积构成和关键指标。"))
    p.append(facts(tid, title="镜像现状", items=[("镜像体积","1.2GB"),("CI 拉取时间","4 分钟"),("本地启动","30 秒"),("构建层数","4 层")]))
    p.append(chapter(tid, "02", "方案选择", "DECISION"))
    p.append(decision(tid, title="构建方案选择", recommended="多阶段构建",
             options=[("单阶段构建","简单但镜像大",False),("多阶段构建","稍复杂但镜像小",True),("Distroless","最小但调试困难",False)]))
    p.append(chapter(tid, "03", "执行步骤", "STEPS"))
    p.append(steps(tid, title="优化步骤", items=["选择 slim 基础镜像","分离构建层与运行层","添加 .dockerignore","验证镜像体积"]))
    p.append(chapter(tid, "04", "方案对比", "COMPARE"))
    p.append(compare(tid, title="构建方案对比",
             cols=["维度","单阶段","多阶段","Distroless"],
             rows=[("镜像体积","大","小","最小"),("构建复杂度","低","中","高"),("调试便利性","高","中","低"),("生产适用性","一般","高","高")]))
    p.append(chapter(tid, "05", "发布检查", "CHECKLIST"))
    p.append(checklist(tid, title="发布前检查", items=[("镜像体积 < 200MB",True),("CI 构建通过",True),("健康检查通过",True),("回滚预案就绪",False)]))
    p.append(signature(tid))
    return container(tid, "\n".join(p))


def gen_b_story_article(tid):
    """B 叙事型文章：timeline + case + faq + annotated-image + cta（5 个组件）"""
    p = []
    p.append(intro_card(tid, "「从原型到上线，6 个月的镜像优化之路。」", "甲木"))
    p.append(chapter(tid, "01", "演进历程", "TIMELINE"))
    p.append(timeline(tid, title="优化历程", items=[("2026-01","完成原型验证"),("2026-02","识别体积问题"),("2026-03","启动多阶段改造"),("2026-05","灰度验证通过"),("2026-06","全量上线")]))
    p.append(chapter(tid, "02", "案例复盘", "CASE"))
    p.append(case(tid, title="镜像瘦身实践",
             context="Node.js 服务镜像 1.2GB，CI 拉取 4 分钟。",
             challenge="部署慢，磁盘告警。",
             action="改用多阶段构建，移除开发依赖。",
             result="镜像降至 180MB，部署时间缩短 60%。"))
    p.append(chapter(tid, "03", "控制台说明", "ANNOTATED"))
    p.append(annotated_image(tid, url="../assets/annotated-dashboard.png", caption="CI/CD 控制台关键区域",
             notes=[("1","左侧导航切换构建配置"),("2","中央显示构建状态"),("3","右上角触发部署")]))
    p.append(chapter(tid, "04", "常见问题", "FAQ"))
    p.append(faq(tid, title="部署 FAQ", items=[("多阶段构建会拖慢 CI 吗？","构建略慢但拉取更快。"),("如何回滚？","保留旧镜像 tag 即可快速回滚。")]))
    p.append(chapter(tid, "05", "下一步", "CTA"))
    p.append(cta(tid, title="开始优化", text="对照你的 Dockerfile 开始优化吧。", action="查看 Docker 官方指南", url="https://docs.docker.com/build/"))
    p.append(signature(tid))
    return container(tid, "\n".join(p))


ARTICLES = {
    "b-all-components": gen_b_all_components,
    "b-structured-article": gen_b_structured_article,
    "b-story-article": gen_b_story_article,
}


def main():
    for art_id, gen_func in ARTICLES.items():
        for tid in ORDER:
            html = gen_func(tid)
            fname = f"{art_id}-{tid}.html"
            fpath = os.path.join(OUT, fname)
            with open(fpath, "w", encoding="utf-8") as f:
                f.write(html)
    print(f"OK: {len(ARTICLES) * len(ORDER)} B-layer article HTML files generated")


if __name__ == "__main__":
    main()
