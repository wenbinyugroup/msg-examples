---
title: "Particle Reinforced Composite"
subtitle: "How to link Gmsh and SwiftComp for microstructural homogenization"
short_title: "Particle Reinforced Composite"
description: Parametric study of particle volume fraction effects on effective engineering constants using SwiftComp
authors:
  - name: Su Tian
    affiliations:
      - AnalySwift
date: 2026-02-11
banner: https://gmsh.info/doc/texinfo/images/t18.png
label: "gmsh-sc-sg3d"
tags:
  - gmsh
  - 3d_sg
  - swiftcomp
  - composites
keywords:
  - SwiftComp
  - Composite Materials
  - Homogenization
  - Gmsh
  - Particle Reinforced Composites
---

# Particle Reinforced Composite Material

## Overview

This example demonstrates the use of Gmsh Python API and SwiftComp to perform a simple parametric study of a particle-reinforced composite material.
The SG is modeled based on the [Gmsh tutorial 18](https://gmsh.info/doc/texinfo/gmsh.html#t18).
The particle volume fraction is varied by changing the radius of the particle. The effective engineering constants are computed and visualized.


### Geometry and Mesh

The SG consists of spherical inclusions embedded in a matrix material, representing a particle-reinforced composite material. Periodic meshing is applied to three pairs of parallel faces.

:::{figure} https://gmsh.info/doc/texinfo/images/t18.png
:label: fig-geometry
:width: 50%
:align: center

Meshed SG. This example uses the model on the right with particle inclusions only. Source: [Gmsh tutorial 18](https://gmsh.info/doc/texinfo/gmsh.html#t18).
:::

### Material Properties

**Matrix**
- Density: 1000 kg/m3
- Young's Modulus: 1.0e9 Pa
- Poisson's Ratio: 0.3

**Inclusion**
- Density: 2500 kg/m3
- Young's Modulus: 1.0e11 Pa
- Poisson's Ratio: 0.25

---

## File Structure

```
gmsh_t18/
├── README.md              # This documentation
├── run.py                 # Main parametric study script
├── build_sg.py            # Gmsh geometry generation
├── convert.py             # Format conversion (Gmsh → SwiftComp)
├── visualization.ipynb    # Result visualizations
├── data/                  # Input files
│   └── materials.json       # Material property definitions
└── results/               # Output files
    └── t18_results.csv      # Analysis results
```

---

## Running the Analysis

:::{note}
**Prerequisites:**
- SwiftComp installed and accessible in PATH
- Python packages: `sgio`, `gmsh`, `numpy`, `pandas`, `plotly`
:::

Execute the complete parametric study:

```bash
# Install dependencies
uv sync

# Activate virtual environment (see AGENTS.md)
.venv\Scripts\activate.ps1  # Windows
# or: source .venv/bin/activate  # Unix

# Run the parametric study
cd examples\gmsh_t18
python run.py

# Results saved to results/t18_results.csv
# Individual case files in evals/ directory
```




## Analysis Workflow Scripting

In general, the analysis workflow consists of the following steps:
1. Geometry generation with Gmsh
2. Format conversion to SwiftComp
3. Running the parametric study

### Geometry Generation with Gmsh

The SG geometry is created using the Gmsh Python API in {download}`build_sg.py` based on the official script [`t18.py`](https://gitlab.onelab.info/gmsh/gmsh/blob/gmsh_4_15_0/tutorials/python/t18.py).
The script is modified in the following ways:
- Setting periodicity is converted to a function and applied to all three pairs of faces.
- Add physical groups for matrix and inclusion volumes to store material assignments.

:::{literalinclude} build_sg.py
:language: python
:caption: Structure genome generation using Gmsh Python API
:linenos: true
:::


### Format Conversion

The {download}`convert.py` script handles the format conversion from Gmsh to SwiftComp.
The overall steps are straightforward and as follows:
1. Read the Gmsh mesh file
2. Add materials to the model
3. Write the SwiftComp model to file

:::{literalinclude} convert.py
:language: python
:caption: Converting Gmsh mesh to SwiftComp format
:linenos: true
:::

### Main Parametric Study

The parametric study sweeps through inclusion radii and computes effective properties for each case. Implementation in {download}`run.py`:

:::{literalinclude} run.py
:language: python
:caption: Main parametric study loop
:linenos: true
:::


## Results and Visualization

The results are saved to `results/t18_results.csv` and can be visualized using the Jupyter notebook {download}`visualization.ipynb`.

![](#fig-t18-results)