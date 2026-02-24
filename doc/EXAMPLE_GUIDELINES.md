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

```bash
uv sync

# Add packages if needed
uv add <package>
```

To activate the virtual environment:

```bash
# Windows PowerShell
.venv\Scripts\activate.ps1

# Unix
source .venv/bin/activate
```

### Local Development

```bash
# Start local server
myst start

# Open in browser: http://localhost:3000
```

### Building Outputs

```bash
# Build website
myst build --html

# Build PDF
myst build --pdf

# Build Word document
myst build --docx

# Build all
myst build --all
```

### Checking for Errors

```bash
# Check for broken links
myst build --check-links

# Validate frontmatter
myst init --check-frontmatter
```

---

## Resources

### Documentation

- [MyST Markdown Guide](https://mystmd.org/guide)
- [Plotly Python Documentation](https://plotly.com/python/)

### Examples

- **Reference Example**: See `examples/gmsh_t18/` for fully documented example
- **Template**: Use `examples/_template/` as starting point

### Getting Help

- Check existing examples for patterns
- Review MyST documentation for specific features
- Check [cdmHUB community](https://community.cdmhub.org/) for questions or comments
- Open an issue on [GitHub](https://github.com/wenbinyugroup/msg-examples/issues)
