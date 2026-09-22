# Exceptional scenarios checklist

Hardening notes for operators / reviewers. Fixes applied in repo where noted.

| Scenario | Risk | Mitigation |
|----------|------|------------|
| Verilator `WIDTHEXPAND` on `cin` | Lint noise / subtle width bugs | Fixed: explicit `cin5` / `one` 5-bit operands |
| Arithmetic underflow (`(A&~B)-1` when 0) | Wrap to `0xF` | Defined 5-bit unsigned wrap; edge tests cover it |
| Floating `uio[6:7]` | Unknown inputs (unused) | Ignored in RTL; PCB ties to GND; drive 0 on demo board |
| `ena=0` (tile not selected) | Stale outputs | Wrapper forces `uo_out=0` when `ena=0` |
| Top module name collision | Shuttle ID clash | Renamed to `tt_um_brightwaterfall_alu74181` |
| Active-low `Cn_n` polarity mix-up | Off-by-one on add/sub | Documented; edge test `test_cn_polarity` |
| `M` wrong | Logic vs arithmetic swap | DIP labeled; docs table |
| Combo glitches on S counter edges | Brief wrong F on PCB | Expected for async S; slow 555 rate |
| Unused `clk`/`rst_n` | Lint unused | Tied in `_unused` reduction |
| P_n/G_n vs TTL datasheet | Not bit-exact CLA | F/Cn4/AeqB are primary; P/G for demo |
| Old GDS artifact name | Stale `tt_um_gddwms_*` files | Re-harden on CI after rename; new release |
| Gerber fab DRC | Scripted layout | Upload ZIP; run fab online DRC before order |
| GitHub Pages viewer | Deploy 404 | Pages enabled; viewer job green |
| CIR vs RTL | Transistor netlist ≠ gate RTL | CIR kept as reference only |

## Re-verify commands

```bash
cd test
pytest test_golden_unit.py test_edge_cases.py -q
python virtual_verify.py
# Full RTL (needs Icarus): make
```
