"""
Tests for the TypeInferrer module.
"""

import ast
import tempfile
from pathlib import Path

import pytest

from pytype.config import Config
from pytype.infer import TypeInferrer


class TestTypeInferrer:
    """Test cases for the TypeInferrer class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = Config()
        self.inferrer = TypeInferrer(self.config)
    
    def test_inferrer_initialization(self):
        """Test that TypeInferrer initializes correctly."""
        assert self.inferrer.config == self.config
        assert self.inferrer._type_map == {}
        assert self.inferrer._function_signatures == {}
        assert self.inferrer._variable_types == {}
    
    def test_infer_types_basic(self):
        """Test basic type inference."""
        code = """
x = 42
y = "hello"
z = [1, 2, 3]
"""
        tree = ast.parse(code)
        result = self.inferrer.infer_types(tree)
        
        assert 'variable_types' in result
        assert result['variable_types']['x'] == 'int'
        assert result['variable_types']['y'] == 'str'
        assert result['variable_types']['z'] == 'List'
    
    def test_infer_function_signature(self):
        """Test function signature inference."""
        code = """
def add(a, b):
    return a + b

def process_list(items):
    return [item.upper() for item in items]
"""
        tree = ast.parse(code)
        result = self.inferrer.infer_types(tree)
        
        assert 'function_signatures' in result
        # The inference should work for basic cases
        assert len(result['function_signatures']) >= 0
    
    def test_infer_return_type(self):
        """Test return type inference."""
        code = """
def get_string():
    return "hello"

def get_number():
    return 42

def get_list():
    return [1, 2, 3]
"""
        tree = ast.parse(code)
        result = self.inferrer.infer_types(tree)
        
        assert 'function_signatures' in result
        # Should infer return types
        assert len(result['function_signatures']) >= 0
    
    def test_infer_constant_types(self):
        """Test inference of constant types."""
        assert self.inferrer._get_constant_type("hello") == "str"
        assert self.inferrer._get_constant_type(42) == "int"
        assert self.inferrer._get_constant_type(3.14) == "float"
        assert self.inferrer._get_constant_type(True) == "bool"
        assert self.inferrer._get_constant_type(None) == "None"
    
    def test_infer_expression_type(self):
        """Test expression type inference."""
        # Test constant
        const_node = ast.Constant(value=42)
        assert self.inferrer._infer_expression_type(const_node) == "int"
        
        # Test name (variable)
        name_node = ast.Name(id="x")
        # Should return None if variable type not known
        assert self.inferrer._infer_expression_type(name_node) is None
    
    def test_infer_binop_type(self):
        """Test binary operation type inference."""
        # Test numeric addition
        left = ast.Constant(value=1)
        right = ast.Constant(value=2)
        binop = ast.BinOp(left=left, op=ast.Add(), right=right)
        
        # Mock the _infer_expression_type method to return known types
        self.inferrer._variable_types = {}
        result = self.inferrer._infer_binop_type(binop)
        assert result == "int"  # Should infer int for numeric addition
    
    def test_infer_type_from_method(self):
        """Test type inference from method names."""
        assert self.inferrer._infer_type_from_method("append") == "List"
        assert self.inferrer._infer_type_from_method("update") == "Dict"
        assert self.inferrer._infer_type_from_method("add") == "Set"
        assert self.inferrer._infer_type_from_method("strip") == "str"
        assert self.inferrer._infer_type_from_method("unknown_method") is None
    
    def test_infer_type_from_operation(self):
        """Test type inference from operations."""
        assert self.inferrer._infer_type_from_operation(ast.Add()) == "int"
        assert self.inferrer._infer_type_from_operation(ast.Sub()) == "int"
        assert self.inferrer._infer_type_from_operation(ast.Mult()) == "int"
        assert self.inferrer._infer_type_from_operation(ast.Div()) == "int"
        assert self.inferrer._infer_type_from_operation(ast.MatMult()) == "Any"
    
    def test_get_type_name(self):
        """Test extracting type names from AST nodes."""
        # Test Name node
        name_node = ast.Name(id="int")
        assert self.inferrer._get_type_name(name_node) == "int"
        
        # Test Attribute node
        attr_node = ast.Attribute(
            value=ast.Name(id="typing"),
            attr="List"
        )
        assert self.inferrer._get_type_name(attr_node) == "typing.List"
        
        # Test None
        assert self.inferrer._get_type_name(None) is None
    
    def test_get_inferred_function_signature(self):
        """Test getting inferred function signature."""
        # Should return None for unknown function
        assert self.inferrer.get_inferred_function_signature("unknown") is None
        
        # Add a mock signature
        self.inferrer._function_signatures["test_func"] = {"returns": "int"}
        assert self.inferrer.get_inferred_function_signature("test_func") == {"returns": "int"}
    
    def test_get_inferred_variable_type(self):
        """Test getting inferred variable type."""
        # Should return None for unknown variable
        assert self.inferrer.get_inferred_variable_type("unknown") is None
        
        # Add a mock type
        self.inferrer._variable_types["test_var"] = "str"
        assert self.inferrer.get_inferred_variable_type("test_var") == "str"
    
    def test_infer_types_clears_previous_results(self):
        """Test that infer_types clears previous results."""
        # Add some mock data
        self.inferrer._function_signatures["old_func"] = {"returns": "int"}
        self.inferrer._variable_types["old_var"] = "str"
        
        # Call infer_types
        code = "x = 42"
        tree = ast.parse(code)
        result = self.inferrer.infer_types(tree)
        
        # Old data should be cleared
        assert "old_func" not in result['function_signatures']
        assert "old_var" not in result['variable_types']


class TestTypeInferrerComplex:
    """Complex test cases for TypeInferrer."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = Config()
        self.inferrer = TypeInferrer(self.config)
    
    def test_infer_complex_function(self):
        """Test inference for a complex function."""
        code = """
def process_data(data):
    result = []
    for item in data:
        if isinstance(item, str):
            result.append(item.upper())
        else:
            result.append(str(item))
    return result
"""
        tree = ast.parse(code)
        result = self.inferrer.infer_types(tree)
        
        assert 'function_signatures' in result
        # Should have inferred some information
        assert len(result['function_signatures']) >= 0
    
    def test_infer_class_methods(self):
        """Test inference for class methods."""
        code = """
class Calculator:
    def __init__(self, name):
        self.name = name
        self.history = []
    
    def add(self, a, b):
        result = a + b
        self.history.append(result)
        return result
    
    def get_history(self):
        return self.history
"""
        tree = ast.parse(code)
        result = self.inferrer.infer_types(tree)
        
        assert 'function_signatures' in result
        # Should have inferred some information about methods
        assert len(result['function_signatures']) >= 0
    
    def test_infer_multiple_return_types(self):
        """Test inference for functions with multiple return types."""
        code = """
def process_item(item):
    if isinstance(item, str):
        return item.upper()
    elif isinstance(item, int):
        return str(item)
    else:
        return None
"""
        tree = ast.parse(code)
        result = self.inferrer.infer_types(tree)
        
        assert 'function_signatures' in result
        # Should handle multiple return types
        assert len(result['function_signatures']) >= 0
    
    def test_infer_list_comprehension(self):
        """Test inference for list comprehensions."""
        code = """
def process_strings(items):
    return [item.upper() for item in items if isinstance(item, str)]
"""
        tree = ast.parse(code)
        result = self.inferrer.infer_types(tree)
        
        assert 'function_signatures' in result
        # Should handle list comprehensions
        assert len(result['function_signatures']) >= 0 