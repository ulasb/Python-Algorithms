#!/usr/bin/env python3
"""Firework Simulation.

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.

Created and published by Ulaş Bardak.

A visual simulation of fireworks using pygame. Users can launch fireworks
that travel upward and explode into colorful particle effects with realistic
physics including gravity and fade-out effects.

The simulation includes:
- Interactive firework launching
- Realistic particle physics with gravity
- Sound effects for launch and explosion
- Real-time FPS monitoring
"""

import pygame
import random
import math
import sys
import numpy as np

# Initialize Pygame
pygame.init()
pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)

# Screen dimensions
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Firework Simulation")

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

# Clock for controlling frame rate
clock = pygame.time.Clock()
FPS = 60


def create_launch_sound():
    """Generate a whoosh sound for rocket launch.

    Creates a synthesized audio effect using a frequency sweep from 200Hz to 800Hz
    with an exponential decay envelope to simulate a rocket launching sound.

    Returns
    -------
    pygame.mixer.Sound
        A pygame Sound object containing the generated whoosh effect.
    """
    sample_rate = 22050
    duration = 0.3  # seconds

    # Create a frequency sweep (whoosh effect)
    t = np.linspace(0, duration, int(sample_rate * duration))
    frequency_start = 200
    frequency_end = 800
    frequency = np.linspace(frequency_start, frequency_end, len(t))

    # Generate the sound wave
    wave = np.sin(2 * np.pi * frequency * t)

    # Apply envelope (fade in and out)
    envelope = np.exp(-3 * t)
    wave = wave * envelope

    # Convert to 16-bit integer
    wave = np.int16(wave * 32767)

    # Create stereo sound
    stereo_wave = np.repeat(wave.reshape(-1, 1), 2, axis=1)

    # Create pygame Sound object
    sound = pygame.sndarray.make_sound(stereo_wave)
    return sound


def create_explosion_sound():
    """Generate an explosion sound.

    Creates a synthesized explosion sound using white noise mixed with low
    frequency components and an exponential decay envelope.

    Returns
    -------
    pygame.mixer.Sound
        A pygame Sound object containing the generated explosion effect.
    """
    sample_rate = 22050
    duration = 0.5  # seconds

    # Create noise for explosion
    t = np.linspace(0, duration, int(sample_rate * duration))

    # White noise
    noise = np.random.uniform(-1, 1, len(t))

    # Apply low-pass filter effect by mixing with sine waves
    low_freq = np.sin(2 * np.pi * 80 * t)
    wave = 0.7 * noise + 0.3 * low_freq

    # Apply envelope (quick attack, longer decay)
    envelope = np.exp(-5 * t)
    wave = wave * envelope

    # Convert to 16-bit integer
    wave = np.int16(wave * 32767 * 0.6)  # Reduce volume slightly

    # Create stereo sound
    stereo_wave = np.repeat(wave.reshape(-1, 1), 2, axis=1)

    # Create pygame Sound object
    sound = pygame.sndarray.make_sound(stereo_wave)
    return sound


# Create sounds
launch_sound = create_launch_sound()
explosion_sound = create_explosion_sound()


class Particle:
    """Represents a single particle from the firework explosion.

    Each particle has its own position, velocity, color, and fade rate.
    Particles are affected by gravity and gradually fade out over time.

    Parameters
    ----------
    x : float
        Initial x-coordinate of the particle.
    y : float
        Initial y-coordinate of the particle.
    color : tuple of int
        RGB color tuple (r, g, b) for the particle.

    Attributes
    ----------
    x : float
        Current x-coordinate.
    y : float
        Current y-coordinate.
    vx : float
        Velocity in x direction.
    vy : float
        Velocity in y direction.
    alpha : float
        Current opacity (0-255).
    gravity : float
        Downward acceleration applied each frame.
    fade_rate : float
        Rate at which particle fades per frame.
    size : int
        Pixel radius of the particle.
    """

    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color

        # Random velocity in all directions for explosion effect
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(2, 8)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed

        # Gravity and fade
        self.gravity = 0.15
        self.alpha = 255  # Opacity
        self.fade_rate = random.uniform(2, 4)
        self.size = random.randint(2, 4)

    def update(self):
        """Update particle position and apply physics.

        Applies gravity to vertical velocity, updates position based on velocity,
        decreases opacity for fade effect, and applies air resistance to horizontal movement.
        """
        self.vy += self.gravity  # Apply gravity
        self.x += self.vx
        self.y += self.vy
        self.alpha -= self.fade_rate  # Fade out

        # Slow down horizontal movement slightly
        self.vx *= 0.98

    def draw(self, surface):
        """Draw the particle with fading effect.

        Parameters
        ----------
        surface : pygame.Surface
            The surface to draw the particle on.
        """
        if self.alpha > 0:
            # Create color with alpha
            color_with_alpha = (*self.color, max(0, int(self.alpha)))
            # Draw particle as a small circle
            surf = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
            pygame.draw.circle(
                surf, color_with_alpha, (self.size, self.size), self.size
            )
            surface.blit(surf, (int(self.x - self.size), int(self.y - self.size)))

    def is_dead(self):
        """Check if particle should be removed.

        Returns
        -------
        bool
            True if the particle has fully faded out (alpha <= 0).
        """
        return self.alpha <= 0


class Firework:
    """Represents a firework rocket that launches and explodes.

    The firework launches from the bottom of the screen at a random x position
    (within center 75% of screen width) and travels upward until reaching a
    random target height (top 10-25% of screen), where it explodes into particles.

    Attributes
    ----------
    x : float
        Current x-coordinate of the rocket.
    y : float
        Current y-coordinate of the rocket.
    target_y : float
        Y-coordinate where the firework will explode.
    vx : float
        Horizontal velocity.
    vy : float
        Vertical velocity (negative = upward).
    exploded : bool
        Whether the firework has exploded.
    particles : list of Particle
        List of particle objects created during explosion.
    trail_color : tuple of int
        RGB color for the rocket trail.
    explosion_color : tuple of int
        RGB color for the explosion particles.
    """

    def __init__(self):
        # Starting position: random x in center 75% of screen, bottom of screen
        center_start = WIDTH * 0.125  # 12.5% from left
        center_end = WIDTH * 0.875  # 87.5% from left
        self.x = random.uniform(center_start, center_end)
        self.y = HEIGHT

        # Target explosion height: top 10-25% of screen (inverted, so 75-90% down)
        explosion_start = HEIGHT * 0.10
        explosion_end = HEIGHT * 0.25
        self.target_y = random.uniform(explosion_start, explosion_end)

        # Rocket velocity
        self.vy = -12  # Upward velocity
        self.vx = 0

        # State
        self.exploded = False
        self.particles = []

        # Firework trail color
        self.trail_color = (255, 255, 200)  # Yellowish white

        # Explosion color (random vibrant color)
        self.explosion_color = self.get_random_color()

        # Play launch sound
        launch_sound.play()

    def get_random_color(self):
        """Generate a random vibrant color for the explosion.

        Returns
        -------
        tuple of int
            RGB color tuple (r, g, b) randomly selected from a preset palette.
        """
        colors = [
            (255, 50, 50),  # Red
            (50, 255, 50),  # Green
            (50, 50, 255),  # Blue
            (255, 255, 50),  # Yellow
            (255, 50, 255),  # Magenta
            (50, 255, 255),  # Cyan
            (255, 150, 50),  # Orange
            (150, 50, 255),  # Purple
        ]
        return random.choice(colors)

    def update(self):
        """Update firework state.

        If not exploded, moves the rocket upward and checks if target height is reached.
        If exploded, updates all particle positions and removes dead particles.
        """
        if not self.exploded:
            # Move rocket upward
            self.y += self.vy
            self.x += self.vx

            # Check if reached target height
            if self.y <= self.target_y:
                self.explode()
        else:
            # Update all particles
            for particle in self.particles[:]:
                particle.update()
                if particle.is_dead():
                    self.particles.remove(particle)

    def explode(self):
        """Create explosion particles.

        Marks the firework as exploded, plays the explosion sound, and generates
        80-120 particles that spread out in all directions from the explosion point.
        """
        self.exploded = True

        # Play explosion sound
        explosion_sound.play()

        # Create many particles for the explosion
        num_particles = random.randint(80, 120)
        for _ in range(num_particles):
            particle = Particle(self.x, self.y, self.explosion_color)
            self.particles.append(particle)

    def draw(self, surface):
        """Draw the firework.

        Parameters
        ----------
        surface : pygame.Surface
            The surface to draw the firework on.

        Notes
        -----
        If not exploded, draws the rocket and trail. If exploded, draws all particles.
        """
        if not self.exploded:
            # Draw the rocket as a small bright circle
            pygame.draw.circle(surface, self.trail_color, (int(self.x), int(self.y)), 3)
            # Draw a small trail
            pygame.draw.circle(
                surface, self.trail_color, (int(self.x), int(self.y + 5)), 2
            )
        else:
            # Draw all particles
            for particle in self.particles:
                particle.draw(surface)

    def is_finished(self):
        """Check if firework is completely done.

        Returns
        -------
        bool
            True if the firework has exploded and all particles have faded away.
        """
        return self.exploded and len(self.particles) == 0


def draw_text(surface, text, size, x, y, color=WHITE):
    """Helper function to draw centered text on screen.

    Parameters
    ----------
    surface : pygame.Surface
        The surface to draw the text on.
    text : str
        The text string to display.
    size : int
        Font size in pixels.
    x : int
        X-coordinate of text center.
    y : int
        Y-coordinate of text center.
    color : tuple of int, optional
        RGB color tuple for the text (default is WHITE).
    """
    font = pygame.font.Font(None, size)
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect()
    text_rect.center = (x, y)
    surface.blit(text_surface, text_rect)


def main():
    """Main game loop.

    Handles event processing, updates all active fireworks, and renders
    the display at 60 FPS. Continues until the user quits.
    """
    running = True
    fireworks = []
    waiting_for_input = True

    print("Firework Simulation Started!")
    print("Press SPACE to launch a firework, or ESC/Q to quit.")

    while running:
        clock.tick(FPS)

        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE or event.key == pygame.K_q:
                    running = False
                elif event.key == pygame.K_SPACE:
                    # Launch a new firework
                    firework = Firework()
                    fireworks.append(firework)
                    waiting_for_input = False
                    print(f"Firework launched! (Total: {len(fireworks)})")

        # Update all fireworks
        for firework in fireworks[:]:
            firework.update()
            if firework.is_finished():
                fireworks.remove(firework)

        # Draw everything
        screen.fill(BLACK)

        # Draw all active fireworks
        for firework in fireworks:
            firework.draw(screen)

        # Draw welcome message if waiting for first firework
        if waiting_for_input and len(fireworks) == 0:
            draw_text(
                screen,
                "Welcome to Firework Simulation!",
                48,
                WIDTH // 2,
                HEIGHT // 2 - 20,
            )

        # Draw permanent controls footer with semi-transparent background
        footer_height = 40
        footer_surface = pygame.Surface((WIDTH, footer_height), pygame.SRCALPHA)
        footer_surface.fill((0, 0, 0, 180))  # Semi-transparent black
        screen.blit(footer_surface, (0, HEIGHT - footer_height))

        # Draw FPS counter on the left
        current_fps = clock.get_fps()
        fps_text = f"FPS: {current_fps:.1f}"
        font = pygame.font.Font(None, 24)
        fps_surface = font.render(fps_text, True, WHITE)
        screen.blit(fps_surface, (10, HEIGHT - footer_height // 2 - 8))

        # Draw control instructions in the center
        draw_text(
            screen,
            "SPACE: Launch Firework  |  ESC/Q: Quit",
            24,
            WIDTH // 2,
            HEIGHT - footer_height // 2,
        )

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
