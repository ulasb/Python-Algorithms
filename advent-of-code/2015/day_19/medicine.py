from collections import deque
import sys
sys.setrecursionlimit(10000)    

def read_input(input_file):
    hit_space = False
    replacements = []
    original_molecule = ""
    with open(input_file) as input_file:
        while(line := input_file.readline()):
            if line == "\n":
                hit_space = True
                continue
            if hit_space:
                original_molecule = line.strip()
            else:
                replacements.append(line.strip().split(" => "))
    return replacements, original_molecule

def generate_molecules(molecule, replacements, seen_before):
    molecules = set()
    for replacementFrom, replacementTo in replacements:
        start_position = 0
        while True:
            start_position = molecule.find(replacementFrom, start_position)
            if start_position == -1:    
                break
            new_molecule = molecule[:start_position] + replacementTo + molecule[start_position + len(replacementFrom):]
            if new_molecule not in seen_before:
                molecules.add(new_molecule)
                seen_before.add(new_molecule)
            start_position += 1
    return molecules


INPUT_FILE = "input.txt"
seen_before = set()

replacements, original_molecule = read_input(INPUT_FILE)

# Part 1
unique_molecules = generate_molecules(original_molecule, replacements, seen_before)
print("Part 1:", len(unique_molecules))

# Part 2
# 1)Push starting molecule into a stack
# 2)Pop molecule from stack and replace all occurrences of each replacement
# 3)Push new molecules into stack
# 4)Repeat until original molecule is reached

# Reset seen_before
seen_before = set()
molecule_queue = deque()
cur_molecule = "e"
num_steps = 0
# TODO: This will result in an infinite loop if the original molecule is not reachable from "e"
while cur_molecule != original_molecule:
    print("Current molecule:", cur_molecule)
    if len(cur_molecule) > 2*len(original_molecule):
        pass
    else:
        num_steps += 1
        new_molecules = generate_molecules(cur_molecule, replacements, seen_before)
        for new_molecule in new_molecules:
            if new_molecule == original_molecule:
                print("Part 2:", num_steps)
                exit()
            molecule_queue.appendleft((new_molecule, num_steps))

    cur_molecule, num_steps = molecule_queue.pop()

print("Part 2:", num_steps)