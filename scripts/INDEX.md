# GMSH Formatter - File Index

## Overview

This directory contains a complete implementation of the GMSH Formatter - a Python solution for enhancing MSH file formatting without modifying GMSH source code.

## Core Files

### 📦 Main Module

**`gmsh_formatter.py`** (650+ lines)
- Complete formatter implementation
- Monkey patching infrastructure
- MSH file parser
- Section-specific formatters
- Configuration system
- Multiple integration methods

**Key Classes/Functions:**
- `MSHFormatter` - Main formatter class
- `format_msh_file()` - Format existing files
- `apply_monkey_patch()` - Enable enhanced gmsh.write()
- `restore_original()` - Restore original gmsh.write()
- `formatted_gmsh()` - Context manager

## Test Scripts

### 🧪 Testing

**`test_format_simple.py`**
- Simple standalone test
- No gmsh installation required
- Formats existing MSH files from examples
- Shows before/after comparisons
- Perfect for quick validation

**`test_gmsh_formatter.py`**
- Comprehensive test suite
- Requires gmsh installed
- Tests all integration methods
- Multiple test scenarios
- Side-by-side comparisons

**`example_usage.py`**
- 5 complete usage examples
- Demonstrates all major features
- Self-contained examples
- Includes batch processing
- Precision comparisons

## Documentation

### 📚 Documentation Files

**`README_GMSH_FORMATTER.md`**
- Complete documentation
- Problem statement and solution
- 4 usage methods
- All configuration options
- Performance benchmarks
- Troubleshooting guide
- Advanced features

**`QUICKSTART.md`**
- Quick start guide
- 30-second start
- Common use cases
- Before/after examples
- FAQ section

**`INDEX.md`** (this file)
- File organization
- Quick navigation
- Usage recommendations

## Project Files

### 📋 Project Documentation

**`../local/dev-notes.md`**
- Original implementation plan
- Design decisions
- Architecture details

**`../local/gmsh-formatter-summary.md`**
- Implementation summary
- Deliverables overview
- Testing results
- Benefits achieved

## Quick Navigation

### I want to...

**...format an existing MSH file quickly**
→ Use `gmsh_formatter.py` directly:
```python
import gmsh_formatter
gmsh_formatter.format_msh_file("mesh.msh", precision=12)
```

**...integrate into my GMSH workflow**
→ Read `QUICKSTART.md`, then:
```python
import gmsh_formatter
gmsh_formatter.apply_monkey_patch()
gmsh.write("output.msh", precision=10, align_columns=True)
```

**...see examples of how to use it**
→ Run `example_usage.py`:
```bash
python scripts/example_usage.py
```

**...test if it works**
→ Run `test_format_simple.py` (no gmsh needed):
```bash
python scripts/test_format_simple.py
```

**...understand all features**
→ Read `README_GMSH_FORMATTER.md`

**...learn the API in detail**
→ Read docstrings in `gmsh_formatter.py`

## File Sizes

| File | Lines | Purpose |
|------|-------|---------|
| `gmsh_formatter.py` | ~650 | Core implementation |
| `test_gmsh_formatter.py` | ~350 | Comprehensive tests |
| `test_format_simple.py` | ~200 | Simple test script |
| `example_usage.py` | ~420 | Usage examples |
| `README_GMSH_FORMATTER.md` | ~650 | Complete documentation |
| `QUICKSTART.md` | ~200 | Quick reference |

## Dependencies

### Required
- Python 3.6+

### Optional
- `gmsh` - Required for:
  - `test_gmsh_formatter.py`
  - `example_usage.py` (examples 2-3)
  - Monkey patching functionality

### Not Required
- Can format existing MSH files without gmsh
- `test_format_simple.py` works without gmsh
- All documentation is standalone

## Typical Workflow

### First Time Setup

1. **Review documentation**
   ```bash
   # Read QUICKSTART.md for overview
   # Read README_GMSH_FORMATTER.md for details
   ```

2. **Test with existing files**
   ```bash
   python scripts/test_format_simple.py
   ```

3. **Try examples**
   ```bash
   python scripts/example_usage.py
   ```

### Daily Usage

**Option A: Format existing files**
```python
import gmsh_formatter
gmsh_formatter.format_msh_file("mesh.msh", precision=12)
```

**Option B: Integrate with GMSH**
```python
import gmsh
import gmsh_formatter

gmsh_formatter.apply_monkey_patch()
# ... use gmsh normally ...
gmsh.write("output.msh", precision=10, align_columns=True)
```

## Configuration Reference

Quick reference for all options:

```python
{
    'precision': 16,              # Decimal places
    'align_columns': True,        # Column alignment
    'add_comments': True,         # Section comments
    'compact_mode': False,        # Compact spacing
    'scientific_threshold': 1e-6, # Sci notation threshold
    'column_width': 20,           # Column width
    'section_spacing': 1,         # Lines between sections
    'node_comment_freq': 0,       # Comment frequency (nodes)
    'element_comment_freq': 0,    # Comment frequency (elements)
}
```

## Common Use Cases

### Use Case 1: Debugging
```python
gmsh_formatter.format_msh_file(
    "debug.msh",
    precision=16,
    align_columns=True,
    add_comments=True
)
```

### Use Case 2: Production
```python
gmsh.write(
    "production.msh",
    precision=8,
    compact_mode=True,
    add_comments=False
)
```

### Use Case 3: Documentation
```python
gmsh_formatter.format_msh_file(
    "tutorial.msh",
    precision=6,
    align_columns=True,
    add_comments=True,
    column_width=15
)
```

## Troubleshooting

### Common Issues

**Problem**: "gmsh module not found"
**Solution**: Install gmsh or use standalone file formatting

**Problem**: "Monkey patch doesn't work"
**Solution**: Call `apply_monkey_patch()` before using gmsh.write()

**Problem**: "Formatting takes too long"
**Solution**: Use lower precision or disable alignment for large files

See `README_GMSH_FORMATTER.md` for detailed troubleshooting.

## Next Steps

1. ✅ Read `QUICKSTART.md` (2 minutes)
2. ✅ Run `test_format_simple.py` (see it work)
3. ✅ Try `example_usage.py` (learn by example)
4. ✅ Integrate into your project
5. ✅ Refer to `README_GMSH_FORMATTER.md` as needed

## Support

For questions or issues:
1. Check `QUICKSTART.md` FAQ section
2. Review `example_usage.py` for similar use cases
3. Read `README_GMSH_FORMATTER.md` troubleshooting
4. Examine source code docstrings in `gmsh_formatter.py`

## Version

**Implementation Date**: 2026-02-10
**Status**: ✅ Complete and Production Ready
**Python Version**: 3.6+
**MSH Format**: 4.1 (extensible to others)

---

**Start Here**: `QUICKSTART.md` → `example_usage.py` → Your project!
