"""
GMSH Formatter - Enhanced MSH File Formatting with Monkey Patching

This module provides formatting enhancements for gmsh.write() function
without modifying the original gmsh source code.

Usage:
    import gmsh
    import gmsh_formatter
    
    # Apply monkey patch (automatic)
    gmsh_formatter.apply_monkey_patch()
    
    # Use gmsh.write with formatting options
    gmsh.write("mesh.msh", precision=8, align_columns=True)
    
    # Or format existing MSH file
    gmsh_formatter.format_msh_file("existing.msh")
"""

import os
import re
import shutil
from typing import Dict, Any, Optional, List, Tuple
from contextlib import contextmanager
import functools


# Store original function
_original_write = None
_patch_applied = False


# Default formatting options
DEFAULT_OPTIONS = {
    'precision': 16,           # Decimal places for floating point
    'align_columns': True,     # Enable column alignment
    'add_comments': True,      # Add explanatory comments
    'compact_mode': False,     # Reduced spacing for smaller files
    'scientific_threshold': 1e-6,  # Threshold for scientific notation
    'column_width': 20,        # Width for aligned columns
    'section_spacing': 1,      # Lines between sections
    'node_comment_freq': 0,    # Add comment every N nodes (0=disable)
    'element_comment_freq': 0, # Add comment every N elements (0=disable)
}


class MSHFormatter:
    """MSH file formatter with comprehensive formatting capabilities"""
    
    def __init__(self, options: Optional[Dict[str, Any]] = None):
        self.options = DEFAULT_OPTIONS.copy()
        if options:
            self.options.update(options)
    
    def format_number(self, value: float) -> str:
        """Format a floating point number with proper precision and alignment"""
        precision = self.options['precision']
        
        # Handle very small numbers with scientific notation
        if abs(value) < self.options['scientific_threshold'] and value != 0:
            formatted = f"{value:.{precision}e}"
        else:
            formatted = f"{value:.{precision}f}"
        
        # Add alignment if enabled
        if self.options['align_columns']:
            formatted = formatted.rjust(self.options['column_width'])
        
        return formatted
    
    def format_integer(self, value: int, width: Optional[int] = None) -> str:
        """Format an integer with optional width alignment"""
        if width is None:
            width = 10 if self.options['align_columns'] else 0
        
        if width > 0:
            return str(value).rjust(width)
        return str(value)
    
    def format_coordinate_line(self, coords: List[float]) -> str:
        """Format a line of coordinates (x, y, z)"""
        formatted_coords = [self.format_number(c) for c in coords]
        return ' '.join(formatted_coords)
    
    def parse_msh_file(self, content: str) -> Dict[str, List[str]]:
        """Parse MSH file content into sections"""
        sections = {}
        current_section = None
        section_content = []
        
        lines = content.split('\n')
        
        for line in lines:
            # Check for section start
            if line.startswith('$') and not line.startswith('$End'):
                if current_section:
                    sections[current_section] = section_content
                current_section = line[1:]  # Remove '$' prefix
                section_content = []
            # Check for section end
            elif line.startswith('$End'):
                if current_section:
                    sections[current_section] = section_content
                    current_section = None
                    section_content = []
            # Regular content line
            elif current_section is not None:
                section_content.append(line)
        
        return sections
    
    def format_mesh_format_section(self, lines: List[str]) -> List[str]:
        """Format the MeshFormat section"""
        formatted = []
        if self.options['add_comments']:
            formatted.append("# MSH File Format Version")
        formatted.extend(lines)
        return formatted
    
    def format_physical_names_section(self, lines: List[str]) -> List[str]:
        """Format the PhysicalNames section"""
        formatted = []
        if self.options['add_comments']:
            formatted.append("# Physical Groups")
        
        if lines:
            # First line is count
            formatted.append(lines[0])
            
            # Subsequent lines are: dim physicalTag "name"
            for line in lines[1:]:
                parts = line.split(None, 2)  # Split into max 3 parts
                if len(parts) >= 3:
                    dim = self.format_integer(int(parts[0]), 3)
                    tag = self.format_integer(int(parts[1]), 10)
                    name = parts[2]
                    formatted.append(f"{dim}{tag} {name}")
                else:
                    formatted.append(line)
        
        return formatted
    
    def format_entities_section(self, lines: List[str]) -> List[str]:
        """Format the Entities section"""
        formatted = []
        if self.options['add_comments']:
            formatted.append("# Geometric Entities")
        
        # Keep first line as-is (counts)
        if lines:
            formatted.append(lines[0])
            
            # Process remaining lines
            for line in lines[1:]:
                if not line.strip():
                    continue
                
                parts = line.split()
                if len(parts) >= 7:  # Entity definition with bounding box
                    # Entity tag
                    tag = self.format_integer(int(parts[0]), 10)
                    # Bounding box coordinates (6 values)
                    bbox = [float(parts[i]) for i in range(1, 7)]
                    bbox_str = ' '.join([self.format_number(v) for v in bbox])
                    # Remaining parts
                    rest = ' '.join(parts[7:])
                    formatted.append(f"{tag} {bbox_str} {rest}")
                else:
                    formatted.append(line)
        
        return formatted
    
    def format_nodes_section(self, lines: List[str]) -> List[str]:
        """Format the Nodes section with aligned coordinates"""
        formatted = []
        
        if not lines:
            return formatted
        
        if self.options['add_comments']:
            # Parse first line for counts
            parts = lines[0].split()
            if len(parts) >= 4:
                formatted.append(f"# Nodes: {parts[0]} entity blocks, {parts[1]} total nodes")
            else:
                formatted.append("# Node Definitions")
        
        # First line: entity count info
        formatted.append(lines[0])
        
        i = 1
        node_count = 0
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue
            
            parts = line.split()
            
            # Entity block header: entityDim entityTag parametric numNodes
            if len(parts) == 4:
                entity_dim = self.format_integer(int(parts[0]), 3)
                entity_tag = self.format_integer(int(parts[1]), 10)
                parametric = self.format_integer(int(parts[2]), 3)
                num_nodes = int(parts[3])
                
                if self.options['add_comments']:
                    formatted.append(f"# Entity {parts[1]}: {num_nodes} nodes")
                
                formatted.append(f"{entity_dim}{entity_tag}{parametric} {self.format_integer(num_nodes, 10)}")
                i += 1
                
                # Next num_nodes lines are node tags
                for _ in range(num_nodes):
                    if i < len(lines):
                        node_tag = int(lines[i].strip())
                        formatted.append(self.format_integer(node_tag, 10))
                        i += 1
                
                # Next num_nodes lines are coordinates
                for j in range(num_nodes):
                    if i < len(lines):
                        coord_line = lines[i].strip()
                        coords = [float(x) for x in coord_line.split()]
                        formatted.append(self.format_coordinate_line(coords))
                        i += 1
                        node_count += 1
                        
                        # Add periodic comments if enabled
                        if (self.options['node_comment_freq'] > 0 and 
                            node_count % self.options['node_comment_freq'] == 0):
                            formatted.append(f"# ... {node_count} nodes processed")
            else:
                # Fallback for unexpected format
                formatted.append(line)
                i += 1
        
        return formatted
    
    def format_elements_section(self, lines: List[str]) -> List[str]:
        """Format the Elements section with aligned connectivity"""
        formatted = []
        
        if not lines:
            return formatted
        
        if self.options['add_comments']:
            # Parse first line for counts
            parts = lines[0].split()
            if len(parts) >= 4:
                formatted.append(f"# Elements: {parts[0]} entity blocks, {parts[1]} total elements")
            else:
                formatted.append("# Element Definitions")
        
        # First line: entity count info
        formatted.append(lines[0])
        
        i = 1
        element_count = 0
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue
            
            parts = line.split()
            
            # Entity block header: entityDim entityTag elementType numElements
            if len(parts) == 4:
                entity_dim = self.format_integer(int(parts[0]), 3)
                entity_tag = self.format_integer(int(parts[1]), 10)
                element_type = self.format_integer(int(parts[2]), 5)
                num_elements = int(parts[3])
                
                if self.options['add_comments']:
                    formatted.append(f"# Entity {parts[1]}: {num_elements} elements of type {parts[2]}")
                
                formatted.append(f"{entity_dim}{entity_tag}{element_type} {self.format_integer(num_elements, 10)}")
                i += 1
                
                # Next num_elements lines are element definitions
                for j in range(num_elements):
                    if i < len(lines):
                        elem_line = lines[i].strip()
                        elem_parts = elem_line.split()
                        
                        # Format: elementTag node1 node2 ... nodeN
                        if elem_parts:
                            elem_tag = self.format_integer(int(elem_parts[0]), 10)
                            node_tags = [self.format_integer(int(n), 10) for n in elem_parts[1:]]
                            formatted.append(f"{elem_tag} {' '.join(node_tags)}")
                        
                        i += 1
                        element_count += 1
                        
                        # Add periodic comments if enabled
                        if (self.options['element_comment_freq'] > 0 and 
                            element_count % self.options['element_comment_freq'] == 0):
                            formatted.append(f"# ... {element_count} elements processed")
            else:
                # Fallback for unexpected format
                formatted.append(line)
                i += 1
        
        return formatted
    
    def format_section(self, section_name: str, lines: List[str]) -> List[str]:
        """Format a section based on its type"""
        formatters = {
            'MeshFormat': self.format_mesh_format_section,
            'PhysicalNames': self.format_physical_names_section,
            'Entities': self.format_entities_section,
            'Nodes': self.format_nodes_section,
            'Elements': self.format_elements_section,
        }
        
        formatter = formatters.get(section_name)
        if formatter:
            return formatter(lines)
        else:
            # Default: just return lines as-is
            if self.options['add_comments']:
                return [f"# Section: {section_name}"] + lines
            return lines
    
    def format_file(self, input_path: str, output_path: Optional[str] = None) -> None:
        """Format an MSH file"""
        # Read original file
        with open(input_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse into sections
        sections = self.parse_msh_file(content)
        
        # Format each section
        formatted_content = []
        
        # Standard section order for MSH 4.1
        section_order = [
            'MeshFormat', 'PhysicalNames', 'Entities', 'Nodes', 'Elements',
            'Periodic', 'GhostElements', 'Parametrizations', 'NodeData', 'ElementData'
        ]
        
        # Add sections in order
        for section_name in section_order:
            if section_name in sections:
                if formatted_content:  # Add spacing between sections
                    for _ in range(self.options['section_spacing']):
                        formatted_content.append('')
                
                formatted_content.append(f'${section_name}')
                formatted_lines = self.format_section(section_name, sections[section_name])
                formatted_content.extend(formatted_lines)
                formatted_content.append(f'$End{section_name}')
        
        # Add any remaining sections not in standard order
        for section_name, lines in sections.items():
            if section_name not in section_order:
                if formatted_content:
                    for _ in range(self.options['section_spacing']):
                        formatted_content.append('')
                
                formatted_content.append(f'${section_name}')
                formatted_lines = self.format_section(section_name, lines)
                formatted_content.extend(formatted_lines)
                formatted_content.append(f'$End{section_name}')
        
        # Write formatted content
        output_path = output_path or input_path
        
        # Create backup if overwriting
        if output_path == input_path:
            backup_path = input_path + '.backup'
            shutil.copy2(input_path, backup_path)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(formatted_content))
            if formatted_content:  # Ensure file ends with newline
                f.write('\n')


def format_msh_file(file_path: str, output_path: Optional[str] = None, **options) -> None:
    """
    Format an existing MSH file with enhanced readability.
    
    Args:
        file_path: Path to the MSH file to format
        output_path: Optional output path (default: overwrite input)
        **options: Formatting options (see DEFAULT_OPTIONS)
    
    Example:
        format_msh_file("mesh.msh", precision=8, align_columns=True)
    """
    formatter = MSHFormatter(options)
    formatter.format_file(file_path, output_path)


def write_formatted(fileName: str, **format_options) -> None:
    """
    Enhanced gmsh.write with formatting options.
    
    This function calls the original gmsh.write, then applies formatting.
    
    Args:
        fileName: Output file name
        **format_options: Formatting options (see DEFAULT_OPTIONS)
    
    Example:
        gmsh.write("mesh.msh", precision=8, align_columns=True)
    """
    global _original_write
    
    # Extract formatting options from kwargs
    msh_options = {}
    for key in list(format_options.keys()):
        if key in DEFAULT_OPTIONS:
            msh_options[key] = format_options.pop(key)
    
    # Call original gmsh.write
    if _original_write is not None:
        _original_write(fileName, **format_options)
    else:
        # Fallback if monkey patch wasn't applied properly
        import gmsh
        gmsh.write(fileName, **format_options)
    
    # Apply formatting if any options were specified
    if msh_options:
        try:
            format_msh_file(fileName, **msh_options)
        except Exception as e:
            print(f"Warning: MSH formatting failed: {e}")
            print("Original unformatted file preserved.")


def apply_monkey_patch() -> None:
    """
    Apply monkey patch to gmsh.write function.
    
    After calling this, all gmsh.write calls will use the enhanced version.
    
    Example:
        import gmsh
        import gmsh_formatter
        
        gmsh_formatter.apply_monkey_patch()
        gmsh.write("mesh.msh", precision=10)
    """
    global _original_write, _patch_applied
    
    if _patch_applied:
        print("Warning: Monkey patch already applied")
        return
    
    try:
        import gmsh
        _original_write = gmsh.write
        gmsh.write = write_formatted
        _patch_applied = True
        print("GMSH formatter monkey patch applied successfully")
    except ImportError:
        raise ImportError("gmsh module not found. Please install gmsh first.")


def restore_original() -> None:
    """
    Restore the original gmsh.write function.
    
    Example:
        gmsh_formatter.restore_original()
    """
    global _original_write, _patch_applied
    
    if not _patch_applied:
        print("Warning: No monkey patch to restore")
        return
    
    try:
        import gmsh
        if _original_write is not None:
            gmsh.write = _original_write
            _patch_applied = False
            print("Original gmsh.write restored")
    except ImportError:
        print("Warning: gmsh module not found")


@contextmanager
def formatted_gmsh(**options):
    """
    Context manager for temporary formatting.
    
    Example:
        with formatted_gmsh(precision=10):
            gmsh.write("formatted.msh")
        gmsh.write("original.msh")  # Original restored
    """
    apply_monkey_patch()
    
    # Store options in a way the patched function can access them
    # This is a simple approach; could be enhanced with thread-local storage
    original_defaults = DEFAULT_OPTIONS.copy()
    DEFAULT_OPTIONS.update(options)
    
    try:
        yield
    finally:
        DEFAULT_OPTIONS.clear()
        DEFAULT_OPTIONS.update(original_defaults)
        restore_original()


def formatted_write(func):
    """
    Decorator to automatically apply formatting to functions that call gmsh.write.
    
    Example:
        @formatted_write
        def create_mesh():
            gmsh.write("mesh.msh")
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        apply_monkey_patch()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            restore_original()
    
    return wrapper


if __name__ == "__main__":
    print("GMSH Formatter Module")
    print("=" * 50)
    print("\nUsage examples:")
    print("\n1. Format existing MSH file:")
    print("   format_msh_file('mesh.msh', precision=10)")
    print("\n2. Apply monkey patch:")
    print("   apply_monkey_patch()")
    print("   gmsh.write('mesh.msh', precision=10)")
    print("\n3. Use context manager:")
    print("   with formatted_gmsh(precision=10):")
    print("       gmsh.write('mesh.msh')")
    print("\nSee module docstring for more details.")
