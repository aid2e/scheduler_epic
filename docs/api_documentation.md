# Automatic API Documentation

This project includes tools to automatically generate API documentation from your Python source code.

## How It Works

The automatic API documentation generator:
1. Scans your Python modules and classes
2. Extracts docstrings, function signatures, and type annotations
3. Generates formatted Markdown files that integrate with MkDocs
4. Creates a consistent API reference structure

## Using the Generator

### Basic Usage

To generate API documentation:

```bash
# Using the helper script (recommended)
./api_docs_helper.sh generate

# Or run the generator directly
./docs_create/generate_api_docs.py
```

This will create or update Markdown files in the `docs/api/` directory.

### Complete API Documentation Workflow

Our API documentation helper script provides several commands:

```bash
# Generate API documentation
./api_docs_helper.sh generate

# Generate and preview in browser
./api_docs_helper.sh preview

# Generate, preview, and deploy to GitHub Pages
./api_docs_helper.sh deploy "Your commit message"

# Validate docstrings in the codebase
./api_docs_helper.sh validate

# Clean generated documentation files
./api_docs_helper.sh clean

# Show help
./api_docs_helper.sh help
```

## Writing Docstrings

For best results, use Google-style docstrings in your code:

### Functions and Methods

```python
def function_name(param1: str, param2: int = 10) -> bool:
    """Short description of the function.
    
    Longer description that explains what the function does.
    
    Args:
        param1: Description of param1
        param2: Description of param2, with default value
        
    Returns:
        Description of the return value
        
    Raises:
        ValueError: When something goes wrong
        
    Examples:
        >>> function_name("test", 5)
        True
        
        You can also include multi-line examples:
        >>> result = function_name("complex", 42)
        >>> print(result)
        True
    """
```

### Classes

```python
class MyClass:
    """Class description.
    
    More detailed description of the class and its behavior.
    
    Attributes:
        attribute1: Description of attribute1
        attribute2: Description of attribute2
    """
    
    def __init__(self, param1: str):
        """Initialize the class.
        
        Args:
            param1: Description of parameter
        """
```

### Type Annotations

Always include type annotations for parameters and return values:

```python
from typing import List, Dict, Optional, Union, Tuple

def complex_function(
    items: List[str],
    options: Dict[str, int],
    name: Optional[str] = None,
    mode: Union[str, int] = "default"
) -> Tuple[bool, List[str]]:
    """Function with complex type annotations.
    
    Args:
        items: List of items to process
        options: Dictionary of options
        name: Optional name parameter
        mode: Mode of operation, can be string or integer
        
    Returns:
        Tuple containing success flag and list of results
    """
```

## Integration with GitHub Actions

The API documentation generator is integrated with the GitHub Actions workflow. When you push changes to your repository, it will automatically:

1. Check out your code
2. Generate updated API documentation
3. Build the MkDocs site
4. Deploy to GitHub Pages

## Best Practices

1. **Write comprehensive docstrings** for all public classes, methods, and functions
2. **Include type annotations** for parameters and return values
3. **Use consistent docstring style** (Google style recommended)
4. **Regenerate documentation** when you make significant API changes
5. **Preview locally** before deploying to ensure everything looks correct
6. **Validate docstrings** regularly using `./api_docs_helper.sh validate`

## Docstring Style Guide

### Do's

✅ Include a brief one-line summary at the start of each docstring  
✅ Document all parameters with `Args:` section  
✅ Document return values with `Returns:` section  
✅ Document exceptions with `Raises:` section  
✅ Include examples where helpful  
✅ Use type annotations for all parameters and return values  

### Don'ts

❌ Leave public methods or classes without docstrings  
❌ Write overly terse docstrings that don't explain usage  
❌ Skip documenting parameters  
❌ Mix different docstring styles (stick to Google style)  

## Troubleshooting

### Missing or Incomplete Documentation

If some classes or methods are missing documentation:

1. Check that they have proper docstrings in the source code
2. Run `./api_docs_helper.sh validate` to find missing docstrings
3. Ensure the class or module is properly imported in the generator script

### Import Errors

If you see import errors when running the generator:

1. Make sure the package is installed or in your Python path
2. Check that all dependencies are installed
3. If adding new modules, update the imports in the generator script

### Formatting Issues

If the documentation doesn't look right:

1. Check your docstring format and make sure it follows Google style
2. Ensure proper indentation in your docstrings
3. Verify that type annotations are formatted correctly
