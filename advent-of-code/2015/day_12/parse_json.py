#!/usr/bin/env python3
"""
Advent of Code 2015 - Day 12: JSAbacusFramework.io

Solution for summing numbers in JSON structures.
Part 1: Sum all numbers in the JSON
Part 2: Sum all numbers, ignoring objects that contain "red"
"""

import json
import sys
import os
import unittest
from typing import Any, Union

def read_input(filename: str) -> str:
    """
    Read the input file and return the contents.

    Args:
        filename: Path to the input file

    Returns:
        The file contents as a string

    Raises:
        SystemExit: If file cannot be read
    """
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        return content
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file: {e}")
        sys.exit(1)

def parse_json(json_string: str) -> Any:
    """
    Parse the JSON string into a Python object.

    Args:
        json_string: Valid JSON string

    Returns:
        Parsed JSON object (dict, list, etc.)

    Raises:
        SystemExit: If JSON is invalid
    """
    try:
        return json.loads(json_string)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        sys.exit(1)


# Constants
RED_VALUE = "red"

def sum_numbers(obj: Any, bad_value: str = "") -> int:
    """
    Recursively traverse the JSON object and sum all numbers.

    For Part 2, if bad_value is specified and any dictionary contains
    bad_value as a value, that entire dictionary is ignored.

    Args:
        obj: JSON object (dict, list, or primitive)
        bad_value: Value that causes entire dictionaries to be ignored

    Returns:
        Sum of all numbers in the structure
    """
    total = 0

    if isinstance(obj, dict):
        # For dictionaries, check if bad_value is present
        if bad_value and bad_value in obj.values():
            return 0  # Ignore this entire dictionary
        # Otherwise, recurse through all values
        for value in obj.values():
            total += sum_numbers(value, bad_value)
    elif isinstance(obj, list):
        # For lists, recurse through all items
        for item in obj:
            total += sum_numbers(item, bad_value)
    elif isinstance(obj, (int, float)):
        # For numbers, add them to the total
        total += obj
    # Ignore strings, booleans, and null values (implicitly return 0)

    return total


class TestJSONSum(unittest.TestCase):
    """Unit tests for Advent of Code Day 12 JSON summing functions."""

    def test_part1_basic_arrays_and_objects(self):
        """Test Part 1: basic arrays and objects."""
        # [1,2,3] and {"a":2,"b":4} both have a sum of 6
        self.assertEqual(sum_numbers([1, 2, 3]), 6)
        self.assertEqual(sum_numbers({"a": 2, "b": 4}), 6)

    def test_part1_nested_structures(self):
        """Test Part 1: nested structures."""
        # [[[3]]] and {"a":{"b":4},"c":-1} both have a sum of 3
        self.assertEqual(sum_numbers([[[3]]]), 3)
        self.assertEqual(sum_numbers({"a": {"b": 4}, "c": -1}), 3)

    def test_part1_zero_sum_cases(self):
        """Test Part 1: cases that sum to zero."""
        # {"a":[-1,1]} and [-1,{"a":1}] both have a sum of 0
        self.assertEqual(sum_numbers({"a": [-1, 1]}), 0)
        self.assertEqual(sum_numbers([-1, {"a": 1}]), 0)

    def test_part1_empty_structures(self):
        """Test Part 1: empty structures."""
        # [] and {} both have a sum of 0
        self.assertEqual(sum_numbers([]), 0)
        self.assertEqual(sum_numbers({}), 0)

    def test_part2_basic_case(self):
        """Test Part 2: basic case still works."""
        # [1,2,3] still has a sum of 6
        self.assertEqual(sum_numbers([1, 2, 3], RED_VALUE), 6)

    def test_part2_ignore_red_object(self):
        """Test Part 2: ignore object containing red."""
        # [1,{"c":"red","b":2},3] now has a sum of 4
        self.assertEqual(sum_numbers([1, {"c": RED_VALUE, "b": 2}, 3], RED_VALUE), 4)

    def test_part2_ignore_entire_structure(self):
        """Test Part 2: ignore entire structure with red."""
        # {"d":"red","e":[1,2,3,4],"f":5} now has a sum of 0
        self.assertEqual(sum_numbers({"d": RED_VALUE, "e": [1, 2, 3, 4], "f": 5}, RED_VALUE), 0)

    def test_part2_red_in_array_no_effect(self):
        """Test Part 2: red in array has no effect."""
        # [1,"red",5] has a sum of 6
        self.assertEqual(sum_numbers([1, RED_VALUE, 5], RED_VALUE), 6)


def main():
    """Main solution function."""
    # Get the input file path
    input_file = os.path.join(os.path.dirname(__file__), 'input.txt')

    # Read and parse the input
    json_string = read_input(input_file)
    data = parse_json(json_string)

    # Part 1: Sum all numbers
    part1_result = sum_numbers(data)
    print(f"Part 1 - Sum of all numbers: {part1_result}")

    # Part 2: Sum all numbers, ignoring objects with "red"
    part2_result = sum_numbers(data, RED_VALUE)
    print(f"Part 2 - Sum ignoring '{RED_VALUE}' objects: {part2_result}")

def run_tests():
    """Run the unit test suite."""
    print("Running unit tests...")
    unittest.main(argv=[''], exit=False, verbosity=2)


if __name__ == "__main__":
    # Check for test-only flag
    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        run_tests()
    else:
        # Run tests first, then main solution
        print("Running unit tests...")
        unittest.main(argv=[''], exit=False, verbosity=0)
        print("\n" + "="*50)
        main()
