# SPDX-FileCopyrightText: © 2026 gddwms
# SPDX-License-Identifier: Apache-2.0

"""Cocotb tests for the Tiny Tapeout 74181 ALU wrapper."""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import Timer

from golden_model import alu74181, pack_ui, pack_uio, unpack_uo


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
    for a in range(16):
        for b in (0x0, 0x1, 0x5, 0xA, 0xF):
            for s in range(16):
                await apply(dut, a, b, s, m=1, cn_n=1)
                f, aeq, *_ = unpack_uo(int(dut.uo_out.value))
                exp_f, exp_aeq, _ = alu74181(a, b, s, 1, 1)
                assert f == exp_f, f"logic A={a:X} B={b:X} S={s:04b}: got {f:X} want {exp_f:X}"
                assert aeq == exp_aeq


@cocotb.test()
async def test_add_and_sub(dut):
    dut.ena.value = 1
    dut.rst_n.value = 1

    for a in range(16):
        for b in range(16):
            await apply(dut, a, b, s=0b1001, m=0, cn_n=1)
            f, _, _, _, cn4_n = unpack_uo(int(dut.uo_out.value))
            exp_f, _, exp_cn4_n = alu74181(a, b, 0b1001, 0, 1)
            assert f == exp_f, f"ADD A={a} B={b}: F={f} want {exp_f}"
            assert cn4_n == exp_cn4_n

            await apply(dut, a, b, s=0b1001, m=0, cn_n=0)
            f, _, _, _, cn4_n = unpack_uo(int(dut.uo_out.value))
            exp_f, _, exp_cn4_n = alu74181(a, b, 0b1001, 0, 0)
            assert f == exp_f
            assert cn4_n == exp_cn4_n

    for a in range(16):
        for b in range(16):
            await apply(dut, a, b, s=0b0110, m=0, cn_n=0)
            f, *_ = unpack_uo(int(dut.uo_out.value))
            exp_f, _, _ = alu74181(a, b, 0b0110, 0, 0)
            assert f == exp_f, f"SUB A={a} B={b}: F={f} want {exp_f}"


@cocotb.test()
async def test_identity_and_zero(dut):
    dut.ena.value = 1
    dut.rst_n.value = 1
    await apply(dut, 0xC, 0x3, s=0b1111, m=1, cn_n=1)
    f, *_ = unpack_uo(int(dut.uo_out.value))
    assert f == 0xC
    await apply(dut, 0xA, 0x5, s=0b0011, m=1, cn_n=1)
    f, *_ = unpack_uo(int(dut.uo_out.value))
    assert f == 0x0
