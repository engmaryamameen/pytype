"""
AST analyzer for PyType.

This module handles parsing Python code into AST and provides utilities for AST walking.
"""

import ast
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union

from .config import Config


class ASTAnalyzer:
    """Analyzes Python code using AST parsing."""
    
    def __init__(self, config: Config):
        self.config = config
        self._imports: Dict[str, str] = {}
        self._functions: Dict[str, ast.FunctionDef] = {}
        self._classes: Dict[str, ast.ClassDef] = {}
        self._variables: Dict[str, ast.Assign] = {}
    
    def parse_file(self, file_path: Path) -> Optional[ast.Module]:
        """Parse a Python file into an AST."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()
            return ast.parse(source, filename=str(file_path))
        except SyntaxError as e:
            print(f"Syntax error in {file_path}: {e}", file=sys.stderr)
            return None
        except Exception as e:
            print(f"Error parsing {file_path}: {e}", file=sys.stderr)
            return None
    
    def analyze_ast(self, tree: ast.Module) -> Dict[str, any]:
        """Analyze AST and extract type-related information."""
        analyzer = _ASTWalker(self.config)
        analyzer.visit(tree)
        
        return {
            'imports': analyzer.imports,
            'functions': analyzer.functions,
            'classes': analyzer.classes,
            'variables': analyzer.variables,
            'type_annotations': analyzer.type_annotations,
            'missing_annotations': analyzer.missing_annotations,
        }
    
    def get_function_signatures(self, tree: ast.Module) -> List[Dict[str, any]]:
        """Extract function signatures with type information."""
        signatures = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                signature = {
                    'name': node.name,
                    'lineno': node.lineno,
                    'args': self._extract_function_args(node),
                    'returns': self._extract_return_type(node),
                    'has_return_annotation': node.returns is not None,
                }
                signatures.append(signature)
        
        return signatures
    
    def get_class_definitions(self, tree: ast.Module) -> List[Dict[str, any]]:
        """Extract class definitions with type information."""
        classes = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_info = {
                    'name': node.name,
                    'lineno': node.lineno,
                    'bases': [self._get_type_name(base) for base in node.bases],
                    'methods': self._extract_class_methods(node),
                    'attributes': self._extract_class_attributes(node),
                }
                classes.append(class_info)
        
        return classes
    
    def get_variable_assignments(self, tree: ast.Module) -> List[Dict[str, any]]:
        """Extract variable assignments with type information."""
        assignments = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        assignment = {
                            'name': target.id,
                            'lineno': node.lineno,
                            'has_annotation': hasattr(target, 'annotation') and target.annotation is not None,
                            'value_type': self._infer_value_type(node.value),
                        }
                        assignments.append(assignment)
        
        return assignments
    
    def _extract_function_args(self, func: ast.FunctionDef) -> List[Dict[str, any]]:
        """Extract function arguments with type information."""
        args = []
        
        for arg in func.args.args:
            arg_info = {
                'name': arg.arg,
                'has_annotation': arg.annotation is not None,
                'annotation': self._get_type_name(arg.annotation) if arg.annotation else None,
            }
            args.append(arg_info)
        
        return args
    
    def _extract_return_type(self, func: ast.FunctionDef) -> Optional[str]:
        """Extract function return type annotation."""
        if func.returns:
            return self._get_type_name(func.returns)
        return None
    
    def _extract_class_methods(self, cls: ast.ClassDef) -> List[Dict[str, any]]:
        """Extract class methods with type information."""
        methods = []
        
        for node in cls.body:
            if isinstance(node, ast.FunctionDef):
                method = {
                    'name': node.name,
                    'lineno': node.lineno,
                    'args': self._extract_function_args(node),
                    'returns': self._extract_return_type(node),
                    'has_return_annotation': node.returns is not None,
                }
                methods.append(method)
        
        return methods
    
    def _extract_class_attributes(self, cls: ast.ClassDef) -> List[Dict[str, any]]:
        """Extract class attributes with type information."""
        attributes = []
        
        for node in cls.body:
            if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                attr = {
                    'name': node.target.id,
                    'lineno': node.lineno,
                    'annotation': self._get_type_name(node.annotation),
                    'has_value': node.value is not None,
                }
                attributes.append(attr)
        
        return attributes
    
    def _get_type_name(self, node: Optional[ast.expr]) -> Optional[str]:
        """Extract type name from AST node."""
        if node is None:
            return None
        
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_type_name(node.value)}.{node.attr}"
        elif isinstance(node, ast.Subscript):
            base = self._get_type_name(node.value)
            slice_name = self._get_type_name(node.slice)
            return f"{base}[{slice_name}]"
        elif isinstance(node, ast.Constant):
            return str(node.value)
        
        return str(node)
    
    def _infer_value_type(self, node: ast.expr) -> Optional[str]:
        """Infer the type of a value expression."""
        if isinstance(node, ast.Constant):
            if isinstance(node.value, str):
                return "str"
            elif isinstance(node.value, int):
                return "int"
            elif isinstance(node.value, float):
                return "float"
            elif isinstance(node.value, bool):
                return "bool"
            elif node.value is None:
                return "None"
        elif isinstance(node, ast.List):
            return "List"
        elif isinstance(node, ast.Dict):
            return "Dict"
        elif isinstance(node, ast.Tuple):
            return "Tuple"
        elif isinstance(node, ast.Set):
            return "Set"
        elif isinstance(node, ast.Call):
            return self._get_type_name(node.func)
        
        return None


class _ASTWalker(ast.NodeVisitor):
    """Internal AST walker for collecting type information."""
    
    def __init__(self, config: Config):
        self.config = config
        self.imports: Dict[str, str] = {}
        self.functions: Dict[str, ast.FunctionDef] = {}
        self.classes: Dict[str, ast.ClassDef] = {}
        self.variables: Dict[str, ast.Assign] = {}
        self.type_annotations: Set[str] = set()
        self.missing_annotations: List[Tuple[str, int]] = []
    
    def visit_Import(self, node: ast.Import):
        """Visit import statements."""
        for alias in node.names:
            self.imports[alias.asname or alias.name] = alias.name
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Visit from-import statements."""
        module = node.module or ""
        for alias in node.names:
            self.imports[alias.asname or alias.name] = f"{module}.{alias.name}"
        self.generic_visit(node)
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Visit function definitions."""
        self.functions[node.name] = node
        
        # Check for missing return type annotation
        if self.config.strict and node.returns is None:
            self.missing_annotations.append((f"function '{node.name}'", node.lineno))
        
        # Check for missing argument type annotations
        for arg in node.args.args:
            if self.config.strict and arg.annotation is None:
                self.missing_annotations.append(
                    (f"parameter '{arg.arg}' in function '{node.name}'", node.lineno)
                )
        
        self.generic_visit(node)
    
    def visit_ClassDef(self, node: ast.ClassDef):
        """Visit class definitions."""
        self.classes[node.name] = node
        self.generic_visit(node)
    
    def visit_Assign(self, node: ast.Assign):
        """Visit assignment statements."""
        for target in node.targets:
            if isinstance(target, ast.Name):
                self.variables[target.id] = node
        self.generic_visit(node)
    
    def visit_AnnAssign(self, node: ast.AnnAssign):
        """Visit annotated assignment statements."""
        if isinstance(node.target, ast.Name):
            self.type_annotations.add(node.target.id)
        self.generic_visit(node) 