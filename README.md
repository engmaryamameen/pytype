# PyType - Advanced Python Static Type Checker

A clean, modular, and extensible Python static type checker designed for modern Python development.

## 🚀 Features

- **Static Type Checking**: Parse and analyze `.py` files for type annotations
- **Type Inference**: Infer variable and return types using AST analysis
- **CLI Tool**: Easy-to-use command-line interface with rich options
- **Modular Architecture**: Clean separation of concerns with extensible design
- **Rich Error Reporting**: Colored CLI output and JSON export for CI/CD
- **Configuration Support**: TOML-based configuration files

## 📦 Installation

### From Source

```bash
git clone https://github.com/pytype/pytype.git
cd pytype
pip install -e .
```

### Development Installation

```bash
pip install -e ".[dev]"
```

## 🛠️ Usage

### Basic Usage

```bash
# Check a single file
pytype myfile.py

# Check a directory
pytype myproject/

# Show inferred types
pytype --infer myfile.py

# Auto-fix with inferred types
pytype --fix myfile.py

# Strict mode (treat missing types as errors)
pytype --strict myfile.py

# JSON output for CI/CD
pytype --format=json myfile.py

# Use custom config
pytype --config=pytype.toml myfile.py
```

### Configuration File

Create a `pytype.toml` file in your project root:

```toml
[tool.pytype]
strict = false
infer = true
fix = false
format = "text"
exclude = ["tests/", "migrations/"]
ignore_errors = ["E501", "F401"]
```

## 🏗️ Architecture

PyType follows a layered, modular architecture:

```
pytype/
├── cli.py          # Command-line interface and argument parsing
├── checker.py      # Core type checking logic
├── infer.py        # Type inference engine
├── analyzer.py     # AST parsing and analysis
├── config.py       # Configuration management
└── reporter.py     # Error reporting and output formatting
```

### Core Components

- **`checker.py`**: Handles type checking logic and validation
- **`infer.py`**: Performs type inference on unannotated code
- **`analyzer.py`**: AST parsing and semantic analysis
- **`reporter.py`**: Formats and outputs errors and warnings
- **`config.py`**: Manages configuration loading and validation

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=pytype

# Run specific test file
pytest tests/test_checker.py
```

## 🔧 Development

### Code Quality

This project uses several tools to maintain code quality:

- **Black**: Code formatting
- **Ruff**: Linting and import sorting
- **Pytest**: Testing framework
- **Coverage**: Test coverage reporting

### Pre-commit Setup

```bash
# Install pre-commit hooks
pre-commit install

# Run all hooks
pre-commit run --all-files
```

## 📝 Example Output

```
[ERROR] myfile.py:12: Expected int, got str in function 'add'
[WARNING] myfile.py:25: Missing return type annotation for function 'process_data'
[INFO] myfile.py:30: Inferred type: List[str] for variable 'items'
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Inspired by tools like `mypy`, `pyright`, and Google's pytype
- Built with modern Python best practices
- Designed for extensibility and maintainability 