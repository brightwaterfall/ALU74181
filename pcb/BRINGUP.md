# Bring-up — 74181 ALU function sequencer PCB

## Hookup

1. Power **off** the Tiny Tapeout demo board.
2. Connect `J_TT` on this PCB to the demo board pins per [connections.csv](connections.csv)
   (ribbon or DuPont jumpers: `ui_*`, `uo_*`, `uio_*`, `3V3`, `GND`).
3. Set **DIP A** and **DIP B** to the operands you want (example: A=`0101`, B=`0011`).
4. Set **M**:
   - `M=1` (switch toward 3V3): logic functions for each S
   - `M=0` (toward GND): arithmetic functions for each S
5. Set **Cn_n** (active-low carry in):
   - open / high = no extra +1 on arithmetic
   - low = carry-in asserted
6. Power on the demo board (select this project’s tile if required).
7. Adjust **RV1** (rate pot): S should step visibly; F LEDs change on every count.

## What you should see

- Four **S LEDs** (optional on Q0–Q3) or a logic probe on `uio[0:3]` count binary 0…15 and wrap.
- **F LEDs** update immediately after each S step (combinational ALU).
- **AeqB LED** lights when `F == 4'hF`.

No firmware, no MCU — only 555 + 74HC161.

## Stop / hold one function

- Ground **HOLD** (ties 74HC161 clock enable low) to freeze on the current S.
- Or remove the 555 output jumper and drive S from an external pattern later if needed.

## Troubleshooting

| Symptom | Check |
|---------|--------|
| No LED activity | 3V3/GND, tile selected, F LED polarity/resistors |
| S not changing | 555 output, ENT/ENP high, /CLR high, HOLD not grounded |
| Wrong F for expected S | M/Cn_n/A/B switches; confirm pin map vs `info.yaml` |
