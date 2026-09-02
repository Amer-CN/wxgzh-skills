"""77T/OH1: 防御性回归钉子 — run_tests.run_script 子进程不变量。

只读断言 tests/run_tests.py 源码（不修改 run_tests.py 本身）：
1) subprocess.run 的命令构造为列表（cmd = [PYTHON, script] + args）；
2) 无 shell=True；
3) 无字符串拼接命令（os.system / f-string 或字面量直接传入 subprocess）。
"""
from __future__ import annotations

from pathlib import Path

RUN_TESTS = Path(__file__).resolve().parent / "run_tests.py"


def test_run_script_invariants():
    source = RUN_TESTS.read_text(encoding="utf-8")

    # ① cmd 构造为列表，且 subprocess.run 使用该列表变量
    assert "cmd = [PYTHON, script] + args" in source
    assert "subprocess.run(cmd," in source

    # ② 无 shell=True
    assert "shell=True" not in source

    # ③ 无字符串拼接命令：全文件唯一的 subprocess 调用就是上面的列表式调用
    assert source.count("subprocess.run(") == 1
    assert "os.system" not in source
    for bad in ('subprocess.run(f"', "subprocess.run(f'", 'subprocess.run("', "subprocess.run('"):
        assert bad not in source
