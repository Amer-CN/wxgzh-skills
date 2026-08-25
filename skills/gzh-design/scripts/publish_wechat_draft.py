#!/usr/bin/env python3
"""微信公众号草稿创建脚本

用法:
    python scripts/publish_wechat_draft.py \
        --html article.wechat.html \
        --title "文章标题" \
        --thumb-media-id <封面素材ID>

    或:

    python scripts/publish_wechat_draft.py \
        --html article.wechat.html \
        --title "文章标题" \
        --cover cover.jpg

环境变量:
    WECHAT_APP_ID     — 公众号 AppID
    WECHAT_APP_SECRET — 公众号 AppSecret

功能:
    1. 读取明确传入的 HTML 文件
    2. 发布前安全校验（调用 validate_gzh_html.validate 做完整校验 +
       E_NOT_HTML / E_NO_CJK_TEXT / E_NOT_RENDERED_HTML / E_RAW_MARKDOWN /
       字面量 \\uXXXX 检测）
    3. 输出安全摘要（路径、SHA-256、CJK count、异常计数）
    4. 获取 access_token  —— 必须在预检全部通过后才执行
    5. 如有 --cover 则上传封面获取 thumb_media_id
    6. 调用微信 draft/add 创建草稿
    7. 返回草稿 media_id

安全:
    - HTML 文件必须明确传入且存在
    - 禁止搜索 latest、日期目录、scratch
    - APPSECRET 和 access_token 不打印、不写文件
    - 微信 API 返回错误时立即停止
    - draft/add 不自动重试
    - 默认只创建草稿，不正式发布和群发
    - 校验失败时不得获取 token，不得调用 draft/add
    - 本次真实发布要求 ERROR=0 且 WARNING=0
"""
import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

# WeChat image hosts (exact-match gate; dev2-hotfix2)
WECHAT_IMAGE_HOSTS = ("mmbiz.qpic.cn", "mmbiz.qlogo.cn")

# 76L/OBS-282:交付凭证门——本脚本只能由管线 wechat_draft 阶段调用。
# 主题签名 = hammer 主题 primary 色值(渲染产物必有;缺失即非管线渲染产物)。
THEME_SIGNATURE = "#B3593B"


def normalize_wechat_image_url(url):
    """Upgrade http->https and require the hostname to EQUAL a WeChat image
    host (urlparse; query/subdomain/path/userinfo tricks rejected). Returns the
    normalized https URL or None."""
    if not url:
        return None
    if url.startswith("http://"):
        url = "https://" + url[len("http://"):]
    try:
        p = urlparse(url)
    except ValueError:
        return None
    if p.scheme != "https" or p.hostname not in WECHAT_IMAGE_HOSTS:
        return None
    return url

# 确保 Windows 控制台 UTF-8 输出，避免 emoji/中文 print 崩溃
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# 从项目根目录 .env 加载环境变量（不影响已设置的真实环境变量）
# 向上查找 .env，最多 5 级
_env_path = None
_search_dir = os.path.dirname(os.path.abspath(__file__))
for _ in range(5):
    _candidate = os.path.join(_search_dir, ".env")
    if os.path.isfile(_candidate):
        _env_path = _candidate
        break
    _parent = os.path.dirname(_search_dir)
    if _parent == _search_dir:
        break
    _search_dir = _parent
if _env_path and os.path.isfile(_env_path):
    with open(_env_path, encoding="utf-8") as _f:
        for _line in _f:
            _line = _line.strip()
            if not _line or _line.startswith("#") or "=" not in _line:
                continue
            _k, _v = _line.split("=", 1)
            _k = _k.strip()
            _v = _v.strip().strip('"').strip("'")
            if _k and not os.environ.get(_k):
                os.environ[_k] = _v

try:
    import requests
except ImportError:
    print("错误: 需要安装 requests 库: pip install requests")
    sys.exit(1)

# 与 validate_gzh_html.py 共享同一套检测逻辑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from validate_gzh_html import (validate, validate_graded, find_cn_quoted_attrs,
                               WARN_ALLOWABLE, WARN_BLOCKING)
from datetime import datetime, timezone

# 微信 API 端点
TOKEN_URL = "https://api.weixin.qq.com/cgi-bin/token"
ADD_DRAFT_URL = "https://api.weixin.qq.com/cgi-bin/draft/add"
BATCHGET_DRAFT_URL = "https://api.weixin.qq.com/cgi-bin/draft/batchget"
GET_DRAFT_URL = "https://api.weixin.qq.com/cgi-bin/draft/get"
UPLOAD_MATERIAL_URL = "https://api.weixin.qq.com/cgi-bin/material/add_material"
UPLOADIMG_URL = "https://api.weixin.qq.com/cgi-bin/media/uploadimg"

# 字面量 \uXXXX 检测（独立于 validator，发布层专用阻断）
LITERAL_UNICODE = re.compile(r'\\u[0-9a-fA-F]{4}')
CJK_RE = re.compile(r'[一-鿿㐀-䶿]')
# 渲染后 HTML 必须出现这些标签之一
RENDERED_TAG_RE = re.compile(r"<(?:section|p|span|img|h[1-6])\b", re.I)
# 原始 Markdown 标题检测（行首 1-6 个 # 后跟空格和文本）
RAW_MARKDOWN_RE = re.compile(r"(?m)^\s{0,3}#{1,6}\s+\S+")

# 内部片段链接检测（发布层专用阻断）
# 微信 draft/add 不接受 href="#..."，会返回 errcode 45166 invalid content
FRAGMENT_HREF_RE = re.compile(r'''href\s*=\s*["']\s*#''', re.I)


def api_error(msg, data=None):
    """简洁错误输出，不输出 Python traceback"""
    if data and isinstance(data, dict):
        errcode = data.get("errcode", "?")
        errmsg = data.get("errmsg", "unknown")
        print(f"错误: {msg} [{errcode}] {errmsg}")
    else:
        print(f"错误: {msg}")
    sys.exit(1)


def get_access_token(app_id, app_secret):
    """获取 access_token"""
    try:
        resp = requests.get(TOKEN_URL, params={
            "grant_type": "client_credential",
            "appid": app_id,
            "secret": app_secret,
        }, timeout=10)
        data = resp.json()
    except requests.exceptions.RequestException as e:
        api_error(f"网络请求失败: {e}")
    except ValueError:
        api_error("微信返回非 JSON 响应", {"errcode": -1, "errmsg": "non-JSON response"})
    if "access_token" not in data:
        api_error("获取 access_token 失败", data)
    return data["access_token"]


def upload_cover(access_token, cover_path):
    """上传封面图片（永久素材），返回 thumb_media_id"""
    try:
        with open(cover_path, "rb") as f:
            resp = requests.post(
                UPLOAD_MATERIAL_URL,
                params={"access_token": access_token, "type": "image"},
                files={"media": f},
                timeout=30,
            )
        data = resp.json()
    except requests.exceptions.RequestException as e:
        api_error(f"上传封面网络请求失败: {e}")
    except ValueError:
        api_error("微信返回非 JSON 响应", {"errcode": -1, "errmsg": "non-JSON response"})
    if "media_id" not in data:
        api_error("上传封面失败", data)
    return data["media_id"]


def _find_cjk_font(bold: bool = False):
    """Pick a CJK-capable font for placeholder covers."""
    candidates = (
        [r"C:\Windows\Fonts\msyhbd.ttc", r"C:\Windows\Fonts\msyh.ttc",
         r"C:\Windows\Fonts\simhei.ttf"] if bold else
        [r"C:\Windows\Fonts\msyh.ttc", r"C:\Windows\Fonts\msyhbd.ttc",
         r"C:\Windows\Fonts\simhei.ttf"]
    )
    if os.name != "nt":
        candidates = [
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
            "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
        ]
    for path in candidates:
        if os.path.isfile(path):
            try:
                from PIL import ImageFont
                return ImageFont.truetype(path, 44)
            except Exception:
                continue
    try:
        from PIL import ImageFont
        return ImageFont.load_default()
    except Exception:
        return None


def generate_placeholder_cover(title, out_dir, brand=None, size=(900, 383)):
    """77H/OBS-318: zero-image placeholder cover in hammer visual language."""
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        return None
    width, height = size
    bg = (250, 249, 245)
    brick = (179, 89, 59)
    title_color = (85, 85, 85)
    sub_color = (115, 115, 115)
    img = Image.new("RGB", (width, height), bg)
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, max(8, width // 64), height], fill=brick)
    big_font = _find_cjk_font(bold=True)
    small_font = _find_cjk_font(bold=False)
    if big_font is None or small_font is None:
        return None
    text = (title or "未命名文章").strip()[:52]
    line1, line2 = text[:26], text[26:] or ""
    draw.text((max(32, width // 24), int(height * 0.34)), line1,
              fill=title_color, font=big_font)
    if line2:
        draw.text((max(32, width // 24), int(height * 0.54)), line2,
                  fill=brick, font=big_font)
    footer = (brand or "给自己造把锤子").strip()[:40]
    draw.text((max(32, width // 24), int(height * 0.84)), footer,
              fill=sub_color, font=small_font)
    out = Path(out_dir) / "placeholder_cover.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, "PNG")
    return out


def upload_content_image(access_token, image_path):
    """上传正文图片到 media/uploadimg，返回微信 CDN HTTPS URL。

    微信 uploadimg 返回的 URL 通常是 http://mmbiz.qpic.cn/...，
    mmbiz.qpic.cn 支持 HTTPS，这里自动升级为 https://。
    同一张图片只需上传一次，返回的 URL 可在 HTML 中复用。
    """
    try:
        with open(image_path, "rb") as f:
            resp = requests.post(
                UPLOADIMG_URL,
                params={"access_token": access_token},
                files={"media": (os.path.basename(image_path), f, "image/png")},
                timeout=60,
            )
        data = resp.json()
    except requests.exceptions.RequestException as e:
        api_error(f"上传正文图片网络请求失败: {e}")
    except ValueError:
        api_error("微信返回非 JSON 响应", {"errcode": -1, "errmsg": "non-JSON response"})
    if "url" not in data:
        api_error("上传正文图片失败", data)
    # dev2-hotfix2: uploadimg 必须返回真正的微信图床 URL（精确 host），否则阻断
    url = normalize_wechat_image_url(data["url"])
    if url is None:
        api_error("上传正文图片返回非微信图床 URL，已阻断",
                  {"errcode": -1, "errmsg": "non-WeChat-host url"})
    return url


def get_draft(access_token, media_id):
    """获取草稿内容（draft/get）。

    关键修复：必须使用 resp.content.decode("utf-8") + json.loads，
    而非 resp.json()。微信 draft/get 返回的 Content-Type 通常是
    text/plain（无 charset），requests 默认用 ISO-8859-1 解码，
    导致中文和 Emoji 产生 mojibake。
    """
    try:
        resp = requests.get(
            GET_DRAFT_URL,
            params={"access_token": access_token, "media_id": media_id},
            timeout=30,
        )
    except requests.exceptions.RequestException as e:
        api_error(f"获取草稿网络请求失败: {e}")
    # 必须显式 UTF-8 解码，不能用 resp.json()
    try:
        data = json.loads(resp.content.decode("utf-8"))
    except (ValueError, UnicodeDecodeError) as e:
        api_error(f"获取草稿响应解码失败: {e}", {"errcode": -1, "errmsg": "decode error"})
    if "news_item" not in data:
        api_error("获取草稿失败", data)
    return data


def create_draft(access_token, title, html_content, thumb_media_id):
    """创建微信公众号草稿

    关键修复：使用 ensure_ascii=False 序列化 JSON，确保中文和 Emoji
    以 UTF-8 直接传递，不转为 \\uXXXX 转义。微信 draft/add API 不会
    正确解码 JSON Unicode 转义（\\uXXXX），会直接保存为字面量。
    """
    article = {
        "title": title,
        "content": html_content,
        "thumb_media_id": thumb_media_id,
        "need_open_comment": 0,
        "only_fans_can_comment": 0,
    }
    payload = {"articles": [article]}

    # ---- 最终发送对象门禁（在 requests.post 前一行执行）----
    outgoing_content = payload["articles"][0]["content"]
    outgoing_title = payload["articles"][0]["title"]

    # 1. 检查 outgoing content 中不得有字面量 \uXXXX
    if LITERAL_UNICODE.search(outgoing_content):
        raise SystemExit("E_OUTGOING_LITERAL_UNICODE: outgoing content 包含字面量 \\uXXXX")
    if LITERAL_UNICODE.search(outgoing_title):
        raise SystemExit("E_OUTGOING_LITERAL_UNICODE: outgoing title 包含字面量 \\uXXXX")

    # 2. 检查 outgoing content 必须含 CJK
    if not CJK_RE.search(outgoing_content):
        raise SystemExit("E_OUTGOING_NO_CJK: outgoing content 不含中文字符")

    # 3. 检查 outgoing content 必须是 HTML
    if "<section" not in outgoing_content:
        raise SystemExit("E_OUTGOING_NOT_HTML: outgoing content 不是 HTML")
    if '<span' not in outgoing_content or 'leaf=""' not in outgoing_content:
        raise SystemExit("E_OUTGOING_NO_LEAF: outgoing content 不含 span leaf")

    # 4. 检查 outgoing content 不得含原始 Markdown **...**
    if re.search(r'\*\*[^*]+\*\*', outgoing_content):
        raise SystemExit("E_OUTGOING_RAW_MARKDOWN: outgoing content 包含原始 Markdown **...**")

    # 5. 检查 input SHA-256 == outgoing SHA-256（防止读取后被篡改）
    # 注意：html_content 是 Python 字符串，SHA-256 基于 encode("utf-8")
    # 只要 html_content 没有被修改，两者必然一致
    # （CRLF -> LF 的转换发生在 open() 读取阶段，不影响这里的比较）

    # 6. JSON 单次往返验证（确保序列化/反序列化后 content 不变）
    # 使用 ensure_ascii=False 序列化，确保中文不被转义
    json_str = json.dumps(payload, ensure_ascii=False)
    roundtrip = json.loads(json_str)
    roundtrip_content = roundtrip["articles"][0]["content"]

    if roundtrip_content != outgoing_content:
        raise SystemExit("E_CONTENT_MUTATED_AFTER_PREFLIGHT: JSON 往返后 content 不一致")

    # 再次检查往返后的 content
    if LITERAL_UNICODE.search(roundtrip_content):
        raise SystemExit("E_ROUNDTRIP_LITERAL_UNICODE: JSON 往返后出现字面量 \\uXXXX")
    if not CJK_RE.search(roundtrip_content):
        raise SystemExit("E_ROUNDTRIP_NO_CJK: JSON 往返后丢失中文字符")
    if '**' in roundtrip_content and re.search(r'\*\*[^*]+\*\*', roundtrip_content):
        raise SystemExit("E_ROUNDTRIP_RAW_MARKDOWN: JSON 往返后出现原始 Markdown")

    print("  outgoing 门禁通过 ✅（无字面量 \\uXXXX、含 CJK、HTML 完整、JSON 往返一致）")

    # ---- 发送请求（使用 data= + ensure_ascii=False，不用 json=）----
    try:
        resp = requests.post(
            ADD_DRAFT_URL,
            params={"access_token": access_token},
            data=json_str.encode("utf-8"),
            headers={"Content-Type": "application/json; charset=utf-8"},
            timeout=30,
        )
        data = resp.json()
    except requests.exceptions.RequestException as e:
        api_error(f"创建草稿网络请求失败: {e}")
    except ValueError:
        api_error("微信返回非 JSON 响应", {"errcode": -1, "errmsg": "non-JSON response"})
    if "media_id" not in data:
        api_error("创建草稿失败", data)
    return data["media_id"]


def preflight_html(html_content, html_path, raw_file_sha256="", audit_dir=None,
                   allow_warnings=False):
    """发布前安全校验 HTML 内容(档54R:WARN 分级 + 显式放行)。

    必须在 get_access_token 之前完成。ERROR 一律阻断;WARN 按类别:
    WARN_ALLOWABLE(半角标点/英文引号)仅当 allow_warnings=True 且逐条留痕时放行;
    WARN_BLOCKING(span leaf 未包裹)与解析中断(已升 ERROR)任何情况不可放行。
    任何未放行的不达标都 sys.exit(1)，绝不进入网络请求阶段。

    参数:
        html_content: open(encoding="utf-8") 读取后的字符串（已 CRLF→LF）
        html_path: HTML 文件路径
        raw_file_sha256: 文件 raw bytes 的 SHA-256（由 main() 计算），
                        与 normalized_content_sha256 分开记录。
        audit_dir: 审计目录;放行时写入 allowance_record.json(可追溯)
        allow_warnings: 显式放行开关,默认关闭;仅对 WARN_ALLOWABLE 类别生效
    """
    errors = []
    warnings = []

    # SHA-256（分开记录 raw_file_sha256 和 normalized_content_sha256）
    # normalized_content_sha256: 基于 open(encoding="utf-8") 读取后的字符串（CRLF→LF）
    # raw_file_sha256: 基于文件 raw bytes（可能含 CRLF），由 main() 传入
    normalized_content_sha256 = hashlib.sha256(html_content.encode("utf-8")).hexdigest()
    sha256 = normalized_content_sha256  # 向后兼容别名

    # CJK count
    cjk_count = len(CJK_RE.findall(html_content))

    # ---- 发布层专属检查 ----

    # E_NOT_HTML: 文件必须是 .html 后缀（防止把 .md 改名后直接发布）
    if not html_path.lower().endswith(".html"):
        errors.append("E_NOT_HTML: 文件必须是 .html 后缀")

    # E_NO_CJK_TEXT: 不含中文字符（可能读错文件）
    if cjk_count == 0:
        errors.append("E_NO_CJK_TEXT: HTML 不包含中文字符，可能读错文件")

    # E_NOT_RENDERED_HTML: 必须出现渲染后的 HTML 标签
    if not RENDERED_TAG_RE.search(html_content):
        errors.append("E_NOT_RENDERED_HTML: 未检测到渲染后的 HTML 标签 "
                      "(section/p/span/img/h1-6)，可能是纯文本")

    # E_RAW_MARKDOWN: 检测原始 Markdown 标题（未渲染）
    if RAW_MARKDOWN_RE.search(html_content):
        errors.append("E_RAW_MARKDOWN: 检测到原始 Markdown 标题，未渲染为 HTML")

    # 字面量 \uXXXX 检查（发布层阻断，防止双重编码）
    unicode_hits = len(LITERAL_UNICODE.findall(html_content))
    if unicode_hits > 0:
        errors.append(f"E_LITERAL_UNICODE: 字面量 \\uXXXX 残留 {unicode_hits} 处")

    # 内部片段链接检查（发布层阻断，防止微信 45166）
    fragment_href_hits = len(FRAGMENT_HREF_RE.findall(html_content))
    if fragment_href_hits > 0:
        errors.append(
            f"E_FRAGMENT_HREF: 内部片段链接 href=\"#...\" 会触发微信 45166 "
            f"invalid content（命中 {fragment_href_hits} 处）；"
            f"请移除 href 属性，保留可见文字。应由 renderer 从源头生成正确 HTML。")

    # ---- 调用完整 HTML 校验器 ----
    # validate() 检查：禁用标签/属性/样式、全属性中文引号、占位符、编辑锚点、
    # span leaf 包裹、半角标点等。返回 (errors, warnings, leaf_count)。
    # 档54R:validate_graded 返回结构化 WARN(类别标记);解析中断已升 ERROR。
    v_errors, v_warnings, leaf_count, graded = validate_graded(html_content, html_path)
    errors.extend(v_errors)
    blocking = [g for g in graded if g.get("category") == WARN_BLOCKING]
    allowable = [g for g in graded if g.get("category") == WARN_ALLOWABLE]
    # 不可放行类别(② span leaf 未包裹)一律阻断
    warnings.extend(g["text"] for g in blocking)
    # 可放行类别(① 半角标点/英文引号):仅当显式开关开启时放行,否则阻断
    allowed_records = []
    if allowable and not allow_warnings:
        warnings.extend(g["text"] for g in allowable)
    elif allowable:
        allowed_records = [{"rule": g["rule"], "category": g["category"],
                           "text": g["text"], "snippets": g.get("snippets") or []}
                          for g in allowable]
        for g in allowable:
            print(f"  → 放行 WARNING（{g['rule']}）: {g['text']}")
        if audit_dir:
            audit_dir = Path(audit_dir)
            audit_dir.mkdir(parents=True, exist_ok=True)
            record = {"schema_version": "1.0", "allow_warnings": True,
                      "allowed_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                      "html_sha256": normalized_content_sha256,
                      "entries": allowed_records}
            (audit_dir / "allowance_record.json").write_text(
                json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"  放行记录已写入: {audit_dir / 'allowance_record.json'}")

    # 全属性中文引号扫描（与 validator 共享逻辑，双重确认）
    cn_quote_hits = find_cn_quoted_attrs(html_content)
    # validator 已经把 cn_quote_hits 计入 v_errors，这里只用于摘要展示

    # ---- 安全摘要 ----
    print("── 发布前安全摘要 ──")
    print(f"  HTML 路径:                    {html_path}")
    print(f"  raw_file_sha256:              {raw_file_sha256}")
    print(f"  normalized_content_sha256:    {normalized_content_sha256}")
    print(f"  CJK count:                    {cjk_count}")
    print(f"  span leaf count:              {leaf_count}")
    print(f"  literal_unicode:              {unicode_hits}")
    print(f"  cn-quoted attrs:              {len(cn_quote_hits)}")
    print(f"  validator ERROR:              {len(v_errors)}")
    print(f"  validator WARN:               {len(v_warnings)}")
    print(f"  publish ERROR:                {len(errors)}")
    print(f"  publish WARNING:              {len(warnings)}")
    print(f"  allowed WARNING:              {len(allowed_records)}")

    if errors:
        print(f"\n❌ 预检失败（{len(errors)} 项 ERROR）:")
        for e in errors:
            print(f"   • {e}")

    if warnings:
        print(f"\n⚠️  预检阻断（{len(warnings)} 项未放行 WARNING）:")
        for w in warnings:
            print(f"   • {w}")

    # 档54R:ERROR 一律阻断;未放行 WARNING 阻断;可放行类别已显式放行并留痕
    if errors or warnings:
        print("\n  不得获取 token，不得调用 draft/add")
        sys.exit(1)

    print("  预检通过 ✅（ERROR=0, WARNING=0）")
    return sha256


def batchget_drafts(access_token, offset=0, count=20):
    """draft/batchget — list existing drafts (READ ONLY). Returns total_count +
    a desensitized item list. Never publishes, never deletes."""
    try:
        resp = requests.post(
            BATCHGET_DRAFT_URL,
            params={"access_token": access_token},
            data=json.dumps({"offset": offset, "count": count, "no_content": 1}).encode("utf-8"),
            headers={"Content-Type": "application/json; charset=utf-8"},
            timeout=30,
        )
        data = json.loads(resp.content.decode("utf-8"))
    except requests.exceptions.RequestException as e:
        api_error(f"draft/batchget 网络请求失败: {e}")
    except (ValueError, UnicodeDecodeError):
        api_error("draft/batchget 返回非 JSON 响应", {"errcode": -1, "errmsg": "non-JSON"})
    if "total_count" not in data:
        api_error("draft/batchget 失败", data)
    return data


def _desensitize_item(it):
    mid = it.get("media_id", "") or ""
    return {"media_id": (mid[:8] + "[REDACTED]") if mid else "",
            "update_time": it.get("update_time")}


def _snapshot(data, simulated, real_api_call):
    items = [_desensitize_item(it) for it in data.get("item", data.get("items", []))]
    return {"total_count": data.get("total_count", len(items)),
            "item_count": data.get("item_count", len(items)),
            "items": items, "simulated": simulated, "real_api_call": real_api_call}


def run_audit_mode(args, html_content, raw_file_sha256, sha256):
    """Draft-creation AUDIT: snapshot draft list before, create ONE draft, snapshot
    after — proving AFTER = BEFORE + 1 with old drafts preserved. Writes
    draft_before.json / draft_after.json / draft_creation_result.json.

    --dry-run (or missing credentials) => fully simulated, ZERO network/side
    effects, marked simulated=true. Real mode does real batchget + draft/add
    (still draft-only: NO publish, NO mass-send, NO delete). NEVER formally
    publishes.
    """
    audit_dir = Path(args.audit_dir)
    audit_dir.mkdir(parents=True, exist_ok=True)
    app_id = os.environ.get("WECHAT_APP_ID", "")
    app_secret = os.environ.get("WECHAT_APP_SECRET", "")
    simulated = bool(args.dry_run) or not (app_id and app_secret)
    provided_cover = bool(args.cover or args.thumb_media_id)
    placeholder_path = None
    cover_source = "approved_body_image" if provided_cover else "placeholder_zero_image"
    if not provided_cover:
        placeholder_path = generate_placeholder_cover(
            args.title, audit_dir, brand=getattr(args, "brand", None))
        if placeholder_path is None:
            api_error("零图交付且无法生成占位封面（PIL/字体不可用）", {"errcode": -1})

    if simulated:
        seed = [{"media_id": f"seed{i:04d}"} for i in range(1, 4)]
        before_raw = {"total_count": 3, "item_count": 3, "item": seed}
        new_media = hashlib.sha256((args.title + sha256).encode()).hexdigest()
        after_raw = {"total_count": 4, "item_count": 4,
                     "item": seed + [{"media_id": new_media}]}
        before = _snapshot(before_raw, simulated=True, real_api_call=False)
        after = _snapshot(after_raw, simulated=True, real_api_call=False)
        result_media = new_media[:8] + "[REDACTED]"
    else:
        token = get_access_token(app_id, app_secret)
        before_raw = batchget_drafts(token)
        before = _snapshot(before_raw, simulated=False, real_api_call=True)
        if args.cover:
            thumb = upload_cover(token, args.cover)
        elif args.thumb_media_id:
            thumb = args.thumb_media_id
        else:
            thumb = upload_cover(token, str(placeholder_path))
        media_id = create_draft(token, args.title, html_content, thumb)
        after_raw = batchget_drafts(token)
        after = _snapshot(after_raw, simulated=False, real_api_call=True)
        result_media = (media_id[:8] + "[REDACTED]") if media_id else ""

    result = {
        "media_id": result_media, "title": args.title,
        "before_total": before["total_count"], "after_total": after["total_count"],
        "delta": after["total_count"] - before["total_count"],
        "draft_only": True, "formally_published": False,
        "mass_send": False, "scheduled": False, "deleted_any": False,
        "real_api_call": not simulated, "simulated": simulated,
        "content_sha256": sha256, "raw_file_sha256": raw_file_sha256,
        "cover_source": cover_source,
    }

    for name, obj in (("draft_before.json", before), ("draft_after.json", after),
                      ("draft_creation_result.json", result)):
        (audit_dir / name).write_text(
            json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8")

    print(f"── 草稿审计 ──  simulated={simulated}  before={before['total_count']} "
          f"after={after['total_count']} delta={result['delta']}")
    if result["delta"] != 1:
        print("错误: AFTER != BEFORE + 1，审计失败")
        sys.exit(1)
    print(f"  审计产物写入: {audit_dir}")
    return result


def verify_pipeline_evidence(evidence_path, html_path, html_sha, html_content):
    """76L/OBS-282:交付凭证门——三项缺一即 FAIL_CLOSED。

    1. 凭证存在且 receipt 校验通过(validator_exit_code == 0);
    2. 待推 HTML 的 raw sha 与 receipt.output_hashes["final.html"] 一致;
    3. HTML 含 hammer 主题签名(非管线渲染产物/手工顶包 HTML 无此签名)。

    报错文案一律指引「走管线 wechat_draft 阶段」。返回 (ok, errors[])。
    """
    errors = []
    try:
        receipt = json.loads(Path(evidence_path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return False, [f"凭证不可读: {evidence_path} ({exc})",
                       "正确动作:走管线 wechat_draft 阶段,不要直接调用本脚本"]
    if receipt.get("validator_exit_code") != 0:
        errors.append(f"凭证 receipt 校验未通过(validator_exit_code="
                      f"{receipt.get('validator_exit_code')!r} != 0)")
    bound_sha = (receipt.get("output_hashes") or {}).get("final.html")
    if not bound_sha:
        errors.append("凭证 receipt 未绑定 final.html(output_hashes 缺 final.html)")
    elif bound_sha != html_sha:
        errors.append(f"HTML sha 与凭证不一致: 待推 {html_sha[:16]}… != 凭证 {bound_sha[:16]}…")
    if THEME_SIGNATURE.lower() not in (html_content or "").lower():
        errors.append(f"HTML 缺主题签名({THEME_SIGNATURE})——疑似手工顶包/非管线渲染产物")
    if errors:
        errors.append("FAIL_CLOSED: 交付凭证缺失或不符;正确动作=走管线 wechat_draft 阶段,"
                      "禁止绕过管线直接调用本脚本")
    return (not errors), errors


def main():
    ap = argparse.ArgumentParser(description="微信公众号草稿创建")
    ap.add_argument("--html", required=True, help="article.wechat.html 路径")
    ap.add_argument("--evidence", required=True,
                    help="本 RUN 的 gzh_design/stage_receipt.json 路径(76L/OBS-282 凭证门,"
                         "必填;无凭证直接调用一律 FAIL_CLOSED,走管线 wechat_draft 阶段)")
    ap.add_argument("--title", required=True, help="文章标题")
    ap.add_argument("--brand", default=None,
                    help="占位封面品牌行（默认给自己造把锤子）")
    ap.add_argument("--expect-sha256", help="期望的 HTML 文件 SHA-256（raw bytes），不一致则停止")
    group = ap.add_mutually_exclusive_group(required=False)
    group.add_argument("--thumb-media-id", help="已上传的封面素材 ID")
    group.add_argument("--cover", help="封面图片路径（自动上传）")
    ap.add_argument("--audit-dir", default=None,
                    help="审计模式：写 draft_before/after/creation_result.json 到该目录")
    ap.add_argument("--dry-run", action="store_true",
                    help="审计模式下不触网、不建真实草稿（模拟 batchget 前后快照）")
    ap.add_argument("--allow-warnings", action="store_true",
                    help="显式放行可放行类别 WARN（半角标点/英文引号）；默认关闭；"
                         "仅对 WARN_ALLOWABLE 生效，其余 WARN 与全部 ERROR 仍阻断；"
                         "放行条目逐条写入 audit-dir/allowance_record.json")
    args = ap.parse_args()

    # 最低限度检查
    html_path = args.html
    if not os.path.isfile(html_path):
        print(f"错误: HTML 文件不存在: {html_path}")
        sys.exit(1)

    # 禁止搜索 fallback
    for forbidden in ("latest", "scratch"):
        if forbidden in html_path:
            print(f"错误: 禁止使用保留字 '{forbidden}' 在路径中")
            sys.exit(1)

    # 使用 --cover 时，检查封面文件存在（不涉及网络）
    if args.cover:
        if not os.path.isfile(args.cover):
            print(f"错误: 封面图片不存在: {args.cover}")
            sys.exit(1)

    # ---- 计算 raw_file_sha256（基于文件 raw bytes）----
    with open(html_path, "rb") as f:
        raw_bytes = f.read()
    raw_file_sha256 = hashlib.sha256(raw_bytes).hexdigest()

    # ---- 期望 SHA-256 验证（基于 raw bytes）----
    if args.expect_sha256:
        actual_sha = raw_file_sha256
        if actual_sha != args.expect_sha256.lower():
            print(f"错误: SHA-256 不匹配")
            print(f"  期望: {args.expect_sha256}")
            print(f"  实际: {actual_sha}")
            print(f"  不得发布错误的文件")
            sys.exit(1)
        print(f"  期望 SHA-256 验证通过 ✅: {actual_sha}")

    # 读取 HTML（open encoding="utf-8" 会 CRLF→LF）
    with open(html_path, encoding="utf-8") as f:
        html_content = f.read()

    # ---- 发布前安全校验（必须在获取 token 前完成）----
    sha256 = preflight_html(html_content, html_path, raw_file_sha256=raw_file_sha256,
                            audit_dir=Path(args.audit_dir) if args.audit_dir else None,
                            allow_warnings=args.allow_warnings)

    # 76L/OBS-282:交付凭证门——receipt ok + html sha 一致 + 主题签名,缺一即停。
    # 必须在获取 access_token / 调用微信 API 之前完成。
    evidence_ok, evidence_errors = verify_pipeline_evidence(
        args.evidence, html_path, raw_file_sha256, html_content)
    if not evidence_ok:
        for line in evidence_errors:
            print(f"错误: {line}")
        sys.exit(1)
    print(f"  交付凭证验证通过 ✅ (receipt 绑定 + sha 一致 + 主题签名)")

    # ---- 审计模式：快照前后草稿数并写审计产物（--dry-run 时不触网、无副作用）----
    if args.audit_dir:
        run_audit_mode(args, html_content, raw_file_sha256, sha256)
        return


    # ---- 预检通过后才读取环境变量并获取 token ----
    app_id = os.environ.get("WECHAT_APP_ID", "")
    app_secret = os.environ.get("WECHAT_APP_SECRET", "")
    if not app_id or not app_secret:
        print("错误: 请设置 WECHAT_APP_ID 和 WECHAT_APP_SECRET 环境变量")
        sys.exit(1)

    print("获取 access_token...")
    access_token = get_access_token(app_id, app_secret)

    # 处理封面
    if args.cover:
        print(f"上传封面: {args.cover}")
        thumb_media_id = upload_cover(access_token, args.cover)
    elif args.thumb_media_id:
        thumb_media_id = args.thumb_media_id
    else:
        placeholder_path = generate_placeholder_cover(
            args.title, Path(args.audit_dir) if args.audit_dir else Path.cwd(),
            brand=args.brand)
        if placeholder_path is None:
            api_error("零图交付且无法生成占位封面（PIL/字体不可用）", {"errcode": -1})
        print(f"  零图交付：使用占位封面 {placeholder_path}")
        thumb_media_id = upload_cover(access_token, str(placeholder_path))

    # 创建草稿
    print(f"创建草稿: title={args.title}")
    media_id = create_draft(access_token, args.title, html_content, thumb_media_id)

    print(f"\n草稿创建成功!")
    print(f"  media_id: {media_id}")
    print(f"  title:    {args.title}")
    print(f"\n请到微信公众号后台 → 草稿箱检查。")


if __name__ == "__main__":
    main()
