"""UD FRP cross-section (2D SG) built with gmshModel's RandomInclusionRVE.

Run from this directory:

    uv run python build.py --fibre e_glass_fibre_nittobo --name udfrp_set1
    uv run python build.py --fibre t300_carbon_fibre --name udfrp_set2

Writes ../../models/gmshmodel_udfrp/<name>.msh and <name>.sg.json, the SG manifest sgio reads
(file_format='sg_manifest'): SG dimension, model space and the physical group -> material
binding that a bare .msh cannot carry.

Randomly placed, non-overlapping circular fibres in a unit square, periodic in x and y. The
mesh lies in the xy plane, which sgio maps to the SG plane (y2, y3); z is y1, the fibre axis.
No element frame is written, so every material keeps SwiftComp's default frame: material 1
along y1. For a transversely isotropic fibre that puts its axis along the fibres already.
"""
import argparse
import json
from pathlib import Path

import numpy as np
from gmshModel.Model import RandomInclusionRVE

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "models" / "gmshmodel_udfrp"


def build(fibre, matrix, radius, count, seed, name):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    np.random.seed(seed)  # placeInclusions draws from the global RNG
    rve = RandomInclusionRVE(
        inclusionSets=[[radius, count]], size=[1.0, 1.0], inclusionType="Circle",
        periodicityFlags=[1, 1], domainGroup="matrix", inclusionGroup="fibre",
    )
    rve.createGmshModel()
    rve.createMesh(refinementOptions={"elementsPerCircumference": 24})
    rve.saveMesh(file=str(OUT_DIR / f"{name}.msh"))
    placed = int(rve.placementInfo[0])
    rve.close()
    if placed != count:
        raise RuntimeError(f"placed only {placed}/{count} fibres; lower the count or radius")

    library = {m["name"]: m for m in json.loads((ROOT / "materials.json").read_text())}
    manifest = {
        "sg_manifest_version": 1,
        "model_file": {"path": f"{name}.msh", "format": "gmsh"},
        "sgdim": 2,
        "model_type": "SD1",
        "model_space": "xy",
        "materials": [library[matrix], library[fibre]],
        "sections": [
            {"name": "matrix", "material": matrix},
            {"name": "fibre", "material": fibre},
        ],
    }
    (OUT_DIR / f"{name}.sg.json").write_text(json.dumps(manifest, indent=2))
    print(f"{name}: {placed} fibres, fibre volume fraction {placed * np.pi * radius**2:.3f}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--fibre", default="e_glass_fibre_nittobo")
    parser.add_argument("--matrix", default="epoxy_resin_sikabiresin_cr132")
    parser.add_argument("--radius", type=float, default=0.1)
    parser.add_argument("--count", type=int, default=16)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--name", default="udfrp_set1")
    args = parser.parse_args()
    build(args.fibre, args.matrix, args.radius, args.count, args.seed, args.name)
