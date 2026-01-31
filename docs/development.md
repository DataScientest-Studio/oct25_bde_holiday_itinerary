# Development

## Dependencies

- **[pre-commit](https://pre-commit.com/)** (`4.2.0`)\
  Git hooks framework used to enforce code quality checks before commits.
- **[Black](https://black.readthedocs.io/)** (`25.11.0`)\
  Opinionated Python code formatter.
- **[isort](https://pycqa.github.io/isort/)** (`7.0.0`)\
  Import sorting and organization tool.
- **[Flake8](https://flake8.pycqa.org/)** (`7.3.0`)\
  Linting tool for style, complexity, and error detection.
- **[MyPy](https://mypy-lang.org/)** (`1.18.2`)\
  Static type checker for Python.
- **[Pytest](https://docs.pytest.org/)** (`9.0.1`)\
  Testing framework for unit and integration tests.
- **[Requests](https://docs.python-requests.org/)** (`2.32.5`)\
  HTTP client used for integration and API testing.
- **[Matplotlib](https://matplotlib.org/)** (`3.10.8`)\
  Plotting library used for data visualization and analysis.
- **[Basemap](https://matplotlib.org/basemap/)** (`2.0.0`)\
  Geospatial plotting toolkit used for map-based visualizations.

## Pre-commit

The project uses **pre-commit** to automatically enforce code formatting,
linting, and basic consistency checks before commits are created.

It applies to Python source code and Markdown files and helps catch common
issues early, keeping the codebase consistent across frontend and backend.

## Poetry

The project uses **Poetry** for dependency management and virtual environment
isolation.

Poetry ensures consistent dependency versions across frontend, backend, and
development tooling, and is also used by pre-commit hooks to run tools inside
the correct virtual environment.

## GitHub Actions

GitHub Actions are used to automatically validate the project on every push and
pull request to the `master` branch.

- **Lint**: Runs all `pre-commit` hooks using Python 3.13 to enforce formatting
  and code quality.
- **Test**: Executes the test suite in a Docker-enabled environment via
  `make tests`.

## Logging

The project uses a shared logging setup based on **Loguru**, which is imported by
both the frontend and backend.

The logger provides consistent formatting and log levels across all components
and also intercepts Python’s standard `logging` module so that third-party
libraries and internal code use the same output.

Logging behavior can be configured via environment variables:

- **LOG_LEVEL** – Sets the minimum log level (compatible with standard Python
  logging levels).
- **LOG_HI** – Enables or disables colored and formatted console output.

All application code should use the shared `logger` instance instead of defining
custom logging configurations.
