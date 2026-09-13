# OBS-384 —— 77AG 自测工具参数护栏验收报告（字节级落盘）

- 档号：77AG（自测工具参数护栏 + 未知参数零副作用）。
- 授权：RELOCK_ALLOWED 临时 0→1（批准人=用户，范围=media-enrichment scripts/generate_evidence.py+tests（+同病 build_zip.py）；GZH 维持 0）。授权登记行随 feat 落账（序数按台账实况=五十四次，77AF 已占五十三）。
- 背景证据：jla535（--help 误触全量跑，evidence/ 20 文件，doctor FAIL_CLOSED）→ xby7hf（同工具同形状，evidence/+.pytest_cache，删构建产物恢复）。
- feat 提交：f1adbb9（16 文件）。

## 1. 任务 0 证据（只读贴回存档）

- 主犯路径：`scripts/generate_evidence.py:557-558`（`__main__` 直调）→ `main()` 539（零 argparse，add_argument/parse_args 零命中）→ 六个 generate_* 直写 `EVIDENCE_DIR`；`EVIDENCE_DIR.mkdir` 在 import 时（:23）即执行。
- 同病并入：`scripts/build_zip.py`（noarg+main+ZipFile/write_text/mkdir 写 API；`EVIDENCE_DIR.mkdir` 在 :35；`OUTPUT_ZIP` 落仓根；bare run 即全量构建）。
- 排除：`_verify_dev7.py`（noarg+main 但零写 API，只读校验）；`generate_test_fixtures.py`/`run_live_tests.py`（无 `main`，不裸跑）。
- 双侧残留：仓侧/装机侧 `media-enrichment/evidence/` 均缺席（False×2；装机侧 `.pytest_cache` 系 pytest 自身产物，gitignored，非构建残留）。

## 2. 实现（任务 1）

- 两文件 `main(argv=None)` 入口先过 argparse（零业务参数）：未知参数 exit 2 + usage 零文件落盘；`--help` 正常打印 exit 0 零副作用；裸调语义零变化。
- `EVIDENCE_DIR.mkdir` 由 import 时移入真跑路径（`_ensure_evidence_dir()`，main() 内 parse 后调用）。
- 测试：新增 `tests/test_hf77ag_cli_guard.py` 4 绿（bogus 双文件 exit 2 零新增/`--help` 双文件 exit 0 零副作用；子进程 stdout/stderr 甩 DEVNULL 不用管道——沙箱曾报 WinError 5；快照排除 `__pycache__/.pytest_cache`）。

## 3. 升版/锁链/回归

- 升版：media dev35→**dev36**（77J 全站同步 11 文件集+CHANGELOG；VERSION previous dev35/release 2026-09-14）。
- relock **#114**（media dev36：`relock-media-enrichment-20260913T194621Z-d601d9e2`，远端见证→apply 全链 PASS，备份在册）；锁 sha `5256ec28…→83d9f5ce…`，R93 双侧一致。
- doctor：双侧 PASS、OBS_69/OBS_68 双侧 MATCH（装机同步：media 16 文件+pipeline obs76r/ledger/observability/根 README）。
- 最终回归（relock 后）：见 §6（`.temp/upgrade_regression_77ag.log`）。
- 台账：OBS-384 + 口径 99 + 授权登记行（五十三→五十四）；唯一编号 `266 119 384 True`；R59 21=21 双差集空。

## 4. 基线链

`61d92a4（gzh toc-scroll 修）→ f1adbb9（feat 77AG，含授权登记行+obs304/obs288/README 随档）→ <docs 本报告+锁链>`

## 5. 执行过程如实记

- executor 通道不可用，主智能体降级直接执行（77AD/77AF 先例）。
- flow-gate 两次拦截过渡文件写入（probe/row/cal .txt），均按要求补简报登记后继续；过渡文件用后删。
