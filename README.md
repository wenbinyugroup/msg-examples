# MSG Examples

Examples demonstrating the use of VABS/SwiftComp for structural analysis using the Mechanics of Structure Genome (MSG) approach.

## Dependency Model

This repository uses two dependency layers:

- The repository root environment is only for shared tooling such as `mystmd`.
- Each directory under `examples/` is an independent Python project with its own `pyproject.toml` and `.venv`.

This keeps incompatible example dependencies isolated and allows users to install only the examples they care about.

## Quick Start for Contributors

1. **Create a new example**: Copy `examples/_template/` and follow the [Example Guidelines](./doc/EXAMPLE_GUIDELINES.md)
2. **Declare dependencies locally**: Add packages to the new example's `pyproject.toml`, not the repository root
3. **Structure**: Use MyST Markdown for documentation (`.md`) + Python scripts (`.py`) + Jupyter visualizations (`.ipynb`)
4. **Reference example**: See `examples/gmsh_t18/` for a complete implementation

## Project Structure

```
examples/
├── _template/          # Template for new examples (copy this!)
├── gmsh_t18/          # Reference implementation
├── gmsh_periodic/      # Existing example (to be refactored)
└── sg23_udfrc_gmsh_sc/ # Existing example (to be refactored)

doc/
├── EXAMPLE_GUIDELINES.md # Comprehensive best practices
```

## Key Features

- **MyST Markdown**: Rich documentation with math, figures, cross-references
- **Interactive Visualizations**: Plotly-based notebooks with hover, zoom, pan
- **Modular Design**: Separate scripts for geometry, analysis, visualization
- **Reproducible**: Well-documented code with logging and configuration
- **Git-Friendly**: Markdown-based documentation for easy collaboration

## Development

**Repository tools**: install only the root environment when you need shared tooling like MyST.

```bash
uv sync
uv run myst start
```

**Run one example**: change into that example directory and sync only its dependencies.

```bash
cd examples/airfoil_cross_sections
uv sync
uv run python main.py
```

If an example has optional groups such as plotting or notebook support, enable them explicitly:

```bash
uv sync --extra plotting --extra notebook
```

## Contributions

Contributions welcome! Please:
1. Use the provided template
2. Follow the guidelines in `EXAMPLE_GUIDELINES.md`
3. Keep example runtime dependencies inside the example directory
4. Ensure examples build without errors
5. Add appropriate frontmatter and cross-references

**License**: See LICENSE file  
**Contact**: [Issues](https://github.com/wenbinyugroup/msg-examples/issues) for questions
