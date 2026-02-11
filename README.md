# MSG Examples

Examples demonstrating the use of VABS/SwiftComp for structural analysis using the Mechanics of Structure Genome (MSG) approach.

## Quick Start for Contributors

1. **Create a new example**: Copy `examples/_template/` and follow the [Example Guidelines](./doc/EXAMPLE_GUIDELINES.md)
2. **Structure**: Use MyST Markdown for documentation (`.md`) + Python scripts (`.py`) + Jupyter visualizations (`.ipynb`)
3. **Reference example**: See `examples/gmsh_t18/` for a complete implementation

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

**Environment setup**: See [pyproject.toml](./pyproject.toml) for virtual environment and dependencies.

**Building documentation**:
```bash
uv add mystmd
uv run myst start  # Preview at http://localhost:3000
uv run myst build --html  # Build website
uv run myst build --pdf   # Export PDF
```

## Contributions

Contributions welcome! Please:
1. Use the provided template
2. Follow the guidelines in `EXAMPLE_GUIDELINES.md`
3. Ensure examples build without errors
4. Add appropriate frontmatter and cross-references

**License**: See LICENSE file  
**Contact**: [Issues](https://github.com/wenbinyugroup/msg-examples/issues) for questions
