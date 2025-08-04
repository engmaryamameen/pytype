"""
Tests for the TypeChecker module.
"""

import ast
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from pytype.checker import TypeChecker
from pytype.config import Config
from pytype.reporter import Reporter


class TestTypeChecker:
    """Test cases for the TypeChecker class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = Config()
        self.reporter = Reporter()
        self.checker = TypeChecker(self.config, self.reporter)
    
    def test_checker_initialization(self):
        """Test that TypeChecker initializes correctly."""
        assert self.checker.config == self.config
        assert self.checker.reporter == self.reporter
        assert self.checker.errors == []
        assert self.checker.warnings == []
    
    def test_check_file_with_valid_python(self):
        """Test checking a valid Python file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("def add(a: int, b: int) -> int:\n    return a + b\n")
            file_path = Path(f.name)
        
        try:
            errors = self.checker.check_file(file_path)
            assert errors == 0
        finally:
            file_path.unlink()
    
    def test_check_file_with_syntax_error(self):
        """Test checking a file with syntax errors."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("def add(a: int, b: int) -> int:\n    return a + b\n    invalid syntax\n")
            file_path = Path(f.name)
        
        try:
            errors = self.checker.check_file(file_path)
            assert errors == 1  # Should return 1 for parsing error
        finally:
            file_path.unlink()
    
    def test_check_file_with_missing_return_type_strict(self):
        """Test checking a file with missing return type in strict mode."""
        self.config.strict = True
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("def add(a: int, b: int):\n    return a + b\n")
            file_path = Path(f.name)
        
        try:
            errors = self.checker.check_file(file_path)
            assert errors >= 1  # Should have at least one error for missing return type
            assert len(self.checker.errors) >= 1
            assert any("Missing return type annotation" in error['message'] for error in self.checker.errors)
        finally:
            file_path.unlink()
    
    def test_check_file_with_missing_arg_type_strict(self):
        """Test checking a file with missing argument type in strict mode."""
        self.config.strict = True
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("def add(a, b: int) -> int:\n    return a + b\n")
            file_path = Path(f.name)
        
        try:
            errors = self.checker.check_file(file_path)
            assert errors >= 0  # Missing arg types can be errors or warnings in strict mode
            assert len(self.checker.warnings) >= 1
            assert any("Missing type annotation for parameter" in warning['message'] for warning in self.checker.warnings)
        finally:
            file_path.unlink()
    
    def test_check_file_with_type_inference(self):
        """Test checking a file with type inference enabled."""
        self.config.infer = True
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("def add(a, b):\n    return a + b\n\nx = 42\ny = 'hello'\n")
            file_path = Path(f.name)
        
        try:
            errors = self.checker.check_file(file_path)
            assert errors == 0
            # Should have inferred types reported
            assert len(self.checker.reporter.info_messages) > 0
        finally:
            file_path.unlink()
    
    def test_get_error_count(self):
        """Test getting error count."""
        assert self.checker.get_error_count() == 0
        
        # Add a mock error
        self.checker.errors.append({'type': 'test_error', 'message': 'test'})
        assert self.checker.get_error_count() == 1
    
    def test_get_warning_count(self):
        """Test getting warning count."""
        assert self.checker.get_warning_count() == 0
        
        # Add a mock warning
        self.checker.warnings.append({'type': 'test_warning', 'message': 'test'})
        assert self.checker.get_warning_count() == 1
    
    def test_get_all_errors(self):
        """Test getting all errors."""
        assert self.checker.get_all_errors() == []
        
        # Add a mock error
        error = {'type': 'test_error', 'message': 'test'}
        self.checker.errors.append(error)
        assert self.checker.get_all_errors() == [error]
    
    def test_get_all_warnings(self):
        """Test getting all warnings."""
        assert self.checker.get_all_warnings() == []
        
        # Add a mock warning
        warning = {'type': 'test_warning', 'message': 'test'}
        self.checker.warnings.append(warning)
        assert self.checker.get_all_warnings() == [warning]
    
    @patch('pytype.checker.ASTAnalyzer.parse_file')
    def test_check_file_parsing_error(self, mock_parse):
        """Test handling of parsing errors."""
        mock_parse.return_value = None
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("def test():\n    pass\n")
            file_path = Path(f.name)
        
        try:
            errors = self.checker.check_file(file_path)
            assert errors == 1
        finally:
            file_path.unlink()
    
    def test_auto_fix_placeholder(self):
        """Test that auto-fix is a placeholder."""
        self.config.fix = True
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("def add(a, b):\n    return a + b\n")
            file_path = Path(f.name)
        
        try:
            # Should not raise an exception
            self.checker.check_file(file_path)
        finally:
            file_path.unlink()


class TestTypeCheckerIntegration:
    """Integration tests for TypeChecker."""
    
    def test_complex_file_analysis(self):
        """Test analysis of a complex Python file."""
        config = Config(strict=True, infer=True)
        reporter = Reporter(verbose=True)
        checker = TypeChecker(config, reporter)
        
        code = """
from typing import List, Dict, Optional

class Calculator:
    def __init__(self, name: str):
        self.name = name
        self.history = []
    
    def add(self, a: int, b: int) -> int:
        result = a + b
        self.history.append(result)
        return result
    
    def get_history(self) -> List[int]:
        return self.history

def process_data(data: List[str]) -> Dict[str, int]:
    result = {}
    for item in data:
        result[item] = len(item)
    return result

def main():
    calc = Calculator("test")
    numbers = [1, 2, 3, 4, 5]
    total = sum(numbers)
    return total
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            file_path = Path(f.name)
        
        try:
            errors = checker.check_file(file_path)
            # Should have errors for missing return type in main()
            assert errors >= 1
            assert len(checker.errors) >= 1
            assert any("main" in error['message'] for error in checker.errors)
        finally:
            file_path.unlink() 