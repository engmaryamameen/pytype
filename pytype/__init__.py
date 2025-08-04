"""
PyType - Advanced Python Static Type Checker

A clean, modular, and extensible Python static type checker designed for modern Python development.
"""

__version__ = "0.1.0"
__author__ = "PyType Team"
__email__ = "team@pytype.dev"

from .checker import TypeChecker
from .infer import TypeInferrer
from .analyzer import ASTAnalyzer
from .reporter import Reporter
from .config import Config

__all__ = [
    "TypeChecker",
    "TypeInferrer", 
    "ASTAnalyzer",
    "Reporter",
    "Config",
    "__version__",
] 