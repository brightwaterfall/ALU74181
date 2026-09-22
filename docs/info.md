<!---
Tiny Tapeout datasheet content for the 74181 ALU project.
-->

## How it works

This project implements a classic **74181-style 4-bit ALU** in synthesizable Verilog for Tiny Tapeout.

- **Logic mode (`M=1`)**: 16 bitwise functions of `A` and `B` selected by `S[3:0]` (NOT, NOR, XOR, AND, OR, pass-through, constants, …), matching the TI active-high data table.
- **Arithmetic mode (`M=0`)**: add / subtract / increment-style operations. Carry-in pin `Cn_n` is **active-low** (TTL naming): drive `Cn_n=0` to assert carry-in.
- Outputs: result `F[3:0]`, equality `AeqB` (high when `F==4'hF`), and active-low look-ahead / carry signals `P_n`, `G_n`, `Cn4_n`.

The design is **combinational** (no clocked state). `clk` / `rst_n` are unused and tied off inside the top module.

A transistor-level SPICE netlist (`74181.cir`) was used as the architectural reference for the ALU function; the shuttle payload is this digital RTL so it fits the Tiny Tapeout digital flow (LibreLane harden + CI).

## How to test

1. Set `A` on `ui_in[3:0]` and `B` on `ui_in[7:4]`.
2. Set function select `S` on `uio_in[3:0]`, mode `M` on `uio_in[4]`, carry-in `Cn_n` on `uio_in[5]`.
3. Read `F` on `uo_out[3:0]` and status flags on `uo_out[7:4]`.

Examples:

| Mode | S | Cn_n | Operation |
|------|---|------|-----------|
| M=1 | `1111` | x | `F = A` |
| M=1 | `0110` | x | `F = A XOR B` |
| M=0 | `1001` | 1 | `F = A + B` |
| M=0 | `1001` | 0 | `F = A + B + 1` |
| M=0 | `0110` | 0 | `F = A - B` |

Automated checks: from `test/`, run `make` (cocotb + Icarus).

## External hardware

- Tiny Tapeout demo board (host for the ASIC tile)
- **74181 ALU test PCB** (`pcb/`): 555 + 74HC161 auto-sequences **S0–S3** through all 16 functions; DIP switches set A/B/M/Cn_n; LEDs show F and AeqB. See `pcb/README.md` and `pcb/BRINGUP.md`.
