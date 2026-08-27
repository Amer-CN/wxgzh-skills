"""77J validator alignment, enforced registry precheck, and page-meta evidence."""

import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

from wxgzh_pipeline import producers as PR
from wxgzh_pipeline.approval_evidence import build_approval_readiness

SW_SCRIPTS = Path(__file__).resolve().parents[2] / "super-writer" / "scripts"


def _load_validator(name):
    spec = importlib.util.spec_from_file_location(name, SW_SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_obs323_runtime_policy_defaults_match_explicit_profile(tmp_path):
    val = _load_validator("validate_article_length")
    profile = tmp_path / "generation-profile.yaml"
    profile.write_text(
        "mode: full\narticle_mode: medium\nlength_mode: medium\n"
        "target_visible_chars: 3000\nacceptable_min: 2500\nacceptable_max: 4000\n",
        encoding="utf-8")
    args = SimpleNamespace(full_mode=True, generation_profile=str(profile),
                           article_mode=None, target_visible_chars=None,
                           acceptable_min=None, acceptable_max=None)
    policy = val._apply_runtime_policy_defaults(args)
    assert policy == {"article_mode": "medium", "target_visible_chars": 3000,
                      "acceptable_min": 2500, "acceptable_max": 4000}
    assert (args.article_mode, args.target_visible_chars) == ("medium", 3000)
    explicit = SimpleNamespace(full_mode=True, generation_profile=str(profile),
                               article_mode="long", target_visible_chars=5000,
                               acceptable_min=4500, acceptable_max=6500)
    val._apply_runtime_policy_defaults(explicit)
    assert (explicit.article_mode, explicit.target_visible_chars) == ("long", 5000)


def test_obs324_bad_registry_shape_is_rejected_by_precheck(tmp_path):
    val = _load_validator("validate_single_product")
    registry = {
        "claims": [{"claim_id": "C-01", "claim_text": "text",
                    "material_id": ["M-01"], "source_url": "https://s.example/a",
                    "source_excerpt": "e", "chart_group": ["group"]}],
        "materials": [{"material_id": ["M-01"], "dedup_id": "d-1",
                       "source_url": "https://s.example/a", "title": "t",
                       "aihot_permalink": "https://aihot.example/a"}],
    }
    path = tmp_path / "registry.json"
    path.write_text(json.dumps(registry), encoding="utf-8")
    errors, _ = val.check_registry(path)
    joined = "\n".join(errors)
    assert "material_id" in joined and "必须是 string" in joined
    assert "chart_group" in joined and "必须是 string" in joined


def test_obs324_registry_precheck_is_in_official_ack_chain(tmp_path):
    sd = tmp_path / "super_writer"
    sd.mkdir()
    (sd / "generation-profile.yaml").write_text(
        "mode: full\narticle_mode: medium\nlength_mode: medium\n"
        "target_visible_chars: 3000\nacceptable_min: 2500\nacceptable_max: 4000\n",
        encoding="utf-8")
    ctx = SimpleNamespace(run_dir=tmp_path, network_mode="live", skills_home=tmp_path)
    validators = PR._agent_validator_args("super_writer", ctx, sd)
    precheck = next(item for item in validators
                    if item[1] == "scripts/validate_single_product.py" and "registry" in item[2])
    argv = precheck[2]
    assert "--product" in argv and "registry" in argv
    assert str(tmp_path / "aihot" / "deduplicated_items.json") in argv
    assert str(tmp_path / "super_writer" / "material-ledger.yaml") in argv


def _manifest(assets):
    return {"run_id": "77j", "input": {"claims_total": 1}, "errors": [],
            "assets": assets}


def _asset(aid, url, method):
    return {"asset_id": aid, "decision": "review_required",
            "extraction_method": method, "resolved_original_url": url,
            "source_page_url": "https://source.example/page",
            "page_region": "unknown",
            "page_position": {"known": False, "heading": None, "level": None},
            "content_description": f"Source page media {aid}",
            "content_description_source": "page_context"}


def test_obs325_page_declared_images_pass_with_page_meta(tmp_path):
    og_url = "https://cdn.example/og.jpg"
    background_url = "https://cdn.example/background.jpg"
    manifest = _manifest([
        _asset("A-OG", og_url, "og:image"),
        _asset("A-BG", background_url, "background-image"),
    ])
    run_dir = tmp_path / "run"
    discover = run_dir / "media_enrichment" / "discover"
    discover.mkdir(parents=True)
    (discover / "media_manifest.json").write_text(
        json.dumps(manifest), encoding="utf-8")
    html = (
        '<html><head><title>Page title</title>'
        f'<meta property="og:image" content="{og_url}"></head><body>'
        f'<div style="background-image:url({background_url})"></div></body></html>')
    readiness = build_approval_readiness(run_dir, claim_texts=["claim"],
                                         html_provider=lambda url: html)
    by_id = {row["asset_id"]: row for row in readiness["assets"]}
    assert by_id["A-OG"]["approvable"] is True
    assert by_id["A-OG"]["page_position"]["level"] == "page-meta"
    assert by_id["A-BG"]["approvable"] is True
    assert by_id["A-BG"]["page_position"]["level"] == "page-meta"


def test_obs325_body_image_without_section_still_blocked(tmp_path):
    url = "https://cdn.example/body.jpg"
    manifest = _manifest([_asset("A-BODY", url, "body-img")])
    run_dir = tmp_path / "run"
    discover = run_dir / "media_enrichment" / "discover"
    discover.mkdir(parents=True)
    (discover / "media_manifest.json").write_text(
        json.dumps(manifest), encoding="utf-8")
    html = ('<html><head><title>Page</title></head><body>'
            f'<img src="{url}"></body></html>')
    readiness = build_approval_readiness(run_dir, claim_texts=["claim"],
                                         html_provider=lambda source: html)
    row = readiness["assets"][0]
    assert row["approvable"] is False
    assert row["page_position"]["known"] is False
