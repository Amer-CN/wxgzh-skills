#!/usr/bin/env python3
"""Stage 1 高级组件 HTML 验收文件生成器

生成 9 组件 x 6 主题 = 54 份验收 HTML 到 tests/advanced-components/expected/
"""
import os, sys

SKILL = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# OBS-108(档71C-1):OUT 与 makedirs 移进 main() —— import 本模块时零写盘。
# render_article.py 需 import 本模块的 builder 函数,不得在 import 时写 tests/。

T = {
 "moyu-green": dict(n="摸鱼绿",p="#059669",pd="#047857",lb="#ECFDF5",bg="#F0FDF4",bd="#BBF7D0",tc="#111827",tx="#374151",st="#9CA3AF",dv="#D1D5DB",wb="#FFFBEB",wt="#92400E",wbd="#FDE68A",r="12px",sh="0 4px 16px -4px rgba(0,0,0,0.08)",style="card",pad="16px 20px"),
 "red-white": dict(n="红白色系",p="#DC2626",pd="#991B1B",lb="#FEF2F2",bg="#FFF",bd="#FEE2E2",tc="#1C1917",tx="#374151",st="#9CA3AF",dv="#E5E7EB",wb="#FFFBEB",wt="#92400E",wbd="#FDE68A",r="10px",sh="0 2px 12px -2px rgba(220,38,38,0.1)",style="leftbar",pad="14px 18px"),
 "graphite-minimal": dict(n="石墨极简",p="#52525B",pd="#27272A",lb="#FAFAFA",bg="#FFFFFF",bd="#E4E4E7",tc="#27272A",tx="#52525B",st="#A1A1AA",dv="#E4E4E7",wb="#FAFAFA",wt="#52525B",wbd="#E4E4E7",r="0px",sh="none",style="minimal",pad="20px 20px"),
 "zen-whitespace": dict(n="留白禅意",p="#4A5D52",pd="#2B2B2B",lb="#FFFFFF",bg="#FFFFFF",bd="#E8E8E8",tc="#2B2B2B",tx="#525252",st="#A3A3A3",dv="#E8E8E8",wb="#FFFFFF",wt="#525252",wbd="#E8E8E8",r="0px",sh="none",style="zen",pad="24px 20px"),
 "moyu-ticket": dict(n="摸鱼票据",p="#059669",pd="#1a1a1a",lb="#fffef8",bg="#fffef8",bd="#1a1a1a",tc="#1a1a1a",tx="#555",st="#888",dv="#A7F3D0",wb="#fffef8",wt="#92400E",wbd="#1a1a1a",r="0px",sh="3px 3px 0 #1a1a1a",style="ticket",pad="14px 18px"),
 "olive-journal": dict(n="橄榄手记",p="#ed7b2f",pd="#1e1f23",lb="#eeefe9",bg="#fdfdf8",bd="#bfc1b7",tc="#23251d",tx="#4d4f46",st="#9ea096",dv="#bfc1b7",wb="#fffdf5",wt="#92400E",wbd="#ed7b2f",r="6px",sh="none",style="journal",pad="14px 18px"),
 "hammer": dict(n="锤子风格",p="#B3593B",pd="#8A4530",lb="#FAF9F5",bg="#F7F7F7",bd="#DAB1A1",tc="#555555",tx="#555555",st="#737373",dv="rgba(202,202,199,0.35)",wb="#FAF9F5",wt="#B3593B",wbd="#E3C6B9",r="12px",sh="0 4px 16px -4px rgba(179,89,59,0.10)",style="card",pad="16px 20px"),
}
ORDER = list(T.keys())

def s(x): return f'<span leaf="">{x}</span>'

def _p_lines(style: str, body: str) -> str:
    """多行正文槽:逐有效行一个 <p>,空行跳过;style 逐字复用调用处字符串。
    R21:不新造 HTML 常量,只把既有单行 <p> 模板按行重复。"""
    lines = [l for l in body.replace("\r\n", "\n").split("\n") if l.strip()]
    if not lines:
        return f'<p style="{style}">{s(body)}</p>'
    return "\n".join(f'<p style="{style}">{s(l)}</p>' for l in lines)


def alert(tid, typ="warning", title="风险提示", body="此版本在 PostgreSQL 16.2 上存在已知的连接池泄漏问题。"):
    # OBS-145(R26):显式枚举判断,未知 type 不抛异常,回落默认 warning。
    # 枚举来自 references/advanced/alerts.md L17-21(note/tip/important/warning/caution)。
    _ALERT_TYPES = {"note", "tip", "important", "warning", "caution"}
    if typ not in _ALERT_TYPES:
        typ = "warning"
    t=T[tid]; at={"note":("NOTE",t["lb"],t["bd"],t["tx"]),"tip":("TIP",t["lb"],t["p"],t["pd"]),"important":("IMPORTANT",t["lb"],t["p"],t["tc"]),"warning":("WARNING",t["wb"],t["wbd"],t["wt"]),"caution":("CAUTION",t["wb"],t["wbd"],t["wt"])}[typ]
    lab,bg,bdc,tx=at
    if t["style"] in("minimal","zen"):
        body_p = _p_lines("margin:0;font-size:14px;color:" + tx + ";line-height:1.8;", body)
        return f'''<section style="margin:0 0 24px;padding:20px 20px;border-top:1px solid {bdc};border-bottom:1px solid {bdc};background:{bg};">
  <p style="margin:0 0 8px;font-size:11px;font-weight:700;letter-spacing:2px;color:{t["st"]};">{s(lab)}</p>
  <p style="margin:0 0 10px;font-size:15px;font-weight:700;color:{t["tc"]};line-height:1.6;">{s(title)}</p>
  {body_p}
</section>'''
    elif t["style"]=="ticket":
        body_p = _p_lines("margin:0;font-size:14px;color:" + t["tx"] + ";line-height:1.8;", body)
        return f'''<section style="margin:0 0 24px;background:{bg};border:2px solid {bdc};box-shadow:{t["sh"]};padding:14px 18px;">
  <p style="margin:0 0 8px;"><span style="display:inline-block;background:{bdc};color:{t["bg"]};font-size:11px;font-weight:700;padding:2px 10px;letter-spacing:1px;">{s(lab)}</span></p>
  <p style="margin:0 0 10px;font-size:15px;font-weight:700;color:{t["tc"]};line-height:1.5;">{s(title)}</p>
  {body_p}
</section>'''
    else:
        body_p = _p_lines("margin:0;font-size:14px;color:" + t["tx"] + ";line-height:1.8;", body)
        return f'''<section style="margin:0 0 24px;background:{bg};border-radius:0 {t["r"]} {t["r"]} 0;border-left:4px solid {bdc};padding:{t["pad"]};">
  <p style="margin:0 0 6px;"><span style="display:inline-block;background:{bdc};color:{t["bg"]};font-size:11px;font-weight:700;padding:2px 10px;border-radius:4px;letter-spacing:1px;">{s(lab)}</span></p>
  <p style="margin:0 0 8px;font-size:15px;font-weight:700;color:{tx};line-height:1.5;">{s(title)}</p>
  {body_p}
</section>'''

def quote(tid, qt="highlight", text="「排版的核心不是好看，而是可读。」", source=None):
    # OBS-145(R26):显式枚举判断,未知 type 不抛异常,回落默认 highlight。
    # 枚举来自 references/advanced/quotes.md L9-21(normal/highlight/sourced)。
    _QUOTE_TYPES = {"normal", "highlight", "sourced"}
    if qt not in _QUOTE_TYPES:
        qt = "highlight"
    t=T[tid]
    if qt=="normal":
        if t["style"] in("minimal","zen"):
            return f'<section style="margin:0 0 24px;padding:16px 20px;border-top:1px solid {t["bd"]};border-bottom:1px solid {t["bd"]};">{_p_lines("margin:0;font-size:14px;color:" + t["tx"] + ";line-height:1.8;", text)}</section>'
        return f'<section style="margin:0 0 24px;background:{t["lb"]};border-radius:0 {t["r"]} {t["r"]} 0;border-left:3px solid {t["bd"]};padding:14px 18px;">{_p_lines("margin:0;font-size:14px;color:" + t["tx"] + ";line-height:1.8;", text)}</section>'
    elif qt=="highlight":
        if t["style"] in("minimal","zen"):
            return f'<section style="margin:0 0 24px;padding:20px 20px;border-top:1px solid {t["bd"]};border-bottom:1px solid {t["bd"]};text-align:center;">{_p_lines("margin:0;font-size:16px;font-weight:700;color:" + t["tc"] + ";line-height:1.7;", text)}</section>'
        elif t["style"]=="ticket":
            return f'<section style="margin:0 0 24px;background:{t["lb"]};border:2px solid {t["bd"]};box-shadow:{t["sh"]};padding:14px 18px;text-align:center;">{_p_lines("margin:0;font-size:16px;font-weight:800;color:" + t["tc"] + ";line-height:1.7;", text)}</section>'
        return f'<section style="margin:0 0 24px;background:{t["lb"]};border-radius:0 {t["r"]} {t["r"]} 0;border-left:4px solid {t["p"]};padding:16px 20px;">{_p_lines("margin:0;font-size:16px;font-weight:800;color:" + t["pd"] + ";line-height:1.7;", text)}</section>'
    else:
        sl=f'\n  <p style="margin:8px 0 0;font-size:12px;color:{t["st"]};">{s(f"—— {source}")}</p>' if source else ""
        if t["style"] in("minimal","zen"):
            return f'<section style="margin:0 0 24px;padding:20px 20px;border-top:1px solid {t["bd"]};border-bottom:1px solid {t["bd"]};">{_p_lines("margin:0;font-size:15px;font-weight:600;color:" + t["tc"] + ";line-height:1.8;", text)}{sl}</section>'
        return f'<section style="margin:0 0 24px;background:{t["lb"]};border-radius:0 {t["r"]} {t["r"]} 0;border-left:4px solid {t["p"]};padding:14px 18px;">{_p_lines("margin:0;font-size:15px;font-weight:600;color:" + t["tc"] + ";line-height:1.8;", text)}{sl}</section>'

def code_compare(tid, title="改前与改后", bc="pool = connect(maxconn=200)", ac="pool = connect(maxconn=200, retry=True)"):
    t=T[tid]
    if t["style"] in("minimal","zen"):
        return f'''<section style="margin:0 0 24px;">
  <p style="margin:0 0 12px;font-size:15px;font-weight:700;color:{t["tc"]};line-height:1.5;">{s(title)}</p>
  <section style="margin:0 0 12px;border-top:1px solid {t["bd"]};border-bottom:1px solid {t["bd"]};background:{t["lb"]};padding:12px 14px;">
    <p style="margin:0 0 4px;font-size:11px;font-weight:700;letter-spacing:1px;color:{t["st"]};">{s("改前")}</p>
    <p style="margin:0;font-family:'SF Mono',Consolas,Monaco,monospace;font-size:13px;line-height:1.6;color:{t["tx"]};">{s(bc)}</p>
  </section>
  <section style="margin:0 0 12px;border-top:1px solid {t["p"]};border-bottom:1px solid {t["p"]};background:{t["lb"]};padding:12px 14px;">
    <p style="margin:0 0 4px;font-size:11px;font-weight:700;letter-spacing:1px;color:{t["p"]};">{s("改后")}</p>
    <p style="margin:0;font-family:'SF Mono',Consolas,Monaco,monospace;font-size:13px;line-height:1.6;color:{t["tx"]};">{s(ac)}</p>
  </section>
</section>'''
    return f'''<section style="margin:0 0 24px;">
  <p style="margin:0 0 12px;font-size:15px;font-weight:700;color:{t["tc"]};line-height:1.5;">{s(title)}</p>
  <section style="margin:0 0 12px;border-radius:{t["r"]};overflow:hidden;background:#1E293B;">
    <section style="padding:7px 14px;background:#0F172A;"><span style="font-size:11px;color:#64748B;letter-spacing:1px;">{s("改前")}</span></section>
    <section style="padding:11px 14px;"><p style="margin:0;font-family:'SF Mono',Consolas,Monaco,monospace;font-size:13px;line-height:1.6;color:#E2E8F0;">{s(bc)}</p></section>
  </section>
  <section style="margin:0 0 12px;border-radius:{t["r"]};overflow:hidden;background:#1a3a2a;">
    <section style="padding:7px 14px;background:#0a2a1a;"><span style="font-size:11px;color:#6BCB77;letter-spacing:1px;">{s("改后")}</span></section>
    <section style="padding:11px 14px;"><p style="margin:0;font-family:'SF Mono',Consolas,Monaco,monospace;font-size:13px;line-height:1.6;color:#C8E6C9;">{s(ac)}</p></section>
  </section>
</section>'''

def media_text(tid, url="../assets/media-demo.png", cap="架构示意图", exp="该架构采用微服务拆分，每个服务独立部署。"):
    t=T[tid]
    if t["style"] in("minimal","zen"):
        return f'''<section style="margin:0 0 24px;">
  <section style="margin:0 0 10px;"><span leaf=""><img src="{url}" style="max-width:100%;height:auto;display:block;margin:0 auto;"></span></section>
  <p style="margin:0 0 10px;font-size:12px;color:{t["st"]};text-align:center;">{s(cap)}</p>
  {_p_lines("margin:0;font-size:14px;color:" + t["tx"] + ";line-height:1.8;", exp)}
</section>'''
    return f'''<section style="margin:0 0 8px;background:{t["bg"]};border-radius:{t["r"]};padding:6px;border:1px solid {t["bd"]};box-shadow:{t["sh"]};">
  <section style="margin:0;border-radius:{t["r"]};overflow:hidden;"><span leaf=""><img src="{url}" style="max-width:100%;height:auto;display:block;margin:0 auto;"></span></section>
</section>
<p style="margin:0 0 8px;font-size:12px;color:{t["st"]};text-align:center;">{s(cap)}</p>
{_p_lines("margin:0 0 24px;font-size:14px;color:" + t["tx"] + ";line-height:1.8;", exp)}'''

def gallery(tid, title="安装过程", imgs=None):
    t=T[tid]
    if imgs is None: imgs=[("../assets/gallery-01.png","下载安装包"),("../assets/gallery-02.png","配置环境变量"),("../assets/gallery-03.png","运行服务")]
    items=""
    for u,c in imgs:
        items+=f'''<section style="margin:0 0 12px;">
    <section style="margin:0 0 6px;border-radius:{t["r"]};overflow:hidden;"><span leaf=""><img src="{u}" style="max-width:100%;height:auto;display:block;margin:0 auto;"></span></section>
    <p style="margin:0 0 16px;font-size:12px;color:{t["st"]};text-align:center;">{s(c)}</p>
  </section>\n'''
    return f'<section style="margin:0 0 24px;"><p style="margin:0 0 14px;font-size:15px;font-weight:700;color:{t["tc"]};line-height:1.5;">{s(title)}</p>\n  {items.strip()}\n</section>'

def long_image(tid, url="../assets/long-flow.png", cap="完整部署流程图"):
    t = T[tid]
    if t["style"] in ("minimal", "zen"):
        cap_line = (f'<p style="margin:12px 0 0;font-size:12px;color:{t["st"]};text-align:center;">{s(cap)}</p>'
                    if cap else "")
        return (f'<section style="margin:0 0 24px;padding:16px 20px;border-top:1px solid {t["bd"]};border-bottom:1px solid {t["bd"]};">'
                f'<span leaf=""><img src="{url}" style="max-width:100%;height:auto;display:block;margin:0 auto;"></span>'
                f'{cap_line}'
                f'</section>')
    cap_line = (f'<p style="margin:0 0 24px;font-size:12px;color:{t["st"]};text-align:center;">{s(cap)}</p>'
                if cap else "")
    return (f'<section style="margin:0 0 8px;background:{t["bg"]};border-radius:{t["r"]};padding:6px;border:1px solid {t["bd"]};box-shadow:{t["sh"]};">'
            f'<span leaf=""><img src="{url}" style="max-width:100%;height:auto;display:block;margin:0 auto;"></span>'
            f'</section>'
            f'{cap_line}')
def resources(tid, title="参考资料", links=None):
    t=T[tid]
    if links is None: links=[("官方文档","https://example.com/docs"),("项目仓库","https://github.com/example/repo")]
    items=""
    for i,(l,u) in enumerate(links,1):
        if t["style"] in("minimal","zen"):
            items+=f'''<p style="margin:0 0 10px;font-size:14px;color:{t["tx"]};line-height:1.8;"><span style="color:{t["st"]};font-weight:700;margin-right:6px;">{s(f"{i:02d}")}</span>{s(l)} <span style="font-size:12px;color:{t["st"]};">{s(u)}</span></p>\n'''
        else:
            items+=f'''<section style="margin:0 0 8px;padding:10px 14px;background:{t["lb"]};border-radius:{t["r"]};border-left:3px solid {t["p"]};"><p style="margin:0;font-size:14px;color:{t["tc"]};font-weight:600;line-height:1.6;">{s(l)}</p><p style="margin:2px 0 0;font-size:12px;color:{t["st"]};">{s(u)}</p></section>\n'''
    return f'<section style="margin:0 0 24px;"><p style="margin:0 0 12px;font-size:15px;font-weight:700;color:{t["tc"]};line-height:1.5;">{s(title)}</p>\n  {items.strip()}\n</section>'

def footnotes(tid, fns=None):
    t=T[tid]
    if fns is None: fns=[("1","数据来源：example/benchmark v3.14.2 release notes"),("2","测试环境：8 核 CPU、32GB 内存")]
    items=""
    for n,txt in fns:
        items+=f'''<p style="margin:0 0 6px;font-size:12px;color:{t["st"]};line-height:1.7;"><span style="font-weight:700;color:{t["p"]};margin-right:4px;">{s(f"[{n}]")}</span>{s(txt)}</p>\n'''
    return f'<section style="margin:24px 0 0;padding-top:16px;border-top:1px solid {t["dv"]};">\n  {items.strip()}\n</section>'

# ── Dialogue 专用色值表（左右聊天窗热修复）──
# 每个主题定义 user/assistant 的气泡背景、文字色、头像色、边框
DIALOGUE_COLORS = {
 "moyu-green": dict(
     u_bg="#059669",u_tx="#FFFFFF",u_av="#047857",u_avtx="#FFFFFF",
     a_bg="#ECFDF5",a_tx="#374151",a_av="#9CA3AF",a_avtx="#FFFFFF",
     u_bdr="",a_bdr="",r="12px"),
 "red-white": dict(
     u_bg="#DC2626",u_tx="#FFFFFF",u_av="#991B1B",u_avtx="#FFFFFF",
     a_bg="#F5F5F5",a_tx="#374151",a_av="#9CA3AF",a_avtx="#FFFFFF",
     u_bdr="",a_bdr="",r="10px"),
 "graphite-minimal": dict(
     u_bg="#27272A",u_tx="#FAFAFA",u_av="#52525B",u_avtx="#FFFFFF",
     a_bg="#FAFAFA",a_tx="#52525B",a_av="#A1A1AA",a_avtx="#FFFFFF",
     u_bdr="",a_bdr="border:1px solid #E4E4E7;",r="0px"),
 "zen-whitespace": dict(
     u_bg="#F5F5F5",u_tx="#2B2B2B",u_av="#4A5D52",u_avtx="#FFFFFF",
     a_bg="#FFFFFF",a_tx="#525252",a_av="#A3A3A3",a_avtx="#FFFFFF",
     u_bdr="border:1px solid #E8E8E8;",a_bdr="border:1px solid #E8E8E8;",r="0px"),
 "moyu-ticket": dict(
     u_bg="#fffef8",u_tx="#1a1a1a",u_av="#1a1a1a",u_avtx="#fffef8",
     a_bg="#fffef8",a_tx="#555",a_av="#888",a_avtx="#fffef8",
     u_bdr="border:2px solid #1a1a1a;box-shadow:3px 3px 0 #1a1a1a;",
     a_bdr="border:1px solid #888;",r="0px"),
 "olive-journal": dict(
     u_bg="#ed7b2f",u_tx="#FFFFFF",u_av="#1e1f23",u_avtx="#FFFFFF",
     a_bg="#eeefe9",a_tx="#4d4f46",a_av="#9ea096",a_avtx="#FFFFFF",
     u_bdr="",a_bdr="",r="6px"),
 "hammer": dict(
     u_bg="#EAD6CC",u_tx="#555555",u_av="#B3593B",u_avtx="#FFFFFF",
     a_bg="#FAF9F5",a_tx="#555555",a_av="#B3593B",a_avtx="#FFFFFF",
     u_bdr="border:1px solid #DAB1A1;",a_bdr="border:1px solid rgba(202,202,199,0.35);",r="12px"),
}

def dialogue(tid, title="排障问答", turns=None):
    """左右聊天窗 dialogue：assistant 左头像+右气泡，user 左气泡+右头像。
    仅用 section/p/span + display:inline-block + text-align，兼容公众号。
    """
    t=T[tid]
    dc=DIALOGUE_COLORS[tid]
    if turns is None:
        turns=[("user","为什么粘贴后代码颜色丢失？"),("assistant","公众号会清洗 class 与外部 CSS，必须使用内联样式。")]
    r=dc["r"]
    av_size='width:34px;height:34px;line-height:34px;text-align:center;border-radius:50%;font-size:12px;font-weight:700;vertical-align:top;'
    bbl='display:inline-block;max-width:72%;vertical-align:top;text-align:left;padding:10px 14px;'
    items=""
    for turn in turns:
        role=turn[0]; txt=turn[1]
        name=turn[2] if len(turn)>2 else None
        if role in ("user","me"):
            av_char=name[0] if name else "我"
            name_p=f'<p style="margin:0 0 4px;font-size:11px;font-weight:700;color:{dc["u_av"]};text-align:right;">{s(name)}</p>' if name else ""
            items+=(f'<section style="text-align:right;margin:0 0 12px;">'
                    f'<section style="{bbl}margin-right:8px;background:{dc["u_bg"]};border-radius:{r};{dc["u_bdr"]}">'
                    f'{name_p}'
                    f'<p style="margin:0;font-size:14px;color:{dc["u_tx"]};line-height:1.8;">{s(txt)}</p>'
                    f'</section>'
                    f'<span style="display:inline-block;{av_size}background:{dc["u_av"]};color:{dc["u_avtx"]};">{s(av_char)}</span>'
                    f'</section>\n')
        else:
            av_char=name[0] if name else "AI"
            name_p=f'<p style="margin:0 0 4px;font-size:11px;font-weight:700;color:{dc["a_av"]};">{s(name)}</p>' if name else ""
            items+=(f'<section style="text-align:left;margin:0 0 12px;">'
                    f'<span style="display:inline-block;{av_size}background:{dc["a_av"]};color:{dc["a_avtx"]};">{s(av_char)}</span>'
                    f'<section style="{bbl}margin-left:8px;background:{dc["a_bg"]};border-radius:{r};{dc["a_bdr"]}">'
                    f'{name_p}'
                    f'<p style="margin:0;font-size:14px;color:{dc["a_tx"]};line-height:1.8;">{s(txt)}</p>'
                    f'</section>'
                    f'</section>\n')
    return f'<section style="margin:0 0 24px;"><p style="margin:0 0 12px;font-size:15px;font-weight:700;color:{t["tc"]};line-height:1.5;">{s(title)}</p>\n  {items.strip()}\n</section>'

COMPS = {
 "alert": lambda tid: alert(tid),
 "quote": lambda tid: quote(tid),
 "code-compare": lambda tid: code_compare(tid),
 "media-text": lambda tid: media_text(tid),
 "gallery": lambda tid: gallery(tid),
 "long-image": lambda tid: long_image(tid),
 "resources": lambda tid: resources(tid),
 "footnotes": lambda tid: footnotes(tid),
 "dialogue": lambda tid: dialogue(tid),
}

def main():
    # OBS-108:OUT 仅在本脚本作为 CLI 执行时创建(import 零写盘)
    OUT = os.path.join(SKILL, "tests", "advanced-components", "expected")
    os.makedirs(OUT, exist_ok=True)
    for cid, gen in COMPS.items():
        for tid in ORDER:
            html = gen(tid)
            fp = os.path.join(OUT, f"{cid}-{tid}.html")
            with open(fp, "w", encoding="utf-8") as f:
                f.write(html)
    print(f"OK: {len(COMPS)*len(ORDER)} HTML files generated in {OUT}")

if __name__ == "__main__":
    main()