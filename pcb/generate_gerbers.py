#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""
Generate JLCPCB-oriented Gerbers + Excellon for the 74181 ALU S-sequencer PCB.

Board: 70 x 50 mm, 2-layer, 3.3 V discrete sequencer (555 + 74HC161) + TT header.
"""
from __future__ import annotations

import math
import zipfile
from pathlib import Path

OUT = Path(__file__).resolve().parent / "gerbers"
BOARD_W, BOARD_H = 70.0, 50.0


class Gerber:
    def __init__(self, name: str):
        self.name = name
        self.lines = [
            "%FSLAX46Y46*%",
            "%MOMM*%",
            "G01*",
            "%LPD*%",
        ]
        self._ap = {}
        self._next = 10

    def _xy(self, x: float, y: float) -> str:
        return f"X{int(round(x * 1e6))}Y{int(round(y * 1e6))}"

    def aperture_circle(self, diam_mm: float) -> int:
        key = ("C", round(diam_mm, 4))
        if key not in self._ap:
            d = self._next
            self._next += 1
            self._ap[key] = d
            self.lines.append(f"%ADD{d}C,{diam_mm:.4f}*%")
        return self._ap[key]

    def aperture_rect(self, w: float, h: float) -> int:
        key = ("R", round(w, 4), round(h, 4))
        if key not in self._ap:
            d = self._next
            self._next += 1
            self._ap[key] = d
            self.lines.append(f"%ADD{d}R,{w:.4f}X{h:.4f}*%")
        return self._ap[key]

    def flash_c(self, x, y, d):
        a = self.aperture_circle(d)
        self.lines.append(f"D{a}*")
        self.lines.append(f"{self._xy(x, y)}D03*")

    def flash_r(self, x, y, w, h):
        a = self.aperture_rect(w, h)
        self.lines.append(f"D{a}*")
        self.lines.append(f"{self._xy(x, y)}D03*")

    def line(self, x1, y1, x2, y2, width):
        a = self.aperture_circle(width)
        self.lines.append(f"D{a}*")
        self.lines.append(f"{self._xy(x1, y1)}D02*")
        self.lines.append(f"{self._xy(x2, y2)}D01*")

    def rect_outline(self, x, y, w, h, width=0.15):
        self.line(x, y, x + w, y, width)
        self.line(x + w, y, x + w, y + h, width)
        self.line(x + w, y + h, x, y + h, width)
        self.line(x, y + h, x, y, width)

    def text_line(self, x, y, s, size=1.0):
        # crude silk as stroked segments (uppercase)
        # keep short labels only
        self.line(x, y, x + size * 0.6 * max(1, len(s) * 0.35), y, 0.15)

    def finish(self) -> str:
        return "\n".join(self.lines + ["M02*"]) + "\n"


class Excellon:
    def __init__(self):
        self.holes: list[tuple[float, float, float]] = []

    def add(self, x, y, d=0.3):
        self.holes.append((x, y, d))

    def dump(self) -> str:
        # Group by diameter
        by_d: dict[float, list] = {}
        for x, y, d in self.holes:
            by_d.setdefault(round(d, 3), []).append((x, y))
        lines = [
            "M48",
            ";DRILL file for 74181 ALU tester",
            "METRIC,TZ",
            "FMAT,2",
        ]
        tool = 1
        body = []
        for d, pts in sorted(by_d.items()):
            lines.append(f"T{tool:02d}C{d:.3f}")
            body.append(f"T{tool:02d}")
            for x, y in pts:
                body.append(f"X{x:.3f}Y{y:.3f}")
            tool += 1
        lines.append("%")
        lines.extend(body)
        lines.append("M30")
        return "\n".join(lines) + "\n"


def soic_pads(cu: Gerber, mask: Gerber, ox, oy, npins_side, pitch=1.27, pad_w=0.6, pad_h=1.5):
    """SOIC: pins along left and right, pin1 bottom-left. Body center at (ox,oy)."""
    body_w = 3.9
    body_h = pitch * (npins_side - 1) + 1.0
    # left pins (1..n bottom to top), right pins (2n..n+1 bottom to top numbering for 161)
    pins = []
    for i in range(npins_side):
        y = oy - (npins_side - 1) * pitch / 2 + i * pitch
        x_l = ox - body_w / 2 - 0.2
        x_r = ox + body_w / 2 + 0.2
        for x in (x_l, x_r):
            cu.flash_r(x, y, pad_w, pad_h)
            mask.flash_r(x, y, pad_w + 0.1, pad_h + 0.1)
        pins.append((x_l, y))  # left ascending
    right = []
    for i in range(npins_side):
        y = oy - (npins_side - 1) * pitch / 2 + i * pitch
        x_r = ox + body_w / 2 + 0.2
        right.append((x_r, y))
    return pins, right, body_w, body_h


def dip4_pads(cu, mask, drill, ox, oy):
    """4-pos DIP switch, 2.54 pitch."""
    pts = []
    for i in range(4):
        x = ox + i * 2.54
        for dy in (-3.81, 3.81):
            y = oy + dy
            cu.flash_c(x, y, 1.6)
            mask.flash_c(x, y, 1.8)
            drill.add(x, y, 0.8)
            pts.append((x, y))
    return pts


def led_pads(cu, mask, drill, x, y):
    cu.flash_c(x - 0.8, y, 1.0)
    cu.flash_c(x + 0.8, y, 1.0)
    mask.flash_c(x - 0.8, y, 1.2)
    mask.flash_c(x + 0.8, y, 1.2)
    # 0805 no drill (SMD)
    return (x - 0.8, y), (x + 0.8, y)


def header_pin(cu, mask, drill, x, y):
    cu.flash_c(x, y, 1.7)
    mask.flash_c(x, y, 1.9)
    drill.add(x, y, 1.0)


def build():
    OUT.mkdir(parents=True, exist_ok=True)
    gtl = Gerber("GTL")
    gbl = Gerber("GBL")
    gts = Gerber("GTS")
    gbs = Gerber("GBS")
    gto = Gerber("GTO")
    gko = Gerber("GKO")
    drill = Excellon()

    # Outline
    gko.rect_outline(0, 0, BOARD_W, BOARD_H, 0.1)

    # Mounting holes
    for mx, my in ((3, 3), (BOARD_W - 3, 3), (3, BOARD_H - 3), (BOARD_W - 3, BOARD_H - 3)):
        gtl.flash_c(mx, my, 3.2)
        gbl.flash_c(mx, my, 3.2)
        gts.flash_c(mx, my, 3.4)
        gbs.flash_c(mx, my, 3.4)
        drill.add(mx, my, 2.2)

    # --- J_TT headers: 2 columns x 14 pins @ x=6 and x=8.54 ---
    hdr = {}
    names = [
        "A0", "A1", "A2", "A3", "B0", "B1", "B2", "B3",
        "S0", "S1", "S2", "S3", "M", "Cn",
    ]
    names2 = [
        "F0", "F1", "F2", "F3", "AEQ", "Pn", "Gn", "Cn4",
        "3V3", "GND", "GND", "3V3", "TP1", "TP2",
    ]
    y0 = 8.0
    for i, n in enumerate(names):
        y = y0 + i * 2.54
        header_pin(gtl, gts, drill, 6.0, y)
        header_pin(gbl, gbs, drill, 6.0, y)
        hdr[n] = (6.0, y)
        gto.flash_r(4.2, y, 0.2, 0.2)
    for i, n in enumerate(names2):
        y = y0 + i * 2.54
        header_pin(gtl, gts, drill, 10.0, y)
        header_pin(gbl, gbs, drill, 10.0, y)
        hdr[n] = (10.0, y)

    # --- U1 NE555 SOIC-8 center (28, 38) ---
    u1_l, u1_r, _, _ = soic_pads(gtl, gts, 28, 38, 4)
    # SOIC-8: left 1-4 bot->top, right 8-5 bot->top
    u1 = {
        1: u1_l[0],
        2: u1_l[1],
        3: u1_l[2],
        4: u1_l[3],
        8: u1_r[0],
        7: u1_r[1],
        6: u1_r[2],
        5: u1_r[3],
    }

    # --- U2 74HC161 SOIC-16 (48, 38) ---
    u2_l, u2_r, _, _ = soic_pads(gtl, gts, 48, 38, 8)
    u2 = {}
    for i in range(8):
        u2[i + 1] = u2_l[i]
        u2[16 - i] = u2_r[i]

    # DIP switches
    dip_a = dip4_pads(gtl, gts, drill, 22, 18)
    dip_b = dip4_pads(gtl, gts, drill, 42, 18)

    # LEDs F0-F3 + AEQ along top
    leds = []
    for i in range(5):
        leds.append(led_pads(gtl, gts, drill, 20 + i * 8, 46))

    # Pot pads (RV1) rough 3 pads
    for dx in (-2.5, 0, 2.5):
        gtl.flash_c(62, 30 + dx, 1.5)
        gts.flash_c(62, 30 + dx, 1.7)
        drill.add(62, 30 + dx, 0.9)

    # Decap 0603 near U1/U2
    for cx, cy in ((28, 32), (48, 32), (15, 40)):
        gtl.flash_r(cx - 0.8, cy, 0.8, 0.9)
        gtl.flash_r(cx + 0.8, cy, 0.8, 0.9)
        gts.flash_r(cx - 0.8, cy, 0.9, 1.0)
        gts.flash_r(cx + 0.8, cy, 0.9, 1.0)

    # --- Routing (top copper) ---
    def route(a, b, w=0.25):
        gtl.line(a[0], a[1], b[0], b[1], w)

    def route_via(a, b, w=0.25):
        # dogleg via bottom when needed
        mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        gtl.line(a[0], a[1], mid[0], a[1], w)
        # via
        gtl.flash_c(mid[0], a[1], 0.7)
        gbl.flash_c(mid[0], a[1], 0.7)
        gts.flash_c(mid[0], a[1], 0.9)
        gbs.flash_c(mid[0], a[1], 0.9)
        drill.add(mid[0], a[1], 0.3)
        gbl.line(mid[0], a[1], mid[0], b[1], w)
        gbl.flash_c(mid[0], b[1], 0.7)
        gtl.flash_c(mid[0], b[1], 0.7)
        drill.add(mid[0], b[1], 0.3)
        gtl.line(mid[0], b[1], b[0], b[1], w)

    # Power: 3V3 / GND to chips
    route(hdr["3V3"], u1[8], 0.4)
    route(hdr["GND"], u1[1], 0.4)
    route(hdr["3V3"], u2[16], 0.4)
    route(hdr["GND"], u2[8], 0.4)

    # 555 OUT (pin3) -> HC161 CLK (pin2)
    route(u1[3], u2[2], 0.25)

    # HC161 Q0..Q3 (pins 14,13,12,11) -> S0..S3
    for qpin, sname in ((14, "S0"), (13, "S1"), (12, "S2"), (11, "S3")):
        route(u2[qpin], hdr[sname], 0.25)

    # Tie ENT(10), ENP(7), /LOAD(9), /CLR(1) to 3V3
    for p in (10, 7, 9, 1):
        route(u2[p], hdr["3V3"], 0.25)

    # DIP A -> A0..A3 (first row of dip toward header)
    for i in range(4):
        route(dip_a[i * 2], hdr[f"A{i}"], 0.25)
        route(dip_a[i * 2 + 1], hdr["GND"], 0.25)
    for i in range(4):
        route(dip_b[i * 2], hdr[f"B{i}"], 0.25)
        route(dip_b[i * 2 + 1], hdr["GND"], 0.25)

    # LEDs from F / AEQ to GND via series (pad1 signal, pad2 gnd)
    for i, name in enumerate(["F0", "F1", "F2", "F3", "AEQ"]):
        route(hdr[name], leds[i][0], 0.25)
        route(leds[i][1], hdr["GND"], 0.25)

    # Silk title
    gto.rect_outline(14, 1.5, 42, 3.5, 0.2)
    gto.line(16, 3, 54, 3, 0.25)

    # Bottom ground pour as sparse hatch (not true pour — grid of lines)
    for x in range(12, 68, 3):
        gbl.line(x, 4, x, 48, 0.2)
    for y in range(4, 48, 3):
        gbl.line(12, y, 68, y, 0.2)

    files = {
        "Gerber_TopLayer.GTL": gtl.finish(),
        "Gerber_BottomLayer.GBL": gbl.finish(),
        "Gerber_TopSolderMaskLayer.GTS": gts.finish(),
        "Gerber_BottomSolderMaskLayer.GBS": gbs.finish(),
        "Gerber_TopSilkscreenLayer.GTO": gto.finish(),
        "Gerber_BoardOutlineLayer.GKO": gko.finish(),
        "Drill_PTH_Through.DRL": drill.dump(),
    }

    for name, data in files.items():
        (OUT / name).write_text(data, encoding="ascii")

    # JLCPCB-friendly zip
    zpath = OUT.parent / "74181_alu_tester_gerbers.zip"
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as zf:
        for name in files:
            zf.write(OUT / name, name)
        readme = OUT / "README_FAB.txt"
        readme.write_text(
            "\n".join(
                [
                    "74181 ALU test PCB — Gerber package",
                    "Size: 70 x 50 mm, 2-layer, 1.6 mm, HASL lead-free",
                    "Min track/clearance: 0.25 mm / 0.2 mm",
                    "Drill: PTH as Drill_PTH_Through.DRL",
                    "Upload ZIP to JLCPCB / PCBWay.",
                    "See ../bom.csv and ../connections.csv for assembly.",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        zf.write(readme, "README_FAB.txt")

    print("Wrote", OUT)
    print("Zip", zpath)
    return zpath


if __name__ == "__main__":
    build()
