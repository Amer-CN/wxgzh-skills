#!/usr/bin/env python3
"""Theme-identity validator (hammer / smartisan). NOT an HTML-syntax check.

Reverse-parses the final HTML for structural fingerprints that appear verbatim
in BOTH the official gzh-design source AND the HTML, asserting official-component
counts, image-component types, theme fallback, and strikethrough safety.
Also emits a program-generated component_usage_report (never hand-declared).

OBS-98(档69):strike 断言改为形态语义判定,不再硬编码 #B3593B/1.5px。
规格来源 = gzh-design references/common-components + 67D 落地实现
(color:#737373 文字 + 同色 text-decoration-color + thickness:1px,白底对比度
>= 4.5)。逐元素校验,不接受任何硬编码色值作为唯一合格值。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

# fingerprint -> literal substring present in official source + rendered HTML
# OBS-109(档71C-1):图片类指纹去碰撞 —— image_media_text_card 原值
# "0 4px 16px -4px rgba(179,89,59,0.10)" == T["hammer"]["sh"] 阴影令牌,
# 被 media-text/long-image 高级组件共享,非图片专有。改为「阴影令牌 + <img
# 标签特征」复合判据:必须同时出现阴影令牌与 <img,才计为 media-text 卡。
FINGERPRINTS = {
    "cover_breaking": "border-radius:20px;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,0.06)",
    "toc_scroll": "overflow-x:scroll;-webkit-overflow-scrolling:touch;white-space:nowrap",
    "chapter_title": "font-size:28px;font-weight:900;color:",
    "signature": "热闹是 AI 的，淡定可以是我们的。",
    "footer_cta": "radial-gradient(circle at center,",
    "image_2a_standard": "box-shadow:0 4px 12px -2px rgba(0,0,0,0.08)",
    "image_media_text_card": "0 4px 16px -4px rgba(179,89,59,0.10)",
}

# OBS-98:主题主色(hammer primary)——删除线不得使用主题主色作为 decoration 色。
_HAMMER_PRIMARY_HEX = "#B3593B"
# OBS-98:低对比度禁用文字色——line-through 元素使用该色一律判 bad,无豁免。
_FORBIDDEN_STRIKE_TEXT_RGBA = "rgba(202,202,199,0.35)"
# OBS-98:白底对比度下限(67C/67D 沿用,WCAG 普通文字阈值)。
_MIN_CONTRAST = 4.5
_WHITE = (255, 255, 255)


def _sha(t: str) -> str:
    return hashlib.sha256(t.encode("utf-8")).hexdigest()


def _hex_to_rgb(value: str) -> tuple[int, int, int] | None:
    """#RRGGBB / RRGGBB -> (r,g,b);其余形态(变量/rgba/未知)返回 None。"""
    s = (value or "").strip().lower().lstrip("#")
    if len(s) != 6 or any(c not in "0123456789abcdef" for c in s):
        return None
    return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


def _linearize(c: float) -> float:
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _relative_luminance(rgb: tuple[int, int, int]) -> float:
    r, g, b = (v / 255.0 for v in rgb)
    return 0.2126 * _linearize(r) + 0.7152 * _linearize(g) + 0.0722 * _linearize(b)


def _contrast_ratio(fg: tuple[int, int, int], bg: tuple[int, int, int] = _WHITE) -> float:
    """WCAG 对比度(与 67D test_obs90 TestStrikeContrast 同一算法,白底默认)。"""
    l1, l2 = _relative_luminance(fg), _relative_luminance(bg)
    if l1 < l2:
        l1, l2 = l2, l1
    return (l1 + 0.05) / (l2 + 0.05)


# OBS-98:逐个 line-through 元素解析其 style 声明(不做全文子串匹配)。
_STYLE_ATTR_RE = re.compile(r'style="([^"]*)"')


def _style_decl(style: str, name: str) -> str | None:
    """从 style 串解析 `name:value` 声明(仅按分号分隔,大小写不敏感)。"""
    for part in style.split(";"):
        if ":" not in part:
            continue
        key, _, val = part.partition(":")
        if key.strip().lower() == name:
            return val.strip()
    return None


def _parse_strike_elements(html: str) -> list[dict]:
    """收集所有含 line-through 的 style 元素(归一化空白后解析,防换行/空格干扰)。

    每个元素返回:
      style 原文 / color / text-decoration-color / text-decoration-thickness。
    声明缺失的字段为 None(调用方按形态语义判 fail,不默认放行)。
    """
    normalized = html.replace(" ", "")
    out = []
    for m in _STYLE_ATTR_RE.finditer(normalized):
        style = m.group(1)
        if "line-through" not in style:
            continue
        out.append({
            "style": style,
            "color": _style_decl(style, "color"),
            "decoration_color": _style_decl(style, "text-decoration-color"),
            "thickness": _style_decl(style, "text-decoration-thickness"),
        })
    return out


def _strike_element_ok(el: dict) -> tuple[bool, list[str]]:
    """OBS-98 形态语义断言:单个 line-through 元素全部满足才算 ok。

    (a) 声明了 text-decoration-color;
    (b) text-decoration-color 与自身 color 为同一色值(同色系细线,67A 第 7 条);
    (c) text-decoration-thickness 存在且 <= 1px;
    (d) text-decoration-color 不为 #B3593B(主题主色不得用作删除线色);
    (e) color 为可解析 hex 且白底对比度 >= 4.5(67C/67D 算法)。
    """
    problems: list[str] = []
    color = el.get("color")
    deco = el.get("decoration_color")
    thick = el.get("thickness")

    if not deco:
        problems.append("missing text-decoration-color")
    if not color:
        problems.append("missing color")
    if deco and color and deco.lower() != color.lower():
        problems.append(f"text-decoration-color {deco!r} != color {color!r}")
    if thick is None:
        problems.append("missing text-decoration-thickness")
    else:
        try:
            px = float(thick.rstrip("px").strip())
            if px > 1.0:
                problems.append(f"text-decoration-thickness {thick} > 1px")
        except ValueError:
            problems.append(f"text-decoration-thickness {thick!r} not parseable")
    if deco and deco.lower() == _HAMMER_PRIMARY_HEX.lower():
        problems.append("text-decoration-color is theme primary #B3593B")
    rgb = _hex_to_rgb(color or "")
    if rgb is None:
        problems.append(f"color {color!r} not a parseable hex")
    else:
        ratio = _contrast_ratio(rgb)
        if ratio < _MIN_CONTRAST:
            problems.append(f"contrast {ratio:.2f}:1 < {_MIN_CONTRAST}:1")
    return (not problems, problems)


def _strike_check(html: str) -> tuple[bool, bool, int]:
    """返回 (strike_props_ok, strike_bad, line_through_count)。

    - line_through == 0 -> props ok(保持原语义);
    - 任一 line-through 元素 low-contrast 文字色(rgba(202,202,199,0.35))-> bad;
      该禁用无豁免(OBS-98 收紧:不再因 decoration-color=#B3593B 而放行)。
    - props ok 要求每个 line-through 元素都通过形态语义断言。
    """
    elements = _parse_strike_elements(html)
    line_through = len(elements)
    if line_through == 0:
        return True, False, 0
    strike_bad = any(
        _FORBIDDEN_STRIKE_TEXT_RGBA in (el.get("color") or "").replace(" ", "")
        for el in elements)
    props_ok = all(_strike_element_ok(el)[0] for el in elements)
    return props_ok, strike_bad, line_through


def _img_type_occurrences(html: str, shadow_token: str) -> int:
    """OBS-123(档71C-2):图片组件指纹去魔数窗口 —— 改结构包含。

    定位含该类型令牌的 <section 开标签 → 深度计数向后找配对 </section> →
    要求 <img 出现在该区间内部。与旧「令牌后 400 字符窗口」(OBS-109) 不同:
    section 闭合之后的 <img 不再误命中;alert/quote 等纯文本组件共享阴影
    令牌但无 <img,仍不计入。无 <section 包裹的令牌不计(组件产物必在
    section 容器内)。"""
    n = 0
    start = 0
    while True:
        i = html.find(shadow_token, start)
        if i < 0:
            break
        sec = html.rfind("<section", 0, i)
        if sec < 0:
            start = i + len(shadow_token)
            continue
        end = _matching_section_end(html, sec)
        if end >= 0 and "<img" in html[i:end]:
            n += 1
        start = i + len(shadow_token)
    return n


def _matching_section_end(html: str, open_pos: int) -> int:
    """从 <section 开标签位置向后深度计数,返回配对 </section> 位置;无配对返回 -1。"""
    depth = 0
    pos = open_pos
    while True:
        o = html.find("<section", pos)
        c = html.find("</section>", pos)
        if o < 0 and c < 0:
            return -1
        if o >= 0 and (c < 0 or o < c):
            depth += 1
            pos = o + len("<section")
        else:
            depth -= 1
            pos = c + len("</section>")
            if depth == 0:
                return c


def validate(final_html: str | Path, expected_chapters: int | None = None,
             usage_out: str | Path | None = None,
             exec_evidence: dict | None = None,
             lock_entry: dict | None = None,
             network_mode: str | None = None,
             image_shortfall: int = 0) -> tuple[int, dict]:  # 76C:少图交付时图片类型门槛降级
    html = Path(final_html).read_text(encoding="utf-8")
    ev = {}
    for cid, fp in FINGERPRINTS.items():
        occ = html.count(fp)
        idx = html.find(fp)
        frag = _sha(html[max(0, idx - 40): idx + len(fp) + 200]) if idx >= 0 else None
        ev[cid] = {"occurrences": occ, "final_fragment_sha256": frag}

    cover = ev["cover_breaking"]["occurrences"]
    toc = ev["toc_scroll"]["occurrences"]
    chapters = ev["chapter_title"]["occurrences"]
    sig = ev["signature"]["occurrences"]
    footer = ev["footer_cta"]["occurrences"]
    toc_dynamic_ok = bool(expected_chapters) and all(
        f"PART {i:02d}" in html for i in range(1, expected_chapters + 1))
    img_types = [c for c in ("image_2a_standard", "image_media_text_card")
                 if _img_type_occurrences(html, FINGERPRINTS[c]) > 0]
    hammer_primary = _HAMMER_PRIMARY_HEX in html
    moyu_absent = "#059669" not in html
    fallback_used = (not hammer_primary) or (not moyu_absent)
    # OBS-98:形态语义 strike 判定(逐元素),不再硬编码 #B3593B/1.5px。
    strike_props_ok, strike_bad, line_through = _strike_check(html)
    chapters_ok = bool(expected_chapters) and (chapters == expected_chapters)

    # ── P0#8/hotfix2: theme identity is only OFFICIAL with REAL execution proof ──
    # We do not trust lock fields alone. The gzh execution receipt must name the
    # render entry + component source, and their ACTUAL on-disk sha256 (recomputed
    # here) must equal BOTH the receipt's recorded value AND the lock. Live also
    # requires the installed runtime root + runtime-manifest hash to match the
    # lock, and a commit present in an install-source proof.
    exec_present = exec_evidence is not None
    official_call = bool(exec_evidence and exec_evidence.get("official_gzh_call"))
    locked_entry_sha = (lock_entry or {}).get("entrypoint_sha256") or (lock_entry or {}).get("render_entry_sha256")
    locked_component_sha = (lock_entry or {}).get("component_source_sha256")
    locked_commit = (lock_entry or {}).get("full_commit_sha")
    locked_root = (lock_entry or {}).get("skill_root_sha256")
    locked_manifest = (lock_entry or {}).get("runtime_manifest_sha256")

    def _sha_file(path):
        # newline-normalized content hash, IDENTICAL to the lock's _file_sha and
        # to compute_root_sha, so entry/component matching holds cross-platform.
        try:
            if not (path and Path(path).is_file()):
                return None
            data = Path(path).read_bytes()
            if b"\x00" not in data:
                data = data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
            return hashlib.sha256(data).hexdigest()
        except OSError:
            return None

    ev_ev = exec_evidence or {}
    entry_path = ev_ev.get("render_entry_path") or ev_ev.get("entry_path")
    comp_path = ev_ev.get("component_source_path")
    actual_entry_sha = _sha_file(entry_path)
    actual_comp_sha = _sha_file(comp_path)
    # entry: actual file hash must equal lock AND the receipt-recorded value
    entry_hash_ok = bool(locked_entry_sha and actual_entry_sha == locked_entry_sha
                         and ev_ev.get("entry_sha256") == actual_entry_sha)
    component_hash_ok = bool(locked_component_sha and actual_comp_sha == locked_component_sha)
    # live: installed runtime root + manifest hash must match the lock AND the
    # external install receipt (P0#1 three-way: recomputed == receipt == lock).
    receipt_root = ev_ev.get("install_receipt_root_sha256")
    receipt_manifest = ev_ev.get("install_receipt_manifest_sha256")
    if network_mode in ("live", "integration"):
        cur_root = ev_ev.get("installed_root_sha256")
        cur_manifest = ev_ev.get("installed_runtime_manifest_sha256")
        root_ok = bool(locked_root and cur_root == locked_root and cur_root == receipt_root)
        manifest_ok = bool(locked_manifest and cur_manifest == locked_manifest
                           and cur_manifest == receipt_manifest)
    else:
        cur_root = cur_manifest = None
        root_ok = manifest_ok = False
    receipt_present = bool(ev_ev.get("install_source_commit"))
    commit_ok = bool(locked_commit and ev_ev.get("install_source_commit") == locked_commit)
    official_ok = (official_call and entry_hash_ok and component_hash_ok
                   and root_ok and manifest_ok and commit_ok
                   and network_mode in ("live", "integration"))

    structure_ok = (cover == 1 and toc == 1 and toc_dynamic_ok and chapters_ok and sig == 1
                    and footer == 1 and len(img_types) >= 2 and not fallback_used
                    and not strike_bad and strike_props_ok)
    # 76C(用户裁决 2026-08-11):图片数量不再是发文限制条件——少图交付
    # (image_shortfall>0)时图片组件类型门槛 2→1 降级,默认(无短少)行为不变。
    img_type_min = 1 if image_shortfall > 0 else 2
    structure_ok = (cover == 1 and toc == 1 and toc_dynamic_ok and chapters_ok and sig == 1
                    and footer == 1 and len(img_types) >= img_type_min and not fallback_used
                    and not strike_bad and strike_props_ok)

    report = {
        "HAMMER_COVER_BREAKING_COUNT": cover,
        "HAMMER_TOC_SCROLL_COUNT": toc,
        "HAMMER_TOC_MATCHES_CHAPTERS": toc_dynamic_ok,
        "HAMMER_CHAPTER_TITLE_COUNT": chapters,
        "expected_chapters": expected_chapters,
        "HAMMER_SIGNATURE_COUNT": sig,
        "HAMMER_FOOTER_CTA_COUNT": footer,
        "OFFICIAL_IMAGE_COMPONENT_TYPES": len(img_types),
        "image_types_present": img_types,
        "IMAGE_TYPE_MIN": img_type_min,
        "image_shortfall": image_shortfall,
        "THEME_FALLBACK_USED": fallback_used,
        "LINE_THROUGH_COUNT": line_through,
        "strikethrough_forbidden_rgba_present": strike_bad,
        "strikethrough_props_ok": strike_props_ok,
        "GZH_EXECUTION_EVIDENCE_PRESENT": exec_present,
        "OFFICIAL_GZH_CALL": official_call,
        "RENDER_ENTRY_HASH_MATCHES_LOCK": entry_hash_ok,
        "COMPONENT_SOURCE_HASH_MATCHES_LOCK": component_hash_ok,
        "INSTALLED_ROOT_MATCHES_LOCK": root_ok,
        "RUNTIME_MANIFEST_MATCHES_LOCK": manifest_ok,
        "INSTALL_RECEIPT_PRESENT": receipt_present,
        "INSTALL_RECEIPT_ROOT_MATCHES": bool(receipt_root and receipt_root == cur_root),
        "INSTALL_SOURCE_COMMIT_MATCHES_LOCK": commit_ok,
        "actual_render_entry_sha256": actual_entry_sha,
        "actual_component_source_sha256": actual_comp_sha,
        "GZH_COMMIT_LOCKED": locked_commit,
        "structure_ok": structure_ok,
        "components": ev,
    }
    if structure_ok and official_ok:
        report["THEME_IDENTITY"] = "PASS"           # official gzh call, hash-anchored
        code = 0
    elif structure_ok and exec_present and network_mode in ("fake_live", "offline_fixture"):
        # simulated executor: orchestration accepted, NEVER claimed official
        report["THEME_IDENTITY"] = "SIMULATED"
        report["note"] = ("simulated gzh executor — structure verified, but this is NOT "
                          "an official gzh-design call and must not be reported as one")
        code = 0
    else:
        report["THEME_IDENTITY"] = "FAIL"
        if structure_ok and not exec_present:
            report["fail_reason"] = "fingerprints present but NO gzh execution evidence (copied HTML)"
        code = 1

    if usage_out:
        usage = {"source": "reverse-parsed from final.html (program-generated, not hand-declared)",
                 "theme": "smartisan / 锤子风格",
                 "structural_components": {c: ev[c]["occurrences"] for c in
                                           ("cover_breaking", "toc_scroll", "chapter_title", "signature", "footer_cta")},
                 "image_components": {c: ev[c]["occurrences"] for c in img_types},
                 "official_image_component_types": len(img_types),
                 "theme_fallback_used": fallback_used,
                 "official_gzh_call": official_call}
        Path(usage_out).write_text(json.dumps(usage, ensure_ascii=False, indent=2), encoding="utf-8")
    return code, report


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--final-html", required=True)
    ap.add_argument("--expected-chapters", type=int, default=None)
    ap.add_argument("--usage-out", default=None)
    ap.add_argument("--report-out", default=None)
    a = ap.parse_args(argv)
    code, report = validate(a.final_html, a.expected_chapters, a.usage_out)
    if a.report_out:
        Path(a.report_out).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "components"}, ensure_ascii=False))
    print("THEME_IDENTITY=", report["THEME_IDENTITY"])
    return code


if __name__ == "__main__":
    sys.exit(main())
