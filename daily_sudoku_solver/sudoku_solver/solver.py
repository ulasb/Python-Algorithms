def solve_sudoku(grid, max_steps=50000):
    """
    Solves a Sudoku puzzle using backtracking.
    grid: 2D list of 9x9 integers (0 for empty)
    """
    steps = [0]
    
    def is_valid(grid, row, col, num):
        # Check row
        for x in range(9):
            if grid[row][x] == num:
                return False
        
        # Check column
        for x in range(9):
            if grid[x][col] == num:
                return False
        
        # Check 3x3 box
        start_row, start_col = 3 * (row // 3), 3 * (col // 3)
        for i in range(3):
            for j in range(3):
                if grid[i + start_row][j + start_col] == num:
                    return False
        return True

    def find_empty(grid):
        for i in range(9):
            for j in range(9):
                if grid[i][j] == 0:
                    return (i, j)
        return None

    def backtrack(grid):
        steps[0] += 1
        if steps[0] > max_steps:
            raise Exception("Solver reached maximum step limit (board might be unsolvable or OCR was incorrect)")
            
        empty = find_empty(grid)
        if not empty:
            return True
        row, col = empty

        for num in range(1, 10):
            if is_valid(grid, row, col, num):
                grid[row][col] = num
                if backtrack(grid):
                    return True
                grid[row][col] = 0
        return False

    if backtrack(grid):
        return grid
    return None

def print_grid(grid):
    if not grid:
        print("No solution found.")
        return
    for i in range(9):
        if i % 3 == 0 and i != 0:
            print("- - - - - - - - - - - -")
        for j in range(9):
            if j % 3 == 0 and j != 0:
                print("|", end=" ")
            print(grid[i][j], end=" ")
        print()
