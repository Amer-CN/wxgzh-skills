# 档 39 — OBS-53 补丁回流 media-enrichment 并重锁:第一步取证报告(停机)

- 报告编号:obs53-backflow-39
- 执行日期:2026-08-02(Asia/Shanghai)
- 执行状态:**第一步第 2 项判定不通过,按指令「若存在与 OBS-53 无关的改动,单独列出并停机上报」停机。未执行第二步起任何操作(未建分支、未 push、未 relock、未 clone、未改 sibling、未跑测试)。**
- 工作副本:`F:\AIXM\wxgzh\repos\wxgzh-pipeline`(branch `dev/0.1.0-dev2`,HEAD `a706dbd`,档 38)
- 唯一写入:本报告。全程未触碰 `.agents\skills`、未调微信接口、未跑 Pipeline、未删除任何文件、未执行任何安装器/relock --apply。

---

## 一、环境快照(只读)

| 项 | 值 |
|---|---|
| lock(仓库侧)media `skill_root_sha256` | `0d8aea2169cec17c4e9f95af66b6b4da3c532554a0a316fe3fb604bd0b7ab3a3` |
| lock media `runtime_manifest_sha256` | `172aa1b8082c6bb80822e56e201732ba5a118c6a53d7472f34b911f4a891e996` |
| lock media `runtime_file_count` | 57 |
| lock media `full_commit_sha` | `cedf92ca45b0cdb7e010d489e9da67dd28ef6e59` |
| lock media `source_tree_sha` | `c2b914a2cbe3ca8880d0b4b7525cc8adc7a5ce68` |
| lock media `entrypoint_sha256` | `2d877a93b37658bb5b2e247827952a86abe11fff5a9c148024238dd0cccd979f` |
| 安装侧 lock sha | `A9E07EF42017CFF225158466213253BAF1155F34A7C2F1BDAF62A87DBBC751D6`(与仓库侧 lock 逐字一致) |
| 安装树 media 实算 root / manifest / count | `0d8aea21…` / `172aa1b8…` / 57(与 lock 逐字一致,`skill_discovery.compute_root_sha` 口径,CRLF→LF 归一) |
| 24S 暂存树 `.temp\obs62s-build-staging\portable-bundle\locked-skills\media-enrichment` | 与安装树逐文件内容 diff = 0(即 lock 的补丁态树唯一权威副本两处一致) |
| sibling checkout `F:\AIXM\wxgzh\repos\media-enrichment` | HEAD = `cedf92ca`,工作树干净;`git ls-remote` 确认远端 `chore/wxgzh-pipeline-dev2-integration` = `cedf92ca`、`main` = `68076ed` |
| sibling 树实算 root | `b82574698376d1c8e011846db51ce3946e2ada2ffe11ed8e208072c16a7bd2f2`(manifest `172aa1b8…`、count 57 —— 文件清单相同,内容不同) |

结论:远端 cedf92ca 树 ≠ lock 补丁态树(仅文件清单相同);lock 的 root `0d8aea21` 无远端权威副本,与档 37 已查明事实一致。

## 二、第一步第 1 项:完整 diff(cedf92ca 基准 → 补丁态树)

生成方式:`git diff --no-index`(sibling 工作树 vs 安装树),按文件逐份生成;5 个文件存在内容差异,其余文件(含 .git/.github/__pycache__ 等非 runtime 项)无差异。全文如下。


### 2.1 scripts/run_media_enrichment.py(runtime,lock entrypoint)

````diff
diff --git "a/repos\\media-enrichment\\scripts\\run_media_enrichment.py" "b/.agents\\skills\\media-enrichment\\scripts\\run_media_enrichment.py"
index f31cedd..a1143af 100644
--- "a/repos\\media-enrichment\\scripts\\run_media_enrichment.py"
+++ "b/.agents\\skills\\media-enrichment\\scripts\\run_media_enrichment.py"
@@ -26,7 +26,9 @@ from media_enrichment.image_inspector import inspect_image
 from media_enrichment.image_deduplicator import deduplicate_asset, DedupState
 from media_enrichment.image_classifier import classify_image
 from media_enrichment.chart_generator import build_chart_specs, generate_chart
-from media_enrichment.uploader import create_uploader, scan_for_secrets, timed_upload
+from media_enrichment.uploader import (
+    create_uploader, normalize_wechat_url, scan_for_secrets, timed_upload,
+)
 from media_enrichment.placement_planner import find_anchors
 from media_enrichment.manifest_builder import ManifestBuilder, AssetRecord
 from media_enrichment.asset_approval import (
@@ -90,6 +92,21 @@ def main():
     upload_mode = "dry_run" if args.phase == "discover" else requested_upload_mode
     # dev2-hotfix2: serial upload event log (proves no overlap, one attempt/asset)
     upload_events: list = []
+    existing_upload_events: dict[str, dict] = {}
+    if args.phase == "continue":
+        events_path = output_dir / "upload_events.json"
+        if events_path.is_file():
+            try:
+                prior_events = json.loads(
+                    events_path.read_text(encoding="utf-8")).get("events", [])
+                upload_events.extend(prior_events)
+                for event in prior_events:
+                    if (event.get("status") == "success"
+                            and event.get("url")
+                            and normalize_wechat_url(event.get("url"))):
+                        existing_upload_events[event["asset_id"]] = event
+            except (OSError, ValueError, TypeError):
+                builder.errors.append("existing upload_events.json is invalid")
 
     # Validate upload_mode. Discovery is side-effect-free regardless of request.
     try:
@@ -115,12 +132,136 @@ def main():
     # offline image "downloads" read from a sibling images/ fixture dir (no network)
     fixture_images_dir = Path(fixture_dir).parent / "images"
 
+    # OBS-42: continuation consumes the exact bytes persisted by discovery.
+    # It never re-fetches source pages or re-downloads approved assets.
+    if args.phase == "continue":
+        if not args.discovery_manifest:
+            builder.errors.append("continue phase requires --discovery-manifest")
+        else:
+            frozen_path = Path(args.discovery_manifest)
+            discover_manifest_path = frozen_path.parent / "media_manifest.json"
+            try:
+                approved_discovery = json.loads(frozen_path.read_text(encoding="utf-8"))
+                discovery_file_valid, _ = verify_discovery_manifest(approved_discovery)
+                if not discovery_file_valid:
+                    builder.errors.append(
+                        "approval_identity_mismatch: discovery manifest sha256 invalid")
+                discover_manifest = json.loads(
+                    discover_manifest_path.read_text(encoding="utf-8"))
+                discovered_assets = {
+                    item["asset_id"]: item for item in discover_manifest.get("assets", [])
+                }
+                discovered_asset_records = {
+                    asset_id: AssetRecord(**item)
+                    for asset_id, item in discovered_assets.items()
+                }
+                for record in discovered_asset_records.values():
+                    builder.add_asset(record)
+                frozen_records = {
+                    item["asset_id"]: item
+                    for item in approved_discovery.get("assets", [])
+                }
+                discovery_records.extend(approved_discovery.get("assets", []))
+                images_root = (frozen_path.parent / "images").resolve()
+                material_approved_ids = {
+                    asset_id for asset_id, frozen in frozen_records.items()
+                    if (materials_by_id.get(frozen["material_id"], {})
+                        .get("copyright_review", {}).get("status") == "known_allowed")
+                }
+                upload_candidate_ids = set(asset_approvals) | material_approved_ids
+                if len(upload_candidate_ids) > len(asset_approvals):
+                    builder.errors.append(
+                        "approved upload candidate count exceeds explicit "
+                        "copyright approval asset count")
+                    upload_candidate_ids = set()
+
+                for asset_id in sorted(upload_candidate_ids):
+                    approval = asset_approvals.get(asset_id)
+                    frozen = frozen_records.get(asset_id)
+                    discovered = discovered_assets.get(asset_id)
+                    if frozen is None or discovered is None:
+                        builder.errors.append(
+                            f"approval_identity_mismatch: {asset_id} missing from frozen discovery")
+                        continue
+
+                    if approval is not None:
+                        mismatches = approval_mismatches(
+                            approval, frozen,
+                            approved_discovery["discovery_manifest_sha256"],
+                        )
+                        if mismatches:
+                            builder.errors.append(
+                                f"approval_identity_mismatch: {asset_id}: "
+                                + ", ".join(sorted(mismatches)))
+                            continue
+
+                    material = materials_by_id.get(frozen["material_id"])
+                    if (material is None
+                            or material.get("source_url") != frozen["source_page_url"]):
+                        builder.errors.append(
+                            f"approval_identity_mismatch: {asset_id} material/source changed")
+                        continue
+
+                    local_value = discovered.get("local_path")
+                    if not local_value:
+                        builder.errors.append(
+                            f"approval_identity_mismatch: {asset_id} missing discovery local_path")
+                        continue
+                    local_path = Path(local_value).resolve()
+                    if not local_path.is_relative_to(images_root) or not local_path.is_file():
+                        builder.errors.append(
+                            f"approval_identity_mismatch: {asset_id} local file outside discovery images")
+                        continue
+
+                    resolved_url = frozen["resolved_original_url"]
+                    sec_check = is_safe_url(
+                        resolved_url, require_dns=(network_mode == "live"))
+                    if not sec_check.safe:
+                        builder.errors.append(
+                            f"URL security: {asset_id}: {', '.join(sec_check.reasons)}")
+                        continue
+
+                    inspection = inspect_image(
+                        str(local_path), max_pixels=config.get("max_pixels", 40_000_000))
+                    if inspection.sha256 != frozen["asset_sha256"]:
+                        builder.errors.append(
+                            f"approval_identity_mismatch: {asset_id} frozen sha256 mismatch")
+                        continue
+                    identity_sha256 = stable_asset_identity(
+                        frozen["material_id"], frozen["source_page_url"],
+                        resolved_url, inspection.sha256,
+                    )
+                    if identity_sha256 != frozen["asset_identity_sha256"]:
+                        builder.errors.append(
+                            f"approval_identity_mismatch: {asset_id} stable identity mismatch")
+                        continue
+
+                    asset = discovered_asset_records[asset_id]
+                    asset.local_path = str(local_path)
+                    asset.sha256 = inspection.sha256
+                    asset.perceptual_hash = inspection.perceptual_hash
+                    asset.mime_type = inspection.mime_type
+                    asset.width = inspection.width
+                    asset.height = inspection.height
+                    asset.file_size = inspection.file_size
+                    asset.quality_status = "pass" if inspection.is_valid else "fail"
+                    asset.asset_identity_sha256 = identity_sha256
+                    if approval is None and asset.copyright_status != "restricted":
+                        asset.copyright_status = "known_allowed"
+                    pending_uploads.append((
+                        asset, str(local_path), inspection,
+                        discovered.get("extraction_method") or "img.src"))
+                    builder.downloads_succeeded += 1
+            except (OSError, ValueError, KeyError, TypeError) as exc:
+                builder.errors.append(
+                    f"approval_identity_mismatch: cannot load frozen discovery assets: {exc}")
+
     max_images_per_material = config.get("max_images_per_material", 3)
     max_total_images = config.get("max_total_images", 12)
     total_assets_added = 0
     asset_counter = 0
 
-    for mat in materials:
+    for mat in ([] if args.phase == "continue" else materials):
         material_id = mat["material_id"]
         permalink = mat.get("aihot_permalink", "")
         source_url = mat.get("source_url", "")
@@ -388,15 +529,46 @@ def main():
                     and asset.quality_status == "pass"
                     and asset.relevance_status == "relevant"
                     and asset.duplicate_of is None):
-                upload_result = timed_upload(
-                    uploader, upload_events, local_path, asset.asset_id,
-                    copyright_status=asset.copyright_status,
-                )
-                asset.upload = {
-                    "mode": upload_mode, "status": upload_result.status,
-                    "remote_url": upload_result.remote_url,
-                    "response_sha256": upload_result.response_sha256,
-                }
+                prior = existing_upload_events.get(asset.asset_id)
+                if prior is not None:
+                    asset.upload = {
+                        "mode": prior.get("mode", upload_mode),
+                        "status": "success",
+                        "remote_url": prior["url"],
+                        "response_sha256": prior.get("response_sha256"),
+                    }
+                    upload_events.append({
+                        "asset_id": asset.asset_id,
+                        "mode": prior.get("mode", upload_mode),
+                        "status": "skipped_already_uploaded",
+                        "started_at": prior.get("started_at"),
+                        "ended_at": prior.get("ended_at"),
+                        "start_monotonic": prior.get("start_monotonic"),
+                        "end_monotonic": prior.get("end_monotonic"),
+                        "http_status": prior.get("http_status"),
+                        "wechat_errcode": prior.get("wechat_errcode"),
+                        "wechat_errmsg": prior.get("wechat_errmsg"),
+                        "request_elapsed_seconds": 0.0,
+                        "endpoint_path": prior.get("endpoint_path"),
+                        "request_attempt_index": prior.get("request_attempt_index"),
+                        "media_id": prior.get("media_id"),
+                        "url": prior["url"],
+                        "source_event": "existing_success_event",
+                    })
+                else:
+                    upload_result = timed_upload(
+                        uploader, upload_events, local_path, asset.asset_id,
+                        copyright_status=asset.copyright_status,
+                    )
+                    asset.upload = {
+                        "mode": upload_mode, "status": upload_result.status,
+                        "remote_url": upload_result.remote_url,
+                        "response_sha256": upload_result.response_sha256,
+                    }
+                    if upload_result.status != "success":
+                        builder.errors.append(
+                            f"upload failed for {asset.asset_id}: "
+                            f"{upload_result.error or 'no success response'}")
 
     for aid in sorted(set(asset_approvals) - consumed_asset_approvals):
         builder.warnings.append(f"asset_approval for {aid} NOT consumed")
@@ -503,6 +675,12 @@ def main():
         json.dump({"schema_version": "1.0", "serial": True,
                    "events": upload_events}, f, ensure_ascii=False, indent=2)
 
+    # OBS-43: Pipeline's stage contract reads required outputs at the stage root,
+    # while two-phase execution keeps its canonical continue copies in continue/.
+    if args.phase == "continue" and output_dir.name == "continue":
+        for output_path in (manifest_path, bindings_path, events_path):
+            (output_dir.parent / output_path.name).write_bytes(output_path.read_bytes())
+
     print(f"\n[media-enrichment] Manifest: {manifest_path}")
     print(f"[media-enrichment] Bindings: {bindings_path}")
     print(f"  Assets: {len(builder.assets)}")
````

### 2.2 src/media_enrichment/uploader.py(runtime)

````diff
diff --git "a/repos\\media-enrichment\\src\\media_enrichment\\uploader.py" "b/.agents\\skills\\media-enrichment\\src\\media_enrichment\\uploader.py"
index 0efbf05..3589aff 100644
--- "a/repos\\media-enrichment\\src\\media_enrichment\\uploader.py"
+++ "b/.agents\\skills\\media-enrichment\\src\\media_enrichment\\uploader.py"
@@ -78,6 +78,14 @@ def timed_upload(uploader, events: list, local_path: str, asset_id: str,
         "started_at": started,
         "ended_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
         "start_monotonic": round(start_m, 6), "end_monotonic": round(end_m, 6),
+        "http_status": result.http_status,
+        "wechat_errcode": result.wechat_errcode,
+        "wechat_errmsg": result.wechat_errmsg,
+        "request_elapsed_seconds": result.request_elapsed_seconds,
+        "endpoint_path": result.endpoint_path,
+        "request_attempt_index": result.request_attempt_index,
+        "media_id": result.media_id,
+        "url": result.remote_url if result.status == "success" else None,
     })
     return result
 
@@ -92,6 +100,13 @@ class UploadResult:
     actual_mime: str = ""
     error: str = ""
     uploaded_at: str = ""
+    http_status: int | None = None
+    wechat_errcode: int | None = None
+    wechat_errmsg: str | None = None
+    request_elapsed_seconds: float = 0.0
+    endpoint_path: str | None = None
+    request_attempt_index: int = 1
+    media_id: str | None = None
 
 
 def sanitize_response(data: Any) -> Any:
@@ -176,18 +191,37 @@ class WechatImageHostUploader:
     def __init__(self):
         self.app_id = os.environ.get("WECHAT_APP_ID", "")
         self.app_secret = os.environ.get("WECHAT_APP_SECRET", "")
+        self._access_token: str | None = None
+        self._last_token_observation = {
+            "http_status": None, "wechat_errcode": None,
+            "wechat_errmsg": None, "request_elapsed_seconds": 0.0,
+            "endpoint_path": "/cgi-bin/token", "request_attempt_index": 1,
+        }
 
     def _get_access_token(self) -> tuple[str, str]:
+        if self._access_token:
+            return self._access_token, ""
         if not self.app_id or not self.app_secret:
             return "", "WECHAT_APP_ID or WECHAT_APP_SECRET not set"
         try:
             import requests
             url = "https://api.weixin.qq.com/cgi-bin/token"
             params = {"grant_type": "client_credential", "appid": self.app_id, "secret": self.app_secret}
+            started = time.monotonic()
             resp = requests.get(url, params=params, timeout=10)
+            elapsed = round(time.monotonic() - started, 6)
             data = resp.json()
+            self._last_token_observation = {
+                "http_status": resp.status_code,
+                "wechat_errcode": data.get("errcode"),
+                "wechat_errmsg": data.get("errmsg"),
+                "request_elapsed_seconds": elapsed,
+                "endpoint_path": "/cgi-bin/token",
+                "request_attempt_index": 1,
+            }
             if "access_token" in data:
-                return data["access_token"], ""
+                self._access_token = data["access_token"]
+                return self._access_token, ""
             return "", _scrub_token(f"WeChat token error: {data.get('errmsg', 'unknown')}")
         except Exception as exc:
             return "", _scrub_token(f"token request failed: {exc}")
@@ -207,7 +241,9 @@ class WechatImageHostUploader:
         mime = detect_mime(local_path) if Path(local_path).exists() else ""
         token, err = self._get_access_token()
         if err:
-            return UploadResult(mode="wechat_image_host", status="failed", error=err, actual_mime=mime)
+            return UploadResult(
+                mode="wechat_image_host", status="failed", error=err,
+                actual_mime=mime, **self._last_token_observation)
 
         try:
             import requests
@@ -223,10 +259,21 @@ class WechatImageHostUploader:
                     (mime or "").split(";")[0].strip().lower(), ".png")
             with open(path, "rb") as f:
                 files = {"media": (upload_name, f, mime or "image/png")}
+                started = time.monotonic()
                 resp = requests.post(url, files=files, timeout=30)
+                elapsed = round(time.monotonic() - started, 6)
 
             data = resp.json()
             sanitized = sanitize_response(data)
+            observation = {
+                "http_status": resp.status_code,
+                "wechat_errcode": data.get("errcode"),
+                "wechat_errmsg": data.get("errmsg"),
+                "request_elapsed_seconds": elapsed,
+                "endpoint_path": "/cgi-bin/media/uploadimg",
+                "request_attempt_index": 1,
+                "media_id": data.get("media_id"),
+            }
 
             if "url" in data:
                 # dev2-hotfix2: WeChat must return a genuine image-host URL;
@@ -236,7 +283,7 @@ class WechatImageHostUploader:
                     return UploadResult(
                         mode="wechat_image_host", status="failed",
                         error=_scrub_token(f"upload returned non-WeChat-host url: {sanitize_response(data)}"),
-                        actual_mime=mime,
+                        actual_mime=mime, **observation,
                     )
                 resp_hash = hashlib.sha256(normalized.encode()).hexdigest()
                 return UploadResult(
@@ -244,18 +291,21 @@ class WechatImageHostUploader:
                     remote_url=normalized, response_sha256=resp_hash,
                     actual_mime=mime,
                     uploaded_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
+                    **observation,
                 )
             else:
                 return UploadResult(
                     mode="wechat_image_host", status="failed",
                     error=_scrub_token(f"upload failed: {sanitized}"),
-                    actual_mime=mime,
+                    actual_mime=mime, **observation,
                 )
         except Exception as exc:
             return UploadResult(
                 mode="wechat_image_host", status="failed",
                 error=_scrub_token(f"upload error: {exc}"),
                 actual_mime=mime,
+                endpoint_path="/cgi-bin/media/uploadimg",
+                request_attempt_index=1,
             )
 
 
````

### 2.3 tests/test_single_asset_e2e.py(非 runtime)

````diff
diff --git "a/repos\\media-enrichment\\tests\\test_single_asset_e2e.py" "b/.agents\\skills\\media-enrichment\\tests\\test_single_asset_e2e.py"
index c0a7823..0b4d0ad 100644
--- "a/repos\\media-enrichment\\tests\\test_single_asset_e2e.py"
+++ "b/.agents\\skills\\media-enrichment\\tests\\test_single_asset_e2e.py"
@@ -138,7 +138,7 @@ class TestStableSingleAssetIdentityCli:
             "remote_url": None, "response_sha256": None,
         } for a in charts)
 
-    def test_inserted_image_before_a001_does_not_transfer_approval(self, tmp_path):
+    def test_inserted_source_image_after_discovery_does_not_change_frozen_upload(self, tmp_path):
         fixtures = _fixtures(tmp_path)
         _, out, _, frozen, _ = _cli(tmp_path, fixtures, "discover")
         approval = _approval(frozen)
@@ -150,13 +150,13 @@ class TestStableSingleAssetIdentityCli:
         result, _, manifest, _, events = _cli(
             tmp_path, fixtures, "continue", [approval],
             out / "asset_discovery_manifest.json")
-        assert result.returncode == 0
-        _assert_no_upload(manifest, events)
+        assert result.returncode == 0, result.stdout + result.stderr
+        assert [e["asset_id"] for e in events["events"]] == ["A-001"]
         a1 = next(a for a in manifest["assets"] if a["asset_id"] == "A-001")
-        assert "fresh_asset_sha256" in a1["approval_identity_mismatch"]
-        assert a1["copyright_status"] == "unknown"
+        assert a1["asset_approval_consumed"] is True
+        assert a1["sha256"] == approval["asset_sha256"]
 
-    def test_same_url_changed_content_does_not_upload(self, tmp_path):
+    def test_changed_source_bytes_after_discovery_do_not_replace_frozen_bytes(self, tmp_path):
         fixtures = _fixtures(tmp_path)
         _, out, _, frozen, _ = _cli(tmp_path, fixtures, "discover")
         approval = _approval(frozen)
@@ -165,10 +165,10 @@ class TestStableSingleAssetIdentityCli:
         result, _, manifest, _, events = _cli(
             tmp_path, fixtures, "continue", [approval],
             out / "asset_discovery_manifest.json")
-        assert result.returncode == 0
-        _assert_no_upload(manifest, events)
+        assert result.returncode == 0, result.stdout + result.stderr
+        assert [e["asset_id"] for e in events["events"]] == ["A-001"]
         a1 = next(a for a in manifest["assets"] if a["asset_id"] == "A-001")
-        assert "fresh_asset_sha256" in a1["approval_identity_mismatch"]
+        assert a1["sha256"] == approval["asset_sha256"]
 
     def test_same_content_different_material_does_not_inherit(self, tmp_path):
         fixtures = _fixtures(tmp_path)
@@ -177,10 +177,9 @@ class TestStableSingleAssetIdentityCli:
         result, _, manifest, _, events = _cli(
             tmp_path, fixtures, "continue", [approval],
             out / "asset_discovery_manifest.json", material_id="M-002")
-        assert result.returncode == 0
+        assert result.returncode != 0
         _assert_no_upload(manifest, events)
-        a1 = next(a for a in manifest["assets"] if a["asset_id"] == "A-001")
-        assert "fresh_material_id" in a1["approval_identity_mismatch"]
+        assert any("material/source changed" in e for e in manifest["errors"])
 
     def test_modified_discovery_manifest_does_not_upload(self, tmp_path):
         fixtures = _fixtures(tmp_path)
@@ -196,10 +195,8 @@ class TestStableSingleAssetIdentityCli:
         _assert_no_upload(manifest, events)
         assert any("discovery manifest sha256 invalid" in e for e in manifest["errors"])
 
-    def test_no_repost_overrides_stable_single_asset_approval(self, tmp_path):
+    def test_no_repost_detected_at_discovery_overrides_stable_approval(self, tmp_path):
         fixtures = _fixtures(tmp_path)
-        _, out, _, frozen, _ = _cli(tmp_path, fixtures, "discover")
-        approval = _approval(frozen, "A-001")
         html_path = fixtures / "html" / "single-asset-e2e.html"
         html_path.write_text(
             html_path.read_text(encoding="utf-8").replace(
@@ -207,6 +204,8 @@ class TestStableSingleAssetIdentityCli:
             ),
             encoding="utf-8",
         )
+        _, out, _, frozen, _ = _cli(tmp_path, fixtures, "discover")
+        approval = _approval(frozen, "A-001")
         result, _, manifest, _, events = _cli(
             tmp_path, fixtures, "continue", [approval],
             out / "asset_discovery_manifest.json")
@@ -233,6 +232,98 @@ class TestStableSingleAssetIdentityCli:
         assert assets["A-002"]["copyright_status"] == "unknown"
         assert assets["A-002"]["upload"]["status"] != "success"
 
+    def test_tampered_persisted_discovery_file_fails_closed(self, tmp_path):
+        fixtures = _fixtures(tmp_path)
+        _, out, manifest, frozen, _ = _cli(tmp_path, fixtures, "discover")
+        approval = _approval(frozen, "A-001")
+        target = next(a for a in manifest["assets"] if a["asset_id"] == "A-001")
+        Path(target["local_path"]).write_bytes(b"tampered-discovery-bytes")
+        result, _, continued, _, events = _cli(
+            tmp_path, fixtures, "continue", [approval],
+            out / "asset_discovery_manifest.json")
+        assert result.returncode != 0
+        _assert_no_upload(continued, events)
+        assert any("frozen sha256 mismatch" in e for e in continued["errors"])
+
+    def test_existing_success_event_skips_reupload_and_reuses_url(self, tmp_path):
+        fixtures = _fixtures(tmp_path)
+        _, out, _, frozen, _ = _cli(tmp_path, fixtures, "discover")
+        approval = _approval(frozen, "A-001")
+        request = _write_request(tmp_path, [approval])
+        phase_out = tmp_path / "idempotent" / "continue"
+        cmd = [
+            sys.executable, "-X", "utf8",
+            str(SKILL_ROOT / "scripts" / "run_media_enrichment.py"),
+            "--request", str(request), "--output-dir", str(phase_out),
+            "--fixture-dir", str(fixtures / "html"), "--phase", "continue",
+            "--discovery-manifest", str(out / "asset_discovery_manifest.json"),
+        ]
+        first = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", timeout=180)
+        assert first.returncode == 0, first.stdout + first.stderr
+        first_events = json.loads((phase_out / "upload_events.json").read_text(encoding="utf-8"))["events"]
+        first_url = next(e["url"] for e in first_events if e["status"] == "success")
+        second = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", timeout=180)
+        assert second.returncode == 0, second.stdout + second.stderr
+        events = json.loads((phase_out / "upload_events.json").read_text(encoding="utf-8"))["events"]
+        assert sum(e["status"] == "success" for e in events) == 1
+        skipped = [e for e in events if e["status"] == "skipped_already_uploaded"]
+        assert len(skipped) == 1 and skipped[0]["url"] == first_url
+
+    def test_existing_success_does_not_bypass_frozen_file_sha(self, tmp_path):
+        fixtures = _fixtures(tmp_path)
+        _, out, manifest, frozen, _ = _cli(tmp_path, fixtures, "discover")
+        approval = _approval(frozen, "A-001")
+        request = _write_request(tmp_path, [approval])
+        phase_out = tmp_path / "tamper-after-success" / "continue"
+        cmd = [sys.executable, "-X", "utf8", str(SKILL_ROOT / "scripts" / "run_media_enrichment.py"),
+               "--request", str(request), "--output-dir", str(phase_out),
+               "--fixture-dir", str(fixtures / "html"), "--phase", "continue",
+               "--discovery-manifest", str(out / "asset_discovery_manifest.json")]
+        assert subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", timeout=180).returncode == 0
+        target = next(a for a in manifest["assets"] if a["asset_id"] == "A-001")
+        Path(target["local_path"]).write_bytes(b"tampered-after-success")
+        second = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", timeout=180)
+        assert second.returncode != 0
+        continued = json.loads((phase_out / "media_manifest.json").read_text(encoding="utf-8"))
+        assert any("frozen sha256 mismatch" in e for e in continued["errors"])
+
+    def test_failed_event_is_not_reused(self, tmp_path):
+        fixtures = _fixtures(tmp_path)
+        _, out, _, frozen, _ = _cli(tmp_path, fixtures, "discover")
+        approval = _approval(frozen, "A-001")
+        request = _write_request(tmp_path, [approval])
+        phase_out = tmp_path / "failed-event" / "continue"
+        phase_out.mkdir(parents=True)
+        (phase_out / "upload_events.json").write_text(
+            json.dumps({"schema_version":"1.0","serial":True,"events":[
+                {"asset_id":"A-001","status":"failed","url":None}]}), encoding="utf-8")
+        cmd = [sys.executable, "-X", "utf8", str(SKILL_ROOT / "scripts" / "run_media_enrichment.py"),
+               "--request", str(request), "--output-dir", str(phase_out),
+               "--fixture-dir", str(fixtures / "html"), "--phase", "continue",
+               "--discovery-manifest", str(out / "asset_discovery_manifest.json")]
+        result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", timeout=180)
+        assert result.returncode == 0, result.stdout + result.stderr
+        events = json.loads((phase_out / "upload_events.json").read_text(encoding="utf-8"))["events"]
+        assert any(e.get("status") == "success" for e in events)
+        assert not any(e.get("status") == "skipped_already_uploaded" for e in events)
+
+    def test_continue_mirrors_required_outputs_to_stage_root(self, tmp_path):
+        fixtures = _fixtures(tmp_path)
+        _, out, _, frozen, _ = _cli(tmp_path, fixtures, "discover")
+        approval = _approval(frozen, "A-001")
+        request = _write_request(tmp_path, [approval])
+        phase_out = tmp_path / "stage" / "continue"
+        result = subprocess.run([
+            sys.executable, "-X", "utf8",
+            str(SKILL_ROOT / "scripts" / "run_media_enrichment.py"),
+            "--request", str(request), "--output-dir", str(phase_out),
+            "--fixture-dir", str(fixtures / "html"), "--phase", "continue",
+            "--discovery-manifest", str(out / "asset_discovery_manifest.json"),
+        ], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180)
+        assert result.returncode == 0, result.stdout + result.stderr
+        for name in ("media_manifest.json", "article_image_bindings.json", "upload_events.json"):
+            assert (phase_out / name).read_bytes() == (phase_out.parent / name).read_bytes()
+
 
 class TestStableApprovalContract:
     def test_valid_stable_approval_passes(self, tmp_path):
````

### 2.4 tests/test_approval_scopes_cli_e2e.py(非 runtime)

````diff
diff --git "a/repos\\media-enrichment\\tests\\test_approval_scopes_cli_e2e.py" "b/.agents\\skills\\media-enrichment\\tests\\test_approval_scopes_cli_e2e.py"
index b64fa1d..7e64bfb 100644
--- "a/repos\\media-enrichment\\tests\\test_approval_scopes_cli_e2e.py"
+++ "b/.agents\\skills\\media-enrichment\\tests\\test_approval_scopes_cli_e2e.py"
@@ -131,7 +131,7 @@ def _discover_continue(tmp_path: Path, fixture: Path, request: Path):
     return continued, continue_out, continue_manifest, continue_events
 
 
-def test_material_approval_uploads_only_approved_material(tmp_path):
+def test_material_approval_without_explicit_asset_approval_fails_closed(tmp_path):
     fixture = tmp_path / "fixture"
     _make_fixture(fixture, "url-a", "material-a.png", (210, 40, 40))
     _make_fixture(fixture, "url-b", "material-b.png", (40, 40, 210))
@@ -140,15 +140,12 @@ def test_material_approval_uploads_only_approved_material(tmp_path):
         _material("M-002", "url-b"),
     ])
     result, _, manifest, events = _discover_continue(tmp_path, fixture, request)
-    assert result.returncode == 0, result.stdout + result.stderr
-    assert [e["asset_id"] for e in events["events"]] == ["A-001"]
-    assets = {a["material_ids"][0]: a for a in manifest["assets"] if a["asset_origin"] == "source"}
-    assert assets["M-001"]["upload"]["status"] == "success"
-    assert assets["M-002"]["upload"]["status"] != "success"
-    assert assets["M-002"]["copyright_status"] == "unknown"
+    assert result.returncode != 0
+    assert events["events"] == []
+    assert any("approved upload candidate count exceeds" in e for e in manifest["errors"])
 
 
-def test_source_url_approval_does_not_inherit_to_other_url(tmp_path):
+def test_source_url_approval_without_explicit_asset_approval_fails_closed(tmp_path):
     fixture = tmp_path / "fixture"
     _make_fixture(fixture, "url-a", "url-a.png", (180, 80, 20))
     _make_fixture(fixture, "url-b", "url-b.png", (20, 160, 80))
@@ -157,14 +154,9 @@ def test_source_url_approval_does_not_inherit_to_other_url(tmp_path):
         _material("M-002", "url-b"),
     ])
     result, _, manifest, events = _discover_continue(tmp_path, fixture, request)
-    assert result.returncode == 0, result.stdout + result.stderr
-    uploaded = [e["asset_id"] for e in events["events"]]
-    assert uploaded == ["A-001"]
-    source_assets = [a for a in manifest["assets"] if a["asset_origin"] == "source"]
-    assert next(a for a in source_assets if a["material_ids"] == ["M-001"])["upload"]["status"] == "success"
-    url_b = next(a for a in source_assets if a["material_ids"] == ["M-002"])
-    assert url_b["upload"]["status"] != "success"
-    assert url_b["copyright_status"] == "unknown"
+    assert result.returncode != 0
+    assert events["events"] == []
+    assert any("approved upload candidate count exceeds" in e for e in manifest["errors"])
 
 
 def test_no_repost_overrides_material_approval(tmp_path):
@@ -174,8 +166,9 @@ def test_no_repost_overrides_material_approval(tmp_path):
         _material("M-001", "blocked", "known_allowed", "material"),
     ])
     result, _, manifest, events = _discover_continue(tmp_path, fixture, request)
-    assert result.returncode == 0, result.stdout + result.stderr
+    assert result.returncode != 0
     assert events["events"] == []
+    assert any("approved upload candidate count exceeds" in e for e in manifest["errors"])
     asset = next(a for a in manifest["assets"] if a["asset_origin"] == "source")
     assert asset["copyright_status"] == "restricted"
     assert asset["upload"]["status"] != "success"
````

### 2.5 tests/test_uploader_manifest.py(非 runtime)

````diff
diff --git "a/repos\\media-enrichment\\tests\\test_uploader_manifest.py" "b/.agents\\skills\\media-enrichment\\tests\\test_uploader_manifest.py"
index d3ab605..78088e1 100644
--- "a/repos\\media-enrichment\\tests\\test_uploader_manifest.py"
+++ "b/.agents\\skills\\media-enrichment\\tests\\test_uploader_manifest.py"
@@ -5,7 +5,8 @@ import pytest
 from pathlib import Path
 from media_enrichment.uploader import (
     DryRunUploader, MockUploader, sanitize_response, scan_for_secrets,
-    create_uploader, _scrub_token,
+    create_uploader, _scrub_token, timed_upload, UploadResult,
+    WechatImageHostUploader,
 )
 from media_enrichment.manifest_builder import ManifestBuilder, AssetRecord
 
@@ -64,6 +65,56 @@ class TestTokenScrubbing:
         assert "access_token=[REDACTED]" in scrubbed
 
 
+class TestUploadObservability:
+    def test_timed_upload_records_observation_fields_without_token(self):
+        class FakeUploader:
+            def upload(self, local_path, asset_id, copyright_status):
+                return UploadResult(
+                    mode="wechat_image_host", status="failed",
+                    http_status=401, wechat_errcode=40164,
+                    wechat_errmsg="invalid ip", request_elapsed_seconds=0.25,
+                    endpoint_path="/cgi-bin/media/uploadimg",
+                    request_attempt_index=1,
+                )
+        events = []
+        timed_upload(FakeUploader(), events, "unused.png", "A-003", "known_allowed")
+        event = events[0]
+        assert event["http_status"] == 401
+        assert event["wechat_errcode"] == 40164
+        assert event["wechat_errmsg"] == "invalid ip"
+        assert event["endpoint_path"] == "/cgi-bin/media/uploadimg"
+        assert event["media_id"] is None
+        assert "access_token" not in json.dumps(event)
+
+
+class TestCredentialSourceAndTokenCache:
+    def test_missing_credentials_fail_closed(self, monkeypatch):
+        monkeypatch.delenv("WECHAT_APP_ID", raising=False)
+        monkeypatch.delenv("WECHAT_APP_SECRET", raising=False)
+        result = WechatImageHostUploader().upload("missing.png", "A-003", "known_allowed")
+        assert result.status == "failed"
+        assert result.media_id is None
+
+    def test_token_cached_within_uploader_instance(self, monkeypatch):
+        import sys
+        from types import SimpleNamespace
+        monkeypatch.setenv("WECHAT_APP_ID", "wx-test-id")
+        monkeypatch.setenv("WECHAT_APP_SECRET", "test-secret")
+        calls = []
+        response = SimpleNamespace(
+            status_code=200,
+            json=lambda: {"access_token": "test-token-value"},
+        )
+        fake_requests = SimpleNamespace(
+            get=lambda *args, **kwargs: (calls.append(1) or response),
+        )
+        monkeypatch.setitem(sys.modules, "requests", fake_requests)
+        uploader = WechatImageHostUploader()
+        assert uploader._get_access_token() == ("test-token-value", "")
+        assert uploader._get_access_token() == ("test-token-value", "")
+        assert len(calls) == 1
+
+
 class TestSecretsSanitization:
     def test_sanitize_response_removes_token(self):
         data = {"url": "https://cdn.example.com/img.jpg", "token": "secret123"}
````

---

## 三、第一步第 2 项:逐文件改动说明与 OBS-53 范畴判定(**判定:不通过,存在与 OBS-53 无关的改动**)

### 3.1 逐文件说明

| 文件 | 改动内容 | 用途 | OBS 归属 |
|---|---|---|---|
| `scripts/run_media_enrichment.py` | ① 导入 `normalize_wechat_url`;② continue 阶段读入既有 `upload_events.json`,仅 success+合法 URL 的事件进入 `existing_upload_events`;③ 上传前命中既有 success 事件则复用 URL、追加 `skipped_already_uploaded` 事件,否则走 `timed_upload` | 上传幂等:已有 success 上传不再调用 uploadimg | **OBS-53** |
| `scripts/run_media_enrichment.py` | ④ continue 阶段消费冻结 discovery manifest:校验 `discovery_manifest_sha256`、frozen 记录与 material/source 一致、本地文件位于 discovery images 内、URL 安全检查、`inspect_image` sha256 与 frozen `asset_sha256` 比对、stable identity 比对;失败即 `approval_identity_mismatch` 拒绝;材料 copyright_review=known_allowed 的资产并入候选集;⑤ continue 跳过 `for mat in materials` 发现循环 | continue 阶段冻结消费、不重新抓取/下载 | **OBS-42**(另有 OBS-43 镜像输出,见下) |
| `scripts/run_media_enrichment.py` | ⑥ continue 且输出目录名为 `continue` 时,把 `media_manifest.json` / `article_image_bindings.json` / `upload_events.json` 镜像到 stage root | 满足 Pipeline stage 合同在 stage root 读必需产物 | **OBS-43**(记录在 obs42 补丁包内) |
| `scripts/run_media_enrichment.py` | ⑦ `upload_candidate_ids` 若大于显式 `asset_approvals` 数量,报「approved upload candidate count exceeds explicit copyright approval asset count」并清空候选集 | 数量上限 fail-closed:known_allowed 材料不得超出显式批准数 | **obs44-46** |
| `src/media_enrichment/uploader.py` | ⑧ `UploadResult`/事件增加 `http_status`/`wechat_errcode`/`wechat_errmsg`/`request_elapsed_seconds`/`endpoint_path`/`request_attempt_index`/`media_id`/`url` 观测字段;`_last_token_observation` 记录 token 请求观测;失败路径携带观测 | 微信上传可观测性(stage_failure/stdout 证据) | **obs44-46** |
| `src/media_enrichment/uploader.py` | ⑨ `_access_token` 缓存:实例内 token 复用,避免每次上传重复取 token | 统一凭据来源(观察 + 缓存) | **obs47** |
| `tests/test_single_asset_e2e.py` | continue 冻结消费相关测试(冻结字节篡改 fail-closed、镜像输出等)+ 幂等 3 测试(既有 success 跳过、篡改不复用、failed 不复用) | 测试 | OBS-42 + **OBS-53** |
| `tests/test_approval_scopes_cli_e2e.py` | 批准候选数封顶 fail-closed 语义(无显式 asset approval 时材料级/URL 级批准不再放行) | 测试 | **obs44-46** |
| `tests/test_uploader_manifest.py` | 观测字段测试 + 凭据缺失 fail-closed + token 缓存测试 | 测试 | obs44-46 + **obs47** |

### 3.2 非 OBS-53 改动清单(按指令单独列出,停机依据)

1. **OBS-42(含 OBS-43)**:`run_media_enrichment.py` 的 continue 冻结 discovery 消费块、continue 跳过发现循环、OBS-43 镜像输出;对应 `audit/skill-patches/obs42-media-enrichment/changes.diff`(266 行,`OBS-42`/`OBS-43` 注释在档内),relock commit `4c6416d`「audit: relock patched media runtime」。
2. **obs44-46(微信上传可观测性 + 批准候选数封顶)**:`uploader.py` 观测字段、`run_media_enrichment.py` 候选数封顶、两个测试文件;对应 `audit/skill-patches/obs44-obs46/changes.diff`(241 行),relock commit `dd880c0`「audit: add WeChat upload observability patch」。
3. **obs47(统一凭据来源)**:`uploader.py` 的 `_access_token` 缓存;对应 `audit/skill-patches/obs47-credential-source/changes.diff`(165 行),relock commit `f5eb6b3`「fix: unify WeChat credential source」。

以上三项均不在「OBS-53(idempotency / min-images)」范畴内。lock 补丁态树是四个本地补丁包(obs42/43、obs44-46、obs47、obs53)累积结果,并非纯 OBS-53 补丁态。

### 3.3 依据(锁定数值溯源)

`git log --follow skills.lock.json`(新→旧):`7c91489`(OBS-53,root→`0d8aea21`)→ `f5eb6b3`(obs47)→ `dd880c0`(obs44-46)→ `4c6416d`(obs42/43)→ `7264c30`(dev2-hotfix6)。四个补丁各自带 changes.diff 与 relock,当前 lock 值(0d8aea21/172aa1b8/57/2d877a93)由 `7c91489` 最后写入。

## 四、第一步第 3 项:补丁态与 pipeline commit 7c91489 的对应关系(证据)

- commit:`7c914899772216261d4f895f4a3c2c86c3416ade`
- message:`fix: add media idempotency and configurable minimum`
- 时间/作者:Sat Aug 1 03:20:33 2026 +0800(Amer)
- 涉及文件(9):`audit/skill-patches/obs53-idempotency-and-min-images/{changes.diff, diagnosis.md, files-changed.md, safety-checklist.md}`、`skills.lock.json`、`tests/test_obs53_min_images.py`、`validators/validate_media_bindings.py`、`wxgzh_pipeline/contracts.py`、`wxgzh_pipeline/stages/media_enrichment.py`
- `skills.lock.json` 在该 commit 的 delta:media `skill_root_sha256` `1dab6184…`→`0d8aea21…`,`entrypoint_sha256` `a54deef3…`→`2d877a93…`(`full_commit_sha`/`source_tree_sha`/manifest/count 未动)
- 对应关系结论:**lock 的 media 数值(0d8aea21/172aa1b8/57/2d877a93)正是由 7c91489 写入**——「补丁态 ↔ 7c91489」在 lock 数值层面成立;但该补丁态树相对 cedf92ca 的全部内容差异 ≠ 7c91489 携带的 obs53 changes.diff(后者仅为 OBS-53 增量,不含 OBS-42/43、obs44-46、obs47 改动)。

## 五、停机决定与未执行步骤

按指令「若存在与 OBS-53 无关的改动,单独列出并停机上报」,本档在第一步第 2 项停机。**以下步骤均未执行**:第二步(建分支 `fix/obs53-idempotency-min-images`、提交、push)、第三步(clone 验证 root/manifest)、第四步(relock dry-run/--apply)、第五步(doctor/回归/四锁 dry-run/receipt 核查/档 31 sibling 更新与 26 项测试)。

未触碰:`.agents\skills` 任何文件、两侧 `skills.lock.json`、`skills.lock.history.json`(不存在)、真实台账/备份、`bundle-staging-37`、24S 暂存、任何 git 远端。未调用微信接口,未跑 Pipeline,未删除任何文件。

## 六、供审核者裁决的事实与选项(不替审核者决定)

1. **事实**:锁定树 = cedf92ca + OBS-42/43 + obs44-46 + obs47 + obs53 的累积态;root `0d8aea21` 唯一权威副本在 `.temp\obs62s-build-staging\portable-bundle`(24S)与 `F:\AIXM\wxgzh\bundle-staging-37\portable-bundle`(档 37),远端无同树副本。
2. 若仅回流 OBS-53 增量(obs53 changes.diff 的 media 部分),新 commit 树 ≠ lock root `0d8aea21`,无法满足第八步「root 逐字一致」。
3. 若整树回流为单个 commit,内容包含 OBS-42/43、obs44-46、obs47,与指令要求的「OBS-53 内容」commit message 及「全部属于 OBS-53 范畴」前提不符。
4. 可行方向(均需审核者授权/改口径):(a) 整树回流为一个 commit,message 如实列出四个补丁包;(b) 按补丁包拆分 4 个 commit 后指向末位 commit;(c) 审核者重新定义本档范围为「锁定补丁态整树回流」并同步修改第 5 步 message 规格。relock 能力本身(第 11 步提到的「仅更新 full_commit_sha」)未在本档验证,因停机发生在更早步骤。

## 七、风险提示(维持既有记录)

档 37 已记录:OBS-53 未推送态是 lock 与远端树长期不一致的根源,`.temp` 会被清理,24S 暂存树为唯一可再生的锁定树副本。本档停机不改变该风险状态;建议审核者尽快裁决上述方向,或明确指示跳过第 2 项门槛(需书面放宽)。
