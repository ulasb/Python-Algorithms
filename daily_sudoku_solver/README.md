# Daily Sudoku Solver

A cross-platform, site-agnostic Sudoku solver that uses Computer Vision (OpenCV) and OCR (Tesseract) to extract puzzles from web pages and solve them using a backtracking algorithm.

## Overview

This project was developed to solve the Daily Sudoku challenge on various websites, specifically handling modern features like HTML5 Canvases, older frameset architectures (e.g., WebSudoku), and transient overlays/popups.

### Approach

1.  **Browser Automation**: Uses `Playwright` to navigate to a target URL, handle overlays, and capture a 4K resolution screenshot of the page.
2.  **Computer Vision**: Uses `OpenCV` to:
    *   Detect the Sudoku grid square in the screenshot using multiple thresholding techniques.
    *   Apply perspective correction (warping) to create a clean, top-down view of the board.
    *   Isolate individual digit contours (blobs) to remove grid-line interference.
3.  **OCR**: Uses `pytesseract` to identify digits from the isolated cell images.
4.  **Backtracking Solver**: Implements a standard backtracking algorithm to solve the 9x9 grid.

## Installation

### Prerequisites

-   Python >= 3.10
-   **Tesseract OCR Engine**:
    *   Mac: `brew install tesseract`
    *   Linux: `sudo apt install tesseract-ocr`
-   **OpenCV Dependencies**:
    *   Varies by OS (usually included in `opencv-python` but might need system libs like `libgl1`).

### Steps

1.  Install Python dependencies:
    ```bash
    pip install -r requirements.txt
    ```
2.  Install Playwright browsers:
    ```bash
    python -m playwright install chromium
    ```

## Usage

Run the solver on the default Daily Challenge:
```bash
python3 sudoku_solver/main.py
```

Run on a specific URL:
```bash
python3 sudoku_solver/main.py https://sudoku.com/hard/
python3 sudoku_solver/main.py https://www.websudoku.com/
```

## Project Structure

-   `sudoku_solver/main.py`: Entry point, parses arguments and handles the main loop.
-   `sudoku_solver/scraper.py`: CV and OCR logic for grid extraction.
-   `sudoku_solver/solver.py`: Backtracking algorithm and grid printing utilities.

## Licensing

This project is created and published by **Ulaş Bardak**.

The code is licensed under the **Mozilla Public License 2.0 (MPL 2.0)**. 

### What this means:
-   **Permissions**: You can use, modify, and distribute the code for both open-source and commercial purposes.
-   **Conditions**: If you modify the source code and distribute it, those modifications must also be released under the MPL 2.0. However, you can combine this code with other files under different licenses to create a larger work (as long as the MPL files remain under MPL).
-   **Disclaimer**: The code is provided "as is" without warranty of any kind.
