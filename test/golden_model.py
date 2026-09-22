# SPDX-FileCopyrightText: © 2026 gddwms
# SPDX-License-Identifier: Apache-2.0
"""Reference 74181 model (matches src/alu74181.v). Used by cocotb and offline pytest."""

from __future__ import annotations


def pack_ui(a: int, b: int) -> int:
    return (a & 0xF) | ((b & 0xF) << 4)


def pack_uio(s: int, m: int, cn_n: int) -> int:
    return (s & 0xF) | ((m & 1) << 4) | ((cn_n & 1) << 5)


def unpack_uo(val: int) -> tuple[int, int, int, int, int]:
    f = val & 0xF
    aeq = (val >> 4) & 1
    p_n = (val >> 5) & 1
    g_n = (val >> 6) & 1
    cn4_n = (val >> 7) & 1
    return f, aeq, p_n, g_n, cn4_n


def logic_f(a: int, b: int, s: int) -> int:
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


def _to_5bit(r: int) -> tuple[int, int]:
    """Match Verilog unsigned 5-bit wrap for + / - expressions."""
    r2 = r & 0x1F
    return r2 & 0xF, (r2 >> 4) & 1


def arith_f(a: int, b: int, s: int, cin: int) -> tuple[int, int]:
    """Return (F, cout_high). cin is active-high (Cn_n inverted)."""
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

    return _to_5bit(r)


def alu74181(a: int, b: int, s: int, m: int, cn_n: int) -> tuple[int, int, int]:
    """
    Returns (F, AeqB, Cn4_n).
    P_n/G_n are look-ahead helpers; not required for functional F checks.
    """
    if m:
        f = logic_f(a, b, s)
        cn4_n = 1
    else:
        cin = 0 if cn_n else 1
        f, cout = arith_f(a, b, s, cin)
        cn4_n = 0 if cout else 1
    aeq = 1 if f == 0xF else 0
    return f, aeq, cn4_n
