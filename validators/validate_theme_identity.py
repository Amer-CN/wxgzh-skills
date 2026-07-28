#!/usr/bin/env python3
"""Theme-identity validator (hammer / smartisan). NOT an HTML-syntax check.

Reverse-parses the final HTML for structural fingerprints that appear verbatim
in BOTH the official gzh-design source AND the HTML, asserting official-component
counts, image-component types, theme fallback, and strikethrough safety.
Also emits a program-generated component_usage_report (never hand-declared).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

# fingerprint -> literal substring present in official source + rendered HTML
FINGERPRINTS = {
    "cover_breaking": "border-radius:20px;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,0.06)",
    "toc_scroll": "overflow-x:scroll;-webkit-overflow-scrolling:touch;white-space:nowrap",
    "chapter_title": "font-size:28px;font-weight:900;color:",
    "signature": "热闹是 AI 的，淡定可以是我们的。",
    "footer_cta": "radial-gradient(circle at center,",
    "image_2a_standard": "box-shadow:0 4px 12px -2px rgba(0,0,0,0.08)",
    "image_media_text_card": "0 4px 16px -4px rgba(179,89,59,0.10)",
}


def _sha(t: str) -> str:
    return hashlib.sha256(t.encode("utf-8")).hexdigest()


def validate(final_html: str | Path, expected_chapters: int | None = None,
             usage_out: str | Path | None = None,
             exec_evidence: dict | None = None,
             lock_entry: dict | None = None,
             network_mode: str | None = None) -> tuple[int, dict]:
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
    img_types = [c for c in ("image_2a_standard", "image_media_text_card") if ev[c]["occurrences"] > 0]
    hammer_primary = "#B3593B" in html
    moyu_absent = "#059669" not in html
    fallback_used = (not hammer_primary) or (not moyu_absent)
    line_through = html.count("line-through")
    # A strikethrough is FORBIDDEN only when struck text uses the low-contrast
    # colour WITHOUT the official hammer strike decoration on the SAME element.
    # The hammer theme legitimately uses rgba(202,202,199,0.35) elsewhere (PART
    # labels, dividers), so a global substring match would false-positive on a
    # real render — scope the check to line-through elements (P0#1 live-proof).
    _nz = html.replace(" ", "")
    strike_bad = any(
        ("line-through" in st and "color:rgba(202,202,199,0.35)" in st
         and "text-decoration-color:#B3593B" not in st)
        for st in re.findall(r'style="([^"]*)"', _nz))
    strike_props_ok = (line_through == 0) or (
        "text-decoration-color:#B3593B" in html and "text-decoration-thickness:1.5px" in html)
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
    if network_mode == "live":
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
                   and root_ok and manifest_ok and commit_ok and network_mode == "live")

    structure_ok = (cover == 1 and toc == 1 and toc_dynamic_ok and chapters_ok and sig == 1
                    and footer == 1 and len(img_types) >= 2 and not fallback_used
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
