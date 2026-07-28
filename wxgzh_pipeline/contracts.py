"""Load stage contracts (YAML) + JSON schemas, validate handoff objects, and
ENFORCE each stage's YAML contract against real on-disk outputs (dev2)."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import jsonschema
import yaml

from . import execmodel as EM

SKILL_ROOT = Path(__file__).resolve().parents[1]

CONTRACT_FILES = {
    "aihot": "01_aihot.yaml",
    "super_writer": "02_super_writer.yaml",
    "zh_human_writing": "03_zh_human_writing.yaml",
    "media_enrichment": "04_media_enrichment.yaml",
    "gzh_design": "05_gzh_design.yaml",
    "wechat_draft": "06_wechat_draft.yaml",
}

STAGE_ORDER = {"aihot": 1, "super_writer": 2, "zh_human_writing": 3,
               "media_enrichment": 4, "gzh_design": 5, "wechat_draft": 6}

# stage -> lock key of the sub-skill that actually executes it
# (wechat_draft reuses gzh-design's publish_wechat_draft.py)
STAGE_LOCK_SKILL = {"aihot": "aihot", "super_writer": "super-writer",
                    "zh_human_writing": "zh-human-writing",
                    "media_enrichment": "media-enrichment",
                    "gzh_design": "gzh-design", "wechat_draft": "gzh-design"}


@lru_cache(maxsize=None)
def load_contract(stage: str) -> dict:
    return yaml.safe_load((SKILL_ROOT / "contracts" / CONTRACT_FILES[stage]).read_text(encoding="utf-8"))


@lru_cache(maxsize=None)
def load_schema(name: str) -> dict:
    return json.loads((SKILL_ROOT / "schemas" / f"{name}.schema.json").read_text(encoding="utf-8"))


def validate(obj: dict, schema_name: str) -> list[str]:
    """Return a list of validation error messages ([] == valid)."""
    schema = load_schema(schema_name)
    errs = []
    v = jsonschema.Draft7Validator(schema)
    for e in sorted(v.iter_errors(obj), key=lambda e: list(e.absolute_path)):
        loc = "/".join(str(p) for p in e.absolute_path) or "<root>"
        errs.append(f"{loc}: {e.message}")
    return errs


def is_valid(obj: dict, schema_name: str) -> bool:
    return not validate(obj, schema_name)


def enforce_contract(stage: str, sd, ctx=None, state=None) -> tuple[bool, dict]:
    """FULLY consume the stage's YAML contract and enforce it against real
    on-disk state (P0#7): stage/order, must_run_after receipt, real upstream
    inputs, frozen-article hash, sub-skill version + commit SHA, official entry +
    validator presence, allowed/forbidden side-effects, image counts, serial
    upload, per-bound-image rules, and theme fallback. Not just file existence."""
    import hashlib
    sd = Path(sd)
    c = load_contract(stage)
    problems = []
    checks = {}

    def chk(name, ok, detail=""):
        checks[name] = {"ok": bool(ok), "detail": detail}
        if not ok:
            problems.append(f"{name}: {detail}" if detail else name)

    chk("stage_matches", c.get("stage") == stage, f"{c.get('stage')} != {stage}")
    chk("order_matches", c.get("order") == STAGE_ORDER.get(stage),
        f"{c.get('order')} != {STAGE_ORDER.get(stage)}")

    expected = list(EM.EXPECTED_OUTPUTS.get(stage, []))
    missing_out = [o for o in expected if not (sd / o).is_file()]
    chk("required_outputs_present", not missing_out, f"missing {missing_out}")

    run_dir = Path(ctx.run_dir) if ctx else sd.parent

    # must_run_after: the named prior stage must have a receipt on disk.
    must_after = c.get("must_run_after")
    if must_after:
        chk("must_run_after_receipt", (run_dir / must_after / "stage_receipt.json").is_file(),
            f"{must_after} receipt missing")

    # real upstream inputs present (P0#2 alignment)
    ups = EM.UPSTREAM_INPUTS.get(stage, [])
    missing_in = [rel for rel in ups if not (run_dir / rel).is_file()]
    chk("real_inputs_present", not missing_in, f"missing inputs {missing_in}")

    # frozen-article hash
    if c.get("depends_on_freeze") and state is not None:
        fa = run_dir / "zh_human_writing" / "final_article.md"
        want = state.final_article_sha256
        cur = hashlib.sha256(fa.read_bytes()).hexdigest() if fa.is_file() else None
        chk("frozen_article_hash", bool(want) and cur == want,
            f"frozen sha mismatch want={str(want)[:12]} cur={str(cur)[:12]}")

    # sub-skill identity: version + commit SHA recorded in the lock
    if ctx is not None:
        from . import skill_discovery as SD
        lock = SD.load_lock(SKILL_ROOT).get("skills", {})
        skill = STAGE_LOCK_SKILL.get(stage)
        locked = lock.get(skill, {}) if skill else {}
        if skill and skill != "aihot":
            chk("locked_version_present", bool(locked.get("skill_version")),
                f"{skill} version not locked")
            chk("locked_commit_present", bool(locked.get("full_commit_sha")),
                f"{skill} full_commit_sha not locked")

    # official entry + validator resolvable
    if ctx is not None and EM.STAGE_EXEC.get(stage) in (EM.SUBPROC, EM.WECHAT):
        entry, validator = EM.resolve_entry(stage, ctx.network_mode, ctx.skills_home)
        chk("official_entry_present", bool(entry) and Path(entry).is_file(),
            f"entry {entry}")
        if validator is not None:
            chk("official_validator_present", Path(validator).is_file(), f"validator {validator}")

    # side-effects allow/deny
    if stage == "wechat_draft":
        res = sd / "draft_creation_result.json"
        if res.is_file():
            r = json.loads(res.read_text(encoding="utf-8"))
            chk("draft_only", r.get("draft_only") is True and r.get("formally_published") is False,
                "formal publish / non-draft detected")
            chk("no_mass_send", not r.get("mass_send") and not r.get("scheduled"), "mass/scheduled")

    # media: counts, serial upload, per-bound-image rules
    if stage == "media_enrichment":
        man_p, bnd_p = sd / "media_manifest.json", sd / "article_image_bindings.json"
        if man_p.is_file() and bnd_p.is_file():
            man = json.loads(man_p.read_text(encoding="utf-8"))
            bnd = json.loads(bnd_p.read_text(encoding="utf-8"))
            by_id = {x["asset_id"]: x for x in man.get("assets", [])}
            body = bnd.get("body_images", [])
            counts = c.get("counts", {})
            cmin = counts.get("BODY_IMAGES_MIN", 6)
            chk("body_images_min", len(body) >= cmin, f"{len(body)} < {cmin}")
            per = c.get("per_bound_image", {})
            host = per.get("remote_url_host", "mmbiz.qpic.cn")
            bad = []
            for b in body:
                m = by_id.get(b.get("asset_id"))
                up = (m or {}).get("upload", {})
                if not m or m.get("decision") != per.get("decision", "eligible"):
                    bad.append(f"{b.get('asset_id')}:decision")
                elif up.get("status") != per.get("upload_status", "success"):
                    bad.append(f"{b.get('asset_id')}:upload")
                elif host not in (up.get("remote_url") or ""):
                    bad.append(f"{b.get('asset_id')}:host")
                elif per.get("binding_sha256_equals_manifest_sha256", True) and b.get("sha256") != m.get("sha256"):
                    bad.append(f"{b.get('asset_id')}:sha")
            chk("per_bound_image_rules", not bad, f"{bad[:4]}")
            chk("upload_serial_declared", c.get("upload", {}).get("serial") is True, "serial not declared")

    # gzh: theme fallback must be false + THEME_IDENTITY gate present
    if stage == "gzh_design":
        tir = sd / "theme_identity_report.json"
        final_html = sd / "final.html"
        if final_html.is_file():
            html = final_html.read_text(encoding="utf-8")
            fallback_forbidden = c.get("theme", {}).get("THEME_FALLBACK_ALLOWED") is False
            chk("no_theme_fallback", ("#B3593B" in html) and ("#059669" not in html) if fallback_forbidden else True,
                "hammer primary absent or moyu-green present")
        if tir.is_file():
            rep = json.loads(tir.read_text(encoding="utf-8"))
            chk("theme_fallback_not_used", rep.get("theme_fallback_used") in (False, None), "fallback used")

    ok = not problems
    return ok, {"CONTRACT": "PASS" if ok else "FAIL", "stage": stage,
                "contract_file": CONTRACT_FILES[stage], "required_outputs": expected,
                "must_run_after": must_after, "checks": checks, "problems": problems}
