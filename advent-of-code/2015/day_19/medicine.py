# Plan:
# 1. Read replacements and molecule from input file
# 2. For each replacement, replace all occurrences in molecule
# 3. Count unique molecules

INPUT_FILE = "input.txt"

hit_space = False
replacements = []
original_molecule = ""
with open(INPUT_FILE) as input_file:
    while(line := input_file.readline()):
        if line == "\n":
            hit_space = True
            continue
        if hit_space:
            original_molecule = line.strip()
        else:
            replacements.append(line.strip().split(" => "))

unique_molecules = set()
for replacementFrom, replacementTo in replacements:
    #Create a new molecule for each replacement
    start_position = 0
    while True:
        start_position = original_molecule.find(replacementFrom, start_position)
        if start_position == -1:
            break
        new_molecule = original_molecule[:start_position] + replacementTo + original_molecule[start_position + len(replacementFrom):]
        unique_molecules.add(new_molecule)
        start_position += 1

print(len(unique_molecules))

    