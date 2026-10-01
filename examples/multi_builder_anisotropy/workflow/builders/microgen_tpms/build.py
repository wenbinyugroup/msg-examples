"""Schwarz-P TPMS sheet (3D SG) built with microgen.

Run from this directory (after `uv sync`, re-pin VTK: microgen's cadquery-ocp vendors its own
VTK into the same vtkmodules/ folder and breaks pyvista's):

    uv pip install --reinstall --no-deps vtk==9.3.1
    uv run python build.py --material peek_victrex_450g --name tpms_set1
    uv run python build.py --material ti6al4v_am --name tpms_set2

Writes ../../models/microgen_tpms/<name>.msh and <name>.sg.json (the SG manifest sgio reads).

Tpms.generate(sheet) -> periodic_split_and_translate -> STEP -> mesh_periodic. Only the solid
sheet is meshed (void is not a phase), as physical group "Mat0". No element frame is written:
the material frame is the global one.
"""
import argparse
import json
from pathlib import Path

import gmsh
import numpy as np
from microgen import Phase, Rve, Tpms, mesh_periodic, periodic_split_and_translate, surface_functions
from microgen.mesh import OutputMeshNotPeriodicError

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "models" / "microgen_tpms"


def check_periodic(mesh_file, tol=1e-6):
    """Fail unless boundary nodes on opposite cell faces pair up by pure translation.

    Nearest-neighbour matching instead of microgen's own check, which assumes the same node
    ordering on opposite faces and false-fails for a sheet crossing a face in several loops.
    """
    gmsh.initialize()
    gmsh.open(str(mesh_file))
    coords = gmsh.model.mesh.getNodes()[1].reshape(-1, 3)
    gmsh.finalize()
    lo, hi = coords.min(axis=0), coords.max(axis=0)
    for axis in range(3):
        other = [a for a in range(3) if a != axis]
        on_lo = coords[np.abs(coords[:, axis] - lo[axis]) < tol][:, other]
        on_hi = coords[np.abs(coords[:, axis] - hi[axis]) < tol][:, other]
        if len(on_lo) != len(on_hi) or any(np.linalg.norm(on_hi - p, axis=1).min() > tol for p in on_lo):
            raise RuntimeError(f"mesh not periodic along axis {axis}")


def build(material, offset, mesh_size, name):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rve = Rve(dim=1.0, center=(0, 0, 0))
    shape = Tpms(surface_function=surface_functions.schwarzP, offset=offset, cell_size=1.0,
                 repeat_cell=1, resolution=20).generate(type_part="sheet")
    volume_fraction = shape.Volume()
    phase = periodic_split_and_translate(Phase(shape=shape), rve)
    step_file = OUT_DIR / f"{name}.step"
    phase.shape.exportStep(str(step_file))

    mesh_file = OUT_DIR / f"{name}.msh"
    try:
        mesh_periodic(mesh_file=str(step_file), rve=rve, list_phases=[phase], size=mesh_size,
                      order=1, output_file=str(mesh_file), msh_file_version=4)
    except OutputMeshNotPeriodicError:
        pass  # the mesh is written before microgen's own check; check_periodic decides
    check_periodic(mesh_file)
    step_file.unlink()

    library = {m["name"]: m for m in json.loads((ROOT / "materials.json").read_text())}
    manifest = {
        "sg_manifest_version": 1,
        "model_file": {"path": f"{name}.msh", "format": "gmsh"},
        "sgdim": 3,
        "model_type": "SD1",
        "materials": [library[material]],
        "sections": [{"name": "Mat0", "material": material}],
    }
    (OUT_DIR / f"{name}.sg.json").write_text(json.dumps(manifest, indent=2))
    print(f"{name}: offset {offset}, solid volume fraction {volume_fraction:.3f}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--material", default="peek_victrex_450g")
    parser.add_argument("--offset", type=float, default=0.5, help="sheet thickness parameter")
    parser.add_argument("--mesh-size", type=float, default=0.05)
    parser.add_argument("--name", default="tpms_set1")
    args = parser.parse_args()
    build(args.material, args.offset, args.mesh_size, args.name)
