# Examples

三个示例展示 zh-human-writing Skill 的典型用法。

| # | 场景 | source | profile | 预期 |
|---|------|--------|---------|------|
| 01 | 作者原创 | author_written | essay | pass（不误杀） |
| 02 | AI 草稿 | ai_draft | essay | fail（检出 hard-residue） |
| 03 | 技术文档 | unknown | technical | pass（保护参数） |

每个示例包含：
- `input.txt` — 输入文本
- `audit-output.json` — `pattern_audit.py` 的实际输出
- `README.md` — 场景说明和预期结果

## 复现

```bash
cd examples/01-author-preserve
python ../../scripts/pattern_audit.py --text input.txt --profile essay --check-level full --output json
```
