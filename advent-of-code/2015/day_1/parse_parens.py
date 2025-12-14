import argparse

def simple_paren_count(parens: str) -> int:
    '''
    Part 1:
    Simply count the number of times the parens are opened and closed.
    '''
    current_floor = 0
    for char in parens:
        if char == '(':
            current_floor += 1
        elif char == ')':
            current_floor -= 1
    return current_floor

def find_first_basement_entry(parens: str) -> int:
    '''
    Part 2:
    Find the first time the floor is -1.
    '''
    current_floor = 0
    for i, char in enumerate(parens):
        if char == '(':
            current_floor += 1
        elif char == ')':
            current_floor -= 1
        if current_floor == -1:
            return i + 1
    return -1

def main():
    parser = argparse.ArgumentParser(description='Advent of Code Day 1: Parentheses Floor Counter')
    parser.add_argument('input_file', nargs='?', default='input.txt',
                       help='Input file containing parentheses (default: input.txt)')
    args = parser.parse_args()

    with open(args.input_file, 'r') as file:
        parens = file.read().strip()
        first_basement_entry = find_first_basement_entry(parens)
        final_floor = simple_paren_count(parens)
    print(f"Final floor: {final_floor}")
    print(f"First basement entry: {first_basement_entry}")

if __name__ == '__main__':
    main()
