# Walkthrough — clone to green CI / harden

This document reproduces the Tiny Tapeout digital flow for `gddwms/ALU74181`.

## 1. Clone

```bash
git clone https://github.com/gddwms/ALU74181.git
cd ALU74181
```

## 2. Simulate (cocotb + Icarus)

Requirements: Python 3.11+, `iverilog`, `pip`.

```bash
cd test
pip install -r requirements.txt
make clean
make
# Pass when results.xml has no failure/error entries
```

On Windows, use WSL or the repo `.devcontainer` for the same commands.

## 3. Project metadata

Edit only if needed:

- `info.yaml` — title, author, `top_module`, `source_files`, pin names
- `src/project.v` — TT wrapper `tt_um_gddwms_alu74181`
- `src/alu74181.v` — ALU core
- `docs/info.md` — datasheet text

## 4. GitHub Actions

On push to `main`:

- `test` — RTL cocotb suite
- `gds` — LibreLane harden (GDS/LEF/netlist artifacts)
- `docs` — datasheet / pages

Enable **GitHub Pages** from Actions if the docs workflow requests it:
https://tinytapeout.com/faq/#my-github-action-is-failing-on-the-pages-part

## 5. Local harden (optional)

Follow Tiny Tapeout “build locally” docs with LibreLane / the official container.
Target command patterns match the GDS workflow (often summarized as a successful harden / `make` equivalent in the TT tooling). Artifacts include GDS, LEF, and gate-level netlist under the action upload or `runs/` output.

## 6. Tagged release

After CI is green:

```bash
git tag -a v1.0.0 -m "74181 ALU TT submission"
git push origin v1.0.0
```

Attach or download GDS artifacts from the successful `gds` workflow run into the GitHub Release.

## 7. Shuttle submission

1. Open https://app.tinytapeout.com/
2. Link this GitHub repository
3. Select the shuttle / pay as required
4. Confirm the project passes the automated checks shown in the app

## PCB test board

PCB bring-up is a separate deliverable (KiCad + Gerbers) once the breakout / LED / switch behavior is specified.
