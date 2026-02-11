# ------------------------------------------------------------------------------
#
#  Gmsh Python tutorial 18
#
#  Periodic meshes
#
# ------------------------------------------------------------------------------

# Periodic meshing constraints can be imposed on surfaces and curves.

import gmsh
# import math
import os
import sys
import json

eps = 1e-3

def set_periodic_faces(min_bbox, max_bbox, translation):
    """
    Set periodicity between two faces based on bounding boxes.
    
    Args:
        min_bbox: Bounding box for the minimum face (xmin, ymin, zmin, xmax, ymax, zmax)
        max_bbox: Bounding box for the maximum face (xmin, ymin, zmin, xmax, ymax, zmax)
        translation: 4x4 affine transformation matrix
    """
    # Get all surfaces on the minimum side
    min_faces = gmsh.model.getEntitiesInBoundingBox(min_bbox[0], min_bbox[1], min_bbox[2], 
                                                   min_bbox[3], min_bbox[4], min_bbox[5], 2)
    
    for i in min_faces:
        # Get the bounding box of each minimum surface
        xmin, ymin, zmin, xmax, ymax, zmax = gmsh.model.getBoundingBox(i[0], i[1])
        
        # Translate the bounding box and look for surfaces inside it
        max_faces = gmsh.model.getEntitiesInBoundingBox(max_bbox[0], max_bbox[1], max_bbox[2],
                                                      max_bbox[3], max_bbox[4], max_bbox[5], 2)
        
        # For all the matches, compare the corresponding bounding boxes
        for j in max_faces:
            xmin2, ymin2, zmin2, xmax2, ymax2, zmax2 = gmsh.model.getBoundingBox(j[0], j[1])
            
            # Apply inverse translation to compare
            if translation[3] != 0:  # x-translation
                xmin2 -= translation[3]
                xmax2 -= translation[3]
            if translation[7] != 0:  # y-translation
                ymin2 -= translation[7]
                ymax2 -= translation[7]
            if translation[11] != 0:  # z-translation
                zmin2 -= translation[11]
                zmax2 -= translation[11]
            
            # If bounding boxes match, apply the periodicity constraint
            if (abs(xmin2 - xmin) < eps and abs(xmax2 - xmax) < eps and
                abs(ymin2 - ymin) < eps and abs(ymax2 - ymax) < eps and
                abs(zmin2 - zmin) < eps and abs(zmax2 - zmax) < eps):
                gmsh.model.mesh.setPeriodic(2, [j[1]], [i[1]], translation)



def build_sg(
    radius=0.35,
    fn_sg_base='sg',
    fn_materials='materials.json',
    mesh_size=0.1,
    nopopup=False
    ):

    # Load materials from JSON file
    with open(fn_materials, 'r') as f:
        materials_data = json.load(f)

    # Create a mapping from material name to material ID
    material_name_to_id = {}
    for material in materials_data:
        material_name_to_id[material['name']] = material['id']

    # Get material IDs for matrix and inclusion
    MATRIX_ID = material_name_to_id['matrix']
    INCLUSION_ID = material_name_to_id['inclusion']

    gmsh.initialize()

    gmsh.model.add("sg")



    # For more complicated cases, finding the corresponding surfaces by hand can
    # be tedious, especially when geometries are created through solid
    # modelling. Let's construct a slightly more complicated geometry.

    # We start with a cube and some spheres:
    gmsh.model.occ.addBox(2, 0, 0, 1, 1, 1, 10)
    x = 2 - 0.3
    y = 0
    z = 0
    gmsh.model.occ.addSphere(x,     y,     z,     radius, 11)
    gmsh.model.occ.addSphere(x + 1, y,     z,     radius, 12)
    gmsh.model.occ.addSphere(x,     y + 1, z,     radius, 13)
    gmsh.model.occ.addSphere(x,     y,     z + 1, radius, 14)
    gmsh.model.occ.addSphere(x + 1, y + 1, z,     radius, 15)
    gmsh.model.occ.addSphere(x,     y + 1, z + 1, radius, 16)
    gmsh.model.occ.addSphere(x + 1, y,     z + 1, radius, 17)
    gmsh.model.occ.addSphere(x + 1, y + 1, z + 1, radius, 18)

    # We first fragment all the volumes, which will leave parts of spheres
    # protruding outside the cube:
    out, outmap = gmsh.model.occ.fragment([(3, 10)], [(3, i) for i in range(11, 19)])
    gmsh.model.occ.synchronize()

    # Track which volumes came from the box (matrix) and which from spheres (inclusions)
    # outmap[i] contains the list of volumes that resulted from fragmenting entity i
    # Index 0 corresponds to the box (tag 10), indices 1-8 correspond to spheres (tags 11-18)
    matrix_volumes = []
    inclusion_volumes = []

    # Get volumes from the box (matrix material)
    if len(outmap) > 0 and len(outmap[0]) > 0:
        for dim_tag in outmap[0]:
            if dim_tag[0] == 3:  # Only 3D volumes
                matrix_volumes.append(dim_tag[1])

    # Get volumes from the spheres (inclusion material)
    for i in range(1, min(9, len(outmap))):
        if len(outmap[i]) > 0:
            for dim_tag in outmap[i]:
                if dim_tag[0] == 3:  # Only 3D volumes
                    inclusion_volumes.append(dim_tag[1])

    # Ask OpenCASCADE to compute more accurate bounding boxes of entities using
    # the STL mesh:
    gmsh.option.setNumber("Geometry.OCCBoundsUseStl", 1)

    # We then retrieve all the volumes in the bounding box of the original cube,
    # and delete all the parts outside it:
    vin = gmsh.model.getEntitiesInBoundingBox(2 - eps, -eps, -eps, 2 + 1 + eps,
                                            1 + eps, 1 + eps, 3)
    for v in vin:
        out.remove(v)
    gmsh.model.removeEntities(out, True)  # Delete outside parts recursively

    # Update the volume lists to only include volumes inside the bounding box
    vin_tags = [v[1] for v in vin]
    inclusion_volumes = [v for v in inclusion_volumes if v in vin_tags]
    matrix_volumes = [v for v in matrix_volumes if (v in vin_tags and v not in inclusion_volumes)]

    # We now set a non-uniform mesh size constraint (again to check results
    # visually):
    p = gmsh.model.getBoundary(vin, False, False, True)  # Get all points
    gmsh.model.mesh.setSize(p, mesh_size)
    p = gmsh.model.getEntitiesInBoundingBox(2 - eps, -eps, -eps, 2 + eps, eps, eps,
                                            0)
    gmsh.model.mesh.setSize(p, mesh_size)

    # ---------------
    # Set Periodicity
    # ---------------

    # x-faces

    # To impose that the mesh on surface 2 (the right side of the cube) should
    # match the mesh from surface 1 (the left side), the following periodicity
    # constraint is set:

    # The periodicity transform is provided as a 4x4 affine transformation matrix,
    # given by row.
    translation = [
        1, 0, 0, 1,
        0, 1, 0, 0,
        0, 0, 1, 0,
        0, 0, 0, 1
        ]

    # During mesh generation, the mesh on surface 2 will be created by copying
    # the mesh from surface 1.

    # We now identify corresponding surfaces on the left and right sides of the
    # geometry automatically using the helper function.
    xmin_bbox = (2 - eps, -eps, -eps, 2 + eps, 1 + eps, 1 + eps)
    xmax_bbox = (2 - eps + 1, -eps, -eps, 2 + eps + 1, 1 + eps, 1 + eps)
    set_periodic_faces(xmin_bbox, xmax_bbox, translation)

    # y-faces
    translation = [
        1, 0, 0, 0,
        0, 1, 0, 1,
        0, 0, 1, 0,
        0, 0, 0, 1
        ]

    # Set periodicity for y-faces using the helper function
    ymin_bbox = (2 - eps, -eps, -eps, 2 + eps + 1, eps, eps + 1)
    ymax_bbox = (2 - eps, -eps + 1, -eps, 2 + eps + 1, eps + 1, eps + 1)
    set_periodic_faces(ymin_bbox, ymax_bbox, translation)

    # z-faces
    translation = [
        1, 0, 0, 0,
        0, 1, 0, 0,
        0, 0, 1, 1,
        0, 0, 0, 1
        ]

    # Set periodicity for z-faces using the helper function
    zmin_bbox = (2 - eps, -eps + 1, -eps, 2 + eps + 1, eps + 1, eps)
    zmax_bbox = (2 - eps, -eps + 1, -eps + 1, 2 + eps + 1, eps + 1, eps + 1)
    set_periodic_faces(zmin_bbox, zmax_bbox, translation)

    gmsh.model.mesh.generate(3)

    # Assign material IDs to elements based on which volume they belong to
    # Use material IDs from materials.json

    # Create physical groups for matrix and inclusion materials
    print(f'{matrix_volumes=}')
    if len(matrix_volumes) > 0:
        gmsh.model.addPhysicalGroup(3, matrix_volumes, MATRIX_ID)
        gmsh.model.setPhysicalName(3, MATRIX_ID, "matrix")

    print(f'{inclusion_volumes=}')
    if len(inclusion_volumes) > 0:
        gmsh.model.addPhysicalGroup(3, inclusion_volumes, INCLUSION_ID)
        gmsh.model.setPhysicalName(3, INCLUSION_ID, "inclusion")

    # Write the mesh file first
    gmsh.write(f"{fn_sg_base}.msh")

    # Launch the GUI to see the results:
    if not nopopup:
        gmsh.fltk.run()

    gmsh.finalize()


if __name__ == "__main__":
    build_sg()
