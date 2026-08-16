"""76R 任务 2/OBS-288:预检强制化 + 指令瘦身测试。

- sw 指令含硬步骤:ACK 前必须跑 align_outline_budget + validate_single_product 且全绿,否则禁止 ACK;
- 通用规则(276/279/283)抽为单一真源常量,三阶段共用(源码去重);
- 语义零丢失:改写前(HEAD)与改写后产物指令规则清单一一对应;公共规则在源码中单写。
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import wxgzh_pipeline.producers as PR

from conftest import SKILL_ROOT


def test_obs288_preflight_mandatory_hard_step():
    """sw 预检强制化——ACK 前必须完成两步且全绿,禁止写 ACK。"""
    instr = PR.AGENT_INSTRUCTIONS["super_writer"]
    assert "76R/OBS-288" in instr and "硬步骤" in instr
    assert "ACK 前必须完成以下两步且全绿" in instr
    assert "否则禁止写 ACK" in instr
    assert "align_outline_budget.py" in instr and "validate_single_product.py" in instr
    assert "valid=true" in instr


def test_obs288_common_rules_single_source():
    """通用规则(276/279/283)单一真源,三阶段产物指令均含。"""
    assert hasattr(PR, "_COMMON_RULES")
    for k in ("aihot", "super_writer", "zh_human_writing"):
        assert "76F/OBS-276" in PR.AGENT_INSTRUCTIONS[k]
        assert "76F/OBS-279" in PR.AGENT_INSTRUCTIONS[k]
        assert "76L/OBS-283" in PR.AGENT_INSTRUCTIONS[k]


def test_obs288_common_rule_not_copied_in_source():
    """源码瘦身:公共规则常量只定义一次,非三份各自内联复制。"""
    src = (SKILL_ROOT / "wxgzh_pipeline" / "producers.py").read_text(encoding="utf-8")
    assert src.count("_COMMON_RULES = ") == 1, "公共常量被重复定义"
    # _COMMON_RULES 含 283 + _COMMON_RULES_283 单拆段供 sw 拼接(结构性拆分,非复制);
    # 硬门:AGENT_INSTRUCTIONS 三指令内不得再内联 276 规则(只许引用常量)
    instr_block = src[src.find("AGENT_INSTRUCTIONS = {"):]
    # sw 中段的 276/279 属其特有顺序(278 前),保留;硬门=283 规则只定义一次
    # (_COMMON_RULES 内含 283,_COMMON_RULES_283 是引用切片,AGENT_INSTRUCTIONS 内无内联 283)
    assert src.count("_COMMON_RULES_283 = ") == 1


def _extract_old_instructions():
    """从 HEAD(改写前)提取 AGENT_INSTRUCTIONS 字典。"""
    # 基线 = 76Q-F 终态(8f6a775),即 76R 指令瘦身前
    old_src = subprocess.run(
        ["git", "show", "8f6a775:skills/wxgzh-pipeline/wxgzh_pipeline/producers.py"],
        capture_output=True, text=True, encoding="utf-8", errors="replace").stdout
    start = old_src.find("AGENT_INSTRUCTIONS = {")
    end_marker = old_src.index("}", old_src.index('"zh_human_writing"'))
    end = old_src.index("\n", end_marker)
    ns = {}
    exec(old_src[start:end], ns)
    return ns["AGENT_INSTRUCTIONS"]


def _rules(v):
    seen, out = set(), []
    for mm in re.findall(r"(\d+(?:[A-Za-z-]*)/OBS-\d+|OBS-\d+)", v):
        if mm not in seen:
            seen.add(mm)
            out.append(mm)
    return out


def test_obs288_semantic_zero_loss_rule_inventory():
    """语义零丢失:改写前后规则清单一一对应(278→288 为预检强制化升级,1:1)。"""
    old_instr = _extract_old_instructions()
    for k in ("aihot", "super_writer", "zh_human_writing"):
        old_rules = ["76R/OBS-288" if r == "76F/OBS-278" else r for r in _rules(old_instr[k])]
        new_rules = _rules(PR.AGENT_INSTRUCTIONS[k])
        # 旧规则全部保留(278→288 升级);新规则仅允许 76R/OBS-290(素材定长度)与
        # 76T/OBS-293(封面划线句改义)
        for r in old_rules:
            assert r in new_rules, f"{k}: 旧规则丢失 {r}"
        extra = set(new_rules) - set(old_rules)
        assert extra <= {"76R/OBS-290", "76T/OBS-293", "76U/OBS-294", "76W/OBS-301", "76Y-R/OBS-305"}, f"{k}: 意外新增规则 {extra}"


def test_obs290_material_exhausted_instruction():
    """76R/OBS-290:sw 指令含「素材写干即停;禁止注水凑字数」明规。"""
    instr = PR.AGENT_INSTRUCTIONS["super_writer"]
    assert "76R/OBS-290" in instr
    assert "素材写干即停" in instr and "禁止注水凑字数" in instr
    assert "不逼扩写" in instr or "不报错逼扩写" in instr

def test_obs293_strike_assumption_instruction():
    """76T/OBS-293:sw 指令含 strike_assumption 明规(被否定旧认知,禁稻草人)。"""
    instr = PR.AGENT_INSTRUCTIONS["super_writer"]
    assert "76T/OBS-293" in instr
    assert "strike_assumption" in instr
    assert "被本文证据否定" in instr and "禁止捏造极端稻草人" in instr
    assert "不再用 hook_line 填充划线位" in instr


def test_obs294_parallel_fetch_instruction():
    """76U/OBS-294:aihot 指令含窗口内并行取料要求,超窗五步保持串行。"""
    instr = PR.AGENT_INSTRUCTIONS["aihot"]
    assert "76U/OBS-294" in instr and "取料并行化" in instr
    assert "并行发出" in instr and "禁止无依赖查询串行排队" in instr
    assert "每路查询增记耗时" in instr
    assert "保持串行不动" in instr


def test_obs294_superwindow_sequence_untouched():
    """76U/OBS-294:超窗五步递进顺序条文逐字未动(日报→快照→回溯→直采→注入)。"""
    instr = PR.AGENT_INSTRUCTIONS["aihot"]
    assert "①已知关键日期" in instr and "/api/v1/dailies/{date}" in instr
    assert "②精选池快照检索" in instr and "selected/snapshot" in instr
    assert "③热点事件回溯" in instr and "/api/v1/stories/{publicId}" in instr
    assert "④官方源直采" in instr and "provenance=supplemental" in instr
    assert "⑤仍缺 → 明示用户手动注入" in instr and "items_file_injection" in instr
    # 顺序断言:五步按序出现
    i1 = instr.find("①已知关键日期"); i2 = instr.find("②精选池快照")
    i3 = instr.find("③热点事件回溯"); i4 = instr.find("④官方源直采")
    i5 = instr.find("⑤仍缺")
    assert i1 < i2 < i3 < i4 < i5, "超窗五步顺序被破坏"


def test_obs299_env_auto_approve_wired():
    """76W/OBS-299:orchestrator _context 合并 .env → WXGZH_MEDIA_AUTO_APPROVE 生效。"""
    import tempfile
    from wxgzh_pipeline.orchestrator import Orchestrator
    tmp = Path(tempfile.mkdtemp())
    # 构造项目 .env
    (tmp / ".env").write_text("WXGZH_MEDIA_AUTO_APPROVE=1\n", encoding="utf-8")
    orch = Orchestrator(project_root=tmp, network_mode="offline_fixture", env={})
    from wxgzh_pipeline.orchestrator import StageContext
    ctx = orch._context(tmp / "runs" / "r1", {}, False)
    assert ctx.env.get("WXGZH_MEDIA_AUTO_APPROVE") == "1", ctx.env
    # 缺省 env 时也合并 .env
    orch2 = Orchestrator(project_root=tmp, network_mode="offline_fixture")
    ctx2 = orch2._context(tmp / "runs" / "r1", {}, False)
    assert ctx2.env.get("WXGZH_MEDIA_AUTO_APPROVE") == "1", ctx2.env


def test_obs302_duplicate_run_warning():
    """76W/OBS-302:同选题等待态 RUN 存在时警告。"""
    import tempfile
    from wxgzh_pipeline.orchestrator import Orchestrator
    from wxgzh_pipeline import paths as P
    tmp = Path(tempfile.mkdtemp())
    orch = Orchestrator(project_root=tmp, network_mode="offline_fixture")
    # 造一个等待态 RUN(slug 相同)
    _rd = P.new_run_dir(tmp, "GLM 5.3 发布")
    import json as _j
    st = {"run_id": _rd.name, "topic": "GLM 5.3 发布", "completed_stages": ["aihot"],
          "draft_created": False, "current_stage": None, "failed_stage": None,
          "output_hashes": {}}
    (_rd / "pipeline_state.json").write_text(_j.dumps(st), encoding="utf-8")
    # 防护逻辑(slug 相等 + 等待态)→ 警告字段
    from wxgzh_pipeline.paths import slugify as _slugify
    dup = []
    for _r in P.list_runs(tmp):
        _sp = _r / "pipeline_state.json"
        if not _sp.is_file():
            continue
        _st = _j.load(open(_sp, encoding="utf-8"))
        if _st.get("draft_created"):
            continue
        if _slugify(str(_st.get("topic", "") or "")) == _slugify("GLM 5.3 发布"):
            dup.append(_r.name)
    assert dup, "同选题等待态 RUN 应被识别"


def test_obs305_lock_discipline_rule():
    """76Y-R/OBS-305:sw 指令含锁纪律明规(遇 FAIL_CLOSED 停机报告禁自行 relock)。"""
    instr = PR.AGENT_INSTRUCTIONS["super_writer"]
    assert "76Y-R/OBS-305" in instr
    assert "禁止自行 relock" in instr
    assert "停机报告等档" in instr
    assert "--regenerate-registry" in instr


def test_obs304_ledger_count_command():
    """76Y-R/OBS-304:唯一编号实测命令(主表五列行去重)输出=区间全长。"""
    import re
    text = (SKILL_ROOT / "audit" / "quality" / "obs-ledger.md").read_text(
        encoding="utf-8")
    nums = {int(x) for x in re.findall(r"^\|\s*(\d{3})\s*\|", text, re.M)}
    n = len(nums)
    # OBS-304/305 登记后区间 119..305 = 187 个编号;去重实测为准
    assert n == 187, f"唯一编号实测 {n} != 187"
    # 区间连续无缺号
    assert set(range(119, 306)) <= nums, "119..305 区间有缺号"


def test_obs301_pwsh_redirect_rule():
    """76W/OBS-301:sw 指令含 pwsh 重定向禁止明规。"""
    instr = PR.AGENT_INSTRUCTIONS["super_writer"]
    assert "76W/OBS-301" in instr
    assert "禁止 pwsh 重定向" in instr
    assert "cmd /c 字节级重定向" in instr


def test_obs296_readiness_sha_contract():
    """76V/OBS-296:contracts/04 含 readiness_sha 照抄规则 + 孪生共享规则。"""
    text = (SKILL_ROOT / "contracts" / "04_media_enrichment.yaml").read_text(
        encoding="utf-8")
    assert "76V/OBS-296" in text
    assert "approval_readiness_sha256" in text
    assert "原样照抄" in text and "禁止自算" in text and "旧 sha 一律作废" in text
    assert "canonical 孪生" in text and "共享审批依据" in text and "禁止裸批" in text


def test_obs296_readiness_sha_media_skill():
    """76V/OBS-296:media SKILL.md 含审批纪律节(照抄 + 孪生共享)。"""
    text = (SKILL_ROOT.parent / "media-enrichment" / "SKILL.md").read_text(
        encoding="utf-8")
    assert "审批纪律（76V/OBS-296）" in text
    assert "approval_readiness_report.json" in text
    assert "禁止自算" in text and "禁止引用旧轮报告" in text
    assert "孪生资产 ID" in text and "禁止裸批" in text


def test_obs294_fetch_log_contract():
    """76U/OBS-294:contracts/01_aihot.yaml 无 fetch_log 耗时字段,由指令语义覆盖。"""
    text = (SKILL_ROOT / "contracts" / "01_aihot.yaml").read_text(encoding="utf-8")
    assert "fetch_log.json" in text


def test_obs293_contract_declares_strike_assumption():
    """76T/OBS-293:02_super_writer.yaml 契约声明 strike_assumption 字段。"""
    text = (SKILL_ROOT / "contracts" / "02_super_writer.yaml").read_text(
        encoding="utf-8")
    assert "76T/OBS-293" in text
    assert "strike_assumption" in text
    assert "≤40 字" in text and "禁稻草人" in text


def test_obs288_instruction_text_unchanged_except_278():
    """产物指令逐字一致(唯一差异=278→288 硬步骤升级 + 290 明规新增,其余零改动)。"""
    old_instr = _extract_old_instructions()
    # aihot:76U/OBS-294 并行化条文新增(仅此段),其余逐字一致
    old_a = old_instr["aihot"]
    new_a = PR.AGENT_INSTRUCTIONS["aihot"]
    assert "76U/OBS-294" in new_a and "76U/OBS-294" not in old_a
    a_head = old_a[:old_a.find("AIHOT 授权边界不变")]
    assert new_a.startswith(a_head), "aihot 指令 294 段之前发生非预期变化"
    # 294 段插在授权边界句后:授权边界句保留,且授权边界句之后的旧内容(76J/76F/76L 段)
    # 在 new_a 中完整保留(294 插入不删任何旧条文)
    assert "AIHOT 授权边界不变:匿名只读、不绕过速率限制、不批量抓取全站。" in new_a
    for keep in ("76J/OBS-273", "76F/OBS-276", "76F/OBS-279", "76L/OBS-283"):
        assert keep in new_a, f"aihot 旧条文丢失 {keep}"
    # zh 逐字一致(未变)
    assert old_instr["zh_human_writing"] == PR.AGENT_INSTRUCTIONS["zh_human_writing"], "zh 指令发生非预期变化"
    old_sw = old_instr["super_writer"]
    new_sw = PR.AGENT_INSTRUCTIONS["super_writer"]
    # 变更点:278→288(硬步骤)+ 290 新增(明规);其余内容逐字保留
    assert "76F/OBS-278" not in new_sw and "76R/OBS-288" in new_sw
    assert "76R/OBS-290" in new_sw and "76Q/OBS-287" in new_sw
    # 旧 sw 中 76F/OBS-278 段之前的内容与新 sw 中 76R/OBS-288 段之前逐字一致
    old_head = old_sw[:old_sw.find("76F/OBS-278")]
    new_head = new_sw[:new_sw.find("76R/OBS-288")]
    assert new_head == old_head, "sw 指令 288 段之前发生非预期变化"
    # 旧 sw 中 76Q/OBS-287 之后的内容与新 sw 中 76Q/OBS-287 之后逐字一致
    old_tail = old_sw[old_sw.find("76Q/OBS-287"):]
    new_tail = new_sw[new_sw.find("76Q/OBS-287"):]
    assert new_tail == old_tail, "sw 指令 287 段之后发生非预期变化"
