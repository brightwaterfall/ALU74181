# SPDX-FileCopyrightText: © 2026 gddwms
# SPDX-License-Identifier: Apache-2.0
"""Offline exhaustive checks (no iverilog required)."""

from golden_model import alu74181, logic_f, arith_f


def test_logic_all():
    for a in range(16):
        for b in range(16):
            for s in range(16):
                f, aeq, cn4_n = alu74181(a, b, s, m=1, cn_n=1)
                assert f == logic_f(a, b, s)
                assert aeq == (1 if f == 0xF else 0)
                assert cn4_n == 1


def test_add_all():
    for a in range(16):
        for b in range(16):
            for cn_n, cin in ((1, 0), (0, 1)):
                f, _, cn4_n = alu74181(a, b, 0b1001, m=0, cn_n=cn_n)
                exp_f, exp_c = arith_f(a, b, 0b1001, cin)
                assert f == exp_f
                assert cn4_n == (0 if exp_c else 1)


def test_sub_all():
    for a in range(16):
        for b in range(16):
            f, _, _ = alu74181(a, b, 0b0110, m=0, cn_n=0)
            exp_f, _ = arith_f(a, b, 0b0110, cin=1)
            assert f == exp_f


def test_known_vectors():
    # F = A
    assert alu74181(0xC, 0x3, 0b1111, 1, 1)[0] == 0xC
    # F = 0
    assert alu74181(0xA, 0x5, 0b0011, 1, 1)[0] == 0x0
    # 7 + 1 = 8
    assert alu74181(0x7, 0x1, 0b1001, 0, 1)[0] == 0x8
    # 7 + 1 + 1 = 9
    assert alu74181(0x7, 0x1, 0b1001, 0, 0)[0] == 0x9
    # AeqB when F=0xF
    assert alu74181(0x0, 0x0, 0b1100, 1, 1)[1] == 1
