# ------------------------------------------------------------------------------
#
#  Gmsh Python tutorial 18
#
#  Periodic meshes
#
# ------------------------------------------------------------------------------

# Periodic meshing constraints can be imposed on surfaces and curves.

import gmsh
import math
import os
import sys

gmsh.initialize()

gmsh.model.add("t18")

# Let's use the OpenCASCADE geometry kernel to build two geometries.

# The first geometry is very simple: a unit cube with a non-uniform mesh size
# constraint (set on purpose to be able to verify visually that the periodicity
# constraint works!):

gmsh.model.occ.addBox(0, 0, 0, 1, 1, 1, 1)
gmsh.model.occ.synchronize()

gmsh.model.mesh.setSize(gmsh.model.getEntities(0), 2)
gmsh.model.mesh.setSize([(0, 1)], 2)

# To impose that the mesh on surface 2 (the right side of the cube) should
# match the mesh from surface 1 (the left side), the following periodicity
# constraint is set:
translation = [1, 0, 0, 1, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]
gmsh.model.mesh.setPeriodic(2, [2], [1], translation)

# The periodicity transform is provided as a 4x4 affine transformation matrix,
# given by row.

# During mesh generation, the mesh on surface 2 will be created by copying
# the mesh from surface 1.

# Multiple periodicities can be imposed in the same way:
gmsh.model.mesh.setPeriodic(2, [6], [5],
                            [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0, 1])
gmsh.model.mesh.setPeriodic(2, [4], [3],
                            [1, 0, 0, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 0, 0, 1])

gmsh.model.mesh.generate(3)
gmsh.write("t18_simple.msh")

# Launch the GUI to see the results:
if '-nopopup' not in sys.argv:
    gmsh.fltk.run()

gmsh.finalize()
