"""Hexagonal honeycomb 2D SG built with Abaqus/CAE scripting.

Run from this directory:

    abaqus cae noGUI=build.py -- --t-over-l 0.1 --material aluminum_5052_h32 --name honeycomb_set1
    abaqus cae noGUI=build.py -- --t-over-l 0.1 --material as4_8773_lamina --ply-angle 90 --name honeycomb_set2

Writes ../../models/abaqus_honeycomb/<name>.inp (Job.writeInput only, never submitted).

Geometry ("skeleton + offset lines"): the wall centerlines of one pointy-top hexagon (edge l)
plus two vertical half-walls above and below form the skeleton. Offsetting it by t/2 on both
sides gives the wall; the periodic cell is sqrt(3) l x 3 l centred on the hexagon, so the two
vertical walls lie on the left/right cell edges (half inside) and the stubs are cut at their
midpoints by the top/bottom cell edges.

The skeleton is then used again to partition the wall, which leaves every wall centerline as
a geometric edge. A DISCRETE orientation takes Abaqus local 1 along the nearest centerline
edge and local 3 = z, so each wall gets its own direction without per-wall bookkeeping.

Axis convention (SwiftComp 2D SG, as mapped by sgio with model_space='xy'): Abaqus (x, y, z)
-> SG (y2, y3, y1), and Abaqus local (1, 2, 3) -> element frame (y2', y3', y1'). So y1' is the
prism axis, y2' runs along the wall and y3' through its thickness, like a laminate wall in a
VABS cross-section. Material constants are given in the material frame (1 = fibre), which is
the element frame rotated about y3' by the ply angle: 0 deg puts the fibre along the prism
axis, 90 deg along the wall. The ply angle goes into a one-ply CompositeLayup, whose section
angle sgio reads as the SwiftComp in-plane rotation angle. (Abaqus itself would rotate that
ply about z; the deck is never solved in Abaqus.)
"""
import argparse
import json
import math
import os
import sys

from abaqus import mdb
from abaqusConstants import (
    AXIS_1, AXIS_3, CPS6M, CPS8, DEFORMABLE_BODY, DISCRETE, EDGE, ENGINEERING_CONSTANTS, FIXED,
    FREE, FROM_SECTION, OFF, ON, QUAD_DOMINATED, ROTATION_NONE, SOLID, SPECIFY_ORIENT,
    SPECIFY_THICKNESS, STANDARD, STACK_3, TWO_D_PLANAR, VECTOR,
)
import mesh

HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT_DIR = os.path.join(ROOT, "models", "abaqus_honeycomb")


def polygon(sketch, points):
    for a, b in zip(points, points[1:] + points[:1]):
        sketch.Line(point1=a, point2=b)


def build(l, t, material, ply_angle, name):
    a = math.sqrt(3) / 2 * l  # hexagon apothem = half cell width
    ly = 3 * l
    h = t / 3  # mesh size: ~3 quadratic elements through the wall
    eps = 1e-6 * l
    model = mdb.Model(name="Honeycomb")

    # --- skeleton: wall centerlines (the two vertical hexagon edges are the cell's side edges) ---
    top, bottom = (0.0, l), (0.0, -l)
    skeleton = [
        ((-a, l / 2), top), (top, (a, l / 2)), ((-a, -l / 2), bottom), (bottom, (a, -l / 2)),
        (top, (0.0, ly / 2)), (bottom, (0.0, -ly / 2)),
        ((-a, -l / 2), (-a, l / 2)), ((a, -l / 2), (a, l / 2)),
    ]

    # --- wall = skeleton offset by t/2 to both sides, clipped by the cell ---
    yj = l + t / (2 * math.sqrt(3))  # where the stub sides meet the outer offsets
    ys = l / 2 + t / math.sqrt(3)  # where the outer offsets meet the cell side edges
    outer = [(t / 2, ly / 2), (t / 2, yj), (a, ys), (a, -ys), (t / 2, -yj), (t / 2, -ly / 2),
             (-t / 2, -ly / 2), (-t / 2, -yj), (-a, -ys), (-a, ys), (-t / 2, yj), (-t / 2, ly / 2)]
    r_in = l - t / math.sqrt(3)  # inner offset hexagon, circumradius
    inner = [(r_in * math.cos(math.radians(90 + 60 * k)), r_in * math.sin(math.radians(90 + 60 * k)))
             for k in range(6)]
    sketch = model.ConstrainedSketch(name="wall", sheetSize=4 * ly)
    polygon(sketch, outer)
    polygon(sketch, inner)
    part = model.Part(name="Cell", dimensionality=TWO_D_PLANAR, type=DEFORMABLE_BODY)
    part.BaseShell(sketch=sketch)

    # --- partition by the skeleton so the centerlines become edges ---
    cut = model.ConstrainedSketch(name="skeleton", sheetSize=4 * ly)
    for p1, p2 in skeleton[:6]:  # the side-edge centerlines already are cell edges
        cut.Line(point1=p1, point2=p2)
    part.PartitionFaceBySketch(faces=part.faces, sketch=cut)
    mid = lambda seg: ((seg[0][0] + seg[1][0]) / 2, (seg[0][1] + seg[1][1]) / 2, 0.0)
    centerlines = part.Set(name="CENTERLINES", edges=part.edges.findAt(*[(mid(s),) for s in skeleton]))
    wall = part.Set(name="WALL", faces=part.faces)

    # --- material, one-ply layup, discrete orientation along the nearest centerline ---
    record = {m["name"]: m for m in json.load(open(os.path.join(ROOT, "materials.json")))}[material]
    e = record["elastic"]
    mat = model.Material(name=material)
    mat.Density(table=((record["density"],),))
    if record["isotropy"] == 0:
        mat.Elastic(table=((e["e1"], e["nu12"]),))
    else:
        mat.Elastic(type=ENGINEERING_CONSTANTS, table=((
            e["e1"], e["e2"], e["e3"], e["nu12"], e["nu13"], e["nu23"], e["g12"], e["g13"], e["g23"]),))
    layup = part.CompositeLayup(name="Wall", elementType=SOLID, symmetric=False,
                                thicknessAssignment=FROM_SECTION, description="")
    layup.CompositePly(
        plyName="Ply-1", region=wall, material=material, thicknessType=SPECIFY_THICKNESS, thickness=1.0,
        orientationType=SPECIFY_ORIENT, orientationValue=ply_angle, additionalRotationType=ROTATION_NONE,
        additionalRotationField="", axis=AXIS_3, angle=0.0, numIntPoints=1, suppressed=False)
    layup.ReferenceOrientation(
        orientationType=DISCRETE, localCsys=None, stackDirection=STACK_3,
        normalAxisDefinition=VECTOR, normalAxisVector=(0.0, 0.0, 1.0), normalAxisDirection=AXIS_3,
        primaryAxisDefinition=EDGE, primaryAxisRegion=centerlines, primaryAxisDirection=AXIS_1,
        flipNormalDirection=False, flipPrimaryDirection=False,
        additionalRotationType=ROTATION_NONE, additionalRotationField="", axis=AXIS_3, angle=0.0)

    # --- mesh: equal seed counts on opposite cell edges keep the mesh periodic ---
    part.seedPart(size=h, deviationFactor=0.1, minSizeFactor=0.1)
    for x1, y1, x2, y2 in ((-a, -ly / 2, -a, ly / 2), (a, -ly / 2, a, ly / 2),
                           (-a, -ly / 2, a, -ly / 2), (-a, ly / 2, a, ly / 2)):
        for edge in part.edges.getByBoundingBox(x1 - eps, y1 - eps, -eps, x2 + eps, y2 + eps, eps):
            n = max(2, int(math.ceil(edge.getSize(printResults=False) / h - 1e-6)))  # same n on both sides
            part.seedEdgeByNumber(edges=part.edges[edge.index:edge.index + 1], number=n, constraint=FIXED)
    part.setMeshControls(regions=part.faces, elemShape=QUAD_DOMINATED, technique=FREE)
    part.setElementType(regions=(part.faces,), elemTypes=(
        mesh.ElemType(elemCode=CPS8, elemLibrary=STANDARD), mesh.ElemType(elemCode=CPS6M, elemLibrary=STANDARD)))
    part.generateMesh()
    check_periodic([n.coordinates for n in part.nodes], a, ly / 2, eps)

    model.rootAssembly.Instance(name="Cell-1", part=part, dependent=ON)
    if not os.path.isdir(OUT_DIR):
        os.makedirs(OUT_DIR)
    os.chdir(OUT_DIR)  # writeInput always writes into the current directory
    mdb.Job(name=name, model="Honeycomb").writeInput(consistencyChecking=OFF)


def check_periodic(coords, half_x, half_y, tol):
    """Fail unless boundary nodes on opposite cell edges pair up by pure translation."""
    for axis, half in ((0, half_x), (1, half_y)):
        lo = sorted(round(c[1 - axis], 9) for c in coords if abs(c[axis] + half) < tol)
        hi = sorted(round(c[1 - axis], 9) for c in coords if abs(c[axis] - half) < tol)
        if not lo or len(lo) != len(hi) or any(abs(p - q) > tol for p, q in zip(lo, hi)):
            raise RuntimeError("mesh not periodic along axis %d" % axis)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--t-over-l", type=float, default=0.1)
    parser.add_argument("--material", default="aluminum_5052_h32")
    parser.add_argument("--ply-angle", type=float, default=0.0, help="deg, about y3' (wall normal)")
    parser.add_argument("--name", default="honeycomb_set1")
    args, _ = parser.parse_known_args(sys.argv[1:])
    build(1.0, args.t_over_l, args.material, args.ply_angle, args.name)
