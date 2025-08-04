"""
Command-line interface for PyType.

This module provides the main CLI entry point and argument parsing functionality.
"""

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from .checker import TypeChecker
from .config import Config
from .reporter import Reporter


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        prog="pytype",
        description="Advanced Python static type checker",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  pytype myfile.py                    # Check a single file
  pytype myproject/                   # Check a directory
  pytype --infer myfile.py           # Show inferred types
  pytype --fix myfile.py             # Auto-fix with inferred types
  pytype --strict myfile.py          # Strict mode
  pytype --format=json myfile.py     # JSON output
        """,
    )

    # Positional arguments
    parser.add_argument(
        "target",
        nargs="+",
        help="Python files or directories to check",
    )

    # Core options
    parser.add_argument(
        "--infer",
        action="store_true",
        help="Show inferred types for unannotated code",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Automatically insert inferred types into code",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat missing type annotations as errors",
    )

    # Output options
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress non-error output",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output",
    )

    # Configuration
    parser.add_argument(
        "--config",
        type=str,
        help="Path to configuration file (default: pytype.toml)",
    )

    # Advanced options
    parser.add_argument(
        "--exclude",
        nargs="+",
        help="Patterns to exclude from checking",
    )
    parser.add_argument(
        "--ignore-errors",
        nargs="+",
        help="Error codes to ignore",
    )

    return parser


def validate_targets(targets: List[str]) -> List[Path]:
    """Validate and convert target paths to Path objects."""
    valid_targets = []
    
    for target in targets:
        path = Path(target)
        if not path.exists():
            print(f"Error: Target '{target}' does not exist", file=sys.stderr)
            sys.exit(1)
        
        if path.is_file() and path.suffix != ".py":
            print(f"Warning: Skipping non-Python file '{target}'", file=sys.stderr)
            continue
            
        valid_targets.append(path)
    
    if not valid_targets:
        print("Error: No valid Python files or directories to check", file=sys.stderr)
        sys.exit(1)
    
    return valid_targets


def load_config(config_path: Optional[str]) -> Config:
    """Load configuration from file or use defaults."""
    if config_path:
        config_file = Path(config_path)
    else:
        config_file = Path("pytype.toml")
    
    if config_file.exists():
        return Config.from_file(config_file)
    else:
        return Config()


def main() -> int:
    """Main entry point for the pytype command."""
    parser = create_parser()
    args = parser.parse_args()
    
    try:
        # Validate targets
        targets = validate_targets(args.target)
        
        # Load configuration
        config = load_config(args.config)
        
        # Override config with command line arguments
        if args.infer:
            config.infer = True
        if args.fix:
            config.fix = True
        if args.strict:
            config.strict = True
        if args.format:
            config.format = args.format
        if args.exclude:
            config.exclude.extend(args.exclude)
        if args.ignore_errors:
            config.ignore_errors.extend(args.ignore_errors)
        
        # Initialize components
        reporter = Reporter(format=config.format, quiet=args.quiet, verbose=args.verbose)
        checker = TypeChecker(config=config, reporter=reporter)
        
        # Process targets
        total_errors = 0
        total_files = 0
        
        for target in targets:
            if target.is_file():
                errors = checker.check_file(target)
                total_errors += errors
                total_files += 1
            else:
                # Directory
                for py_file in target.rglob("*.py"):
                    # Skip excluded patterns
                    if any(pattern in str(py_file) for pattern in config.exclude):
                        continue
                    
                    errors = checker.check_file(py_file)
                    total_errors += errors
                    total_files += 1
        
        # Print summary
        if not args.quiet:
            print(f"\nChecked {total_files} file(s)")
            if total_errors == 0:
                print("✅ No type errors found!")
            else:
                print(f"❌ Found {total_errors} type error(s)")
        
        return 0 if total_errors == 0 else 1
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main()) 