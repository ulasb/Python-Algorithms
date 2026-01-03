# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Created and published by Ulaş Bardak.

"""
Main entry point for the Sudoku solver application.
"""

import sys
import asyncio
from solver import solve_sudoku, print_grid
from scraper import extract_sudoku


async def main():
    """
    Main execution loop. Parses arguments, extracts the grid, and solves it.

    Parameters
    ----------
    sys.argv[1] : str, optional
        The URL of the Sudoku puzzle to solve. Defaults to the Sudoku.com Daily Challenge.
    """
    # Get URL from command line argument or use default
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = "https://sudoku.com/challenges/daily-sudoku"

    print(f"Loading puzzle from: {url}")

    try:
        # Extract the grid via scraper (OCR/CV)
        grid = await extract_sudoku(url)

        if not grid:
            print("Error: Could not extract Sudoku grid from the page.")
            return

        print("\n--- Extracted Puzzle ---")
        print_grid(grid)

        # Solve the extracted grid
        print("\nSolving...")
        # Make a deep copy of the grid for the solver to avoid mutating the original
        solution = solve_sudoku([row[:] for row in grid])

        if solution:
            print("\n--- Solution ---")
            print_grid(solution)
        else:
            print("\nError: No solution found for this puzzle.")

    except Exception as e:
        # Guidelines: Let errors flow up to the top level and handle them there
        print(f"Error: An unexpected error occurred: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())
