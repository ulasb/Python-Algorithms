import sys
import asyncio
from solver import solve_sudoku, print_grid
from scraper import extract_sudoku

async def main():
    # Get URL from command line argument or use default
    url = sys.argv[1] if len(sys.argv) > 1 else "https://sudoku.com/challenges/daily-sudoku"
    
    print(f"Loading puzzle from: {url}")
    
    try:
        # Extract the grid
        grid = await extract_sudoku(url)
        
        if not grid:
            print("Error: Could not extract Sudoku grid from the page.")
            return

        print("\n--- Extracted Puzzle ---")
        print_grid(grid)
        
        print("\nSolving...")
        # Make a deep copy of the grid for the solver
        solution = solve_sudoku([row[:] for row in grid])

        if solution:
            print("\n--- Solution ---")
            print_grid(solution)
        else:
            print("\nError: No solution found for this puzzle.")
            
    except Exception as e:
        print(f"Error: An unexpected error occurred: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
