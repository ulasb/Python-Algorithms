#!/usr/bin/env python3
"""
Advent of Code 2015 - Day 2: I Was Told There Would Be No Math

This script reads present dimensions from a file and processes them.
Each line contains three dimensions separated by 'x'.
"""

import sys
import argparse
import unittest


def read_present_dimensions(filename):
    """
    Read present dimensions from a file.

    Args:
        filename (str): Path to the input file

    Returns:
        list: List of lists, where each inner list contains three integers
              representing the dimensions of a present
    """
    presents = []

    try:
        with open(filename, 'r') as file:
            for line_num, line in enumerate(file, 1):
                # Remove whitespace and split by 'x'
                line = line.strip()
                if not line:
                    continue  # Skip empty lines

                # Split by 'x' and convert to integers
                try:
                    dimensions = [int(dim) for dim in line.split('x')]
                    dimensions.sort()
                    if len(dimensions) != 3:
                        print(f"Warning: Line {line_num} does not contain exactly 3 dimensions: {line}")
                        continue
                    presents.append(dimensions)
                except ValueError as e:
                    print(f"Error on line {line_num}: Could not parse dimensions from '{line}' - {e}")
                    continue

    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file '{filename}': {e}")
        sys.exit(1)

    return presents

def get_ribbon_length(presents):
    """
    Calculate the length of ribbon needed for a list of presents.
    """
    total_ribbon_length = 0
    for p in presents:
        #Bow
        total_ribbon_length += p[0] * p[1] * p[2]
        #Wrap - As the list is sorted, we can just take the first two
        total_ribbon_length += 2 * p[0] + 2 * p[1]
    return total_ribbon_length
        

def get_total_wrapping_paper(presents):
    """
    Calculate the total wrapping paper required for a list of presents.
    """
    total_wrapping_paper = 0
    for p in presents:
        # Total area
        area1 = p[0]*p[1]
        area2 = p[1]*p[2]
        area3 = p[0]*p[2]
        total_wrapping_paper += 2*area1 + 2*area2 + 2*area3
        # Slack (as the list is sorted, we can just take the first item)
        total_wrapping_paper += area1
    return total_wrapping_paper


def main():
    """
    Main function to handle command line arguments and process the input file.
    """
    parser = argparse.ArgumentParser(
        description='Read present dimensions from a file for Advent of Code Day 2'
    )
    parser.add_argument(
        'input_file',
        nargs='?',
        default='input.txt',
        help='Path to input file (default: input.txt)'
    )

    args = parser.parse_args()

    # Read the present dimensions
    presents = read_present_dimensions(args.input_file)
    print(f"Successfully read {len(presents)} presents from '{args.input_file}'")
    total_wrapping_paper = get_total_wrapping_paper(presents)
    print(f"Total wrapping paper needed {total_wrapping_paper}")
    total_ribbon_length = get_ribbon_length(presents)
    print(f"Total ribbon length needed {total_ribbon_length}")


class TestWrappingPaper(unittest.TestCase):
    """Test cases for the get_total_wrapping_paper function."""

    def test_present_2x3x4(self):
        """Test wrapping paper calculation for a present with dimensions 2x3x4."""
        presents = [[2, 3, 4]]
        result = get_total_wrapping_paper(presents)
        # Areas: 2*3=6, 3*4=12, 2*4=8
        # Total wrapping paper: 2*6 + 2*12 + 2*8 = 52
        # Slack: min(6, 12, 8) = 6
        # Total: 52 + 6 = 58
        self.assertEqual(result, 58)

    def test_present_1x1x10(self):
        """Test wrapping paper calculation for a present with dimensions 1x1x10."""
        presents = [[1, 1, 10]]
        result = get_total_wrapping_paper(presents)
        # Areas: 1*1=1, 1*10=10, 1*10=10
        # Total wrapping paper: 2*1 + 2*10 + 2*10 = 42
        # Slack: min(1, 10, 10) = 1
        # Total: 42 + 1 = 43
        self.assertEqual(result, 43)

    def test_multiple_presents(self):
        """Test wrapping paper calculation for multiple presents."""
        presents = [[2, 3, 4], [1, 1, 10]]
        result = get_total_wrapping_paper(presents)
        # 58 + 43 = 101
        self.assertEqual(result, 101)

    def test_empty_list(self):
        """Test wrapping paper calculation for an empty list of presents."""
        presents = []
        result = get_total_wrapping_paper(presents)
        self.assertEqual(result, 0)

    def test_ribbon_present_2x3x4(self):
        """Test ribbon length calculation for a present with dimensions 2x3x4."""
        presents = [[2, 3, 4]]
        result = get_ribbon_length(presents)
        # Wrap: 2+2+3+3 = 10 feet (shortest distance around sides)
        # Bow: 2*3*4 = 24 feet (volume)
        # Total: 10 + 24 = 34 feet
        self.assertEqual(result, 34)

    def test_ribbon_present_1x1x10(self):
        """Test ribbon length calculation for a present with dimensions 1x1x10."""
        presents = [[1, 1, 10]]
        result = get_ribbon_length(presents)
        # Wrap: 1+1+1+1 = 4 feet (shortest distance around sides)
        # Bow: 1*1*10 = 10 feet (volume)
        # Total: 4 + 10 = 14 feet
        self.assertEqual(result, 14)

    def test_ribbon_multiple_presents(self):
        """Test ribbon length calculation for multiple presents."""
        presents = [[2, 3, 4], [1, 1, 10]]
        result = get_ribbon_length(presents)
        # 34 + 14 = 48
        self.assertEqual(result, 48)

    def test_ribbon_empty_list(self):
        """Test ribbon length calculation for an empty list of presents."""
        presents = []
        result = get_ribbon_length(presents)
        self.assertEqual(result, 0)


if __name__ == "__main__":
    # Check if running tests
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        unittest.main(argv=[''], exit=False, verbosity=2)
    else:
        main()
