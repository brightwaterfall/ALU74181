# 74181 ALU test PCB

Auto-exerciser for the Tiny Tapeout **74181 ALU** chip.

## What it does

With **A**, **B**, **M**, and **Cn_n** held steady (DIP/slide switches):

1. A slow clock advances a **4-bit counter**
2. Counter outputs drive **S0–S3**
3. S steps **0000 → 0001 → … → 1111 → 0000 → …** continuously (one function immediately after another)
4. LEDs show **F[3:0]** (and **AeqB**) from the chip for each S value

That is the entire test behavior — cycle every ALU function select code in order.

## Files

| File | Purpose |
|------|---------|
| [BRINGUP.md](BRINGUP.md) | Power-on, jumpers, how to watch the sequence |
| [SCHEMATIC.md](SCHEMATIC.md) | Full schematic / net description |
| [bom.csv](bom.csv) | Parts list (JLCPCB-friendly) |
| [connections.csv](connections.csv) | Header ↔ Tiny Tapeout pin map |
| `74181_alu_tester.kicad_pro` | KiCad project |
| `74181_alu_tester.kicad_sch` | KiCad schematic |

## Block diagram

```
  [DIP A3..A0] ----ui[3:0]---+
  [DIP B3..B0] ----ui[7:4]---+---> Tiny Tapeout 74181 tile
  [SW M]       ----uio[4]----+         |
  [SW Cn_n]    ----uio[5]----+         |
                                       v
  [555 + pot] --> CLK --> [74HC161] --S[3:0]--> uio[3:0]
                              Q0..Q3

  uo[3:0] F[3:0] --> LED0..LED3
  uo[4]   AeqB   --> LED_AEQ
```

## Fab notes

- 2-layer, ~50×50 mm, 3.3 V logic (74HC)
- Power from the Tiny Tapeout demo board 3V3 (no USB regulator required)
- Open in KiCad 8+ to finish copper pour / DRC before ordering Gerbers
