"""
Type inference engine for PyType.

This module handles automatic type inference for unannotated Python code.
"""

import ast
from typing import Dict, List, Optional, Set, Tuple, Union

from .config import Config


class TypeInferrer:
    """Performs type inference on Python code."""
    
    def __init__(self, config: Config):
        self.config = config
        self._type_map: Dict[str, str] = {}
        self._function_signatures: Dict[str, Dict[str, str]] = {}
        self._variable_types: Dict[str, str] = {}
    
    def infer_types(self, tree: ast.Module) -> Dict[str, any]:
        """Perform type inference on an AST."""
        self._type_map.clear()
        self._function_signatures.clear()
        self._variable_types.clear()
        
        # First pass: collect basic type information
        self._collect_basic_types(tree)
        
        # Second pass: infer function signatures
        self._infer_function_signatures(tree)
        
        # Third pass: infer variable types
        self._infer_variable_types(tree)
        
        return {
            'function_signatures': self._function_signatures,
            'variable_types': self._variable_types,
            'type_map': self._type_map,
        }
    
    def get_inferred_function_signature(self, func_name: str) -> Optional[Dict[str, str]]:
        """Get inferred signature for a specific function."""
        return self._function_signatures.get(func_name)
    
    def get_inferred_variable_type(self, var_name: str) -> Optional[str]:
        """Get inferred type for a specific variable."""
        return self._variable_types.get(var_name)
    
    def _collect_basic_types(self, tree: ast.Module):
        """Collect basic type information from the AST."""
        for node in ast.walk(tree):
            if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                # Already annotated variable
                type_name = self._get_type_name(node.annotation)
                if type_name:
                    self._variable_types[node.target.id] = type_name
            
            elif isinstance(node, ast.FunctionDef):
                # Function with return type annotation
                if node.returns:
                    return_type = self._get_type_name(node.returns)
                    if return_type:
                        self._function_signatures[node.name] = {'returns': return_type}
    
    def _infer_function_signatures(self, tree: ast.Module):
        """Infer function signatures by analyzing function bodies."""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                signature = self._infer_function_signature(node)
                if signature:
                    self._function_signatures[node.name] = signature
    
    def _infer_variable_types(self, tree: ast.Module):
        """Infer variable types by analyzing assignments."""
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        inferred_type = self._infer_expression_type(node.value)
                        if inferred_type:
                            self._variable_types[target.id] = inferred_type
    
    def _infer_function_signature(self, func: ast.FunctionDef) -> Optional[Dict[str, str]]:
        """Infer the signature of a function by analyzing its body."""
        signature = {}
        
        # Infer argument types from usage
        arg_types = self._infer_argument_types(func)
        if arg_types:
            signature['args'] = arg_types
        
        # Infer return type from return statements
        return_type = self._infer_return_type(func)
        if return_type:
            signature['returns'] = return_type
        
        return signature if signature else None
    
    def _infer_argument_types(self, func: ast.FunctionDef) -> Optional[Dict[str, str]]:
        """Infer argument types by analyzing function body."""
        arg_types = {}
        
        # Look for operations on arguments in the function body
        for node in ast.walk(func):
            if isinstance(node, ast.Call):
                # Check if this is a method call on an argument
                if isinstance(node.func, ast.Attribute):
                    if isinstance(node.func.value, ast.Name):
                        arg_name = node.func.value.id
                        if arg_name in [arg.arg for arg in func.args.args]:
                            # Try to infer type from method name
                            method_type = self._infer_type_from_method(node.func.attr)
                            if method_type:
                                arg_types[arg_name] = method_type
            
            elif isinstance(node, ast.BinOp):
                # Check if this is an operation on an argument
                if isinstance(node.left, ast.Name):
                    arg_name = node.left.id
                    if arg_name in [arg.arg for arg in func.args.args]:
                        op_type = self._infer_type_from_operation(node.op)
                        if op_type:
                            arg_types[arg_name] = op_type
        
        return arg_types if arg_types else None
    
    def _infer_return_type(self, func: ast.FunctionDef) -> Optional[str]:
        """Infer return type by analyzing return statements."""
        return_types = []
        
        for node in ast.walk(func):
            if isinstance(node, ast.Return):
                if node.value:
                    return_type = self._infer_expression_type(node.value)
                    if return_type:
                        return_types.append(return_type)
        
        if return_types:
            # If all return types are the same, use that
            if len(set(return_types)) == 1:
                return return_types[0]
            else:
                # Multiple different return types - use Union
                return f"Union[{', '.join(set(return_types))}]"
        
        return None
    
    def _infer_expression_type(self, node: ast.expr) -> Optional[str]:
        """Infer the type of an expression."""
        if isinstance(node, ast.Constant):
            return self._get_constant_type(node.value)
        elif isinstance(node, ast.Name):
            # Check if we already know the type of this variable
            return self._variable_types.get(node.id)
        elif isinstance(node, ast.List):
            return "List"
        elif isinstance(node, ast.Dict):
            return "Dict"
        elif isinstance(node, ast.Tuple):
            return "Tuple"
        elif isinstance(node, ast.Set):
            return "Set"
        elif isinstance(node, ast.Call):
            return self._infer_call_type(node)
        elif isinstance(node, ast.Attribute):
            return self._infer_attribute_type(node)
        elif isinstance(node, ast.BinOp):
            return self._infer_binop_type(node)
        elif isinstance(node, ast.UnaryOp):
            return self._infer_unaryop_type(node)
        
        return None
    
    def _get_constant_type(self, value) -> str:
        """Get the type of a constant value."""
        if isinstance(value, str):
            return "str"
        elif isinstance(value, bool):
            return "bool"
        elif isinstance(value, int):
            return "int"
        elif isinstance(value, float):
            return "float"
        elif value is None:
            return "None"
        else:
            return type(value).__name__
    
    def _infer_call_type(self, node: ast.Call) -> Optional[str]:
        """Infer the return type of a function call."""
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
            # Check if we have a signature for this function
            if func_name in self._function_signatures:
                return self._function_signatures[func_name].get('returns')
        
        return None
    
    def _infer_attribute_type(self, node: ast.Attribute) -> Optional[str]:
        """Infer the type of an attribute access."""
        # This is a simplified implementation
        # In a real implementation, you'd need to track object types
        return None
    
    def _infer_binop_type(self, node: ast.BinOp) -> Optional[str]:
        """Infer the type of a binary operation."""
        left_type = self._infer_expression_type(node.left)
        right_type = self._infer_expression_type(node.right)
        
        if isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div)):
            if left_type == "str" and right_type == "str":
                return "str"
            elif left_type in ("int", "float") and right_type in ("int", "float"):
                return "float" if "float" in (left_type, right_type) else "int"
        
        return left_type  # Default to left operand type
    
    def _infer_unaryop_type(self, node: ast.UnaryOp) -> Optional[str]:
        """Infer the type of a unary operation."""
        operand_type = self._infer_expression_type(node.operand)
        
        if isinstance(node.op, (ast.UAdd, ast.USub)):
            if operand_type in ("int", "float"):
                return operand_type
        
        return operand_type
    
    def _infer_type_from_method(self, method_name: str) -> Optional[str]:
        """Infer type from method name."""
        method_type_map = {
            'append': 'List',
            'extend': 'List',
            'insert': 'List',
            'remove': 'List',
            'pop': 'List',
            'clear': 'List',
            'index': 'List',
            'count': 'List',
            'sort': 'List',
            'reverse': 'List',
            'copy': 'List',
            'update': 'Dict',
            'get': 'Dict',
            'setdefault': 'Dict',
            'popitem': 'Dict',
            'keys': 'Dict',
            'values': 'Dict',
            'items': 'Dict',
            'add': 'Set',
            'remove': 'Set',
            'discard': 'Set',
            'pop': 'Set',
            'clear': 'Set',
            'union': 'Set',
            'intersection': 'Set',
            'difference': 'Set',
            'symmetric_difference': 'Set',
            'strip': 'str',
            'split': 'str',
            'join': 'str',
            'replace': 'str',
            'upper': 'str',
            'lower': 'str',
            'capitalize': 'str',
            'title': 'str',
        }
        
        return method_type_map.get(method_name)
    
    def _infer_type_from_operation(self, op: ast.operator) -> Optional[str]:
        """Infer type from operation."""
        if isinstance(op, (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod, ast.Pow)):
            return "int"  # Likely numeric operation
        elif isinstance(op, ast.MatMult):
            return "Any"  # Matrix multiplication
        elif isinstance(op, (ast.LShift, ast.RShift, ast.BitOr, ast.BitXor, ast.BitAnd)):
            return "int"  # Bitwise operations
        
        return None
    
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