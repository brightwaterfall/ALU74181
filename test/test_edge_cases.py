# SPDX-FileCopyrightText: © 2026 brightwaterfall
# SPDX-License-Identifier: Apache-2.0
"""Exceptional / corner-case checks for the 74181 model + wrapper assumptions."""

from golden_model import alu74181, arith_f


def test_underflow_wrap_rows():
    # S=0111, cin=0: (A&~B)-1 with A&~B==0 wraps to 0xF, cout=1 in 5-bit
    f, _, cn4_n = alu74181(0x0, 0xF, 0b0111, m=0, cn_n=1)
    exp_f, exp_c = arith_f(0x0, 0xF, 0b0111, cin=0)
    assert f == exp_f == 0xF
    assert cn4_n == (0 if exp_c else 1)

    # S=1111, A=0, cin=0: A-1 wraps
    f, _, cn4_n = alu74181(0x0, 0x0, 0b1111, m=0, cn_n=1)
    exp_f, exp_c = arith_f(0x0, 0x0, 0b1111, cin=0)
    assert f == exp_f == 0xF


def test_max_add_carry():
    # 0xF+0xF+1 = 0x1F -> F=0xF, cout=1
    f, _, cn4_n = alu74181(0xF, 0xF, 0b1001, m=0, cn_n=0)
    assert f == 0xF
    assert cn4_n == 0  # carry out asserted (active-low pin low)


def test_logic_constants():
    assert alu74181(0xA, 0x5, 0b0011, 1, 1)[0] == 0x0
    assert alu74181(0x0, 0x0, 0b1100, 1, 1)[0] == 0xF
    assert alu74181(0x0, 0x0, 0b1100, 1, 1)[1] == 1  # AeqB


def test_cn_polarity():
    # Same A+B: Cn_n=1 => no +1; Cn_n=0 => +1
    f0, _, _ = alu74181(0x3, 0x1, 0b1001, 0, 1)
    f1, _, _ = alu74181(0x3, 0x1, 0b1001, 0, 0)
    assert f0 == 0x4
    assert f1 == 0x5
