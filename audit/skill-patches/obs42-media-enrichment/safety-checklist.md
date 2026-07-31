# Safety Checklist

- [x] **本地SHA强校验**：continue重新读取本地文件并计算SHA-256；与冻结`asset_sha256`不一致写入builder.errors、零上传、非零退出，不降级为警告。
- [x] **仅批准资产**：single_asset目标集合来自`request.asset_approvals`；既有material/source_url批准路径保留但不扩大。当前RUN请求仅A-003/A-004。
- [x] **数量不超过批准数**：single_asset只遍历批准asset_id集合；未批准资产仅保留审计记录，不进入pending_uploads。
- [x] **URL安全不放宽**：冻结`resolved_original_url`仍调用`is_safe_url(..., require_dns=live)`，失败即拒绝。
- [x] **批准合同不放宽**：仍调用现有input contract、`approval_mismatches`、冻结manifest SHA与稳定身份校验；无自动降级。
- [x] **无自动批准新路径**：没有新增unknown→eligible路径；restricted/no-repost仍高于material和single_asset批准。

## 回归验证

- `test_tampered_persisted_discovery_file_fails_closed`：篡改持久化文件后零上传。
- `test_continue_mirrors_required_outputs_to_stage_root`：continue/与阶段根三个required outputs字节一致。
- 完整测试：`283 passed, 6 skipped`。
