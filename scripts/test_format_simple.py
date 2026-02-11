"""
Simple test script for GMSH Formatter - formats existing MSH files without requiring gmsh
"""

import sys
import os

# Add scripts directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import gmsh_formatter


def main():
    print("\n" + "="*70)
    print("GMSH FORMATTER - Simple File Formatting Test")
    print("="*70)
    
    # Find existing MSH files
    test_files = [
        "../examples/gmsh_t18/t18_simple.msh",
        "../examples/gmsh_periodic/periodic.msh",
        "../examples/gmsh_t18/sg.msh",
        "../examples/sg23_udfrc_gmsh_sc/sg2d_fm_square.msh",
    ]
    
    found_files = []
    for test_file in test_files:
        file_path = os.path.join(os.path.dirname(__file__), test_file)
        if os.path.exists(file_path):
            found_files.append((test_file, file_path))
    
    if not found_files:
        print("\n✗ No test MSH files found!")
        return
    
    print(f"\nFound {len(found_files)} MSH file(s) to format:\n")
    
    for test_name, file_path in found_files:
        print("-" * 70)
        print(f"\nFile: {test_name}")
        print(f"Path: {file_path}")
        
        # Get file info
        orig_size = os.path.getsize(file_path)
        print(f"Original size: {orig_size:,} bytes")
        
        # Show original first 15 lines
        print("\nOriginal content (first 15 lines):")
        with open(file_path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f, 1):
                if i > 15:
                    break
                print(f"  {i:3d}: {line.rstrip()}")
        
        # Format the file
        output_path = file_path.replace('.msh', '_formatted.msh')
        
        print(f"\nFormatting with options:")
        print("  - precision: 12")
        print("  - align_columns: True")
        print("  - add_comments: True")
        
        try:
            gmsh_formatter.format_msh_file(
                file_path,
                output_path=output_path,
                precision=12,
                align_columns=True,
                add_comments=True
            )
            
            # Get formatted file info
            fmt_size = os.path.getsize(output_path)
            
            print(f"\n✓ Formatted file created: {os.path.basename(output_path)}")
            print(f"  Formatted size: {fmt_size:,} bytes")
            print(f"  Size difference: {fmt_size - orig_size:+,} bytes ({100*(fmt_size/orig_size - 1):+.1f}%)")
            
            # Show formatted first 15 lines
            print("\nFormatted content (first 15 lines):")
            with open(output_path, 'r', encoding='utf-8') as f:
                for i, line in enumerate(f, 1):
                    if i > 15:
                        break
                    print(f"  {i:3d}: {line.rstrip()}")
            
            # Show side-by-side comparison of Nodes section
            print("\n" + "="*70)
            print("NODES SECTION COMPARISON")
            print("="*70)
            print("\nOriginal (left) vs Formatted (right):")
            print("-" * 140)
            
            with open(file_path, 'r', encoding='utf-8') as f1, \
                 open(output_path, 'r', encoding='utf-8') as f2:
                
                # Find Nodes section in both files
                orig_lines = []
                fmt_lines = []
                
                # Read original
                in_nodes = False
                for line in f1:
                    if line.strip() == '$Nodes':
                        in_nodes = True
                        orig_lines.append(line)
                    elif line.strip() == '$EndNodes':
                        orig_lines.append(line)
                        break
                    elif in_nodes:
                        orig_lines.append(line)
                        if len(orig_lines) > 25:  # Limit to first 25 lines
                            break
                
                # Read formatted
                in_nodes = False
                for line in f2:
                    if line.strip() == '$Nodes':
                        in_nodes = True
                        fmt_lines.append(line)
                    elif line.strip() == '$EndNodes':
                        fmt_lines.append(line)
                        break
                    elif in_nodes:
                        fmt_lines.append(line)
                        if len(fmt_lines) > 25:  # Limit to first 25 lines
                            break
                
                # Show comparison
                max_lines = max(len(orig_lines), len(fmt_lines))
                for i in range(min(max_lines, 25)):
                    line1 = orig_lines[i].rstrip() if i < len(orig_lines) else ""
                    line2 = fmt_lines[i].rstrip() if i < len(fmt_lines) else ""
                    
                    # Truncate for display
                    line1_display = (line1[:65] + "...") if len(line1) > 68 else line1
                    line2_display = (line2[:65] + "...") if len(line2) > 68 else line2
                    
                    print(f"{i+1:3d}: {line1_display:68s} | {line2_display}")
            
            print()
            
        except Exception as e:
            print(f"\n✗ Error formatting file: {e}")
            import traceback
            traceback.print_exc()
        
        print()
    
    print("="*70)
    print("TEST COMPLETED")
    print("="*70)
    print("\nFormatted files have been created with '_formatted.msh' suffix.")
    print("You can compare them with the original files to see the improvements.")


if __name__ == "__main__":
    main()
