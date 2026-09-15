"""77AK/OBS-388:super_writer 单节回滚重试路径测试。

覆盖:
1. 单节失败注入 → 只重跑该节(失败校验器跑 2 次,其余校验器与它们的 stdout 落盘
   产物哈希不变);
2. 重组装逐字节无损(split→reassemble 恒等;朴素 join 会丢标题行/丢行尾换行);
3. 旧调用兼容:ctx 无 section_retry_driver / 失败节数非 1 → 零重跑,失败语义照旧。
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

import wxgzh_pipeline.producers as PR
from wxgzh_pipeline import agent_handshake as AH
from wxgzh_pipeline import section_retry as SR

FAILING = "validate_article_length.py"

ARTICLE_OLD = """# 主标题

导语一句话。

## 第一节

旧正文一行。

## 第二节

第二节正文保持不变。

## 第三节

第三节正文保持不变。
"""

ARTICLE_NEW = """# 主标题

导语一句话。

## 第一节

新正文一行(77AK 单节重跑)。

## 第二节

第二节正文保持不变。

## 第三节

第三节正文保持不变。
"""


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _seed_stage(sd: Path, article: str = ARTICLE_OLD) -> None:
    """super_writer 阶段目录种子:agent 应产出的 13 件 + registry + article。"""
    sd.mkdir(parents=True, exist_ok=True)
    names = list(PR.EM.AGENT_EXPECTED_OUTPUTS["super_writer"])
    for name in names:
        body = article if name == "article.md" else f"# {name}\n"
        (sd / name).write_text(body, encoding="utf-8")
    project = sd.parent
    (project / "super_writer").mkdir(parents=True, exist_ok=True)
    (project / "super_writer" / "canonical_claim_registry.json").write_text(
        json.dumps({"claims": [], "materials": []}, ensure_ascii=False),
        encoding="utf-8")


def _validators(article_path: Path):
    """五点官方校验链(与 _agent_validator_args 同名同序);article 校验器的
    --article 指向真实阶段文件(失败注入挂在这里),其余 argv 无关紧要。"""
    return [
        ("super-writer", "scripts/material_ingestion.py", ["--ledger", "x", "--output", "y"]),
        ("super-writer", "scripts/validate_article_length.py",
         ["--article", str(article_path), "--json"]),
        ("super-writer", "scripts/validate_semantic_map.py",
         ["--article", str(article_path)]),
        ("super-writer", "scripts/validate_single_product.py",
         ["--product", "article", "--file", str(article_path)]),
        ("super-writer", "scripts/validate_single_product.py",
         ["--product", "registry", "--file", "x"]),
    ]


def _rec(script, exit_code, stdout=""):
    def sha(text):
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    return {"command": [str(script)], "exit_code": exit_code, "stdout": stdout, "stderr": "",
            "stdout_sha256": sha(stdout), "stderr_sha256": sha(""),
            "elapsed_seconds": 0.0, "script_path": str(script),
            "script_sha256": sha(str(script))}


class _Recorder:
    """假 run_script:按脚本名计次;article 长度校验在首见旧正文时 exit 1。

    sections=1 → 失败报告自报「失败节=1」(单节粒度,进重试路径);
    sections=2 → 整篇级失败(不进重试路径,保留整阶段重跑语义)。
    """

    def __init__(self, failing_name: str | None = FAILING, sections: int = 1):
        self.failing_name = failing_name
        self.sections = sections
        self.calls: list[str] = []

    def __call__(self, script, args=None, cwd=None, timeout=None, env=None, python=None):
        name = Path(script).name
        self.calls.append(name)
        text = ""
        for i, arg in enumerate(args or []):
            if arg == "--article" and i + 1 < len(args):
                p = Path(args[i + 1])
                if p.is_file():
                    text = p.read_text(encoding="utf-8")
        if name == self.failing_name:
            if "旧正文一行" in text:
                return _rec(script, 1, json.dumps({"passed": False, "sections": self.sections,
                                                   "errors": ["section visible chars"]}))
            return _rec(script, 0, json.dumps({"passed": True, "sections": self.sections,
                                               "errors": []}))
        return _rec(script, 0, f"[fake] {name} PASS")


def _driver(calls: list, header: str = "第一节"):
    """失败节重生成 driver:按标题定位失败节,返回重生成后的节原文。"""
    def hook(ctx, stage, sd, article, retry):
        retry.header = header
        assert retry.locate(), f"section {header!r} not found"
        calls.append((stage, retry.located_index, retry.section_text()))
        return f"## {header}\n\n新正文一行(77AK 单节重跑)。\n\n"
    return hook

def _run_agent(tmp_path, monkeypatch, *, driver, recorder, snapshot: dict | None = None):
    sd = tmp_path / "super_writer"
    _seed_stage(sd)
    (sd / "stage_request.json").write_text("{}", encoding="utf-8")
    if snapshot is not None:      # 调用前的阶段目录快照(逐文件哈希)
        snapshot.update({p.name: _hash(p) for p in sorted(sd.iterdir()) if p.is_file()})
    ctx = SimpleNamespace(run_dir=tmp_path, network_mode="fake_live",
                          skills_home=tmp_path / "skills", env={}, discovery={},
                          fake_agent=None, fixture_dir=tmp_path / "fixtures",
                          section_retry_driver=driver)
    state = SimpleNamespace(run_id="run-77ak", topic="t", final_article_sha256=None,
                            items_file=None)
    monkeypatch.setattr(PR, "_agent_validator_args",
                        lambda stage, ctx, sd: _validators(sd / "article.md"))
    monkeypatch.setattr(PR, "run_script", recorder)
    expected = list(PR.EM.EXPECTED_OUTPUTS["super_writer"])
    agent_expected = list(PR.EM.AGENT_EXPECTED_OUTPUTS["super_writer"])
    outputs, meta = PR._agent(ctx, "super_writer", sd, expected, agent_expected, state)
    return sd, outputs, meta


# ---------- 1. 单节失败注入:只重跑该节 ----------

def test_single_section_failure_reruns_only_that_section(tmp_path, monkeypatch):
    recorder = _Recorder()
    hook_calls: list = []
    sd, outputs, meta = _run_agent(tmp_path, monkeypatch, driver=_driver(hook_calls),
                                  recorder=recorder)
    # 失败校验器首跑 1 次 + 单节重试 1 次 = 2;其余校验器各 1 次(零重跑)
    assert recorder.calls.count(FAILING) == 2, recorder.calls
    for name in ("material_ingestion.py", "validate_semantic_map.py"):
        assert recorder.calls.count(name) == 1, (name, recorder.calls)
    # 首跑链里 validate_single_product 出现两次(article + registry),重试后仍是两次
    assert recorder.calls.count("validate_single_product.py") == 2, recorder.calls
    assert len(hook_calls) == 1, "driver 应只被调用一次(重试一轮)"
    assert hook_calls[0][1] == 1, "定位到的节序号=第一节(preamble 为第 0 节)"
    assert hook_calls[0][2].startswith("## 第一节"), hook_calls[0][2]
    # 重试后失败清零,阶段不判失败
    assert "official_validator_failed" not in meta, meta.get("official_validator_failed")
    assert meta["section_retry"]["attempts"] == 1
    assert meta["section_retry"]["validators_rerun"] == []


def test_single_section_retry_keeps_other_artifacts_byte_identical(tmp_path, monkeypatch):
    before: dict = {}
    recorder = _Recorder()
    sd, outputs, meta = _run_agent(tmp_path, monkeypatch, driver=_driver([]),
                                  recorder=recorder, snapshot=before)
    agent_expected = list(PR.EM.AGENT_EXPECTED_OUTPUTS["super_writer"])
    # 只有 article.md 变;其余阶段文件逐字节不变(重试只写失败节所在文件)
    assert (sd / "article.md").read_text(encoding="utf-8") == ARTICLE_NEW
    after = {p.name: _hash(p) for p in sorted(sd.iterdir()) if p.is_file()}
    # 新增文件仅限:握手三件套 + 首跑/重跑的校验器 stdout 落盘 + full_mode 报告
    new_files = set(after) - set(before)
    assert new_files == {"agent_handshake_request.json", AH.ACK_FILE, "HANDSHAKE.md",
                         "material_ingestion.stdout.json",
                         "validate_article_length.stdout.json",
                         "validate_semantic_map.stdout.json",
                         "validate_single_product.stdout.json",
                         "full_mode_validator_report.json"}, new_files
    # 既有文件里只有 article.md 内容变了(token 随新字节重写属新增文件,见上)
    changed = {name for name in before if name in after and before[name] != after[name]}
    assert changed == {"article.md"}, changed
    # 未重跑的校验器 stdout 落盘产物 = 首跑原样(重跑会改这三个文件)
    for name in ("material_ingestion.stdout.json", "validate_semantic_map.stdout.json",
                 "validate_single_product.stdout.json"):
        assert (sd / name).read_text(encoding="utf-8") == f"[fake] {name.replace('.stdout.json', '.py')} PASS"
    # 失败校验器自身的 stdout 产物随重跑更新(单一产物,非其余产物)
    assert json.loads((sd / "validate_article_length.stdout.json").read_text(
        encoding="utf-8"))["passed"] is True
    assert json.loads((sd / "full_mode_validator_report.json").read_text(
        encoding="utf-8"))["passed"] is True
    # ACK token 按新文章字节重算(agent_handshake L104-111/L146 口径)
    ack = json.loads((sd / AH.ACK_FILE).read_text(encoding="utf-8"))
    ok, hs = AH.verify_ack(sd, "super_writer", agent_expected, run_dir=tmp_path)
    assert ok and hs["token_ok"], hs
    assert ack["agent_id"] == "fake-agent", "重 ACK 必须沿用原 agent_id"
    assert "article.md" in [p.name for p in outputs], [p.name for p in outputs]


def test_single_section_retry_bounded_by_explicit_constant(tmp_path, monkeypatch):
    """重试上限=显式常量;driver 不修好 → 超上限后失败语义照旧(不无限循环)。"""
    recorder = _Recorder()
    hook_calls: list = []

    def stubborn(ctx, stage, sd, article, retry):
        hook_calls.append(stage)
        retry.header = "第一节"
        assert retry.locate()
        retry.rewrite_section(retry.section_text())   # 原样写回=没修好
        return retry.section_text()

    sd, outputs, meta = _run_agent(tmp_path, monkeypatch, driver=stubborn,
                                  recorder=recorder)
    assert len(hook_calls) == PR.SECTION_RETRY_MAX_ATTEMPTS == 1
    assert recorder.calls.count(FAILING) == 2      # 首跑 + 上限内 1 轮
    assert meta["official_validators"][1]["exit_code"] == 1
    assert meta["official_validator_failed"], "超上限后必须保留既有失败语义"


# ---------- 2. 重组装无损 ----------

@pytest.mark.parametrize("text", [
    ARTICLE_OLD,
    "# T\n\nlead\n\n## A\nbody\n",
    "## A\n```bash\n# not a heading\necho 1\n```\ntail\n## B\nlast\n",
    "## H1\n## H2\nbody\n",
    "no heading at all\nline2\n",
    "# T\nbody-no-trailing",
    "pre\n# H\n\n## A\n\n## B\nend",
    "",
])
def test_reassemble_is_byte_lossless(text):
    assert SR.reassemble(SR.split_sections(text)) == text


def test_naive_join_would_lose_heading_lines():
    """朴素 join(丢标题行/丢行尾换行)与本节 assemble 的差异坐实。"""
    sections = SR.split_sections(ARTICLE_OLD)
    naive = "".join(s["text"].split("\n", 1)[-1] for s in sections)
    assert "# 第一节" not in naive
    assert "# 第一节" in SR.reassemble(sections)
    assert SR.reassemble(sections) == ARTICLE_OLD
    assert SR.reassemble_preserving_headings(ARTICLE_OLD, sections) == ARTICLE_OLD


def test_reassemble_preserving_headings_rejects_heading_loss():
    sections = SR.split_sections(ARTICLE_OLD)
    sections[1]["text"] = "旧正文一行。\n"      # 丢了标题行
    with pytest.raises(ValueError):
        SR.reassemble_preserving_headings(ARTICLE_OLD, sections)


def test_section_retry_guards_other_section_edits(tmp_path):
    """driver 顺手动别的节 → unchanged() False(单节回滚边界,拒写)。"""
    article = tmp_path / "article.md"
    article.write_text(ARTICLE_OLD, encoding="utf-8")
    retry = SR.SectionRetry(article, header="第一节")
    assert retry.locate() and retry.located_index == 1
    retry.rewrite_section("## 第一节\n\n新正文\n")
    assert retry.unchanged() is True
    retry._sections[2]["text"] = "被动过的第二节\n"
    assert retry.unchanged() is False


def test_section_retry_write_back_keeps_other_sections_verbatim(tmp_path):
    article = tmp_path / "article.md"
    article.write_text(ARTICLE_OLD, encoding="utf-8")
    retry = SR.SectionRetry(article, header="第一节")
    assert retry.locate() and retry.located_index == 1
    others_before = retry.other_section_texts()
    retry.rewrite_section("## 第一节\n\n新正文\n")
    retry.write_back()
    after = SR.SectionRetry(article, header="第一节")
    assert after.locate() and after.located_index == 1
    assert after.other_section_texts() == others_before


# ---------- 3. 旧调用兼容 ----------

def test_legacy_call_without_driver_keeps_full_stage_semantics(tmp_path, monkeypatch):
    """ctx 无 driver(旧调用形态)→ 零重跑、零 section_retry、失败语义照旧。"""
    recorder = _Recorder()
    sd, outputs, meta = _run_agent(tmp_path, monkeypatch, driver=None, recorder=recorder)
    assert recorder.calls.count(FAILING) == 1
    assert "section_retry" not in meta
    assert meta["official_validator_failed"], "无 driver 必须保留整阶段重跑语义"
    assert (sd / "article.md").read_text(encoding="utf-8") == ARTICLE_OLD


def test_legacy_call_ctx_without_attribute_is_supported(tmp_path, monkeypatch):
    """旧 SimpleNamespace ctx 连 section_retry_driver 属性都没有 → 不得抛异常。"""
    recorder = _Recorder()
    sd = tmp_path / "super_writer"
    _seed_stage(sd)
    (sd / "stage_request.json").write_text("{}", encoding="utf-8")
    ctx = SimpleNamespace(run_dir=tmp_path, network_mode="fake_live",
                          skills_home=tmp_path / "skills", env={}, discovery={},
                          fake_agent=None, fixture_dir=tmp_path / "fixtures")
    state = SimpleNamespace(run_id="run-77ak", topic="t", final_article_sha256=None,
                            items_file=None)
    monkeypatch.setattr(PR, "_agent_validator_args",
                        lambda stage, ctx, sd_: _validators(sd / "article.md"))
    monkeypatch.setattr(PR, "run_script", recorder)
    expected = list(PR.EM.EXPECTED_OUTPUTS["super_writer"])
    agent_expected = list(PR.EM.AGENT_EXPECTED_OUTPUTS["super_writer"])
    outputs, meta = PR._agent(ctx, "super_writer", sd, expected, agent_expected, state)
    assert recorder.calls.count(FAILING) == 1
    assert meta["official_validators"][1]["exit_code"] == 1
    assert "official_validator_failed" in meta


def test_whole_article_failure_is_not_section_scoped(tmp_path, monkeypatch):
    """失败报告自报 sections=2(整篇级)→ 不进单节路径,保留整阶段重跑语义。"""
    hook_calls: list = []
    sd, outputs, meta = _run_agent(tmp_path, monkeypatch, driver=_driver(hook_calls),
                                  recorder=_Recorder(sections=2))
    assert hook_calls == [], "整篇级失败不得触发单节重生成"
    assert "section_retry" not in meta
    assert meta["official_validator_failed"]
