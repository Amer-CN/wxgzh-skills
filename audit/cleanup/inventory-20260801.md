# 清理候选清单(只读盘点)— 2026-08-01

## 范围与方法
- 盘点范围:`F:\AIXM\wxgzh` 全部内容 + `C:\Users\Admin\.agents\skills`
- 归类:A=开发过程产物(建议删);B=历史物证备份(需审核者裁决);C=必须保留(理由)
- 强制 C 四项(不得出现在删除候选):`F:\AIXM\wxgzh\.env`、`C:\Users\Admin\.agents\skills\aihot`、`F:\AIXM\wxgzh\.agents\skills`、`F:\AIXM\wxgzh\repos\wxgzh-pipeline`
- 大小=递归字节合计;文件数=递归文件合计(含隐藏文件)
- 本清单只读生成;未删除任何文件。`F:\AIXM\wxgzh-env-backup\.env` 位于盘点范围之外,未列入

## 清单

| 完整路径 | 类型 | 大小(字节) | 文件数 | 归类 | 备注 |
|---|---|---:|---:|---|---|
| `F:\AIXM\wxgzh\.agents` | 目录 | 55874155 | 6226 | **C** | 强制保留:含 .agents\skills 运行环境 |
| `F:\AIXM\wxgzh\.codely` | 目录 | 3219581 | 3 | **B** | 工具状态目录,需裁决 |
| `F:\AIXM\wxgzh\.codely-cli` | 目录 | 56836758 | 22 | **B** | 工具状态目录,需裁决 |
| `F:\AIXM\wxgzh\.env` | 文件 | 84 | 1 | **C** | 强制保留:凭据(已备份至 F:\AIXM\wxgzh-env-backup\.env) |
| `F:\AIXM\wxgzh\.pytest_cache` | 目录 | 175132 | 5 | **A** | 可再生缓存 |
| `F:\AIXM\wxgzh\.reasonix` | 目录 | 317810 | 83 | **B** | 工具状态目录,需裁决 |
| `F:\AIXM\wxgzh\.temp` | 目录 | 420023517 | 51930 | **B** | 临时区整体;子项逐条见下 |
| `F:\AIXM\wxgzh\.workbuddy` | 目录 | 33495 | 6 | **B** | 工具状态目录,需裁决 |
| `F:\AIXM\wxgzh\articles` | 目录 | 14420721 | 251 | **B** | 历史写作产物,需裁决 |
| `F:\AIXM\wxgzh\candidate-manifest-hotfix2.sha256` | 文件 | 6834 | 1 | **B** | 历史物证包/校验文件,需裁决 |
| `F:\AIXM\wxgzh\candidate-manifest-hotfix3.sha256` | 文件 | 7014 | 1 | **B** | 历史物证包/校验文件,需裁决 |
| `F:\AIXM\wxgzh\candidate-manifest-hotfix4.sha256` | 文件 | 9747 | 1 | **B** | 历史物证包/校验文件,需裁决 |
| `F:\AIXM\wxgzh\candidate-manifest-hotfix5.sha256` | 文件 | 9838 | 1 | **B** | 历史物证包/校验文件,需裁决 |
| `F:\AIXM\wxgzh\candidate-manifest-hotfix6.sha256` | 文件 | 9838 | 1 | **B** | 历史物证包/校验文件,需裁决 |
| `F:\AIXM\wxgzh\candidate-manifest-hotfix7.sha256` | 文件 | 9838 | 1 | **B** | 历史物证包/校验文件,需裁决 |
| `F:\AIXM\wxgzh\candidate-manifest.sha256` | 文件 | 6931 | 1 | **B** | 历史物证包/校验文件,需裁决 |
| `F:\AIXM\wxgzh\claude-opus-5-hammer-fix-evidence.zip` | 文件 | 2933416 | 1 | **B** | 历史物证包/校验文件,需裁决 |
| `F:\AIXM\wxgzh\claude-opus-5-wechat-pipeline-evidence.zip` | 文件 | 5659119 | 1 | **B** | 历史物证包/校验文件,需裁决 |
| `F:\AIXM\wxgzh\CODELY.md` | 文件 | 22673 | 1 | **B** | 旧环境指令文档,需裁决 |
| `F:\AIXM\wxgzh\fresh-extract-verification-hotfix3.log` | 文件 | 1208 | 1 | **B** | 历史验证日志,需裁决 |
| `F:\AIXM\wxgzh\fresh-extract-verification-hotfix4.log` | 文件 | 965 | 1 | **B** | 历史验证日志,需裁决 |
| `F:\AIXM\wxgzh\fresh-extract-verification-hotfix5.log` | 文件 | 4951 | 1 | **B** | 历史验证日志,需裁决 |
| `F:\AIXM\wxgzh\fresh-extract-verification-hotfix6.log` | 文件 | 5447 | 1 | **B** | 历史验证日志,需裁决 |
| `F:\AIXM\wxgzh\fresh-extract-verification-hotfix7.log` | 文件 | 5447 | 1 | **B** | 历史验证日志,需裁决 |
| `F:\AIXM\wxgzh\fresh-extract-verification.log` | 文件 | 1044 | 1 | **B** | 历史验证日志,需裁决 |
| `F:\AIXM\wxgzh\gzh-copilot-handoff.md` | 文件 | 2958 | 1 | **B** | 交接文档,需裁决 |
| `F:\AIXM\wxgzh\gzh-design-runtime-precheck` | 目录 | 0 | 1 | **A** | 空目录 |
| `F:\AIXM\wxgzh\gzh-design-skill` | 目录 | 8942167 | 716 | **B** | 旧 git checkout(HEAD 1c5dd963,非锁定 commit),需裁决 |
| `F:\AIXM\wxgzh\gzh-design-v5-candidate-hotfix1-render-audit.zip` | 文件 | 11169 | 1 | **B** | 历史物证包/校验文件,需裁决 |
| `F:\AIXM\wxgzh\gzh-design-v5-candidate-hotfix1-runtime-diff-report.md` | 文件 | 4539 | 1 | **B** | 历史候选物证,需裁决 |
| `F:\AIXM\wxgzh\gzh-design-v5-candidate-hotfix1-source-bundle.md` | 文件 | 2388 | 1 | **B** | 历史候选物证,需裁决 |
| `F:\AIXM\wxgzh\gzh-design-v5-candidate-hotfix1-test-report.md` | 文件 | 3919 | 1 | **B** | 历史候选物证,需裁决 |
| `F:\AIXM\wxgzh\gzh-design-v5-candidate-hotfix1.zip` | 文件 | 264169 | 1 | **B** | 历史物证包/校验文件,需裁决 |
| `F:\AIXM\wxgzh\gzh-design-v5-candidate-hotfix2-render-audit.zip` | 文件 | 11242 | 1 | **B** | 历史物证包/校验文件,需裁决 |
| `F:\AIXM\wxgzh\gzh-design-v5-candidate-hotfix2-runtime-diff-report.md` | 文件 | 3627 | 1 | **B** | 历史候选物证,需裁决 |
| `F:\AIXM\wxgzh\gzh-design-v5-candidate-hotfix2-source-bundle.md` | 文件 | 4497 | 1 | **B** | 历史候选物证,需裁决 |
| `F:\AIXM\wxgzh\gzh-design-v5-candidate-hotfix2-test-report.md` | 文件 | 4972 | 1 | **B** | 历史候选物证,需裁决 |
| `F:\AIXM\wxgzh\gzh-design-v5-candidate-hotfix2.zip` | 文件 | 275822 | 1 | **B** | 历史物证包/校验文件,需裁决 |
| `F:\AIXM\wxgzh\gzh-design-v5-candidate-hotfix3-render-audit.zip` | 文件 | 84915 | 1 | **B** | 历史物证包/校验文件,需裁决 |
| `F:\AIXM\wxgzh\gzh-design-v5-candidate-hotfix3-runtime-diff-report.md` | 文件 | 3872 | 1 | **B** | 历史候选物证,需裁决 |
| `F:\AIXM\wxgzh\gzh-design-v5-candidate-hotfix3-source-bundle.md` | 文件 | 2823 | 1 | **B** | 历史候选物证,需裁决 |
| `F:\AIXM\wxgzh\gzh-design-v5-candidate-hotfix3-test-report.md` | 文件 | 4570 | 1 | **B** | 历史候选物证,需裁决 |
| `F:\AIXM\wxgzh\gzh-design-v5-candidate-hotfix3.zip` | 文件 | 283859 | 1 | **B** | 历史物证包/校验文件,需裁决 |
| `F:\AIXM\wxgzh\gzh-design-v5-candidate-hotfix4-render-audit.zip` | 文件 | 81869 | 1 | **B** | 历史物证包/校验文件,需裁决 |
| `F:\AIXM\wxgzh\gzh-design-v5-candidate-hotfix4-runtime-diff-report.md` | 文件 | 2896 | 1 | **B** | 历史候选物证,需裁决 |
| `F:\AIXM\wxgzh\gzh-design-v5-candidate-hotfix4-source-bundle.md` | 文件 | 1976 | 1 | **B** | 历史候选物证,需裁决 |
| `F:\AIXM\wxgzh\gzh-design-v5-candidate-hotfix4-test-report.md` | 文件 | 3256 | 1 | **B** | 历史候选物证,需裁决 |
| `F:\AIXM\wxgzh\gzh-design-v5-candidate-hotfix4.zip` | 文件 | 373569 | 1 | **B** | 历史物证包/校验文件,需裁决 |
| `F:\AIXM\wxgzh\gzh-design-v5-candidate-hotfix5-render-audit.zip` | 文件 | 81869 | 1 | **B** | 历史物证包/校验文件,需裁决 |
| `F:\AIXM\wxgzh\gzh-design-v5-candidate-hotfix5-runtime-diff-report.md` | 文件 | 2857 | 1 | **B** | 历史候选物证,需裁决 |
| `F:\AIXM\wxgzh\gzh-design-v5-candidate-hotfix5-source-bundle.md` | 文件 | 2358 | 1 | **B** | 历史候选物证,需裁决 |
| `F:\AIXM\wxgzh\gzh-design-v5-candidate-hotfix5-test-report.md` | 文件 | 3094 | 1 | **B** | 历史候选物证,需裁决 |
| `F:\AIXM\wxgzh\gzh-design-v5-candidate-hotfix5.zip` | 文件 | 376143 | 1 | **B** | 历史物证包/校验文件,需裁决 |
| `F:\AIXM\wxgzh\gzh-design-v5-candidate-hotfix6-render-audit.zip` | 文件 | 81869 | 1 | **B** | 历史物证包/校验文件,需裁决 |
| `F:\AIXM\wxgzh\gzh-design-v5-candidate-hotfix6-runtime-diff-report.md` | 文件 | 2181 | 1 | **B** | 历史候选物证,需裁决 |
| `F:\AIXM\wxgzh\gzh-design-v5-candidate-hotfix6-source-bundle.md` | 文件 | 1838 | 1 | **B** | 历史候选物证,需裁决 |
| `F:\AIXM\wxgzh\gzh-design-v5-candidate-hotfix6-test-report.md` | 文件 | 2646 | 1 | **B** | 历史候选物证,需裁决 |
| `F:\AIXM\wxgzh\gzh-design-v5-candidate-hotfix6.zip` | 文件 | 377407 | 1 | **B** | 历史物证包/校验文件,需裁决 |
| `F:\AIXM\wxgzh\gzh-design-v5-candidate-hotfix7-render-audit.zip` | 文件 | 81869 | 1 | **B** | 历史物证包/校验文件,需裁决 |
| `F:\AIXM\wxgzh\gzh-design-v5-candidate-hotfix7-runtime-diff-report.md` | 文件 | 1741 | 1 | **B** | 历史候选物证,需裁决 |
| `F:\AIXM\wxgzh\gzh-design-v5-candidate-hotfix7-source-bundle.md` | 文件 | 2741 | 1 | **B** | 历史候选物证,需裁决 |
| `F:\AIXM\wxgzh\gzh-design-v5-candidate-hotfix7-test-report.md` | 文件 | 2184 | 1 | **B** | 历史候选物证,需裁决 |
| `F:\AIXM\wxgzh\gzh-design-v5-candidate-hotfix7.zip` | 文件 | 378104 | 1 | **B** | 历史物证包/校验文件,需裁决 |
| `F:\AIXM\wxgzh\gzh-design-v5-candidate-source-bundle.md` | 文件 | 2525 | 1 | **B** | 历史候选物证,需裁决 |
| `F:\AIXM\wxgzh\gzh-design-v5-candidate-test-report.md` | 文件 | 3965 | 1 | **B** | 历史候选物证,需裁决 |
| `F:\AIXM\wxgzh\gzh-design-v5-candidate.zip` | 文件 | 1965365 | 1 | **B** | 历史物证包/校验文件,需裁决 |
| `F:\AIXM\wxgzh\gzh-design-v5-runtime-diff-report.md` | 文件 | 3061 | 1 | **B** | 历史物证文档 |
| `F:\AIXM\wxgzh\gzh-latest-audit` | 目录 | 404576 | 47 | **B** | 历史审计产物,需裁决 |
| `F:\AIXM\wxgzh\humanizer-audit-bundle.zip` | 文件 | 14328 | 1 | **B** | 历史物证包/校验文件,需裁决 |
| `F:\AIXM\wxgzh\kimi-k3-visual-acceptance-final-candidate.zip` | 文件 | 133938 | 1 | **B** | 历史物证包/校验文件,需裁决 |
| `F:\AIXM\wxgzh\kimi-k3-visual-acceptance-v1.zip` | 文件 | 4183503 | 1 | **B** | 历史物证包/校验文件,需裁决 |
| `F:\AIXM\wxgzh\kimi-k3-visual-acceptance-v2.zip` | 文件 | 7481436 | 1 | **B** | 历史物证包/校验文件,需裁决 |
| `F:\AIXM\wxgzh\kimi-k3-visual-acceptance-v2a.zip` | 文件 | 117568 | 1 | **B** | 历史物证包/校验文件,需裁决 |
| `F:\AIXM\wxgzh\media-enrichment-v0.1.0-dev1.zip` | 文件 | 166759 | 1 | **B** | 历史物证包/校验文件,需裁决 |
| `F:\AIXM\wxgzh\media-enrichment-v0.1.0-dev2.zip` | 文件 | 171701 | 1 | **B** | 历史物证包/校验文件,需裁决 |
| `F:\AIXM\wxgzh\media-enrichment-v0.1.0-dev3.zip` | 文件 | 268701 | 1 | **B** | 历史物证包/校验文件,需裁决 |
| `F:\AIXM\wxgzh\media-enrichment-v0.1.0-dev4.zip` | 文件 | 286715 | 1 | **B** | 历史物证包/校验文件,需裁决 |
| `F:\AIXM\wxgzh\media-enrichment-v0.1.0-dev5.zip` | 文件 | 5423665 | 1 | **B** | 历史物证包/校验文件,需裁决 |
| `F:\AIXM\wxgzh\media-enrichment-v0.1.0-dev6-hotfix1.zip` | 文件 | 5439489 | 1 | **B** | 历史物证包/校验文件,需裁决 |
| `F:\AIXM\wxgzh\media-enrichment-v0.1.0-dev6.zip` | 文件 | 5428272 | 1 | **B** | 历史物证包/校验文件,需裁决 |
| `F:\AIXM\wxgzh\media-enrichment-v0.1.0-dev7-hotfix1.zip` | 文件 | 5440005 | 1 | **B** | 历史物证包/校验文件,需裁决 |
| `F:\AIXM\wxgzh\media-enrichment-v0.1.0-dev7.zip` | 文件 | 5435500 | 1 | **B** | 历史物证包/校验文件,需裁决 |
| `F:\AIXM\wxgzh\mem-log` | 目录 | 1111910 | 10 | **C** | 运行环境持续维护的记忆日志,建议保留 |
| `F:\AIXM\wxgzh\output` | 目录 | 1424502 | 74 | **B** | 历史 hotfix 证据输出,需裁决 |
| `F:\AIXM\wxgzh\outputs` | 目录 | 30544737 | 123 | **B** | 历史 hotfix 证据输出,需裁决 |
| `F:\AIXM\wxgzh\pytest-8.4.2-offline-wheels.zip` | 文件 | 1791084 | 1 | **B** | 历史物证包/校验文件,需裁决 |
| `F:\AIXM\wxgzh\qwen3.8-wechat-pipeline-final.zip` | 文件 | 4525146 | 1 | **B** | 历史物证包/校验文件,需裁决 |
| `F:\AIXM\wxgzh\qwen3.8-wechat-pipeline-fix.zip` | 文件 | 6423351 | 1 | **B** | 历史物证包/校验文件,需裁决 |
| `F:\AIXM\wxgzh\real_article_pilot_v1` | 目录 | 183999 | 33 | **B** | 历史文章试点产物,需裁决 |
| `F:\AIXM\wxgzh\real_article_pilot_v1-hotfix1.1-clean.zip` | 文件 | 79740 | 1 | **B** | 历史物证包/校验文件,需裁决 |
| `F:\AIXM\wxgzh\real_article_pilot_v1-hotfix1.1.zip` | 文件 | 79431 | 1 | **B** | 历史物证包/校验文件,需裁决 |
| `F:\AIXM\wxgzh\real_article_pilot_v1.zip` | 文件 | 65615 | 1 | **B** | 历史物证包/校验文件,需裁决 |
| `F:\AIXM\wxgzh\repos` | 目录 | 2618549 | 600 | **C** | 强制保留:含 repos\wxgzh-pipeline 工作副本 |
| `F:\AIXM\wxgzh\runs` | 目录 | 6847245 | 149 | **B** | 历史 run 产物,可能含仅存副本,需裁决 |
| `F:\AIXM\wxgzh\rx580_build_html.py` | 文件 | 67865 | 1 | **B** | 用户脚本,需裁决 |
| `F:\AIXM\wxgzh\skill-backups` | 目录 | 35675424 | 2116 | **B** | 历史备份,需裁决 |
| `F:\AIXM\wxgzh\skill-integration` | 目录 | 232301 | 27 | **B** | 历史集成验证产物,需裁决 |
| `F:\AIXM\wxgzh\skill-source-bundle.md` | 文件 | 1830729 | 1 | **B** | 历史物证文档 |
| `F:\AIXM\wxgzh\skill-source-map.md` | 文件 | 25392 | 1 | **B** | 历史物证文档 |
| `F:\AIXM\wxgzh\source-routing-hotfix2.csv` | 文件 | 3638 | 1 | **B** | 历史物证 CSV,需裁决 |
| `F:\AIXM\wxgzh\source-routing-hotfix3.csv` | 文件 | 3864 | 1 | **B** | 历史物证 CSV,需裁决 |
| `F:\AIXM\wxgzh\source-routing-hotfix4.csv` | 文件 | 3596 | 1 | **B** | 历史物证 CSV,需裁决 |
| `F:\AIXM\wxgzh\source-routing-hotfix5.csv` | 文件 | 3607 | 1 | **B** | 历史物证 CSV,需裁决 |
| `F:\AIXM\wxgzh\source-routing-hotfix6.csv` | 文件 | 3607 | 1 | **B** | 历史物证 CSV,需裁决 |
| `F:\AIXM\wxgzh\source-routing-hotfix7.csv` | 文件 | 3607 | 1 | **B** | 历史物证 CSV,需裁决 |
| `F:\AIXM\wxgzh\super-writer-v0.3.2-rc1` | 目录 | 1646816 | 152 | **B** | 旧版本源码目录,需裁决 |
| `F:\AIXM\wxgzh\super-writer-v0.3.2-rc1-material-heavy-hotfix1.zip` | 文件 | 565991 | 1 | **B** | 历史物证包/校验文件,需裁决 |
| `F:\AIXM\wxgzh\super-writer-v0.3.2-rc1-material-heavy-hotfix2.1.zip` | 文件 | 330809 | 1 | **B** | 历史物证包/校验文件,需裁决 |
| `F:\AIXM\wxgzh\super-writer-v0.3.2-rc1-material-heavy-hotfix2.zip` | 文件 | 329379 | 1 | **B** | 历史物证包/校验文件,需裁决 |
| `F:\AIXM\wxgzh\super-writer-v0.3.2-rc1-material-heavy.zip` | 文件 | 158621 | 1 | **B** | 历史物证包/校验文件,需裁决 |
| `F:\AIXM\wxgzh\upload_85f77aec-9fe2-4543-9e38-f47d61f4108b.jpg` | 文件 | 23793 | 1 | **B** | 用户文件,需裁决 |
| `F:\AIXM\wxgzh\wxgzh-pipeline-portable-bundle-v0.1.0-dev1.zip` | 文件 | 6548865 | 1 | **B** | 历史物证包/校验文件,需裁决 |
| `F:\AIXM\wxgzh\wxgzh-pipeline-v0.1.0-dev1.zip` | 文件 | 70440 | 1 | **B** | 历史物证包/校验文件,需裁决 |
| `F:\AIXM\wxgzh\wxgzh-super-writer-v0.3.2-rc1-runtime-smoke-evidence-v2.zip` | 文件 | 35868 | 1 | **B** | 历史物证包/校验文件,需裁决 |
| `F:\AIXM\wxgzh\wxgzh-super-writer-v0.3.2-rc1-runtime-smoke-evidence.zip` | 文件 | 31164 | 1 | **B** | 历史物证包/校验文件,需裁决 |
| `F:\AIXM\wxgzh\xiaohongshu-post.md` | 文件 | 1242 | 1 | **B** | 用户内容,需裁决 |
| `F:\AIXM\wxgzh\两三百块的旧 A 卡 RX 580，我把它折腾成了本地 AI 画图机（纯小白全程踩坑记） d593feeacacb469a82872780e513c738.md` | 文件 | 39892 | 1 | **B** | 用户内容,需裁决 |
| `F:\AIXM\wxgzh\.temp\_expand.py` | 文件 | 1549 | 1 | **A** | 一次性脚本/结果或可再生测试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\_fix_o3.py` | 文件 | 3085 | 1 | **A** | 一次性脚本/结果或可再生测试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\_fix_o4.py` | 文件 | 2228 | 1 | **A** | 一次性脚本/结果或可再生测试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\_fix_outline.py` | 文件 | 5166 | 1 | **A** | 一次性脚本/结果或可再生测试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\_fix_outline2.py` | 文件 | 8668 | 1 | **A** | 一次性脚本/结果或可再生测试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\_fix_sw.py` | 文件 | 14593 | 1 | **A** | 一次性脚本/结果或可再生测试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\_fix_sw2.py` | 文件 | 9855 | 1 | **A** | 一次性脚本/结果或可再生测试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\_fix_sw3.py` | 文件 | 8811 | 1 | **A** | 一次性脚本/结果或可再生测试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\_gen_ack_sw.py` | 文件 | 450 | 1 | **A** | 一次性脚本/结果或可再生测试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\_gen_sw.py` | 文件 | 20248 | 1 | **A** | 一次性脚本/结果或可再生测试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\_gen_sw2.py` | 文件 | 35000 | 1 | **A** | 一次性脚本/结果或可再生测试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\_hf4_audit.txt` | 文件 | 2600 | 1 | **A** | 一次性脚本/结果或可再生测试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\aihot-super-writer-177-material-audit.zip` | 文件 | 102882 | 1 | **B** | 审计物证,需裁决 |
| `F:\AIXM\wxgzh\.temp\audit_materials.py` | 文件 | 12467 | 1 | **A** | 一次性脚本/结果或可再生测试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\bump_media_version.py` | 文件 | 2205 | 1 | **A** | 一次性脚本/结果或可再生测试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\claude-opus-5-pipeline` | 目录 | 34891630 | 230 | **B** | 历史构建/验证/解包物证,需裁决 |
| `F:\AIXM\wxgzh\.temp\dev5-install-extract-20260727` | 目录 | 1068 | 1 | **B** | 历史构建/验证/解包物证,需裁决 |
| `F:\AIXM\wxgzh\.temp\duplicate-groups.json` | 文件 | 1171 | 1 | **A** | 一次性脚本/结果或可再生测试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\evidence-zip-staging` | 目录 | 62245 | 34 | **B** | 历史构建/验证/解包物证,需裁决 |
| `F:\AIXM\wxgzh\.temp\fix_quotes.py` | 文件 | 425 | 1 | **A** | 一次性脚本/结果或可再生测试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\fix_quotes2.py` | 文件 | 941 | 1 | **A** | 一次性脚本/结果或可再生测试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\gen_audit_files.py` | 文件 | 6142 | 1 | **A** | 一次性脚本/结果或可再生测试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\gen_audit_v3.py` | 文件 | 4988 | 1 | **A** | 一次性脚本/结果或可再生测试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\gen_html.py` | 文件 | 16664 | 1 | **A** | 一次性脚本/结果或可再生测试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\gen_media_fixtures.py` | 文件 | 2133 | 1 | **A** | 一次性脚本/结果或可再生测试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\gen_traceability.py` | 文件 | 5270 | 1 | **A** | 一次性脚本/结果或可再生测试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\get_hashes.py` | 文件 | 1040 | 1 | **A** | 一次性脚本/结果或可再生测试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\gzh-baseline-ba1f417` | 目录 | 1763108 | 106 | **B** | 历史构建/验证/解包物证,需裁决 |
| `F:\AIXM\wxgzh\.temp\gzh-design-v5-candidate` | 目录 | 2132517 | 352 | **B** | 历史构建/验证/解包物证,需裁决 |
| `F:\AIXM\wxgzh\.temp\gzh-design-v5-hotfix7-fresh` | 目录 | 4075418 | 370 | **B** | 历史构建/验证/解包物证,需裁决 |
| `F:\AIXM\wxgzh\.temp\gzh-design-v5-rc2-fresh` | 目录 | 4081731 | 382 | **B** | 历史构建/验证/解包物证,需裁决 |
| `F:\AIXM\wxgzh\.temp\gzh-design-v5-rc2-fresh2` | 目录 | 4066189 | 381 | **B** | 历史构建/验证/解包物证,需裁决 |
| `F:\AIXM\wxgzh\.temp\gzh-design-v5-rc2-fresh3` | 目录 | 4075785 | 382 | **B** | 历史构建/验证/解包物证,需裁决 |
| `F:\AIXM\wxgzh\.temp\gzh-design-v5-rc2-fresh4` | 目录 | 4074407 | 382 | **B** | 历史构建/验证/解包物证,需裁决 |
| `F:\AIXM\wxgzh\.temp\gzh-design-v5-rc2-fresh5` | 目录 | 4072256 | 382 | **B** | 历史构建/验证/解包物证,需裁决 |
| `F:\AIXM\wxgzh\.temp\gzh-design-v5-rc2-fresh6` | 目录 | 4072767 | 382 | **B** | 历史构建/验证/解包物证,需裁决 |
| `F:\AIXM\wxgzh\.temp\gzh-design-v5-rc2-fresh7` | 目录 | 4074282 | 382 | **B** | 历史构建/验证/解包物证,需裁决 |
| `F:\AIXM\wxgzh\.temp\gzh-design-v5-runtime-source` | 目录 | 4224645 | 381 | **B** | 历史构建/验证/解包物证,需裁决 |
| `F:\AIXM\wxgzh\.temp\gzh-github-1c5dd963` | 目录 | 5865000 | 485 | **B** | 历史构建/验证/解包物证,需裁决 |
| `F:\AIXM\wxgzh\.temp\gzh-v5-fresh-extract` | 目录 | 1626183 | 297 | **B** | 历史构建/验证/解包物证,需裁决 |
| `F:\AIXM\wxgzh\.temp\gzh-v5-fresh-extract3` | 目录 | 1811229 | 326 | **B** | 历史构建/验证/解包物证,需裁决 |
| `F:\AIXM\wxgzh\.temp\gzh-v5-fresh-extract4` | 目录 | 1831540 | 327 | **B** | 历史构建/验证/解包物证,需裁决 |
| `F:\AIXM\wxgzh\.temp\gzh-v5-fresh-extract5` | 目录 | 1368025 | 122 | **B** | 历史构建/验证/解包物证,需裁决 |
| `F:\AIXM\wxgzh\.temp\gzh-v5-fresh-extract5b` | 目录 | 1842808 | 328 | **B** | 历史构建/验证/解包物证,需裁决 |
| `F:\AIXM\wxgzh\.temp\gzh-v5-fresh5c` | 目录 | 1842684 | 328 | **B** | 历史构建/验证/解包物证,需裁决 |
| `F:\AIXM\wxgzh\.temp\gzh-v5-fresh5d` | 目录 | 1843025 | 328 | **B** | 历史构建/验证/解包物证,需裁决 |
| `F:\AIXM\wxgzh\.temp\gzh-v5-fresh6` | 目录 | 1868878 | 330 | **B** | 历史构建/验证/解包物证,需裁决 |
| `F:\AIXM\wxgzh\.temp\gzh-v5-fresh7` | 目录 | 1878768 | 330 | **B** | 历史构建/验证/解包物证,需裁决 |
| `F:\AIXM\wxgzh\.temp\hotfix5-integration-fix` | 目录 | 7564 | 1 | **A** | 一次性脚本/结果或可再生测试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\hotfix5-integration-fix-final` | 目录 | 7564 | 1 | **A** | 一次性脚本/结果或可再生测试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\hotfix5-integration-skills` | 目录 | 5174034 | 640 | **B** | 历史构建/验证/解包物证,需裁决 |
| `F:\AIXM\wxgzh\.temp\hotfix5-media-final-explicit-basetemp` | 目录 | 907443 | 371 | **A** | pytest 临时区/可再生产物,建议删 |
| `F:\AIXM\wxgzh\.temp\hotfix5-media-final-results.json` | 文件 | 272501 | 1 | **A** | 一次性脚本/结果或可再生测试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\hotfix5-media-nonskip` | 目录 | 491685 | 311 | **B** | 未显式归类,需裁决 |
| `F:\AIXM\wxgzh\.temp\hotfix5-media-pytest-results.zip` | 文件 | 25290 | 1 | **A** | 一次性脚本/结果或可再生测试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\hotfix5-media-safety-final-basetemp` | 目录 | 598506 | 343 | **A** | pytest 临时区/可再生产物,建议删 |
| `F:\AIXM\wxgzh\.temp\hotfix5-media-stable-final-basetemp` | 目录 | 512024 | 304 | **A** | pytest 临时区/可再生产物,建议删 |
| `F:\AIXM\wxgzh\.temp\hotfix5-media-stable-final2-basetemp` | 目录 | 571205 | 306 | **A** | pytest 临时区/可再生产物,建议删 |
| `F:\AIXM\wxgzh\.temp\hotfix5-media-stable-final3-basetemp` | 目录 | 571205 | 306 | **A** | pytest 临时区/可再生产物,建议删 |
| `F:\AIXM\wxgzh\.temp\hotfix5-media-test-results.json` | 文件 | 272501 | 1 | **A** | 一次性脚本/结果或可再生测试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\hotfix5-pipeline-evidence-basetemp` | 目录 | 37091 | 198 | **B** | 历史构建/验证/解包物证,需裁决 |
| `F:\AIXM\wxgzh\.temp\hotfix5-pipeline-final-full-basetemp` | 目录 | 2607848 | 1490 | **A** | pytest 临时区/可再生产物,建议删 |
| `F:\AIXM\wxgzh\.temp\hotfix5-pipeline-final-pytest` | 目录 | 1182857 | 610 | **A** | pytest 临时区/可再生产物,建议删 |
| `F:\AIXM\wxgzh\.temp\hotfix5-pipeline-full2-basetemp` | 目录 | 2594277 | 1474 | **A** | pytest 临时区/可再生产物,建议删 |
| `F:\AIXM\wxgzh\.temp\hotfix5-pipeline-install-final-basetemp` | 目录 | 29325 | 166 | **A** | pytest 临时区/可再生产物,建议删 |
| `F:\AIXM\wxgzh\.temp\hotfix5-pipeline-install-gates-basetemp` | 目录 | 33491 | 182 | **A** | pytest 临时区/可再生产物,建议删 |
| `F:\AIXM\wxgzh\.temp\hotfix5-pipeline-targeted-final` | 目录 | 24048 | 99 | **B** | 未显式归类,需裁决 |
| `F:\AIXM\wxgzh\.temp\hotfix5-pytest-media` | 目录 | 800530 | 339 | **A** | pytest 临时区/可再生产物,建议删 |
| `F:\AIXM\wxgzh\.temp\hotfix5-pytest-media-final` | 目录 | 800698 | 339 | **A** | pytest 临时区/可再生产物,建议删 |
| `F:\AIXM\wxgzh\.temp\hotfix5-pytest-pipeline` | 目录 | 27355 | 150 | **A** | pytest 临时区/可再生产物,建议删 |
| `F:\AIXM\wxgzh\.temp\hotfix5-pytest-pipeline-2` | 目录 | 27355 | 150 | **A** | pytest 临时区/可再生产物,建议删 |
| `F:\AIXM\wxgzh\.temp\hotfix6-accept-skills` | 目录 | 5362639 | 660 | **B** | 历史构建/验证/解包物证,需裁决 |
| `F:\AIXM\wxgzh\.temp\hotfix6-ci-fix-basetemp` | 目录 | 493599 | 297 | **A** | 测试/调试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\hotfix6-ci-fix2-basetemp` | 目录 | 610273 | 353 | **A** | 测试/调试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\hotfix6-cross-repo-integration.json` | 文件 | 9091 | 1 | **A** | 一次性脚本/结果或可再生测试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\hotfix6-debug-run` | 目录 | 37681 | 33 | **A** | 一次性脚本/结果或可再生测试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\hotfix6-debug-run2` | 目录 | 66494 | 39 | **A** | 一次性脚本/结果或可再生测试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\hotfix6-debug-run3` | 目录 | 94435 | 48 | **A** | 一次性脚本/结果或可再生测试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\hotfix6-doctor-project` | 目录 | 0 | 0 | **A** | 测试/调试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\hotfix6-final-accept-skills` | 目录 | 5362741 | 660 | **B** | 历史构建/验证/解包物证,需裁决 |
| `F:\AIXM\wxgzh\.temp\hotfix6-final-doctor-project` | 目录 | 0 | 0 | **A** | 测试/调试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\hotfix6-final-light-basetemp` | 目录 | 18359 | 82 | **A** | 测试/调试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\hotfix6-final-rollback-original.py` | 文件 | 27617 | 1 | **A** | 一次性脚本/结果或可再生测试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\hotfix6-final-unpacked` | 目录 | 5410301 | 651 | **B** | 历史构建/验证/解包物证,需裁决 |
| `F:\AIXM\wxgzh\.temp\hotfix6-install-src` | 目录 | 5410289 | 651 | **B** | 历史构建/验证/解包物证,需裁决 |
| `F:\AIXM\wxgzh\.temp\hotfix6-integration-fixtures` | 目录 | 47693 | 11 | **B** | 未显式归类,需裁决 |
| `F:\AIXM\wxgzh\.temp\hotfix6-integration-run` | 目录 | 80005 | 76 | **A** | 测试/调试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\hotfix6-integration-run10` | 目录 | 288582 | 80 | **A** | 测试/调试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\hotfix6-integration-run2` | 目录 | 39002 | 38 | **A** | 测试/调试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\hotfix6-integration-run3` | 目录 | 78004 | 76 | **A** | 测试/调试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\hotfix6-integration-run4` | 目录 | 78003 | 76 | **A** | 测试/调试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\hotfix6-integration-run6` | 目录 | 78005 | 76 | **A** | 测试/调试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\hotfix6-integration-run7` | 目录 | 39003 | 38 | **A** | 测试/调试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\hotfix6-integration-run8` | 目录 | 38954 | 38 | **A** | 测试/调试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\hotfix6-integration-run9` | 目录 | 88357 | 54 | **A** | 测试/调试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\hotfix6-integration-skills` | 目录 | 5214101 | 642 | **B** | 历史构建/验证/解包物证,需裁决 |
| `F:\AIXM\wxgzh\.temp\hotfix6-integration-src` | 目录 | 7635009 | 650 | **B** | 历史构建/验证/解包物证,需裁决 |
| `F:\AIXM\wxgzh\.temp\hotfix6-media-approval-basetemp` | 目录 | 685393 | 370 | **A** | 测试/调试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\hotfix6-media-approval-basetemp2` | 目录 | 685432 | 370 | **A** | 测试/调试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\hotfix6-media-final-full-basetemp` | 目录 | 1083318 | 471 | **A** | 测试/调试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\hotfix6-media-final-full-results.json` | 文件 | 267031 | 1 | **A** | 一次性脚本/结果或可再生测试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\hotfix6-media-full-basetemp` | 目录 | 1083054 | 471 | **A** | 测试/调试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\hotfix6-media-full-results.json` | 文件 | 266723 | 1 | **A** | 一次性脚本/结果或可再生测试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\hotfix6-media-probe3-basetemp` | 目录 | 685315 | 370 | **A** | 测试/调试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\hotfix6-media-version-full-basetemp` | 目录 | 1083408 | 471 | **A** | 测试/调试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\hotfix6-media-version-full-results.json` | 文件 | 269726 | 1 | **A** | 一次性脚本/结果或可再生测试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\hotfix6-pipeline-failed3-basetemp` | 目录 | 122047 | 63 | **A** | 测试/调试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\hotfix6-pipeline-full-basetemp` | 目录 | 3060180 | 1578 | **A** | 测试/调试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\hotfix6-pipeline-full-results.json` | 文件 | 91184 | 1 | **A** | 一次性脚本/结果或可再生测试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\hotfix6-pipeline-full2-basetemp` | 目录 | 3114110 | 1595 | **A** | 测试/调试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\hotfix6-pipeline-full2-results.json` | 文件 | 80408 | 1 | **A** | 一次性脚本/结果或可再生测试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\hotfix6-pipeline-probe-basetemp` | 目录 | 176422 | 191 | **A** | 测试/调试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\hotfix6-pipeline-probe2-basetemp` | 目录 | 189542 | 203 | **A** | 测试/调试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\hotfix6-pipeline-probe3-basetemp` | 目录 | 308392 | 227 | **A** | 测试/调试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\hotfix6-pipeline-probe4-basetemp` | 目录 | 422886 | 263 | **A** | 测试/调试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\hotfix6-pipeline-probe5-basetemp` | 目录 | 496656 | 297 | **A** | 测试/调试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\hotfix6-pipeline-targeted-basetemp` | 目录 | 479073 | 254 | **A** | 测试/调试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\hotfix6-repos` | 目录 | 4461430 | 825 | **B** | 指定保留物证(第三轮指令),需审核者裁决 |
| `F:\AIXM\wxgzh\.temp\hotfix6-rollback-original-run_media_enrichment.py` | 文件 | 27617 | 1 | **A** | 一次性脚本/结果或可再生测试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\hotfix6-src` | 目录 | 4801269 | 535 | **B** | 历史构建/验证/解包物证,需裁决 |
| `F:\AIXM\wxgzh\.temp\hotfix6-src-git` | 目录 | 7616959 | 661 | **B** | 历史构建/验证/解包物证,需裁决 |
| `F:\AIXM\wxgzh\.temp\hotfix6-stage7-build-20260729T144447` | 目录 | 1837740 | 240 | **B** | 历史构建/验证/解包物证,需裁决 |
| `F:\AIXM\wxgzh\.temp\hotfix6-staging` | 目录 | 21526300 | 2588 | **B** | 历史构建/验证/解包物证,需裁决 |
| `F:\AIXM\wxgzh\.temp\hotfix6-unpacked-bundle` | 目录 | 5410305 | 651 | **B** | 历史构建/验证/解包物证,需裁决 |
| `F:\AIXM\wxgzh\.temp\hotfix7-build-staging` | 目录 | 5520031 | 665 | **B** | 历史构建/验证/解包物证,需裁决 |
| `F:\AIXM\wxgzh\.temp\hotfix7-build-staging-final` | 目录 | 5521633 | 665 | **B** | 历史构建/验证/解包物证,需裁决 |
| `F:\AIXM\wxgzh\.temp\hotfix7R-build-staging` | 目录 | 5522512 | 665 | **B** | 历史构建/验证/解包物证,需裁决 |
| `F:\AIXM\wxgzh\.temp\hotfix7R2-build-staging` | 目录 | 5523255 | 665 | **B** | 历史构建/验证/解包物证,需裁决 |
| `F:\AIXM\wxgzh\.temp\hotfix7R3-build-staging` | 目录 | 11757411 | 1488 | **B** | 历史构建/验证/解包物证,需裁决 |
| `F:\AIXM\wxgzh\.temp\hotfix7R4-build-staging` | 目录 | 11789570 | 1488 | **B** | 历史构建/验证/解包物证,需裁决 |
| `F:\AIXM\wxgzh\.temp\humanizer-audit` | 目录 | 438588 | 102 | **B** | 历史构建/验证/解包物证,需裁决 |
| `F:\AIXM\wxgzh\.temp\integ_dl3` | 目录 | 2347 | 1 | **A** | 一次性脚本/结果或可再生测试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\integ_dl4` | 目录 | 27350 | 1 | **A** | 一次性脚本/结果或可再生测试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\integ_h3.json` | 文件 | 4135 | 1 | **A** | 一次性脚本/结果或可再生测试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\integ_h4.json` | 文件 | 7146 | 1 | **A** | 一次性脚本/结果或可再生测试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\integ_local.json` | 文件 | 1579 | 1 | **A** | 一次性脚本/结果或可再生测试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\integ_local_result.json` | 文件 | 1579 | 1 | **A** | 一次性脚本/结果或可再生测试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\k3-raw-full.json` | 文件 | 191733 | 1 | **A** | 一次性脚本/结果或可再生测试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\k3-raw-full.md` | 文件 | 80132 | 1 | **A** | 一次性脚本/结果或可再生测试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\k3-raw-v2.json` | 文件 | 117712 | 1 | **A** | 一次性脚本/结果或可再生测试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\k3-raw-v2.md` | 文件 | 50065 | 1 | **A** | 一次性脚本/结果或可再生测试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\k3-raw-v3.json` | 文件 | 191984 | 1 | **A** | 一次性脚本/结果或可再生测试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\k3-raw.json` | 文件 | 169643 | 1 | **A** | 一次性脚本/结果或可再生测试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\k3-raw.md` | 文件 | 70576 | 1 | **A** | 一次性脚本/结果或可再生测试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\kimi-k3-full-rerun-20260725T` | 目录 | 0 | 0 | **B** | 历史构建/验证/解包物证,需裁决 |
| `F:\AIXM\wxgzh\.temp\kimi-k3-full-rerun-20260725T200400` | 目录 | 2567065 | 146 | **B** | 历史构建/验证/解包物证,需裁决 |
| `F:\AIXM\wxgzh\.temp\kimi-k3-visual-acceptance-v1-20260727T001021` | 目录 | 4426025 | 32 | **B** | 历史构建/验证/解包物证,需裁决 |
| `F:\AIXM\wxgzh\.temp\kimi-k3-visual-acceptance-v2-20260727T020114` | 目录 | 8148594 | 76 | **B** | 历史构建/验证/解包物证,需裁决 |
| `F:\AIXM\wxgzh\.temp\lastrun.txt` | 文件 | 13 | 1 | **A** | 一次性脚本/结果或可再生测试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\liveproof_check.py` | 文件 | 2739 | 1 | **A** | 一次性脚本/结果或可再生测试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\liveproof_out` | 目录 | 43132 | 4 | **B** | 历史构建/验证/解包物证,需裁决 |
| `F:\AIXM\wxgzh\.temp\material-audit-report.md` | 文件 | 1908 | 1 | **A** | 一次性脚本/结果或可再生测试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\material-audit.json` | 文件 | 761 | 1 | **A** | 一次性脚本/结果或可再生测试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\material-usage-map.csv` | 文件 | 26644 | 1 | **A** | 一次性脚本/结果或可再生测试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\media-enrichment-dev5-20260727T0030` | 目录 | 6506692 | 156 | **B** | 历史构建/验证/解包物证,需裁决 |
| `F:\AIXM\wxgzh\.temp\media-enrichment-dev6-20260727T1329` | 目录 | 8425224 | 185 | **B** | 历史构建/验证/解包物证,需裁决 |
| `F:\AIXM\wxgzh\.temp\media-enrichment-dev6-hotfix1-20260727T1434` | 目录 | 8449052 | 185 | **B** | 历史构建/验证/解包物证,需裁决 |
| `F:\AIXM\wxgzh\.temp\media-enrichment-dev7-hotfix1-20260727T1457` | 目录 | 6611474 | 159 | **B** | 历史构建/验证/解包物证,需裁决 |
| `F:\AIXM\wxgzh\.temp\media-enrichment-oss-20260727T1547` | 目录 | 529682 | 172 | **B** | 历史构建/验证/解包物证,需裁决 |
| `F:\AIXM\wxgzh\.temp\media-enrichment-v0.1.0-dev5.zip` | 文件 | 5423665 | 1 | **A** | 与根目录重复的 zip,建议删 |
| `F:\AIXM\wxgzh\.temp\media-enrichment-v0.1.0-dev6-hotfix1.zip` | 文件 | 5439489 | 1 | **A** | 与根目录重复的 zip,建议删 |
| `F:\AIXM\wxgzh\.temp\media-enrichment-v0.1.0-dev6.zip` | 文件 | 5428272 | 1 | **A** | 与根目录重复的 zip,建议删 |
| `F:\AIXM\wxgzh\.temp\media-enrichment-v0.1.0-dev7-hotfix1.zip` | 文件 | 5440005 | 1 | **A** | 与根目录重复的 zip,建议删 |
| `F:\AIXM\wxgzh\.temp\media-enrichment-v0.1.0-dev7.zip` | 文件 | 5435500 | 1 | **A** | 与根目录重复的 zip,建议删 |
| `F:\AIXM\wxgzh\.temp\obs47-credential-source-test` | 目录 | 71 | 1 | **B** | 历史构建/验证/解包物证,需裁决 |
| `F:\AIXM\wxgzh\.temp\obs62s-build-staging` | 目录 | 6796064 | 972 | **B** | 历史构建/验证/解包物证,需裁决 |
| `F:\AIXM\wxgzh\.temp\pytest_canon.txt` | 文件 | 464 | 1 | **A** | 一次性脚本/结果或可再生测试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\pytest_full.txt` | 文件 | 462 | 1 | **A** | 一次性脚本/结果或可再生测试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\pytest_host.txt` | 文件 | 464 | 1 | **A** | 一次性脚本/结果或可再生测试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\pytest_negative.txt` | 文件 | 708 | 1 | **A** | 一次性脚本/结果或可再生测试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\pytest_out.txt` | 文件 | 81 | 1 | **A** | 一次性脚本/结果或可再生测试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\pytest_out2.txt` | 文件 | 381 | 1 | **A** | 一次性脚本/结果或可再生测试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\qwen38-pipeline-20260727T114809` | 目录 | 17167722 | 200 | **B** | 历史构建/验证/解包物证,需裁决 |
| `F:\AIXM\wxgzh\.temp\skill-backups` | 目录 | 1602315 | 137 | **B** | 历史构建/验证/解包物证,需裁决 |
| `F:\AIXM\wxgzh\.temp\smoke-direct-v032-rc1` | 目录 | 14234 | 7 | **B** | 历史构建/验证/解包物证,需裁决 |
| `F:\AIXM\wxgzh\.temp\smoke-material-heavy-v032-rc1` | 目录 | 22352 | 14 | **B** | 历史构建/验证/解包物证,需裁决 |
| `F:\AIXM\wxgzh\.temp\stage19-direct-min` | 目录 | 329 | 2 | **B** | 未显式归类,需裁决 |
| `F:\AIXM\wxgzh\.temp\stage19-media-pytest` | 目录 | 1312701 | 634 | **B** | 未显式归类,需裁决 |
| `F:\AIXM\wxgzh\.temp\stage19-pipeline-pytest` | 目录 | 0 | 0 | **B** | 未显式归类,需裁决 |
| `F:\AIXM\wxgzh\.temp\stage19-pipeline-pytest-2` | 目录 | 5512766 | 1973 | **B** | 历史构建/验证/解包物证,需裁决 |
| `F:\AIXM\wxgzh\.temp\stage20r-media-pytest-1` | 目录 | 1312914 | 634 | **B** | 未显式归类,需裁决 |
| `F:\AIXM\wxgzh\.temp\stage20r-media-results.txt` | 文件 | 438 | 1 | **A** | 一次性脚本/结果或可再生测试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\stage20r-obs56-pytest-1` | 目录 | 173467 | 66 | **B** | 未显式归类,需裁决 |
| `F:\AIXM\wxgzh\.temp\stage20r-obs56-pytest-2` | 目录 | 1169 | 5 | **B** | 未显式归类,需裁决 |
| `F:\AIXM\wxgzh\.temp\stage20r-obs56-pytest-3` | 目录 | 1169 | 5 | **B** | 未显式归类,需裁决 |
| `F:\AIXM\wxgzh\.temp\stage20r-observation-direct-2` | 目录 | 377 | 1 | **B** | 未显式归类,需裁决 |
| `F:\AIXM\wxgzh\.temp\stage20r-pipeline-pytest-1` | 目录 | 5558207 | 1990 | **B** | 历史构建/验证/解包物证,需裁决 |
| `F:\AIXM\wxgzh\.temp\stage20r-pipeline-results.txt` | 文件 | 49063 | 1 | **A** | 一次性脚本/结果或可再生测试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\super-writer-199-runtime-audit` | 目录 | 436581 | 44 | **B** | 历史构建/验证/解包物证,需裁决 |
| `F:\AIXM\wxgzh\.temp\super-writer-199-runtime-audit.zip` | 文件 | 145590 | 1 | **B** | 审计物证,需裁决 |
| `F:\AIXM\wxgzh\.temp\super-writer-github-verify` | 目录 | 1418608 | 126 | **B** | 历史构建/验证/解包物证,需裁决 |
| `F:\AIXM\wxgzh\.temp\super-writer-v0.3.1-backup` | 目录 | 1544351 | 136 | **B** | 历史构建/验证/解包物证,需裁决 |
| `F:\AIXM\wxgzh\.temp\sw-hotfix2-work` | 目录 | 3810410 | 469 | **B** | 历史构建/验证/解包物证,需裁决 |
| `F:\AIXM\wxgzh\.temp\sw-hotfix2.1-work` | 目录 | 2811280 | 147 | **B** | 历史构建/验证/解包物证,需裁决 |
| `F:\AIXM\wxgzh\.temp\sw-v3-audit` | 目录 | 222393 | 17 | **B** | 历史构建/验证/解包物证,需裁决 |
| `F:\AIXM\wxgzh\.temp\sw-v3-audit.zip` | 文件 | 73957 | 1 | **B** | 审计物证,需裁决 |
| `F:\AIXM\wxgzh\.temp\sync-verify-fresh` | 目录 | 983933 | 138 | **B** | 历史构建/验证/解包物证,需裁决 |
| `F:\AIXM\wxgzh\.temp\t_canon.txt` | 文件 | 81 | 1 | **A** | 一次性脚本/结果或可再生测试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\t_fl.txt` | 文件 | 81 | 1 | **A** | 一次性脚本/结果或可再生测试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\t_full3.txt` | 文件 | 462 | 1 | **A** | 一次性脚本/结果或可再生测试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\t_full4.txt` | 文件 | 463 | 1 | **A** | 一次性脚本/结果或可再生测试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\t_h3.txt` | 文件 | 81 | 1 | **A** | 一次性脚本/结果或可再生测试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\t_h4.txt` | 文件 | 4527 | 1 | **A** | 一次性脚本/结果或可再生测试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\t_h4b.txt` | 文件 | 81 | 1 | **A** | 一次性脚本/结果或可再生测试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\t_media_e2e.txt` | 文件 | 1375 | 1 | **A** | 一次性脚本/结果或可再生测试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\t_media_full.txt` | 文件 | 3685 | 1 | **A** | 一次性脚本/结果或可再生测试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\t_media_full2.txt` | 文件 | 356 | 1 | **A** | 一次性脚本/结果或可再生测试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\t_theme.txt` | 文件 | 81 | 1 | **A** | 一次性脚本/结果或可再生测试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\topic-clusters.json` | 文件 | 4499 | 1 | **A** | 一次性脚本/结果或可再生测试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\verification-result.md` | 文件 | 493 | 1 | **A** | 一次性脚本/结果或可再生测试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\verify_audit.py` | 文件 | 3926 | 1 | **A** | 一次性脚本/结果或可再生测试临时区,建议删 |
| `F:\AIXM\wxgzh\.temp\wxgzh-hotfix7R3-install-source` | 目录 | 5534608 | 666 | **B** | 历史构建/验证/解包物证,需裁决 |
| `F:\AIXM\wxgzh\.temp\wxgzh-hotfix7R4-verification-source` | 目录 | 5565446 | 670 | **B** | 历史构建/验证/解包物证,需裁决 |
| `F:\AIXM\wxgzh\.temp\wxgzh-pipeline` | 目录 | 4926095 | 384 | **B** | 运行目录区;子项逐条见下 |
| `F:\AIXM\wxgzh\.temp\wxgzh-pipeline\20260729T233443-topic-jn47b4` | 目录 | 43070 | 33 | **B** | 未归档早期 run,可能含仅存数据,需裁决 |
| `F:\AIXM\wxgzh\.temp\wxgzh-pipeline\20260729T235653-topic-3ikaxu` | 目录 | 40106 | 38 | **B** | 未归档早期 run,可能含仅存数据,需裁决 |
| `F:\AIXM\wxgzh\.temp\wxgzh-pipeline\20260730T041535-openai-gpt-5-6-sol-terra-0ltbjg` | 目录 | 135302 | 30 | **B** | 未归档早期 run,可能含仅存数据,需裁决 |
| `F:\AIXM\wxgzh\.temp\wxgzh-pipeline\20260730T204429-openai-gpt-5-6-sol-terra-gnk5xb` | 目录 | 7849 | 10 | **B** | 未归档早期 run,可能含仅存数据,需裁决 |
| `F:\AIXM\wxgzh\.temp\wxgzh-pipeline\20260730T222605-ai-9je33o` | 目录 | 101537 | 45 | **A** | 已完整归档至 repo audit/runs(含 final.html 补档),建议删 |
| `F:\AIXM\wxgzh\.temp\wxgzh-pipeline\20260731T031531-ai-u8zlo6` | 目录 | 167092 | 46 | **A** | 已完整归档至 repo audit/runs(含 final.html 补档),建议删 |
| `F:\AIXM\wxgzh\.temp\wxgzh-pipeline\20260731T135947-ai-bbg4al` | 目录 | 2966433 | 98 | **A** | 已完整归档至 repo audit/runs(含 final.html 补档),建议删 |
| `F:\AIXM\wxgzh\.temp\wxgzh-pipeline\20260801T182628-topic-ui5f7p` | 目录 | 1464706 | 84 | **A** | 已完整归档至 repo audit/runs(含 final.html 补档),建议删 |
| `F:\AIXM\wxgzh\.temp\wxgzh-pipeline-build` | 目录 | 9478607 | 702 | **B** | 历史构建/验证/解包物证,需裁决 |
| `F:\AIXM\wxgzh\.temp\wxgzh-pipeline-repo` | 目录 | 1708229 | 615 | **B** | 指定保留物证(第三轮指令),需审核者裁决 |
| `F:\AIXM\wxgzh\.temp\wxgzh-repos-sync` | 目录 | 9284764 | 1001 | **B** | 历史构建/验证/解包物证,需裁决 |
| `F:\AIXM\wxgzh\.temp\zh-human-writing-v0.1.0-fresh` | 目录 | 404316 | 88 | **B** | 历史构建/验证/解包物证,需裁决 |
| `F:\AIXM\wxgzh\.agents\.skills-hotfix6.hotfix5-install-24124-20260729T182626685523` | 目录 | 0 | 0 | **B** | 安装事务残留(空),需裁决 |
| `F:\AIXM\wxgzh\.agents\.skills-hotfix7R3.hotfix5-install-27200-20260730T163828424004` | 目录 | 0 | 0 | **B** | 安装事务残留(空),需裁决 |
| `F:\AIXM\wxgzh\.agents\.skills.hotfix5-install-20808-20260729T173007584151` | 目录 | 10484859 | 871 | **B** | 安装事务残留/备份,需裁决 |
| `F:\AIXM\wxgzh\.agents\skills` | 目录 | 6643025 | 982 | **C** | 强制保留:运行环境 |
| `F:\AIXM\wxgzh\.agents\skills-backup` | 目录 | 14931668 | 2079 | **B** | 历史 skills 状态备份,需裁决 |
| `F:\AIXM\wxgzh\.agents\skills-halfstate-20260730` | 目录 | 12831028 | 946 | **B** | 历史中间态快照,需裁决 |
| `F:\AIXM\wxgzh\.agents\skills-hotfix6-lastknown-good-20260730` | 目录 | 5616032 | 687 | **B** | 历史 last-known-good 快照,需裁决 |
| `F:\AIXM\wxgzh\.agents\skills-hotfix7R3` | 目录 | 5367543 | 661 | **B** | 历史 skills 快照,需裁决 |
| `F:\AIXM\wxgzh\repos\wxgzh-pipeline` | 目录 | 2618549 | 600 | **C** | 强制保留:wxgzh-pipeline 工作副本 |
| `F:\AIXM\wxgzh\runs\2026-07-28-freemodel` | 目录 | 108167 | 24 | **B** | 历史 run 产物,可能含仅存副本,需裁决 |
| `F:\AIXM\wxgzh\runs\2026-07-28-manual` | 目录 | 6005121 | 70 | **B** | 历史 run 产物,可能含仅存副本,需裁决 |
| `F:\AIXM\wxgzh\runs\2026-07-29-rx580` | 目录 | 643748 | 46 | **B** | 历史 run 产物,可能含仅存副本,需裁决 |
| `F:\AIXM\wxgzh\runs\2026-07-29-tokenrhythm` | 目录 | 90209 | 9 | **B** | 历史 run 产物,可能含仅存副本,需裁决 |
| `F:\AIXM\wxgzh\articles\core-card.md` | 文件 | 2443 | 1 | **B** | 历史写作产物,需裁决 |
| `F:\AIXM\wxgzh\articles\deepseek-v4-flash` | 目录 | 388610 | 10 | **B** | 历史写作产物,需裁决 |
| `F:\AIXM\wxgzh\articles\editor-report.md` | 文件 | 1664 | 1 | **B** | 历史写作产物,需裁决 |
| `F:\AIXM\wxgzh\articles\evidence-map.md` | 文件 | 3923 | 1 | **B** | 历史写作产物,需裁决 |
| `F:\AIXM\wxgzh\articles\k3-article-draft.md` | 文件 | 7537 | 1 | **B** | 历史写作产物,需裁决 |
| `F:\AIXM\wxgzh\articles\k3-article-hammer.html` | 文件 | 16661 | 1 | **B** | 历史写作产物,需裁决 |
| `F:\AIXM\wxgzh\articles\k3-article-hammer_预览.html` | 文件 | 27152 | 1 | **B** | 历史写作产物,需裁决 |
| `F:\AIXM\wxgzh\articles\k3-article-v3-hammer.html` | 文件 | 16187 | 1 | **B** | 历史写作产物,需裁决 |
| `F:\AIXM\wxgzh\articles\k3-article.md` | 文件 | 7834 | 1 | **B** | 历史写作产物,需裁决 |
| `F:\AIXM\wxgzh\articles\k3-final-draft.md` | 文件 | 7894 | 1 | **B** | 历史写作产物,需裁决 |
| `F:\AIXM\wxgzh\articles\k3-final-hammer.html` | 文件 | 16253 | 1 | **B** | 历史写作产物,需裁决 |
| `F:\AIXM\wxgzh\articles\k3-latest-draft.md` | 文件 | 4005 | 1 | **B** | 历史写作产物,需裁决 |
| `F:\AIXM\wxgzh\articles\k3-latest-hammer.html` | 文件 | 11921 | 1 | **B** | 历史写作产物,需裁决 |
| `F:\AIXM\wxgzh\articles\k3-v2-hammer.html` | 文件 | 11657 | 1 | **B** | 历史写作产物,需裁决 |
| `F:\AIXM\wxgzh\articles\kimi-k3-ab-test` | 目录 | 5336774 | 175 | **B** | 历史写作产物,需裁决 |
| `F:\AIXM\wxgzh\articles\kimi-k3-ab-test-experiment-bundle.zip` | 文件 | 225782 | 1 | **B** | 历史写作产物,需裁决 |
| `F:\AIXM\wxgzh\articles\kimi-k3-ab-test-hotfix1.zip` | 文件 | 322361 | 1 | **B** | 历史写作产物,需裁决 |
| `F:\AIXM\wxgzh\articles\kimi-k3-ab-test-hotfix2.1.zip` | 文件 | 472094 | 1 | **B** | 历史写作产物,需裁决 |
| `F:\AIXM\wxgzh\articles\kimi-k3-ab-test-hotfix2.2.zip` | 文件 | 932823 | 1 | **B** | 历史写作产物,需裁决 |
| `F:\AIXM\wxgzh\articles\kimi-k3-ab-test-hotfix2.3.1.zip` | 文件 | 1032457 | 1 | **B** | 历史写作产物,需裁决 |
| `F:\AIXM\wxgzh\articles\kimi-k3-ab-test-hotfix2.3.2.zip` | 文件 | 1034180 | 1 | **B** | 历史写作产物,需裁决 |
| `F:\AIXM\wxgzh\articles\kimi-k3-ab-test-hotfix2.3.3-clean.zip` | 文件 | 1035334 | 1 | **B** | 历史写作产物,需裁决 |
| `F:\AIXM\wxgzh\articles\kimi-k3-ab-test-hotfix2.3.3.zip` | 文件 | 1035018 | 1 | **B** | 历史写作产物,需裁决 |
| `F:\AIXM\wxgzh\articles\kimi-k3-ab-test-hotfix2.3.zip` | 文件 | 1054765 | 1 | **B** | 历史写作产物,需裁决 |
| `F:\AIXM\wxgzh\articles\kimi-k3-ab-test-hotfix2.zip` | 文件 | 369089 | 1 | **B** | 历史写作产物,需裁决 |
| `F:\AIXM\wxgzh\articles\kimi-k3-article` | 目录 | 743103 | 36 | **B** | 历史写作产物,需裁决 |
| `F:\AIXM\wxgzh\articles\material-readiness.yaml` | 文件 | 505 | 1 | **B** | 历史写作产物,需裁决 |
| `F:\AIXM\wxgzh\articles\outline.md` | 文件 | 865 | 1 | **B** | 历史写作产物,需裁决 |
| `F:\AIXM\wxgzh\articles\phase1-material-readiness.md` | 文件 | 629 | 1 | **B** | 历史写作产物,需裁决 |
| `F:\AIXM\wxgzh\articles\phase6-editor-report.md` | 文件 | 1049 | 1 | **B** | 历史写作产物,需裁决 |
| `F:\AIXM\wxgzh\articles\rx580` | 目录 | 299071 | 2 | **B** | 历史写作产物,需裁决 |
| `F:\AIXM\wxgzh\articles\writing-brief.md` | 文件 | 1081 | 1 | **B** | 历史写作产物,需裁决 |
| `F:\AIXM\wxgzh\output\check_session.py` | 文件 | 669 | 1 | **B** | 历史产物,需裁决 |
| `F:\AIXM\wxgzh\output\k3-continuous-20260721-172131` | 目录 | 42693 | 8 | **B** | 历史产物,需裁决 |
| `F:\AIXM\wxgzh\output\k3-fix-20260721-154824` | 目录 | 1371658 | 59 | **B** | 历史产物,需裁决 |
| `F:\AIXM\wxgzh\output\k3-phase3-20260721-171537` | 目录 | 9074 | 5 | **B** | 历史产物,需裁决 |
| `F:\AIXM\wxgzh\output\session_check.py` | 文件 | 408 | 1 | **B** | 历史产物,需裁决 |
| `F:\AIXM\wxgzh\outputs\hotfix5-audit` | 目录 | 644567 | 15 | **B** | 历史 hotfix 证据输出,需裁决 |
| `F:\AIXM\wxgzh\outputs\hotfix6-stage7-20260729T144447` | 目录 | 470 | 1 | **B** | 历史 hotfix 证据输出,需裁决 |
| `F:\AIXM\wxgzh\outputs\hotfix6-stage7-run2` | 目录 | 11555963 | 42 | **B** | 历史 hotfix 证据输出,需裁决 |
| `F:\AIXM\wxgzh\outputs\hotfix6-stage8` | 目录 | 51281 | 10 | **B** | 历史 hotfix 证据输出,需裁决 |
| `F:\AIXM\wxgzh\outputs\hotfix6-stage8-3R` | 目录 | 369861 | 5 | **B** | 历史 hotfix 证据输出,需裁决 |
| `F:\AIXM\wxgzh\outputs\hotfix6-stage8-3S-dry-run.json` | 文件 | 3047 | 1 | **B** | 历史 hotfix 证据输出,需裁决 |
| `F:\AIXM\wxgzh\outputs\hotfix6-stage8-3S-dry-run.stderr` | 文件 | 0 | 1 | **B** | 历史 hotfix 证据输出,需裁决 |
| `F:\AIXM\wxgzh\outputs\hotfix6-stage8-3S-install.json` | 文件 | 3538 | 1 | **B** | 历史 hotfix 证据输出,需裁决 |
| `F:\AIXM\wxgzh\outputs\hotfix6-stage8-3S-install.stderr` | 文件 | 193 | 1 | **B** | 历史 hotfix 证据输出,需裁决 |
| `F:\AIXM\wxgzh\outputs\hotfix6-stage8-3S-post-failure-state.json` | 文件 | 873 | 1 | **B** | 历史 hotfix 证据输出,需裁决 |
| `F:\AIXM\wxgzh\outputs\hotfix6-stage8-3S-stop-report.md` | 文件 | 2019 | 1 | **B** | 历史 hotfix 证据输出,需裁决 |
| `F:\AIXM\wxgzh\outputs\hotfix6-stage8-3V-doctor-offline.json` | 文件 | 1726 | 1 | **B** | 历史 hotfix 证据输出,需裁决 |
| `F:\AIXM\wxgzh\outputs\hotfix6-stage8-3V-doctor-offline.stderr` | 文件 | 142 | 1 | **B** | 历史 hotfix 证据输出,需裁决 |
| `F:\AIXM\wxgzh\outputs\hotfix6-stage8-3V-stop-report.md` | 文件 | 3764 | 1 | **B** | 历史 hotfix 证据输出,需裁决 |
| `F:\AIXM\wxgzh\outputs\hotfix6-stage8-4S-doctor-live.json` | 文件 | 3698 | 1 | **B** | 历史 hotfix 证据输出,需裁决 |
| `F:\AIXM\wxgzh\outputs\hotfix6-stage8-4S-doctor-live.stderr` | 文件 | 0 | 1 | **B** | 历史 hotfix 证据输出,需裁决 |
| `F:\AIXM\wxgzh\outputs\hotfix6-stage8-4S-doctor-offline.json` | 文件 | 1726 | 1 | **B** | 历史 hotfix 证据输出,需裁决 |
| `F:\AIXM\wxgzh\outputs\hotfix6-stage8-4S-doctor-offline.stderr` | 文件 | 0 | 1 | **B** | 历史 hotfix 证据输出,需裁决 |
| `F:\AIXM\wxgzh\outputs\hotfix6-stage8-4S-doctor-require-wechat.json` | 文件 | 3699 | 1 | **B** | 历史 hotfix 证据输出,需裁决 |
| `F:\AIXM\wxgzh\outputs\hotfix6-stage8-4S-doctor-require-wechat.stderr` | 文件 | 0 | 1 | **B** | 历史 hotfix 证据输出,需裁决 |
| `F:\AIXM\wxgzh\outputs\hotfix6-stage8-4S5-evidence.json` | 文件 | 10124 | 1 | **B** | 历史 hotfix 证据输出,需裁决 |
| `F:\AIXM\wxgzh\outputs\hotfix6-stage8-4S5-stop-report.md` | 文件 | 5656 | 1 | **B** | 历史 hotfix 证据输出,需裁决 |
| `F:\AIXM\wxgzh\outputs\hotfix6-stage8-5-cold-run-first.json` | 文件 | 325 | 1 | **B** | 历史 hotfix 证据输出,需裁决 |
| `F:\AIXM\wxgzh\outputs\hotfix6-stage8-5-cold-run-first.stderr` | 文件 | 0 | 1 | **B** | 历史 hotfix 证据输出,需裁决 |
| `F:\AIXM\wxgzh\outputs\hotfix6-stage8-5R-doctor-require-wechat.json` | 文件 | 3698 | 1 | **B** | 历史 hotfix 证据输出,需裁决 |
| `F:\AIXM\wxgzh\outputs\hotfix6-stage8-5R-doctor-require-wechat.stderr` | 文件 | 0 | 1 | **B** | 历史 hotfix 证据输出,需裁决 |
| `F:\AIXM\wxgzh\outputs\hotfix6-stage8-5R-integration-first.json` | 文件 | 301 | 1 | **B** | 历史 hotfix 证据输出,需裁决 |
| `F:\AIXM\wxgzh\outputs\hotfix6-stage8-5R-integration-first.stderr` | 文件 | 0 | 1 | **B** | 历史 hotfix 证据输出,需裁决 |
| `F:\AIXM\wxgzh\outputs\hotfix6-stage8-5R-stop-report.md` | 文件 | 4830 | 1 | **B** | 历史 hotfix 证据输出,需裁决 |
| `F:\AIXM\wxgzh\outputs\hotfix6-stage8-backup-verification.json` | 文件 | 82 | 1 | **B** | 历史 hotfix 证据输出,需裁决 |
| `F:\AIXM\wxgzh\outputs\hotfix6-stage9-preflight-6-stop-report.md` | 文件 | 3611 | 1 | **B** | 历史 hotfix 证据输出,需裁决 |
| `F:\AIXM\wxgzh\outputs\hotfix6-stage9-preflight-6R-v2-report.md` | 文件 | 10763 | 1 | **B** | 历史 hotfix 证据输出,需裁决 |
| `F:\AIXM\wxgzh\outputs\hotfix6-stage9-preflight-7-report.md` | 文件 | 8020 | 1 | **B** | 历史 hotfix 证据输出,需裁决 |
| `F:\AIXM\wxgzh\outputs\hotfix7` | 目录 | 2919745 | 2 | **B** | 历史 hotfix 证据输出,需裁决 |
| `F:\AIXM\wxgzh\outputs\hotfix7-final` | 目录 | 3060933 | 4 | **B** | 历史 hotfix 证据输出,需裁决 |
| `F:\AIXM\wxgzh\outputs\hotfix7R` | 目录 | 2926867 | 3 | **B** | 历史 hotfix 证据输出,需裁决 |
| `F:\AIXM\wxgzh\outputs\hotfix7R2` | 目录 | 2929519 | 3 | **B** | 历史 hotfix 证据输出,需裁决 |
| `F:\AIXM\wxgzh\outputs\hotfix7R3` | 目录 | 2938618 | 4 | **B** | 历史 hotfix 证据输出,需裁决 |
| `F:\AIXM\wxgzh\outputs\hotfix7R4` | 目录 | 2950528 | 5 | **B** | 历史 hotfix 证据输出,需裁决 |
| `F:\AIXM\wxgzh\outputs\skills-hotfix6-inventory.json` | 文件 | 124550 | 1 | **B** | 历史 hotfix 证据输出,需裁决 |
| `F:\AIXM\wxgzh\mem-log\mem-2026-07-21.log` | 文件 | 21575 | 1 | **C** | 运行环境记忆日志,建议保留 |
| `F:\AIXM\wxgzh\mem-log\mem-2026-07-23.log` | 文件 | 171053 | 1 | **C** | 运行环境记忆日志,建议保留 |
| `F:\AIXM\wxgzh\mem-log\mem-2026-07-24.log` | 文件 | 159840 | 1 | **C** | 运行环境记忆日志,建议保留 |
| `F:\AIXM\wxgzh\mem-log\mem-2026-07-25.log` | 文件 | 204468 | 1 | **C** | 运行环境记忆日志,建议保留 |
| `F:\AIXM\wxgzh\mem-log\mem-2026-07-26.log` | 文件 | 67876 | 1 | **C** | 运行环境记忆日志,建议保留 |
| `F:\AIXM\wxgzh\mem-log\mem-2026-07-28.log` | 文件 | 101637 | 1 | **C** | 运行环境记忆日志,建议保留 |
| `F:\AIXM\wxgzh\mem-log\mem-2026-07-29.log` | 文件 | 242102 | 1 | **C** | 运行环境记忆日志,建议保留 |
| `F:\AIXM\wxgzh\mem-log\mem-2026-07-30.log` | 文件 | 57811 | 1 | **C** | 运行环境记忆日志,建议保留 |
| `F:\AIXM\wxgzh\mem-log\mem-2026-07-31.log` | 文件 | 76956 | 1 | **C** | 运行环境记忆日志,建议保留 |
| `F:\AIXM\wxgzh\mem-log\mem-2026-08-01.log` | 文件 | 8592 | 1 | **C** | 运行环境记忆日志,建议保留 |
| `F:\AIXM\wxgzh\skill-backups\pre-hotfix6-20260729T164448` | 目录 | 17837712 | 1058 | **B** | 历史备份,需裁决 |
| `F:\AIXM\wxgzh\skill-backups\pre-hotfix6-20260729T164448-COPY2` | 目录 | 17837712 | 1058 | **B** | 历史备份,需裁决 |
| `C:\Users\Admin\.agents\skills\aihot` | 目录 | 26253 | 7 | **C** | 强制保留:aihot 外部依赖 |
| `C:\Users\Admin\.agents\skills\brainstorming` | 目录 | 74839 | 8 | **C** | 当前环境注册的用户级 skill 库,删除破坏会话能力 |
| `C:\Users\Admin\.agents\skills\dispatching-parallel-agents` | 目录 | 6441 | 1 | **C** | 当前环境注册的用户级 skill 库,删除破坏会话能力 |
| `C:\Users\Admin\.agents\skills\docx` | 目录 | 1128695 | 61 | **C** | 当前环境注册的用户级 skill 库,删除破坏会话能力 |
| `C:\Users\Admin\.agents\skills\executing-plans` | 目录 | 2469 | 1 | **C** | 当前环境注册的用户级 skill 库,删除破坏会话能力 |
| `C:\Users\Admin\.agents\skills\finishing-a-development-branch` | 目录 | 7061 | 1 | **C** | 当前环境注册的用户级 skill 库,删除破坏会话能力 |
| `C:\Users\Admin\.agents\skills\guard` | 目录 | 3277 | 1 | **C** | 当前环境注册的用户级 skill 库,删除破坏会话能力 |
| `C:\Users\Admin\.agents\skills\impeccable` | 目录 | 811766 | 62 | **C** | 当前环境注册的用户级 skill 库,删除破坏会话能力 |
| `C:\Users\Admin\.agents\skills\make-pdf` | 目录 | 28645 | 1 | **C** | 当前环境注册的用户级 skill 库,删除破坏会话能力 |
| `C:\Users\Admin\.agents\skills\neat-freak` | 目录 | 16186 | 3 | **C** | 当前环境注册的用户级 skill 库,删除破坏会话能力 |
| `C:\Users\Admin\.agents\skills\pdf` | 目录 | 60529 | 12 | **C** | 当前环境注册的用户级 skill 库,删除破坏会话能力 |
| `C:\Users\Admin\.agents\skills\receiving-code-review` | 目录 | 6314 | 1 | **C** | 当前环境注册的用户级 skill 库,删除破坏会话能力 |
| `C:\Users\Admin\.agents\skills\requesting-code-review` | 目录 | 7610 | 2 | **C** | 当前环境注册的用户级 skill 库,删除破坏会话能力 |
| `C:\Users\Admin\.agents\skills\skill-creator` | 目录 | 224992 | 18 | **C** | 当前环境注册的用户级 skill 库,删除破坏会话能力 |
| `C:\Users\Admin\.agents\skills\storage-analyzer` | 目录 | 64828 | 7 | **C** | 当前环境注册的用户级 skill 库,删除破坏会话能力 |
| `C:\Users\Admin\.agents\skills\subagent-driven-development` | 目录 | 19883 | 4 | **C** | 当前环境注册的用户级 skill 库,删除破坏会话能力 |
| `C:\Users\Admin\.agents\skills\systematic-debugging` | 目录 | 40733 | 11 | **C** | 当前环境注册的用户级 skill 库,删除破坏会话能力 |
| `C:\Users\Admin\.agents\skills\test-driven-development` | 目录 | 18118 | 2 | **C** | 当前环境注册的用户级 skill 库,删除破坏会话能力 |
| `C:\Users\Admin\.agents\skills\ui-ux-pro-max` | 目录 | 1903111 | 57 | **C** | 当前环境注册的用户级 skill 库,删除破坏会话能力 |
| `C:\Users\Admin\.agents\skills\using-git-worktrees` | 目录 | 7983 | 1 | **C** | 当前环境注册的用户级 skill 库,删除破坏会话能力 |
| `C:\Users\Admin\.agents\skills\using-superpowers` | 目录 | 12678 | 4 | **C** | 当前环境注册的用户级 skill 库,删除破坏会话能力 |
| `C:\Users\Admin\.agents\skills\verification-before-completion` | 目录 | 4201 | 1 | **C** | 当前环境注册的用户级 skill 库,删除破坏会话能力 |
| `C:\Users\Admin\.agents\skills\writing-plans` | 目录 | 7814 | 2 | **C** | 当前环境注册的用户级 skill 库,删除破坏会话能力 |
| `C:\Users\Admin\.agents\skills\writing-skills` | 目录 | 103331 | 7 | **C** | 当前环境注册的用户级 skill 库,删除破坏会话能力 |
| `C:\Users\Admin\.agents\skills\xlsx` | 目录 | 1102893 | 53 | **C** | 当前环境注册的用户级 skill 库,删除破坏会话能力 |

## 汇总

- 条目总数:470;A(建议删):133 条;B(需裁决):296 条;C(必须保留):41 条
- A 合计:61920748 字节 / 15488 文件;B 合计:1158640354 字节 / 100617 文件;C 合计:75668832 字节 / 8757 文件
- 强制保留四项已全部归 C:`.env`、`aihot`、`.agents\skills`、`repos\wxgzh-pipeline`;它们不在删除候选内
- 待删候选仅限 A 类;删除授权待审核者逐条裁决后开放
