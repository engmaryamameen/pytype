"""
Tests for the CLI module.
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from pytype.cli import create_parser, validate_targets, load_config, main


class TestCLI:
    """Test cases for the CLI module."""
    
    def test_create_parser(self):
        """Test argument parser creation."""
        parser = create_parser()
        
        # Test that parser has expected arguments
        assert parser.prog == "pytype"
        assert "target" in parser.format_help()
        assert "--infer" in parser.format_help()
        assert "--fix" in parser.format_help()
        assert "--strict" in parser.format_help()
        assert "--format" in parser.format_help()
        assert "--config" in parser.format_help()
    
    def test_validate_targets_valid_files(self):
        """Test validation of valid target files."""
        with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as f:
            f.write(b"def test():\n    pass\n")
            file_path = f.name
        
        try:
            targets = validate_targets([file_path])
            assert len(targets) == 1
            assert targets[0] == Path(file_path)
        finally:
            Path(file_path).unlink()
    
    def test_validate_targets_valid_directories(self):
        """Test validation of valid target directories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            targets = validate_targets([temp_dir])
            assert len(targets) == 1
            assert targets[0] == Path(temp_dir)
    
    def test_validate_targets_nonexistent(self):
        """Test validation of nonexistent targets."""
        with pytest.raises(SystemExit):
            validate_targets(["nonexistent_file.py"])
    
    def test_validate_targets_non_python_file(self):
        """Test validation of non-Python files."""
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            f.write(b"not python code\n")
            file_path = f.name
        
        try:
            with pytest.raises(SystemExit):
                targets = validate_targets([file_path])
        finally:
            Path(file_path).unlink()
    
    def test_validate_targets_mixed(self):
        """Test validation of mixed valid and invalid targets."""
        with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as f:
            f.write(b"def test():\n    pass\n")
            file_path = f.name
        
        try:
            with pytest.raises(SystemExit):
                validate_targets([file_path, "nonexistent.py"])
        finally:
            Path(file_path).unlink()
    
    def test_load_config_with_file(self):
        """Test loading configuration from file."""
        config_content = """
[tool.pytype]
strict = true
infer = true
format = "json"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write(config_content)
            config_path = f.name
        
        try:
            config = load_config(config_path)
            assert config.strict is True
            assert config.infer is True
            assert config.format == "json"
        finally:
            Path(config_path).unlink()
    
    def test_load_config_without_file(self):
        """Test loading configuration without file."""
        config = load_config(None)
        assert isinstance(config, type(config))  # Should be Config instance
        assert config.strict is False  # Default value
    
    def test_load_config_invalid_file(self):
        """Test loading configuration from invalid file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write("invalid toml content")
            config_path = f.name
        
        try:
            config = load_config(config_path)
            # Should return default config on error
            assert config.strict is False
        finally:
            Path(config_path).unlink()
    
    @patch('pytype.cli.TypeChecker')
    @patch('pytype.cli.Reporter')
    def test_main_success(self, mock_reporter, mock_checker):
        """Test successful main execution."""
        # Create a temporary Python file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("def test():\n    pass\n")
            file_path = f.name
        
        try:
            # Mock the checker to return 0 errors
            mock_checker_instance = Mock()
            mock_checker_instance.check_file.return_value = 0
            mock_checker.return_value = mock_checker_instance
            
            # Mock the reporter
            mock_reporter_instance = Mock()
            mock_reporter.return_value = mock_reporter_instance
            
            # Test main function with proper sys.argv
            with patch('sys.argv', ['pytype', file_path]):
                result = main()
                assert result == 0
        finally:
            Path(file_path).unlink()
    
    @patch('pytype.cli.TypeChecker')
    @patch('pytype.cli.Reporter')
    def test_main_with_errors(self, mock_reporter, mock_checker):
        """Test main execution with type errors."""
        # Create a temporary Python file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("def test():\n    pass\n")
            file_path = f.name
        
        try:
            # Mock the checker to return 2 errors
            mock_checker_instance = Mock()
            mock_checker_instance.check_file.return_value = 2
            mock_checker.return_value = mock_checker_instance
            
            # Mock the reporter
            mock_reporter_instance = Mock()
            mock_reporter.return_value = mock_reporter_instance
            
            # Test main function with proper sys.argv
            with patch('sys.argv', ['pytype', file_path]):
                result = main()
                assert result == 1  # Should return 1 for errors
        finally:
            Path(file_path).unlink()
    
    @patch('pytype.cli.TypeChecker')
    @patch('pytype.cli.Reporter')
    def test_main_with_infer_option(self, mock_reporter, mock_checker):
        """Test main execution with --infer option."""
        # Create a temporary Python file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("def test():\n    pass\n")
            file_path = f.name
        
        try:
            # Mock the checker
            mock_checker_instance = Mock()
            mock_checker_instance.check_file.return_value = 0
            mock_checker.return_value = mock_checker_instance
            
            # Mock the reporter
            mock_reporter_instance = Mock()
            mock_reporter.return_value = mock_reporter_instance
            
            # Test main function with --infer
            with patch('sys.argv', ['pytype', '--infer', file_path]):
                result = main()
                assert result == 0
        finally:
            Path(file_path).unlink()
    
    @patch('pytype.cli.TypeChecker')
    @patch('pytype.cli.Reporter')
    def test_main_with_strict_option(self, mock_reporter, mock_checker):
        """Test main execution with --strict option."""
        # Create a temporary Python file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("def test():\n    pass\n")
            file_path = f.name
        
        try:
            # Mock the checker
            mock_checker_instance = Mock()
            mock_checker_instance.check_file.return_value = 0
            mock_checker.return_value = mock_checker_instance
            
            # Mock the reporter
            mock_reporter_instance = Mock()
            mock_reporter.return_value = mock_reporter_instance
            
            # Test main function with --strict
            with patch('sys.argv', ['pytype', '--strict', file_path]):
                result = main()
                assert result == 0
        finally:
            Path(file_path).unlink()
    
    def test_main_with_nonexistent_target(self):
        """Test main execution with nonexistent target."""
        with patch('sys.argv', ['pytype', 'nonexistent.py']):
            result = main()
            assert result == 1  # Should return 1 for error
    
    def test_main_keyboard_interrupt(self):
        """Test main execution with keyboard interrupt."""
        with patch('sys.argv', ['pytype', 'test.py']):
            with patch('pytype.cli.validate_targets', side_effect=KeyboardInterrupt):
                result = main()
                assert result == 130  # Should return 130 for keyboard interrupt
    
    def test_main_exception(self):
        """Test main execution with exception."""
        with patch('sys.argv', ['pytype', 'test.py']):
            with patch('pytype.cli.validate_targets', side_effect=Exception("Test error")):
                result = main()
                assert result == 1  # Should return 1 for error


class TestCLIIntegration:
    """Integration tests for CLI."""
    
    def test_cli_with_directory(self):
        """Test CLI with directory target."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a Python file in the directory
            py_file = Path(temp_dir) / "test.py"
            py_file.write_text("def test():\n    pass\n")
            
            with patch('sys.argv', ['pytype', temp_dir]):
                result = main()
                assert result == 0
    
    def test_cli_with_multiple_files(self):
        """Test CLI with multiple file targets."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f1:
            f1.write("def test1():\n    pass\n")
            file1 = f1.name
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f2:
            f2.write("def test2():\n    pass\n")
            file2 = f2.name
        
        try:
            with patch('sys.argv', ['pytype', file1, file2]):
                result = main()
                assert result == 0
        finally:
            Path(file1).unlink()
            Path(file2).unlink() 