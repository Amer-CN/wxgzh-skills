"""Agent-driven stage handshake — dev2-hotfix1.

The orchestrator writes a handshake REQUEST that embeds: run_id, stage,
stage_request.json sha256, ALL upstream input hashes, expected outputs, the
sub-skill identity (name/version/root sha) and the stage contract sha256. The
agent produces the outputs and writes an ACK whose token binds the REQUEST FILE
BYTES + the CURRENT produced output hashes. Verification recomputes everything
from disk, so:

- editing the request                -> request sha changes -> token mismatch -> FAIL
- editing any produced output        -> produced hash changes -> token mismatch -> FAIL
- editing any UPSTREAM input after ACK -> upstream drift check -> FAIL
- live mode with no ACK yet          -> AWAITING_AGENT (clean pause, not a crash)
- fake_live                          -> FakeAgent fulfills deterministically
"""
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

from .state import atomic_write_json, sha256_file

REQUEST_FILE = "agent_handshake_request.json"
ACK_FILE = "agent_handshake.json"
DOC_FILE = "HANDSHAKE.md"


def _canon(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def token(*, run_id, stage, request_sha256, stage_request_sha256, upstream_hashes,
          expected_outputs, produced_hashes, skill_identity, contract_sha256) -> str:
    basis = _canon({
        "run_id": run_id, "stage": stage,
        "request_sha256": request_sha256,
        "stage_request_sha256": stage_request_sha256,
        "upstream_hashes": upstream_hashes or {},
        "expected_outputs": sorted(expected_outputs),
        "produced_hashes": produced_hashes,
        "skill_identity": skill_identity or {},
        "contract_sha256": contract_sha256,
    })
    return hashlib.sha256(basis.encode("utf-8")).hexdigest()


def write_request(sd: Path, stage: str, skill: str, instructions: str,
                  expected_outputs, inputs: dict, *, run_id=None,
                  upstream_hashes=None, stage_request_sha256=None,
                  skill_identity=None, contract_sha256=None) -> dict:
    sd = Path(sd)
    req = {"run_id": run_id, "stage": stage, "skill": skill, "kind": "agent_handshake",
           "instructions": instructions, "expected_outputs": list(expected_outputs),
           "inputs": inputs, "upstream_hashes": upstream_hashes or {},
           "stage_request_sha256": stage_request_sha256,
           "skill_identity": skill_identity or {"skill_name": skill},
           "contract_sha256": contract_sha256}
    atomic_write_json(sd / REQUEST_FILE, req)
    (sd / DOC_FILE).write_text(
        f"# Agent handshake — {stage}\n\nSkill: `{skill}`\n\n{instructions}\n\n"
        f"Produce these files in this directory, then write `{ACK_FILE}`:\n"
        + "".join(f"- `{o}`\n" for o in expected_outputs)
        + "\nThe ACK token binds the request bytes + upstream input hashes + the "
        "produced file hashes; any post-ACK edit invalidates the handshake.\n",
        encoding="utf-8", newline="\n")
    return req


def _token_from_disk(sd: Path, stage: str, expected_outputs) -> tuple[str | None, dict]:
    """Recompute the token basis fully from CURRENT on-disk state."""
    sd = Path(sd)
    reqp = sd / REQUEST_FILE
    if not reqp.is_file():
        return None, {}
    req = json.loads(reqp.read_text(encoding="utf-8"))
    produced = {o: sha256_file(sd / o) for o in expected_outputs if (sd / o).is_file()}
    t = token(run_id=req.get("run_id"), stage=stage,
              request_sha256=sha256_file(reqp),
              stage_request_sha256=req.get("stage_request_sha256"),
              upstream_hashes=req.get("upstream_hashes"),
              expected_outputs=expected_outputs, produced_hashes=produced,
              skill_identity=req.get("skill_identity"),
              contract_sha256=req.get("contract_sha256"))
    return t, req


def write_ack(sd: Path, stage: str, expected_outputs, agent_id: str = "agent") -> dict:
    sd = Path(sd)
    t, req = _token_from_disk(sd, stage, expected_outputs)
    produced = {o: sha256_file(sd / o) for o in expected_outputs if (sd / o).is_file()}
    ack = {"run_id": req.get("run_id"), "stage": stage, "agent_id": agent_id,
           "produced_files": sorted(produced), "produced_hashes": produced,
           "handshake_token": t}
    atomic_write_json(sd / ACK_FILE, ack)
    return ack


def verify_ack(sd: Path, stage: str, expected_outputs,
               run_dir: Path | None = None) -> tuple[bool, dict]:
    sd = Path(sd)
    ackp = sd / ACK_FILE
    if not ackp.is_file():
        return False, {"HANDSHAKE": "AWAITING_AGENT", "reason": f"{ACK_FILE} not present yet"}
    ack = json.loads(ackp.read_text(encoding="utf-8"))
    missing = [o for o in expected_outputs if not (sd / o).is_file()]
    recomputed, req = _token_from_disk(sd, stage, expected_outputs)
    token_ok = recomputed is not None and ack.get("handshake_token") == recomputed

    # upstream drift: recompute every upstream input hash from disk and compare
    # with what the request bound at request time.
    upstream_drift = []
    if run_dir and req:
        for rel, want in (req.get("upstream_hashes") or {}).items():
            p = Path(run_dir) / rel
            cur = sha256_file(p) if p.is_file() else None
            if cur != want:
                upstream_drift.append(rel)

    ok = (not missing) and token_ok and ack.get("stage") == stage and not upstream_drift
    return ok, {"HANDSHAKE": "PASS" if ok else "FAIL", "missing_outputs": missing,
                "token_ok": token_ok, "upstream_drift": upstream_drift,
                "agent_id": ack.get("agent_id"), "recomputed_token": recomputed}


class FakeAgent:
    """Deterministic fake agent used ONLY in fake_live: copies fixture outputs
    into the stage dir and writes the ACK. No network; no real agent."""

    def __init__(self, fixture_dir: Path):
        self.fixture_dir = Path(fixture_dir)

    def fulfill(self, sd: Path, stage: str, expected_outputs) -> dict:
        sd = Path(sd)
        src = self.fixture_dir / stage / "outputs"
        if src.is_dir():
            for p in sorted(src.rglob("*")):
                if p.is_file():
                    target = sd / p.relative_to(src)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(p, target)
        return write_ack(sd, stage, expected_outputs, agent_id="fake-agent")
