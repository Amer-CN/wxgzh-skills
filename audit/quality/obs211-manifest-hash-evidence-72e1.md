# OBS-211 书面证据补录（档72E-1）

## 结论

`runtime_manifest_sha256` 只哈希「运行时文件路径清单」，不哈希文件内容；内容由 `skill_root_sha256` 覆盖。72A/72A-F 两次内容变更未触发 manifest 变化由此解释。

## 代码行证据（grep 原文）

`wxgzh_pipeline/skill_discovery.py`:

```python
67:def compute_runtime_manifest_sha(root: Path) -> tuple[str | None, list[str]]:
68:    """Hash of the runtime FILE LIST itself (which files count as runtime)."""
69:    if not Path(root).is_dir():
70:        return None, []
71:    rels = [p.relative_to(root).as_posix() for p in _runtime_files(root)]
72:    return hashlib.sha256("\n".join(rels).encode("utf-8")).hexdigest(), rels
```

- L68 docstring 自述：哈希的是「runtime FILE LIST 本身」。
- L71–72：输入仅为相对路径字符串列表（`_runtime_files` 产出），内容字节不参与。

## 排除的假说（72C-6F 已记）

- size/mtime 假说：pattern_audit.py 改 154/6 行、大小与 mtime 必变而 manifest sha 不动——与 L71-72 只哈希路径一致。
- 内容哈希假说：被 L72 直接排除（`"\n".join(rels)` 无内容字节）。

## 状态

OBS-211 已坐实（只哈希路径清单），状态不变（未修，行为本身是设计语义）；本档补书面 grep 证据。
