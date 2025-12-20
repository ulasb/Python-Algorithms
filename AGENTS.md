# Project Guide for AI Agents

## Python Environment
*   **Python Version:** Use Python >= 3.10
*   **Dependency Tool:** Use `pip` for all dependency management tasks.
*   **Virtual Environment:** Ensure operations are performed within the active `venv`.

## Testing Instructions
*   **Test Style:** New tests must use the `unittest` framework.

## Code Style
*   **Formatting:** Use `black` as the auto-formatter. Do not introduce unformatted code.
*   **Docstrings:** All functions and classes must have clear, concise docstrings following the NumPy style.

## Security Considerations
*   **SQL Injections:** Use parameterized queries for all database interactions. Never use string formatting for SQL.

## Input/Output Conventions
* Whenever there is an external file to read, take that as an input parameter and default to "input.txt".
* Whenever output needs to be produced, simply print to STDOUT in human readable but succinct format.

## Error Handling and Logging
* Keep error handling to a reasonable amount - we're looking for errors to help with development or understanding when there is a problem with the input so action can be taken.
* Use comments instead to talk about potential error cases that are very unlikely and therefore we will make assumptions instead of making the code unreadable or unnecessarily long.

## Project structure
* Generally try to keep Part 1 and Part 2 solutions separate so if a change in algorithm is required it is easy to understand it end-to-end.
* Stay with one file unless it grows beyond the level of easy maintainability.
* Don't create classes needlessly if they don't help with readability and maintainability.

## Overall theme
These scripts are created as solutions to the Advent of Code problems. Make sure that the scripts are:
- Performant
- Follow Python best practices for design, readability, and maintainability
- Make sure that a human is able to read and understand what the code is doing even if it means sacrificing a small amount of performance.
