# OBS-47 Credential Source Diagnosis

## 0节自检
- 正式版本：`0.1.0-dev2-hotfix7R4`。
- 档16冻结字节补丁存在；档17观测字段与显式批准数量硬上限存在。
- 未安装、未解压、未搜索ZIP、未触碰历史物证。

## A-1 doctor来源
`wxgzh_pipeline/orchestrator.py:110-115`复制进程环境，再从`project_root/.env`经`SEC.parse_env_file()`按`setdefault`补充；`wxgzh_pipeline/secrets.py:52-60`检查APP_ID/SECRET非空且非占位。

## A-2 uploader来源
`media-enrichment/src/media_enrichment/uploader.py:191-193`读取`os.environ`；`_get_access_token()`使用实例中的appid/secret。

## A-3差异与根因
修复前不同：doctor验证进程环境+项目`.env`，而`producers.py:758-776`调用media子进程未传doctor合并后的env，上传器只看继承环境。修复后`_media_subprocess_env()`复用doctor规则并显式传入media discover/continue子进程；doctor未反向修改。

## A-4凭据状态
`F:/AIXM/wxgzh/.env`存在：APP_ID存在、长度18；SECRET存在、长度32。未记录明文、前缀或后缀。

## A-5/A-6
A-5不触发。A-6根因是doctor局部合并字典未传递给子进程。

## Token缓存
Uploader实例内存缓存首次成功token，单RUN复用；不落盘、不进入事件/报告/日志。

## 网络
.NET：`120.233.18.202,120.232.65.161,112.53.42.235,112.60.20.154`；Python：`120.233.18.202`；无fake-IP。当前出口`185.217.5.28`，档17为`212.135.214.6`。
