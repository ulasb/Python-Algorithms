from collections import deque

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
# A backward search from the target molecule to "e" is much more efficient.
# We reverse the replacements and use a standard Breadth-First Search (BFS).
reverse_replacements = [(to, from_) for from_, to in replacements]

seen_before = {original_molecule}
molecule_queue = deque([(original_molecule, 0)])

while molecule_queue:
    cur_molecule, num_steps = molecule_queue.popleft()
    print(cur_molecule)

    if cur_molecule == "e":
        print("Part 2:", num_steps)
        exit()

    # Generate next states by applying reverse replacements
    for mol_from, mol_to in reverse_replacements:
        start_pos = 0
        while True:
            start_pos = cur_molecule.find(mol_from, start_pos)
            if start_pos == -1:
                break
            
            new_molecule = cur_molecule[:start_pos] + mol_to + cur_molecule[start_pos + len(mol_from):]
            if new_molecule not in seen_before:
                seen_before.add(new_molecule)
                molecule_queue.append((new_molecule, num_steps + 1))
            
            start_pos += 1

print("Part 2: Could not find a solution.")