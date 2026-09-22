# 74181 ALU test PCB

Auto-exerciser for the Tiny Tapeout **74181 ALU** chip.

## What it does

With **A**, **B**, **M**, and **Cn_n** held on switches:

1. A slow **555** clock advances a **74HC161** counter  
2. **Q0–Q3 → S0–S3**  
3. S runs **0 → 1 → … → 15 → 0…** (every ALU function, one after another)  
4. LEDs show **F[3:0]** and **AeqB**

## Deliverables

| File | Purpose |
|------|---------|
| [BRINGUP.md](BRINGUP.md) | Power-on / how to watch the sequence |
| [SCHEMATIC.md](SCHEMATIC.md) | Full net / wiring description |
| [schematic_sequencer.svg](schematic_sequencer.svg) | Block schematic drawing |
| [bom.csv](bom.csv) | Parts + typical LCSC codes |
| [connections.csv](connections.csv) | Header ↔ TT pin map |
| `74181_alu_tester.kicad_pro` / `.kicad_sch` | KiCad project entry |
| [generate_schematic_svg.py](generate_schematic_svg.py) | Regenerate SVG |

## Fab

1. Open KiCad project and place symbols from `SCHEMATIC.md` (555, 74HC161, DIP, headers, LEDs).  
2. Route 2-layer ~50×50 mm, 3V3 from TT demo board.  
3. Export Gerbers + CPL from KiCad for JLCPCB.  
4. Assemble using `bom.csv`.

No MCU — discrete sequencer only.
