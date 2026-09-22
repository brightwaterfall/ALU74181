# Walkthrough — clone to green Tiny Tapeout CI / harden

Repo: https://github.com/brightwaterfall/ALU74181

Verified on this project (push `403d9e8`):

| Workflow job | Result |
|--------------|--------|
| `test` | success |
| `docs` | success |
| `gds` (LibreLane harden) | success |
| `precheck` | success |
| `gl_test` (gate-level) | success |
| `viewer` (GitHub Pages) | enable Pages under Settings → Pages → GitHub Actions, then re-run `gds` |

## 1. Clone

```bash
git clone https://github.com/brightwaterfall/ALU74181.git
cd ALU74181
```

## 2. RTL simulation (cocotb + Icarus)

```bash
cd test
pip install -r requirements.txt
make clean
make
# Pass: no <failure> / <error> in results.xml
```

Offline golden model (no Icarus):

```bash
pip install pytest
pytest test_golden_unit.py -q
```

## 3. Local harden (optional; same as CI `gds` job)

Requires Docker + Python 3.11+. Official guide: https://www.tinytapeout.com/guides/local-hardening/

```bash
git clone https://github.com/TinyTapeout/tt-support-tools tt
python3 -m venv ~/ttsetup/venv
source ~/ttsetup/venv/bin/activate   # Windows: ttsetup\venv\Scripts\activate
pip install -r tt/requirements.txt
export PDK_ROOT=~/ttsetup/pdk
export PDK=sky130A
export LIBRELANE_TAG=3.0.3           # match tt-gds-action default if updated
pip install librelane==$LIBRELANE_TAG

./tt/tt_tool.py --create-user-config
./tt/tt_tool.py --harden
./tt/tt_tool.py --print-warnings
./tt/tt_tool.py --create-png
```

Outputs land under `runs/` (GDS, LEF, netlist, PNG). CI uploads the same class of files as the `tt_submission` / `gds_render` artifacts.

> Note: older docs mention `make lf` (OpenLane). Current Tiny Tapeout SKY flow uses **LibreLane via `tt_tool.py --harden`** (what GitHub Actions runs).

## 4. GitHub Actions

On every push to `main`:

- **test** — cocotb RTL
- **gds** — harden + precheck + gate-level test + viewer
- **docs** — datasheet

Enable **Pages** (Settings → Pages → Deploy from GitHub Actions) so the viewer job can publish.

## 5. Tagged release with GDS

After a green `gds` run:

1. Download artifacts `tt_submission` and `gds_render` from the Actions run
2. Tag and publish:

```bash
git tag -a v1.0.0 -m "74181 ALU — TT harden artifacts"
git push origin v1.0.0
gh release create v1.0.0 --title "v1.0.0" --notes "Tiny Tapeout 74181 ALU GDS package" tt_submission.zip gds_render.png
```

## 6. Shuttle submission

1. https://app.tinytapeout.com/
2. Link `brightwaterfall/ALU74181`
3. Select shuttle / complete payment
4. Confirm automated checks are green

## 7. Test PCB

See [`pcb/`](pcb/). Auto-sequences **S0–S3** through all 16 functions; LEDs show **F**.
