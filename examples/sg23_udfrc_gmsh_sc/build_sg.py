import gmsh

# Parameters
side_length = 1.0  # Square side length
fiber_radius = 0.3  # Fiber radius (r in the image)
mesh_size = 0.1  # Mesh element size

print("\n--- Starting GMSH Meshing ---")

gmsh.initialize()
gmsh.model.add("fiber_matrix_2d")

# Create geometry in the Y-Z plane (x=0)
# The geometry is in the Y-Z plane, so we use y and z as our 2D coordinates
# In GMSH, we work in x-y plane by default, so map: gmsh_x = y, gmsh_y = z

# Create the outer square (matrix boundary)
# Rectangle centered at origin: corners at (-0.5, -0.5) to (0.5, 0.5)
half_side = side_length / 2.0
square = gmsh.model.occ.addRectangle(-half_side, -half_side, 0, side_length, side_length)
print(f'{square=}')

# Create the fiber circle at center
circle = gmsh.model.occ.addDisk(0, 0, 0, fiber_radius, fiber_radius)
print(f'{circle=}')

# Cut the circle from the square to create the matrix region
# This creates two surfaces: matrix (square - circle) and fiber (circle)
out_dimtags, out_dimtags_map = gmsh.model.occ.fragment([(2, square)], [(2, circle)])
print(f"{out_dimtags=}")
print(f"{out_dimtags_map=}")

# Synchronize the CAD model with GMSH
gmsh.model.occ.synchronize()

# Get all surfaces
surfaces = gmsh.model.getEntities(dim=2)
print(f"Surfaces after fragmentation: {surfaces}")

fiber_surfaces = [circle]
matrix_surfaces = []
for _dim, _tag in out_dimtags_map[0]:
    if _tag not in fiber_surfaces:
        matrix_surfaces.append(_tag)

print(f"Matrix surfaces: {matrix_surfaces}")
print(f"Fiber surfaces: {fiber_surfaces}")

# Create physical groups for material assignment
if matrix_surfaces:
    matrix_group = gmsh.model.addPhysicalGroup(2, matrix_surfaces, 1)
    gmsh.model.setPhysicalName(2, matrix_group, "Matrix")

if fiber_surfaces:
    fiber_group = gmsh.model.addPhysicalGroup(2, fiber_surfaces, 2)
    gmsh.model.setPhysicalName(2, fiber_group, "Fiber")

# Set mesh size
gmsh.option.setNumber("Mesh.CharacteristicLengthMin", mesh_size)
gmsh.option.setNumber("Mesh.CharacteristicLengthMax", mesh_size)

gmsh.model.occ.synchronize()

gmsh.model.geo.mesh.setRecombine(2, 1)

gmsh.model.geo.synchronize()

# Generate 2D mesh
gmsh.model.mesh.generate(2)

# Export mesh to .msh file
output_file = "sg2d_fm_square.msh"
gmsh.write(output_file)
print(f"\nMesh exported to: {output_file}")

# Get mesh statistics
node_tags, node_coords, _ = gmsh.model.mesh.getNodes()
elem_types, elem_tags, elem_node_tags = gmsh.model.mesh.getElements(dim=2)
total_elements = sum(len(tags) for tags in elem_tags)
print(f"Mesh statistics: {len(node_tags)} nodes, {total_elements} elements")

# Finalize GMSH
gmsh.finalize()

print("--- GMSH Meshing Complete ---")

