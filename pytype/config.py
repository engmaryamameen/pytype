"""
Configuration management for PyType.

This module handles loading and validation of configuration files.
"""

import sys
from pathlib import Path
from typing import List, Optional

try:
    import tomllib
except ImportError:
    import tomli as tomllib


class Config:
    """Configuration class for PyType settings."""
    
    def __init__(
        self,
        strict: bool = False,
        infer: bool = False,
        fix: bool = False,
        format: str = "text",
        exclude: Optional[List[str]] = None,
        ignore_errors: Optional[List[str]] = None,
        max_line_length: int = 88,
        python_version: str = "3.8",
    ):
        self.strict = strict
        self.infer = infer
        self.fix = fix
        self.format = format
        self.exclude = exclude or []
        self.ignore_errors = ignore_errors or []
        self.max_line_length = max_line_length
        self.python_version = python_version
    
    @classmethod
    def from_file(cls, config_path: Path) -> "Config":
        """Load configuration from a TOML file."""
        try:
            with open(config_path, "rb") as f:
                data = tomllib.load(f)
        except Exception as e:
            print(f"Error loading config file {config_path}: {e}", file=sys.stderr)
            return cls()
        
        # Extract pytype section
        pytype_config = data.get("tool", {}).get("pytype", {})
        
        return cls(
            strict=pytype_config.get("strict", False),
            infer=pytype_config.get("infer", False),
            fix=pytype_config.get("fix", False),
            format=pytype_config.get("format", "text"),
            exclude=pytype_config.get("exclude", []),
            ignore_errors=pytype_config.get("ignore_errors", []),
            max_line_length=pytype_config.get("max_line_length", 88),
            python_version=pytype_config.get("python_version", "3.8"),
        )
    
    @classmethod
    def default(cls) -> "Config":
        """Create a default configuration."""
        return cls()
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of errors."""
        errors = []
        
        if self.format not in ["text", "json"]:
            errors.append(f"Invalid format: {self.format}. Must be 'text' or 'json'")
        
        if self.max_line_length < 1:
            errors.append("max_line_length must be positive")
        
        # Validate Python version format
        try:
            major, minor = map(int, self.python_version.split(".")[:2])
            if major < 3 or (major == 3 and minor < 8):
                errors.append("Python version must be 3.8 or higher")
        except (ValueError, IndexError):
            errors.append(f"Invalid Python version format: {self.python_version}")
        
        return errors
    
    def to_dict(self) -> dict:
        """Convert configuration to dictionary."""
        return {
            "strict": self.strict,
            "infer": self.infer,
            "fix": self.fix,
            "format": self.format,
            "exclude": self.exclude,
            "ignore_errors": self.ignore_errors,
            "max_line_length": self.max_line_length,
            "python_version": self.python_version,
        }
    
    def __repr__(self) -> str:
        return f"Config({', '.join(f'{k}={v!r}' for k, v in self.to_dict().items())})" 