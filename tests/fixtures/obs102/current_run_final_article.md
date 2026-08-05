# 护栏从「自觉」到「硬拦」:vibe-coding-guide v2.1 的数字与代码

给 AI 编程立规矩,最难的不是写出规矩,而是让规矩真的生效。vibe-coding-guide 在 2026 年 8 月 1 日发布的 2.1.0 版本里,把铁律从四条扩到五条,并给 README 加上了「装完后,花一分钟确认护栏真的生效了」的验证步骤。这篇文章用三组数字、十六行拦截文案和两行安装命令,把这套护栏的演进、机制与边界讲清楚。先看数字,它们说明规矩在怎么长。

## 一、三组数字:规矩是怎么长出来的

把 CHANGELOG 的版本记录排开,能看到三条清晰的数字线,它们就是这套规矩生长速度的刻度。

第一组是红线。v1.2.0 把红线从 8 条扩到 11 条,新增「AI 功能」「依赖供应链」「AI 代理操作安全」三组;同一版里,自检清单从 19 条扩到 25 条,并标出 8 条最小必查项。红线管边界,清单管交付,数字越大,规矩覆盖的面越宽。同一版还补上了 assets 模板三件套(AGENTS.template.md、gitignore.template、delivery-report.template.md),把新项目的起步动作也标准化了。

第二组是铁律。v2.1.0 把铁律从四条扩到五条,新增的两条分别禁止「改测试来迁就实现」和「闷头执行矛盾指令」:前一条堵死了测试红着时最省事的捷径——AI 的第一反应往往是改测试让它变绿,而不是改实现让它真正通过;后一条要求指令与红线冲突时停下来问用户,因为继续执行任何一个都是错的。CHANGELOG 注明这两条是行为约束的扩充、非破坏性变更,所以升的是次版本号而不是主版本号。

再往后,2.0.0 做了一件定位上的大事:在仓库里加入 hooks 目录,基于 PreToolUse 钩子做强制护栏,红线从「只靠自觉」变为「部分由 hooks 强制」,所以升了主版本号;v2.1.0 则回到行为约束本身。第三组是验证。v2.1.0 给 README 双语加了「花一分钟确认护栏真的生效了」的步骤,把「安装」和「生效」拆开;同时给 SKILL.md 的 description 末尾追加英文触发句——description 是 AI 客户端判断要不要加载这个技能的唯一依据,纯中文会让英文提问几乎不触发。

三组数字(8→11、19→25、四→五)构成了文章配图的数据点:红线数量对比、清单条数对比、铁律条数对比。

## 二、十六行拦截文案:护栏到底在拦什么

hooks 目录下的两个脚本是护栏的实际执行者。hooks/_common.sh 是共用层,设计原则只有一条:任何自身故障都必须 fail-open,即放行,绝不阻断用户;hooks/guard-bash.sh 负责拦截危险 Bash 命令。全部十六行拦截文案如下,逐字来自脚本原文:

```bash
⛔ vibe-coding-guide 拦截：这是对根目录或家目录的递归删除，会清空整台机器（铁律 1）。确需执行请你自己在终端手动运行。关闭护栏：/plugin disable vibe-coding-guide
⛔ vibe-coding-guide 拦截：这是对系统目录的递归删除，会让系统无法启动（铁律 1）。确需执行请你自己在终端手动运行。关闭护栏：/plugin disable vibe-coding-guide
⛔ vibe-coding-guide 拦截：这会删掉整个当前目录，包括你还没提交的代码（铁律 1）。确需执行请你自己在终端手动运行。关闭护栏：/plugin disable vibe-coding-guide
⛔ vibe-coding-guide 拦截：强推主分支会永久覆盖远端历史，别人的提交会消失（红线 11）。确需执行请你自己在终端手动运行。关闭护栏：/plugin disable vibe-coding-guide
⛔ vibe-coding-guide 拦截：这会删除整个数据库，且通常无法恢复（红线 6）。确需执行请你自己在终端手动运行。关闭护栏：/plugin disable vibe-coding-guide
⛔ vibe-coding-guide 拦截：这是把网上下载的内容直接执行，你没机会看清它要做什么（红线 10）。确需执行请你自己在终端手动运行。关闭护栏：/plugin disable vibe-coding-guide
⛔ vibe-coding-guide 拦截：递归 777 会把文件权限对所有人开放（红线 7）。确需执行请你自己在终端手动运行。关闭护栏：/plugin disable vibe-coding-guide
⛔ vibe-coding-guide 拦截：这是直接格式化或写裸设备，会造成不可恢复的数据丢失（铁律 1）。确需执行请你自己在终端手动运行。关闭护栏：/plugin disable vibe-coding-guide
⚠️ vibe-coding-guide 提醒：要安装新依赖了。装之前请先确认包名全称、用途、周下载量和最近更新时间（红线 10）。确认要继续吗？关闭护栏：/plugin disable vibe-coding-guide
⚠️ vibe-coding-guide 提醒：这会丢弃你本地还没提交的改动，丢了找不回来（铁律 1）。确认要继续吗？关闭护栏：/plugin disable vibe-coding-guide
⚠️ vibe-coding-guide 提醒：这是在改数据库结构。请先出迁移文件再执行，不要直接改库（红线 6）。确认要继续吗？关闭护栏：/plugin disable vibe-coding-guide
⚠️ vibe-coding-guide 提醒：这条 DELETE 没有 WHERE 条件，会清空整张表（红线 6）。确认要继续吗？关闭护栏：/plugin disable vibe-coding-guide
⚠️ vibe-coding-guide 提醒：强推会覆盖远端历史。确认这个分支只有你一个人在用（红线 11）。确认要继续吗？关闭护栏：/plugin disable vibe-coding-guide
⚠️ vibe-coding-guide 提醒：要递归删除文件了。确认路径没写错、且这些文件已经提交过（铁律 1）。确认要继续吗？关闭护栏：/plugin disable vibe-coding-guide
⚠️ vibe-coding-guide 提醒：你正在把 .env 加进 Git。密钥一旦提交，删掉也留在历史里（红线 7）。确认要继续吗？关闭护栏：/plugin disable vibe-coding-guide
⚠️ vibe-coding-guide 提醒：这是往线上环境部署。确认已经在本地验证过（红线 11）。确认要继续吗？关闭护栏：/plugin disable vibe-coding-guide
```

每条 deny 文案都标明铁律或红线编号,并且提供关闭方法(/plugin disable vibe-coding-guide)。

## 三、安装与边界:两行命令和一个不承诺

install.sh 把安装边界写得很清楚:先检查 git 是否可用,不可用就退出并提示先装 git;然后创建 ~/.claude/skills 目录,把仓库克隆到 ~/.claude/skills/vibe-coding-guide;如果已经装过,就用 git pull --ff-only 更新到最新版本。安装完成后,脚本会明确输出:这种装法安装的是「规矩本」部分,并提示在新对话里说一句「我要用 vibe-coding-guide 规范来写代码」来启用。整个安装刻意保持简单:一个文件、一条命令、一个目标目录,不要求用户理解仓库结构。

在 Claude Code 里启用这套规矩,需要两行命令:

```text
/plugin marketplace add Amer-CN/vibe-coding-guide
/plugin install vibe-coding-guide@vibe-coding-guide
```

install.sh 同时明确区分「规矩本安装」与「完整安装」,并声明:护栏是否随 skills 目录安装生效,未经实测,不做承诺。这句话几乎反直觉——一个做了强制护栏的项目,却在安装脚本里主动说「可能不生效」。但恰恰是它让项目可信:护栏最大的风险不是拦不住,而是用户以为拦住了。如果 README 只写「安装即生效」,用户就会把信任建立在一个未经验证的假设上;配合 README 的「花一分钟确认生效」步骤,验证的责任被明确交回给用户:规矩本装上就能用,护栏是否生效,装完花一分钟自己验证。同一个逻辑也出现在 checklist 里——2.1.0 给 references/checklist.md 第 15 条补充了要求:新加的每一条校验或拦截规则,是否本身也有一条测试覆盖。

## 四、机制加边界,才是可信的护栏

三条数字线说明规矩在长,十六行文案说明机制在拦,一个不承诺说明边界在明。把 2.1.0 的改动放一起看,主线不是「加了更多拦截」,而是「把生效与否变得可验证」。

铁律第五条「停下来问用户」,把冲突场景从「猜一个对的」变成「承认没有对的那个」;README 的验证步骤,把「装完」和「生效」分开;install.sh 的不承诺,把「应该生效」和「实测生效」分开。四条线指向同一个结论:护栏的可信度,不来自拦截规则的多少,而来自每一处边界都被明确标注、每一条承诺都可以被验证。这也是 v2.1 与之前版本最不一样的地方——它没有新增任何一条硬拦规则,却让整套机制变得更可信。

对 AI 编程护栏来说,规则可以被绕过,承诺不会——一旦边界被公开声明,用户就知道该在哪里验证。这正是 hooks 的 fail-open 设计与 install.sh 的不承诺声明放在一起的原因:机制保证「不误伤」,声明保证「不欺骗」。

要给 Claude Code 装这套护栏的话,install.sh 装完之后,记得照 README 的步骤花一分钟确认它真的生效。