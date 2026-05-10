# Contribution Guidelines

## Overview

This guide provides comprehensive best practices for creating MyST Markdown documentation for VABS/SwiftComp structural analysis examples in the msg-examples repository.

**Target Audience:** Contributors creating new examples or improving existing ones.

**Quick Start:** Use the template in `examples/_template/` as a starting point for new examples.

---

## Document Structure

### Recommended File Organization

Each example should follow this structure:

```
examples/your_example/
├── your_example.md        # Main documentation (MyST Markdown)
├── run.py                 # Main analysis script
├── other_scripts.py       # (if applicable)
├── visualization.ipynb    # Interactive visualizations
├── data/                  # Input files
│   ├── materials.json
│   └── geometry.msh
├── results/               # Output files  
│   └── results.csv
└── images/                # Figures for documentation
    └── geometry.png
```

### Why This Structure?

- **Separation of Concerns**: Documentation (MD), computation (PY), visualization (IPYNB)
- **Maintainability**: Each file has a single, clear purpose
- **Reusability**: Notebooks can be embedded in main documentation
- **Git-Friendly**: Markdown diffs are easier to review than notebook diffs

---

## Building and Previewing

### Environment setup

Repository-level documentation tooling:

```bash
uv sync
```

Example-specific runtime dependencies:

```bash
cd examples/your_example
uv add numpy pandas
uv sync
```

### Local Development

```bash
# Start local server
uv run myst start

# Open in browser: http://localhost:3000
```

### Building Outputs

```bash
# Build website
uv run myst build --html

# Build PDF
uv run myst build --pdf

# Build Word document
uv run myst build --docx

# Build all
uv run myst build --all
```

### Checking for Errors

```bash
# Check for broken links
uv run myst build --check-links

# Validate frontmatter
uv run myst init --check-frontmatter
```

---

## Resources

### Documentation

- [MyST Markdown Guide](https://mystmd.org/guide)
- [Plotly Python Documentation](https://plotly.com/python/)

### Examples

- **Reference Example**: See `examples/gmsh_t18/` for fully documented example
- **Template**: Use `examples/_template/` as starting point

## Dependency Management Policy

Every example under `examples/` should be treated as an independent Python project.

- Put repository-wide tools in the root `pyproject.toml`.
- Put example runtime dependencies in that example's `pyproject.toml`.
- Use optional dependencies for non-essential features such as plotting, notebooks, or heavy visualization stacks.
- Do not add example-specific runtime packages to the repository root just because another example already uses them.

Recommended pattern:

```toml
[project]
dependencies = [
  "numpy",
  "pandas",
]

[project.optional-dependencies]
plotting = [
  "matplotlib",
  "plotly",
]
notebook = [
  "jupyterlab",
  "ipywidgets",
]
```

Typical commands:

```bash
# Install only the base dependencies for one example
cd examples/your_example
uv sync

# Add a required runtime dependency
uv add scipy

# Add an optional dependency to a named extra
uv add --optional plotting matplotlib
uv add --optional notebook jupyterlab ipywidgets
```

### Getting Help

- Check existing examples for patterns
- Review MyST documentation for specific features
- Check [cdmHUB community](https://community.cdmhub.org/) for questions or comments
- Open an issue on [GitHub](https://github.com/wenbinyugroup/msg-examples/issues)
