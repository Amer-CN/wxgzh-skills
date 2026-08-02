#!/usr/bin/env python3
"""生成 B 层注释图片测试资产"""
import os
from PIL import Image, ImageDraw, ImageFont

ASSETS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      "tests", "advanced-components", "assets")

def get_font(size):
    for path in ["C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/segoeui.ttf"]:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()

def gen_annotated_dashboard():
    img = Image.new("RGB", (700, 450), (245, 247, 250))
    d = ImageDraw.Draw(img)
    ft = get_font(18)
    d.rectangle([0, 0, 699, 449], outline=(91, 155, 213), width=2)
    d.text((200, 15), "CONTROL DASHBOARD", fill=(50, 100, 200), font=ft)
    d.rectangle([20, 50, 180, 400], fill=(91, 155, 213))
    d.text((40, 60), "1 NAV", fill=(255, 255, 255), font=ft)
    d.rectangle([200, 50, 500, 350], fill=(52, 199, 89))
    d.text((300, 60), "2 STATUS", fill=(255, 255, 255), font=ft)
    d.rectangle([520, 50, 680, 100], fill=(245, 158, 11))
    d.text((530, 60), "3 PUBLISH", fill=(255, 255, 255), font=ft)
    img.save(os.path.join(ASSETS, "annotated-dashboard.png"))
    print("OK: annotated-dashboard.png (700x450)")

def gen_annotated_flow():
    img = Image.new("RGB", (700, 600), (245, 247, 250))
    d = ImageDraw.Draw(img)
    ft = get_font(18)
    d.rectangle([0, 0, 699, 599], outline=(52, 199, 89), width=2)
    d.text((200, 15), "ANNOTATED FLOW", fill=(50, 100, 200), font=ft)
    d.ellipse([50, 60, 120, 130], fill=(91, 155, 213))
    d.text((65, 85), "1", fill=(255, 255, 255), font=ft)
    d.line([85, 130, 85, 180], fill=(100, 100, 100), width=3)
    d.ellipse([50, 180, 120, 250], fill=(52, 199, 89))
    d.text((65, 205), "2", fill=(255, 255, 255), font=ft)
    d.line([85, 250, 85, 300], fill=(100, 100, 100), width=3)
    d.ellipse([50, 300, 120, 370], fill=(245, 158, 11))
    d.text((65, 325), "3", fill=(255, 255, 255), font=ft)
    img.save(os.path.join(ASSETS, "annotated-flow.png"))
    print("OK: annotated-flow.png (700x600)")

if __name__ == "__main__":
    gen_annotated_dashboard()
    gen_annotated_flow()
    print(f"\nAll assets in: {ASSETS}")
