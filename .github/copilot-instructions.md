# Project Guidelines for GitHub Copilot

## Project Overview
This project is a Python library for accessing Lidarr servers using the Lidarr API. It provides a comprehensive client with built-in retry logic, rate limiting, configuration persistence, and both programmatic and CLI interfaces.

## Architecture
- **`LidarrClient`** (`lidarr_api/client.py`): Main API client with automatic retries, rate limiting (default 2.0 req/sec), and comprehensive error handling
- **`Config`** (`lidarr_api/config.py`): Persistent configuration management storing defaults in `~/.config/lidarr-api/defaults.json`
- **CLI Interface** (`bin/lidarr_search.py`): Interactive command-line tool with artist search and management features

## Code Style and Conventions
- **Language:** Python 3.8+
- **Formatting:** Adhere to PEP 8 standards. Use Black for automatic formatting.
- **Type Hinting:** All functions and methods should include type hints for parameters and return values.
- **Docstrings:** Use Google-style docstrings for all public functions, classes, and methods.
- **Naming Conventions:** Follow standard Python naming conventions (e.g., `snake_case` for functions/variables, `PascalCase` for classes).

## Testing
- **Unit Tests:** All core functionality requires comprehensive unit tests using `pytest`.
- **Test Coverage:** Aim for high test coverage for critical components.
- **Mocking:** Use `unittest.mock` for mocking external dependencies in tests.
- **Test Strategy:** Dual approach with mocked unit tests using `responses` library and integration tests marked with `@pytest.mark.integration`

## Dependency Management
- **Dependencies:** Manage dependencies using `pyproject.toml` and Poetry
- **Virtual Environments:** Always work within a virtual environment. Use `poetry shell` or `venv`

## Development Workflow
- **Install Dependencies:** `poetry install` (includes dev dependencies)
- **Run Unit Tests:** `poetry run pytest -m "not integration"` (uses mocked responses)
- **Run Integration Tests:** `poetry run pytest -m integration` (requires live Lidarr instance)
- **Add New Dependencies:** `poetry add <package>` or `poetry add --group dev <package>` for dev dependencies

## Project-Specific Patterns
- **Rate Limiting:** Client enforces configurable rate limiting (default 2.0 requests/second) to prevent server overload
- **Retry Logic:** Built-in exponential backoff retry mechanism with configurable attempts and backoff factors
- **Configuration Persistence:** Use `Config` class to save/load connection settings and artist defaults to JSON files
- **Entry Points:** Console script `lidarr-search` provides CLI access via `pyproject.toml` poetry scripts
- **Test Configuration:** Keep sensitive data (API keys, URLs) in `tests/config.py` - ensure this file is excluded from version control

## Security Considerations
- **Vulnerabilities:** Be mindful of common security vulnerabilities (e.g., SQL injection, XSS) and write secure code.
- **Sensitive Data:** Handle sensitive data securely and avoid hardcoding credentials. Use configuration files excluded from version control.

## Copilot Interaction Guidelines
- **Focus on Python:** When generating code, prioritize Python solutions.
- **Context Awareness:** Pay close attention to existing code and project structure for relevant suggestions.
- **Refactoring:** Suggest improvements for code readability, maintainability, and performance.
- **Error Handling:** Include robust error handling mechanisms where appropriate, following the project's retry and timeout patterns.
