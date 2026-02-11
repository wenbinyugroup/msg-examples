"""
Test script for GMSH Formatter

This script tests the formatting functionality on existing MSH files
and demonstrates various usage patterns.
"""

import sys
import os

# Add scripts directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import gmsh_formatter
from pathlib import Path


def test_format_existing_file():
    """Test formatting an existing MSH file"""
    print("\n" + "="*60)
    print("TEST 1: Format Existing MSH File")
    print("="*60)
    
    # Find an existing MSH file
    test_files = [
        "../examples/gmsh_t18/t18_simple.msh",
        "../examples/gmsh_periodic/periodic.msh",
        "../examples/gmsh_t18/sg.msh",
    ]
    
    for test_file in test_files:
        file_path = os.path.join(os.path.dirname(__file__), test_file)
        if os.path.exists(file_path):
            print(f"\nFormatting: {test_file}")
            
            # Create output file
            output_path = file_path.replace('.msh', '_formatted.msh')
            
            try:
                # Format with default options
                gmsh_formatter.format_msh_file(
                    file_path, 
                    output_path=output_path,
                    precision=10,
                    align_columns=True,
                    add_comments=True
                )
                
                print(f"✓ Formatted file created: {output_path}")
                
                # Show file size comparison
                orig_size = os.path.getsize(file_path)
                fmt_size = os.path.getsize(output_path)
                print(f"  Original size: {orig_size:,} bytes")
                print(f"  Formatted size: {fmt_size:,} bytes")
                print(f"  Size difference: {fmt_size - orig_size:+,} bytes ({100*(fmt_size/orig_size - 1):.1f}%)")
                
                # Show first few lines
                print("\n  First 20 lines of formatted file:")
                with open(output_path, 'r') as f:
                    lines = f.readlines()[:20]
                    for i, line in enumerate(lines, 1):
                        print(f"    {i:3d}: {line.rstrip()}")
                    if len(lines) < 20:
                        print(f"    ... (file has {len(lines)} total lines)")
                
            except Exception as e:
                print(f"✗ Error: {e}")
                import traceback
                traceback.print_exc()
            
            break
    else:
        print("No test MSH files found!")


def test_monkey_patch():
    """Test monkey patching functionality"""
    print("\n" + "="*60)
    print("TEST 2: Monkey Patch Functionality")
    print("="*60)
    
    try:
        import gmsh
        
        # Apply monkey patch
        print("\nApplying monkey patch...")
        gmsh_formatter.apply_monkey_patch()
        
        # Initialize gmsh
        gmsh.initialize()
        gmsh.model.add("test_patch")
        
        # Create simple geometry
        lc = 1.0
        gmsh.model.geo.addPoint(0, 0, 0, lc, 1)
        gmsh.model.geo.addPoint(1, 0, 0, lc, 2)
        gmsh.model.geo.addPoint(1, 1, 0, lc, 3)
        gmsh.model.geo.addPoint(0, 1, 0, lc, 4)
        
        gmsh.model.geo.addLine(1, 2, 1)
        gmsh.model.geo.addLine(2, 3, 2)
        gmsh.model.geo.addLine(3, 4, 3)
        gmsh.model.geo.addLine(4, 1, 4)
        
        gmsh.model.geo.addCurveLoop([1, 2, 3, 4], 1)
        gmsh.model.geo.addPlaneSurface([1], 1)
        
        gmsh.model.geo.synchronize()
        gmsh.model.addPhysicalGroup(2, [1], 1, name="Test Surface")
        
        # Generate mesh
        gmsh.model.mesh.generate(2)
        
        # Write with formatting options
        output_file = os.path.join(os.path.dirname(__file__), "test_monkey_patch.msh")
        print(f"\nWriting formatted mesh to: {output_file}")
        
        gmsh.write(
            output_file,
            precision=12,
            align_columns=True,
            add_comments=True
        )
        
        gmsh.finalize()
        
        print("✓ Mesh created with monkey-patched gmsh.write()")
        
        # Show result
        if os.path.exists(output_file):
            print("\n  First 30 lines of generated file:")
            with open(output_file, 'r') as f:
                lines = f.readlines()[:30]
                for i, line in enumerate(lines, 1):
                    print(f"    {i:3d}: {line.rstrip()}")
        
        # Restore original
        print("\nRestoring original gmsh.write...")
        gmsh_formatter.restore_original()
        print("✓ Original function restored")
        
    except ImportError:
        print("✗ gmsh module not available, skipping monkey patch test")
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()


def test_context_manager():
    """Test context manager functionality"""
    print("\n" + "="*60)
    print("TEST 3: Context Manager")
    print("="*60)
    
    try:
        import gmsh
        
        gmsh.initialize()
        gmsh.model.add("test_context")
        
        # Create simple geometry
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
        gmsh.model.mesh.generate(2)
        
        # Use context manager for formatted output
        output_file = os.path.join(os.path.dirname(__file__), "test_context_formatted.msh")
        print(f"\nWriting with context manager to: {output_file}")
        
        with gmsh_formatter.formatted_gmsh(precision=8, align_columns=True):
            gmsh.write(output_file)
        
        print("✓ Mesh written with context manager")
        
        gmsh.finalize()
        
        # Show result
        if os.path.exists(output_file):
            print("\n  First 25 lines:")
            with open(output_file, 'r') as f:
                lines = f.readlines()[:25]
                for i, line in enumerate(lines, 1):
                    print(f"    {i:3d}: {line.rstrip()}")
        
    except ImportError:
        print("✗ gmsh module not available, skipping context manager test")
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()


def test_different_options():
    """Test various formatting options"""
    print("\n" + "="*60)
    print("TEST 4: Different Formatting Options")
    print("="*60)
    
    # Find a test file
    test_file = None
    test_files = [
        "../examples/gmsh_t18/t18_simple.msh",
        "../examples/gmsh_periodic/periodic.msh",
    ]
    
    for tf in test_files:
        file_path = os.path.join(os.path.dirname(__file__), tf)
        if os.path.exists(file_path):
            test_file = file_path
            break
    
    if not test_file:
        print("No test MSH files found!")
        return
    
    print(f"\nTesting various options on: {test_file}")
    
    # Test different configurations
    configs = [
        {
            'name': 'High Precision',
            'options': {'precision': 16, 'align_columns': True, 'add_comments': False}
        },
        {
            'name': 'Compact Mode',
            'options': {'precision': 6, 'align_columns': False, 'compact_mode': True}
        },
        {
            'name': 'With Comments',
            'options': {'precision': 8, 'align_columns': True, 'add_comments': True}
        },
    ]
    
    for config in configs:
        print(f"\n  Testing: {config['name']}")
        output_file = test_file.replace('.msh', f"_opt_{config['name'].replace(' ', '_').lower()}.msh")
        
        try:
            gmsh_formatter.format_msh_file(test_file, output_path=output_file, **config['options'])
            
            size = os.path.getsize(output_file)
            orig_size = os.path.getsize(test_file)
            print(f"    ✓ Created: {os.path.basename(output_file)}")
            print(f"      Size: {size:,} bytes (original: {orig_size:,}, diff: {100*(size/orig_size - 1):+.1f}%)")
            
        except Exception as e:
            print(f"    ✗ Error: {e}")


def show_comparison():
    """Show side-by-side comparison of original vs formatted"""
    print("\n" + "="*60)
    print("TEST 5: Side-by-Side Comparison")
    print("="*60)
    
    test_file = None
    test_files = [
        "../examples/gmsh_t18/t18_simple.msh",
        "../examples/gmsh_periodic/periodic.msh",
    ]
    
    for tf in test_files:
        file_path = os.path.join(os.path.dirname(__file__), tf)
        if os.path.exists(file_path):
            test_file = file_path
            break
    
    if not test_file:
        print("No test MSH files found!")
        return
    
    # Create formatted version
    formatted_file = test_file.replace('.msh', '_comparison.msh')
    gmsh_formatter.format_msh_file(
        test_file, 
        output_path=formatted_file,
        precision=10,
        align_columns=True,
        add_comments=True
    )
    
    # Show comparison
    print(f"\nComparing: {os.path.basename(test_file)}")
    print("\nOriginal (left) vs Formatted (right):")
    print("-" * 120)
    
    with open(test_file, 'r') as f1, open(formatted_file, 'r') as f2:
        lines1 = f1.readlines()[:40]
        lines2 = f2.readlines()[:40]
        
        max_lines = max(len(lines1), len(lines2))
        for i in range(max_lines):
            line1 = lines1[i].rstrip() if i < len(lines1) else ""
            line2 = lines2[i].rstrip() if i < len(lines2) else ""
            
            # Truncate long lines for display
            line1 = line1[:55] + "..." if len(line1) > 58 else line1
            line2 = line2[:55] + "..." if len(line2) > 58 else line2
            
            print(f"{i+1:3d}: {line1:58s} | {line2}")


def main():
    """Run all tests"""
    print("\n")
    print("="*60)
    print("GMSH FORMATTER TEST SUITE")
    print("="*60)
    
    tests = [
        ("Format Existing File", test_format_existing_file),
        ("Monkey Patch", test_monkey_patch),
        ("Context Manager", test_context_manager),
        ("Different Options", test_different_options),
        ("Comparison View", show_comparison),
    ]
    
    for name, test_func in tests:
        try:
            test_func()
        except Exception as e:
            print(f"\n✗ Test '{name}' failed with error: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*60)
    print("TEST SUITE COMPLETED")
    print("="*60)


if __name__ == "__main__":
    main()
