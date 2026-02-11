---
title: "Example: [Your Problem Title]"
description: Brief description of the structural analysis problem being solved
short_title: Short Title
date: 2024-02-11
authors:
  - name: Author Name
    affiliation: Institution Name
    email: author@institution.edu
keywords:
  - VABS
  - SwiftComp
  - [Add domain-specific keywords]
  - Structural Analysis
  - Composite Materials
thumbnail: ./images/thumbnail.png
---

# [Problem Title]

## Overview

Brief summary paragraph introducing the example. Explain what structural analysis problem is being solved and why it's interesting or important.

:::{note}
**Prerequisites:**
- SwiftComp or VABS installed and accessible in PATH
- Python packages: `sgio`, `numpy`, `pandas`
- [Any other specific requirements]
:::

## Problem Description

### Geometry

Describe the geometric configuration being analyzed. Include dimensions, coordinate systems, and any important geometric features.

:::{figure} ./images/geometry.png
:label: fig-geometry
:width: 70%
:align: center

Geometric configuration showing [describe what is shown in the figure]. Include relevant dimensions and annotations.
:::

As shown in [](#fig-geometry), the structure consists of...

### Material Properties

Present material properties in a clear, structured format:

| Component | Property | Value | Units |
|-----------|----------|-------|-------|
| Matrix | Young's Modulus | 3.5 | GPa |
| Matrix | Poisson's Ratio | 0.35 | - |
| Fiber | Young's Modulus | 230 | GPa |
| Fiber | Poisson's Ratio | 0.2 | - |

:::{tip}
Material properties can also be stored in JSON format for easy loading. See [materials.json](./data/materials.json).
:::

### Analysis Objectives

Clearly state what you are trying to compute or investigate:

1. **Primary objective**: Calculate effective engineering constants
2. **Parametric study**: Investigate the effect of [parameter] on [response]
3. **Validation**: Compare results with [analytical/experimental] data

The effective properties are related through the compliance matrix:

$$
\mathbf{S} = \mathbf{C}^{-1}
$$ (eq:compliance)

where the engineering constants can be extracted:

$$
E_1 = \frac{1}{S_{11}}, \quad \nu_{12} = -\frac{S_{12}}{S_{11}}
$$ (eq:eng-constants)

## Implementation

This section explains the computational implementation using a modular approach.

### Project Structure

```
example_name/
├── README.md              # This file - main documentation
├── run.py                 # Main analysis script
├── build_sg.py           # Structure genome generation
├── visualization.ipynb    # Interactive visualizations
├── data/                 # Input files
│   ├── materials.json
│   └── geometry.msh
└── results/              # Output files
    └── results.csv
```

### Structure Genome Generation

The geometry is created using GMSH Python API. The [`build_sg.py`](./build_sg.py) script handles the mesh generation:

:::{literalinclude} build_sg.py
:language: python
:caption: Structure genome generation using GMSH
:emphasize-lines: 1-5
:::

Key points in the geometry generation:
- Line XX: Define geometric parameters
- Line XX: Create material regions
- Line XX: Generate finite element mesh
- Line XX: Export to `.msh` format

### Format Conversion

SwiftComp requires a specific input format. We convert from GMSH format:

:::{literalinclude} convert.py
:language: python
:lines: 10-30
:caption: Converting GMSH mesh to SwiftComp format
:::

:::{warning}
Ensure node and element numbering is consistent between formats. The converter handles 1-based vs 0-based indexing automatically.
:::

### Main Analysis Loop

The parametric study is implemented in [`run.py`](./run.py:20):

:::{literalinclude} run.py
:language: python
:lines: 20-60
:caption: Main parametric study loop
:::

The analysis workflow consists of:

1. **Define parameter range** (lines XX-XX): Set up the values to sweep
2. **For each parameter value**:
   - Generate geometry with `build_sg()`
   - Convert to SwiftComp format
   - Run homogenization analysis
   - Extract and store results
3. **Post-process**: Export results to CSV for visualization

:::{admonition} Performance Tip
For large parametric studies, consider parallelizing the loop using `multiprocessing` or `joblib`.
:::

### Running the Analysis

To execute the complete analysis:

```bash
# Activate your virtual environment
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Run the main analysis script
python run.py

# Results will be saved to results/results.csv
```

## Results

### Engineering Constants

The computed effective engineering constants show the following trends:

:::{embed} visualization.ipynb#fig-eng-constants
:remove-input: true
:::

**Key observations:**
- Young's moduli $E_1$, $E_2$, $E_3$ [describe trend]
- Poisson's ratios $\nu_{12}$, $\nu_{13}$, $\nu_{23}$ [describe trend]  
- Shear moduli $G_{12}$, $G_{13}$, $G_{23}$ [describe trend]

The interactive figure above shows [describe what users can explore]. Hover over data points to see exact values.

### Detailed Analysis

For a more detailed exploration with additional visualizations and analysis, see the complete [visualization notebook](./visualization.ipynb).

### Validation

Compare results with analytical or experimental data:

| Source | $E_1$ (GPa) | $E_2$ (GPa) | Error (%) |
|--------|-------------|-------------|-----------|
| SwiftComp | XX.XX | XX.XX | - |
| Analytical | XX.XX | XX.XX | X.X% |
| Literature | XX.XX | XX.XX | X.X% |

## Physical Interpretation

Discuss the physical meaning of the results:

1. **Effect of [parameter]**: As [parameter] increases, we observe [trend] because [physical explanation]
2. **Comparison to constituent materials**: The effective properties show [behavior] which is characteristic of [material type]
3. **Engineering implications**: These results suggest that [practical insight]

## Limitations and Future Work

:::{caution}
**Current limitations:**
- Assumes perfect bonding between constituents
- Linear elastic material behavior only
- [Add other assumptions/limitations]
:::

Potential extensions:
- Include material nonlinearity
- Investigate failure criteria
- Extend to thermomechanical coupling

## References

Key references for this example:

- Yu, W., & Tang, T. (2007). *Variational Asymptotic Method for Unit Cell Homogenization*
- [Add relevant papers]
- [SwiftComp documentation](http://cdmhub.org/resources/scstandard)

:::{seealso}
**Related examples:**
- [Another Example](../other_example/README.md) - Similar problem with different geometry
- [Extended Analysis](../extended_example/README.md) - Builds on this example
:::

## Appendix

### Complete Parameter List

List all parameters used in the analysis for reproducibility:

```python
# Geometric parameters
param1 = value1
param2 = value2

# Mesh parameters  
mesh_size = 0.05
element_order = 2

# Analysis parameters
analysis_type = 'homogenization'
smdim = 3  # Structure model dimension
```

### Troubleshooting

Common issues and solutions:

**Issue**: SwiftComp fails with "singular stiffness matrix"
- **Solution**: Check mesh quality, refine in areas with high aspect ratios

**Issue**: Results don't converge with mesh refinement
- **Solution**: Verify material property assignment, check element connectivity

---

:::{note}
**Using this template:**
1. Replace all `[placeholder text]` with your specific content
2. Update frontmatter with correct title, authors, keywords
3. Add your own figures to `./images/`
4. Implement your analysis scripts following the structure
5. Create visualizations in the notebook
6. Delete this note when done
:::
