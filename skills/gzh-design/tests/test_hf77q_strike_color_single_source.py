"""77Q/OBS-341: cover strike color single source and contrast regression."""
from __future__ import annotations

import importlib.util
import re
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = SKILL_ROOT / "scripts" / "generate_hammer_upgrade_samples.py"

spec = importlib.util.spec_from_file_location("hammer_samples", SCRIPT)
hammer_samples = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hammer_samples)


def _relative_luminance(color: str) -> float:
    hex_color = color.lstrip("#")
    channels = [int(hex_color[index:index + 2], 16) / 255 for index in (0, 2, 4)]
    linear = [
        value / 12.92 if value <= 0.03928 else ((value + 0.055) / 1.055) ** 2.4
        for value in channels
    ]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def _contrast_ratio(foreground: str, background: str = "#ffffff") -> float:
    first = _relative_luminance(foreground)
    second = _relative_luminance(background)
    lighter, darker = max(first, second), min(first, second)
    return (lighter + 0.05) / (darker + 0.05)


def _style_properties(style: str) -> dict[str, str]:
    return {
        match.group(1).strip(): match.group(2).strip()
        for match in re.finditer(r"([\w-]+)\s*:\s*([^;]+)", style)
    }


def test_cover_strike_uses_readable_single_source_color():
    assert hammer_samples.PALETTES["moyu-green"]["strike_text"] == "#4B5563"
    assert hammer_samples.PALETTES["hammer"]["strike_text"] == "#555555"
    for theme_key, theme in hammer_samples.PALETTES.items():
        assert _contrast_ratio(theme["strike_text"]) >= 4.5
        html = hammer_samples.hammer_cover(
            theme_key, kicker="K", strike="训练用了版权内容=侵权？",
            title_line1="标题一", title_line2="标题二", subtitle="副标题",
        )
        strike_styles = [
            _style_properties(style)
            for style in re.findall(r'<p style="([^"]+)"', html)
            if "line-through" in style
        ]
        assert len(strike_styles) == 1
        expected = theme["strike_text"]
        assert strike_styles[0]["color"] == expected
        assert strike_styles[0]["text-decoration-color"] == expected
        assert "rgba(202,202,199" not in strike_styles[0]["color"]
        assert "#D1D5DB" not in strike_styles[0]["color"]
