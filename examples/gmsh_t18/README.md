---
title: "GMSH Tutorial 18"
description: Parametric study of particle volume fraction effects on effective engineering constants using SwiftComp
short_title: GMSH T18
date: 2026-02-11
keywords:
  - SwiftComp
  - Composite Materials
  - Homogenization
  - GMSH
  - Particle Reinforced Composites
thumbnail: https://gmsh.info/doc/texinfo/images/t18.png
---

# GMSH Tutorial 18

## Overview

This example demonstrates the use of GMSH Python API and SwiftComp to perform a parametric homogenization study of a fiber-reinforced composite cylinder. The analysis investigates how the fiber radius (and thus fiber volume fraction) affects the effective engineering constants of the composite material.

:::{note}
**Prerequisites:**
- SwiftComp installed and accessible in PATH
- Python packages: `sgio`, `gmsh`, `numpy`, `pandas`, `plotly`
- Basic understanding of composite mechanics and homogenization theory
:::

:::{seealso}
This example is based on [GMSH Python Tutorial 18](https://gmsh.info/doc/texinfo/gmsh.html#t18_002epy), adapted for structural analysis with SwiftComp.
:::

## Problem Description

### Geometry

The unit cell consists of a circular fiber embedded in a matrix material, representing a unidirectional fiber-reinforced composite. The geometry is defined in the cross-sectional (2-3) plane perpendicular to the fiber direction (axis 1).

:::{figure} https://gmsh.info/doc/texinfo/images/t18.png
:label: fig-geometry
:width: 50%
:align: center

Unit cell geometry showing fiber (inner circle) and matrix (outer region) with periodic boundary conditions on all sides.
:::

**Geometric Parameters:**
- Fiber radius: $r_f$ (varied from 0.1 to 0.4 mm)
- Unit cell size: 1.0 × 1.0 mm²
- Fiber volume fraction: $V_f = \pi r_f^2$ (for unit cell area = 1)

As shown in [](#fig-geometry), the fiber is centered in a square unit cell. Periodic boundary conditions are applied to ensure the unit cell can tessellate to represent the bulk material behavior.

### Material Properties

Two-phase composite material system:

| Component | Young's Modulus (GPa) | Poisson's Ratio | Material Type |
|-----------|----------------------|-----------------|---------------|
| **Fiber** | 230.0 | 0.20 | Carbon fiber |
| **Matrix** | 3.5 | 0.35 | Epoxy resin |

The large stiffness ratio (≈65:1) between fiber and matrix creates significant anisotropy in the effective properties.

:::{tip}
Material properties are defined in [materials.json](./data/materials.json) for easy modification.
:::

### Analysis Objectives

The primary objectives of this parametric study are:

1. **Compute effective properties**: Determine the nine engineering constants ($E_1, E_2, E_3, \nu_{12}, \nu_{13}, \nu_{23}, G_{12}, G_{13}, G_{23}$) as functions of fiber radius
2. **Understand scaling behavior**: Investigate how properties vary with fiber volume fraction
3. **Validate homogenization**: Verify results follow expected composite mechanics trends

The effective properties are obtained through homogenization theory, where the heterogeneous unit cell is replaced by an equivalent homogeneous material. The compliance matrix relates strains to stresses:

$$
\boldsymbol{\varepsilon} = \mathbf{S} \boldsymbol{\sigma}
$$ (eq:compliance)

From the compliance matrix components, engineering constants are extracted:

$$
\begin{aligned}
E_i &= \frac{1}{S_{ii}} \\
\nu_{ij} &= -\frac{S_{ij}}{S_{ii}} \\
G_{ij} &= \frac{1}{S_{ij}}
\end{aligned}
$$ (eq:eng-constants)

## Implementation

This analysis uses a modular approach with separate scripts for geometry generation, format conversion, and the main parametric study.

### Project Structure

```
gmsh_t18/
├── README.md              # This documentation
├── run.py                 # Main parametric study script
├── build_sg.py           # GMSH geometry generation
├── convert.py            # Format conversion (GMSH → SwiftComp)
├── visualization.ipynb    # Interactive result visualizations
└── data/                 # Input files
    └── materials.json        # Material property definitions
└── results/              # Output files
    └── t18_results.csv
```

### Geometry Generation with GMSH

The unit cell geometry is created using the GMSH Python API in [`build_sg.py`](./build_sg.py:1). The script creates a 2D mesh with two material regions:

:::{literalinclude} build_sg.py
:language: python
:caption: Structure genome generation using GMSH Python API
:::

**Key steps in geometry generation:**
1. **Initialize GMSH**: Set up the GMSH environment
2. **Define geometry**: Create circle (fiber) and square (matrix) with Boolean operations
3. **Assign materials**: Tag regions with appropriate material IDs
4. **Generate mesh**: Create finite element mesh with specified characteristic size
5. **Export**: Write to `.msh` format

The mesh quality is controlled by the `mesh_size` parameter, which should be small enough to capture stress gradients near the fiber-matrix interface.

### Format Conversion

SwiftComp requires a specific input format (`.sg` files) that differs from GMSH's native `.msh` format. The [`convert.py`](./convert.py:1) script handles this conversion:

:::{literalinclude} convert.py
:language: python
:caption: Converting GMSH mesh to SwiftComp format
:::

The conversion ensures:
- Proper node and element numbering
- Material property assignment to elements
- Correct boundary condition specification for periodic homogenization

:::{warning}
The converter assumes 1-based indexing for SwiftComp. Ensure your GMSH mesh uses consistent numbering.
:::

### Main Parametric Study

The parametric study sweeps through fiber radii and computes effective properties for each case. Implementation in [`run.py`](./run.py:20):

:::{literalinclude} run.py
:language: python
:lines: 19-62
:caption: Main parametric study loop
:::

**Analysis workflow:**
1. **Define parameter range** (line 22): Create array of fiber radii from 0.1 to 0.4 mm
2. **Initialize storage** (lines 25-29): Set up data structures for results
3. **Loop over cases** (lines 31-57):
   - Create working directory for each case
   - Generate geometry with current fiber radius
   - Convert to SwiftComp format
   - Run homogenization analysis with `sgio.run()`
   - Extract engineering constants from output
4. **Export results** (lines 59-61): Save to CSV for visualization

:::{admonition} Computational Notes
**Runtime**: ~5-10 seconds per case on typical hardware  
**Memory**: ~100 MB peak  
**Parallelization**: Could be parallelized using `multiprocessing` for larger studies
:::

### Running the Analysis

Execute the complete parametric study:

```bash
# Ensure SwiftComp is in your PATH
# Activate virtual environment (see AGENTS.md)
.venv\Scripts\activate  # Windows
# or: source .venv/bin/activate  # Unix

# Run the parametric study
python run.py

# Results saved to t18_results.csv
# Individual case files in evals/ directory
```

The script logs progress to both console and `run.log` file.
