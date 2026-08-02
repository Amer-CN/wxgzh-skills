# 档 46 — 端到端复跑:停机于启动前(微信接口 IP 白名单阻塞)

- 报告编号:e2e-verify-46
- 执行日期:2026-08-02(Asia/Shanghai)
- 状态:**停机**。按「任一阶段失败即停机…不要自行重试」处理:本轮在启动前即确认微信接口不可达(两次独立复验均 40164 invalid ip),media_enrichment 上传与 wechat_draft 创建草稿均依赖微信 token,无法执行。未发起任何 RUN,未产生 RUN_ID,未创建/修改任何草稿,未调用 user_materials_override,未修改任何被锁 skill / lock / 台账,未删除任何文件。
- 工作副本:`F:\AIXM\wxgzh\repos\wxgzh-pipeline`(dev/0.1.0-dev2)

## 基线记录(第 1 项,已完成)

- 四锁 root:
  - super-writer `46a00a1bcdd5eeafae1ce6723241f97a6c1cd92f14f7baf8dc3625c9aed3018a`(50)
  - zh-human-writing `18491b361060a28d5eaf228f58b9b75e6ebde697eaa1149573bf468e0daea786`(53)
  - media-enrichment `0d8aea2169cec17c4e9f95af66b6b4da3c532554a0a316fe3fb604bd0b7ab3a3`(57)
  - gzh-design `f59d64bbb63309a7cdca2ae58081b49223731f86d1d866d058989d492816a6e4`(76)
- 两侧 skills.lock.json sha:均 `8fb33d83cdb128e15744023dde97a9bddadee1e962cee95f716c8dcefeb5a34d`
- 台账:2 条(`relock-gzh-design-20260802T131321Z-59d63817`、`relock-gzh-design-20260802T133343Z-843f9372`)
- 草稿箱 total_count:**无法查询**(微信 token 获取失败,见下)

## 阻塞证据(完整报错)

微信 token 获取(只读,`GET https://api.weixin.qq.com/cgi-bin/token`),两次独立复验:

```
attempt 1: errcode=40164 errmsg=invalid ip 183.221.4.191 ipv6 ::ffff:183.221.4.191, not in whitelist rid: 6a6f4d3b-6895a9a2-7511b6ba
attempt 2: errcode=40164 errmsg=invalid ip 183.221.4.191 ipv6 ::ffff:183.221.4.191, not in whitelist rid: 6a6f4d3d-5d0183f1-0c407fef
```

- 判定:errcode 40164 = invalid ip。凭据本身有效(appid/secret 被接受,错误指向 IP),当前出口 IP `183.221.4.191` 不在该公众号的 IP 白名单中。
- 影响面(确定,非推测):
  - media_enrichment 的 uploadimg(微信图床上传)依赖 token → 必失败;
  - wechat_draft 创建草稿依赖 token → 必失败;
  - 基线草稿箱 total_count 与副作用的只读对账同样依赖 token → 无法完成。
- 这是外部环境配置问题,不在 Pipeline 代码/授权范围内;不自行重试(已复验两次)、不绕过、不修改公众号配置。

## 未执行项

- 第 2-9 项(选题抓取、六阶段、观察项、媒体批准、validate_draft_delta、跑后复核、副作用总账)全部未执行——启动条件不满足,执行任何阶段都必然在微信侧失败。
- 未产生 RUN_ID,故 `audit/runs/<RUN_ID>/` 不存在;本报告落在 `audit/quality/e2e-verify-46.md`。

## 恢复条件(需外部动作)

1. 在微信公众平台「设置与开发 → 基本配置 → IP 白名单」加入当前出口 IP `183.221.4.191`(或将该环境接入白名单内网络/固定出口),然后重新授权本档复跑;
2. 或提供白名单内可用的网络路径后再执行。

## 环境状态(停机时)

- 四锁 root、两侧 lock sha、台账与基线一致(上述记录);未产生任何新副作用;证据/暂存目录未触碰。
- 快照 `F:\AIXM\wxgzh-presnapshot-45\` 未动用。
