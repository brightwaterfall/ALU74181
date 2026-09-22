# Schematic — 74181 ALU auto-S sequencer

Supply: **3V3** / **GND** from Tiny Tapeout demo board. All logic **74HC** @ 3.3 V.

## 1. Rate clock (555 astable)

| Ref | Value | Notes |
|-----|-------|-------|
| U1 | NE555 (or ICM7555) | Astable |
| R1 | 10 kΩ | |
| RV1 | 100 kΩ pot | Speed adjust |
| R2 | 10 kΩ | |
| C1 | 10 µF | ~0.5–10 Hz depending on pot |
| C2 | 100 nF | Control pin bypass |

Wiring (standard astable): discharge/threshold via R1+RV1/R2, C1 to GND, OUT → counter CLK.

## 2. S0–S3 sequencer (74HC161)

| Pin | Connection |
|-----|------------|
| VCC / GND | 3V3 / GND |
| CLK | U1 OUT |
| ENT, ENP | 3V3 (count enable) |
| /LOAD | 3V3 (never parallel-load) |
| /CLR | 3V3 (no reset; free run 0–15) |
| A,B,C,D load inputs | GND |
| Q0 | **S0** → `uio[0]` |
| Q1 | **S1** → `uio[1]` |
| Q2 | **S2** → `uio[2]` |
| Q3 | **S3** → `uio[3]` |
| RCO | NC |

**HOLD** test point: pull **ENP** to GND through a switch to freeze S.

Sequence: `S = 0,1,2,…,15,0,…` — each value is one ALU function select, one after another.

## 3. Static ALU inputs (switches)

| Control | Destination | Default |
|---------|-------------|---------|
| DIP4 SW_A | `ui[0:3]` = A0…A3 | user |
| DIP4 SW_B | `ui[4:7]` = B0…B3 | user |
| SPDT SW_M | `uio[4]` = M | 3V3 = logic |
| SPDT SW_CN | `uio[5]` = Cn_n | 3V3 = carry inactive |

Each switch line: 10 kΩ pull-down to GND; switch to 3V3 closes = logic 1  
(or DIP with common GND and pull-ups — same idea). Use **10 kΩ** pull-downs + switch-to-3V3 for clarity.

`uio[6]`, `uio[7]`: tie to GND on the PCB.

## 4. Result LEDs (from chip)

| Source | Series R | LED |
|--------|----------|-----|
| `uo[0]` F0 | 330 Ω | LED0 |
| `uo[1]` F1 | 330 Ω | LED1 |
| `uo[2]` F2 | 330 Ω | LED2 |
| `uo[3]` F3 | 330 Ω | LED3 |
| `uo[4]` AeqB | 330 Ω | LED_AEQ |

Cathodes to GND (assuming active-high drive from TT outputs).

Optional: LEDs on Q0–Q3 (S) with 330 Ω for watching the function index.

## 5. Decoupling

- 100 nF on U1 VCC, U2 VCC to GND  
- 10 µF bulk on 3V3 entry

## 6. Connector `J_TT`

See [connections.csv](connections.csv). 2.54 mm male headers, one pin per signal + 3V3 + GND.
