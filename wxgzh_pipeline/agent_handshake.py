"""Agent-driven stage handshake.

Some stages can only be performed by an LLM agent: AI HOT fetch/aggregate,
Super Writer Material-Heavy Full Mode, and zh-human-writing de-AI. The
orchestrator does NOT call a subprocess for these. Instead it writes a handshake
REQUEST describing what to produce and where; the agent produces the outputs on
disk and writes a signed ACK. The orchestrator then verifies the ACK: every
expected output must exist and the ACK token must bind the request to the
CURRENT file hashes (so tampering an output after the ACK breaks the token).

- live mode + no ACK yet  -> AWAITING_AGENT (a clean pause, never a crash;
  this is the dev1 P0 fix — live no longer dies on NotImplementedError).
- fake_live mode          -> FakeAgent fulfills the handshake deterministically
  from fixture templates (real handshake machinery, no real agent, no side effects).
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


def token(stage: str, expected_outputs, produced_hashes: dict) -> str:
    basis = stage + "|" + ",".join(sorted(expected_outputs)) + "|" + \
        ",".join(f"{k}={produced_hashes[k]}" for k in sorted(produced_hashes))
    return hashlib.sha256(basis.encode("utf-8")).hexdigest()


def write_request(sd: Path, stage: str, skill: str, instructions: str,
                  expected_outputs, inputs: dict) -> dict:
    sd = Path(sd)
    req = {"stage": stage, "skill": skill, "kind": "agent_handshake",
           "instructions": instructions, "expected_outputs": list(expected_outputs),
           "inputs": inputs}
    atomic_write_json(sd / REQUEST_FILE, req)
    (sd / DOC_FILE).write_text(
        f"# Agent handshake — {stage}\n\nSkill: `{skill}`\n\n{instructions}\n\n"
        f"Produce these files in this directory, then write `{ACK_FILE}`:\n"
        + "".join(f"- `{o}`\n" for o in expected_outputs)
        + "\nThe orchestrator resumes and verifies the ACK token against the "
        "produced file hashes before accepting this stage.\n",
        encoding="utf-8", newline="\n")
    return req


def write_ack(sd: Path, stage: str, expected_outputs, agent_id: str = "agent") -> dict:
    sd = Path(sd)
    produced = {o: sha256_file(sd / o) for o in expected_outputs if (sd / o).is_file()}
    ack = {"stage": stage, "agent_id": agent_id, "produced_files": sorted(produced),
           "produced_hashes": produced, "handshake_token": token(stage, expected_outputs, produced)}
    atomic_write_json(sd / ACK_FILE, ack)
    return ack


def verify_ack(sd: Path, stage: str, expected_outputs) -> tuple[bool, dict]:
    sd = Path(sd)
    ackp = sd / ACK_FILE
    if not ackp.is_file():
        return False, {"HANDSHAKE": "AWAITING_AGENT", "reason": f"{ACK_FILE} not present yet"}
    ack = json.loads(ackp.read_text(encoding="utf-8"))
    missing = [o for o in expected_outputs if not (sd / o).is_file()]
    current = {o: sha256_file(sd / o) for o in expected_outputs if (sd / o).is_file()}
    recomputed = token(stage, expected_outputs, current)
    token_ok = ack.get("handshake_token") == recomputed
    ok = (not missing) and token_ok and ack.get("stage") == stage
    return ok, {"HANDSHAKE": "PASS" if ok else "FAIL", "missing_outputs": missing,
                "token_ok": token_ok, "agent_id": ack.get("agent_id"),
                "recomputed_token": recomputed}


class FakeAgent:
    """Deterministic fake agent used ONLY in fake_live: copies fixture outputs
    into the stage dir and writes the ACK. No network; no real agent."""

    def __init__(self, fixture_dir: Path):
        self.fixture_dir = Path(fixture_dir)

    def fulfill(self, sd: Path, stage: str, expected_outputs) -> dict:
        sd = Path(sd)
        src = self.fixture_dir / stage / "outputs"
        for o in expected_outputs:
            s = src / o
            if s.is_file():
                shutil.copyfile(s, sd / o)
        return write_ack(sd, stage, expected_outputs, agent_id="fake-agent")
