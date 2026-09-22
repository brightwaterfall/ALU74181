#!/usr/bin/env python3
"""Virtual verification suite for ALU74181 deliverables."""
from __future__ import annotations

import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "test"))
from golden_model import alu74181, logic_f, arith_f  # noqa: E402

errs: list[str] = []
oks: list[str] = []


def ok(msg: str) -> None:
    oks.append(msg)
    print("PASS:", msg)


def fail(msg: str) -> None:
    errs.append(msg)
    print("FAIL:", msg)


def check_info_yaml() -> None:
    try:
        import yaml
    except ImportError:
        # minimal parse
        text = (ROOT / "info.yaml").read_text(encoding="utf-8")
        tm = re.search(r'top_module:\s*"([^"]+)"', text)
        tiles = re.search(r'tiles:\s*"([^"]+)"', text)
        srcs = re.findall(r'-\s*"([^"]+\.v)"', text)
        top = tm.group(1) if tm else ""
        if not top.startswith("tt_um_"):
            fail("top_module prefix")
        else:
            ok(f"top_module={top}")
        if tiles and tiles.group(1) == "1x1":
            ok("tiles=1x1")
        else:
            fail(f"tiles={tiles}")
        for f in srcs:
            if (ROOT / "src" / f).is_file():
                ok(f"source {f}")
            else:
                fail(f"missing {f}")
        proj = (ROOT / "src" / "project.v").read_text(encoding="utf-8")
        if f"module {top}" in proj:
            ok("project.v module matches info.yaml")
        else:
            fail("project.v module mismatch")
        return

    import yaml

    info = yaml.safe_load((ROOT / "info.yaml").read_text(encoding="utf-8"))
    p = info["project"]
    if not p["top_module"].startswith("tt_um_"):
        fail("top_module prefix")
    else:
        ok(f"top_module={p['top_module']}")
    if p["tiles"] != "1x1":
        fail(f"tiles={p['tiles']}")
    else:
        ok("tiles=1x1")
    for f in p["source_files"]:
        if (ROOT / "src" / f).is_file():
            ok(f"source {f}")
        else:
            fail(f"missing {f}")
    proj = (ROOT / "src" / "project.v").read_text(encoding="utf-8")
    if f"module {p['top_module']}" not in proj:
        fail("project.v module mismatch")
    else:
        ok("project.v module matches")
    for port in ["ui_in", "uo_out", "uio_in", "uio_out", "uio_oe", "ena", "clk", "rst_n"]:
        if port not in proj:
            fail(f"missing port {port}")
    else:
        ok("TT ports present")
    # pinout completeness
    po = info["pinout"]
    for i in range(8):
        for pref in ("ui", "uo", "uio"):
            if f"{pref}[{i}]" not in po:
                fail(f"missing pinout {pref}[{i}]")
    ok("pinout keys 0..7 for ui/uo/uio")


def check_exhaustive_golden() -> None:
    n = 0
    for a in range(16):
        for b in range(16):
            for s in range(16):
                f, aeq, cn4 = alu74181(a, b, s, 1, 1)
                assert f == logic_f(a, b, s)
                assert aeq == (1 if f == 0xF else 0)
                assert cn4 == 1
                n += 1
                for cn_n in (0, 1):
                    f2, _, cn4b = alu74181(a, b, s, 0, cn_n)
                    exp_f, exp_c = arith_f(a, b, s, 0 if cn_n else 1)
                    assert f2 == exp_f, (a, b, s, cn_n, f2, exp_f)
                    assert cn4b == (0 if exp_c else 1)
                    n += 1
    ok(f"exhaustive golden vectors checked ({n})")


def check_verilog_wrapper_map() -> None:
    """Sanity: packing used by cocotb matches project.v comments."""
    proj = (ROOT / "src" / "project.v").read_text(encoding="utf-8")
    for needle in [
        "ui_in[3:0]",
        "ui_in[7:4]",
        "uio_in[3:0]",
        "uio_in[4]",
        "uio_in[5]",
        "uo_out",
    ]:
        if needle not in proj:
            fail(f"wrapper map missing {needle}")
            return
    ok("wrapper pin map comments/wires present")


def check_gerbers() -> None:
    gdir = ROOT / "pcb" / "gerbers"
    need = [
        "Gerber_TopLayer.GTL",
        "Gerber_BottomLayer.GBL",
        "Gerber_TopSolderMaskLayer.GTS",
        "Gerber_BottomSolderMaskLayer.GBS",
        "Gerber_TopSilkscreenLayer.GTO",
        "Gerber_BoardOutlineLayer.GKO",
        "Drill_PTH_Through.DRL",
    ]
    for n in need:
        p = gdir / n
        if not p.is_file() or p.stat().st_size < 50:
            fail(f"gerber missing/small {n}")
        else:
            text = p.read_text(encoding="ascii", errors="replace")
            if n.endswith(".DRL"):
                if "M30" not in text and "M48" not in text:
                    fail(f"drill format {n}")
                else:
                    ok(f"drill {n} ({p.stat().st_size}B)")
            else:
                if "%FSLAX" not in text or "M02*" not in text:
                    fail(f"gerber format {n}")
                else:
                    ok(f"gerber {n} ({p.stat().st_size}B)")
    z = ROOT / "pcb" / "74181_alu_tester_gerbers.zip"
    if not z.is_file():
        fail("gerber zip missing")
    else:
        with zipfile.ZipFile(z) as zf:
            names = zf.namelist()
            for n in need:
                if n not in names:
                    fail(f"zip missing {n}")
            ok(f"gerber zip OK ({len(names)} files, {z.stat().st_size}B)")


def check_docs() -> None:
    for rel in [
        "WALKTHROUGH.md",
        "README.md",
        "docs/info.md",
        "pcb/README.md",
        "pcb/BRINGUP.md",
        "pcb/SCHEMATIC.md",
        "pcb/bom.csv",
        "pcb/connections.csv",
        "test/Makefile",
        "test/test.py",
        "test/tb.v",
        ".github/workflows/test.yaml",
        ".github/workflows/gds.yaml",
        ".github/workflows/docs.yaml",
    ]:
        if (ROOT / rel).is_file():
            ok(f"file {rel}")
        else:
            fail(f"missing {rel}")


def check_tt_submission_artifact() -> None:
    art = ROOT / "release_artifacts" / "tt_submission"
    gds = list(art.rglob("*.gds")) if art.exists() else []
    if not gds:
        # try zip in release_artifacts
        z = ROOT / "release_artifacts" / "tt_submission.zip"
        if z.is_file():
            with zipfile.ZipFile(z) as zf:
                gds_names = [n for n in zf.namelist() if n.endswith(".gds")]
                if gds_names:
                    ok(f"local tt_submission.zip has GDS ({gds_names[0]})")
                else:
                    fail("tt_submission.zip has no .gds")
        else:
            fail("no local GDS artifact (rely on GitHub release)")
    else:
        ok(f"local GDS {gds[0].name} ({gds[0].stat().st_size}B)")
        lef = list(art.rglob("*.lef"))
        if lef:
            ok(f"local LEF {lef[0].name}")
        else:
            fail("no LEF in artifacts")


def main() -> int:
    print("=== DELIVERABLE FILES ===")
    check_docs()
    print("\n=== info.yaml / RTL ===")
    check_info_yaml()
    check_verilog_wrapper_map()
    print("\n=== GOLDEN MODEL (exhaustive) ===")
    check_exhaustive_golden()
    print("\n=== PCB GERBERS ===")
    check_gerbers()
    print("\n=== GDS ARTIFACTS ===")
    check_tt_submission_artifact()
    print("\n=== SUMMARY ===")
    print(f"Passed: {len(oks)}  Failed: {len(errs)}")
    for e in errs:
        print(" -", e)
    return 1 if errs else 0


if __name__ == "__main__":
    raise SystemExit(main())
