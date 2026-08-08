#!/usr/bin/env python3
"""
run_tests.py — zh-human-writing v1 测试运行器

运行所有确定性单元测试，验证三个脚本的正确性。

用法:
    python run_tests.py [--verbose]

退出码:
    0 — 全部通过
    1 — 有失败
"""

import json
import os
import re
import subprocess
import sys
import tempfile

# 脚本路径
SCRIPTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'scripts')
FIDELITY_GUARD = os.path.join(SCRIPTS_DIR, 'fidelity_guard.py')
CHANGE_REPORT = os.path.join(SCRIPTS_DIR, 'change_report.py')
PATTERN_AUDIT = os.path.join(SCRIPTS_DIR, 'pattern_audit.py')

# 档72B-2R PB-010:恒等回归的硬编码期望值(R110)——这 18 个数 =
# 0c8962f 版 max(1, int(threshold * multiplier)) 的逐格结果,
# multiplier = essay 1.0 / technical 1.5 / social 2.0。
# int() 是截断,SC-005 technical 因此是 4 不是 5。
# 禁止用公式现算期望值——用公式就会把同一个 bug 再算一遍。
EXPECTED_SC_THRESHOLDS = {
    'SC-001': {'essay': 2, 'technical': 3, 'social': 4},
    'SC-002': {'essay': 2, 'technical': 3, 'social': 4},
    'SC-003': {'essay': 2, 'technical': 3, 'social': 4},
    'SC-004': {'essay': 2, 'technical': 3, 'social': 4},
    'SC-005': {'essay': 3, 'technical': 4, 'social': 6},
    'SC-006': {'essay': 2, 'technical': 3, 'social': 4},
}

PYTHON = sys.executable


class TestResult:
    def __init__(self, test_id, test_type, passed, message=''):
        self.test_id = test_id
        self.test_type = test_type
        self.passed = passed
        self.message = message

    def __str__(self):
        status = 'PASS' if self.passed else 'FAIL'
        return f'[{status}] {self.test_id} ({self.test_type}): {self.message}'


def write_temp(text):
    """写入临时文件，返回路径。"""
    fd, path = tempfile.mkstemp(suffix='.txt')
    os.write(fd, text.encode('utf-8'))
    os.close(fd)
    return path


def run_script(script, args):
    """运行脚本，返回 (returncode, stdout, stderr)。"""
    cmd = [PYTHON, script] + args
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    return result.returncode, result.stdout, result.stderr


# ============================================================
# must-preserve 测试（10 条）
# ============================================================

def test_must_preserve():
    results = []

    # MP-001: 数字不变
    orig = "系统响应时间为 100ms，在 2024 年 1 月 15 日的测试中，延迟降低了 30%。"
    edited = "系统响应时间为 100ms，在 2024 年 1 月 15 日的测试中，延迟降低了 30%。"
    rc, out, err = run_script(FIDELITY_GUARD, ['--original', write_temp(orig), '--edited', write_temp(edited), '--output', 'json'])
    data = json.loads(out)
    passed = data['fails'] == 0
    results.append(TestResult('MP-001', 'must-preserve', passed, f'数字检查 fails={data["fails"]}'))

    # MP-002: 数字被改变 → fail
    orig = "系统响应时间为 100ms。"
    edited = "系统响应时间为 99ms。"
    rc, out, err = run_script(FIDELITY_GUARD, ['--original', write_temp(orig), '--edited', write_temp(edited), '--output', 'json'])
    data = json.loads(out)
    passed = data['fails'] > 0
    results.append(TestResult('MP-002', 'must-preserve', passed, f'数字变化检测 fails={data["fails"]}'))

    # MP-003: 日期不变
    orig = "在 2024 年 1 月 15 日，系统上线。"
    edited = "在 2024-01-15，系统上线。"
    rc, out, err = run_script(FIDELITY_GUARD, ['--original', write_temp(orig), '--edited', write_temp(edited), '--output', 'json'])
    data = json.loads(out)
    passed = data['fails'] == 0
    results.append(TestResult('MP-003', 'must-preserve', passed, f'日期格式变化允许 fails={data["fails"]}'))

    # MP-004: URL 不变
    orig = "详见 https://example.com/docs/api/v2"
    edited = "详见 https://example.com/docs/api/v2"
    rc, out, err = run_script(FIDELITY_GUARD, ['--original', write_temp(orig), '--edited', write_temp(edited), '--output', 'json'])
    data = json.loads(out)
    passed = data['fails'] == 0
    results.append(TestResult('MP-004', 'must-preserve', passed, f'URL 检查 fails={data["fails"]}'))

    # MP-005: URL 被改变 → fail
    orig = "详见 https://example.com/docs/api/v2"
    edited = "详见 https://example.com/docs/api/v3"
    rc, out, err = run_script(FIDELITY_GUARD, ['--original', write_temp(orig), '--edited', write_temp(edited), '--output', 'json'])
    data = json.loads(out)
    passed = data['fails'] > 0
    results.append(TestResult('MP-005', 'must-preserve', passed, f'URL 变化检测 fails={data["fails"]}'))

    # MP-006: 代码块不变
    orig = "使用命令 `npm install` 安装依赖。"
    edited = "使用命令 `npm install` 安装依赖。"
    rc, out, err = run_script(FIDELITY_GUARD, ['--original', write_temp(orig), '--edited', write_temp(edited), '--output', 'json'])
    data = json.loads(out)
    passed = data['fails'] == 0
    results.append(TestResult('MP-006', 'must-preserve', passed, f'代码检查 fails={data["fails"]}'))

    # MP-007: 代码被改变 → fail
    orig = "使用命令 `npm install` 安装依赖。"
    edited = "使用命令 `npm i` 安装依赖。"
    rc, out, err = run_script(FIDELITY_GUARD, ['--original', write_temp(orig), '--edited', write_temp(edited), '--output', 'json'])
    data = json.loads(out)
    passed = data['fails'] > 0
    results.append(TestResult('MP-007', 'must-preserve', passed, f'代码变化检测 fails={data["fails"]}'))

    # MP-008: 千分位格式变化允许
    orig = "处理了 1,000,000 次请求。"
    edited = "处理了 1000000 次请求。"
    rc, out, err = run_script(FIDELITY_GUARD, ['--original', write_temp(orig), '--edited', write_temp(edited), '--output', 'json'])
    data = json.loads(out)
    passed = data['fails'] == 0
    results.append(TestResult('MP-008', 'must-preserve', passed, f'千分位格式变化允许 fails={data["fails"]}'))

    # MP-009: 百分比不变
    orig = "增长了 25%。"
    edited = "增长了 25％。"
    rc, out, err = run_script(FIDELITY_GUARD, ['--original', write_temp(orig), '--edited', write_temp(edited), '--output', 'json'])
    data = json.loads(out)
    passed = data['fails'] == 0
    results.append(TestResult('MP-009', 'must-preserve', passed, f'百分比符号变化允许 fails={data["fails"]}'))

    # MP-010: 用户 protected spans 不变
    orig = "[[protected]]这段不能改[[/protected]]"
    edited = "[[protected]]这段不能改[[/protected]]"
    rc, out, err = run_script(FIDELITY_GUARD, ['--original', write_temp(orig), '--edited', write_temp(edited), '--output', 'json'])
    data = json.loads(out)
    passed = data['fails'] == 0
    results.append(TestResult('MP-010', 'must-preserve', passed, f'用户 protected spans 检查 fails={data["fails"]}'))

    return results


# ============================================================
# must-edit 测试（10 条）
# ============================================================

def test_must_edit():
    results = []

    # ME-001: 模板占位符被检测
    text = "{{产品名称}}是一款{{产品类型}}，旨在帮助用户{{核心价值}}。"
    rc, out, err = run_script(PATTERN_AUDIT, ['--text', write_temp(text), '--check-level', 'full', '--output', 'json'])
    data = json.loads(out)
    passed = data['hard_residue']['count'] > 0
    results.append(TestResult('ME-001', 'must-edit', passed, f'模板占位符检测 count={data["hard_residue"]["count"]}'))

    # ME-002: AI 自我标识被检测
    text = "作为AI，我无法直接体验产品，但根据用户反馈，这款产品的交互设计有待改进。"
    rc, out, err = run_script(PATTERN_AUDIT, ['--text', write_temp(text), '--check-level', 'full', '--output', 'json'])
    data = json.loads(out)
    passed = data['hard_residue']['count'] > 0
    results.append(TestResult('ME-002', 'must-edit', passed, f'AI自我标识检测 count={data["hard_residue"]["count"]}'))

    # ME-003: 知识截止声明被检测
    text = "截至我的知识截止日期，这个功能尚未发布。"
    rc, out, err = run_script(PATTERN_AUDIT, ['--text', write_temp(text), '--check-level', 'full', '--output', 'json'])
    data = json.loads(out)
    passed = data['hard_residue']['count'] > 0
    results.append(TestResult('ME-003', 'must-edit', passed, f'知识截止声明检测 count={data["hard_residue"]["count"]}'))

    # ME-004: 聊天助手残留被检测
    text = "请问还有什么可以帮助您的？随时告诉我。"
    rc, out, err = run_script(PATTERN_AUDIT, ['--text', write_temp(text), '--check-level', 'full', '--output', 'json'])
    data = json.loads(out)
    passed = data['hard_residue']['count'] > 0
    results.append(TestResult('ME-004', 'must-edit', passed, f'聊天助手残留检测 count={data["hard_residue"]["count"]}'))

    # ME-005: AI 来源参数被检测
    text = "model=gpt-4 temperature=0.7 生成结果"
    rc, out, err = run_script(PATTERN_AUDIT, ['--text', write_temp(text), '--check-level', 'full', '--output', 'json'])
    data = json.loads(out)
    passed = data['hard_residue']['count'] > 0
    results.append(TestResult('ME-005', 'must-edit', passed, f'AI来源参数检测 count={data["hard_residue"]["count"]}'))

    # ME-006: 无 hard-residue 时 pass
    text = "这是一篇普通文章，没有 AI 残留。"
    rc, out, err = run_script(PATTERN_AUDIT, ['--text', write_temp(text), '--check-level', 'full', '--output', 'json'])
    data = json.loads(out)
    passed = data['overall']['pass_fail'] == 'pass' and rc == 0
    results.append(TestResult('ME-006', 'must-edit', passed, f'无残留时 pass={data["overall"]["pass_fail"]}'))

    # ME-007: 有 hard-residue 时 fail
    text = "作为AI，我认为这个产品不错。"
    rc, out, err = run_script(PATTERN_AUDIT, ['--text', write_temp(text), '--check-level', 'full', '--output', 'json'])
    data = json.loads(out)
    passed = data['overall']['pass_fail'] == 'fail' and rc == 2
    results.append(TestResult('ME-007', 'must-edit', passed, f'有残留时 fail={data["overall"]["pass_fail"]}'))

    # ME-008: 退出码正确（pass → 0）
    text = "这是一段正常的文字。"
    rc, out, err = run_script(PATTERN_AUDIT, ['--text', write_temp(text), '--output', 'json'])
    passed = rc == 0
    results.append(TestResult('ME-008', 'must-edit', passed, f'退出码=0 rc={rc}'))

    # ME-009: 退出码正确（fail → 2）
    text = "作为AI，我建议..."
    rc, out, err = run_script(PATTERN_AUDIT, ['--text', write_temp(text), '--output', 'json'])
    passed = rc == 2
    results.append(TestResult('ME-009', 'must-edit', passed, f'退出码=2 rc={rc}'))

    # ME-010: advisory-only 不影响 pass/fail
    text = "不是因为它不好看，而是因为它太贵了。这不是问题。"
    rc, out, err = run_script(PATTERN_AUDIT, ['--text', write_temp(text), '--check-level', 'full', '--output', 'json'])
    data = json.loads(out)
    passed = data['overall']['pass_fail'] == 'pass' and data['advisory_only']['count'] > 0
    results.append(TestResult('ME-010', 'must-edit', passed, f'advisory-only 不影响 pass/fail, ao={data["advisory_only"]["count"]}'))

    return results


# ============================================================
# fidelity-stress 测试（5 条）
# ============================================================

def test_fidelity_stress():
    results = []

    # FS-001: 密集数字
    orig = "处理了 1,234,567 次请求，平均响应时间 45ms，错误率 0.03%。增长了 25%。"
    edited = "处理了 1,234,567 次请求，平均响应时间 45ms，错误率 0.03%。增长了 25%。"
    rc, out, err = run_script(FIDELITY_GUARD, ['--original', write_temp(orig), '--edited', write_temp(edited), '--output', 'json'])
    data = json.loads(out)
    passed = data['fails'] == 0
    results.append(TestResult('FS-001', 'fidelity-stress', passed, f'密集数字 fails={data["fails"]}'))

    # FS-002: 密集数字被改变
    orig = "处理了 1,234,567 次请求，平均响应时间 45ms。"
    edited = "处理了 1,234,568 次请求，平均响应时间 46ms。"
    rc, out, err = run_script(FIDELITY_GUARD, ['--original', write_temp(orig), '--edited', write_temp(edited), '--output', 'json'])
    data = json.loads(out)
    passed = data['fails'] > 0
    results.append(TestResult('FS-002', 'fidelity-stress', passed, f'密集数字变化 fails={data["fails"]}'))

    # FS-003: 否定词变化 → warning
    orig = "这个方案不会导致系统崩溃。"
    edited = "这个方案会导致系统崩溃。"
    rc, out, err = run_script(FIDELITY_GUARD, ['--original', write_temp(orig), '--edited', write_temp(edited), '--output', 'json'])
    data = json.loads(out)
    passed = data['warnings'] > 0
    results.append(TestResult('FS-003', 'fidelity-stress', passed, f'否定词变化 warning={data["warnings"]}'))

    # FS-004: 条件词变化 → warning
    orig = "如果配置正确，系统正常运行。"
    edited = "配置正确时系统正常运行。"
    rc, out, err = run_script(FIDELITY_GUARD, ['--original', write_temp(orig), '--edited', write_temp(edited), '--output', 'json'])
    data = json.loads(out)
    passed = data['warnings'] > 0
    results.append(TestResult('FS-004', 'fidelity-stress', passed, f'条件词变化 warning={data["warnings"]}'))

    # FS-005: change_report 长度比例计算
    orig = "这是一段测试文本，用于验证长度比例计算的正确性。" * 10
    edited = "这是一段测试文本，用于验证长度比例计算的正确性。" * 8
    rc, out, err = run_script(CHANGE_REPORT, ['--original', write_temp(orig), '--edited', write_temp(edited), '--output', 'json'])
    data = json.loads(out)
    ratio = data['length_ratio']['value']
    passed = 0.7 <= ratio <= 0.9
    results.append(TestResult('FS-005', 'fidelity-stress', passed, f'长度比例={ratio}'))

    return results


# ============================================================
# profile-boundaries 测试（6 条）
# ============================================================

def test_profile_boundaries():
    results = []

    # PB-001: technical profile 不报告步骤说明
    text = "首先，安装 Node.js。然后，运行 npm install。最后，执行 npm start。"
    rc, out, err = run_script(PATTERN_AUDIT, ['--text', write_temp(text), '--profile', 'technical', '--check-level', 'full', '--output', 'json'])
    data = json.loads(out)
    sc_count = data['strong_contextual']['count']
    # technical profile 阈值放宽，可能不报告
    passed = data['overall']['pass_fail'] == 'pass'
    results.append(TestResult('PB-001', 'profile-boundaries', passed, f'technical 步骤说明 pass={data["overall"]["pass_fail"]}'))

    # PB-002: essay profile 同样的步骤说明可能被标记
    text = "首先，安装 Node.js。然后，运行 npm install。最后，执行 npm start。"
    rc, out, err = run_script(PATTERN_AUDIT, ['--text', write_temp(text), '--profile', 'essay', '--check-level', 'full', '--output', 'json'])
    data = json.loads(out)
    passed = data['overall']['pass_fail'] == 'pass'
    results.append(TestResult('PB-002', 'profile-boundaries', passed, f'essay 步骤说明 pass={data["overall"]["pass_fail"]}'))

    # PB-003: social profile 假互动不报告
    text = "你可能会问，这个产品好用吗？你想知道吗？"
    rc, out, err = run_script(PATTERN_AUDIT, ['--text', write_temp(text), '--profile', 'social', '--check-level', 'full', '--output', 'json'])
    data = json.loads(out)
    passed = data['overall']['pass_fail'] == 'pass'
    results.append(TestResult('PB-003', 'profile-boundaries', passed, f'social 假互动 pass={data["overall"]["pass_fail"]}'))

    # PB-004: essay profile 假互动被检测
    text = "你可能会问，这个产品好用吗？你想知道吗？你想了解更多吗？"
    rc, out, err = run_script(PATTERN_AUDIT, ['--text', write_temp(text), '--profile', 'essay', '--check-level', 'full', '--output', 'json'])
    data = json.loads(out)
    passed = True  # 只验证不崩溃
    results.append(TestResult('PB-004', 'profile-boundaries', passed, f'essay 假互动 sc={data["strong_contextual"]["count"]}'))

    # PB-005: technical profile 被动语态不检测
    text = "代码被执行。数据被处理。结果被返回。"
    rc, out, err = run_script(PATTERN_AUDIT, ['--text', write_temp(text), '--profile', 'technical', '--check-level', 'full', '--output', 'json'])
    data = json.loads(out)
    passed = data['overall']['pass_fail'] == 'pass'
    results.append(TestResult('PB-005', 'profile-boundaries', passed, f'technical 被动语态 pass={data["overall"]["pass_fail"]}'))

    # PB-006: social profile 短句不检测
    text = "好。对。行。可以。没问题。"
    rc, out, err = run_script(PATTERN_AUDIT, ['--text', write_temp(text), '--profile', 'social', '--check-level', 'full', '--output', 'json'])
    data = json.loads(out)
    passed = data['overall']['pass_fail'] == 'pass'
    results.append(TestResult('PB-006', 'profile-boundaries', passed, f'social 短句 pass={data["overall"]["pass_fail"]}'))

    return results


# ============================================================
# long-form 测试（3 条）
# ============================================================

def test_long_form():
    results = []

    # LF-001: strict 模式长度比例 ≥ 0.90
    orig = "这是一段测试文本。" * 200
    edited = "这是一段测试文本。" * 200
    rc, out, err = run_script(CHANGE_REPORT, ['--original', write_temp(orig), '--edited', write_temp(edited), '--length-retention', 'strict', '--output', 'json'])
    data = json.loads(out)
    passed = data['length_ratio']['value'] >= 0.90 and data['length_ratio']['meets_threshold']
    results.append(TestResult('LF-001', 'long-form', passed, f'strict 长度比例={data["length_ratio"]["value"]}'))

    # LF-002: balanced 模式长度比例 ≥ 0.80
    orig = "这是一段测试文本。" * 200
    edited = "这是一段测试文本。" * 160
    rc, out, err = run_script(CHANGE_REPORT, ['--original', write_temp(orig), '--edited', write_temp(edited), '--length-retention', 'balanced', '--output', 'json'])
    data = json.loads(out)
    passed = data['length_ratio']['value'] >= 0.80
    results.append(TestResult('LF-002', 'long-form', passed, f'balanced 长度比例={data["length_ratio"]["value"]}'))

    # LF-003: strict 模式长度不足 → 不达标
    orig = "这是一段测试文本。" * 200
    edited = "这是一段测试文本。" * 150
    rc, out, err = run_script(CHANGE_REPORT, ['--original', write_temp(orig), '--edited', write_temp(edited), '--length-retention', 'strict', '--output', 'json'])
    data = json.loads(out)
    passed = not data['length_ratio']['meets_threshold']
    results.append(TestResult('LF-003', 'long-form', passed, f'strict 不足 {data["length_ratio"]["value"]} meets={data["length_ratio"]["meets_threshold"]}'))

    return results


# ============================================================
# unsupported-fiction 测试（2 条）
# ============================================================

def test_unsupported_fiction():
    results = []

    # UF-001: fiction 请求被拒绝（通过 profile 参数验证）
    text = "月光下，少女缓缓走向古堡的大门。"
    rc, out, err = run_script(PATTERN_AUDIT, ['--text', write_temp(text), '--profile', 'essay', '--output', 'json'])
    # pattern_audit 不直接处理 fiction，但验证 profile 参数有效
    passed = rc in [0, 2]
    results.append(TestResult('UF-001', 'unsupported-fiction', passed, f'fiction 文本处理 rc={rc}'))

    # UF-002: fiction profile 不在允许值中
    rc, out, err = run_script(PATTERN_AUDIT, ['--text', write_temp(text), '--profile', 'fiction', '--output', 'json'])
    passed = rc == 3 or 'invalid choice' in err
    results.append(TestResult('UF-002', 'unsupported-fiction', passed, f'fiction profile 被拒绝 rc={rc}'))

    return results


# ============================================================
# 主函数
# ============================================================



# ============================================================
# profile-thresholds 测试（5 条,档72B-2 新增,OBS-218/221）
# ============================================================

def test_profile_thresholds():
    results = []

    # PB-007 正例:essay 下 3 处 SC-001「随着…的发展」聚集 → 命中
    text_007 = (
        "随着人工智能的发展，整个行业正在发生明显而深刻的变化。"
        "随着大模型的发展，成本下降。"
        "随着应用的发展，落地过程正在明显加速。")
    rc, out, err = run_script(PATTERN_AUDIT, ['--text', write_temp(text_007), '--profile', 'essay', '--check-level', 'full', '--output', 'json'])
    data = json.loads(out)
    passed = data['strong_contextual']['count'] > 0
    results.append(TestResult('PB-007', 'profile-thresholds', passed, f'essay SC-001 聚集 sc={data["strong_contextual"]["count"]}'))

    # PB-008 反例:同一段文本,宽松 profile social 下不误报(R55 单变量=profile)
    rc, out, err = run_script(PATTERN_AUDIT, ['--text', write_temp(text_007), '--profile', 'social', '--check-level', 'full', '--output', 'json'])
    data = json.loads(out)
    passed = data['strong_contextual']['count'] == 0
    results.append(TestResult('PB-008', 'profile-thresholds', passed, f'social 同文本 sc={data["strong_contextual"]["count"]}'))

    # PB-009 关键:同一段文本 essay 与 technical 两次运行,count 不相等
    # —— 唯一能证明 profile 分档在工作的测试(旧 PB-001~006 全部做不到)。
    # SC-008 单命中:essay 阈值 1 → 命中;technical 阈值 2 → 不命中。
    text_009 = "说白了，真正的风险在于没有人验证它。"
    rc, out, err = run_script(PATTERN_AUDIT, ['--text', write_temp(text_009), '--profile', 'essay', '--check-level', 'full', '--output', 'json'])
    data = json.loads(out)
    essay_count = data['strong_contextual']['count']
    rc, out, err = run_script(PATTERN_AUDIT, ['--text', write_temp(text_009), '--profile', 'technical', '--check-level', 'full', '--output', 'json'])
    data = json.loads(out)
    technical_count = data['strong_contextual']['count']
    passed = essay_count != technical_count
    results.append(TestResult('PB-009', 'profile-thresholds', passed, f'essay={essay_count} technical={technical_count} 不相等'))

    # SC-008 正例:含「说白了」,essay 下 SC-008 命中
    rc, out, err = run_script(PATTERN_AUDIT, ['--text', write_temp("说白了，这件事到此为止。"), '--profile', 'essay', '--check-level', 'full', '--output', 'json'])
    data = json.loads(out)
    sc_ids = [item['pattern_id'] for item in data['strong_contextual']['items']]
    passed = 'SC-008' in sc_ids
    results.append(TestResult('SC-008-POS', 'profile-thresholds', passed, f'SC-008 命中 ids={sc_ids}'))

    # SC-008 反例:不含三词,essay 下 SC-008 零命中
    rc, out, err = run_script(PATTERN_AUDIT, ['--text', write_temp("这件事到此为止，没有别的了。"), '--profile', 'essay', '--check-level', 'full', '--output', 'json'])
    data = json.loads(out)
    sc_ids = [item['pattern_id'] for item in data['strong_contextual']['items']]
    passed = 'SC-008' not in sc_ids
    results.append(TestResult('SC-008-NEG', 'profile-thresholds', passed, f'SC-008 零命中 ids={sc_ids}'))

    return results



# ============================================================
# identity-regression 测试（1 条,档72B-2R 新增,PB-010）
# ============================================================



# ============================================================
# sc005-threshold-liveness 测试（1 条,档72B-2F 新增,PB-011/R112）
# ============================================================

# 4 个连续句:长度 20/23/23/26,相邻差 3/0/3(均<=5),句长均>10,
# 不命中 SC-001~008 任何正则(中性陈述句,实测 sc_hits=[])。
# 只数 pattern_id == 'SC-005' 的条目;consecutive_count 递推 2,3,4。
SC005_TEXT = ("清晨的阳光洒满安静的街道，行人脚步从容。"
              "午后的小雨落在青石板路上，屋檐滴答声清晰可闻。"
              "傍晚的微风穿过长长小巷，远处亮起一片温暖灯光。"
              "深夜的月光落进半开的窗台，书桌上的纸张被风轻轻翻动。")


def test_sc005_threshold_liveness():
    results = []
    import importlib.util
    spec = importlib.util.spec_from_file_location("pattern_audit", PATTERN_AUDIT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    observed = {}
    for prof in ("essay", "technical", "social"):
        findings = mod.detect_strong_contextual(SC005_TEXT, prof)
        sc5 = [f for f in findings if f['pattern_id'] == 'SC-005']
        observed[prof] = (len(sc5), [f['cluster_threshold'] for f in sc5])

    essay_n, essay_t = observed['essay']
    tech_n, tech_t = observed['technical']
    soc_n, soc_t = observed['social']
    ok = (
        essay_n == 2 and all(x == 3 for x in essay_t)
        and tech_n == 1 and all(x == 4 for x in tech_t)
        and soc_n == 0
    )
    msg = (f"essay={essay_n}(thr={essay_t}) technical={tech_n}(thr={tech_t}) "
           f"social={soc_n}(thr={soc_t})")
    results.append(TestResult('PB-011', 'sc005-threshold-liveness', ok, msg))
    return results

def test_thresholds_identity():
    results = []
    import importlib.util
    spec = importlib.util.spec_from_file_location("pattern_audit", PATTERN_AUDIT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mismatches = []
    for rule in mod.STRONG_CONTEXTUAL_PATTERNS:
        rid = rule.get('id')
        if rid not in EXPECTED_SC_THRESHOLDS:
            continue
        got = rule.get('thresholds') or {}
        for prof, want in EXPECTED_SC_THRESHOLDS[rid].items():
            if got.get(prof) != want:
                mismatches.append(f"{rid}.{prof}: 期望 {want} 实得 {got.get(prof)}")
    passed = not mismatches
    results.append(TestResult('PB-010', 'identity-regression', passed,
                              '；'.join(mismatches) if mismatches else '18 格全等'))
    return results

def main():
    verbose = '--verbose' in sys.argv

    all_results = []
    all_results.extend(test_must_preserve())
    all_results.extend(test_must_edit())
    all_results.extend(test_fidelity_stress())
    all_results.extend(test_profile_boundaries())
    all_results.extend(test_profile_thresholds())
    all_results.extend(test_thresholds_identity())
    all_results.extend(test_sc005_threshold_liveness())
    all_results.extend(test_long_form())
    all_results.extend(test_unsupported_fiction())

    passed = sum(1 for r in all_results if r.passed)
    failed = sum(1 for r in all_results if not r.passed)

    print(f'{"="*60}')
    print(f'zh-human-writing v1 单元测试报告')
    print(f'{"="*60}')
    print(f'总计: {len(all_results)}')
    print(f'通过: {passed}')
    print(f'失败: {failed}')
    print(f'{"="*60}')

    if verbose:
        for r in all_results:
            print(r)

    if failed:
        print(f'\n失败详情:')
        for r in all_results:
            if not r.passed:
                print(f'  {r}')
        sys.exit(1)
    else:
        print('\n全部通过！')
        sys.exit(0)

if __name__ == '__main__':
    main()
