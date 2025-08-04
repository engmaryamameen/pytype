"""
Error reporting and output formatting for PyType.

This module handles formatting and output of errors, warnings, and other messages.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Optional

try:
    import colorama
    from colorama import Fore, Back, Style
    colorama.init()
    HAS_COLORAMA = True
except ImportError:
    HAS_COLORAMA = False


class Reporter:
    """Handles reporting of errors, warnings, and other messages."""
    
    def __init__(self, format: str = "text", quiet: bool = False, verbose: bool = False):
        self.format = format
        self.quiet = quiet
        self.verbose = verbose
        self.errors: List[Dict[str, any]] = []
        self.warnings: List[Dict[str, any]] = []
        self.info_messages: List[str] = []
    
    def report_error(self, file_path: Path, line: int, message: str, error_type: str):
        """Report a type error."""
        error = {
            'file': str(file_path),
            'line': line,
            'message': message,
            'type': error_type,
            'severity': 'error',
        }
        
        self.errors.append(error)
        
        if not self.quiet:
            if self.format == "json":
                print(json.dumps(error))
            else:
                self._print_error(file_path, line, message, error_type)
    
    def report_warning(self, file_path: Path, line: int, message: str, warning_type: str):
        """Report a type warning."""
        warning = {
            'file': str(file_path),
            'line': line,
            'message': message,
            'type': warning_type,
            'severity': 'warning',
        }
        
        self.warnings.append(warning)
        
        if not self.quiet:
            if self.format == "json":
                print(json.dumps(warning))
            else:
                self._print_warning(file_path, line, message, warning_type)
    
    def report_info(self, message: str):
        """Report an informational message."""
        self.info_messages.append(message)
        
        if not self.quiet and self.verbose:
            if self.format == "json":
                print(json.dumps({'message': message, 'severity': 'info'}))
            else:
                self._print_info(message)
    
    def _print_error(self, file_path: Path, line: int, message: str, error_type: str):
        """Print an error message in text format."""
        if HAS_COLORAMA:
            prefix = f"{Fore.RED}[ERROR]{Style.RESET_ALL}"
            file_part = f"{Fore.CYAN}{file_path}{Style.RESET_ALL}"
            line_part = f"{Fore.YELLOW}{line}{Style.RESET_ALL}"
        else:
            prefix = "[ERROR]"
            file_part = str(file_path)
            line_part = str(line)
        
        print(f"{prefix} {file_part}:{line_part}: {message}")
    
    def _print_warning(self, file_path: Path, line: int, message: str, warning_type: str):
        """Print a warning message in text format."""
        if HAS_COLORAMA:
            prefix = f"{Fore.YELLOW}[WARNING]{Style.RESET_ALL}"
            file_part = f"{Fore.CYAN}{file_path}{Style.RESET_ALL}"
            line_part = f"{Fore.YELLOW}{line}{Style.RESET_ALL}"
        else:
            prefix = "[WARNING]"
            file_part = str(file_path)
            line_part = str(line)
        
        print(f"{prefix} {file_part}:{line_part}: {message}")
    
    def _print_info(self, message: str):
        """Print an informational message in text format."""
        if HAS_COLORAMA:
            prefix = f"{Fore.BLUE}[INFO]{Style.RESET_ALL}"
        else:
            prefix = "[INFO]"
        
        print(f"{prefix} {message}")
    
    def print_summary(self, total_files: int, total_errors: int, total_warnings: int):
        """Print a summary of the checking results."""
        if self.quiet:
            return
        
        if self.format == "json":
            summary = {
                'summary': {
                    'files_checked': total_files,
                    'errors': total_errors,
                    'warnings': total_warnings,
                }
            }
            print(json.dumps(summary))
        else:
            print(f"\nChecked {total_files} file(s)")
            if total_errors == 0 and total_warnings == 0:
                if HAS_COLORAMA:
                    print(f"{Fore.GREEN}✅ No type errors found!{Style.RESET_ALL}")
                else:
                    print("✅ No type errors found!")
            else:
                if total_errors > 0:
                    if HAS_COLORAMA:
                        print(f"{Fore.RED}❌ Found {total_errors} type error(s){Style.RESET_ALL}")
                    else:
                        print(f"❌ Found {total_errors} type error(s)")
                
                if total_warnings > 0:
                    if HAS_COLORAMA:
                        print(f"{Fore.YELLOW}⚠️  Found {total_warnings} warning(s){Style.RESET_ALL}")
                    else:
                        print(f"⚠️  Found {total_warnings} warning(s)")
    
    def get_all_issues(self) -> Dict[str, List[Dict[str, any]]]:
        """Get all reported issues as a dictionary."""
        return {
            'errors': self.errors,
            'warnings': self.warnings,
            'info': [{'message': msg} for msg in self.info_messages],
        }
    
    def export_json(self, output_file: Optional[Path] = None) -> str:
        """Export all issues as JSON."""
        issues = self.get_all_issues()
        json_str = json.dumps(issues, indent=2)
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(json_str)
        
        return json_str
    
    def print_code_context(self, file_path: Path, line: int, context_lines: int = 3):
        """Print code context around a specific line."""
        try:
            with open(file_path, 'r') as f:
                lines = f.readlines()
            
            start_line = max(1, line - context_lines)
            end_line = min(len(lines), line + context_lines + 1)
            
            print(f"\nContext for {file_path}:{line}:")
            print("-" * 50)
            
            for i in range(start_line, end_line):
                if i == line:
                    if HAS_COLORAMA:
                        print(f"{Fore.RED}{i:4d} >>> {lines[i-1].rstrip()}{Style.RESET_ALL}")
                    else:
                        print(f"{i:4d} >>> {lines[i-1].rstrip()}")
                else:
                    print(f"{i:4d}     {lines[i-1].rstrip()}")
            
            print("-" * 50)
            
        except Exception as e:
            print(f"Could not show context: {e}")
    
    def format_error_message(self, error_type: str, details: Dict[str, any]) -> str:
        """Format an error message based on its type."""
        if error_type == "missing_return_type":
            return f"Missing return type annotation for function '{details.get('function_name', 'unknown')}'"
        elif error_type == "missing_arg_type":
            return f"Missing type annotation for parameter '{details.get('param_name', 'unknown')}' in function '{details.get('function_name', 'unknown')}'"
        elif error_type == "type_mismatch":
            expected = details.get('expected_type', 'unknown')
            actual = details.get('actual_type', 'unknown')
            return f"Expected {expected}, got {actual}"
        elif error_type == "argument_count_mismatch":
            expected = details.get('expected_count', 0)
            actual = details.get('actual_count', 0)
            return f"Function expects {expected} arguments, got {actual}"
        else:
            return details.get('message', 'Unknown error') 