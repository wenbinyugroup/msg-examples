# GMSH Formatter - Quick Start Guide

Get started with formatted GMSH MSH files in 2 minutes!

## 30-Second Start

```python
import gmsh
import gmsh_formatter

# 1. Apply the monkey patch
gmsh_formatter.apply_monkey_patch()

# 2. Use gmsh.write() with formatting options
gmsh.initialize()
gmsh.model.add("example")
# ... your mesh code ...
gmsh.write("output.msh", precision=10, align_columns=True)
gmsh.finalize()
```

That's it! Your MSH file now has:
- ✅ Aligned numbers in columns
- ✅ Consistent decimal precision
- ✅ Explanatory comments
- ✅ Clean, readable structure

## Format Existing Files (No GMSH Needed)

Already have MSH files? Format them instantly:

```python
import gmsh_formatter

# Format any existing MSH file
gmsh_formatter.format_msh_file("your_mesh.msh", precision=12)
```

## Common Use Cases

### Use Case 1: Debugging Meshes

```python
import gmsh_formatter

# Format for easy debugging
gmsh_formatter.format_msh_file(
    "debug_mesh.msh",
    precision=16,      # High precision
    align_columns=True,  # Easy to read
    add_comments=True    # Helpful labels
)
```

### Use Case 2: Production Meshes

```python
import gmsh
import gmsh_formatter

gmsh_formatter.apply_monkey_patch()

# Compact output for production
gmsh.write(
    "production.msh",
    precision=8,       # Reasonable precision
    compact_mode=True,  # Smaller files
    add_comments=False  # No extra content
)
```

### Use Case 3: Documentation/Teaching

```python
# Maximum readability for teaching
gmsh_formatter.format_msh_file(
    "tutorial_mesh.msh",
    precision=6,        # Simpler numbers
    align_columns=True, # Clean layout
    add_comments=True,  # Explain sections
    column_width=15     # Narrower for slides
)
```

## Before vs After

### Before (Original):
```
$Nodes
8 1 1 8
3 1 0 8
1
2
3
4
5
6
7
8
0 0 0
1 0 0
1 1 0
0 1 0
```

### After (Formatted):
```
$Nodes
# Nodes: 8 entity blocks, 1 total nodes
8 1 1 8
# Entity 1: 8 nodes
         3          1          0          8
         1
         2
         3
         4
         5
         6
         7
         8
    0.000000000000    0.000000000000    0.000000000000
    1.000000000000    0.000000000000    0.000000000000
    1.000000000000    1.000000000000    0.000000000000
    0.000000000000    1.000000000000    0.000000000000
```

## All Configuration Options

```python
gmsh.write(
    "mesh.msh",
    precision=16,            # Decimal places (default: 16)
    align_columns=True,      # Column alignment (default: True)
    add_comments=True,       # Section comments (default: True)
    compact_mode=False,      # Compact spacing (default: False)
    column_width=20,         # Column width (default: 20)
    section_spacing=1,       # Lines between sections (default: 1)
    scientific_threshold=1e-6  # Scientific notation threshold
)
```

## Testing

Test with your existing files:

```bash
# Format existing files (no gmsh required)
python scripts/test_format_simple.py

# Full test suite (requires gmsh)
python scripts/test_gmsh_formatter.py
```

## Next Steps

- Read [README_GMSH_FORMATTER.md](README_GMSH_FORMATTER.md) for complete documentation
- Check `test_format_simple.py` for more examples
- Examine `gmsh_formatter.py` source for advanced customization

## Questions?

**Q: Will this change my mesh data?**  
A: No! Only formatting changes. All coordinates and connectivity remain identical.

**Q: Do I need to modify GMSH source code?**  
A: No! Uses Python monkey patching - zero GMSH modifications needed.

**Q: Can I use this with my existing scripts?**  
A: Yes! Just add one line: `gmsh_formatter.apply_monkey_patch()`

**Q: What if I want to go back to original formatting?**  
A: Call `gmsh_formatter.restore_original()` anytime.

Start formatting your MSH files today! 🚀
