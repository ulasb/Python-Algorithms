# Firework Simulation

A visual firework simulation built with Python and Pygame featuring realistic physics, particle effects, and procedurally generated sound effects.

## Features

- 🎆 **Interactive launching**: Press SPACE to launch fireworks
- 🎨 **Colorful explosions**: Random vibrant colors for each firework
- ⚡ **Realistic physics**: Gravity, velocity, and fade effects on particles
- 🔊 **Sound effects**: Procedurally generated launch and explosion sounds
- 📊 **Performance monitoring**: Real-time FPS counter
- 🎮 **Intuitive controls**: Simple keyboard interface

## Requirements

- Python >= 3.10
- pygame >= 2.5.0
- numpy >= 1.20.0

## Installation

1. Clone the repository or download the files
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the simulation:
```bash
python3 fireworks.py
```

### Controls

- **SPACE**: Launch a firework
- **ESC or Q**: Quit the simulation

## How It Works

### Firework Physics

Each firework follows these stages:
1. **Launch**: Rockets start from the bottom of the screen at a random x-coordinate (within the center 75% of screen width)
2. **Ascent**: Travel upward with constant velocity
3. **Explosion**: At 10-25% from the top of the screen, explodes into 80-120 particles
4. **Particle effects**: Particles spread in all directions, affected by:
   - Gravity (downward acceleration)
   - Air resistance (horizontal velocity dampening)
   - Alpha fade (gradual transparency increase)

### Sound Generation

Sound effects are synthesized using NumPy:
- **Launch sound**: Frequency sweep from 200Hz to 800Hz with exponential decay
- **Explosion sound**: White noise mixed with low-frequency components

## Code Structure

- `Particle`: Represents individual explosion particles with physics
- `Firework`: Manages rocket launch, explosion triggering, and particle creation
- `create_launch_sound()`: Generates whoosh sound effect
- `create_explosion_sound()`: Generates boom sound effect
- `main()`: Game loop handling events, updates, and rendering

## License

This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0.
If a copy of the MPL was not distributed with this file, You can obtain one at https://mozilla.org/MPL/2.0/.

**Created and published by Ulaş Bardak**

The MPL 2.0 is a copyleft license that allows you to:
- Use the code commercially
- Modify the code
- Distribute the code
- Use patent claims

With the requirement that:
- Modifications must be released under MPL 2.0
- Original source must be disclosed
- A copy of the license and copyright notice must be included

## Development

This code follows Python best practices:
- Formatted with `black`
- Docstrings follow NumPy style guide
- PEP8 compliant

To format the code:
```bash
python3 -m black fireworks.py
```
