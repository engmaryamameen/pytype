"""
Core type checker for PyType.

This module contains the main TypeChecker class that orchestrates the type checking process.
"""

import ast
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from .analyzer import ASTAnalyzer
from .config import Config
from .infer import TypeInferrer
from .reporter import Reporter


class TypeChecker:
    """Main type checker class that orchestrates the type checking process."""
    
    def __init__(self, config: Config, reporter: Reporter):
        self.config = config
        self.reporter = reporter
        self.analyzer = ASTAnalyzer(config)
        self.inferrer = TypeInferrer(config)
        self.errors: List[Dict[str, any]] = []
        self.warnings: List[Dict[str, any]] = []
    
    def check_file(self, file_path: Path) -> int:
        """Check a single Python file for type errors."""
        self.errors.clear()
        self.warnings.clear()
        
        # Parse the file
        tree = self.analyzer.parse_file(file_path)
        if tree is None:
            return 1  # Error occurred during parsing
        
        # Analyze the AST
        analysis = self.analyzer.analyze_ast(tree)
        
        # Perform type inference if enabled
        if self.config.infer:
            inferred_types = self.inferrer.infer_types(tree)
            self._report_inferred_types(file_path, inferred_types)
        
        # Check for type errors
        self._check_function_signatures(file_path, tree)
        self._check_variable_assignments(file_path, tree)
        self._check_missing_annotations(file_path, analysis)
        self._check_type_mismatches(file_path, tree)
        
        # Report errors and warnings
        self._report_issues(file_path)
        
        # Auto-fix if enabled
        if self.config.fix:
            self._auto_fix_file(file_path, tree)
        
        return len(self.errors)
    
    def _check_function_signatures(self, file_path: Path, tree: ast.Module):
        """Check function signatures for type errors."""
        signatures = self.analyzer.get_function_signatures(tree)
        
        for sig in signatures:
            # Check for missing return type annotations in strict mode
            if self.config.strict and not sig['has_return_annotation']:
                self.errors.append({
                    'type': 'missing_return_type',
                    'message': f"Missing return type annotation for function '{sig['name']}'",
                    'line': sig['lineno'],
                    'file': str(file_path),
                })
            
            # Check for missing argument type annotations in strict mode
            for arg in sig['args']:
                if self.config.strict and not arg['has_annotation']:
                    self.warnings.append({
                        'type': 'missing_arg_type',
                        'message': f"Missing type annotation for parameter '{arg['name']}' in function '{sig['name']}'",
                        'line': sig['lineno'],
                        'file': str(file_path),
                    })
    
    def _check_variable_assignments(self, file_path: Path, tree: ast.Module):
        """Check variable assignments for type errors."""
        assignments = self.analyzer.get_variable_assignments(tree)
        
        for assignment in assignments:
            # Check for type mismatches if we have both annotation and value
            if assignment['has_annotation'] and assignment['value_type']:
                # This would require more sophisticated type checking
                # For now, we'll just note that we have both
                pass
    
    def _check_missing_annotations(self, file_path: Path, analysis: Dict[str, any]):
        """Check for missing type annotations."""
        missing_annotations = analysis.get('missing_annotations', [])
        
        for item, line in missing_annotations:
            if self.config.strict:
                self.errors.append({
                    'type': 'missing_annotation',
                    'message': f"Missing type annotation for {item}",
                    'line': line,
                    'file': str(file_path),
                })
            else:
                self.warnings.append({
                    'type': 'missing_annotation',
                    'message': f"Missing type annotation for {item}",
                    'line': line,
                    'file': str(file_path),
                })
    
    def _check_type_mismatches(self, file_path: Path, tree: ast.Module):
        """Check for type mismatches in function calls and assignments."""
        # This is a simplified implementation
        # A full implementation would need to track types throughout the code
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                self._check_function_call(file_path, node)
            elif isinstance(node, ast.Assign):
                self._check_assignment(file_path, node)
    
    def _check_function_call(self, file_path: Path, node: ast.Call):
        """Check a function call for type errors."""
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
            
            # Check if we have inferred signature for this function
            if self.config.infer:
                signature = self.inferrer.get_inferred_function_signature(func_name)
                if signature and 'args' in signature:
                    expected_args = signature['args']
                    actual_args = node.args
                    
                    if len(actual_args) != len(expected_args):
                        self.errors.append({
                            'type': 'argument_count_mismatch',
                            'message': f"Function '{func_name}' expects {len(expected_args)} arguments, got {len(actual_args)}",
                            'line': node.lineno,
                            'file': str(file_path),
                        })
    
    def _check_assignment(self, file_path: Path, node: ast.Assign):
        """Check an assignment for type errors."""
        # This is a placeholder for more sophisticated type checking
        # In a real implementation, you'd check if the assigned value
        # matches the expected type of the target variable
        pass
    
    def _report_inferred_types(self, file_path: Path, inferred_types: Dict[str, any]):
        """Report inferred types if inference is enabled."""
        function_signatures = inferred_types.get('function_signatures', {})
        variable_types = inferred_types.get('variable_types', {})
        
        if function_signatures:
            self.reporter.report_info(f"Inferred function signatures in {file_path.name}:")
            for func_name, signature in function_signatures.items():
                self.reporter.report_info(f"  {func_name}: {signature}")
        
        if variable_types:
            self.reporter.report_info(f"Inferred variable types in {file_path.name}:")
            for var_name, var_type in variable_types.items():
                self.reporter.report_info(f"  {var_name}: {var_type}")
    
    def _report_issues(self, file_path: Path):
        """Report all errors and warnings for a file."""
        for error in self.errors:
            self.reporter.report_error(
                file_path,
                error['line'],
                error['message'],
                error['type']
            )
        
        for warning in self.warnings:
            self.reporter.report_warning(
                file_path,
                warning['line'],
                warning['message'],
                warning['type']
            )
    
    def _auto_fix_file(self, file_path: Path, tree: ast.Module):
        """Automatically fix type annotations in a file."""
        if not self.config.fix:
            return
        
        # This is a placeholder for auto-fixing functionality
        # In a real implementation, you would:
        # 1. Parse the file
        # 2. Infer types for unannotated code
        # 3. Generate new AST with annotations
        # 4. Write the modified code back to the file
        
        self.reporter.report_info(f"Auto-fixing {file_path.name} (placeholder)")
    
    def get_error_count(self) -> int:
        """Get the total number of errors found."""
        return len(self.errors)
    
    def get_warning_count(self) -> int:
        """Get the total number of warnings found."""
        return len(self.warnings)
    
    def get_all_errors(self) -> List[Dict[str, any]]:
        """Get all errors found during checking."""
        return self.errors.copy()
    
    def get_all_warnings(self) -> List[Dict[str, any]]:
        """Get all warnings found during checking."""
        return self.warnings.copy() 