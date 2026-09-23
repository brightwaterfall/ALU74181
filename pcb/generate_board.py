#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""
Full 74181 ALU S-sequencer test PCB:
  - JLCPCB Gerbers + Excellon + zip
  - Top-view board preview PNG (pcb_render.png)

Board: 70 x 50 mm, 2-layer, 3.3 V from Tiny Tapeout demo board.
"""
from __future__ import annotations

import math
import zipfile
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError as e:  # pragma: no cover
    raise SystemExit("Pillow required: py -3 -m pip install Pillow") from e

HERE = Path(__file__).resolve().parent
OUT = HERE / "gerbers"
BOARD_W, BOARD_H = 70.0, 50.0
SCALE = 12  # pixels per mm for preview


# ---------------------------------------------------------------------------
# Gerber / Excellon helpers
# ---------------------------------------------------------------------------
class Gerber:
    def __init__(self, name: str):
        self.name = name
        self.lines = ["%FSLAX46Y46*%", "%MOMM*%", "G01*", "%LPD*%"]
        self._ap: dict = {}
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

    def finish(self) -> str:
        return "\n".join(self.lines + ["M02*"]) + "\n"


class Excellon:
    def __init__(self):
        self.holes: list[tuple[float, float, float]] = []

    def add(self, x, y, d=0.3):
        self.holes.append((x, y, d))

    def dump(self) -> str:
        by_d: dict[float, list] = {}
        for x, y, d in self.holes:
            by_d.setdefault(round(d, 3), []).append((x, y))
        lines = ["M48", ";DRILL 74181 ALU tester", "METRIC,TZ", "FMAT,2"]
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


# ---------------------------------------------------------------------------
# Placement model (shared by Gerber + preview)
# ---------------------------------------------------------------------------
def layout():
    """Return dict of named pads / parts for routing and drawing."""
    L: dict = {"hdr": {}, "parts": {}}

    # Dual pin headers along left edge
    names_in = [
        "A0", "A1", "A2", "A3", "B0", "B1", "B2", "B3",
        "S0", "S1", "S2", "S3", "M", "Cn",
    ]
    names_out = [
        "F0", "F1", "F2", "F3", "AEQ", "Pn", "Gn", "Cn4",
        "3V3", "GND", "uio6", "uio7", "HOLD", "TP",
    ]
    y0 = 6.5
    for i, n in enumerate(names_in):
        L["hdr"][n] = (5.5, y0 + i * 2.54)
    for i, n in enumerate(names_out):
        L["hdr"][n] = (9.5, y0 + i * 2.54)

    # ICs
    L["parts"]["U1"] = {"kind": "soic8", "xy": (28.0, 36.0), "label": "U1 7555"}
    L["parts"]["U2"] = {"kind": "soic16", "xy": (48.0, 36.0), "label": "U2 74HC161"}

    # DIP switches
    L["parts"]["SW_A"] = {"kind": "dip4", "xy": (24.0, 16.0), "label": "SW_A A[3:0]"}
    L["parts"]["SW_B"] = {"kind": "dip4", "xy": (42.0, 16.0), "label": "SW_B B[3:0]"}

    # Slide switches
    L["parts"]["SW_M"] = {"kind": "spdt", "xy": (60.0, 12.0), "label": "M"}
    L["parts"]["SW_CN"] = {"kind": "spdt", "xy": (60.0, 20.0), "label": "Cn_n"}
    L["parts"]["SW_HOLD"] = {"kind": "spdt", "xy": (60.0, 28.0), "label": "HOLD"}

    # Pot
    L["parts"]["RV1"] = {"kind": "pot", "xy": (62.0, 40.0), "label": "RV1 RATE"}

    # LEDs along top
    leds = []
    for i, name in enumerate(["F0", "F1", "F2", "F3", "AEQ"]):
        leds.append({"name": name, "xy": (20.0 + i * 8.5, 46.0)})
    L["leds"] = leds

    # Passives (decap / timing)
    L["passives"] = [
        {"ref": "C1", "xy": (22.0, 36.0), "kind": "0805"},   # 10uF timing
        {"ref": "C2", "xy": (22.0, 40.0), "kind": "0603"},   # 100n CTRL
        {"ref": "CD1", "xy": (28.0, 30.0), "kind": "0603"},
        {"ref": "CD2", "xy": (48.0, 30.0), "kind": "0603"},
        {"ref": "CBULK", "xy": (14.0, 42.0), "kind": "0805"},
        {"ref": "R1", "xy": (34.0, 42.0), "kind": "0603"},
        {"ref": "R2", "xy": (38.0, 42.0), "kind": "0603"},
    ]

    # Series LED resistors under LEDs
    L["led_r"] = [
        {"ref": f"R{name}", "xy": (20.0 + i * 8.5, 42.5)}
        for i, name in enumerate(["F0", "F1", "F2", "F3", "AEQ"])
    ]

    return L


def soic_pin_map(ox, oy, npins_side, pitch=1.27):
    body_w = 3.9 if npins_side == 4 else 4.0
    left, right = [], []
    for i in range(npins_side):
        y = oy - (npins_side - 1) * pitch / 2 + i * pitch
        left.append((ox - body_w / 2 - 0.2, y))
        right.append((ox + body_w / 2 + 0.2, y))
    pins = {}
    for i in range(npins_side):
        pins[i + 1] = left[i]
        pins[2 * npins_side - i] = right[i]
    return pins, body_w, pitch * (npins_side - 1) + 1.0


def dip4_pins(ox, oy):
    pts = []
    for i in range(4):
        x = ox + (i - 1.5) * 2.54
        pts.append((x, oy - 3.81))  # switch side (signal)
        pts.append((x, oy + 3.81))  # common
    return pts


def spdt_pins(ox, oy):
    # 3 pins horizontal
    return [(ox - 2.54, oy), (ox, oy), (ox + 2.54, oy)]


def pot_pins(ox, oy):
    return [(ox, oy - 2.5), (ox, oy), (ox, oy + 2.5)]


def smd0603(ox, oy):
    return (ox - 0.8, oy), (ox + 0.8, oy)


def smd0805(ox, oy):
    return (ox - 1.0, oy), (ox + 1.0, oy)


def led_pads(ox, oy):
    return (ox - 0.85, oy), (ox + 0.85, oy)


# ---------------------------------------------------------------------------
# Build Gerbers
# ---------------------------------------------------------------------------
def build_gerbers(L):
    OUT.mkdir(parents=True, exist_ok=True)
    gtl, gbl = Gerber("GTL"), Gerber("GBL")
    gts, gbs = Gerber("GTS"), Gerber("GBS")
    gto, gko = Gerber("GTO"), Gerber("GKO")
    drill = Excellon()

    gko.rect_outline(0, 0, BOARD_W, BOARD_H, 0.1)

    # Mounting holes
    for mx, my in ((3, 3), (BOARD_W - 3, 3), (3, BOARD_H - 3), (BOARD_W - 3, BOARD_H - 3)):
        for g, m, d in ((gtl, gts, 3.2), (gbl, gbs, 3.2)):
            g.flash_c(mx, my, d)
            m.flash_c(mx, my, d + 0.2)
        drill.add(mx, my, 2.2)

    def pth(x, y, pad=1.7, hole=1.0):
        gtl.flash_c(x, y, pad)
        gbl.flash_c(x, y, pad)
        gts.flash_c(x, y, pad + 0.2)
        gbs.flash_c(x, y, pad + 0.2)
        drill.add(x, y, hole)

    def smd_r(x, y, w, h):
        gtl.flash_r(x, y, w, h)
        gts.flash_r(x, y, w + 0.1, h + 0.1)

    def via(x, y):
        gtl.flash_c(x, y, 0.7)
        gbl.flash_c(x, y, 0.7)
        gts.flash_c(x, y, 0.9)
        gbs.flash_c(x, y, 0.9)
        drill.add(x, y, 0.3)

    def route_top(a, b, w=0.25):
        gtl.line(a[0], a[1], b[0], b[1], w)

    def route_bot(a, b, w=0.25):
        gbl.line(a[0], a[1], b[0], b[1], w)

    def route_l(a, b, w=0.25):
        """Orthogonal dogleg on top."""
        mid = (b[0], a[1])
        route_top(a, mid, w)
        route_top(mid, b, w)

    # Headers
    for n, (x, y) in L["hdr"].items():
        pth(x, y)
        # silk tick
        gto.flash_c(x - 1.6 if x < 8 else x + 1.6, y, 0.25)

    # U1 / U2 SOIC
    u1, _, _ = soic_pin_map(*L["parts"]["U1"]["xy"], 4)
    u2, _, _ = soic_pin_map(*L["parts"]["U2"]["xy"], 8)
    for pins in (u1, u2):
        for x, y in pins.values():
            smd_r(x, y, 0.6, 1.5)

    # Body silk outline for ICs
    for key, nside in (("U1", 4), ("U2", 8)):
        ox, oy = L["parts"][key]["xy"]
        bw = 3.9 if nside == 4 else 4.0
        bh = 1.27 * (nside - 1) + 1.0
        gto.rect_outline(ox - bw / 2, oy - bh / 2, bw, bh, 0.15)
        gto.flash_c(ox - bw / 2 - 0.4, oy - bh / 2, 0.4)  # pin1 mark

    # DIP
    dip_a = dip4_pins(*L["parts"]["SW_A"]["xy"])
    dip_b = dip4_pins(*L["parts"]["SW_B"]["xy"])
    for pts, part in ((dip_a, "SW_A"), (dip_b, "SW_B")):
        for x, y in pts:
            pth(x, y, pad=1.6, hole=0.8)
        ox, oy = L["parts"][part]["xy"]
        gto.rect_outline(ox - 6, oy - 3.2, 12, 6.4, 0.15)

    # SPDT
    for key in ("SW_M", "SW_CN", "SW_HOLD"):
        pins = spdt_pins(*L["parts"][key]["xy"])
        for x, y in pins:
            pth(x, y, pad=1.6, hole=0.9)
        ox, oy = L["parts"][key]["xy"]
        gto.rect_outline(ox - 4, oy - 2, 8, 4, 0.15)

    # Pot
    for x, y in pot_pins(*L["parts"]["RV1"]["xy"]):
        pth(x, y, pad=1.6, hole=0.9)
    ox, oy = L["parts"]["RV1"]["xy"]
    gto.rect_outline(ox - 3, oy - 4, 6, 8, 0.15)

    # LEDs + series R
    led_pad = []
    for led in L["leds"]:
        a, b = led_pads(*led["xy"])
        smd_r(a[0], a[1], 1.0, 1.0)
        smd_r(b[0], b[1], 1.0, 1.0)
        led_pad.append((a, b))
        gto.rect_outline(led["xy"][0] - 1.2, led["xy"][1] - 0.7, 2.4, 1.4, 0.12)

    for r in L["led_r"]:
        a, b = smd0603(*r["xy"])
        smd_r(a[0], a[1], 0.8, 0.9)
        smd_r(b[0], b[1], 0.8, 0.9)

    for p in L["passives"]:
        fn = smd0805 if p["kind"] == "0805" else smd0603
        a, b = fn(*p["xy"])
        w, h = (1.2, 1.0) if p["kind"] == "0805" else (0.8, 0.9)
        smd_r(a[0], a[1], w, h)
        smd_r(b[0], b[1], w, h)

    hdr = L["hdr"]

    # --- Power ---
    route_l(hdr["3V3"], u1[8], 0.4)
    route_l(hdr["GND"], u1[1], 0.4)
    route_l(hdr["3V3"], u2[16], 0.4)
    route_l(hdr["GND"], u2[8], 0.4)

    # uio6/uio7 tie GND
    route_l(hdr["uio6"], hdr["GND"], 0.4)
    route_l(hdr["uio7"], hdr["GND"], 0.4)

    # 555 OUT -> CLK
    route_l(u1[3], u2[2], 0.25)

    # Q -> S
    for qpin, sname in ((14, "S0"), (13, "S1"), (12, "S2"), (11, "S3")):
        route_l(u2[qpin], hdr[sname], 0.25)

    # Enables to 3V3 (ENP via HOLD switch center)
    for p in (10, 9, 1):  # ENT, /LOAD, /CLR
        route_l(u2[p], hdr["3V3"], 0.25)

    # HOLD switch: left=3V3, center=ENP(u2.7), right=GND  (center position = run)
    hm, hc, hg = spdt_pins(*L["parts"]["SW_HOLD"]["xy"])
    route_l(hm, hdr["3V3"], 0.25)
    route_l(hc, u2[7], 0.25)
    route_l(hg, hdr["GND"], 0.25)

    # M / Cn switches: left=3V3, center=signal, right=GND (pulldown via right when open — use center to header)
    for key, sig in (("SW_M", "M"), ("SW_CN", "Cn")):
        a, c, b = spdt_pins(*L["parts"][key]["xy"])
        route_l(a, hdr["3V3"], 0.25)
        route_l(c, hdr[sig], 0.25)
        route_l(b, hdr["GND"], 0.25)

    # DIP A/B: top row -> signals, bottom -> GND (common)
    for i in range(4):
        route_l(dip_a[i * 2], hdr[f"A{i}"], 0.25)
        route_l(dip_a[i * 2 + 1], hdr["GND"], 0.25)
        route_l(dip_b[i * 2], hdr[f"B{i}"], 0.25)
        route_l(dip_b[i * 2 + 1], hdr["GND"], 0.25)

    # LEDs: F -> R -> LED anode, cathode -> GND
    for i, name in enumerate(["F0", "F1", "F2", "F3", "AEQ"]):
        ra, rb = smd0603(*L["led_r"][i]["xy"])
        la, lb = led_pad[i]
        route_l(hdr[name], ra, 0.25)
        route_top(rb, la, 0.25)
        route_l(lb, hdr["GND"], 0.25)

    # Timing network sketch: R1/R2/C1 near 555 (functional connectivity)
    # U1 pin7 DIS, pin6 THR, pin2 TRIG classic astable
    c1a, c1b = smd0805(*next(p["xy"] for p in L["passives"] if p["ref"] == "C1"))
    r1a, r1b = smd0603(*next(p["xy"] for p in L["passives"] if p["ref"] == "R1"))
    r2a, r2b = smd0603(*next(p["xy"] for p in L["passives"] if p["ref"] == "R2"))
    pot = pot_pins(*L["parts"]["RV1"]["xy"])
    route_l(u1[7], r1a, 0.25)
    route_l(r1b, pot[0], 0.25)
    route_l(pot[2], r2a, 0.25)
    route_l(r2b, u1[6], 0.25)
    route_l(u1[6], u1[2], 0.25)  # THR-TRIG
    route_l(u1[2], c1a, 0.25)
    route_l(c1b, hdr["GND"], 0.25)
    route_l(u1[4], hdr["3V3"], 0.25)  # RESET high
    c2a, c2b = smd0603(*next(p["xy"] for p in L["passives"] if p["ref"] == "C2"))
    route_l(u1[5], c2a, 0.25)
    route_l(c2b, hdr["GND"], 0.25)

    # Decap to GND / 3V3
    for ref, vpin in (("CD1", u1[8]), ("CD2", u2[16])):
        a, b = smd0603(*next(p["xy"] for p in L["passives"] if p["ref"] == ref))
        route_l(a, vpin, 0.3)
        route_l(b, hdr["GND"], 0.3)
    ba, bb = smd0805(*next(p["xy"] for p in L["passives"] if p["ref"] == "CBULK"))
    route_l(ba, hdr["3V3"], 0.4)
    route_l(bb, hdr["GND"], 0.4)

    # Bottom GND hatch
    for x in range(12, 68, 4):
        gbl.line(x, 5, x, 47, 0.2)
    for y in range(5, 48, 4):
        gbl.line(12, y, 68, y, 0.2)

    # Title silk box
    gto.rect_outline(16, 1.2, 38, 3.2, 0.2)

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

    zpath = HERE / "74181_alu_tester_gerbers.zip"
    readme = OUT / "README_FAB.txt"
    readme.write_text(
        "\n".join(
            [
                "74181 ALU test PCB — Gerber package",
                "Size: 70 x 50 mm, 2-layer, 1.6 mm, HASL lead-free",
                "Min track/clearance: 0.25 mm / 0.2 mm",
                "Drill: PTH as Drill_PTH_Through.DRL",
                "Upload ZIP to JLCPCB / PCBWay.",
                "Assembly: ../bom.csv  Wiring: ../connections.csv  Preview: ../pcb_render.png",
                "",
            ]
        ),
        encoding="utf-8",
    )
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as zf:
        for name in files:
            zf.write(OUT / name, name)
        zf.write(readme, "README_FAB.txt")
    return zpath


# ---------------------------------------------------------------------------
# Board preview PNG
# ---------------------------------------------------------------------------
def _font(size: int):
    for name in (
        "C:/Windows/Fonts/consola.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "DejaVuSans.ttf",
    ):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def mm(x, y=None):
    """Board mm -> image px (origin bottom-left in PCB, top-left in image)."""
    # Preview: Y flipped so top of board is top of image
    if y is None:
        return int(x * SCALE)
    return int(x * SCALE), int((BOARD_H - y) * SCALE)


def build_preview(L, path: Path):
    margin = 40
    W = int(BOARD_W * SCALE) + margin * 2
    H = int(BOARD_H * SCALE) + margin * 2 + 50
    img = Image.new("RGB", (W, H), (32, 36, 40))
    d = ImageDraw.Draw(img)
    font = _font(14)
    font_s = _font(11)
    font_t = _font(18)

    ox, oy = margin, margin + 36

    def P(x, y):
        return ox + int(x * SCALE), oy + int((BOARD_H - y) * SCALE)

    # Board body (solder-mask green)
    d.rounded_rectangle(
        [P(0, BOARD_H)[0], P(0, BOARD_H)[1], P(BOARD_W, 0)[0], P(BOARD_W, 0)[1]],
        radius=8,
        fill=(20, 110, 55),
        outline=(10, 70, 35),
        width=2,
    )

    # Copper tint tracks (approximate from key routes)
    cu = (200, 160, 60)

    def track(a, b, w=2):
        d.line([P(*a), P(*b)], fill=cu, width=w)

    hdr = L["hdr"]
    u1, _, _ = soic_pin_map(*L["parts"]["U1"]["xy"], 4)
    u2, _, _ = soic_pin_map(*L["parts"]["U2"]["xy"], 8)

    # Power / key nets
    for a, b in (
        (hdr["3V3"], u1[8]),
        (hdr["GND"], u1[1]),
        (hdr["3V3"], u2[16]),
        (hdr["GND"], u2[8]),
        (u1[3], u2[2]),
    ):
        track(a, (b[0], a[1]), 3)
        track((b[0], a[1]), b, 3)
    for qpin, sname in ((14, "S0"), (13, "S1"), (12, "S2"), (11, "S3")):
        a, b = u2[qpin], hdr[sname]
        track(a, (b[0], a[1]), 2)
        track((b[0], a[1]), b, 2)

    # Mounting holes
    for mx, my in ((3, 3), (BOARD_W - 3, 3), (3, BOARD_H - 3), (BOARD_W - 3, BOARD_H - 3)):
        cx, cy = P(mx, my)
        d.ellipse([cx - 8, cy - 8, cx + 8, cy + 8], fill=(40, 40, 40), outline=(180, 180, 180))

    # Headers
    for n, (x, y) in hdr.items():
        cx, cy = P(x, y)
        d.ellipse([cx - 5, cy - 5, cx + 5, cy + 5], fill=(180, 180, 190), outline=(80, 80, 90))
        side = -1 if x < 8 else 1
        tx = cx + side * 10
        d.text((tx if side > 0 else tx - 28, cy - 6), n, fill=(240, 240, 240), font=font_s)

    def draw_soic(ox_, oy_, nside, label):
        bw = 3.9 if nside == 4 else 4.0
        bh = 1.27 * (nside - 1) + 1.0
        x0, y0 = P(ox_ - bw / 2, oy_ + bh / 2)
        x1, y1 = P(ox_ + bw / 2, oy_ - bh / 2)
        d.rectangle([x0, y0, x1, y1], fill=(25, 25, 30), outline=(200, 200, 210))
        # pin1 dot
        dx, dy = P(ox_ - bw / 2 - 0.3, oy_ - bh / 2)
        d.ellipse([dx - 3, dy - 3, dx + 3, dy + 3], fill=(220, 220, 80))
        pins, _, _ = soic_pin_map(ox_, oy_, nside)
        for x, y in pins.values():
            cx, cy = P(x, y)
            d.rectangle([cx - 3, cy - 5, cx + 3, cy + 5], fill=(210, 180, 80))
        d.text((x0, y1 + 4), label, fill=(255, 255, 255), font=font_s)

    draw_soic(*L["parts"]["U1"]["xy"], 4, "U1 7555")
    draw_soic(*L["parts"]["U2"]["xy"], 8, "U2 HC161")

    # DIP bodies
    for key, color in (("SW_A", (60, 60, 70)), ("SW_B", (60, 60, 70))):
        ox_, oy_ = L["parts"][key]["xy"]
        x0, y0 = P(ox_ - 6, oy_ + 3.2)
        x1, y1 = P(ox_ + 6, oy_ - 3.2)
        d.rectangle([x0, y0, x1, y1], fill=color, outline=(200, 200, 210))
        for i in range(4):
            sx = ox_ + (i - 1.5) * 2.54
            cx, cy = P(sx, oy_)
            d.rectangle([cx - 4, cy - 8, cx + 4, cy + 8], fill=(230, 230, 240))
        d.text((x0, y1 + 2), L["parts"][key]["label"], fill=(255, 255, 255), font=font_s)

    # SPDT
    for key in ("SW_M", "SW_CN", "SW_HOLD"):
        ox_, oy_ = L["parts"][key]["xy"]
        x0, y0 = P(ox_ - 4, oy_ + 2)
        x1, y1 = P(ox_ + 4, oy_ - 2)
        d.rectangle([x0, y0, x1, y1], fill=(70, 70, 80), outline=(220, 220, 230))
        d.text((x0, y1 + 2), L["parts"][key]["label"], fill=(255, 255, 200), font=font_s)

    # Pot
    ox_, oy_ = L["parts"]["RV1"]["xy"]
    cx, cy = P(ox_, oy_)
    d.ellipse([cx - 18, cy - 18, cx + 18, cy + 18], fill=(40, 90, 160), outline=(200, 220, 255))
    d.text((cx - 22, cy + 20), "RV1 RATE", fill=(255, 255, 255), font=font_s)

    # LEDs
    for led in L["leds"]:
        cx, cy = P(*led["xy"])
        d.ellipse([cx - 7, cy - 7, cx + 7, cy + 7], fill=(220, 40, 40), outline=(255, 180, 180))
        d.text((cx - 10, cy + 10), led["name"], fill=(255, 220, 220), font=font_s)

    # Passives as small tan rectangles
    for p in L["passives"] + [{"ref": r["ref"], "xy": r["xy"], "kind": "0603"} for r in L["led_r"]]:
        cx, cy = P(*p["xy"])
        d.rectangle([cx - 6, cy - 3, cx + 6, cy + 3], fill=(210, 180, 120), outline=(90, 70, 40))

    # Title
    d.text((ox + 10, 8), "74181 ALU tester — Tiny Tapeout S0–S3 sequencer", fill=(240, 240, 240), font=font_t)
    d.text(
        (ox + 10, H - 28),
        "70×50 mm · 2-layer · 3.3 V from TT demo board · Gerbers: 74181_alu_tester_gerbers.zip",
        fill=(180, 180, 180),
        font=font_s,
    )

    img.save(path, "PNG")
    return path


def main():
    L = layout()
    zpath = build_gerbers(L)
    preview = HERE / "pcb_render.png"
    build_preview(L, preview)
    # Keep generate_gerbers.py as thin wrapper alias
    print("Gerbers:", OUT)
    print("Zip:", zpath)
    print("Preview:", preview)


if __name__ == "__main__":
    main()
