"""2x2 plain weave (3D SG) built with TexGen's periodic voxel mesh.

Needs the TexGen application (C:/Program Files/TexGen), whose SWIG bindings are compiled for
CPython 3.9. Run from this directory:

    uv run python build.py --yarn e_glass_fibre_nittobo --name weave_set1
    uv run python build.py --yarn as4_8773_lamina --name weave_set2

Writes ../../models/texgen_weave/<name>.inp and <name>.ori (per-element yarn frames, read by
sgio through the deck's *Distribution ... Input=). The deck is TexGen's full analysis deck
(PBC equations, driver nodes, a step); sgio reads only the mesh, sets, sections and
orientations. A voxel grid is periodic by construction, so no periodicity check is needed.

TexGen writes placeholder materials Mat0 (matrix) and Mat1 (yarn); they are replaced by the
records from ../../materials.json. Material 1 of the yarn is its fibre direction (TexGen's
first orientation vector).
"""
import argparse
import json
import os
import sys
from pathlib import Path

TEXGEN_ROOT = r"C:\Program Files\TexGen"
sys.path.insert(0, os.path.join(TEXGEN_ROOT, "Python", "libxtra"))
os.add_dll_directory(TEXGEN_ROOT)
os.add_dll_directory(os.path.join(TEXGEN_ROOT, "Python", "libxtra", "TexGen"))
from TexGen.Core import CRectangularVoxelMesh, CTextileWeave2D  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "models" / "texgen_weave"


def material_block(name, record):
    e = record["elastic"]
    head = [f"*Material, Name={name}\n", "*Density\n", f"{record['density']:.12g},\n"]
    if record["isotropy"] == 0:
        return head + ["*Elastic\n", f"{e['e1']:.12g}, {e['nu12']:.12g}\n"]
    c = [e[k] for k in ("e1", "e2", "e3", "nu12", "nu13", "nu23", "g12", "g13", "g23")]
    return head + ["*Elastic, type=ENGINEERING CONSTANTS\n",
                   ", ".join(f"{v:.12g}" for v in c[:8]) + "\n", f"{c[8]:.12g}\n"]


def build(yarn, matrix, spacing, thickness, width, height, voxels, name):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    textile = CTextileWeave2D(2, 2, spacing, thickness, False)
    # The default interlacement stacks all x-yarns over all y-yarns; swapping the diagonal
    # crossings gives the over/under checkerboard of a plain weave.
    textile.SwapPosition(0, 0)
    textile.SwapPosition(1, 1)
    textile.SetYarnWidths(width)
    textile.SetYarnHeights(height)
    textile.AssignDefaultDomain()
    inp = OUT_DIR / f"{name}.inp"
    CRectangularVoxelMesh("CPeriodicBoundaries").SaveVoxelMesh(textile, str(inp), *voxels, True, True, 0)
    (OUT_DIR / f"{name}.eld").unlink()  # TexGen-internal element data, not used

    library = {m["name"]: m for m in json.loads((ROOT / "materials.json").read_text())}
    lines = inp.read_text().splitlines(keepends=True)
    start = next(i for i, l in enumerate(lines) if l.strip().lower() == "*material, name=mat0")
    stop = next(i for i, l in enumerate(lines) if l.lower().startswith("*solid section"))
    lines[start:stop] = material_block("Mat0", library[matrix]) + material_block("Mat1", library[yarn])
    inp.write_text("".join(lines))
    print(f"{name}: yarn {yarn}, matrix {matrix}, voxels {voxels}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--yarn", default="e_glass_fibre_nittobo")
    parser.add_argument("--matrix", default="epoxy_resin_sikabiresin_cr132")
    parser.add_argument("--spacing", type=float, default=1.0, help="yarn spacing")
    parser.add_argument("--thickness", type=float, default=0.2, help="fabric thickness")
    parser.add_argument("--width", type=float, default=0.8, help="yarn width")
    parser.add_argument("--height", type=float, default=0.1, help="yarn height")
    parser.add_argument("--voxels", type=int, nargs=3, default=[20, 20, 8])
    parser.add_argument("--name", default="weave_set1")
    args = parser.parse_args()
    build(args.yarn, args.matrix, args.spacing, args.thickness, args.width, args.height,
          args.voxels, args.name)
