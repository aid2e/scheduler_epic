#!/usr/bin/env python3
"""
Generate API documentation for the scheduler package.
This script parses Python modules and classes to generate Markdown documentation.
"""

import os
import sys
import inspect
import importlib.util
import re
import logging
from typing import List, Dict, Any, Optional, Union, Tuple, Set

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('api_doc_generator')

# Add the project root to the Python path so we can import the modules
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_root)

# Output directory for API documentation
OUTPUT_DIR = os.path.join(project_root, "docs", "api")
os.makedirs(OUTPUT_DIR, exist_ok=True)

logger.info(f"Generating API documentation in {OUTPUT_DIR}")

# Import modules from the scheduler package
try:
    import scheduler
    from scheduler.ax_scheduler import AxScheduler
    from scheduler.trial.trial import Trial
    from scheduler.job.job import Job
    from scheduler.runners.base_runner import BaseRunner
    from scheduler.runners.joblib_runner import JobLibRunner
    from scheduler.runners.slurm_runner import SlurmRunner
    try:
        from scheduler.runners.panda_runner import PandaRunner
        has_panda = True
    except ImportError:
        has_panda = False
        logger.warning("PandaRunner module not found, skipping documentation for this component")
except ImportError as e:
    logger.error(f"Error importing scheduler modules: {e}")
    logger.error("Make sure the package is installed or in your PYTHONPATH")
    sys.exit(1)

def format_docstring(docstring: str) -> str:
    """Format docstring for Markdown output.
    
    This function cleans up docstrings and formats them for Markdown rendering,
    handling Google-style and NumPy-style docstrings appropriately.
    
    Args:
        docstring: The raw docstring from the Python object
        
    Returns:
        A formatted Markdown string
    """
    if not docstring:
        return "*No documentation available.*"
    
    # Clean up the docstring
    lines = docstring.split('\n')
    
    # Remove indentation
    if len(lines) > 1:
        # Find the minimum indentation (excluding empty lines)
        min_indent = min(
            (len(line) - len(line.lstrip()) for line in lines[1:] if line.strip()),
            default=0
        )
        # Remove that amount of indentation from all lines
        lines = [lines[0]] + [line[min_indent:] if line.strip() else line for line in lines[1:]]
    
    # Process sections for Google-style docstrings
    result = []
    current_section = None
    section_content = []
    section_indent = 0
    
    for line in lines:
        # Check if this is a section header (Google style)
        section_match = re.match(r'^(\s*)(?:Args|Arguments|Parameters|Returns|Yields|Raises|Examples|Notes|Attributes|Warning|Warnings):(\s*)$', line)
        
        if section_match:
            # If we were in a section, add its content to the result
            if current_section:
                result.append(f"**{current_section}:**")
                
                # Format as a list if it's parameters
                if current_section in ["Args", "Arguments", "Parameters", "Raises"]:
                    param_list = []
                    current_param = None
                    param_desc = []
                    
                    for content_line in section_content:
                        # Check if this is a parameter definition
                        param_match = re.match(r'^\s*([a-zA-Z0-9_]+)(?:\s*\([a-zA-Z0-9_, ]+\))?\s*:\s*(.*)$', content_line)
                        if param_match:
                            # If we were describing a parameter, add it to the list
                            if current_param:
                                param_list.append(f"* **{current_param}**: {' '.join(param_desc)}")
                            
                            # Start a new parameter
                            current_param = param_match.group(1)
                            param_desc = [param_match.group(2).strip()]
                        elif current_param and content_line.strip():
                            # Continue the description of the current parameter
                            param_desc.append(content_line.strip())
                    
                    # Add the last parameter
                    if current_param:
                        param_list.append(f"* **{current_param}**: {' '.join(param_desc)}")
                    
                    result.extend(param_list)
                else:
                    # For other sections, just add the content
                    result.extend([f"  {line.strip()}" for line in section_content if line.strip()])
                
                result.append("")  # Add a blank line after the section
            
            # Start a new section
            current_section = section_match.group(0).strip().rstrip(':')
            section_content = []
            section_indent = len(section_match.group(1))
        elif current_section:
            # If we're in a section, add the line to the section content
            section_content.append(line)
        else:
            # If we're not in a section, add the line to the result
            if line.strip():
                result.append(line)
    
    # Add the last section if there is one
    if current_section:
        result.append(f"**{current_section}:**")
        
        # Format as a list if it's parameters
        if current_section in ["Args", "Arguments", "Parameters", "Raises"]:
            param_list = []
            current_param = None
            param_desc = []
            
            for content_line in section_content:
                # Check if this is a parameter definition
                param_match = re.match(r'^\s*([a-zA-Z0-9_]+)(?:\s*\([a-zA-Z0-9_, ]+\))?\s*:\s*(.*)$', content_line)
                if param_match:
                    # If we were describing a parameter, add it to the list
                    if current_param:
                        param_list.append(f"* **{current_param}**: {' '.join(param_desc)}")
                    
                    # Start a new parameter
                    current_param = param_match.group(1)
                    param_desc = [param_match.group(2).strip()]
                elif current_param and content_line.strip():
                    # Continue the description of the current parameter
                    param_desc.append(content_line.strip())
            
            # Add the last parameter
            if current_param:
                param_list.append(f"* **{current_param}**: {' '.join(param_desc)}")
            
            result.extend(param_list)
        else:
            # For other sections, just add the content
            result.extend([f"  {line.strip()}" for line in section_content if line.strip()])
    
    # Join the result into a single string
    return '\n'.join(result)

def format_type_annotation(annotation) -> str:
    """Format type annotation as a string.
    
    Converts Python type annotations to a more readable string format.
    Handles typing generics, Optional, Union, etc.
    
    Args:
        annotation: The type annotation to format
        
    Returns:
        A string representation of the type annotation
    """
    if annotation is inspect.Parameter.empty:
        return "Any"
    
    # Convert to string
    anno_str = str(annotation)
    
    # Clean up typing annotations
    anno_str = anno_str.replace('typing.', '')
    anno_str = anno_str.replace('NoneType', 'None')
    
    # Handle common typing generics
    anno_str = re.sub(r'Union\[(.*?), NoneType\]', r'Optional[\1]', anno_str)
    anno_str = re.sub(r'ForwardRef\(\'(.*?)\'\)', r'\1', anno_str)
    
    # Handle self-references with full module path
    anno_str = re.sub(r'scheduler\.([a-zA-Z0-9_\.]+)\.([a-zA-Z0-9_]+)', r'\2', anno_str)
    
    return anno_str

def get_class_methods(cls) -> List[Dict[str, Any]]:
    """Extract methods from a class."""
    methods = []
    
    # Get all methods including inherited ones
    for name, method in inspect.getmembers(cls, predicate=inspect.isfunction):
        # Skip private methods except __init__
        if name.startswith('_') and name != '__init__':
            continue
        
        docstring = inspect.getdoc(method) or "*No documentation available.*"
        signature = inspect.signature(method)
        
        # Format parameters
        formatted_params = []
        for param_name, param in signature.parameters.items():
            if param_name == 'self':
                continue
                
            param_type = format_type_annotation(param.annotation)
            default_value = "" if param.default is inspect.Parameter.empty else f" = {param.default}"
            
            formatted_params.append(f"{param_name}: {param_type}{default_value}")
        
        # Format return annotation
        return_annotation = format_type_annotation(signature.return_annotation)
        
        methods.append({
            'name': name,
            'params': formatted_params,
            'return_type': return_annotation,
            'docstring': format_docstring(docstring)
        })
    
    return sorted(methods, key=lambda m: (m['name'] != '__init__', m['name']))

def generate_class_doc(cls, filename: str) -> None:
    """Generate documentation for a class.
    
    Args:
        cls: The class to document
        filename: The filename to write the documentation to
    """
    class_name = cls.__name__
    module_name = cls.__module__
    class_doc = format_docstring(inspect.getdoc(cls) or "*No documentation available.*")
    methods = get_class_methods(cls)
    
    logger.info(f"Generating documentation for {module_name}.{class_name}")
    
    with open(os.path.join(OUTPUT_DIR, filename), 'w') as f:
        f.write(f"# {class_name}\n\n")
        
        # Module information
        f.write(f"*Defined in [`{module_name}`](https://github.com/aid2e/scheduler_epic/blob/main/{module_name.replace('.', '/')}.py)*\n\n")
        
        # Class description
        f.write(f"{class_doc}\n\n")
        
        # Class inheritance
        base_classes = cls.__bases__
        if base_classes and base_classes[0] != object:
            base_names = []
            for base in base_classes:
                if base.__module__.startswith('scheduler'):
                    base_names.append(f"[{base.__name__}]({base.__name__.lower()}.md)")
                else:
                    base_names.append(base.__name__)
            
            f.write(f"**Inherits from:** {', '.join(base_names)}\n\n")
        
        # Class definition
        f.write("## Class Definition\n\n")
        f.write("```python\n")
        
        # Get init method signature
        init_method = next((m for m in methods if m['name'] == '__init__'), None)
        if init_method:
            params_str = ", ".join(["self"] + init_method['params'])
            f.write(f"class {class_name}({params_str}):\n")
            # Add init docstring indented
            if init_method['docstring'] != "*No documentation available.*":
                docstring_lines = init_method['docstring'].split('\n')
                f.write(f"    \"\"\"\n")
                for line in docstring_lines:
                    f.write(f"    {line}\n")
                f.write(f"    \"\"\"\n")
            else:
                f.write(f"    # No documentation available for constructor\n")
        else:
            f.write(f"class {class_name}:\n")
            f.write(f"    # No constructor documentation available\n")
            
        f.write("```\n\n")
        
        # Create a Table of Contents for methods
        if len(methods) > 1:  # More than just __init__
            f.write("## Methods\n\n")
            f.write("| Method | Description |\n")
            f.write("|--------|-------------|\n")
            
            for method in methods:
                if method['name'] == '__init__':
                    continue
                
                # Get the first line of the docstring for the description
                description = method['docstring'].split('\n')[0]
                if description == "*No documentation available.*":
                    description = ""
                
                f.write(f"| [`{method['name']}`](#{method['name'].lower()}) | {description} |\n")
            
            f.write("\n")
        
        # Methods section with detailed documentation
        f.write("## Method Details\n\n")
        for method in methods:
            # Skip __init__ as it's already documented
            if method['name'] == '__init__':
                continue
                
            f.write(f"### {method['name']}\n\n")
            f.write("```python\n")
            
            params_str = ", ".join(["self"] + method['params'])
            f.write(f"def {method['name']}({params_str}) -> {method['return_type']}\n")
            f.write("```\n\n")
            
            # Add the docstring
            f.write(f"{method['docstring']}\n\n")
            
            # Add a separator between methods
            if method != methods[-1] and method['name'] != '__init__':
                f.write("---\n\n")
    
    logger.info(f"Documentation for {class_name} written to {filename}")
    
    # Return the path to the generated file
    return os.path.join(OUTPUT_DIR, filename)

def generate_module_overview(module_path: str, filename: str) -> None:
    """Generate overview documentation for a module."""
    module_name = os.path.basename(module_path).replace('.py', '')
    
    # Import the module
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    module_doc = format_docstring(inspect.getdoc(module) or "*No module documentation available.*")
    
    # Find all classes in the module
    classes = []
    for name, obj in inspect.getmembers(module):
        if inspect.isclass(obj) and obj.__module__ == module.__name__:
            classes.append(obj)
    
    with open(os.path.join(OUTPUT_DIR, filename), 'w') as f:
        f.write(f"# {module_name.capitalize()} Module\n\n")
        f.write(f"{module_doc}\n\n")
        
        if classes:
            f.write("## Classes\n\n")
            for cls in classes:
                cls_doc = format_docstring(inspect.getdoc(cls) or "*No documentation available.*")
                # Take just the first paragraph for the overview
                first_paragraph = cls_doc.split('\n\n')[0]
                f.write(f"### [{cls.__name__}]({cls.__name__.lower()}.md)\n\n")
                f.write(f"{first_paragraph}\n\n")

def generate_index_page():
    """Generate the API index page with links to all documented classes."""
    logger.info("Generating API index page")
    
    with open(os.path.join(OUTPUT_DIR, "index.md"), 'w') as f:
        f.write("# API Reference\n\n")
        f.write("This section provides detailed API documentation for the scheduler package.\n\n")
        
        # Add search box info
        f.write("> **Tip:** Use the search box in the top navigation bar to quickly find specific classes or methods.\n\n")
        
        # Core Components section
        f.write("## Core Components\n\n")
        
        # AxScheduler
        f.write("### [AxScheduler](ax_scheduler.md)\n\n")
        f.write("The main entry point for using the Scheduler library. It integrates with Ax for optimization and manages the execution of trials.\n\n")
        f.write("```python\n")
        f.write("# Example usage\n")
        f.write("from scheduler import AxScheduler, JobLibRunner\n")
        f.write("from ax.service.ax_client import AxClient\n\n")
        f.write("ax_client = AxClient()\n")
        f.write("# Set up parameters...\n\n")
        f.write("runner = JobLibRunner()\n")
        f.write("scheduler = AxScheduler(ax_client, runner)\n")
        f.write("scheduler.set_objective_function(my_objective_function)\n")
        f.write("best_params = scheduler.run_optimization(max_trials=10)\n")
        f.write("```\n\n")
        
        # Trial
        f.write("### [Trial](trial.md)\n\n")
        f.write("Represents a single optimization trial with parameters and jobs.\n\n")
        
        # Job
        f.write("### [Job](job.md)\n\n")
        f.write("Represents a single computational job that executes code with specific parameters.\n\n")
        
        # Runners section
        f.write("## Runners\n\n")
        f.write("Runners are responsible for executing jobs on different computing backends.\n\n")
        
        f.write("### [BaseRunner](base_runner.md)\n\n")
        f.write("The abstract base class that defines the interface for all runners.\n\n")
        
        f.write("### [JobLibRunner](joblib_runner.md)\n\n")
        f.write("Runner for local parallel execution using JobLib.\n\n")
        
        f.write("### [SlurmRunner](slurm_runner.md)\n\n")
        f.write("Runner for execution on Slurm clusters.\n\n")
        
        if has_panda:
            f.write("### [PandaRunner](panda_runner.md)\n\n")
            f.write("Runner for execution using PanDA distributed computing.\n\n")
        
        # Class Hierarchy section
        f.write("## Class Hierarchy\n\n")
        f.write("```\n")
        f.write("BaseRunner\n")
        f.write("├── JobLibRunner\n")
        f.write("├── SlurmRunner\n")
        if has_panda:
            f.write("└── PandaRunner\n")
        f.write("```\n\n")
        
        # Add a "How to Use This Documentation" section
        f.write("## How to Use This Documentation\n\n")
        f.write("Each class documentation page includes:\n\n")
        f.write("1. **Class Description** - Overview of the class's purpose\n")
        f.write("2. **Class Definition** - The constructor signature and parameters\n")
        f.write("3. **Methods Table** - Quick reference of all available methods\n")
        f.write("4. **Method Details** - Detailed documentation for each method\n\n")
        
        f.write("The documentation is automatically generated from docstrings in the source code.\n")
    
    logger.info("API index page generated successfully")

def main():
    """Main entry point for the script."""
    logger.info("Starting API documentation generation")
    
    # Create a list to track generated files
    generated_files = []
    
    try:
        # Generate documentation for core classes
        generated_files.append(generate_class_doc(AxScheduler, "ax_scheduler.md"))
        generated_files.append(generate_class_doc(Trial, "trial.md"))
        generated_files.append(generate_class_doc(Job, "job.md"))
        
        # Generate documentation for runner classes
        generated_files.append(generate_class_doc(BaseRunner, "base_runner.md"))
        generated_files.append(generate_class_doc(JobLibRunner, "joblib_runner.md"))
        generated_files.append(generate_class_doc(SlurmRunner, "slurm_runner.md"))
        if has_panda:
            generated_files.append(generate_class_doc(PandaRunner, "panda_runner.md"))
        
        # Generate index page
        generate_index_page()
        
        # Generate a combined markdown file for all runners
        generate_combined_doc(
            "runners.md",
            "Runners",
            "Runners are responsible for executing jobs on different computing backends.",
            [BaseRunner, JobLibRunner, SlurmRunner] + ([PandaRunner] if has_panda else [])
        )
        
        logger.info(f"API documentation generation complete")
        logger.info(f"Generated {len(generated_files)} documentation files")
        
        return 0
    except Exception as e:
        logger.error(f"Error generating API documentation: {e}", exc_info=True)
        return 1

def generate_combined_doc(filename, title, description, classes):
    """Generate a combined documentation file for multiple related classes.
    
    Args:
        filename: The filename to write to
        title: The title of the combined documentation
        description: The description of the combined documentation
        classes: A list of classes to include
    """
    logger.info(f"Generating combined documentation for {title}")
    
    with open(os.path.join(OUTPUT_DIR, filename), 'w') as f:
        f.write(f"# {title}\n\n")
        f.write(f"{description}\n\n")
        
        # Add links to individual class documentation
        f.write("## Classes\n\n")
        for cls in classes:
            class_name = cls.__name__
            class_doc = inspect.getdoc(cls) or "*No documentation available.*"
            first_line = class_doc.split('\n')[0]
            
            f.write(f"### [{class_name}]({class_name.lower()}.md)\n\n")
            f.write(f"{first_line}\n\n")
        
        # Add class inheritance diagram
        f.write("## Class Hierarchy\n\n")
        f.write("```\n")
        
        # Find the base class
        base_classes = [c for c in classes if not any(c.__bases__[0] in classes)]
        
        for base_class in base_classes:
            f.write(f"{base_class.__name__}\n")
            
            # Find direct subclasses
            subclasses = [c for c in classes if c.__bases__[0] == base_class]
            for i, subclass in enumerate(subclasses):
                prefix = "└── " if i == len(subclasses) - 1 else "├── "
                f.write(f"{prefix}{subclass.__name__}\n")
        
        f.write("```\n\n")
        
        # Add common usage examples if available
        f.write("## Usage Examples\n\n")
        
        f.write("```python\n")
        if title == "Runners":
            f.write("# Using JobLibRunner for local parallel execution\n")
            f.write("from scheduler import AxScheduler, JobLibRunner\n")
            f.write("from ax.service.ax_client import AxClient\n\n")
            f.write("runner = JobLibRunner(n_jobs=4)  # Use 4 parallel processes\n")
            f.write("scheduler = AxScheduler(ax_client, runner)\n\n")
            
            f.write("# Using SlurmRunner for cluster execution\n")
            f.write("from scheduler import SlurmRunner\n\n")
            f.write("runner = SlurmRunner(\n")
            f.write("    partition='compute',\n")
            f.write("    time='1:00:00',\n")
            f.write("    memory='4G'\n")
            f.write(")\n")
            f.write("scheduler = AxScheduler(ax_client, runner)\n")
        f.write("```\n\n")
    
    logger.info(f"Combined documentation written to {filename}")

if __name__ == "__main__":
    sys.exit(main())
