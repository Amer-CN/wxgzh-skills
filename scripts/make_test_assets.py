#!/usr/bin/env python3
"""用 Pillow 生成本地测试图片素材 —— 快速版"""
import os
from PIL import Image, ImageDraw, ImageFont

ASSETS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      "tests", "advanced-components", "assets")
os.makedirs(ASSETS, exist_ok=True)

def get_font(size):
    for path in ["C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/segoeui.ttf"]:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()

def gen_media_demo():
    img = Image.new("RGB", (800, 400), (245, 247, 250))
    d = ImageDraw.Draw(img)
    d.text((280, 20), "ARCHITECTURE", fill=(50, 100, 200), font=get_font(28))
    d.rectangle([50, 100, 230, 200], fill=(91, 155, 213))
    d.text((95, 130), "API", fill=(255, 255, 255), font=get_font(24))
    d.rectangle([310, 100, 490, 200], fill=(52, 199, 89))
    d.text((335, 130), "SERVICE", fill=(255, 255, 255), font=get_font(18))
    d.rectangle([570, 100, 750, 200], fill=(245, 158, 11))
    d.text((605, 130), "DB", fill=(255, 255, 255), font=get_font(24))
    d.rectangle([230, 145, 310, 155], fill=(100, 100, 100))
    d.rectangle([490, 145, 570, 155], fill=(100, 100, 100))
    d.rectangle([150, 260, 650, 320], fill=(200, 200, 200))
    d.text((330, 275), "API GATEWAY", fill=(80, 80, 80), font=get_font(18))
    img.save(os.path.join(ASSETS, "media-demo.png"))
    print("OK: media-demo.png (800x400)")

def gen_gallery(n, label, color):
    img = Image.new("RGB", (600, 400), (250, 250, 248))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 599, 399], outline=color, width=3)
    d.rectangle([20, 40, 580, 70], fill=color)
    d.text((200, 45), label, fill=(255, 255, 255), font=get_font(18))
    d.rectangle([250, 150, 350, 250], fill=tuple(c//2 for c in color))
    d.text((280, 180), str(n), fill=(255, 255, 255), font=get_font(28))
    d.text((200, 280), f"STEP {n}", fill=(80, 80, 80), font=get_font(18))
    img.save(os.path.join(ASSETS, f"gallery-0{n}.png"))
    print(f"OK: gallery-0{n}.png (600x400)")

def gen_long_flow():
    img = Image.new("RGB", (800, 1800), (252, 252, 250))
    d = ImageDraw.Draw(img)
    d.text((250, 20), "CI/CD FLOW", fill=(50, 100, 200), font=get_font(28))
    nodes = [
        (100, "GIT PUSH", (91, 155, 213)), (250, "BUILD", (52, 199, 89)),
        (400, "TEST", (245, 158, 11)), (550, "DOCKER BUILD", (239, 71, 111)),
        (700, "DEPLOY STAGING", (139, 92, 246)), (850, "SMOKE TEST", (20, 184, 166)),
        (1000, "APPROVE", (245, 158, 11)), (1150, "DEPLOY PROD", (239, 71, 111)),
        (1300, "NOTIFY", (52, 199, 89)), (1450, "MONITOR", (91, 155, 213)),
    ]
    for y, label, color in nodes:
        d.rectangle([200, y, 600, y+80], fill=color)
        d.text((260, y+25), label, fill=(255, 255, 255), font=get_font(18))
        if y < 1450:
            d.rectangle([395, y+80, 405, y+150], fill=(150, 150, 150))
    d.text((180, 1600), "FULL DEPLOYMENT PIPELINE", fill=(100, 100, 100), font=get_font(18))
    d.text((220, 1640), "10 STAGES - 1800PX LONG", fill=(150, 150, 150), font=get_font(16))
    img.save(os.path.join(ASSETS, "long-flow.png"))
    print("OK: long-flow.png (800x1800)")

def main():
    gen_media_demo()
    gen_gallery(1, "DOWNLOAD", (91, 155, 213))
    gen_gallery(2, "CONFIG", (52, 199, 89))
    gen_gallery(3, "RUN", (245, 158, 11))
    gen_long_flow()
    print(f"\nAll assets in: {ASSETS}")

if __name__ == "__main__":
    main()
