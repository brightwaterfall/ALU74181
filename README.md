![](../../workflows/gds/badge.svg) ![](../../workflows/docs/badge.svg) ![](../../workflows/test/badge.svg)

# Tiny Tapeout — 74181 4-bit ALU

Digital Verilog **74181-style 4-bit ALU** for Tiny Tapeout (SKY130 / LibreLane).

**Repo:** https://github.com/brightwaterfall/ALU74181

- [Project documentation](docs/info.md)
- [Reproduce the flow](WALKTHROUGH.md)
- [Test PCB (auto S0–S3)](pcb/README.md)

## Status

| Check | Result |
|-------|--------|
| RTL cocotb (`test`) | Passing on GitHub Actions |
| GDS harden + precheck + GL test | Passing |
| Tagged release with GDS | See [Releases](https://github.com/brightwaterfall/ALU74181/releases) |

## Pin map

| Port | Signal |
|------|--------|
| `ui_in[3:0]` | A[3:0] |
| `ui_in[7:4]` | B[3:0] |
| `uio_in[3:0]` | S[3:0] |
| `uio_in[4]` | M (1=logic, 0=arithmetic) |
| `uio_in[5]` | Cn_n (active-low carry in) |
| `uo_out[3:0]` | F[3:0] |
| `uo_out[4]` | AeqB |
| `uo_out[5]` | P_n |
| `uo_out[6]` | G_n |
| `uo_out[7]` | Cn4_n |

Top module: `tt_um_brightwaterfall_alu74181`

## Quick test

```bash
cd test
pip install -r requirements.txt
make
```

## What is Tiny Tapeout?

https://tinytapeout.com
