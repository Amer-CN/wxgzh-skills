"""Stage output production for live / fake_live — dev2-hotfix1.

Every executable stage is invoked with the REAL sub-skill CLI (dev2's invented
--stage-dir/--article args are gone):

  media_enrichment  build media_request.json ->
                    run_media_enrichment.py --request <req> --output-dir <sd>
                    validate_media_manifest.py --manifest --request --bindings
  gzh_design        render_article.py --article --bindings --output-dir --theme smartisan
                    validate_gzh_html.py <final.html>          (positional)
  wechat_draft      publish_wechat_draft.py --html --title --audit-dir <sd>
                    (+ --dry-run in fake_live: zero side effects)

Agent stages (aihot / super_writer / zh_human_writing) use the handshake, then
the orchestrator subprocess-executes the OFFICIAL sub-skill validators (P0#5),
recording command + exit + stdout/stderr sha256 for the receipt.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

from . import execmodel as EM
from . import agent_handshake as AH
from . import secrets as SEC
from .state import read_json, sha256_file
from .subprocess_runner import run_script
from .approval_evidence import (ApprovalEvidenceError, build_approval_readiness,
                                enforce_approval_readiness)

AGENT_INSTRUCTIONS = {
    "aihot": "Query AI HOT (anonymous read-only), aggregate + dedup; do not write the article. 76H/OBS-267(超窗取料规程,通用规则):选题关键素材可能超出 7 天窗口、或用户显式写历史/回顾类选题时,按下列顺序取料:①已知关键日期 → /api/v1/dailies/{date} 取当日日报(归档正式端点);②精选池快照检索:selected/snapshot(fields=minimal,翻完分页后本地按关键词过滤,遵守 ETag/流量纪律;仅超窗选题使用,日常发文不走快照);③热点事件回溯:hot-topics → /api/v1/stories/{publicId} 时间线(逆序报道可回溯超 7 天);④官方源直采:官方博客/公告页/releases 等一手来源(永久可访问,宣传图就在上面)——走补充来源注册(registry/ledger provenance=supplemental);⑤仍缺 → 明示用户手动注入(items_file_injection 既有通道,不得静默降级)。AIHOT 授权边界不变:匿名只读、不绕过速率限制、不批量抓取全站。76J/OBS-273(dedup 模板):deduplicated_items.json 严格按 contracts/01_aihot.yaml 的字段模板书写(id/title/source_url 必填,links/content/published_at/category/score/selected/aihot_permalink/provenance 可选),不得自造字段名或改动既有键(aihot_permalink 类字段名税绝版)。76F/OBS-276(恢复SOP,通用规则):若卡在 ACK/request 循环——以当前最新 agent_handshake_request.json 为准重新 ACK(python -m wxgzh_pipeline.ack_cli --stage-dir <stage目录>),禁止删除文件重来;路径一律 POSIX 正斜杠,禁止把 Windows 反斜杠路径传给 rm 类命令。76F/OBS-279(编码,通用规则):写 JSON 一律 utf-8 无 BOM;读到带 BOM 的文件属正常,读侧容忍,不要重写上游产物。""76L/OBS-283(反顶包明规,通用规则):禁止手写 HTML 或其他脚本顶包 gzh_design 渲染产物;禁止绕过阶段直接调用 publish_wechat_draft.py(该脚本强制 --evidence 凭证门,只认管线 wechat_draft 阶段传入的本 RUN receipt);遇阻的正确动作=停下并报告(对照 Z Code 诚实停机先例),不得自行绕过或另走侧门;草稿存在但六阶段 receipt 不齐=顶包红旗,该草稿不可发、全程复查。",
    "super_writer": ("Run Super Writer Material-Heavy Full Mode. Generate every requested "
                     "product, then run the locked official validate_article_length.py with "
                     "--full-mode --json and save its exact JSON stdout as "
                     "full_mode_validator_report.json before ACK. "
                     "注入路径强制(OBS-88/档66,通用规则,不含单篇素材字面量):1) 含数字对比的事实必须登记为结构化 numbers(unit/value)+ chart_group + metric_name + series_label,中文数字转阿拉伯;2) 命令/脚本片段/终端输出以 fenced code block 原文呈现,不得转写为散文(并列短句清单除外,见 3));3) 注入素材中同一批并列短句清单,按语义分组拆进多个 :::alert 块,每组一块;块内每条独占一行、逐字不得改写;同一批文案全文只出现一次,不得再以 fenced code block 重复;alert type 按语义选择,阻断类与提醒类必须用不同 type;title 由写作侧按该组语义自拟;4) 每组数字对比在其首次出现的章节完整展开;同一组数字不得在多个章节重复对比表述;导语不出现任何数字对比。76G-R/OBS-265(行为层,通用规则):a) 产 handoff.yaml 时如实填写 prose_craft_applied / prose_craft_version——实际执行了 R1–R9 自检才许填 prose_craft_applied=true,未执行必须填 false,禁止默认 true 或留空误导下游;b) Phase 6 内容审稿的标题选定子步骤为必做——必须从 title_candidates 中按 评分尺(具体>有判断>贴核心张力>长度≤30字>无标题党空壳)选定最终标题,handoff 的 selected_title 与 title_selection_reason 必填且不得为空,article.md 的 H1 必须与 selected_title 一致。76F/OBS-276(恢复SOP,通用规则):若卡在 ACK/request 循环——以当前最新 agent_handshake_request.json 为准重新 ACK(python -m wxgzh_pipeline.ack_cli --stage-dir <stage目录>),禁止删除文件重来;路径一律 POSIX 正斜杠,禁止把 Windows 反斜杠路径传给 rm 类命令。76F/OBS-279(编码,通用规则):写 JSON 一律 utf-8 无 BOM;读到带 BOM 的文件属正常,读侧容忍,不要重写上游产物。76F/OBS-278(产物自检,super-writer 阶段):outline 写完后先跑 super-writer 仓 scripts/align_outline_budget.py --outline <outline.md> --target-visible-chars <目标字数> 做 ±5% 自动对齐(只调预算数值字段,保护域/数字/产品名不动);每个关键产物(outline/core-card/semantic-map/handoff/registry)写完后先跑 scripts/validate_single_product.py --product <名> --file <路径> 自检,失败按输出补字段,再交 ACK。""76L/OBS-283(反顶包明规,通用规则):禁止手写 HTML 或其他脚本顶包 gzh_design 渲染产物;禁止绕过阶段直接调用 publish_wechat_draft.py(该脚本强制 --evidence 凭证门,只认管线 wechat_draft 阶段传入的本 RUN receipt);遇阻的正确动作=停下并报告(对照 Z Code 诚实停机先例),不得自行绕过或另走侧门;草稿存在但六阶段 receipt 不齐=顶包红旗,该草稿不可发、全程复查。"),
    "zh_human_writing": "De-AI the Super Writer article only; freeze final_article.md (no new facts). "
                     "fidelity_report.json 自报 length_retention 必须为 balanced"
                     "(管线以 --length-retention balanced 实跑,0.8 阈值;不得自报 strict,防 OBS-220 口径漂移)。"
                     "76J/OBS-272(专名明规,通用规则):产品名/专名中的词永不改写——如 "
                     "Luma Agents、ComfyUI、MiniMax H3 等,任何语言/词形(Agent、agent、Agents)都不得"
                     "因「疑似 AI 味」被改写或删除;检测报告中的 FT-001 advisory 命中无需处理、不影响"
                     "交付(76D 专名豁免语义);改写产品名即违反「不得改产品名」铁律。76F/OBS-276(恢复SOP,通用规则):若卡在 ACK/request 循环——以当前最新 agent_handshake_request.json 为准重新 ACK(python -m wxgzh_pipeline.ack_cli --stage-dir <stage目录>),禁止删除文件重来;路径一律 POSIX 正斜杠,禁止把 Windows 反斜杠路径传给 rm 类命令。76F/OBS-279(编码,通用规则):写 JSON 一律 utf-8 无 BOM;读到带 BOM 的文件属正常,读侧容忍,不要重写上游产物。""76L/OBS-283(反顶包明规,通用规则):禁止手写 HTML 或其他脚本顶包 gzh_design 渲染产物;禁止绕过阶段直接调用 publish_wechat_draft.py(该脚本强制 --evidence 凭证门,只认管线 wechat_draft 阶段传入的本 RUN receipt);遇阻的正确动作=停下并报告(对照 Z Code 诚实停机先例),不得自行绕过或另走侧门;草稿存在但六阶段 receipt 不齐=顶包红旗,该草稿不可发、全程复查。",
}


# OBS-187(档71G,5b):aihot 注入路径运行时指令串(供反硬编码测试扫描,不复制)。
# OBS-198(档71H,2c):错误文案单一来源(live 未授权微信 API)。
# _wechat_api_blocked_meta 拼 "FAIL_CLOSED: " 前缀;_media_two_phase 的 raise
# 不带前缀(外层 except 已拼 f"FAIL_CLOSED: {exc}",避免双重前缀)。
WECHAT_API_BLOCKED_MSG = (
    "WXGZH_WECHAT_API_ALLOWED 未显式允许(当前环境值 %r)。"
    "live 模式默认拒绝微信 API 调用。在 .env 中加入 "
    "WXGZH_WECHAT_API_ALLOWED=1(取值 1/true/yes;命令行临时导出 0 "
    "可覆盖 .env 的 1)以放行。")


AIHOT_INJECTION_INSTRUCTIONS = (
    "素材已由正式注入入口提供(--items-file,自有素材注入)。"
    "禁止调用 AI HOT API;核验 aihot/ 三文件(fetch_log.mode="
    "items_file_injection)与哈希后 ACK。"
)


def _wechat_api_env(ctx, project_root=None) -> dict:
    """OBS-180/191(档71G-F,1a/R61):统一 env 读法,顺序与 _media_subprocess_env
    完全一致:dict(os.environ) → update(getattr(ctx, "env", None) or {}) →
    项目 .env setdefault。★禁止直接访问 ctx.env(仓内手写 fake ctx 无该属性,
    必须防御式读取)。合并优先级:os.environ < ctx.env < .env(setdefault)——
    命令行临时导出 0 可覆盖 .env 里的 1。
    """
    resolved = dict(os.environ)
    resolved.update(getattr(ctx, "env", None) or {})
    root = Path(project_root) if project_root is not None else Path(ctx.run_dir).parents[2]
    dotenv = Path(root) / ".env"
    if dotenv.is_file():
        for k, v in SEC.parse_env_file(dotenv).items():
            resolved.setdefault(k, v)
    return resolved


def wechat_api_allowed(env: dict | None) -> tuple[bool, str]:
    """OBS-180(档71G):WXGZH_WECHAT_API_ALLOWED 解析(合并由 _wechat_api_env 负责)。

    仅【取值解析】照抄 WXGZH_ALLOW_WARNINGS:strip().lower() in ("1","true","yes");
    【解析范围刻意不同】(OBS-197/R82):WXGZH_WECHAT_API_ALLOWED 走 _wechat_api_env
    (os.environ + ctx.env + .env),而 WXGZH_ALLOW_WARNINGS 刻意只读 ctx.env(命令行
    时点),不读 .env——放行开关不得被持久化文件静默开启,放宽需用户单独授权。
    返回 (allowed, raw_value)。
    """
    raw = (env or {}).get("WXGZH_WECHAT_API_ALLOWED", "")
    return raw.strip().lower() in ("1", "true", "yes"), raw


def _wechat_api_blocked_meta(entry, raw: str) -> dict:
    """live + 键未显式允许 → FAIL_CLOSED meta(exit_code=2,不得复用 skipped 语义)。"""
    return {
        "exec_kind": EM.WECHAT,
        "invoked_entrypoint": str(entry),
        "entrypoint_path": str(entry),
        "entrypoint_sha256": sha256_file(entry),
        "entry_run": {
            "exit_code": 2,
            "stdout": "",
            "stderr": "FAIL_CLOSED: " + WECHAT_API_BLOCKED_MSG % raw,
            "elapsed_seconds": 0.0,
        },
    }


def _frozen_article(ctx) -> Path:
    return Path(ctx.run_dir) / "zh_human_writing" / "final_article.md"


def _vresult(run: dict) -> dict:
    """Receipt-grade record of one real validator subprocess (P0#5)."""
    return {"path": run["script_path"], "sha256": run["script_sha256"],
            "command": run["command"], "exit_code": run["exit_code"],
            "stdout_sha256": run["stdout_sha256"], "stderr_sha256": run["stderr_sha256"],
            "elapsed_seconds": run["elapsed_seconds"]}


def produce(ctx, stage: str, state) -> tuple[list, dict]:
    kind = EM.STAGE_EXEC[stage]
    sd = ctx.stage_dir(stage)
    expected = EM.EXPECTED_OUTPUTS[stage]
    if kind == EM.AGENT:
        agent_expected = EM.AGENT_EXPECTED_OUTPUTS[stage]
        return _agent(ctx, stage, sd, expected, agent_expected, state)
    if kind == EM.SUBPROC:
        return _subprocess(ctx, stage, sd, expected, state)
    if kind == EM.WECHAT:
        return _wechat(ctx, stage, sd, expected, state)
    raise ValueError(f"unknown exec kind for {stage}")


# ---------- agent stages ----------

def _upstream_hashes(ctx, stage: str) -> dict:
    out = {}
    for rel in EM.UPSTREAM_INPUTS.get(stage, []):
        p = Path(ctx.run_dir) / rel
        out[rel] = sha256_file(p) if p.is_file() else None
    return out


def _skill_identity(ctx, stage: str) -> dict:
    from .stages import STAGE_SKILL
    skill = STAGE_SKILL[stage]
    disc = ctx.discovery.get(skill, {})
    return {"skill_name": skill,
            "skill_version": disc.get("current_version") or disc.get("locked_version"),
            "skill_root_sha256": disc.get("current_root_sha256") or disc.get("locked_root_sha256")}


def _contract_sha(stage: str) -> str | None:
    from .contracts import CONTRACT_FILES, SKILL_ROOT as REPO
    p = REPO / "contracts" / CONTRACT_FILES[stage]
    return sha256_file(p) if p.is_file() else None


def _super_writer_policy(sd: Path) -> dict:
    """Load the declared length policy; never derive it from article length."""
    profile = sd / "generation-profile.yaml"
    try:
        data = yaml.safe_load(profile.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise ValueError(f"invalid generation-profile.yaml: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("generation-profile.yaml top-level must be an object")
    fields = ("article_mode", "target_visible_chars", "acceptable_min", "acceptable_max")
    missing = [name for name in fields if data.get(name) in (None, "")]
    if missing:
        raise ValueError(f"generation-profile.yaml missing length policy: {missing}")
    mode = data["article_mode"]
    if not isinstance(mode, str):
        raise ValueError("generation-profile.yaml article_mode must be a string")
    values = {}
    for name in fields[1:]:
        value = data[name]
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise ValueError(f"generation-profile.yaml {name} must be a positive integer")
        values[name] = value
    if not values["acceptable_min"] <= values["target_visible_chars"] <= values["acceptable_max"]:
        raise ValueError("generation-profile.yaml requires min <= target <= max")
    return {"article_mode": mode, **values}


def _agent_validator_args(stage: str, ctx, sd: Path) -> list[tuple[str, str, list]]:
    """(skill, validator_rel, argv) for each OFFICIAL agent-stage validator."""
    rd = Path(ctx.run_dir)
    if stage == "super_writer":
        policy = _super_writer_policy(sd)
        length_args = [
            "--article", str(sd / "article.md"),
            "--outline", str(sd / "outline.md"),
            "--full-mode",
            "--generation-profile", str(sd / "generation-profile.yaml"),
            "--brief", str(sd / "writing-brief.md"),
            "--material-readiness", str(sd / "material-readiness.yaml"),
            "--material-ledger", str(sd / "material-ledger.yaml"),
            "--material-report", str(sd / "material-ingestion-report.json"),
            "--evidence-map", str(sd / "evidence-map.md"),
            "--core-card", str(sd / "core-card.md"),
            "--semantic-map", str(sd / "semantic-map.yaml"),
            "--editor-report", str(sd / "editor-report.md"),
            "--handoff", str(sd / "handoff.yaml"),  # 档76A/OBS-252:full-mode 必检
            "--article-mode", policy["article_mode"],
            "--target-visible-chars", str(policy["target_visible_chars"]),
            "--acceptable-min", str(policy["acceptable_min"]),
            "--acceptable-max", str(policy["acceptable_max"]),
            "--json",
        ]
        return [
            ("super-writer", "scripts/material_ingestion.py",
             ["--ledger", str(sd / "material-ledger.yaml"),
              "--output", str(sd / "material_ingestion_verification.json")]),
            ("super-writer", "scripts/validate_article_length.py", length_args),
            ("super-writer", "scripts/validate_semantic_map.py",
             ["--article", str(sd / "article.md"),
              "--semantic-map", str(sd / "semantic-map.yaml"),
               "--evidence-map", str(sd / "evidence-map.md")]),
        ]
    if stage == "zh_human_writing":
        orig = rd / "super_writer" / "article.md"
        return [
            ("zh-human-writing", "scripts/fidelity_guard.py",
             ["--original", str(orig), "--edited", str(sd / "final_article.md")]),
            # 0-1(72B-1/OBS-215/216):--check-level full 让 strong_contextual /
            # advisory_only 两级真正执行(默认 hard_residue_only 是假零来源);
            # --profile 本档写死 essay(公众号长文场景),不做可配置(Batch 3 范围)。
            ("zh-human-writing", "scripts/pattern_audit.py",
             ["--text", str(sd / "final_article.md"),
              "--check-level", "full",
              "--profile", "essay"]),
            # 0-2(72B-1/OBS-220):--length-retention balanced 写死,与 agent 自报口径对齐。
            ("zh-human-writing", "scripts/change_report.py",
             ["--original", str(orig), "--edited", str(sd / "final_article.md"),
              "--length-retention", "balanced"]),
        ]
    return []


def _agent(ctx, stage, sd, expected, agent_expected, state):
    upstream = _upstream_hashes(ctx, stage)
    identity = _skill_identity(ctx, stage)
    instructions = AGENT_INSTRUCTIONS.get(stage, "")
    inputs = {"topic": state.topic, "frozen_article_sha256": state.final_article_sha256}
    injection_meta = None
    # OBS-64(档64):自有素材注入正门——aihot 阶段若指定 --items-file,
    # 由 Pipeline 代码(而非 agent)写三文件:同构 schema 校验 + 来源留痕 +
    # 注入标记;agent 只核验后 ACK,不得再调用 AI HOT API。
    if stage == "aihot" and getattr(state, "items_file", None):
        from .material_injection import write_injected_aihot, INJECTION_MODE
        fetch_log_p = sd / "fetch_log.json"
        existing = None
        if fetch_log_p.is_file():
            try:
                existing = read_json(fetch_log_p)
            except ValueError:
                existing = None
        if existing and existing.get("mode") == INJECTION_MODE:
            # 幂等:resume 不重写注入文件(fetch_log 含 generated_at 时间戳,
            # 重写会破坏握手 token 绑定;注入事实已在首次写入时落盘)。
            # meta 字段集必须与 write_injected_aihot 返回值逐字同构,否则
            # agent_handshake_request 字节变化导致 token 漂移(档 64/66 实测)。
            inj = existing.get("injection") or {}
            injection_meta = {"mode": INJECTION_MODE,
                              "items_file": state.items_file,
                              "items_file_sha256": inj.get("items_file_sha256"),
                              "frozen_copy": str(sd / "items_file.injected.json"),
                              "item_count": inj.get("item_count")}
        else:
            injection_meta = write_injected_aihot(
                sd, state.items_file, state.run_id, state.topic)
        instructions = AIHOT_INJECTION_INSTRUCTIONS
        inputs["items_file"] = state.items_file
        inputs["material_injection"] = injection_meta
    AH.write_request(sd, stage, identity["skill_name"], instructions,
                     agent_expected, inputs, run_id=state.run_id, upstream_hashes=upstream,
                     stage_request_sha256=sha256_file(sd / "stage_request.json"),
                     skill_identity=identity, contract_sha256=_contract_sha(stage))
    if ctx.network_mode in ("fake_live", "integration"):
        agent = ctx.fake_agent or AH.FakeAgent(ctx.fixture_dir)
        try:
            agent.fulfill(sd, stage, agent_expected)
        except (OSError, ValueError, TypeError) as exc:
            outputs = [sd / o for o in expected if (sd / o).is_file()]
            return outputs, {"exec_kind": EM.AGENT,
                             "handshake": {"HANDSHAKE": "FAIL", "reason": str(exc)},
                             "handshake_failed": True,
                             "invoked_entrypoint": f"agent_handshake:{stage}",
                             "entrypoint_path": None, "entrypoint_sha256": None}
    ok, hs = AH.verify_ack(sd, stage, agent_expected, run_dir=ctx.run_dir)
    outputs = [sd / o for o in expected if (sd / o).is_file()]
    meta = {"exec_kind": EM.AGENT, "handshake": hs,
            "invoked_entrypoint": f"agent_handshake:{stage}",
            "entrypoint_path": None, "entrypoint_sha256": None}
    if injection_meta is not None:
        # OBS-64:注入事实显式标记(不伪装为 aihot 检索结果)
        meta["material_injection"] = injection_meta
    if not ok:
        meta["await_agent"] = (hs.get("HANDSHAKE") == "AWAITING_AGENT")
        meta["handshake_failed"] = not meta["await_agent"]
        return outputs, meta

    # P0#5 — REALLY execute the official sub-skill validators via subprocess.
    officials = []
    try:
        validators = _agent_validator_args(stage, ctx, sd)
    except ValueError as exc:
        validators = []
        if stage == "super_writer":
            validators = [
                ("super-writer", "scripts/material_ingestion.py",
                 ["--ledger", str(sd / "material-ledger.yaml"),
                  "--output", str(sd / "material_ingestion_verification.json")]),
                ("super-writer", "scripts/validate_semantic_map.py",
                 ["--article", str(sd / "article.md"),
                  "--semantic-map", str(sd / "semantic-map.yaml"),
               "--evidence-map", str(sd / "evidence-map.md")]),
            ]
        officials.append({"path": None, "sha256": None, "command": [], "exit_code": 2,
                          "stdout_sha256": hashlib.sha256(b"").hexdigest(),
                          "stderr_sha256": hashlib.sha256(str(exc).encode("utf-8")).hexdigest(),
                          "elapsed_seconds": 0.0, "error": str(exc)})
    validator_stdout_files: list[Path] = []
    for skill, rel, argv in validators:
        script = EM.resolve_agent_validator(skill, rel, ctx.network_mode, ctx.skills_home)
        run = run_script(script, argv, timeout=180)
        officials.append(_vresult(run))
        # 0-3(72B-1):官方校验器 stdout 落盘为 <脚本名>.stdout.json(Batch 2 量化验收通道)。
        stdout_file = sd / (Path(rel).name.replace(".py", ".stdout.json"))
        stdout_file.write_text(run.get("stdout") or "", encoding="utf-8")
        validator_stdout_files.append(stdout_file)
        if stage == "super_writer" and rel == "scripts/validate_article_length.py":
            try:
                official_report = json.loads(run.get("stdout") or "{}")
                agent_report = json.loads((sd / "full_mode_validator_report.json").read_text(encoding="utf-8"))
                report_matches = agent_report == official_report
            except (OSError, UnicodeError, json.JSONDecodeError):
                report_matches = False
            if not report_matches:
                run["exit_code"] = run["exit_code"] or 3
                run["stderr"] = (run.get("stderr") or "") + "\nagent report != official validator JSON"
                run["stderr_sha256"] = hashlib.sha256(run["stderr"].encode("utf-8")).hexdigest()
                officials[-1] = _vresult(run)
    outputs = [sd / o for o in expected if (sd / o).is_file()] + validator_stdout_files
    meta["official_validators"] = officials
    if any(v["exit_code"] != 0 for v in officials):
        meta["official_validator_failed"] = [v for v in officials if v["exit_code"] != 0]
    return outputs, meta


# ---------- executable stages ----------

class MediaRequestError(Exception):
    """Fail-closed: canonical registry missing / malformed / unmappable."""


_HEX64 = re.compile(r"^[0-9a-fA-F]{64}$")
_APPROVAL_BASE = {"approval_id", "approved_scope", "approved_at", "approved_by",
                  "approval_evidence_sha256"}
_STABLE_SINGLE_ASSET_FIELDS = {
    "asset_id", "material_id", "source_page_url", "resolved_original_url",
    "asset_sha256", "asset_identity_sha256", "discovery_manifest_sha256",
    "approval_id", "approved_scope", "approved_by", "approved_at",
    "approval_evidence_sha256",
}
VALID_APPROVAL_SCOPES = ("material", "source_url", "single_asset")

def _approval_precheck(rd: Path) -> dict:
    """OBS-82(档55):discover 候选硬门槛预校验——不让不达标资产进入人工批准。

    判定口径:正文图最小 480x200(用户裁决 2026-08-09,档 HF-3)。
    读 discover/media_manifest.json 的 width/height(discover 已下载并测尺寸),
    不依赖 decision/quality_status 字段(档50 实证:A-107 decision=rejected 仍被
    人工批准,quality=pass 语义混乱)。封面无独立尺寸门槛(从已批准正文图选择,
    正文门槛已隐含覆盖;若未来引入封面专用尺寸需扩展本函数)。
    行为:排除 + 标注——不达标资产从 eligible 清单排除,同时完整保留在 excluded
    列表(可追溯、可人工复核)。"""
    media_root = Path(rd) / "media_enrichment"
    manifest_path = media_root / "discover" / "media_manifest.json"
    eligible, excluded = [], []
    if manifest_path.is_file():
        try:
            manifest = read_json(manifest_path)
        except ValueError as exc:
            raise MediaRequestError(
                f"approval precheck FAIL_CLOSED: invalid discover media_manifest: {exc}") from exc
        for asset in manifest.get("assets", []):
            aid = asset.get("asset_id") if isinstance(asset, dict) else None
            if not aid:
                continue
            w, h = asset.get("width"), asset.get("height")
            if isinstance(w, int) and isinstance(h, int) and (w < 480 or h < 200):
                excluded.append({"asset_id": aid, "width": w, "height": h,
                                "reason": "dimensions below minimum 480x200"})
            else:
                eligible.append(aid)
    return {"schema_version": "1.0", "eligible": eligible, "excluded": excluded,
            "min_width": 480, "min_height": 200, "source": "discover/media_manifest.json"}


def _enforce_approval_precheck(rd: Path, precheck: dict) -> None:
    """OBS-82 消费端兜底:批准合同中任何资产不在预校验 eligible 清单 -> FAIL_CLOSED。
    防止「批准记录被消费而绑定数不足」(档50 A-107 场景)重演。"""
    eligible = set(precheck.get("eligible") or [])
    excluded_by_id = {a["asset_id"]: a for a in precheck.get("excluded") or []}
    for approval in (precheck.get("checked_approvals") or []):
        aid = approval.get("asset_id")
        if aid not in eligible:
            detail = excluded_by_id.get(aid)
            extra = (f"({detail['width']}x{detail['height']} below minimum 640x360)"
                     if detail else "not in eligible list")
            raise MediaRequestError(
                f"approval precheck FAIL_CLOSED: approved asset {aid} {extra}")


def _canonical_discovery_sha(manifest: dict) -> str:
    unsigned = dict(manifest)
    unsigned.pop("discovery_manifest_sha256", None)
    payload = (json.dumps(
        unsigned, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    ) + "\n").encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _stable_asset_identity(record: dict) -> str:
    payload = "\n".join((
        str(record.get("material_id", "")),
        str(record.get("source_page_url", "")),
        str(record.get("resolved_original_url", "")),
        str(record.get("asset_sha256", "")),
    )).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _load_copyright_approvals(rd: Path) -> dict:
    """P0#2: scope-aware copyright approvals. known_allowed can ONLY come from a
    real approval record whose approved_scope is one of material/source_url/
    single_asset, whose scope-specific binding field is present, and whose
    approval_evidence_sha256 is a well-formed 64-hex digest. Returns:

      {"material": {material_id: rec}, "source_url": {source_url: rec},
       "single_asset": {asset_id: rec}, "count": int}

    - material     -> requires material_id; approves ONLY that material.
    - source_url   -> requires source_url;  approves ONLY that exact URL.
    - single_asset -> requires asset_id;    NEVER marks the whole material
                      known_allowed (applied per-asset downstream, AFTER the
                      asset_id is produced from image extraction).
    Unknown scope / scope-binding mismatch / malformed evidence hash => ignored.
    """
    out = {"material": {}, "source_url": {}, "single_asset": {}, "count": 0}
    p = rd / "media_enrichment" / "copyright_approval.json"
    if not p.is_file():
        return out
    try:
        data = read_json(p)
    except ValueError:
        return out
    for rec in data.get("approvals", []):
        if not isinstance(rec, dict) or not _APPROVAL_BASE.issubset(rec):
            if isinstance(rec, dict) and rec.get("approved_scope") == "single_asset":
                raise MediaRequestError(
                    "old/malformed single_asset approval rejected: full stable fields required")
            continue
        ev = rec.get("approval_evidence_sha256", "")
        if not isinstance(ev, str) or not _HEX64.match(ev):
            continue  # evidence hash format error => FAIL_CLOSED (ignore record)
        scope = rec.get("approved_scope")
        if scope == "material" and rec.get("material_id"):
            out["material"][rec["material_id"]] = rec
        elif scope == "source_url" and rec.get("source_url"):
            out["source_url"][rec["source_url"]] = rec
        elif scope == "single_asset":
            if not _STABLE_SINGLE_ASSET_FIELDS.issubset(rec):
                raise MediaRequestError(
                    "old single_asset approval rejected: full stable fields required")
            if any(not rec.get(field) for field in _STABLE_SINGLE_ASSET_FIELDS):
                raise MediaRequestError(
                    "single_asset approval rejected: stable fields cannot be empty")
            if any(not _HEX64.fullmatch(str(rec.get(field, ""))) for field in (
                "asset_sha256", "asset_identity_sha256",
                "discovery_manifest_sha256", "approval_evidence_sha256",
            )):
                raise MediaRequestError(
                    "single_asset approval rejected: invalid sha256 field")
            if rec["asset_identity_sha256"] != _stable_asset_identity(rec):
                raise MediaRequestError(
                    "single_asset approval rejected: asset_identity_sha256 mismatch")
            out["single_asset"][rec["asset_id"]] = rec
        else:
            continue  # unknown scope OR missing required binding field => ignore
        out["count"] += 1
    return out


def _material_source_url(item: dict) -> str | None:
    """Single source of truth for a material/dedup item's source URL (OBS-31).

    Priority: `source_url` -> `links.original`. This MUST stay byte-identical
    with the canonical_claim_registry generation convention (档46R onward:
    source_url, else links.original) — the 档46R FAIL_CLOSED was caused by a
    divergence here (dedup side lacked the links.original fallback while the
    registry side used it). Any future change must be applied to BOTH sides
    through this one function; never re-implement the priority elsewhere.
    NOTE: the old dedup-side `url` intermediate alias is deliberately NOT kept
    (no real data uses it; keeping it would recreate a second split point).
    """
    url = item.get("source_url")
    if not url:
        links = item.get("links")
        if isinstance(links, dict):
            url = links.get("original")
    return url or None


def _check_material_url_consistency(mid: str, dedup_url, registry_url) -> None:
    """OBS-31/OBS-81: dedup side and canonical registry side must agree on the
    material source URL. FAIL_CLOSED unless BOTH sides have a non-empty URL AND
    they are equal — two empty values are NEVER treated as consistent (the most
    source-less case must not pass validation)."""
    if not dedup_url or not registry_url:
        raise MediaRequestError(
            f"material {mid} source_url missing on one side "
            f"(dedup={dedup_url!r} registry={registry_url!r}) (FAIL_CLOSED)")
    if dedup_url != registry_url:
        raise MediaRequestError(
            f"material {mid} source_url disagrees with dedup (FAIL_CLOSED)")


def _load_dedup_index(rd: Path) -> tuple[Path, dict]:
    """P0#3 (strict): load aihot/deduplicated_items.json into a deterministic index
    used to cross-verify the canonical registry (tolerant of id/url key aliases).
    Raises MediaRequestError on missing/malformed dedup, on ANY duplicated dedup id
    (even with an identical URL), or when one source_url is mapped by multiple
    different ids (ambiguous)."""
    p = rd / "aihot" / "deduplicated_items.json"
    if not p.is_file():
        raise MediaRequestError("aihot/deduplicated_items.json missing (FAIL_CLOSED)")
    try:
        data = read_json(p)
    except ValueError as e:
        raise MediaRequestError(f"deduplicated_items malformed: {e}")
    items = data.get("items") if isinstance(data, dict) else data
    if not isinstance(items, list) or not items:
        raise MediaRequestError("deduplicated_items empty/invalid (FAIL_CLOSED)")
    by_id, by_url = {}, {}
    for it in items:
        if not isinstance(it, dict):
            continue
        iid = it.get("id", it.get("material_id", it.get("item_id")))
        iid = str(iid) if iid is not None else None
        url = _material_source_url(it)
        permalink = it.get("aihot_permalink") or it.get("permalink") or url
        links = it.get("links") if isinstance(it.get("links"), dict) else {}
        norm = {"id": iid, "source_url": url, "aihot_permalink": permalink,
                "title": it.get("title", ""),
                # 76E/OBS-260:AI HOT 站内页(links.aihot)直出 HTML,抓图优先来源
                "aihot_internal_url": links.get("aihot") or ""}
        if iid is not None:
            if iid in by_id:
                raise MediaRequestError(
                    f"dedup id {iid} appears more than once (FAIL_CLOSED)")
            by_id[iid] = norm
        if url:
            prev = by_url.get(url)
            if prev is not None and prev["id"] != iid:
                raise MediaRequestError(
                    f"dedup source_url {url} is mapped by multiple different ids "
                    "(ambiguous, FAIL_CLOSED)")
            by_url[url] = norm
    return p, {"by_id": by_id, "by_url": by_url}


def _validate_with_fixed_media(ctx, request_path: Path) -> dict:
    """Run the installed/fixed media Commit's real validate_request in-process.

    This is deliberately independent from Pipeline's own field checks. Every
    generated media_request.json must pass the exact media runtime that will be
    invoked next; otherwise Pipeline fails closed before media execution.
    """
    ctx_env = getattr(ctx, "env", {}) or {}
    media_root = Path(
        ctx_env.get("WXGZH_FIXED_MEDIA_ROOT")
        or os.environ.get("WXGZH_FIXED_MEDIA_ROOT")
        or (Path(getattr(ctx, "skills_home", Path(__file__).resolve().parents[2]))
            / "media-enrichment")
    )
    contract_path = media_root / "src" / "media_enrichment" / "input_contract.py"
    package_root = media_root / "src"
    if not contract_path.is_file():
        raise MediaRequestError(
            f"fixed media validate_request unavailable: {contract_path}")
    inserted = False
    if str(package_root) not in sys.path:
        sys.path.insert(0, str(package_root))
        inserted = True
    try:
        module_name = f"_wxgzh_fixed_media_contract_{hashlib.sha256(str(contract_path).encode()).hexdigest()[:12]}"
        spec = importlib.util.spec_from_file_location(module_name, contract_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        try:
            spec.loader.exec_module(module)
            validation = module.validate_request(request_path)
        finally:
            sys.modules.pop(module_name, None)
    finally:
        if inserted:
            sys.path.remove(str(package_root))
    if not validation.valid:
        raise MediaRequestError(
            "fixed media validate_request rejected Pipeline request: "
            + "; ".join(validation.errors))
    return {
        "validator": str(contract_path),
        "validator_sha256": sha256_file(contract_path),
        "request_sha256": validation.request_sha256,
        "valid": True,
    }


def _build_media_request(ctx, sd: Path, state, *, phase: str = "discover") -> Path:
    """Build the REAL media request bound to the CANONICAL registry (P0#2/#3).

    Reads super_writer/canonical_claim_registry.json + aihot/deduplicated_items
    + the frozen article, and copies claim_id/material_id/claim_text/source_url/
    source_excerpt/selected_claim_ids/numbers/chart_group VERBATIM. NEVER invents
    IDs, NEVER uses material titles as claims, NEVER uses example.com fallback,
    and NEVER self-approves copyright. Missing/malformed registry => FAIL_CLOSED.
    """
    rd = Path(ctx.run_dir)
    reg_p = rd / "super_writer" / "canonical_claim_registry.json"
    if not reg_p.is_file():
        raise MediaRequestError("canonical_claim_registry.json missing (FAIL_CLOSED)")
    try:
        reg = read_json(reg_p)
    except ValueError as e:
        raise MediaRequestError(f"canonical registry malformed: {e}")
    reg_claims = reg.get("claims") or reg.get("canonical_claims") or []
    reg_materials = reg.get("materials") or []
    if not reg_claims or not reg_materials:
        raise MediaRequestError("canonical registry has no claims/materials (FAIL_CLOSED)")

    if phase not in ("discover", "continue"):
        raise MediaRequestError(f"invalid media phase: {phase}")
    dedup_p, dedup = _load_dedup_index(rd)           # P0#3 (raises on missing/bad)
    approvals = _load_copyright_approvals(rd)         # P0#2 scope-aware
    if phase == "discover":
        # Discovery must never carry an old, forged, or even valid single-asset
        # approval. Stable approval can only be created from its frozen output.
        approvals["single_asset"] = {}
    materials, claims = [], []
    mat_ids = set()
    verified_material_count = 0
    for m in reg_materials:
        mid = m.get("material_id")
        src = m.get("source_url")
        if not mid or not src:
            raise MediaRequestError(f"registry material missing id/source_url: {m}")
        mat_ids.add(mid)
        # 76H/OBS-268:supplemental(权威补充来源)正式注册——官方博客/公告页/
        # releases 等一手来源不在 aihot dedup 池属预期,携带自身 source_url +
        # 抓取证据 + 登记理由,不再被 dedup 对齐规则挤出或 FAIL_CLOSED。
        if m.get("provenance") == "supplemental":
            materials.append({
                "material_id": mid,
                "aihot_permalink": m.get("aihot_permalink") or src,
                "aihot_internal_url": "",
                "source_url": src, "title": m.get("title", ""),
                "selected_claim_ids": list(m.get("selected_claim_ids", [])),
                "provenance": "supplemental",
                "copyright_review": {"status": "unknown"},
            })
            verified_material_count += 1
            continue
        # ── P0#3 STRICT dedup mapping (hotfix4): the canonical material must map
        #    by its FORMAL upstream/dedup ID ONLY. A URL can NEVER be used to find
        #    a substitute item for a wrong/missing ID (no by_url fallback). ──
        explicit = m.get("dedup_id") or m.get("upstream_id") or m.get("aihot_id")
        dkey = str(explicit) if explicit is not None else str(mid)
        di = dedup["by_id"].get(dkey)
        if di is None:
            raise MediaRequestError(
                f"material {mid}: canonical/upstream id {dkey} not found in dedup "
                "(URL fallback is FORBIDDEN) (FAIL_CLOSED)")
        if explicit is not None:
            also = dedup["by_id"].get(str(mid))
            if also is not None and also != di:
                raise MediaRequestError(
                    f"material {mid}: dedup_id {dkey} conflicts with the "
                    "material_id mapping (FAIL_CLOSED)")
        _check_material_url_consistency(mid, di["source_url"], src)
        permalink = m.get("aihot_permalink") or src
        if di.get("aihot_permalink") and di["aihot_permalink"] != permalink:
            raise MediaRequestError(
                f"material {mid} aihot_permalink disagrees with dedup (FAIL_CLOSED)")
        verified_material_count += 1
        # ── P0#2 approval: ONLY material/source_url scope marks the material;
        #    single_asset NEVER marks the whole material known_allowed. ──
        appr = approvals["material"].get(mid) or approvals["source_url"].get(src)
        cr = ({"status": "known_allowed", "reviewed_by": appr["approved_by"],
               "reviewed_at": appr["approved_at"],
               "evidence": appr["approval_evidence_sha256"],
               "approval_id": appr["approval_id"], "approved_scope": appr["approved_scope"]}
              if appr else {"status": "unknown"})
        materials.append({
            "material_id": mid,
            "aihot_permalink": permalink,
            # 76E/OBS-260:站内页优先抓取(links.aihot;缺失时 media 回落原始页)
            "aihot_internal_url": di.get("aihot_internal_url") or "",
            "source_url": src, "title": m.get("title", ""),
            "selected_claim_ids": list(m.get("selected_claim_ids", [])),
            "dedup_id": di["id"],
            "copyright_review": cr,
        })
    # 76E/OBS-261:媒体请求范围 = registry(claim 绑定) ∪ material-ledger used。
    # used 但未绑定 claim 的素材(M-25 案例)必须进入抓取范围;dedup 按 source_url
    # 严格映射,缺失即 FAIL_CLOSED(与 registry 同强度)。
    for lmid, le in sorted(_ledger_used_materials(rd).items()):
        if lmid in mat_ids:
            continue
        # 76H/OBS-268:supplemental 条目(携带 source_url + 登记理由)不要求
        # dedup 池映射——权威补充来源正式注册位。
        if le.get("provenance") == "supplemental":
            mat_ids.add(lmid)
            verified_material_count += 1
            materials.append({
                "material_id": lmid,
                "aihot_permalink": le["aihot_permalink"],
                "aihot_internal_url": "",
                "source_url": le["source_url"], "title": le["title"],
                "selected_claim_ids": [],
                "provenance": "supplemental",
                "copyright_review": {"status": "unknown"},
            })
            continue
        di = dedup["by_url"].get(le["source_url"])
        if di is None:
            raise MediaRequestError(
                f"material {lmid}: ledger used source_url not found in dedup "
                "(FAIL_CLOSED)")
        _check_material_url_consistency(lmid, di["source_url"], le["source_url"])
        mat_ids.add(lmid)
        verified_material_count += 1
        materials.append({
            "material_id": lmid,
            "aihot_permalink": le["aihot_permalink"],
            "aihot_internal_url": di.get("aihot_internal_url") or "",
            "source_url": le["source_url"], "title": le["title"],
            "selected_claim_ids": [],
            "dedup_id": di["id"],
            "copyright_review": {"status": "unknown"},
        })

    for c in reg_claims:
        cid, mid = c.get("claim_id"), c.get("material_id")
        if not cid or not mid:
            raise MediaRequestError(f"registry claim missing claim_id/material_id: {c}")
        if mid not in mat_ids:
            raise MediaRequestError(f"claim {cid} references unknown material {mid} (FAIL_CLOSED)")
        claim = {"claim_id": cid, "claim_text": c.get("claim_text", ""),
                 "material_id": mid, "source_url": c.get("source_url", ""),
                 # 76C:source_excerpt 为 None 时置空串(schema 要求 string;seedance
                 # RUN 曾因 registry 某 claim 的 source_excerpt=None 被 media schema 拒绝)
                 "source_excerpt": c.get("source_excerpt") or ""}
        for opt in ("numbers", "chart_group", "metric_name", "series_label"):
            if opt in c:
                claim[opt] = c[opt]
        claims.append(claim)

    article = _frozen_article(ctx)
    # Integration uses the real media CLI with frozen local HTML/image fixtures.
    # Those fixtures contain one material; keep the Pipeline path authentic while
    # avoiding unrelated fixture coverage gaps for the second canonical material.
    ctx_env = getattr(ctx, "env", {}) or {}
    if ctx.network_mode == "integration" and ctx_env.get("WXGZH_INTEGRATION_MATERIAL_ID"):
        only_mid = ctx_env["WXGZH_INTEGRATION_MATERIAL_ID"]
        materials = [m for m in materials if m["material_id"] == only_mid]
        claims = [c for c in claims if c["material_id"] == only_mid]
        if not materials or not claims:
            raise MediaRequestError(
                f"integration material {only_mid} missing from canonical registry")
    req = {
        "schema_version": "1.0", "run_id": state.run_id,
        "article": {"path": "../zh_human_writing/final_article.md",
                    "sha256": state.final_article_sha256 or sha256_file(article)},
        "materials": materials, "claims": claims,
        "asset_approvals": [
            {field: rec[field] for field in sorted(_STABLE_SINGLE_ASSET_FIELDS)}
            for _, rec in sorted(approvals["single_asset"].items())],
        "config": {
            "upload_mode": (
                "wechat_audit" if ctx.network_mode in ("fake_live", "integration")
                else "wechat_image_host"
            ),
            "network_mode": (
                "offline_fixture" if ctx.network_mode in ("fake_live", "integration")
                else "live"
            ),
            "max_images_per_material": int(ctx_env.get("WXGZH_MEDIA_MAX_PER_MATERIAL", 8)),
            "max_total_images": int(ctx_env.get("WXGZH_MEDIA_MAX_TOTAL", 8)),
            # 档HF-3:正文图尺寸门槛 480x200(用户裁决 2026-08-09);
            # schemas/media_enrichment_request.schema.json 已声明合法键(默认 640/360)。
            "min_width": 480, "min_height": 200,
            "allow_unknown_license_for_publish": False,
            # 76C/OBS-248:来源域名黑名单(首批 ithome.com / img.ithome.com,水印广告图,
            # 用户两次手动删除;名单可配置,命中即拒)
            "domain_blacklist": ["ithome.com", "img.ithome.com"],
            # 76C/OBS-254:discover 扩池上限(全池潜力源补充抓取,防请求爆炸)
            "pool_fetch_limit": int(ctx_env.get("WXGZH_MEDIA_POOL_FETCH_LIMIT", 30)),
            # 76E/OBS-260:discovery 独立预算(与 max_total_images 分离;0/缺省由
            # media 侧默认 max(24, 3×max_total))
            **({"discovery_budget": int(ctx_env["WXGZH_MEDIA_DISCOVERY_BUDGET"])}
               if ctx_env.get("WXGZH_MEDIA_DISCOVERY_BUDGET") else {}),
        },
        "provenance": {"canonical_registry_sha256": sha256_file(reg_p),
                       "deduplicated_items_sha256": sha256_file(dedup_p),
                       "material_mapping_verified": True,
                       "verified_material_count": verified_material_count,
                       "copyright_approvals_bound": approvals["count"]},
    }

    # 76C/OBS-254:discover 扩池——全池潜力源(deduplicated_items)经站内页通道
    # (links.aihot 直出 HTML)补充抓取;仅 discover 阶段携带。
    if phase == "discover":
        try:
            dedup_data = read_json(dedup_p)
        except ValueError:
            dedup_data = {}
        pool_items = dedup_data.get("items") if isinstance(dedup_data, dict) else dedup_data
        if not isinstance(pool_items, list):
            pool_items = []
        req["pool_items"] = [{
            "id": it.get("id", ""), "title": it.get("title") or it.get("originalTitle", ""),
            "summary": it.get("summary", ""), "links": it.get("links", {}),
            "source_url": (it.get("links") or {}).get("original", ""),
            "aihot_permalink": (it.get("links") or {}).get("aihot", ""),
        } for it in pool_items if isinstance(it, dict) and it.get("id")]
        # 76C/OBS-255:用户供图注入——runs/<RUN>/media_enrichment/user_images.json
        # (直链清单,user_provided 免版权审批,用户供图责任自负,登记来源链接)
        user_images_p = rd / "media_enrichment" / "user_images.json"
        if user_images_p.is_file():
            try:
                user_images = read_json(user_images_p)
            except ValueError:
                user_images = None
            if isinstance(user_images, list):
                req["user_images"] = user_images
    req_path = sd / (
        "media_discovery_request.json" if phase == "discover"
        else "media_continuation_request.json"
    )
    req_path.write_text(json.dumps(req, ensure_ascii=False, indent=2, sort_keys=True),
                        encoding="utf-8", newline="\n")
    if getattr(ctx, "skills_home", None) or (getattr(ctx, "env", {}) or {}).get(
            "WXGZH_FIXED_MEDIA_ROOT"):
        validation = _validate_with_fixed_media(ctx, req_path)
        (sd / f"{phase}_request_validation.json").write_text(
            json.dumps(validation, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8", newline="\n",
        )
    return req_path


def _entry_args(
    ctx, stage: str, sd: Path, state, req_path: Path | None, *,
    media_phase: str = "discover", discovery_manifest: Path | None = None,
) -> list:
    rd = Path(ctx.run_dir)
    if stage == "media_enrichment":
        phase_dir = sd / media_phase
        args = ["--phase", media_phase, "--request", str(req_path),
                "--output-dir", str(phase_dir)]
        fixture_html = (getattr(ctx, "env", {}) or {}).get("WXGZH_MEDIA_FIXTURE_DIR")
        if fixture_html:
            args.extend(["--fixture-dir", fixture_html])
        if media_phase == "continue":
            args.extend(["--discovery-manifest", str(discovery_manifest)])
        return args
    if stage == "gzh_design":
        bindings_path = _captioned_bindings_path(ctx)
        args = ["--article", str(_frozen_article(ctx)),
                "--bindings", str(bindings_path),
                "--output-dir", str(sd), "--theme", "smartisan"]
        # 72E-1/OBS-251:handoff formatter.cover 存在则传 --strike/--tags/--brand/--kicker;
        # --date 永远不传(渲染自动当月);无 cover 字段时行为与现状逐字一致。
        cover = _handoff_cover(ctx)
        if cover:
            for flag, key in (("--strike", "strike"), ("--tags", "tags"),
                              ("--brand", "brand"), ("--kicker", "kicker")):
                val = cover.get(key)
                if val:
                    if key == "tags" and isinstance(val, list):
                        val = ",".join(str(t) for t in val)
                    args += [flag, str(val)]
        # 76D/OBS-257:封面标题 = handoff.selected_title(缺省回落 title_candidates[0]);
        # 副标题默认 = 文章导语(渲染器 intro),仅当终稿无导语且 hook_line 存在时兜底传入。
        cover_title = _handoff_title(ctx)
        if cover_title:
            args += ["--title", cover_title]
        if not _article_has_intro(ctx):
            hook = _handoff_hook(ctx)
            if hook:
                args += ["--subtitle", hook]
        return args
    raise ValueError(stage)




_OFFICIAL_HINTS = ("official", "官方", "announcement", "公告", "发布",
                   "github.com/minimax", "minimax.io", "releases")


def _caption_type(asset: dict, title: str) -> str:
    """76I/OBS-269:图注来源类型——官方资料图 / 社区演示 / 视频封面 / 本文数据图表。"""
    if asset.get("asset_origin") == "generated":
        return "本文数据图表"
    if asset.get("video_poster"):
        return "视频封面"
    low = f"{title} {asset.get('source_page_url') or ''}".lower()
    if any(h in low for h in _OFFICIAL_HINTS):
        return "官方资料图"
    return "社区演示"


def _clean_caption_title(t: str) -> str:
    """76I 遗留打磨(记入 OBS-269):图注标题清理——剥离站点前缀(「GitHub - 」等)、
    「 | 」「 - 」后缀段与多余冒号。"""
    s = (t or "").strip()
    # 76J/OBS-269 打磨:前缀剥离仅限 ASCII 站点名(GitHub - 等),避免把
    # 「MiniMax H3 - 官方博客」这类真实标题当站点前缀吃掉(后缀段由下方 - 规则剥)。
    m = re.match(r"^[A-Za-z0-9.]{1,24} - ", s)
    if m:
        s = s[m.end():]
    for sep in (" | ", " - "):
        idx = s.find(sep)
        if idx > 0:
            s = s[:idx]
    s = re.sub(r"[：:]{2,}", lambda m: m.group(0)[0], s)  # 多余冒号合并为第一个冒号的宽度
    s = re.sub(r"^[:：]\s*", "", s)
    return s.strip()


def _readable_desc(desc: str) -> str:
    """76I/OBS-269:content_description 可读性判定——<img 开头的裸 HTML 判不可读。"""
    d = (desc or "").strip()
    if not d or d.startswith("<img"):
        return ""
    return d


def _captioned_bindings_path(ctx) -> Path:
    """76I/OBS-269:图注合成——为 gzh 渲染生成 captioned bindings 副本
    (媒体冻结 bindings 不动,media receipt 不受影响);图注=来源类型+素材标题
    [+可读摘要],≤40 字,任何情况不含 HTML 片段。"""
    rd = Path(ctx.run_dir)
    src_bnd = rd / "media_enrichment" / "article_image_bindings.json"
    if not src_bnd.is_file():
        return src_bnd
    try:
        bnd = read_json(src_bnd)
    except (OSError, ValueError):
        return src_bnd
    titles = {}
    reg_p = rd / "super_writer" / "canonical_claim_registry.json"
    if reg_p.is_file():
        try:
            reg = read_json(reg_p)
            for m in reg.get("materials") or []:
                if m.get("material_id"):
                    titles[str(m["material_id"])] = str(m.get("title") or "")
        except (OSError, ValueError):
            pass
    man_p = rd / "media_enrichment" / "media_manifest.json"
    man = {}
    if man_p.is_file():
        try:
            man = read_json(man_p)
        except (OSError, ValueError):
            man = {}
    by_id = {a.get("asset_id"): a for a in man.get("assets", [])}
    out_dir = rd / "gzh_design" / "inputs"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = dict(bnd)
    for b in out.get("body_images", []):
        aid = b.get("asset_id")
        a = by_id.get(aid) or {}
        mids = b.get("material_ids") or a.get("material_ids") or []
        title = next((titles.get(str(m)) for m in mids if titles.get(str(m))), "") or ""
        ctype = _caption_type(a, title)
        desc = _readable_desc(a.get("content_description") or "")
        title_clean = _clean_caption_title(title)
        if desc:
            title_part = title_clean[:14] if title_clean else "素材"
            caption = f"{ctype}·{title_part}:{desc[:20]}"
        else:
            caption = f"{ctype}·{title_clean[:24]}" if title_clean else ctype
        b["caption"] = caption[:40]
        b["alt_text"] = b.get("alt_text") or caption[:40]
    p = out_dir / "article_image_bindings.captioned.json"
    p.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    return p


def _handoff_cover(ctx) -> dict | None:
    """读 super_writer/handoff.yaml 的 handoff.formatter.cover(72E-1/OBS-251)。
    文件缺失/解析失败/无 cover → None(行为与现状一致,绝不阻断)。"""
    try:
        p = Path(ctx.run_dir) / "super_writer" / "handoff.yaml"
        if not p.is_file():
            return None
        data = yaml.safe_load(p.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return None
        formatter = data.get("handoff", {}).get("formatter", {}) if isinstance(
            data.get("handoff"), dict) else {}
        cover = formatter.get("cover") if isinstance(formatter, dict) else None
        return cover if isinstance(cover, dict) and cover else None
    except (OSError, ValueError, yaml.YAMLError):
        return None


def _handoff_title(ctx) -> str | None:
    """读 handoff.selected_title;缺省回落 title_candidates[0](76D/OBS-257/258)。
    文件缺失/解析失败/两者皆无 → None(回落既有逻辑,绝不阻断)。"""
    try:
        p = Path(ctx.run_dir) / "super_writer" / "handoff.yaml"
        if not p.is_file():
            return None
        data = yaml.safe_load(p.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or not isinstance(data.get("handoff"), dict):
            return None
        h = data["handoff"]
        sel = h.get("selected_title")
        if isinstance(sel, str) and sel.strip():
            return sel.strip()
        cands = h.get("title_candidates")
        if isinstance(cands, list) and cands and isinstance(cands[0], str) and cands[0].strip():
            return cands[0].strip()
        return None
    except (OSError, ValueError, yaml.YAMLError):
        return None


def _article_has_intro(ctx) -> bool:
    """终稿第一个 "## " 之前是否存在非空正文行(导语);缺失时封面副标题用 hook_line 兜底。
    文件缺失/解析失败 → True(不触发兜底,行为与现状一致)。"""
    try:
        md = _frozen_article(ctx).read_text(encoding="utf-8")
        for ln in md.replace("\r\n", "\n").split("\n"):
            st = ln.strip()
            if st.startswith("## "):
                break
            if st and not st.startswith("#"):
                return True
        return False
    except (OSError, ValueError):
        return True






def _ledger_used_materials(rd: Path) -> dict:
    """76E/OBS-261:读 material-ledger.yaml 的 status:used 素材(id → 条目)。
    缺失/解析失败 → {};仅返回 used 且含 id/source_url 的条目(绝不阻断)。"""
    try:
        p = rd / "super_writer" / "material-ledger.yaml"
        if not p.is_file():
            return {}
        data = yaml.safe_load(p.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return {}
        ml = data.get("material_ledger")
        if not isinstance(ml, dict):
            return {}
        out = {}
        for m in ml.get("materials") or []:
            if not isinstance(m, dict):
                continue
            if m.get("status") != "used":
                continue
            mid = m.get("id") or m.get("material_id")
            if mid and m.get("source_url"):
                out[str(mid)] = {
                    "title": m.get("title", ""),
                    "source_url": m["source_url"],
                    "aihot_permalink": m.get("aihot_permalink") or m["source_url"],
                    "provenance": m.get("provenance"),
                }
        return out
    except (OSError, ValueError, yaml.YAMLError):
        return {}

def _wechat_title(ctx, state) -> str:
    """76D/OBS-258:草稿标题 = handoff.selected_title → title_candidates[0] → topic。"""
    return _handoff_title(ctx) or (state.topic or "wxgzh article")

def _handoff_hook(ctx) -> str | None:
    """读 handoff.hook_line(封面副标题兜底,76D/OBS-257);缺失 → None。"""
    try:
        p = Path(ctx.run_dir) / "super_writer" / "handoff.yaml"
        if not p.is_file():
            return None
        data = yaml.safe_load(p.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or not isinstance(data.get("handoff"), dict):
            return None
        hook = data["handoff"].get("hook_line")
        return hook.strip() if isinstance(hook, str) and hook.strip() else None
    except (OSError, ValueError, yaml.YAMLError):
        return None


def _validator_args(stage: str, sd: Path, req_path: Path | None) -> list:
    if stage == "media_enrichment":
        continue_dir = sd / "continue"
        return ["--manifest", str(continue_dir / "media_manifest.json"),
                "--request", str(req_path),
                "--bindings", str(continue_dir / "article_image_bindings.json")]
    if stage == "gzh_design":
        return [str(sd / "final.html")]  # validate_gzh_html.py takes a positional path
    return []


def _subprocess(ctx, stage, sd, expected, state):
    entry, validator = EM.resolve_entry(stage, ctx.network_mode, ctx.skills_home)
    req_path = None
    if stage == "media_enrichment":
        if ctx.network_mode == "fake_live":
            return _media_fake_live(ctx, sd, expected, state, entry, validator)
        return _media_two_phase(ctx, sd, expected, state, entry, validator)
    run = run_script(entry, _entry_args(ctx, stage, sd, state, req_path), timeout=300)
    meta = {"exec_kind": EM.SUBPROC, "invoked_entrypoint": str(entry),
            "entrypoint_path": run["script_path"], "entrypoint_sha256": run["script_sha256"],
            "entry_run": {"command": run["command"], "exit_code": run["exit_code"],
                          "elapsed": run["elapsed_seconds"],
                          "elapsed_seconds": run["elapsed_seconds"],
                          "stdout_sha256": run["stdout_sha256"],
                          "stderr_sha256": run["stderr_sha256"],
                          "stdout": run["stdout"][-2000:] if run["exit_code"] else "",
                          "stderr": run["stderr"][-2000:] if run["exit_code"] else ""}}
    if validator:
        vr = run_script(validator, _validator_args(stage, sd, req_path), timeout=180)
        meta["official_validator"] = _vresult(vr)
    outputs = [sd / o for o in expected if (sd / o).is_file()]
    return outputs, meta


def _media_fake_live(ctx, sd, expected, state, entry, validator):
    """Compatibility fake-live path; request still uses the fixed media contract."""
    try:
        request_path = _build_media_request(ctx, sd, state, phase="discover")
    except MediaRequestError as exc:
        return [], {
            "exec_kind": EM.SUBPROC, "invoked_entrypoint": str(entry),
            "entrypoint_path": str(entry),
            "entrypoint_sha256": sha256_file(entry) if Path(entry).is_file() else None,
            "media_request_failed": str(exc),
            "entry_run": {"exit_code": 2, "stderr": f"FAIL_CLOSED: {exc}"},
        }
    run = run_script(
        entry, ["--request", str(request_path), "--output-dir", str(sd)], timeout=300)
    meta = {
        "exec_kind": EM.SUBPROC, "invoked_entrypoint": str(entry),
        "entrypoint_path": run["script_path"], "entrypoint_sha256": run["script_sha256"],
        "entry_run": {"command": run["command"], "exit_code": run["exit_code"],
                      "elapsed": run["elapsed_seconds"],
                      "elapsed_seconds": run["elapsed_seconds"],
                      "stdout_sha256": run["stdout_sha256"],
                      "stderr_sha256": run["stderr_sha256"],
                      "stdout": run["stdout"][-2000:] if run["exit_code"] else "",
                      "stderr": run["stderr"][-2000:] if run["exit_code"] else ""},
    }
    if run["exit_code"] == 0 and validator:
        vr = run_script(
            validator,
            ["--manifest", str(sd / "media_manifest.json"),
             "--request", str(request_path),
             "--bindings", str(sd / "article_image_bindings.json")],
            timeout=180,
        )
        meta["official_validator"] = _vresult(vr)
    return [sd / name for name in expected if (sd / name).is_file()], meta


def _media_subprocess_env(ctx) -> dict:
    """OBS-196(档71H,2a):单一实现委派——env 解析统一走 _wechat_api_env。
    行为与旧实现逐字等价(os.environ → ctx.env → .env setdefault)。"""
    return _wechat_api_env(ctx)


# 档HF-1/OBS-243:discover 部分 fetch 失败的可恢复降级判定。
# 前缀在锁 pin 18414cc9 的 run_media_enrichment.py 中只有一处生成点
# (fetch 失败),锁不动即稳定;一律 startswith,不许 in/模糊匹配。
_DISCOVER_FETCH_ERROR_PREFIX = "Failed to fetch page for "


def _discover_degraded_recoverable(discover_dir):
    """判定 discover 非零退出是否可恢复降级进批准点(全部满足才算可恢复):

    1. discover/media_manifest.json 存在且 json 可解析;
    2. manifest.run_id != "validation_failed" 且 input.claims_total > 0;
    3. errors 非空,且每一条都以 "Failed to fetch page for " 开头;
    4. summary.eligible_assets + summary.review_required_assets > 0
       (至少存在一个可供人工批准的候选;为 0 则降级无意义)。

    返回 {"errors": [...]}(errors 原文)或 None。
    """
    manifest_path = discover_dir / "media_manifest.json"
    try:
        manifest = read_json(manifest_path)
    except (OSError, ValueError):
        return None
    if not isinstance(manifest, dict):
        return None
    if manifest.get("run_id") == "validation_failed":
        return None
    inputs = manifest.get("input")
    if not isinstance(inputs, dict) or not (inputs.get("claims_total") or 0) > 0:
        return None
    errors = manifest.get("errors") or []
    if not errors or not all(
            isinstance(e, str) and e.startswith(_DISCOVER_FETCH_ERROR_PREFIX)
            for e in errors):
        return None
    summary = manifest.get("summary")
    if not isinstance(summary, dict):
        return None
    candidates = ((summary.get("eligible_assets") or 0)
                  + (summary.get("review_required_assets") or 0))
    if not candidates > 0:
        return None
    return {"errors": errors}


def _media_two_phase(ctx, sd, expected, state, entry, validator):
    """State-machine-owned media discover/continue execution.

    First invocation runs discover and returns an explicit clean pause. Resume
    requires a stable approval file bound to the frozen discovery manifest,
    rebuilds and independently validates the continuation request, then invokes
    continue and the official media validator. Final outputs are copied only
    after both processes succeed.
    """
    discover_dir = sd / "discover"
    continue_dir = sd / "continue"
    frozen = discover_dir / "asset_discovery_manifest.json"
    approval_file = sd / "copyright_approval.json"

    try:
        # 档65:discover 失败残留判定——frozen 存在但 precheck/readiness 缺失
        # 说明上次 discover 未成功收尾(失败残留),必须重跑,不得直接进批准点。
        discover_paused = (frozen.is_file()
                           and (sd / "approval_precheck.json").is_file()
                           and (sd / "approval_readiness.json").is_file())
        if discover_paused:
            # 档66:上游 registry 变化 → discover 产物失效,必须重跑
            # (discover 请求的 provenance 记录 canonical_registry_sha256)。
            req_p = sd / "media_discovery_request.json"
            old_reg_sha = None
            if req_p.is_file():
                try:
                    old_reg_sha = read_json(req_p)                         .get("provenance", {}).get("canonical_registry_sha256")
                except (OSError, ValueError, AttributeError):
                    old_reg_sha = None
            cur_reg_sha = sha256_file(Path(ctx.run_dir) / "super_writer"
                                      / "canonical_claim_registry.json")
            if old_reg_sha != cur_reg_sha:
                discover_paused = False
        if not discover_paused:
            request_path = _build_media_request(ctx, sd, state, phase="discover")
            run = run_script(
                entry,
                _entry_args(ctx, "media_enrichment", sd, state, request_path,
                            media_phase="discover"),
                # 76C/OBS-254:discover 扩池后抓取预算=素材页 + pool_fetch_limit(默认 30)
                # 站内页,单页 15s 上限;300s 旧预算不足曾放大至 900s。
                # 76F/OBS-275:抓取并行(media worker=4)+ x.com 原文页短超时(5s)跳过,
                # 最坏预算重估 ≈ materials×(15×2)/4 + pool×15/4 + 余量 → 600s。
                timeout=600, env=_media_subprocess_env(ctx),
            )
            events_path = discover_dir / "upload_events.json"
            zero_upload = False
            if events_path.is_file():
                try:
                    zero_upload = not json.loads(
                        events_path.read_text(encoding="utf-8")).get("events", [])
                except ValueError:
                    zero_upload = False
            meta = {
                "exec_kind": EM.SUBPROC,
                "invoked_entrypoint": str(entry),
                "entrypoint_path": run["script_path"],
                "entrypoint_sha256": run["script_sha256"],
                "entry_run": {"command": run["command"], "exit_code": run["exit_code"],
                              "elapsed": run["elapsed_seconds"],
                              "elapsed_seconds": run["elapsed_seconds"],
                              "stdout_sha256": run["stdout_sha256"],
                              "stderr_sha256": run["stderr_sha256"],
                              "stdout": run["stdout"][-2000:] if run["exit_code"] else "",
                              "stderr": run["stderr"][-2000:] if run["exit_code"] else ""},
                "media_phase": "discover",
                "discovery_zero_upload_events": zero_upload,
            }
            if run["exit_code"] != 0:
                # 档HF-1/OBS-243:可恢复降级——仅部分 fetch 失败且仍有可批准
                # 候选时,继续走既有 paused 路径进批准点;否则维持 STAGE_FAILED。
                degraded = _discover_degraded_recoverable(discover_dir)
                if degraded is None:
                    return [], meta
                meta["discover_degraded"] = True
                meta["discover_exit_code"] = run["exit_code"]
                meta["discover_errors"] = degraded["errors"]
            if not frozen.is_file() or not zero_upload:
                meta["entry_run"]["exit_code"] = 2
                meta["entry_run"]["stderr"] = (
                    "FAIL_CLOSED: discovery manifest missing or upload events not empty")
                return [], meta
            # OBS-82(档55):discover 完成后、等待人工批准前,写可批准性预校验报告
            precheck = _approval_precheck(Path(ctx.run_dir))
            precheck_path = Path(ctx.run_dir) / "media_enrichment" / "approval_precheck.json"
            precheck_path.write_text(json.dumps(precheck, ensure_ascii=False, indent=2),
                                    encoding="utf-8")
            meta["approval_precheck"] = str(precheck_path)
            # OBS-87(档61):批准点信息完备性——内容描述 + 页面位置,缺字段 FAIL_CLOSED
            readiness = build_approval_readiness(Path(ctx.run_dir))
            readiness_path = (Path(ctx.run_dir) / "media_enrichment"
                              / "approval_readiness.json")
            readiness_path.write_text(json.dumps(readiness, ensure_ascii=False, indent=2),
                                     encoding="utf-8")
            meta["approval_readiness"] = str(readiness_path)
            meta["await_media_approval"] = True
            meta["discovery_manifest"] = str(frozen)
            meta["approval_file"] = str(approval_file)
            return [], meta

        if not approval_file.is_file():
            return [], {
                "exec_kind": EM.SUBPROC,
                "invoked_entrypoint": str(entry),
                "entrypoint_path": str(entry),
                "entrypoint_sha256": sha256_file(entry),
                "entry_run": {"exit_code": None, "stderr": ""},
                "media_phase": "awaiting_approval",
                "await_media_approval": True,
                "discovery_manifest": str(frozen),
                "approval_file": str(approval_file),
            }

        # OBS-180(档71G,2c③):live 进入 continue(真正 uploadimg)前检查;discover 不检查。
        if ctx.network_mode == "live":
            allowed, raw = wechat_api_allowed(_wechat_api_env(ctx))
            if not allowed:
                # OBS-198:raise 不带 FAIL_CLOSED 前缀(外层 except 已拼 f"FAIL_CLOSED: {exc}")。
                raise MediaRequestError(WECHAT_API_BLOCKED_MSG % raw)

        discovery = read_json(frozen)
        if discovery.get("discovery_manifest_sha256") != _canonical_discovery_sha(discovery):
            raise MediaRequestError("frozen discovery manifest sha256 invalid")
        approval_data = read_json(approval_file)
        stable = [a for a in approval_data.get("approvals", [])
                  if a.get("approved_scope") == "single_asset"]
        # OBS-82(档55):消费批准合同前,预校验兜底——批准了不达标资产必须 FAIL_CLOSED
        precheck_path = Path(ctx.run_dir) / "media_enrichment" / "approval_precheck.json"
        if not precheck_path.is_file():
            raise MediaRequestError(
                "approval precheck FAIL_CLOSED: approval_precheck.json missing")
        precheck = read_json(precheck_path)
        precheck["checked_approvals"] = stable
        _enforce_approval_precheck(Path(ctx.run_dir), precheck)
        # OBS-87(档61):批准信息链闸门——旧合同自动失效;内容不明/rejected 不得消费
        readiness_path = (Path(ctx.run_dir) / "media_enrichment"
                          / "approval_readiness.json")
        if not readiness_path.is_file():
            raise MediaRequestError(
                "approval readiness FAIL_CLOSED: approval_readiness.json missing")
        readiness = read_json(readiness_path)
        enforce_approval_readiness(readiness_path, readiness, stable)
        frozen_by_id = {a["asset_id"]: a for a in discovery.get("assets", [])}
        for approval in stable:
            if not _STABLE_SINGLE_ASSET_FIELDS.issubset(approval):
                raise MediaRequestError("old single_asset approval rejected")
            frozen_asset = frozen_by_id.get(approval.get("asset_id"))
            if frozen_asset is None:
                raise MediaRequestError("single_asset approval target missing from frozen manifest")
            checks = {
                **frozen_asset,
                "discovery_manifest_sha256": discovery["discovery_manifest_sha256"],
            }
            for field in (
                "asset_id", "material_id", "source_page_url", "resolved_original_url",
                "asset_sha256", "asset_identity_sha256", "discovery_manifest_sha256",
            ):
                if approval.get(field) != checks.get(field):
                    raise MediaRequestError(
                        f"single_asset approval does not match frozen manifest: {field}")

        request_path = _build_media_request(ctx, sd, state, phase="continue")
        run = run_script(
            entry,
            _entry_args(ctx, "media_enrichment", sd, state, request_path,
                        media_phase="continue", discovery_manifest=frozen),
            timeout=300, env=_media_subprocess_env(ctx),
        )
        meta = {
            "exec_kind": EM.SUBPROC,
            "invoked_entrypoint": str(entry),
            "entrypoint_path": run["script_path"],
            "entrypoint_sha256": run["script_sha256"],
            "entry_run": {"command": run["command"], "exit_code": run["exit_code"],
                          "elapsed": run["elapsed_seconds"],
                          "elapsed_seconds": run["elapsed_seconds"],
                          "stdout_sha256": run["stdout_sha256"],
                          "stderr_sha256": run["stderr_sha256"],
                          "stdout": run["stdout"][-2000:] if run["exit_code"] else "",
                          "stderr": run["stderr"][-2000:] if run["exit_code"] else ""},
            "media_phase": "continue",
        }
        if run["exit_code"] == 0 and validator:
            vr = run_script(
                validator,
                _validator_args("media_enrichment", sd, request_path),
                timeout=180,
            )
            meta["official_validator"] = _vresult(vr)
            if vr["exit_code"] == 0:
                for name in expected:
                    source = continue_dir / name
                    if source.is_file():
                        (sd / name).write_bytes(source.read_bytes())
        outputs = [sd / name for name in expected if (sd / name).is_file()]
        return outputs, meta
    except (OSError, ValueError, KeyError, TypeError, MediaRequestError,
            ApprovalEvidenceError) as exc:
        return [], {
            "exec_kind": EM.SUBPROC,
            "invoked_entrypoint": str(entry),
            "entrypoint_path": str(entry),
            "entrypoint_sha256": sha256_file(entry),
            "media_request_failed": str(exc),
            "entry_run": {"exit_code": 2, "stderr": f"FAIL_CLOSED: {exc}"},
        }


def _select_live_cover(ctx):
    """OBS-72/档70(OBS-99):封面从本 RUN 已批准资产的本地冻结文件选择。

    规则(显式,不依赖隐式顺序):article_image_bindings.json body_images
    顺序中第一张「已批准(single_asset)+ 已成功上传」的资产;取不到任何
    候选即 FAIL_CLOSED。

    本地文件定位(OBS-99,不再硬编码 discover/images 单目录):
    (a) 候选目录集合 = media_enrichment/discover/ 下由冻结清单实际引用到的
        资产目录:asset_origin=generated -> discover/charts/,其余 ->
        discover/images/;media_manifest 若记录了 local_path,其父目录亦纳入
        候选(须 resolve 后在 media_root 之内)。不得递归扫描整个 RUN 目录,
        不得把 RUN 目录之外的任何路径纳入候选。
    (b) 在候选目录内按 <asset_sha256>.* 匹配;若冻结清单记录了 local_path,
        仅用它做交叉验证(解析后必须落在 media_root 之内、必须是常规文件),
        不得作为唯一取值来源直接 open。
    (c) 命中文件必须 resolve() 后仍位于 media_root.resolve() 之内
        (防符号链接/路径穿越),否则 FAIL_CLOSED。
    (d) 命中文件 sha256 必须等于冻结清单 asset_sha256。
    (e) 若 local_path 记录值与实际命中文件不是同一文件 -> FAIL_CLOSED
        (记录与实物不符)。

    三条件 FAIL_CLOSED(任一条即拦截,exit 2 零副作用):批准缺失/未上传/
    本地文件缺失或 sha 失配。返回 (cover_path, asset_id)。
    """
    rd = Path(ctx.run_dir)
    media_root = rd / "media_enrichment"
    media_root_resolved = media_root.resolve()
    approvals = _load_copyright_approvals(rd)
    if not approvals["single_asset"]:
        raise MediaRequestError(
            "cover: no stable single_asset approval in contract")
    frozen = media_root / "discover" / "asset_discovery_manifest.json"
    if not frozen.is_file():
        raise MediaRequestError(
            "cover: frozen asset_discovery_manifest.json missing")
    manifest = read_json(frozen)
    by_id = {a["asset_id"]: a for a in manifest.get("assets", [])}
    events_path = media_root / "continue" / "upload_events.json"
    if not events_path.is_file():
        raise MediaRequestError(
            "cover: continue/upload_events.json missing")
    events = read_json(events_path)
    success_ids = []
    for ev in events.get("events", []):
        aid = ev.get("asset_id") if isinstance(ev, dict) else None
        if aid and ev.get("status") == "success" and aid not in success_ids:
            success_ids.append(aid)
    if not success_ids:
        raise MediaRequestError(
            "cover: no successful upload in continue/upload_events.json")
    bindings_path = media_root / "article_image_bindings.json"
    if not bindings_path.is_file():
        raise MediaRequestError(
            "cover: article_image_bindings.json missing")
    bindings = read_json(bindings_path)
    candidates = []
    for img in bindings.get("body_images", []):
        aid = img.get("asset_id") if isinstance(img, dict) else None
        if aid in success_ids and aid in approvals["single_asset"]:
            candidates.append(aid)
    if not candidates:
        raise MediaRequestError(
            "cover: no approved and uploaded asset in bindings")

    # OBS-99:候选目录集合 = 冻结清单实际引用到的资产目录(images/ + charts/)。
    # 以 asset_discovery_manifest 的 asset_origin 为确定性依据;media_manifest
    # 的 local_path 父目录仅作补充(须在 media_root 内),绝不信任字符串直接 open。
    full_manifest_path = media_root / "discover" / "media_manifest.json"
    full_by_id: dict = {}
    if full_manifest_path.is_file():
        try:
            full = read_json(full_manifest_path)
            full_by_id = {a.get("asset_id"): a
                          for a in full.get("assets", []) if isinstance(a, dict)}
        except (OSError, ValueError):
            full_by_id = {}

    def _candidate_dirs() -> list[Path]:
        dirs: list[Path] = []
        seen = set()
        for asset in manifest.get("assets", []):
            if not isinstance(asset, dict) or not asset.get("asset_id"):
                continue
            if asset.get("asset_origin") == "generated":
                d = media_root / "discover" / "charts"
            else:
                d = media_root / "discover" / "images"
            try:
                dr = d.resolve()
            except OSError:
                continue
            if dr in seen:
                continue
            seen.add(dr)
            if dr.is_dir() and dr.is_relative_to(media_root_resolved):
                dirs.append(dr)
        # media_manifest 记录的 local_path 父目录补充(仅限 media_root 内)
        for asset in full_by_id.values():
            lp = asset.get("local_path") if isinstance(asset, dict) else None
            if not lp:
                continue
            try:
                dr = Path(lp).resolve().parent
            except OSError:
                continue
            if dr in seen or not dr.is_relative_to(media_root_resolved):
                continue
            seen.add(dr)
            if dr.is_dir():
                dirs.append(dr)
        return dirs

    def _find_frozen_file(asset_id: str, expected_sha: str) -> Path:
        """定位本 RUN 冻结产物:候选文件 = 候选目录内 <sha>.* 命中的文件 ∪
        media_manifest local_path 解析后的文件(带 resolve/越界/常规文件约束)。

        - 图表资产命名 chart-NNN.png(非 <sha> 命名),glob 不命中时由
          local_path 定位;local_path 是记录值,★绝不直接 open —— 必须
          resolve 后在 media_root 内、必须是常规文件、字节 sha 必须等于
          冻结清单值(三重约束后才是可用的本地冻结文件)。
        - 两者都存在且不是同一文件 -> FAIL_CLOSED(记录与实物不符)。
        """
        glob_hits: list[Path] = []
        for d in _candidate_dirs():
            try:
                for p in sorted(d.glob(f"{expected_sha}.*")):
                    rp = p.resolve()
                    if rp.is_file() and rp.is_relative_to(media_root_resolved):
                        glob_hits.append(rp)
            except OSError:
                continue
        rec_full = full_by_id.get(asset_id) or {}
        lp = rec_full.get("local_path") if isinstance(rec_full, dict) else None
        lp_resolved: Path | None = None
        if lp:
            try:
                lpr = Path(lp).resolve()
            except OSError:
                raise MediaRequestError(
                    f"cover: {asset_id} local_path invalid")
            if not lpr.is_relative_to(media_root_resolved):
                raise MediaRequestError(
                    f"cover: {asset_id} local_path outside media_root")
            if lpr.exists() and not lpr.is_file():
                raise MediaRequestError(
                    f"cover: {asset_id} local_path not a regular file")
            # 记录的文件不存在:不作为定位来源(等同无记录);最终无任何命中 -> missing
            if lpr.is_file():
                lp_resolved = lpr
        if not glob_hits and lp_resolved is None:
            raise MediaRequestError(
                f"cover: {asset_id} local frozen file missing")
        if glob_hits and lp_resolved is not None and lp_resolved not in glob_hits:
            raise MediaRequestError(
                f"cover: {asset_id} local_path record does not match hit file")
        local = lp_resolved if lp_resolved is not None else glob_hits[0]
        # (d) 字节 sha 必须与冻结清单一致
        if sha256_file(local) != expected_sha:
            raise MediaRequestError(
                f"cover: {asset_id} local frozen file sha256 mismatch")
        return local

    for asset_id in candidates:
        rec = approvals["single_asset"][asset_id]
        manifest_rec = by_id.get(asset_id)
        if manifest_rec is None:
            raise MediaRequestError(
                f"cover: {asset_id} missing from frozen discovery manifest")
        if manifest_rec.get("asset_sha256") != rec.get("asset_sha256"):
            raise MediaRequestError(
                f"cover: {asset_id} approval sha diverges from frozen manifest")
        local = _find_frozen_file(asset_id, rec["asset_sha256"])
        # 76G-R/76D 配套:封面本地文件若是 WebP 转 JPEG(微信 40113 unsupported
        # file type 实证;上传路径已转码,封面选择路径同样处理)
        return _webp_cover_to_jpeg(local, rd), asset_id
    raise MediaRequestError("cover: no usable approved cover asset")


def _webp_cover_to_jpeg(local: Path, run_dir: Path) -> Path:
    """封面 WebP → JPEG(alpha 白底合成,与 media uploader 同法);非 WebP 原样。"""
    try:
        head = local.read_bytes()[:12]
    except OSError:
        return local
    if len(head) < 12 or head[:4] != b"RIFF" or head[8:12] != b"WEBP":
        return local
    try:
        from PIL import Image
        im = Image.open(local)
        if im.mode in ("RGBA", "LA", "P"):
            im = im.convert("RGBA")
            bg = Image.new("RGB", im.size, (255, 255, 255))
            bg.paste(im, mask=im.split()[-1])
            im = bg
        else:
            im = im.convert("RGB")
        out = Path(run_dir) / "wechat_draft" / (local.stem + ".cover.jpg")
        out.parent.mkdir(parents=True, exist_ok=True)
        im.save(out, "JPEG", quality=90)
        return out
    except Exception:
        return local  # 转码失败回落原路径(由发布端如实报错)


def _wechat(ctx, stage, sd, expected, state):
    # OBS-180(档71G,2c②):live + 键未允许 → FAIL_CLOSED,先于 create_wechat_draft 检查。
    if ctx.network_mode == "live":
        entry0, _ = EM.resolve_entry(stage, ctx.network_mode, ctx.skills_home)
        allowed, raw = wechat_api_allowed(_wechat_api_env(ctx))
        if not allowed:
            return [], _wechat_api_blocked_meta(entry0, raw)
    if not ctx.create_wechat_draft:
        return [], {"exec_kind": EM.WECHAT, "skipped": "create_wechat_draft=False"}
    entry, _ = EM.resolve_entry(stage, ctx.network_mode, ctx.skills_home)
    html = Path(ctx.run_dir) / "gzh_design" / "final.html"
    args = ["--html", str(html), "--title", (state.topic or "wxgzh article")[:60],
            "--audit-dir", str(sd)]
    # 76D/OBS-258:草稿标题优先取 handoff.selected_title(缺省回落 title_candidates[0]);
    # 都没有再回落既有 topic 逻辑。标题 60 字符上限沿用。
    args = ["--html", str(html), "--title", _wechat_title(ctx, state)[:60],
            "--audit-dir", str(sd),
            # 76L/OBS-282:交付凭证门——publish 脚本必须绑定本 RUN 的 gzh receipt
            "--evidence", str(Path(ctx.run_dir) / "gzh_design" / "stage_receipt.json")]
    if ctx.network_mode == "live":
        try:
            cover, cover_asset_id = _select_live_cover(ctx)
        except (OSError, ValueError, KeyError, TypeError, MediaRequestError) as exc:
            return [], {
                "exec_kind": EM.WECHAT,
                "invoked_entrypoint": str(entry),
                "entrypoint_path": str(entry),
                "entrypoint_sha256": sha256_file(entry),
                "entry_run": {
                    "exit_code": 2,
                    "stdout": "",
                    "stderr": f"FAIL_CLOSED: {exc}",
                    "elapsed_seconds": 0.0,
                },
            }
        args.extend(["--cover", str(cover)])
        # 档54R:显式放行开关——仅当环境变量显式开启时向被锁脚本传 --allow-warnings
        # OBS-197(档71H,5b/R82):WXGZH_ALLOW_WARNINGS 刻意只读 ctx.env(命令行时点),
        # 不读 .env——放行开关不得被持久化文件静默开启。
        # (默认关闭;双层显式:env 开关 + 脚本参数;放行留痕由脚本写入 allowance_record.json)
        ctx_env = getattr(ctx, "env", {}) or {}
        allow_raw = str(ctx_env.get("WXGZH_ALLOW_WARNINGS") or "").strip().lower()
        if allow_raw in ("1", "true", "yes"):
            args.append("--allow-warnings")
    if ctx.network_mode in ("fake_live", "integration"):
        args.append("--dry-run")  # zero side effects; simulated batchget snapshots
    run = run_script(entry, args, timeout=300)
    meta = {"exec_kind": EM.WECHAT, "invoked_entrypoint": str(entry),
            "entrypoint_path": run["script_path"], "entrypoint_sha256": run["script_sha256"],
            "entry_run": {"command": run["command"], "exit_code": run["exit_code"],
                          "elapsed_seconds": run["elapsed_seconds"],
                          "stdout_sha256": run["stdout_sha256"],
                          "stderr_sha256": run["stderr_sha256"],
                          "stdout": run["stdout"][-2000:] if run["exit_code"] else "",
                          "stderr": run["stderr"][-2000:] if run["exit_code"] else ""}}
    if ctx.network_mode == "live":
        meta["cover_asset_id"] = cover_asset_id
    outputs = [sd / o for o in expected if (sd / o).is_file()]
    # 档54R:放行产物(allowance_record.json)作为正式 stage 产物纳入 receipt,可追溯
    allowance = sd / "allowance_record.json"
    if allowance.is_file():
        outputs.append(allowance)
    return outputs, meta
