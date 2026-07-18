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
    2. 获取 access_token
    3. 如有 --cover 则上传封面获取 thumb_media_id
    4. 调用微信 draft/add 创建草稿
    5. 返回草稿 media_id

安全:
    - HTML 文件必须明确传入且存在
    - 禁止搜索 latest、日期目录、scratch
    - APPSECRET 和 access_token 不打印、不写文件
    - 微信 API 返回错误时立即停止
    - draft/add 不自动重试
    - 默认只创建草稿，不正式发布和群发
"""
import argparse
import os
import sys

try:
    import requests
except ImportError:
    print("错误: 需要安装 requests 库: pip install requests")
    sys.exit(1)

# 微信 API 端点
TOKEN_URL = "https://api.weixin.qq.com/cgi-bin/token"
ADD_DRAFT_URL = "https://api.weixin.qq.com/cgi-bin/draft/add"
UPLOAD_MATERIAL_URL = "https://api.weixin.qq.com/cgi-bin/material/add_material"


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
    """上传封面图片，返回 thumb_media_id"""
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


def create_draft(access_token, title, html_content, thumb_media_id):
    """创建微信公众号草稿"""
    article = {
        "title": title,
        "content": html_content,
        "thumb_media_id": thumb_media_id,
        "need_open_comment": 0,
        "only_fans_can_comment": 0,
    }
    try:
        resp = requests.post(
            ADD_DRAFT_URL,
            params={"access_token": access_token},
            json={"articles": [article]},
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


def main():
    ap = argparse.ArgumentParser(description="微信公众号草稿创建")
    ap.add_argument("--html", required=True, help="article.wechat.html 路径")
    ap.add_argument("--title", required=True, help="文章标题")
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--thumb-media-id", help="已上传的封面素材 ID")
    group.add_argument("--cover", help="封面图片路径（自动上传）")
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

    # 使用 --cover 时，在获取 access_token 前检查封面文件存在
    if args.cover:
        if not os.path.isfile(args.cover):
            print(f"错误: 封面图片不存在: {args.cover}")
            sys.exit(1)

    # 读取环境变量
    app_id = os.environ.get("WECHAT_APP_ID", "")
    app_secret = os.environ.get("WECHAT_APP_SECRET", "")
    if not app_id or not app_secret:
        print("错误: 请设置 WECHAT_APP_ID 和 WECHAT_APP_SECRET 环境变量")
        sys.exit(1)

    # 读取 HTML
    with open(html_path, encoding="utf-8") as f:
        html_content = f.read()

    # 获取 access_token
    print("获取 access_token...")
    access_token = get_access_token(app_id, app_secret)

    # 处理封面
    if args.cover:
        print(f"上传封面: {args.cover}")
        thumb_media_id = upload_cover(access_token, args.cover)
    else:
        thumb_media_id = args.thumb_media_id

    # 创建草稿
    print(f"创建草稿: title={args.title}")
    media_id = create_draft(access_token, args.title, html_content, thumb_media_id)

    print(f"\n草稿创建成功!")
    print(f"  media_id: {media_id}")
    print(f"  title:    {args.title}")
    print(f"\n请到微信公众号后台 → 草稿箱检查。")


if __name__ == "__main__":
    main()
