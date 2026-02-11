"""
Example Usage of GMSH Formatter

This script demonstrates how to integrate gmsh_formatter into your workflow.
Run this to see the formatter in action!
"""

import sys
import os

# Add scripts directory to path if needed
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import gmsh_formatter


def example_1_format_existing_file():
    """
    Example 1: Format an existing MSH file
    
    This is the simplest use case - you already have MSH files
    and want to make them more readable.
    """
    print("\n" + "="*70)
    print("EXAMPLE 1: Format Existing MSH File")
    print("="*70)
    
    # Find an existing MSH file from the examples
    test_file = None
    possible_files = [
        "../examples/gmsh_t18/t18_simple.msh",
        "../examples/gmsh_periodic/periodic.msh",
        "../examples/gmsh_t18/sg.msh",
    ]
    
    for f in possible_files:
        path = os.path.join(os.path.dirname(__file__), f)
        if os.path.exists(path):
            test_file = path
            break
    
    if not test_file:
        print("No example MSH files found. Skipping this example.")
        return
    
    print(f"\nFormatting file: {test_file}")
    
    # Create output file
    output_file = test_file.replace('.msh', '_example1_formatted.msh')
    
    # Format with custom options
    print("\nApplying formatting with options:")
    print("  - precision: 10 decimal places")
    print("  - align_columns: True")
    print("  - add_comments: True")
    print("  - column_width: 18")
    
    gmsh_formatter.format_msh_file(
        test_file,
        output_path=output_file,
        precision=10,
        align_columns=True,
        add_comments=True,
        column_width=18
    )
    
    print(f"\n✓ Formatted file created: {output_file}")
    print(f"\nCompare the files to see the difference:")
    print(f"  Original:  {test_file}")
    print(f"  Formatted: {output_file}")


def example_2_with_gmsh_api():
    """
    Example 2: Use with GMSH API (requires gmsh installed)
    
    This shows how to integrate formatter into your mesh generation workflow.
    """
    print("\n" + "="*70)
    print("EXAMPLE 2: Integration with GMSH API")
    print("="*70)
    
    try:
        import gmsh
    except ImportError:
        print("\nGMSH not installed. Skipping this example.")
        print("Install with: pip install gmsh")
        return
    
    # Apply the monkey patch
    print("\nApplying monkey patch to gmsh.write()...")
    gmsh_formatter.apply_monkey_patch()
    print("✓ Monkey patch applied")
    
    # Create a simple mesh
    print("\nCreating a simple 2D mesh...")
    
    gmsh.initialize()
    gmsh.model.add("example2_square")
    
    # Create a square
    lc = 0.5
    gmsh.model.geo.addPoint(0, 0, 0, lc, 1)
    gmsh.model.geo.addPoint(2, 0, 0, lc, 2)
    gmsh.model.geo.addPoint(2, 2, 0, lc, 3)
    gmsh.model.geo.addPoint(0, 2, 0, lc, 4)
    
    gmsh.model.geo.addLine(1, 2, 1)
    gmsh.model.geo.addLine(2, 3, 2)
    gmsh.model.geo.addLine(3, 4, 3)
    gmsh.model.geo.addLine(4, 1, 4)
    
    gmsh.model.geo.addCurveLoop([1, 2, 3, 4], 1)
    gmsh.model.geo.addPlaneSurface([1], 1)
    
    gmsh.model.geo.synchronize()
    
    # Add physical group
    gmsh.model.addPhysicalGroup(2, [1], 1, name="Square Surface")
    
    # Generate mesh
    gmsh.model.mesh.generate(2)
    print("✓ Mesh generated")
    
    # Write with formatting options
    output_file = os.path.join(os.path.dirname(__file__), "example2_formatted.msh")
    
    print(f"\nWriting mesh with formatting to: {output_file}")
    print("  Options: precision=12, align_columns=True, add_comments=True")
    
    # Now gmsh.write accepts formatting parameters!
    gmsh.write(
        output_file,
        precision=12,
        align_columns=True,
        add_comments=True
    )
    
    gmsh.finalize()
    
    print("✓ Formatted mesh file created")
    print(f"\nView the file to see nicely formatted output: {output_file}")
    
    # Restore original if needed
    gmsh_formatter.restore_original()
    print("\n✓ Original gmsh.write() restored")


def example_3_context_manager():
    """
    Example 3: Use context manager for temporary formatting
    
    This shows how to use formatting only when needed.
    """
    print("\n" + "="*70)
    print("EXAMPLE 3: Context Manager for Temporary Formatting")
    print("="*70)
    
    try:
        import gmsh
    except ImportError:
        print("\nGMSH not installed. Skipping this example.")
        return
    
    print("\nCreating mesh with context manager...")
    
    gmsh.initialize()
    gmsh.model.add("example3_circle")
    
    # Create a circle
    gmsh.model.occ.addDisk(0, 0, 0, 1, 1)
    gmsh.model.occ.synchronize()
    
    gmsh.model.addPhysicalGroup(2, [1], 1, name="Circle")
    gmsh.model.mesh.setSize(gmsh.model.getEntities(0), 0.2)
    gmsh.model.mesh.generate(2)
    
    # Use context manager for formatted output
    formatted_file = os.path.join(os.path.dirname(__file__), "example3_formatted.msh")
    unformatted_file = os.path.join(os.path.dirname(__file__), "example3_unformatted.msh")
    
    print(f"\nWriting formatted file with context manager...")
    with gmsh_formatter.formatted_gmsh(precision=10, align_columns=True):
        gmsh.write(formatted_file)
    print(f"✓ Formatted: {formatted_file}")
    
    print(f"\nWriting unformatted file (original gmsh.write)...")
    gmsh.write(unformatted_file)
    print(f"✓ Unformatted: {unformatted_file}")
    
    gmsh.finalize()
    
    # Show size comparison
    fmt_size = os.path.getsize(formatted_file)
    unfmt_size = os.path.getsize(unformatted_file)
    
    print(f"\nFile size comparison:")
    print(f"  Formatted:   {fmt_size:,} bytes")
    print(f"  Unformatted: {unfmt_size:,} bytes")
    print(f"  Difference:  {fmt_size - unfmt_size:+,} bytes ({100*(fmt_size/unfmt_size - 1):+.1f}%)")


def example_4_batch_processing():
    """
    Example 4: Batch process multiple MSH files
    
    Format all MSH files in a directory.
    """
    print("\n" + "="*70)
    print("EXAMPLE 4: Batch Processing Multiple Files")
    print("="*70)
    
    import glob
    
    # Find MSH files in examples directory
    examples_dir = os.path.join(os.path.dirname(__file__), "..", "examples")
    pattern = os.path.join(examples_dir, "**", "*.msh")
    
    msh_files = glob.glob(pattern, recursive=True)
    
    if not msh_files:
        print("\nNo MSH files found for batch processing.")
        return
    
    print(f"\nFound {len(msh_files)} MSH file(s) to process")
    
    # Process each file
    for i, msh_file in enumerate(msh_files[:3], 1):  # Limit to 3 for demo
        print(f"\n[{i}/{min(3, len(msh_files))}] Processing: {os.path.basename(msh_file)}")
        
        output_file = msh_file.replace('.msh', '_batch_formatted.msh')
        
        try:
            gmsh_formatter.format_msh_file(
                msh_file,
                output_path=output_file,
                precision=8,
                align_columns=True,
                add_comments=False,  # Compact for batch
                compact_mode=True
            )
            
            orig_size = os.path.getsize(msh_file)
            new_size = os.path.getsize(output_file)
            
            print(f"  ✓ Created: {os.path.basename(output_file)}")
            print(f"    Size: {orig_size:,} → {new_size:,} bytes ({100*(new_size/orig_size - 1):+.1f}%)")
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
    
    if len(msh_files) > 3:
        print(f"\n... and {len(msh_files) - 3} more files")


def example_5_different_precisions():
    """
    Example 5: Compare different precision settings
    
    Show how precision affects file size and readability.
    """
    print("\n" + "="*70)
    print("EXAMPLE 5: Comparing Different Precision Settings")
    print("="*70)
    
    # Find a test file
    test_file = None
    possible_files = [
        "../examples/gmsh_t18/t18_simple.msh",
        "../examples/gmsh_periodic/periodic.msh",
    ]
    
    for f in possible_files:
        path = os.path.join(os.path.dirname(__file__), f)
        if os.path.exists(path):
            test_file = path
            break
    
    if not test_file:
        print("No example MSH files found. Skipping this example.")
        return
    
    print(f"\nTest file: {test_file}")
    print(f"Original size: {os.path.getsize(test_file):,} bytes")
    
    # Test different precisions
    precisions = [4, 8, 12, 16]
    
    print(f"\nFormatting with different precision settings:")
    print(f"{'Precision':<12} {'File Size':<15} {'Size Change':<15}")
    print("-" * 42)
    
    for precision in precisions:
        output_file = test_file.replace('.msh', f'_precision{precision}.msh')
        
        gmsh_formatter.format_msh_file(
            test_file,
            output_path=output_file,
            precision=precision,
            align_columns=True
        )
        
        size = os.path.getsize(output_file)
        orig_size = os.path.getsize(test_file)
        
        print(f"{precision:<12} {size:>12,} B   {100*(size/orig_size - 1):>+6.1f}%")


def main():
    """Run all examples"""
    print("\n")
    print("="*70)
    print("GMSH FORMATTER - USAGE EXAMPLES")
    print("="*70)
    print("\nThis script demonstrates various ways to use gmsh_formatter.")
    print("Each example is self-contained and can be run independently.")
    
    examples = [
        ("Format Existing File", example_1_format_existing_file),
        ("GMSH API Integration", example_2_with_gmsh_api),
        ("Context Manager", example_3_context_manager),
        ("Batch Processing", example_4_batch_processing),
        ("Precision Comparison", example_5_different_precisions),
    ]
    
    for name, example_func in examples:
        try:
            example_func()
        except Exception as e:
            print(f"\n✗ Example '{name}' failed: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*70)
    print("EXAMPLES COMPLETED")
    print("="*70)
    print("\nFormatted files have been created in the scripts directory.")
    print("Compare them with originals to see the improvements!")
    print("\nFor more information, see:")
    print("  - README_GMSH_FORMATTER.md (complete documentation)")
    print("  - QUICKSTART.md (quick reference)")


if __name__ == "__main__":
    main()
