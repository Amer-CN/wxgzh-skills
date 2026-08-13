# OBS-42 / OBS-43 Diagnosis

## 1. Continue入口

`media-enrichment/scripts/run_media_enrichment.py::main()`；`--phase continue`由同一CLI入口处理。

## 2. 原重新抓取路径

原实现无continue专用读取分支。`run_media_enrichment.py`约123-291行始终遍历materials，调用`fetch_page`、`extract_images`、`decode_proxy_url`和`download_image`，再将新鲜结果放入`pending_uploads`；305行后才与批准的冻结manifest对比。因此源站变化或回退到AI HOT会让asset_id对应的新鲜资产漂移。

## 3. Discover持久化位置与命名

Discover下载到`<stage>/media_enrichment/discover/images/`。`downloader.download_image`按内容SHA-256命名，识别到常规格式时保留扩展名；完整映射保存在`discover/media_manifest.json`的`local_path`、`sha256`、`mime_type`、尺寸等字段。已确认当前RUN discover目录存在持久化图片。

## 4. 冻结资产与本地文件映射

`asset_discovery_manifest.json`保存`asset_id`、`material_id`、`source_page_url`、`resolved_original_url`、`asset_sha256`、`asset_identity_sha256`；同目录`media_manifest.json`以相同asset_id补充`local_path`。两者联合得到冻结身份和本地字节映射。

## 5. 稳定身份算法

`stable_asset_identity = sha256(material_id + "
" + source_page_url + "
" + resolved_original_url + "
" + asset_sha256)`。冻结manifest自身SHA按删除`discovery_manifest_sha256`后的规范JSON计算。

## 6. 产物落盘与合同读取

Skill在`output_dir`写`media_manifest.json`、`article_image_bindings.json`、`upload_events.json`。Pipeline两阶段执行把continue的`output_dir`设为`media_enrichment/continue/`，但阶段内容合同从`media_enrichment/`根目录读取required outputs，造成OBS-43误报。补丁保留continue/规范副本，并在成功写出时字节镜像到阶段根。

## 最小修复

- Continue不再抓源站；只读取冻结manifest同目录的discover media manifest与images文件。
- 只准备批准范围内的冻结资产；当前request材料/来源必须仍匹配。
- 上传前重新执行URL安全、目录边界、实际SHA、稳定身份和图片检查。
- 保留原批准消费、restricted优先级、分类门禁、串行上传与validator。
- Discover分支不改。
