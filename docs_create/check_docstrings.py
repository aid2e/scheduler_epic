#!/usr/bin/env python3
"""
Check Python files for missing or incomplete docstrings.
This script helps maintain good documentation quality by identifying missing docstrings.
"""

import os
import sys
import ast
import argparse
import re
from typing import Dict, List, Set, Tuple, Optional, Any

# Configure colors for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class DocstringChecker:
    def __init__(self, path: str, ignore_private: bool = True, ignore_dirs: Optional[List[str]] = None):
        self.path = os.path.abspath(path)
        self.ignore_private = ignore_private
        self.ignore_dirs = ignore_dirs or ['venv', 'env', '__pycache__', 'build', 'dist', '.git', '.github', 'tests']
        self.missing_docstrings = []
        self.incomplete_docstrings = []
        self.statistics = {
            'files_checked': 0,
            'classes_checked': 0,
            'methods_checked': 0,
            'functions_checked': 0,
            'missing_class_docstrings': 0,
            'missing_method_docstrings': 0,
            'missing_function_docstrings': 0,
            'incomplete_docstrings': 0,
        }
    
    def should_ignore_dir(self, dir_path: str) -> bool:
        """Check if a directory should be ignored.
        
        Args:
            dir_path: Path to the directory
            
        Returns:
            True if the directory should be ignored, False otherwise
        """
        dir_name = os.path.basename(dir_path)
        return dir_name in self.ignore_dirs
    
    def should_ignore_file(self, file_path: str) -> bool:
        """Check if a file should be ignored.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if the file should be ignored, False otherwise
        """
        return not file_path.endswith('.py')
    
    def is_private(self, name: str) -> bool:
        """Check if a name is private (starts with underscore).
        
        Args:
            name: The name to check
            
        Returns:
            True if the name is private, False otherwise
        """
        return name.startswith('_') and not name.startswith('__') and not name.endswith('__')
    
    def check_file(self, file_path: str) -> None:
        """Check a single Python file for docstrings.
        
        Args:
            file_path: Path to the Python file
        """
        self.statistics['files_checked'] += 1
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()
            
            tree = ast.parse(source)
            
            for node in ast.walk(tree):
                # Check for class definitions
                if isinstance(node, ast.ClassDef):
                    self.statistics['classes_checked'] += 1
                    
                    if self.ignore_private and self.is_private(node.name):
                        continue
                    
                    # Check class docstring
                    if not ast.get_docstring(node):
                        self.missing_docstrings.append((file_path, f"Class '{node.name}'", node.lineno))
                        self.statistics['missing_class_docstrings'] += 1
                    elif not self._check_docstring_completeness(ast.get_docstring(node)):
                        self.incomplete_docstrings.append((file_path, f"Class '{node.name}'", node.lineno))
                        self.statistics['incomplete_docstrings'] += 1
                    
                    # Check methods
                    for subnode in node.body:
                        if isinstance(subnode, ast.FunctionDef):
                            self.statistics['methods_checked'] += 1
                            
                            if self.ignore_private and self.is_private(subnode.name):
                                continue
                            
                            # Skip __special__ methods except __init__
                            if subnode.name.startswith('__') and subnode.name.endswith('__') and subnode.name != '__init__':
                                continue
                            
                            # Check method docstring
                            if not ast.get_docstring(subnode):
                                self.missing_docstrings.append((file_path, f"Method '{node.name}.{subnode.name}'", subnode.lineno))
                                self.statistics['missing_method_docstrings'] += 1
                            elif not self._check_docstring_completeness(ast.get_docstring(subnode)):
                                self.incomplete_docstrings.append((file_path, f"Method '{node.name}.{subnode.name}'", subnode.lineno))
                                self.statistics['incomplete_docstrings'] += 1
                
                # Check for function definitions
                elif isinstance(node, ast.FunctionDef) and node.parent_field != 'body':
                    self.statistics['functions_checked'] += 1
                    
                    if self.ignore_private and self.is_private(node.name):
                        continue
                    
                    # Check function docstring
                    if not ast.get_docstring(node):
                        self.missing_docstrings.append((file_path, f"Function '{node.name}'", node.lineno))
                        self.statistics['missing_function_docstrings'] += 1
                    elif not self._check_docstring_completeness(ast.get_docstring(node)):
                        self.incomplete_docstrings.append((file_path, f"Function '{node.name}'", node.lineno))
                        self.statistics['incomplete_docstrings'] += 1
        
        except SyntaxError as e:
            print(f"{Colors.RED}Syntax error in {file_path}: {e}{Colors.ENDC}")
        except Exception as e:
            print(f"{Colors.RED}Error processing {file_path}: {e}{Colors.ENDC}")
    
    def _check_docstring_completeness(self, docstring: str) -> bool:
        """Check if a docstring is complete (has all sections).
        
        Args:
            docstring: The docstring to check
            
        Returns:
            True if the docstring is complete, False otherwise
        """
        if not docstring:
            return False
        
        # Check if docstring is just a placeholder
        if docstring.strip() in ["TODO", "TODO:", "FIXME", "FIXME:", "..."]:
            return False
        
        # Check for Args section if there are parameters
        # This is a simple heuristic and may not catch all cases
        if "Args:" not in docstring and "Parameters:" not in docstring:
            # This might be a simple docstring for a function without parameters
            return True
        
        # Check if Args section is empty
        args_section = re.search(r'Args:(.*?)(?:Returns:|Raises:|Yields:|Examples:|$)', docstring, re.DOTALL)
        if args_section and not args_section.group(1).strip():
            return False
        
        return True
    
    def check_directory(self, dir_path: Optional[str] = None) -> None:
        """Recursively check all Python files in a directory.
        
        Args:
            dir_path: Path to the directory
        """
        if dir_path is None:
            dir_path = self.path
        
        for item in os.listdir(dir_path):
            item_path = os.path.join(dir_path, item)
            
            if os.path.isdir(item_path):
                if not self.should_ignore_dir(item_path):
                    self.check_directory(item_path)
            elif os.path.isfile(item_path) and not self.should_ignore_file(item_path):
                self.check_file(item_path)
    
    def print_results(self) -> None:
        """Print the results of the docstring check."""
        print(f"\n{Colors.HEADER}Docstring Check Results{Colors.ENDC}")
        print(f"{Colors.BOLD}{'=' * 80}{Colors.ENDC}")
        
        # Print statistics
        print(f"\n{Colors.BLUE}Statistics:{Colors.ENDC}")
        print(f"  Files checked: {self.statistics['files_checked']}")
        print(f"  Classes checked: {self.statistics['classes_checked']}")
        print(f"  Methods checked: {self.statistics['methods_checked']}")
        print(f"  Functions checked: {self.statistics['functions_checked']}")
        
        # Print missing docstrings
        if self.missing_docstrings:
            print(f"\n{Colors.RED}Missing Docstrings:{Colors.ENDC}")
            for file_path, item_name, line_no in self.missing_docstrings:
                rel_path = os.path.relpath(file_path, self.path)
                print(f"  {rel_path}:{line_no} - {item_name}")
        
        # Print incomplete docstrings
        if self.incomplete_docstrings:
            print(f"\n{Colors.YELLOW}Incomplete Docstrings:{Colors.ENDC}")
            for file_path, item_name, line_no in self.incomplete_docstrings:
                rel_path = os.path.relpath(file_path, self.path)
                print(f"  {rel_path}:{line_no} - {item_name}")
        
        # Print summary
        print(f"\n{Colors.BLUE}Summary:{Colors.ENDC}")
        total_missing = sum([
            self.statistics['missing_class_docstrings'],
            self.statistics['missing_method_docstrings'],
            self.statistics['missing_function_docstrings']
        ])
        total_items = sum([
            self.statistics['classes_checked'],
            self.statistics['methods_checked'],
            self.statistics['functions_checked']
        ])
        
        if total_items > 0:
            coverage = (total_items - total_missing) / total_items * 100
            print(f"  Docstring coverage: {coverage:.1f}%")
            
            if coverage >= 90:
                status = f"{Colors.GREEN}Excellent{Colors.ENDC}"
            elif coverage >= 75:
                status = f"{Colors.BLUE}Good{Colors.ENDC}"
            elif coverage >= 50:
                status = f"{Colors.YELLOW}Needs Improvement{Colors.ENDC}"
            else:
                status = f"{Colors.RED}Poor{Colors.ENDC}"
            
            print(f"  Documentation status: {status}")
        
        print(f"{Colors.BOLD}{'=' * 80}{Colors.ENDC}")
        
        # Print calls to action
        if self.missing_docstrings or self.incomplete_docstrings:
            print(f"\n{Colors.YELLOW}Recommendations:{Colors.ENDC}")
            print("  1. Add docstrings to all public classes, methods, and functions")
            print("  2. Follow Google-style docstring format")
            print("  3. Include Args, Returns, and Raises sections where appropriate")
            print("  4. Use type annotations for all parameters and return values")
        else:
            print(f"\n{Colors.GREEN}Great job! All code is properly documented.{Colors.ENDC}")

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description='Check Python files for missing or incomplete docstrings')
    parser.add_argument('path', nargs='?', default='.', help='Path to the directory or file to check')
    parser.add_argument('--include-private', action='store_true', help='Include private (underscore-prefixed) items')
    parser.add_argument('--ignore-dirs', nargs='+', help='Additional directories to ignore')
    
    args = parser.parse_args()
    
    ignore_dirs = ['venv', 'env', '__pycache__', 'build', 'dist', '.git', '.github', 'tests']
    if args.ignore_dirs:
        ignore_dirs.extend(args.ignore_dirs)
    
    checker = DocstringChecker(
        path=args.path,
        ignore_private=not args.include_private,
        ignore_dirs=ignore_dirs
    )
    
    if os.path.isdir(args.path):
        checker.check_directory()
    elif os.path.isfile(args.path):
        checker.check_file(args.path)
    else:
        print(f"{Colors.RED}Error: {args.path} is not a valid file or directory{Colors.ENDC}")
        return 1
    
    checker.print_results()
    
    # Return non-zero exit code if there are missing docstrings
    return 1 if checker.missing_docstrings else 0

if __name__ == "__main__":
    sys.exit(main())
