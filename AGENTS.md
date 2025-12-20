# Project Guide for AI Agents

## Python Environment
*   **Python Version:** Use Python > 3.10
*   **Dependency Tool:** Use `pip` for all dependency management tasks.
*   **Virtual Environment:** Ensure operations are performed within the active `venv`.

## Testing Instructions
*   **Test Style:** New tests must use the `unittest` framework.

## Code Style
*   **Formatting:** Use `black` as the auto-formatter. Do not introduce unformatted code.
*   **Docstrings:** All functions and classes must have clear, concise docstrings following the NumPy style.

## Security Considerations
*   **SQL Injections:** Use parameterized queries for all database interactions. Never use string formatting for SQL.

## Overall theme
These scripts are created as solutions to the Advent of Code problems. Make sure that the scripts are:
- Performant
- Follow Python best practices for design, readability, and maintainability
- Make sure that a human is able to read and understand what the code is doing even if it means sacrificing a small amount of performance.
