"""Model files -> sgio -> SwiftComp -> effective C and density -> anisotropy measure -> publish.

Reads the builder outputs under models/ (see build_all.py), so it runs without any builder
installed. Writes .sg/.sg.k per case under results/<builder>/ and results/summary.csv. For the
representative cases (marked "baseline" in summary.csv) it also writes a PyVista .html with the
element local axes (red/green/blue) and a .png of the mesh.

Finally copies what the article needs into the msg-examples example folder (PUBLISH_DIR): data,
results, images, and these scripts under workflow/. Bulky files (the representative .sg inputs)
go to its tmp/, which git ignores; the .html views stay here.
"""
import csv
import shutil
from pathlib import Path

import numpy as np
import pyvista as pv
import sgio
from PIL import Image, ImageDraw, ImageFont

from build_all import SWEEPS, case_name
from scripts.energy_ratio import energy_ratio_based_measure

HERE = Path(__file__).resolve().parent
pv.OFF_SCREEN = True  # .png snapshots without opening a window
PUBLISH_DIR = HERE.parents[1] / "msg-examples" / "examples" / "multi_builder_anisotropy"
# Scripts mirrored into PUBLISH_DIR/workflow/ (same layout as here; edit them here, not there)
SCRIPTS = ["build_all.py", "run.py", "pyproject.toml", "builders/abaqus_honeycomb/build.py",
           *(f"builders/{b}/{f}" for b in ("gmshmodel_udfrp", "microgen_tpms", "texgen_weave")
             for f in ("build.py", "pyproject.toml"))]

# builder: (input format, SG dimension). A .msh carries no materials, so Gmsh models come
# with an SG manifest that references the mesh.
FORMATS = {
    "abaqus_honeycomb": ("abaqus", 2),
    "gmshmodel_udfrp": ("sg_manifest", 2),
    "microgen_tpms": ("sg_manifest", 3),
    "texgen_weave": ("abaqus", 3),
}
EXT = {"abaqus": ".inp", "sg_manifest": ".sg.json"}
LABELS = {"abaqus_honeycomb": "Honeycomb", "gmshmodel_udfrp": "UD FRP",
          "microgen_tpms": "Schwarz-P TPMS", "texgen_weave": "Plain weave"}


def snapshot(builder, case):
    """Write <case>.html (element frames) and <case>.png (mesh + x/y/z triad) from the written .sg.

    The plot axes are the SG axes y1, y2, y3, labelled x, y, z as in the article's figures.
    """
    sgdim = FORMATS[builder][1]
    sg_file = HERE / "results" / builder / f"{case}.sg"
    # Read the written .sg back, so the plot shows the element frames SwiftComp actually gets
    sg = sgio.read(str(sg_file), "sc", sgdim=sgdim, model_type="SD1")
    sgio.plot_sg_pyvista(sg, show_local_axes=True, output_html=sg_file.with_suffix(".html"))
    plotter = sgio.plot_sg_pyvista(sg)
    if builder == "texgen_weave":  # matrix voxels (property 1) hide the yarns; colour yarns by height
        yarns = plotter.mesh.threshold(1.5, scalars="property_id")
        plotter = pv.Plotter()
        plotter.add_mesh(yarns, scalars=yarns.cell_centers().points[:, 2], cmap="coolwarm",
                         show_edges=True, show_scalar_bar=False)
    if sgdim == 2:
        plotter.view_yz()  # 2D SGs lie in the (y, z) plane; x is the fibre / prism axis
    plotter.remove_legend()  # "Property N" says nothing the caption does not
    plotter.add_axes(xlabel="x", ylabel="y", zlabel="z", line_width=4, viewport=(0, 0, 0.25, 0.25))
    image = plotter.screenshot(window_size=(800, 720), return_img=True)
    rows, cols = np.nonzero((image < 245).any(axis=2))  # crop the white margin
    image = image[max(rows.min() - 10, 0):rows.max() + 10, max(cols.min() - 10, 0):cols.max() + 10]
    Image.fromarray(image).save(sg_file.with_suffix(".png"))


def gallery(cases, out, cell=(450, 405)):
    """2x2 grid of the <case>.png snapshots [(builder, case), ...], each labelled with its model."""
    try:
        font = ImageFont.truetype("arial.ttf", 28)
    except OSError:
        font = ImageFont.load_default()
    w, h = cell
    sheet = Image.new("RGB", (2 * w, 2 * h), "white")
    for index, (builder, case) in enumerate(cases):
        tile = Image.open(HERE / "results" / builder / f"{case}.png").convert("RGB")
        tile.thumbnail((w - 20, h - 50))
        x0, y0 = (index % 2) * w, (index // 2) * h
        sheet.paste(tile, (x0 + (w - tile.width) // 2, y0 + 40 + (h - 40 - tile.height) // 2))
        ImageDraw.Draw(sheet).text((x0 + w // 2, y0 + 8), LABELS[builder], fill="black", font=font, anchor="mt")
    sheet.save(out)


def run_case(builder, case, plot):
    file_format, sgdim = FORMATS[builder]
    source = HERE / "models" / builder / f"{case}{EXT[file_format]}"
    sg_file = HERE / "results" / builder / f"{case}.sg"
    sg_file.parent.mkdir(parents=True, exist_ok=True)
    sgio.convert(str(source), str(sg_file), file_format, "sc", file_version_out="2.1",
                 sgdim=sgdim, model_space="xy" if sgdim == 2 else None, model_type="SD1")
    if plot:
        snapshot(builder, case)
    sgio.run("swiftcomp", str(sg_file), "h", smdim=3, scrnout=False)
    model = sgio.read_output_model(f"{sg_file}.k", "sc", "sd1")
    if not model.density > 0:  # a material without density makes SwiftComp report 0
        raise ValueError(f"{case}: effective density is {model.density}")
    return np.asarray(model.stff), model.density


def publish(rows):
    """Copy the files the article reads into PUBLISH_DIR."""
    def copy(src, dst):
        dst = PUBLISH_DIR / dst
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)

    copy(HERE / "materials.json", "data/materials.json")
    for script in SCRIPTS:
        copy(HERE / script, f"workflow/{script}")
    copy(HERE / "scripts" / "energy_ratio.py", "energy_ratio.py")
    copy(HERE / "results" / "summary.csv", "results/summary.csv")
    for row in rows:
        builder, case = row["builder"], row["case"]
        copy(HERE / "results" / builder / f"{case}.sg.k", f"results/{builder}/{case}.sg.k")
        if row["baseline"]:
            copy(HERE / "results" / builder / f"{case}.sg", f"tmp/{builder}/{case}.sg")
            copy(HERE / "results" / builder / f"{case}.png", f"images/{case}.png")
    gallery([(r["builder"], r["case"]) for r in rows if r["baseline"] and r["material"] == "set1"],
            PUBLISH_DIR / "images" / "sg_models.png")


def main():
    rows = []
    for builder, (_, parameter, _, values, baseline, materials, _) in SWEEPS.items():
        for material in materials:
            for value in values:
                case = case_name(builder, material, value)
                C, density = run_case(builder, case, plot=value == baseline)
                A = energy_ratio_based_measure(C)
                print(f"{builder}/{case}: A_energy_ratio = {A:.4f}", flush=True)
                rows.append({"builder": builder, "case": case, "material": material,
                             "parameter": parameter, "value": float(value),
                             "baseline": int(value == baseline), "density": density,
                             "A_energy_ratio": A,
                             **{f"C{i + 1}{j + 1}": C[i, j] for i in range(6) for j in range(i, 6)}})
    with open(HERE / "results" / "summary.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    if PUBLISH_DIR.is_dir():  # only in the author's workspace, next to the msg-examples repo
        publish(rows)


if __name__ == "__main__":
    main()
