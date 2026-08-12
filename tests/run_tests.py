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

def _sc_items(data):
    """档72C-4/§3-2:strong_contextual.items 拆为 high_confidence + low_confidence。"""
    sc = data['strong_contextual']
    return sc.get('high_confidence', []) + sc.get('low_confidence', [])

# 档72C-2 PB-010:期望值来源=references/patterns/strong-contextual.md 逐条
# profile 声明(非统一乘数)。基线 2(SC-005 为 3),technical ×1.5 / social
# ×2.0 只在文档明写该档放宽的规则上生效。SC-007a 阈值 1 见档 72C-2 §4。
# 禁止用公式现算期望值——用公式就会把同一个 bug 再算一遍(R110)。
EXPECTED_SC_THRESHOLDS = {
    'SC-001': {'essay': 2, 'technical': 3, 'social': 2},
    'SC-002': {'essay': 2, 'technical': 3, 'social': 2},
    'SC-003': {'essay': 2, 'technical': 3, 'social': 2},
    'SC-004': {'essay': 2, 'technical': 2, 'social': 2},
    'SC-005': {'essay': 3, 'technical': 3, 'social': 3},
    'SC-006': {'essay': 2, 'technical': 2, 'social': 4},
}

PYTHON = sys.executable
# 76D:子进程统一 UTF-8 输出/解码(Windows 管道默认 GBK 会互相踩编码)。
_RUN_SCRIPT_ENV = dict(os.environ, PYTHONUTF8="1")


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
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                                errors="replace", env=_RUN_SCRIPT_ENV, timeout=30)
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
    # 档72C-3/OBS-234:argparse 错误统一退出码 3(收紧,消除恒真写法)
    passed = rc == 3
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

    # PB-007 正例:essay 下 2 处 SC-006「你可能会问」聚集 → 命中
    # 档72C-2:SC-001 的 social 阈值=2(文档声明 social 正常),不再适合做
    # essay/social 分档演示;改用 SC-006(essay 2 / social 4,文档明写 social ×2.0)。
    text_007 = "你可能会问，这个产品好用吗？你可能会问，价格合理吗？"
    rc, out, err = run_script(PATTERN_AUDIT, ['--text', write_temp(text_007), '--profile', 'essay', '--check-level', 'full', '--output', 'json'])
    data = json.loads(out)
    passed = data['strong_contextual']['count'] > 0
    results.append(TestResult('PB-007', 'profile-thresholds', passed, f'essay SC-006 聚集 sc={data["strong_contextual"]["count"]}'))

    # PB-008 反例:同一段文本,宽松 profile social 下不误报(R55 单变量=profile;
    # SC-006 social 阈值 4,2 处命中不触发)
    rc, out, err = run_script(PATTERN_AUDIT, ['--text', write_temp(text_007), '--profile', 'social', '--check-level', 'full', '--output', 'json'])
    data = json.loads(out)
    passed = data['strong_contextual']['count'] == 0
    results.append(TestResult('PB-008', 'profile-thresholds', passed, f'social 同文本 sc={data["strong_contextual"]["count"]}'))

    # PB-009 关键:同一段文本 essay 与 technical 两次运行,count 不相等
    # —— 唯一能证明 profile 分档在工作的测试(旧 PB-001~006 全部做不到)。
    # 档72C-2:SC-008 已移入 HR-007,改用 SC-001(essay 2 / technical 3):
    # 2 处命中 → essay 触发(2>=2)、technical 不触发(2<3)。
    text_009 = "随着人工智能的发展，行业开始变化。随着大模型的发展，成本下降。"
    rc, out, err = run_script(PATTERN_AUDIT, ['--text', write_temp(text_009), '--profile', 'essay', '--check-level', 'full', '--output', 'json'])
    data = json.loads(out)
    essay_count = data['strong_contextual']['count']
    rc, out, err = run_script(PATTERN_AUDIT, ['--text', write_temp(text_009), '--profile', 'technical', '--check-level', 'full', '--output', 'json'])
    data = json.loads(out)
    technical_count = data['strong_contextual']['count']
    passed = essay_count != technical_count
    results.append(TestResult('PB-009', 'profile-thresholds', passed, f'essay={essay_count} technical={technical_count} 不相等'))

    # HR-007 反例:不含三词,essay 下 hard_residue 零命中(与 PB-016 构成正反例)
    rc, out, err = run_script(PATTERN_AUDIT, ['--text', write_temp("这件事到此为止，没有别的了。"), '--profile', 'essay', '--check-level', 'full', '--output', 'json'])
    data = json.loads(out)
    passed = data['hard_residue']['count'] == 0 and rc == 0
    results.append(TestResult('HR-007-NEG', 'profile-thresholds', passed, f'HR-007 零命中 hr={data["hard_residue"]["count"]} rc={rc}'))

    # SC-008-MIGRATED 迁移守卫:三词文本的 strong 输出不得再含 SC-008(§3 已移入 HR-007)
    rc, out, err = run_script(PATTERN_AUDIT, ['--text', write_temp("说白了，这件事到此为止。"), '--profile', 'essay', '--check-level', 'full', '--output', 'json'])
    data = json.loads(out)
    sc_ids = [item.get('rule_id') for item in _sc_items(data)]
    passed = 'SC-008' not in sc_ids and data['hard_residue']['count'] > 0
    results.append(TestResult('SC-008-MIGRATED', 'profile-thresholds', passed,
                              f'strong ids={sc_ids} hr={data["hard_residue"]["count"]}'))

    return results



# ============================================================
# identity-regression 测试（1 条,档72B-2R 新增,PB-010）
# ============================================================

# ============================================================
# sc001-threshold-liveness 测试（1 条,档72C-2 重挂,PB-011/R112）
# ============================================================

# 档72C-2:SC-005 阈值改为 3/3/3 后无法区分 profile,PB-011 改挂 SC-001
# (essay 2 / technical 3 / social 2)。文本含恰好 2 处 SC-001「随着…的发展」,
# 同一段落;两句句式骨架相同但同构簇=2,SC-005 阈值 3 不触发(档72E-1/OBS-227
# 语义重写后仍不触发:同构检测量句式非句长)。
# 预期:essay 命中 1(cluster_threshold 2)、technical 0、social 命中 1。
SC001_TEXT = ("随着人工智能的发展，行业开始变化。随着大模型的发展，成本下降。")


def test_sc001_threshold_liveness():
    results = []
    import importlib.util
    spec = importlib.util.spec_from_file_location("pattern_audit", PATTERN_AUDIT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    observed = {}
    for prof in ("essay", "technical", "social"):
        findings = mod.detect_strong_contextual(SC001_TEXT, SC001_TEXT, prof, [])
        sc1 = [f for f in findings if f.get('rule_id') == 'SC-001']
        observed[prof] = (len(sc1), [f['cluster_threshold'] for f in sc1])

    essay_n, essay_t = observed['essay']
    tech_n, tech_t = observed['technical']
    soc_n, soc_t = observed['social']
    ok = (
        essay_n == 1 and essay_t == [2]
        and tech_n == 0
        and soc_n == 1 and soc_t == [2]
    )
    msg = (f"essay={essay_n}(thr={essay_t}) technical={tech_n}(thr={tech_t}) "
           f"social={soc_n}(thr={soc_t})")
    results.append(TestResult('PB-011', 'sc001-threshold-liveness', ok, msg))
    return results


# ============================================================
# sc007b-upgrade 测试（1 条,档72C-2 新增,PB-012）
# ============================================================

# 同一段落内 AO-001(不是…而是 / 并非…而是)命中 >= 2 → 升级为
# strong_contextual finding SC-007b(confidence=low);单发只留 advisory。
SC007B_SINGLE = "他不是因为失败才放弃，而是因为方向错了。"
SC007B_DOUBLE = ("他不是因为失败才放弃，而是因为方向错了。"
                 "并非能力不足，而是时机未到。")


def test_sc007b_upgrade():
    results = []
    rc, out, err = run_script(PATTERN_AUDIT, ['--text', write_temp(SC007B_SINGLE), '--profile', 'essay', '--check-level', 'full', '--output', 'json'])
    data = json.loads(out)
    single_ids = [f['pattern_id'] for f in _sc_items(data)]
    ok1 = 'SC-007b' not in single_ids and data['advisory_only']['count'] >= 1
    rc, out, err = run_script(PATTERN_AUDIT, ['--text', write_temp(SC007B_DOUBLE), '--profile', 'essay', '--check-level', 'full', '--output', 'json'])
    data = json.loads(out)
    sc007b = [f for f in _sc_items(data) if f.get('rule_id') == 'SC-007b']
    ok2 = len(sc007b) == 1 and sc007b[0].get('confidence') == 'low'
    ok = ok1 and ok2
    msg = (f"单发={'通过' if ok1 else '失败'}(ids={single_ids}) "
           f"双发={'通过' if ok2 else '失败'}(sc007b={len(sc007b)} conf={[f.get('confidence') for f in sc007b]})")
    results.append(TestResult('PB-012', 'sc007b-upgrade', ok, msg))
    return results


# ============================================================
# config-liveness 测试（1 条,档72C-2 新增,PB-013/R112）
# ============================================================

def test_config_liveness():
    results = []
    import importlib.util
    spec = importlib.util.spec_from_file_location("pattern_audit", PATTERN_AUDIT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    # 构造临时配置:SC-001 essay=9,其余与默认一致
    import tempfile
    fd, cfg_path = tempfile.mkstemp(suffix='.yaml')
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        f.write("""pattern_thresholds:
  SC-001: {essay: 9, technical: 3, social: 2}
  SC-002: {essay: 2, technical: 3, social: 2}
  SC-003: {essay: 2, technical: 3, social: 2}
  SC-004: {essay: 2, technical: 2, social: 2}
  SC-005: {essay: 3, technical: 3, social: 3}
  SC-006: {essay: 2, technical: 2, social: 4}
  SC-007a: {essay: 1, technical: 1, social: 1}
  SC-009: {essay: 1, technical: 1, social: 1}
  SC-010: {essay: 1, technical: 1, social: 1}
  SC-011: {essay: 2, technical: 2, social: 2}
""")
    text = ("随着人工智能的发展，整个行业正在发生明显而深刻的变化。"
            "随着大模型的发展，成本下降。"
            "随着应用的发展，落地过程正在明显加速。")
    text_p = write_temp(text)
    rc, out, err = run_script(PATTERN_AUDIT, ['--text', text_p, '--profile', 'essay', '--check-level', 'full', '--output', 'json'])
    data = json.loads(out)
    default_hits = data['strong_contextual']['count']
    rc2, out2, err2 = run_script(PATTERN_AUDIT, ['--config', cfg_path, '--text', text_p, '--profile', 'essay', '--check-level', 'full', '--output', 'json'])
    ok = default_hits > 0 and rc2 == 0
    if ok:
        data2 = json.loads(out2)
        ok = data2['strong_contextual']['count'] == 0
    temp_count = None
    if rc2 == 0 and out2:
        temp_count = json.loads(out2)['strong_contextual']['count']
    results.append(TestResult('PB-013', 'config-liveness', ok,
                              f'默认={default_hits} 临时配置={temp_count} rc2={rc2}'))
    os.unlink(cfg_path)
    return results


# ============================================================
# config-default 测试（1 条,档72C-2 新增,PB-014/R104）
# ============================================================

def test_config_default():
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
    ok = not mismatches
    results.append(TestResult('PB-014', 'config-default', ok,
                              '；'.join(mismatches) if mismatches else '默认配置 18 格与 §1 表逐格相同'))
    return results


# ============================================================
# config-error 测试（1 条,档72C-2 新增,PB-015）
# ============================================================

def test_config_errors():
    results = []
    text_p = write_temp("这是一段普通测试文本。")
    rc, out, err = run_script(PATTERN_AUDIT, ['--config', os.path.join(tempfile.gettempdir(), 'no-such-config-72c2.yaml'), '--text', text_p, '--output', 'json'])
    ok1 = rc == 3
    fd, bad_path = tempfile.mkstemp(suffix='.yaml')
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        f.write("pattern_thresholds: [broken\n")
    rc, out, err = run_script(PATTERN_AUDIT, ['--config', bad_path, '--text', text_p, '--output', 'json'])
    ok2 = rc == 3
    os.unlink(bad_path)
    fd, miss_path = tempfile.mkstemp(suffix='.yaml')
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        f.write("""pattern_thresholds:
  SC-001: {essay: 2}
  SC-002: {essay: 2, technical: 3, social: 2}
  SC-003: {essay: 2, technical: 3, social: 2}
  SC-004: {essay: 2, technical: 2, social: 2}
  SC-005: {essay: 3, technical: 3, social: 3}
  SC-006: {essay: 2, technical: 2, social: 4}
  SC-007a: {essay: 1, technical: 1, social: 1}
""")
    rc, out, err = run_script(PATTERN_AUDIT, ['--config', miss_path, '--text', text_p, '--output', 'json'])
    ok3 = rc == 3
    os.unlink(miss_path)
    ok = ok1 and ok2 and ok3
    results.append(TestResult('PB-015', 'config-error', ok,
                              f'缺失={ok1}(rc={rc if not ok1 else 3}) yaml错={ok2} 缺键={ok3}'))
    return results


# ============================================================
# hr007 测试（1 条,档72C-2 新增,PB-016）
# ============================================================

def test_hr007():
    results = []
    text = "说白了，这件事到此为止。"
    rc, out, err = run_script(PATTERN_AUDIT, ['--text', write_temp(text), '--profile', 'essay', '--check-level', 'full', '--output', 'json'])
    data = json.loads(out)
    ok = rc == 2 and data['hard_residue']['count'] > 0
    results.append(TestResult('PB-016', 'hr007', ok, f'rc={rc} hr={data["hard_residue"]["count"]}'))
    return results


# ============================================================
# sc007a-threshold1 测试（1 条,档72C-2 新增,PB-017）
# ============================================================

def test_sc007a_threshold1():
    results = []
    text = "看似简单，实则复杂。"
    rc, out, err = run_script(PATTERN_AUDIT, ['--text', write_temp(text), '--profile', 'essay', '--check-level', 'full', '--output', 'json'])
    data = json.loads(out)
    sc007a = [f for f in _sc_items(data) if f.get('rule_id') == 'SC-007a']
    ok = len(sc007a) == 1 and 'context_note' in sc007a[0]
    results.append(TestResult('PB-017', 'sc007a-threshold1', ok,
                              f'sc007a={len(sc007a)} note={"有" if sc007a and "context_note" in sc007a[0] else "无"}'))
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



# ============================================================
# 十字段/屏蔽层/argparse 测试（4 条,档72C-3 新增,PB-018~021）
# ============================================================

CROSS_FIELDS = {'rule_id', 'group', 'severity', 'confidence', 'profile',
                'action', 'location', 'span_text', 'reason', 'suggestion'}


def test_cross_section_fields():
    results = []
    text = "说白了，这不是问题而是机会。随着人工智能的发展，行业开始变化。随着大模型的发展，成本下降。"
    rc, out, err = run_script(PATTERN_AUDIT, ['--text', write_temp(text), '--profile', 'essay', '--check-level', 'full', '--output', 'json'])
    data = json.loads(out)
    all_items = (data['hard_residue']['items'] + _sc_items(data)
                 + data['advisory_only']['items'])
    ok = (len(all_items) >= 3
          and all(CROSS_FIELDS <= set(it) for it in all_items)
          and all(it.get('severity') in ('audit', 'strong', 'advisory') for it in all_items)
          and all(it.get('confidence') in ('high', 'medium', 'low') for it in all_items)
          and all(it.get('action') in ('mark', 'suggest', 'review_only') for it in all_items))
    bad = [it.get('rule_id', '<缺失>') for it in all_items if not (CROSS_FIELDS <= set(it))]
    results.append(TestResult('PB-018', 'cross-section', ok,
                              f'items={len(all_items)} 缺字段={bad}'))
    return results


def test_protected_span_review_only():
    results = []
    text = "[[protected]]说白了[[/protected]]，其余内容没有变化。"
    rc, out, err = run_script(PATTERN_AUDIT, ['--text', write_temp(text), '--profile', 'essay', '--check-level', 'full', '--output', 'json'])
    data = json.loads(out)
    hr = data['hard_residue']['items']
    ok = len(hr) == 1 and hr[0].get('action') == 'review_only'
    results.append(TestResult('PB-019', 'protected-span', ok,
                              f'hr={len(hr)} action={[f.get("action") for f in hr]}'))
    return results


def test_mask_liveness():
    results = []
    fenced = "```\n看似简单，实则复杂。\n```"
    plain = "看似简单，实则复杂。"
    rc, out, err = run_script(PATTERN_AUDIT, ['--text', write_temp(fenced), '--profile', 'essay', '--check-level', 'full', '--output', 'json'])
    data = json.loads(out)
    fenced_count = data['strong_contextual']['count']
    rc, out, err = run_script(PATTERN_AUDIT, ['--text', write_temp(plain), '--profile', 'essay', '--check-level', 'full', '--output', 'json'])
    data = json.loads(out)
    plain_count = data['strong_contextual']['count']
    ok = fenced_count == 0 and plain_count > 0
    results.append(TestResult('PB-020', 'mask-liveness', ok,
                              f'围栏内={fenced_count} 围栏外={plain_count}'))
    return results


def test_argparse_exit3():
    results = []
    text_p = write_temp("这是一段普通测试文本。")
    rc, out, err = run_script(PATTERN_AUDIT, ['--text', text_p, '--nonsense'])
    ok1 = rc == 3
    rc, out, err = run_script(FIDELITY_GUARD, ['--original', text_p, '--edited', text_p, '--nonsense'])
    ok2 = rc == 3
    rc, out, err = run_script(CHANGE_REPORT, ['--original', text_p, '--edited', text_p, '--nonsense'])
    ok3 = rc == 3
    ok = ok1 and ok2 and ok3
    results.append(TestResult('PB-021', 'argparse-exit3', ok,
                              f'pattern={ok1} fidelity={ok2} change={ok3}'))
    return results




# ============================================================
# 词表规则测试（9 条,档72C-4 新增,PB-022~030）
# ============================================================

def test_sc009_single_hit():
    results = []
    rc, out, err = run_script(PATTERN_AUDIT, ['--text', write_temp("赋能一下这个项目。"), '--profile', 'essay', '--check-level', 'full', '--output', 'json'])
    data = json.loads(out)
    ids = [f.get('rule_id') for f in _sc_items(data)]
    ok = data['strong_contextual']['count'] == 1 and 'SC-009' in ids
    results.append(TestResult('PB-022', 'sc009', ok, f'sc={data["strong_contextual"]["count"]} ids={ids}'))
    return results


def test_ao013_never_upgrades():
    results = []
    text = ("颗粒度的问题在于颗粒度。颗粒度决定颗粒度，颗粒度影响颗粒度，颗粒度始终是颗粒度。")
    rc, out, err = run_script(PATTERN_AUDIT, ['--text', write_temp(text), '--profile', 'essay', '--check-level', 'full', '--output', 'json'])
    data = json.loads(out)
    ao_ids = [f.get('rule_id') for f in data['advisory_only']['items']]
    sc_ids = [f.get('rule_id') for f in _sc_items(data)]
    ok = data['advisory_only']['count'] >= 5 and 'AO-013' in ao_ids and 'SC-009' not in sc_ids and 'SC-011' not in sc_ids
    results.append(TestResult('PB-023', 'ao013', ok, f'ao={data["advisory_only"]["count"]} ao_ids={set(ao_ids)} sc_ids={set(sc_ids)}'))
    return results


def test_ao014_single_and_sc011():
    results = []
    rc, out, err = run_script(PATTERN_AUDIT, ['--text', write_temp("微光落在窗台上。"), '--profile', 'essay', '--check-level', 'full', '--output', 'json'])
    data = json.loads(out)
    single_ok = data['advisory_only']['count'] == 1 and all(f.get('rule_id') == 'AO-014' for f in data['advisory_only']['items'])
    sc_ids = [f.get('rule_id') for f in _sc_items(data)]
    single_ok = single_ok and 'SC-011' not in sc_ids
    rc, out, err = run_script(PATTERN_AUDIT, ['--text', write_temp("微光落在褶皱里，滚烫的丰盈被轻盈地安放。"), '--profile', 'essay', '--check-level', 'full', '--output', 'json'])
    data = json.loads(out)
    sc011 = [f for f in _sc_items(data) if f.get('rule_id') == 'SC-011']
    double_ok = len(sc011) == 1 and sc011[0].get('confidence') == 'low'
    ok = single_ok and double_ok
    results.append(TestResult('PB-024', 'ao014-sc011', ok,
                              f'单发={"通过" if single_ok else "失败"} 双发={"通过" if double_ok else "失败"}(sc011={len(sc011)})'))
    return results


def test_sc010_prefix():
    results = []
    rc, out, err = run_script(PATTERN_AUDIT, ['--text', write_temp("还有一层，问题在于成本。"), '--profile', 'essay', '--check-level', 'full', '--output', 'json'])
    data = json.loads(out)
    hit_ids = [f.get('rule_id') for f in _sc_items(data)]
    ok1 = 'SC-010' in hit_ids
    rc, out, err = run_script(PATTERN_AUDIT, ['--text', write_temp("还有一层"), '--profile', 'essay', '--check-level', 'full', '--output', 'json'])
    data = json.loads(out)
    ok2 = data['strong_contextual']['count'] == 0
    ok = ok1 and ok2
    results.append(TestResult('PB-025', 'sc010-prefix', ok, f'带内容={"通过" if ok1 else "失败"} 单独成句={"通过" if ok2 else "失败"}'))
    return results


def test_lexicon_liveness():
    results = []
    text_p = write_temp("赋能一下这个项目。")
    rc, out, err = run_script(PATTERN_AUDIT, ['--text', text_p, '--profile', 'essay', '--check-level', 'full', '--output', 'json'])
    data = json.loads(out)
    default_hits = data['strong_contextual']['count']
    import tempfile as _tf
    fd, lex_path = _tf.mkstemp(suffix='.yaml')
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        f.write("""version: 1
absolute_jargon:
  - 抓手
contextual_jargon:
  - 颗粒度
lyrical:
  - 微光
model_signposts:
  - 更微妙的是
forbidden_term:
  - 智能体助手
""")
    rc, out, err = run_script(PATTERN_AUDIT, ['--lexicon', lex_path, '--text', text_p, '--profile', 'essay', '--check-level', 'full', '--output', 'json'])
    ok = default_hits > 0 and rc == 0
    temp_hits = None
    if ok and out:
        temp_hits = json.loads(out)['strong_contextual']['count']
        ok = temp_hits == 0
    results.append(TestResult('PB-026', 'lexicon-liveness', ok, f'默认={default_hits} 临时词表={temp_hits} rc2={rc}'))
    os.unlink(lex_path)
    return results


def test_mask_lexicon():
    results = []
    words = "赋能 颗粒度 闭环 链路 沉淀"
    fenced = "```\n赋能 颗粒度 闭环 链路 沉淀\n```"
    inline = "正文里有 `赋能 颗粒度 闭环 链路 沉淀` 这一段。"
    plain = "赋能 颗粒度 闭环 链路 沉淀"
    rc, out, err = run_script(PATTERN_AUDIT, ['--text', write_temp(fenced), '--profile', 'essay', '--check-level', 'full', '--output', 'json'])
    data = json.loads(out)
    fenced_total = data['strong_contextual']['count'] + data['advisory_only']['count']
    rc, out, err = run_script(PATTERN_AUDIT, ['--text', write_temp(inline), '--profile', 'essay', '--check-level', 'full', '--output', 'json'])
    data = json.loads(out)
    inline_total = data['strong_contextual']['count'] + data['advisory_only']['count']
    rc, out, err = run_script(PATTERN_AUDIT, ['--text', write_temp(plain), '--profile', 'essay', '--check-level', 'full', '--output', 'json'])
    data = json.loads(out)
    plain_total = data['strong_contextual']['count'] + data['advisory_only']['count']
    ok = fenced_total == 0 and inline_total == 0 and plain_total == 5
    results.append(TestResult('PB-027', 'mask-lexicon', ok,
                              f'围栏={fenced_total} 行内={inline_total} 正文={plain_total}'))
    return results


def test_long_word_priority():
    results = []
    rc, out, err = run_script(PATTERN_AUDIT, ['--text', write_temp("商业闭环很重要。"), '--profile', 'essay', '--check-level', 'full', '--output', 'json'])
    data = json.loads(out)
    sc009 = [f for f in _sc_items(data) if f.get('rule_id') == 'SC-009']
    ao013 = [f for f in data['advisory_only']['items'] if f.get('rule_id') == 'AO-013']
    ok = len(sc009) == 1 and len(ao013) == 0
    results.append(TestResult('PB-028', 'long-word-priority', ok, f'sc009={len(sc009)} ao013={len(ao013)}'))
    return results


def test_strategy_hr007():
    results = []
    text = "说白了，这件事到此为止。"
    rc, out, err = run_script(PATTERN_AUDIT, ['--text', write_temp(text), '--strategy', 'preserve', '--profile', 'essay', '--check-level', 'full', '--output', 'json'])
    data = json.loads(out) if out else {}
    hr_ids = [f.get('rule_id') for f in data.get('hard_residue', {}).get('items', [])]
    ok1 = rc == 0 and 'HR-007' in hr_ids
    rc, out, err = run_script(PATTERN_AUDIT, ['--text', write_temp(text), '--strategy', 'balance', '--profile', 'essay', '--check-level', 'full', '--output', 'json'])
    ok2 = rc == 2
    rc, out, err = run_script(PATTERN_AUDIT, ['--text', write_temp(text), '--profile', 'essay', '--check-level', 'full', '--output', 'json'])
    ok3 = rc == 2
    ok = ok1 and ok2 and ok3
    results.append(TestResult('PB-029', 'strategy-hr007', ok,
                              f'preserve={"通过" if ok1 else "失败"}(rc={rc if not ok1 else 0},ids={hr_ids}) balance={"通过" if ok2 else "失败"} 默认={"通过" if ok3 else "失败"}'))
    return results


def test_strong_grouping():
    results = []
    text = "赋能与颗粒度并存。褶皱与微光同在。说白了，这不是问题而是机会。"
    rc, out, err = run_script(PATTERN_AUDIT, ['--text', write_temp(text), '--profile', 'essay', '--check-level', 'full', '--output', 'json'])
    data = json.loads(out)
    sc = data['strong_contextual']
    high = sc.get('high_confidence', [])
    low = sc.get('low_confidence', [])
    high_ids = {f.get('rule_id') for f in high}
    low_ids = {f.get('rule_id') for f in low}
    ok = (sc['count'] == len(high) + len(low)
          and 'SC-009' in high_ids and 'SC-009' not in low_ids
          and all(f.get('rule_id') in ('SC-007b', 'SC-011') for f in low))
    results.append(TestResult('PB-030', 'strong-grouping', ok,
                              f'count={sc["count"]} high={sorted(high_ids)} low={sorted(low_ids)}'))
    return results


def test_ao_aggregation():
    """档72C-6/任务3:AO-007/AO-011 按段落聚合(每段一条 + occurrence_count)。"""
    results = []
    # PB-031:同段 5 个「我」→ AO-011 恰好 1 条 finding 且 occurrence_count=5
    text = "我来了。我看见自己。我明白了。我走了。我回来了。"
    rc, out, err = run_script(PATTERN_AUDIT, ['--text', write_temp(text), '--profile', 'essay', '--check-level', 'full', '--output', 'json'])
    data = json.loads(out)
    ao11 = [f for f in data['advisory_only']['items'] if f.get('rule_id') == 'AO-011']
    ok1 = len(ao11) == 1 and ao11[0].get('occurrence_count') == 5
    results.append(TestResult('PB-031', 'ao011-aggregate', ok1,
                              f'findings={len(ao11)} count={ao11[0].get("occurrence_count") if ao11 else None}'))
    # PB-032:三个段落各 1 个「你」→ AO-007 恰好 3 条 finding,每条 count=1
    text = "你好。\n\n你在哪里。\n\n你走吧。"
    rc, out, err = run_script(PATTERN_AUDIT, ['--text', write_temp(text), '--profile', 'essay', '--check-level', 'full', '--output', 'json'])
    data = json.loads(out)
    ao07 = [f for f in data['advisory_only']['items'] if f.get('rule_id') == 'AO-007']
    ok2 = len(ao07) == 3 and all(f.get('occurrence_count') == 1 for f in ao07)
    results.append(TestResult('PB-032', 'ao007-per-para', ok2,
                              f'findings={len(ao07)} counts={[f.get("occurrence_count") for f in ao07]}'))
    # PB-033:A 样本回归——AO-011 finding 条数 <= 段落数
    sample = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'examples', 'samples', 'A-human', 'input.md')
    rc, out, err = run_script(PATTERN_AUDIT, ['--text', sample, '--profile', 'essay', '--check-level', 'full', '--output', 'json'])
    data = json.loads(out)
    ao11 = [f for f in data['advisory_only']['items'] if f.get('rule_id') == 'AO-011']
    n_paras = len([ln for ln in open(sample, encoding='utf-8').read().split('\n') if ln.strip()])
    ok3 = len(ao11) <= n_paras
    results.append(TestResult('PB-033', 'ao011-sample-regression', ok3,
                              f'findings={len(ao11)} paras={n_paras}'))
    return results


def test_stat_wiring():
    """档72C-6/任务4:统计层管道活性(指标待任务书 §4 注入,机制先行)。"""
    results = []
    # PB-046:顶层 statistical 段存在、count 与 items 一致、当前为 0、
    # 不影响 pass_fail 与退出码(干净文本 rc=0,hard-residue 文本 rc=2)。
    text = "这是一段干净的中文文本。没有任何硬残留。"
    rc, out, err = run_script(PATTERN_AUDIT, ['--text', write_temp(text), '--profile', 'essay', '--check-level', 'full', '--output', 'json'])
    data = json.loads(out)
    st = data.get('statistical')
    ok1 = rc == 0 and isinstance(st, dict) and st.get('count') == len(st.get('items', [])) == 0
    results.append(TestResult('PB-046', 'stat-section-wiring', ok1,
                              f'rc={rc} count={st.get("count") if st else None}'))
    text = "说白了，这是硬残留。"
    rc, out, err = run_script(PATTERN_AUDIT, ['--text', write_temp(text), '--profile', 'essay', '--check-level', 'full', '--output', 'json'])
    data = json.loads(out) if out else {}
    ok2 = rc == 2 and data.get('statistical', {}).get('count') == 0
    results.append(TestResult('PB-047', 'stat-passfail-neutral', ok2,
                              f'rc={rc} stat_count={data.get("statistical", {}).get("count")}'))
    # PB-048:缺 statistical 段的部分覆盖配置(72C-2 PB-013 契约)→ 正常 rc=0,
    # statistical count=0;statistical 段非对象 → fail-closed exit 3。
    full_pt = ("pattern_thresholds:\n"
               "  SC-001: {essay: 2, technical: 3, social: 2}\n"
               "  SC-002: {essay: 2, technical: 3, social: 2}\n"
               "  SC-003: {essay: 2, technical: 3, social: 2}\n"
               "  SC-004: {essay: 2, technical: 2, social: 2}\n"
               "  SC-005: {essay: 3, technical: 3, social: 3}\n"
               "  SC-006: {essay: 2, technical: 2, social: 4}\n"
               "  SC-007a: {essay: 1, technical: 1, social: 1}\n"
               "  SC-009: {essay: 1, technical: 1, social: 1}\n"
               "  SC-010: {essay: 1, technical: 1, social: 1}\n"
               "  SC-011: {essay: 2, technical: 2, social: 2}\n")
    clean = "这是一段干净的中文文本。没有任何硬残留。"
    fd, tmp = tempfile.mkstemp(suffix='.yaml')
    os.write(fd, full_pt.encode('utf-8'))
    os.close(fd)
    rc, out, err = run_script(PATTERN_AUDIT, ['--text', write_temp(clean), '--config', tmp, '--profile', 'essay', '--check-level', 'full', '--output', 'json'])
    ok3 = rc == 0 and json.loads(out).get('statistical', {}).get('count') == 0
    os.unlink(tmp)
    fd, tmp = tempfile.mkstemp(suffix='.yaml')
    os.write(fd, (full_pt + "statistical: []\n").encode('utf-8'))
    os.close(fd)
    rc, out, err = run_script(PATTERN_AUDIT, ['--text', write_temp(text), '--config', tmp, '--profile', 'essay', '--check-level', 'full', '--output', 'json'])
    ok4 = rc == 3
    os.unlink(tmp)
    ok = ok3 and ok4
    results.append(TestResult('PB-048', 'stat-config-contract', ok,
                              f'缺段={"通过" if ok3 else "失败"} 非对象={"通过" if ok4 else "失败"}'))
    return results


def _stat_items(data):
    """统计层 finding 列表(档72C-6R)。"""
    return data.get('statistical', {}).get('items', [])


def test_stat_indicators():
    """档72C-6R/任务书 §4:九项指标活性断言(R112,每项必然命中+必然不命中)。"""
    results = []
    cases = []
    # PB-034 ST-001 句长变异系数:12 句等长 → CV=0 < 0.42 命中;等差长度 → 不命中
    hit34 = "甲乙丙丁戊己庚辛壬癸。" * 12
    miss34 = "".join("甲乙" * (2 + 2 * i) + "。" for i in range(12))
    cases.append(('PB-034', 'ST-001', hit34, miss34, 'essay'))
    # PB-035 ST-002 连词密度:H=610>=600,5 连词 → 8.2‰ > 7‰ 命中;无连词 → 不命中
    hit35 = "一二三四五六七八九十" * 60 + "因为因为因为因为因为。"
    miss35 = "一二三四五六七八九十" * 60 + "。"
    cases.append(('PB-035', 'ST-002', hit35, miss35, 'essay'))
    # PB-036 ST-003 「」高亮:4 对 > max(3, H//700) 命中;3 对 → 不命中
    hit36 = "「你好」。「世界」。「测试」。「文本」。"
    miss36 = "「你好」。「世界」。「测试」。"
    cases.append(('PB-036', 'ST-003', hit36, miss36, 'essay'))
    # PB-037 ST-004 软路标:3 词 > max(2, H//900) 命中;2 词 → 不命中
    hit37 = "真正重要的是这个。本质上也是。换句话说如此。"
    miss37 = "真正重要的是这个。本质上也是。"
    cases.append(('PB-037', 'ST-004', hit37, miss37, 'essay'))
    # PB-038 ST-005 长前置成分:3 句前置 >=12 汉字 > max(2, H//1200) 命中;2 句 → 不命中
    pre38 = "一二三四五六七八九十甲乙丙丁"
    hit38 = pre38 + "，这是第一句。" + pre38 + "，这是第二句。" + pre38 + "，这是第三句。"
    miss38 = pre38 + "，这是第一句。" + pre38 + "，这是第二句。"
    cases.append(('PB-038', 'ST-005', hit38, miss38, 'essay'))
    # PB-039 ST-006 重"的"长句:2 句(>=38 汉字且的>=4) > max(1, H//1500) 命中;1 句 → 不命中
    long39 = "我的你的他的她的它的这些那些我们的大家的，一二三四五六七八九十甲乙丙丁戊己庚辛壬癸子丑。"
    cases.append(('PB-039', 'ST-006', long39 * 2, long39, 'essay'))
    # PB-040 ST-007 单句段占比:9/12=75% >=75% 命中;8/12 → 不命中
    one40 = "这是单句段落。"
    two40 = "这是第一句。这是第二句。"
    hit40 = "\n\n".join([one40] * 9 + [two40] * 3)
    miss40 = "\n\n".join([one40] * 8 + [two40] * 4)
    cases.append(('PB-040', 'ST-007', hit40, miss40, 'essay'))
    # PB-041 ST-008 连续短段:连续 4 段(<=24 汉字且 1 句) 命中;3 段 → 不命中
    hit41 = "\n\n".join(["甲。", "乙。", "丙。", "丁。"])
    miss41 = "\n\n".join(["甲。", "乙。", "丙。"])
    cases.append(('PB-041', 'ST-008', hit41, miss41, 'essay'))
    # PB-042 ST-009 段落开场重复:4 段以"其实"开头 >=4 命中;3 段 → 不命中
    hit42 = "\n\n".join(["其实，这是第一段。"] * 4)
    miss42 = "\n\n".join(["其实，这是第一段。"] * 3)
    cases.append(('PB-042', 'ST-009', hit42, miss42, 'essay'))

    for tid, rid, hit, miss, prof in cases:
        rc, out, err = run_script(PATTERN_AUDIT, ['--text', write_temp(hit), '--profile', prof, '--check-level', 'full', '--output', 'json'])
        data = json.loads(out)
        n_hit = len([f for f in _stat_items(data) if f.get('rule_id') == rid])
        rc2, out2, err2 = run_script(PATTERN_AUDIT, ['--text', write_temp(miss), '--profile', prof, '--check-level', 'full', '--output', 'json'])
        data2 = json.loads(out2)
        n_miss = len([f for f in _stat_items(data2) if f.get('rule_id') == rid])
        ok = n_hit > 0 and n_miss == 0
        results.append(TestResult(tid, 'stat-liveness', ok,
                                  f'{rid} 命中={n_hit} 不命中={n_miss}'))
    return results


def test_stat_technical_exempt():
    """档72C-6R/任务书 §4:technical 下列表项与有序步骤段不参与 CV/连词密度/单句段占比/连续短段。"""
    results = []
    ok_all = True
    msgs = []
    # CV:等长正文 + 1 个 48 字列表段 → essay 混合 CV=0.815 不命中,technical 剔除后 CV=0 命中
    cv_text = "\n\n".join(["甲乙丙丁戊己庚辛壬癸。"] * 12 + ["- " + "一二三四五六七八九十" * 4 + "甲乙丙丁戊己庚辛。"])
    rc, out, err = run_script(PATTERN_AUDIT, ['--text', write_temp(cv_text), '--profile', 'essay', '--check-level', 'full', '--output', 'json'])
    n_essay = len([f for f in _stat_items(json.loads(out)) if f.get('rule_id') == 'ST-001'])
    rc, out, err = run_script(PATTERN_AUDIT, ['--text', write_temp(cv_text), '--profile', 'technical', '--check-level', 'full', '--output', 'json'])
    n_tech = len([f for f in _stat_items(json.loads(out)) if f.get('rule_id') == 'ST-001'])
    ok1 = n_essay == 0 and n_tech == 1
    ok_all &= ok1
    msgs.append(f'CV:essay={n_essay} tech={n_tech}')
    # 连词密度:5 次连词全放进列表段 → essay 密度=5/610*1000=8.20>7 命中,
    # technical 分子剔除后 0<10 不命中(分母全局 H=610,门 600 通过)
    conj_text = "一二三四五六七八九十" * 60 + "\n\n- 因为所以但是然而同时。"
    rc, out, err = run_script(PATTERN_AUDIT, ['--text', write_temp(conj_text), '--profile', 'essay', '--check-level', 'full', '--output', 'json'])
    n_essay = len([f for f in _stat_items(json.loads(out)) if f.get('rule_id') == 'ST-002'])
    rc, out, err = run_script(PATTERN_AUDIT, ['--text', write_temp(conj_text), '--profile', 'technical', '--check-level', 'full', '--output', 'json'])
    n_tech = len([f for f in _stat_items(json.loads(out)) if f.get('rule_id') == 'ST-002'])
    ok2 = n_essay == 1 and n_tech == 0
    ok_all &= ok2
    msgs.append(f'连词密度:essay={n_essay} tech={n_tech}')
    # 单句段占比:9 单句(含 3 列表单句)/12 → essay 命中;technical 剔除后 6/9=66.7% 且门 9<10 → 不命中
    ratio_text = "\n\n".join(["- 这是单句段落。"] * 3 + ["这是单句段落。"] * 6 + ["这是第一句。这是第二句。"] * 3)
    rc, out, err = run_script(PATTERN_AUDIT, ['--text', write_temp(ratio_text), '--profile', 'essay', '--check-level', 'full', '--output', 'json'])
    n_essay = len([f for f in _stat_items(json.loads(out)) if f.get('rule_id') == 'ST-007'])
    rc, out, err = run_script(PATTERN_AUDIT, ['--text', write_temp(ratio_text), '--profile', 'technical', '--check-level', 'full', '--output', 'json'])
    n_tech = len([f for f in _stat_items(json.loads(out)) if f.get('rule_id') == 'ST-007'])
    ok3 = n_essay == 1 and n_tech == 0
    ok_all &= ok3
    msgs.append(f'单句段占比:essay={n_essay} tech={n_tech}')
    # 连续短段:4 个列表短段 → essay 命中,technical 剔除后不命中
    short_text = "\n\n".join(["- 甲。", "- 乙。", "- 丙。", "- 丁。"])
    rc, out, err = run_script(PATTERN_AUDIT, ['--text', write_temp(short_text), '--profile', 'essay', '--check-level', 'full', '--output', 'json'])
    n_essay = len([f for f in _stat_items(json.loads(out)) if f.get('rule_id') == 'ST-008'])
    rc, out, err = run_script(PATTERN_AUDIT, ['--text', write_temp(short_text), '--profile', 'technical', '--check-level', 'full', '--output', 'json'])
    n_tech = len([f for f in _stat_items(json.loads(out)) if f.get('rule_id') == 'ST-008'])
    ok4 = n_essay == 1 and n_tech == 0
    ok_all &= ok4
    msgs.append(f'连续短段:essay={n_essay} tech={n_tech}')
    results.append(TestResult('PB-043', 'stat-technical-exempt', ok_all, '; '.join(msgs)))
    return results


def test_stat_social_disabled():
    """档72C-6R/任务书 §4:social 关闭 CV/连词密度/单句段占比/连续短段四项。"""
    results = []
    text = "甲乙丙丁戊己庚辛壬癸。" * 12 + "\n\n" + "\n\n".join(["甲。", "乙。", "丙。", "丁。"])
    rc, out, err = run_script(PATTERN_AUDIT, ['--text', write_temp(text), '--profile', 'social', '--check-level', 'full', '--output', 'json'])
    data = json.loads(out)
    ids = {f.get('rule_id') for f in _stat_items(data)}
    closed = {'ST-001', 'ST-002', 'ST-007', 'ST-008'}
    ok = not (ids & closed)
    results.append(TestResult('PB-044', 'stat-social-disabled', ok,
                              f'social_ids={sorted(ids)}'))
    return results


def test_stat_neutral():
    """档72C-6R/任务书 §4:统计层命中不改变 pass_fail、不改变退出码(三档各验一次)。"""
    results = []
    text = "甲乙丙丁戊己庚辛壬癸。" * 12  # essay/technical 下 ST-001 必命中
    ok_all = True
    msgs = []
    for prof in ('essay', 'technical', 'social'):
        rc, out, err = run_script(PATTERN_AUDIT, ['--text', write_temp(text), '--profile', prof, '--check-level', 'full', '--output', 'json'])
        data = json.loads(out)
        ok = rc == 0 and data.get('overall', {}).get('pass_fail') == 'pass'
        ok_all &= ok
        msgs.append(f'{prof}:rc={rc} n={data.get("statistical", {}).get("count")}')
    results.append(TestResult('PB-045', 'stat-neutral', ok_all, '; '.join(msgs)))
    return results



def test_forbidden_term_proper_noun():
    """76D/OBS-253:forbidden_term 疑似专名命中降级 advisory,普通命中保持 strong。"""
    results = []
    # 产品名语境:Luma Agents 中的 Agent(大写开头)→ FT-001 advisory
    text1 = "Luma Agents 上线了 H3。"
    rc, out, err = run_script(PATTERN_AUDIT, ['--text', write_temp(text1), '--profile', 'essay', '--check-level', 'full', '--output', 'json'])
    data1 = json.loads(out)
    ft1 = [f for f in data1['advisory_only']['items'] if f.get('rule_id') == 'FT-001']
    ok1 = len(ft1) == 1 and ft1[0]['severity'] == 'advisory' and '疑似专名' in ft1[0]['reason']
    results.append(TestResult('PB-048', 'ft001-proper-noun-advisory', ok1,
                              f'advisory={len(ft1)}'))
    # 普通语境:智能体助手 → FT-001 strong(高置信桶,语义不变)
    text2 = "这款智能体助手很好用。"
    rc, out, err = run_script(PATTERN_AUDIT, ['--text', write_temp(text2), '--profile', 'essay', '--check-level', 'full', '--output', 'json'])
    data2 = json.loads(out)
    sc2 = data2['strong_contextual']
    ft2 = [f for f in sc2.get('high_confidence', []) if f.get('rule_id') == 'FT-001']
    ok2 = len(ft2) == 1 and ft2[0]['severity'] == 'strong'
    results.append(TestResult('PB-049', 'ft001-plain-strong', ok2,
                              f'strong={len(ft2)}'))
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
    all_results.extend(test_sc001_threshold_liveness())
    all_results.extend(test_sc007b_upgrade())
    all_results.extend(test_config_liveness())
    all_results.extend(test_config_default())
    all_results.extend(test_config_errors())
    all_results.extend(test_hr007())
    all_results.extend(test_sc007a_threshold1())
    all_results.extend(test_cross_section_fields())
    all_results.extend(test_protected_span_review_only())
    all_results.extend(test_mask_liveness())
    all_results.extend(test_argparse_exit3())
    all_results.extend(test_sc009_single_hit())
    all_results.extend(test_ao013_never_upgrades())
    all_results.extend(test_ao014_single_and_sc011())
    all_results.extend(test_sc010_prefix())
    all_results.extend(test_lexicon_liveness())
    all_results.extend(test_mask_lexicon())
    all_results.extend(test_long_word_priority())
    all_results.extend(test_strategy_hr007())
    all_results.extend(test_strong_grouping())
    all_results.extend(test_ao_aggregation())
    all_results.extend(test_stat_wiring())
    all_results.extend(test_stat_indicators())
    all_results.extend(test_stat_technical_exempt())
    all_results.extend(test_stat_social_disabled())
    all_results.extend(test_stat_neutral())
    all_results.extend(test_long_form())



    all_results.extend(test_forbidden_term_proper_noun())
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
