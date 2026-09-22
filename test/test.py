# SPDX-FileCopyrightText: © 2026 gddwms
# SPDX-License-Identifier: Apache-2.0

"""Cocotb tests for the Tiny Tapeout 74181 ALU wrapper."""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import Timer


def pack_ui(a: int, b: int) -> int:
    return (a & 0xF) | ((b & 0xF) << 4)


def pack_uio(s: int, m: int, cn_n: int) -> int:
    return (s & 0xF) | ((m & 1) << 4) | ((cn_n & 1) << 5)


def unpack_uo(val: int):
    f = val & 0xF
    aeq = (val >> 4) & 1
    p_n = (val >> 5) & 1
    g_n = (val >> 6) & 1
    cn4_n = (val >> 7) & 1
    return f, aeq, p_n, g_n, cn4_n


def golden_logic(a: int, b: int, s: int) -> int:
    a &= 0xF
    b &= 0xF
    table = {
        0b0000: (~a) & 0xF,
        0b0001: (~(a | b)) & 0xF,
        0b0010: ((~a) & b) & 0xF,
        0b0011: 0x0,
        0b0100: (~(a & b)) & 0xF,
        0b0101: (~b) & 0xF,
        0b0110: (a ^ b) & 0xF,
        0b0111: (a & (~b)) & 0xF,
        0b1000: ((~a) | b) & 0xF,
        0b1001: (~(a ^ b)) & 0xF,
        0b1010: b & 0xF,
        0b1011: (a & b) & 0xF,
        0b1100: 0xF,
        0b1101: (a | (~b)) & 0xF,
        0b1110: (a | b) & 0xF,
        0b1111: a & 0xF,
    }
    return table[s & 0xF]


def golden_arith(a: int, b: int, s: int, cin: int) -> tuple[int, int]:
    """Return (F, cout) for arithmetic mode. cin is active-high."""
    a &= 0xF
    b &= 0xF
    cin &= 1
    a_and_b = a & b
    a_and_nb = a & ((~b) & 0xF)
    a_or_b = a | b
    a_or_nb = a | ((~b) & 0xF)

    if s == 0b0000:
        r = a + cin
    elif s == 0b0001:
        r = a_or_b + cin
    elif s == 0b0010:
        r = a_or_nb + cin
    elif s == 0b0011:
        r = 0xF + cin
    elif s == 0b0100:
        r = a + a_and_nb + cin
    elif s == 0b0101:
        r = a_or_b + a_and_nb + cin
    elif s == 0b0110:
        r = a + ((~b) & 0xF) + cin
    elif s == 0b0111:
        r = a_and_nb + cin - 1
    elif s == 0b1000:
        r = a + a_and_b + cin
    elif s == 0b1001:
        r = a + b + cin
    elif s == 0b1010:
        r = a_or_nb + a_and_b + cin
    elif s == 0b1011:
        r = a_and_b + cin - 1
    elif s == 0b1100:
        r = a + a + cin
    elif s == 0b1101:
        r = a_or_b + a + cin
    elif s == 0b1110:
        r = a_or_nb + a + cin
    else:
        r = a + cin - 1

    f = r & 0xF
    cout = 1 if r >= 0x10 or r < 0 else (1 if (r >> 4) & 1 else 0)
    # For negative intermediate (shouldn't happen often), normalize
    if r < 0:
        # two's complement wrap to 5-bit then split
        r2 = r & 0x1F
        f = r2 & 0xF
        cout = (r2 >> 4) & 1
    else:
        cout = (r >> 4) & 1
    return f, cout


async def apply(dut, a, b, s, m, cn_n):
    dut.ui_in.value = pack_ui(a, b)
    dut.uio_in.value = pack_uio(s, m, cn_n)
    await Timer(1, unit="ns")


@cocotb.test()
async def test_reset_and_enable(dut):
    clock = Clock(dut.clk, 10, unit="us")
    cocotb.start_soon(clock.start())
    dut.ena.value = 1
    dut.rst_n.value = 0
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    await Timer(100, unit="ns")
    dut.rst_n.value = 1
    await Timer(100, unit="ns")


@cocotb.test()
async def test_logic_mode_exhaustive_nibbles(dut):
    dut.ena.value = 1
    dut.rst_n.value = 1
    # Sample A/B space densely enough for CI runtime
    for a in range(16):
        for b in (0x0, 0x1, 0x5, 0xA, 0xF):
            for s in range(16):
                await apply(dut, a, b, s, m=1, cn_n=1)
                f, aeq, *_ = unpack_uo(int(dut.uo_out.value))
                exp = golden_logic(a, b, s)
                assert f == exp, f"logic A={a:X} B={b:X} S={s:04b}: got {f:X} want {exp:X}"
                assert aeq == (1 if f == 0xF else 0)


@cocotb.test()
async def test_add_and_sub(dut):
    dut.ena.value = 1
    dut.rst_n.value = 1

    # A + B  (S=1001), Cn_n=1 => cin=0
    for a in range(16):
        for b in range(16):
            await apply(dut, a, b, s=0b1001, m=0, cn_n=1)
            f, _, _, _, cn4_n = unpack_uo(int(dut.uo_out.value))
            exp_f, exp_c = golden_arith(a, b, 0b1001, cin=0)
            assert f == exp_f, f"ADD A={a} B={b}: F={f} want {exp_f}"
            assert cn4_n == (0 if exp_c else 1)

            # A + B + 1 when Cn_n=0 => cin=1
            await apply(dut, a, b, s=0b1001, m=0, cn_n=0)
            f, _, _, _, cn4_n = unpack_uo(int(dut.uo_out.value))
            exp_f, exp_c = golden_arith(a, b, 0b1001, cin=1)
            assert f == exp_f
            assert cn4_n == (0 if exp_c else 1)

    # A - B (S=0110, cin=1) and A - B - 1 (cin=0)
    for a in range(16):
        for b in range(16):
            await apply(dut, a, b, s=0b0110, m=0, cn_n=0)
            f, *_ = unpack_uo(int(dut.uo_out.value))
            exp_f, _ = golden_arith(a, b, 0b0110, cin=1)
            assert f == exp_f, f"SUB A={a} B={b}: F={f} want {exp_f}"


@cocotb.test()
async def test_identity_and_zero(dut):
    dut.ena.value = 1
    dut.rst_n.value = 1
    # Logic: F=A (S=1111, M=1)
    await apply(dut, 0xC, 0x3, s=0b1111, m=1, cn_n=1)
    f, *_ = unpack_uo(int(dut.uo_out.value))
    assert f == 0xC
    # Logic: F=0 (S=0011, M=1)
    await apply(dut, 0xA, 0x5, s=0b0011, m=1, cn_n=1)
    f, *_ = unpack_uo(int(dut.uo_out.value))
    assert f == 0x0
