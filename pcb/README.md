# PCB test board (pending client pin / feature brief)

This folder will hold the KiCad project (schematic, PCB, Gerbers, BOM) for
exercising the Tiny Tapeout 74181 chip on a bench.

**Status:** waiting on the PCB behavior description (switches, LEDs, connector,
power, target fab).

Planned contents once specified:

- `74181_breakout.kicad_pro` / `.kicad_sch` / `.kicad_pcb`
- `gerbers/` export for JLCPCB-style fab
- `bom.csv`, `cpl.csv`
- `BRINGUP.md` — power-on and pin mapping to the TT demo board / carrier
