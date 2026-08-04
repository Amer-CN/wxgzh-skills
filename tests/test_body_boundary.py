"""档62 OBS-86:正文边界判定测试。

覆盖:
1. ithome 聚合页夹具:六张真实图全部在正文容器内,但仅 claim 对齐的 A-113 保留;
   四张汽车图 + 携程图判为跨章节图(下载前排除,位置仍记录);
   A-108 惰性占位 src(t.png)与头像/侧边栏/推荐位/广告/页脚/1×1 像素
   在提取阶段直接排除(下载前,零请求)。
2. 未知结构(裸 body 无容器)保留为 unknown 候选,不默认排除也不默认放行。
3. section_align:真实章节标题 vs claim C-06 的对齐判定。
4. run-level:CLI discover 离线跑,断言 manifest 与下载行为。
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from PIL import Image

SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "src"))
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from media_enrichment.image_extractor import extract_images  # noqa: E402
from media_enrichment.section_align import section_matches_claims, tokenize  # noqa: E402

FIXTURES = SKILL_ROOT / "fixtures" / "html"
ITHOME = FIXTURES / "ithome-aggregate-obs86.html"

C06 = "OpenAI 于 7 月 31 日宣布下调 GPT-5.6 Terra 和 GPT-5.6 Luna 两款模型的调用费用"
SECTIONS = {
    "A-113": "2、降价 80%！OpenAI 下调 GPT-5.6 Luna 模型费用，性价比超 DeepSeek V4 Pro",
    "A-114": "3、携程回应“1.5 万元机票天价退票费全额退还”：非平台破例优待，将升级风险提示机制",
    "A-109": "4、29.99 万元！小米澎程 N90 Max 增程 SUV 预售价格公布",
    "A-110": "14、比亚迪大汉核心信息公布：四驱版 3.8 秒破百，1008km“大型轿车全球第一纯电续航”",
    "A-111": "18、消息称比亚迪日本海獭 RACCO 微型车首周锁单定金突破 5000 台",
    "A-112": "20、特斯拉全球第 1000 万辆电动车下线",
}
URLS = {
    "A-109": "https://img.ithome.com/newsuploadfiles/2026/7/73648c29-3084-47ca-8955-3da40e34cb77.jpg",
    "A-110": "https://img.ithome.com/newsuploadfiles/2026/7/223135f7-2204-4dcd-b454-0ef877979b10.jpg",
    "A-111": "https://img.ithome.com/newsuploadfiles/2026/7/22c6f53e-cf1d-456c-8f27-1a38c1b9629d.jpg",
    "A-112": "https://img.ithome.com/newsuploadfiles/2026/7/6555a03f-76e4-4daa-96a4-3277ff825f6c.jpg",
    "A-113": "https://img.ithome.com/newsuploadfiles/2026/7/f8292a43-1a6d-4d21-8a2b-c97832406267.png",
    "A-114": "https://img.ithome.com/newsuploadfiles/2026/7/75ea2358-26d7-4579-a143-ae21317dd4ca.jpg",
}


def _extract():
    return extract_images(ITHOME.read_text(encoding="utf-8"),
                          page_url="https://www.ithome.com/0/983/917.htm")


# ── 1. 提取层:区域判定 + 章节归属 + 下载前排除 ─────────────────

def test_six_images_body_region_with_section_heading():
    result = _extract()
    by_url = {c.url: c for c in result.candidates}
    for aid in ("A-109", "A-110", "A-111", "A-112", "A-113", "A-114"):
        c = by_url[URLS[aid]]
        assert c.page_region == "body", aid
        assert c.section_heading == SECTIONS[aid], aid
        assert c.section_level == "h2", aid


def test_placeholder_src_excluded_before_download():
    result = _extract()
    urls = [c.url for c in result.candidates]
    # t.png(惰性占位,真实 URL 在 srcset)不产候选——A-108 场景在下载前排除
    assert not any("images/v2/t.png" in u for u in urls)
    assert any("t.png" in e["url"] for e in result.excluded)
    assert any("placeholder" in e["reason"] for e in result.excluded)


def test_page_furniture_excluded_at_extraction():
    result = _extract()
    urls = [c.url for c in result.candidates]
    for furniture in (
        "mpimg/account/10233.jpg",   # 头像(档50 A-107 同款)
        "thumb-recommend-car.jpg",   # 推荐位缩略图
        "ads.example.com/banner",    # 广告位
        "footer-logo.png",           # 页脚
        "tracker.example.com/pixel.gif",  # 1×1 追踪像素(尺寸属性)
    ):
        assert not any(furniture in u for u in urls), furniture
    reasons = " | ".join(e["reason"] for e in result.excluded)
    assert "avatar" in reasons or "aside" in reasons or "sidebar" in reasons
    assert "tracking pixel" in reasons


def test_unknown_structure_kept_as_candidate():
    html = "<html><body><img src='https://example.com/x.jpg'></body></html>"
    result = extract_images(html, page_url="https://example.com/p")
    assert len(result.candidates) == 1
    assert result.candidates[0].page_region == "unknown"
    assert result.candidates[0].section_heading == ""


# ── 2. 章节对齐(claim 驱动)────────────────────────────────────

def test_section_align_real_headings():
    # C-06 对齐 OpenAI 章节
    assert section_matches_claims(SECTIONS["A-113"], [C06]) is True
    # 汽车/机票章节不对齐
    for aid in ("A-109", "A-110", "A-111", "A-112", "A-114"):
        assert section_matches_claims(SECTIONS[aid], [C06]) is False, aid
    # 空标题 / 空 claim -> 不对齐(保守排除)
    assert section_matches_claims("", [C06]) is False
    assert section_matches_claims(SECTIONS["A-113"], []) is False


def test_tokenize():
    toks = tokenize(SECTIONS["A-113"])
    assert "openai" in toks and "gpt" in toks and "luna" in toks
    assert tokenize("小米澎程 N90 Max 增程 SUV 预售价格公布") & tokenize(C06) == set()


# ── 3. run-level:CLI discover 离线跑 ──────────────────────────

def _make_offline_run(tmp_path):
    """构造离线 fixture:页面 HTML(聚合页)+ A-113 图片 + 请求 + 文章。"""
    fixtures = tmp_path / "fixtures"
    fixtures.mkdir()
    # 页面 fixture:slug = URL 最后一段
    # page_fetcher 的 slug = URL 路径最后一段(917.htm),fixture 文件为 917.htm.html
    (fixtures / "917.htm.html").write_text(ITHOME.read_text(encoding="utf-8"), encoding="utf-8")
    # A-113 图片 fixture(唯一会走到下载的资产)。下载器按 fixture_dir 的
    # 同级 images/ 目录映射 URL 文件名(run_media_enrichment L134)。
    images_dir = tmp_path / "images"
    images_dir.mkdir()
    img = Image.new("RGB", (800, 600), color=(255, 255, 255))
    img.save(str(images_dir / "f8292a43-1a6d-4d21-8a2b-c97832406267.png"), "PNG")
    # 文章(供 placement)
    article = tmp_path / "article.md"
    article.write_text(f"# 标题\n\n{C06}\n", encoding="utf-8")
    import hashlib
    request = {
        "schema_version": "1.0",
        "run_id": "obs86-regression",
        "article": {"path": "article.md",
                    "sha256": hashlib.sha256(article.read_bytes()).hexdigest()},
        "materials": [{
            "material_id": "M-06",
            "aihot_permalink": "https://www.ithome.com/0/983/917.htm",
            "source_url": "https://www.ithome.com/0/983/917.htm",
            "title": "IT 早报", "selected_claim_ids": ["C-06"],
        }],
        "claims": [{"claim_id": "C-06", "claim_text": C06,
                    "material_id": "M-06",
                    "source_url": "https://www.ithome.com/0/983/917.htm",
                    "source_excerpt": C06}],
        "config": {
            "network_mode": "offline_fixture", "upload_mode": "dry_run",
            "max_images_per_material": 12, "max_total_images": 12,
            "min_width": 640, "min_height": 360,
            "allow_unknown_license_for_publish": False,
        },
    }
    req = tmp_path / "request.json"
    req.write_text(json.dumps(request, ensure_ascii=False), encoding="utf-8")
    return req, fixtures


def test_cli_discover_obs86_regression(tmp_path):
    req, fixtures = _make_offline_run(tmp_path)
    out = tmp_path / "out"
    proc = subprocess.run(
        [sys.executable, str(SKILL_ROOT / "scripts" / "run_media_enrichment.py"),
         "--request", str(req), "--output-dir", str(out),
         "--fixture-dir", str(fixtures), "--phase", "discover"],
        capture_output=True, text=True, encoding="utf-8",
    )
    assert proc.returncode == 0, proc.stderr[-2000:]
    manifest = json.loads((out / "media_manifest.json").read_text(encoding="utf-8"))
    by_url = {a["resolved_original_url"]: a for a in manifest["assets"]}
    # A-113(claim 对齐)保留并下载
    a113 = by_url[URLS["A-113"]]
    assert a113["decision"] == "review_required"
    assert a113["page_region"] == "body"
    assert a113["page_position"]["known"] is True
    assert "OpenAI" in a113["page_position"]["heading"]
    assert a113["local_path"]  # 有本地文件=真的下载了
    # 四张汽车图 + 携程图:跨章节,下载前排除(无 local_path),位置仍记录
    for aid in ("A-109", "A-110", "A-111", "A-112", "A-114"):
        rec = by_url[URLS[aid]]
        assert rec["decision"] == "rejected", aid
        assert rec["local_path"] is None, aid
        assert any("cross-section image" in r for r in rec["reasons"]), aid
        assert rec["page_position"]["known"] is True, aid
    # 周边图(A-108 占位/头像/推荐位/广告/页脚/像素)不进 manifest
    for url, rec in by_url.items():
        assert "t.png" not in (url or ""), url
    # 下载次数:仅 A-113
    assert manifest["summary"]["downloads_succeeded"] == 1
    # 排除统计在 warnings 中可见
    joined = " | ".join(manifest.get("warnings", []))
    assert "excluded" in joined and "peripheral" in joined
