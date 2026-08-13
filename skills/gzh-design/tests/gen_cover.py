#!/usr/bin/env python3
"""Generate a Hammer-themed cover image for the showcase article."""
from PIL import Image, ImageDraw, ImageFont

W, H = 900, 383
img = Image.new('RGB', (W, H), '#FFFFFF')
draw = ImageDraw.Draw(img)

# Background gradient (brick red to light brick)
for y in range(H):
    r = int(179 + (200 - 179) * y / H)
    g = int(89 + (100 - 89) * y / H)
    b = int(59 + (66 - 59) * y / H)
    draw.line([(0, y), (W, y)], fill=(r, g, b))

# Main title
try:
    font_large = ImageFont.truetype('C:/Windows/Fonts/msyhbd.ttc', 52)
    font_small = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', 22)
except Exception:
    font_large = ImageFont.load_default()
    font_small = ImageFont.load_default()

title = "\u9524\u5b50\u98ce\u683c\u7ec4\u4ef6\u5168\u5c55\u793a"
bbox = draw.textbbox((0, 0), title, font=font_large)
tw = bbox[2] - bbox[0]
draw.text(((W - tw) // 2, 110), title, fill='#FFFFFF', font=font_large)

sub = 'HAMMER THEME · ALL COMPONENTS SHOWCASE'
bbox2 = draw.textbbox((0, 0), sub, font=font_small)
tw2 = bbox2[2] - bbox2[0]
draw.text(((W - tw2) // 2, 195), sub, fill=(230, 198, 185), font=font_small)

# Bottom bar
draw.rectangle([0, H - 55, W, H], fill=(179, 89, 59))
tag = 'SHOWCASE \u00b7 2026.07'
bbox3 = draw.textbbox((0, 0), tag, font=font_small)
tw3 = bbox3[2] - bbox3[0]
draw.text(((W - tw3) // 2, H - 42), tag, fill='#FFFFFF', font=font_small)

img.save('tests/hammer-showcase-cover.jpg', 'JPEG', quality=90)
print('Cover image saved to tests/hammer-showcase-cover.jpg')
