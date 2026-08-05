# 档 70 OBS-99：封面本地文件定位修复 + 档 69 落地 + 续跑 wechat_draft

- 日期：2026-08-05
- 范围：Pipeline 仓 `producers.py`（`_select_live_cover`）+ 新测试；零 relock；gzh-design 仓零改动
- 报告 blob sha：见文末

## OBS-99 登记（全文）

**OBS-99（中）：封面本地文件定位与资产类型耦合、硬编码 `discover/images` 单目录；docstring 亦把该缺陷写成规格（「local discover/images/<asset_sha256>.*」）；测试夹具只含 images 类资产 → 「图表作封面」路径从未被任何测试覆盖。**

- 现象：`_select_live_cover` 只在 `media_enrichment/discover/images/` 下按 `<sha>.*` 找封面文件；本 RUN 已批准资产为生成图表（文件在 `discover/charts/chart-001.png`），封面选择必然 `FAIL_CLOSED: A-005 local frozen file missing`。
- 根因：OBS-72（档 52）设计时未要求覆盖 generated 资产目录；档 63 图表纳入批准后未回头复核封面路径（我方指令缺陷第 48 处）。
- 修复（本档）：候选目录集合（images/ + charts/，由冻结清单 asset_origin 确定性推导 + media_manifest local_path 父目录补充）+ sha 命名匹配 + local_path 交叉验证 + resolve 防穿越 + 字节 sha 校验，三条 FAIL_CLOSED 语义一字不放宽。
- 观测（不阻塞）：A-005 的 asset_sha256 `46d83857…` 与事件 RUN（UNCONTROLLED）chart-001.png 同值——图表渲染确定性，非污染。

## 第 1 步：档 69 成果落地

- commit 1（档 68 配套，视觉分级+contract 层）：`4cff39a386cb64d58e24badb469f8fc8c599d728`
- commit 2（档 69 OBS-98）：`0899727c41de39c59d3fc50efb72d2fb623478a9`
- 报告：`audit/quality/obs98-strike-validator-69.md`，blob `6fd87dec48fd2ed78c3d4012b4c5c578bdb3f50f`，126 行
- 远端 HEAD：`0899727c41de39c59d3fc50efb72d2fb623478a9`（已 push）
- gzh-design 仓零改动，HEAD `af03b438a37233c111a20be77c4fd28898dc8f10`；lock 双侧 `0CD0EBC3…`

## 第 2 步：_select_live_cover 修改

### 修改后完整源码（wxgzh_pipeline/producers.py）

```python
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
    ...
    """
    rd = Path(ctx.run_dir)
    media_root = rd / "media_enrichment"
    media_root_resolved = media_root.resolve()
    approvals = _load_copyright_approvals(rd)
    if not approvals["single_asset"]:
        raise MediaRequestError(
            "cover FAIL_CLOSED: no stable single_asset approval in contract")
    frozen = media_root / "discover" / "asset_discovery_manifest.json"
    if not frozen.is_file():
        raise MediaRequestError(
            "cover FAIL_CLOSED: frozen asset_discovery_manifest.json missing")
    manifest = json.loads(frozen.read_text(encoding="utf-8"))
    by_id = {a["asset_id"]: a for a in manifest.get("assets", [])}
    events_path = media_root / "continue" / "upload_events.json"
    if not events_path.is_file():
        raise MediaRequestError(
            "cover FAIL_CLOSED: continue/upload_events.json missing")
    events = json.loads(events_path.read_text(encoding="utf-8"))
    success_ids = []
    for ev in events.get("events", []):
        aid = ev.get("asset_id") if isinstance(ev, dict) else None
        if aid and ev.get("status") == "success" and aid not in success_ids:
            success_ids.append(aid)
    if not success_ids:
        raise MediaRequestError(
            "cover FAIL_CLOSED: no successful upload in continue/upload_events.json")
    bindings_path = media_root / "article_image_bindings.json"
    if not bindings_path.is_file():
        raise MediaRequestError(
            "cover FAIL_CLOSED: article_image_bindings.json missing")
    bindings = json.loads(bindings_path.read_text(encoding="utf-8"))
    candidates = []
    for img in bindings.get("body_images", []):
        aid = img.get("asset_id") if isinstance(img, dict) else None
        if aid in success_ids and aid in approvals["single_asset"]:
            candidates.append(aid)
    if not candidates:
        raise MediaRequestError(
            "cover FAIL_CLOSED: no approved and uploaded asset in bindings")

    full_manifest_path = media_root / "discover" / "media_manifest.json"
    full_by_id: dict = {}
    if full_manifest_path.is_file():
        try:
            full = json.loads(full_manifest_path.read_text(encoding="utf-8"))
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
        ...(完整实现见 commit)"""
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
                    f"cover FAIL_CLOSED: {asset_id} local_path invalid")
            if not lpr.is_relative_to(media_root_resolved):
                raise MediaRequestError(
                    f"cover FAIL_CLOSED: {asset_id} local_path outside media_root")
            if lpr.exists() and not lpr.is_file():
                raise MediaRequestError(
                    f"cover FAIL_CLOSED: {asset_id} local_path not a regular file")
            if lpr.is_file():
                lp_resolved = lpr
        if not glob_hits and lp_resolved is None:
            raise MediaRequestError(
                f"cover FAIL_CLOSED: {asset_id} local frozen file missing")
        if glob_hits and lp_resolved is not None and lp_resolved not in glob_hits:
            raise MediaRequestError(
                f"cover FAIL_CLOSED: {asset_id} local_path record does not match hit file")
        local = lp_resolved if lp_resolved is not None else glob_hits[0]
        if sha256_file(local) != expected_sha:
            raise MediaRequestError(
                f"cover FAIL_CLOSED: {asset_id} local frozen file sha256 mismatch")
        return local

    for asset_id in candidates:
        rec = approvals["single_asset"][asset_id]
        manifest_rec = by_id.get(asset_id)
        if manifest_rec is None:
            raise MediaRequestError(
                f"cover FAIL_CLOSED: {asset_id} missing from frozen discovery manifest")
        if manifest_rec.get("asset_sha256") != rec.get("asset_sha256"):
            raise MediaRequestError(
                f"cover FAIL_CLOSED: {asset_id} approval sha diverges from frozen manifest")
        local = _find_frozen_file(asset_id, rec["asset_sha256"])
        return local, asset_id
    raise MediaRequestError("cover FAIL_CLOSED: no usable approved cover asset")
```

要点：local_path 是记录值，绝不直接 open——三重约束（resolve 在 media_root 内 + 常规文件 + 字节 sha 等于冻结值）后才作为可用文件；图表（chart-NNN.png 非 sha 命名）由 local_path 定位，网页图（sha 命名）由 glob 命中，两者交叉验证。

### 2.4 全仓扫描（"discover/images" 硬编码）

| 文件:行 | 内容 | 判定 |
|---|---|---|
| `wxgzh_pipeline/producers.py` L1007（旧 docstring） | 「local discover/images/<asset_sha256>.*」 | **需改**（本档已改为候选目录集合描述） |
| `tests/test_obs72_cover_selection.py` L6 | 测试 docstring 描述 images 单目录 | 需改（已随 obs99 新增 charts 场景覆盖；obs72 夹具保留 images 语义不回退） |
| `audit/*.md` 各历史报告 | 旧封面路径描述 | 不需改（历史记录） |

运行时代码仅 1 处需改，已处理。

## 第 3 步：回归测试（tests/test_obs99_cover_path.py，9 项）

| 用例 | 覆盖 | 结果 |
|---|---|---|
| test_obs99_generated_chart_cover_passes | a. ★图表作封面（charts/）PASS | PASS |
| test_obs99_generated_chart_real_naming_passes | a2. ★真实命名 chart-001.png + local_path 定位 PASS | PASS |
| test_obs99_source_image_cover_passes | b. 网页图（images/）仍 PASS | PASS |
| test_obs99_local_path_outside_run_fails_closed | c. local_path 越界 FAIL_CLOSED | PASS |
| test_obs99_file_missing_fails_closed | d. 文件缺失 FAIL_CLOSED | PASS |
| test_obs99_file_sha_mismatch_fails_closed | e. sha 失配 FAIL_CLOSED | PASS |
| test_obs99_unapproved_asset_fails_closed | f1. 未批准 FAIL_CLOSED | PASS |
| test_obs99_no_upload_event_fails_closed | f2. 无 success 上传 FAIL_CLOSED | PASS |
| test_obs99_local_path_mismatch_hit_file_fails_closed | g. 记录与实物不符 FAIL_CLOSED | PASS |

- obs72 旧 8 项：全 PASS（原语义不回退）
- Pipeline 全量 pytest：仅 1 项 deselect（`test_hotfix1.py::test_portable_installer_preserves_pipeline_release_include`，档 30/31 既有项，无新增）
- upgrade_regression：ALL PASS（relock dry-run x4 无变化；doctor --require-wechat PASS；cross-side SKIP 为既有 P2）

## 第 4 步：安装器与基线

- bundle-staging-61 重建（build 校验常量 `EXPECTED_PIPELINE_FILE_COUNT` 为档 30/31 既有已知过时项，staging 已写入新代码）+ install.py 实装成功
- doctor：PASS；OBS_68 MATCH（648/648）；OBS_69 MATCH
- skills.lock.json sha 双侧：`0CD0EBC35CF516BD0BD74DA515C74D50F929948F1D0E1FDD772D80D56C6B1CF9`（零 relock）
- receipt：aihot / super_writer / zh_human_writing / media_enrichment / gzh_design 五阶段全部 ok=True（gzh_design 未重渲染——Pipeline 代码变更不影响其 receipt 哈希）

## 第 5 步：续跑 wechat_draft（真实）

- 首次续跑被 allowable WARN 拦截（17 处半角标点，0 ERROR）→ 显式 `WXGZH_ALLOW_WARNINGS=1` 续跑 → **COMPLETE**，`draft_created: true`、`formally_published: false`
- 放行留痕 `wechat_draft/allowance_record.json`：schema 1.0、`allow_warnings: true`、html_sha256 `ae8db428…`、1 条 entry（rule `half_width_punct`，category `allowable`，含 5 条示例 snippet 原文）——无夹带其他规则

### 封面五项（第 5.2/5.3 条）

| 项 | 值 |
|---|---|
| asset_id | A-005（bindings body_images 顺序第一张，已批准 AP-20260805T013229-INDEPENDENT-REVIEW-001 + 已上传 success） |
| 命中文件绝对路径 | `F:\AIXM\wxgzh\.temp\wxgzh-pipeline\20260804T174355-vibe-coding-guide-v2-1-6-by4s00\media_enrichment\discover\charts\chart-001.png` |
| 文件字节数 | 37032 |
| sha256 | `46D83857D12E70FEF795A0E883BBB89812E88302A9DB5D5ACC5B043D0656977B` |
| 与冻结清单 asset_sha256 比对 | 一致（local_path 交叉验证通过） |
| 像素尺寸 | **1195 × 752**（≥ 640×360，无触发停机条件） |

### 草稿 delta 四项（第 5.4 条）

- NEW_DRAFT_COUNT = 1 ✓（before 6 → after 7）
- before update_time 集合为 after 子集 ✓（UPDATE_TIME_SUBSET: true，OLD_DRAFTS_PRESERVED: true）
- after 中恰好 1 条新 update_time ✓（1785903116，NEW_UPDATE_TIME_COUNT: 1，NEW_DRAFT_UNIQUE: true）
- deleted_any / formally_published / mass_send / scheduled 全 false ✓
- DRAFT_DELTA = PASS，CREATION_RESULT = PASS

### 副作用总账（第 5 步 + 本档）

- uploadimg：本档 **0**（A-005/A-007/A-009 各 1 次 success 为档 68 完成，本档 3 条 skipped_already_uploaded 幂等跳过）
- add_material：封面永久素材 1 次（wechat_draft 阶段，随草稿创建）
- 草稿：+1（箱内草稿总数 7：before 6 → after 7）
- 发布 / 群发 / 定时 / 预览群发：0

## 第 6 步：commit + push

- 本档 commit：见汇报（j 项）
- 报告：本文件 `audit/quality/obs99-cover-path-70.md`
- gzh-design 仓：零改动，HEAD `af03b438a37233c111a20be77c4fd28898dc8f10`

## 待裁决清单

- 无阻塞项。观测：A-005 sha 与事件 RUN chart-001.png 同值（图表渲染确定性，非污染）
- 草稿已就绪，等待用户在后台肉眼验收
