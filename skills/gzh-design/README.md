# gzh-design Skill

> 个人备份与自用增强版 — 保留原作者署名

## 功能简介

- **6 个公众号主题**：摸鱼绿、红白色系、石墨极简风、留白禅意风、摸鱼票据风、橄榄手记
- **19 个高级组件**：alert、quote、code-compare、media-text、gallery、long-image、resources、footnotes、dialogue、facts、decision、steps、compare、annotated-image、faq、timeline、checklist、case、cta
- **微信/QQ 左右 Dialogue**：自动识别对话角色，头像在左/在右正确布局
- **Markdown / Word(.docx) / PDF / 纯文本排版**：非 Markdown 输入先自动归一化
- **自定义主题生成**：根据用户描述/参考图生成新主题组件库
- **微信公众号草稿箱创建**：简单直接的发布脚本，不含复杂抽象层

## 安装方法

### macOS / Linux

```bash
git clone https://github.com/Amer-CN/gzh-design-skill.git ~/.reasonix/skills/gzh-design

cd ~/.reasonix/skills/gzh-design

python -m pip install -r requirements.txt
```

### Windows

```bash
git clone https://github.com/Amer-CN/gzh-design-skill.git f:/AIXM/wxgzh/.reasonix/skills/gzh-design

cd f:/AIXM/wxgzh/.reasonix/skills/gzh-design

python -m pip install -r requirements.txt
```

## 更新方法

```bash
cd ~/.reasonix/skills/gzh-design    # 或 Windows 对应路径

git pull origin main
```

## 微信凭证配置

**只使用环境变量，不要把凭证写入任何文件。**

### Windows PowerShell

```powershell
$env:WECHAT_APP_ID="你的公众号AppID"
$env:WECHAT_APP_SECRET="你的公众号AppSecret"
```

### macOS / Linux

```bash
export WECHAT_APP_ID="你的公众号AppID"
export WECHAT_APP_SECRET="你的公众号AppSecret"
```

## 创建草稿示例

```bash
python scripts/publish_wechat_draft.py \
  --html article.wechat.html \
  --title "文章标题" \
  --thumb-media-id "封面素材ID"
```

或上传本地封面图片：

```bash
python scripts/publish_wechat_draft.py \
  --html article.wechat.html \
  --title "文章标题" \
  --cover cover.jpg
```

成功后返回 `media_id`，到微信公众号后台草稿箱检查。

## 备份恢复说明

如果本地 Skill 误删，可以：

### 方式一：git clone

```bash
git clone https://github.com/Amer-CN/gzh-design-skill.git ~/.reasonix/skills/gzh-design
```

### 方式二：从 Release 下载 ZIP

从 [GitHub Release](https://github.com/Amer-CN/gzh-design-skill/releases) 下载 `gzh-design-simplified-final-v2.zip`，解压到 skills 目录即可。

## 许可证

详见 [LICENSE](LICENSE)。

原作者：甲木 (Jiamu) × 摸鱼小李 (Moyu Xiaoli)

本仓库为个人备份与自用增强版，保持 Private。
