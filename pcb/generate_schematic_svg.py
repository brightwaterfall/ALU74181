# SPDX-FileCopyrightText: © 2026 brightwaterfall / gddwms
# SPDX-License-Identifier: Apache-2.0

"""
Generate a fabrication-oriented SVG schematic for the ALU S-sequencer PCB.
Open in a browser or Inkscape; use with SCHEMATIC.md / bom.csv for assembly.
"""
from __future__ import annotations

from pathlib import Path

OUT = Path(__file__).with_name("schematic_sequencer.svg")

W, H = 1100, 720


def esc(t: str) -> str:
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def box(x, y, w, h, title, lines, fill="#f5f5f5"):
    ts = "\n".join(
        f'<text x="{x+8}" y="{y+36+i*16}" font-size="13" font-family="Segoe UI,Arial">{esc(L)}</text>'
        for i, L in enumerate(lines)
    )
    return f'''
  <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{fill}" stroke="#222" stroke-width="2"/>
  <text x="{x+8}" y="{y+20}" font-size="15" font-weight="700" font-family="Segoe UI,Arial">{esc(title)}</text>
  {ts}'''


def arrow(x1, y1, x2, y2, label=""):
    return f'''
  <line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#333" stroke-width="2" marker-end="url(#arrow)"/>
  <text x="{(x1+x2)/2}" y="{(y1+y2)/2-6}" font-size="12" text-anchor="middle" font-family="Segoe UI,Arial">{esc(label)}</text>'''


svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
  <defs>
    <marker id="arrow" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L6,3 L0,6 Z" fill="#333"/>
    </marker>
  </defs>
  <rect width="100%" height="100%" fill="#ffffff"/>
  <text x="24" y="36" font-size="22" font-weight="700" font-family="Segoe UI,Arial">74181 ALU test PCB — auto S0–S3 sequencer</text>
  <text x="24" y="58" font-size="13" fill="#444" font-family="Segoe UI,Arial">3.3 V from Tiny Tapeout demo board · cycles every ALU function (S=0..15) continuously</text>

  {box(40, 90, 220, 140, "U1 NE555 + RV1", ["Astable clock", "R1/R2=10k, C1=10uF", "RV1=100k rate pot", "OUT → U2.CLK"], "#e8f4ff")}
  {box(320, 90, 260, 160, "U2 74HC161", ["ENT/ENP=/LOAD=/CLR = 3V3", "Q0..Q3 = S0..S3", "Free-run count 0..15", "HOLD pulls ENP low to freeze"], "#fff4e0")}
  {box(640, 90, 400, 200, "J_TT → Tiny Tapeout tile", [
      "ui[3:0]←A  ui[7:4]←B",
      "uio[3:0]←S0..S3 (from U2)",
      "uio[4]←M  uio[5]←Cn_n",
      "uio[6..7]←GND",
      "uo[3:0]→F LEDs  uo[4]→AeqB LED",
      "3V3, GND from demo board",
  ], "#eaffea")}

  {box(40, 320, 280, 150, "SW_A / SW_B / M / Cn", ["DIP4 A → ui[0:3]", "DIP4 B → ui[4:7]", "SPDT M → uio[4]", "SPDT Cn_n → uio[5]", "10k pull-downs to GND"], "#f0e8ff")}
  {box(360, 320, 280, 150, "LED bank", ["F0..F3 + 330R → LED", "AeqB + 330R → LED", "Optional LEDs on S0..S3", "Cathodes → GND"], "#ffe8e8")}
  {box(680, 320, 360, 150, "Decoupling", ["100nF @ U1,U2 VCC", "10uF bulk on 3V3", "All logic 74HC @ 3.3V"], "#f5f5f5")}

  {arrow(260, 160, 320, 160, "CLK")}
  {arrow(580, 160, 640, 160, "S[3:0]")}
  {arrow(320, 395, 640, 220, "A/B/M/Cn")}
  {arrow(640, 250, 500, 320, "F / AeqB")}

  <text x="24" y="560" font-size="13" font-family="Segoe UI,Arial">Behavior: with A,B,M,Cn fixed, S advances 0→1→…→15→0 so each 74181 function runs one after another; F LEDs update each step.</text>
  <text x="24" y="585" font-size="12" fill="#555" font-family="Segoe UI,Arial">Refs: bom.csv · connections.csv · SCHEMATIC.md · BRINGUP.md · 74181_alu_tester.kicad_pro</text>
  <text x="24" y="680" font-size="11" fill="#777" font-family="Segoe UI,Arial">brightwaterfall/ALU74181 · Apache-2.0</text>
</svg>
'''

OUT.write_text(svg, encoding="utf-8")
print("Wrote", OUT)
