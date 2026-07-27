"""Stage output production for live / fake_live. This REPLACES dev1's run_live
NotImplementedError stubs with real machinery:

- agent stages     -> write a handshake request; fake_live fulfills it via a
  FakeAgent and verifies the ACK; live with no ACK yet returns await_agent
  (clean pause, not a crash).
- subprocess stages -> run the resolved entry script for REAL, then run the
  official sub-skill validator for REAL (captured in meta['official_validator']).
- wechat stage     -> run the fake WeChat client (fake_live) / audited draft
  module (live) for REAL; draft-only, no publish/delete.

Returns (output_paths, meta). No NotImplementedError anywhere.
"""
from __future__ import annotations

from pathlib import Path

from . import execmodel as EM
from . import agent_handshake as AH
from .subprocess_runner import run_script

AGENT_INSTRUCTIONS = {
    "aihot": "Query AI HOT (anonymous read-only), aggregate + dedup; do not write the article.",
    "super_writer": "Run Super Writer Material-Heavy Full Mode; FULL_MODE_VALIDATOR_EXIT must be 0.",
    "zh_human_writing": "De-AI the Super Writer article only; freeze final_article.md (no new facts).",
}


def _frozen_article(ctx) -> Path:
    return Path(ctx.run_dir) / "zh_human_writing" / "final_article.md"


def produce(ctx, stage: str, state) -> tuple[list, dict]:
    kind = EM.STAGE_EXEC[stage]
    sd = ctx.stage_dir(stage)
    expected = EM.EXPECTED_OUTPUTS[stage]
    if kind == EM.AGENT:
        return _agent(ctx, stage, sd, expected, state)
    if kind == EM.SUBPROC:
        return _subprocess(ctx, stage, sd, expected, state)
    if kind == EM.WECHAT:
        return _wechat(ctx, stage, sd, expected, state)
    raise ValueError(f"unknown exec kind for {stage}")


def _agent(ctx, stage, sd, expected, state):
    inputs = {"topic": state.topic, "frozen_article_sha256": state.final_article_sha256}
    AH.write_request(sd, stage, EM.AGENT, AGENT_INSTRUCTIONS.get(stage, ""), expected, inputs)
    if ctx.network_mode == "fake_live":
        agent = ctx.fake_agent or AH.FakeAgent(ctx.fixture_dir)
        agent.fulfill(sd, stage, expected)
    ok, hs = AH.verify_ack(sd, stage, expected)
    outputs = [sd / o for o in expected if (sd / o).is_file()]
    meta = {"exec_kind": EM.AGENT, "handshake": hs, "invoked_entrypoint": f"agent_handshake:{stage}",
            "entrypoint_path": None, "entrypoint_sha256": None}
    if not ok:
        meta["await_agent"] = (hs.get("HANDSHAKE") == "AWAITING_AGENT")
        meta["handshake_failed"] = not meta["await_agent"]
    return outputs, meta


def _validator_args(stage, sd):
    if stage == "media_enrichment":
        return ["--media-manifest", str(sd / "media_manifest.json"),
                "--bindings", str(sd / "article_image_bindings.json")]
    if stage == "gzh_design":
        return ["--html", str(sd / "final.html")]
    return []


def _subprocess(ctx, stage, sd, expected, state):
    entry, validator = EM.resolve_entry(stage, ctx.network_mode, ctx.skills_home)
    args = ["--stage-dir", str(sd), "--article", str(_frozen_article(ctx))]
    if stage == "media_enrichment":
        args += ["--article-sha", state.final_article_sha256 or ""]
    if stage == "gzh_design":
        args += ["--bindings", str(Path(ctx.run_dir) / "media_enrichment" / "article_image_bindings.json")]
    run = run_script(entry, args, timeout=180)
    meta = {"exec_kind": EM.SUBPROC, "invoked_entrypoint": str(entry),
            "entrypoint_path": run["script_path"], "entrypoint_sha256": run["script_sha256"],
            "entry_run": {"exit_code": run["exit_code"], "elapsed": run["elapsed_seconds"],
                          "stderr": run["stderr"][-400:] if run["exit_code"] else ""}}
    if validator:
        vr = run_script(validator, _validator_args(stage, sd), timeout=120)
        meta["official_validator"] = {"path": vr["script_path"], "sha256": vr["script_sha256"],
                                      "exit_code": vr["exit_code"]}
    outputs = [sd / o for o in expected if (sd / o).is_file()]
    return outputs, meta


def _wechat(ctx, stage, sd, expected, state):
    if not ctx.create_wechat_draft:
        return [], {"exec_kind": EM.WECHAT, "skipped": "create_wechat_draft=False"}
    entry, _ = EM.resolve_entry(stage, ctx.network_mode, ctx.skills_home)
    html = Path(ctx.run_dir) / "gzh_design" / "final.html"
    run = run_script(entry, ["--stage-dir", str(sd), "--html", str(html)], timeout=120)
    meta = {"exec_kind": EM.WECHAT, "invoked_entrypoint": str(entry),
            "entrypoint_path": run["script_path"], "entrypoint_sha256": run["script_sha256"],
            "entry_run": {"exit_code": run["exit_code"], "stderr": run["stderr"][-400:] if run["exit_code"] else ""}}
    outputs = [sd / o for o in expected if (sd / o).is_file()]
    return outputs, meta
