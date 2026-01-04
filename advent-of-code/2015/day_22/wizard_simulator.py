"""
Wizard Simulator 2015.

This script simulates a turn-based combat between a Wizard player and a Boss.
The goal is to find the minimum mana spent to win the battle.

Created and published by Ulaş Bardak.
Follows Mozilla Public License 2.0.
"""

import heapq
import sys
import argparse
import unittest
from typing import Dict, Tuple


class Spell:
    """
    Represents a magic spell with its cost, effects, and duration.

    Attributes:
        name (str): The name of the spell.
        cost (int): Mana cost to cast.
        damage (int): Instant damage dealt.
        heal (int): Instant healing for the player.
        duration (int): Number of rounds the effect lasts.
    """

    def __init__(
        self,
        name: str,
        cost: int,
        damage: int = 0,
        heal: int = 0,
        duration: int = 0,
    ):
        self.name = name
        self.cost = cost
        self.damage = damage
        self.heal = heal
        self.duration = duration


class Character:
    """
    Represents both the player and the boss.

    Attributes:
        name (str): Name of the character.
        hp (int): Hit points.
        mana (int): Current mana.
        damage (int): Damage dealt by attacks.
    """

    def __init__(self, name: str, hp: int, mana: int = 0, damage: int = 0):
        self.name = name
        self.hp = hp
        self.mana = mana
        self.damage = damage


# Define official spells
MAGIC_MISSILE = Spell("Magic Missile", 53, damage=4)
DRAIN = Spell("Drain", 73, damage=2, heal=2)
SHIELD = Spell("Shield", 113, duration=6)
POISON = Spell("Poison", 173, duration=6)
RECHARGE = Spell("Recharge", 229, duration=5)

SPELLS = [MAGIC_MISSILE, DRAIN, SHIELD, POISON, RECHARGE]


def apply_effects(
    p_hp: int, p_mana: int, b_hp: int, effects: Dict[str, int]
) -> Tuple[int, int, int, Dict[str, int], int]:
    """
    Iterates any active spells effects at the start of each turn.

    Args:
        p_hp: Player hit points.
        p_mana: Player mana.
        b_hp: Boss hit points.
        effects: Dictionary of active spell effects and their remaining durations.

    Returns:
        Tuple containing updated p_hp, p_mana, b_hp, new_effects, and p_armor.
    """
    p_armor = 0
    new_effects = {}

    # Shield effect
    if "Shield" in effects:
        p_armor = 7
        if effects["Shield"] > 1:
            new_effects["Shield"] = effects["Shield"] - 1

    # Poison effect
    if "Poison" in effects:
        b_hp -= 3
        if effects["Poison"] > 1:
            new_effects["Poison"] = effects["Poison"] - 1

    # Recharge effect
    if "Recharge" in effects:
        p_mana += 101
        if effects["Recharge"] > 1:
            new_effects["Recharge"] = effects["Recharge"] - 1

    return p_hp, p_mana, b_hp, new_effects, p_armor


def simulate_round(
    p_hp: int,
    p_mana: int,
    b_hp: int,
    effects_tuple: Tuple[Tuple[str, int], ...],
    spell: Spell,
    boss_damage: int,
    hard_mode: bool = False,
) -> Tuple[bool, int, int, int, Dict[str, int], int]:
    """
    Simulates a player turn and a boss turn.

    Args:
        p_hp: Player HP.
        p_mana: Player mana.
        b_hp: Boss HP.
        effects_tuple: Tuple of (spell_name, duration) pairs.
        spell: The spell the player chooses to cast.
        boss_damage: The base damage of the boss.
        hard_mode: Whether the simulation is in hard mode.

    Returns:
        Tuple: (win_flag, res_p_hp, res_p_mana, res_b_hp, res_effects, status)
        status: 0 for continue, -1 for loss.
    """
    effects = dict(effects_tuple)

    # --- PLAYER TURN ---
    if hard_mode:
        p_hp -= 1
        if p_hp <= 0:
            return False, 0, 0, 0, {}, -1

    p_hp, p_mana, b_hp, effects, p_armor = apply_effects(p_hp, p_mana, b_hp, effects)
    if b_hp <= 0:
        return True, p_hp, p_mana, b_hp, effects, 0

    # Cast spell
    p_mana -= spell.cost
    next_p_hp = p_hp + spell.heal
    next_b_hp = b_hp - spell.damage
    if spell.duration > 0:
        effects[spell.name] = spell.duration

    if next_b_hp <= 0:
        return True, next_p_hp, p_mana, next_b_hp, effects, 0

    # --- BOSS TURN ---
    b_p_hp, b_p_mana, b_b_hp, b_effects, b_p_armor = apply_effects(
        next_p_hp, p_mana, next_b_hp, effects
    )
    if b_b_hp <= 0:
        return True, b_p_hp, b_p_mana, b_b_hp, b_effects, 0

    # Boss attack
    damage = max(1, boss_damage - b_p_armor)
    b_p_hp -= damage

    if b_p_hp <= 0:
        return False, 0, 0, 0, {}, -1

    return False, b_p_hp, b_p_mana, b_b_hp, b_effects, 0


def find_min_mana(boss_hp: int, boss_damage: int, hard_mode: bool = False) -> int:
    """
    Finds the least amount of mana spent to win using Dijkstra's algorithm.

    Args:
        boss_hp: Initial hit points of the boss.
        boss_damage: Initial damage of the boss.
        hard_mode: Whether hard mode is enabled.

    Returns:
        The minimum mana required to win.
    """
    # Priority Queue: (mana_spent, p_hp, p_mana, b_hp, effects_tuple)
    pq = [(0, 50, 500, boss_hp, ())]
    visited = {}

    while pq:
        mana_spent, p_hp, p_mana, b_hp, effects_tuple = heapq.heappop(pq)

        state = (p_hp, p_mana, b_hp, effects_tuple)
        if state in visited and visited[state] <= mana_spent:
            continue
        visited[state] = mana_spent

        # Peek turn to see what can be cast after start-of-turn effects
        trial_p_hp = p_hp
        if hard_mode:
            trial_p_hp -= 1
            if trial_p_hp <= 0:
                continue

        trial_p_hp, trial_p_mana, trial_b_hp, trial_effects, _ = apply_effects(
            trial_p_hp, p_mana, b_hp, dict(effects_tuple)
        )

        if trial_b_hp <= 0:
            return mana_spent

        for spell in SPELLS:
            if trial_p_mana >= spell.cost and spell.name not in trial_effects:
                win, res_p_hp, res_p_mana, res_b_hp, res_effects, status = (
                    simulate_round(
                        p_hp,
                        p_mana,
                        b_hp,
                        effects_tuple,
                        spell,
                        boss_damage,
                        hard_mode,
                    )
                )

                new_mana_spent = mana_spent + spell.cost
                if win:
                    return new_mana_spent

                if status == 0:
                    res_effects_tuple = tuple(sorted(res_effects.items()))
                    new_state = (res_p_hp, res_p_mana, res_b_hp, res_effects_tuple)
                    if new_state not in visited or visited[new_state] > new_mana_spent:
                        heapq.heappush(
                            pq,
                            (
                                new_mana_spent,
                                res_p_hp,
                                res_p_mana,
                                res_b_hp,
                                res_effects_tuple,
                            ),
                        )

    return sys.maxsize


class TestWizardSimulator(unittest.TestCase):
    """Unit tests for the Wizard combat simulator."""

    def test_scenario_1(self):
        """Test a simple combat scenario where Poison and Magic Missile are used."""
        p_hp, p_mana = 10, 250
        b_hp, b_damage = 13, 8
        effects = ()

        # Turn 1: Poison
        win, ph, pm, bh, effects, status = simulate_round(
            p_hp, p_mana, b_hp, effects, POISON, b_damage
        )
        self.assertFalse(win)
        self.assertEqual(ph, 2)
        self.assertEqual(pm, 77)
        self.assertEqual(bh, 10)

        # Turn 2: Magic Missile
        win, ph, pm, bh, effects, status = simulate_round(
            ph, pm, bh, tuple(sorted(effects.items())), MAGIC_MISSILE, b_damage
        )
        self.assertTrue(win)
        self.assertEqual(bh, 0)

    def test_scenario_2(self):
        """Test a complex scenario involving Recharge and Shield."""
        p_hp, p_mana = 10, 250
        b_hp, b_damage = 14, 8
        effects = ()

        # Turn 1: Recharge
        win, ph, pm, bh, effects, status = simulate_round(
            p_hp, p_mana, b_hp, effects, RECHARGE, b_damage
        )
        self.assertFalse(win)
        self.assertEqual(ph, 2)
        self.assertEqual(pm, 122)

        # Turn 2: Shield
        win, ph, pm, bh, effects, status = simulate_round(
            ph, pm, bh, tuple(sorted(effects.items())), SHIELD, b_damage
        )
        self.assertFalse(win)
        self.assertEqual(ph, 1)
        self.assertEqual(pm, 211)

        # Turn 3: Drain
        win, ph, pm, bh, effects, status = simulate_round(
            ph, pm, bh, tuple(sorted(effects.items())), DRAIN, b_damage
        )
        self.assertFalse(win)
        self.assertEqual(ph, 2)
        self.assertEqual(pm, 340)


def main():
    """Main execution point for the Wizard Simulator script."""
    parser = argparse.ArgumentParser(description="Advent of Code 2015 Day 22 Solver")
    parser.add_argument(
        "filename",
        nargs="?",
        default="input.txt",
        help="Input file with boss stats",
    )
    parser.add_argument("--test", action="store_true", help="Run unit tests")
    parser.add_argument(
        "--hard",
        action="store_true",
        help="Enable Hard Mode (-1 HP at player turn start)",
    )
    args = parser.parse_args()

    if args.test:
        sys.argv = [sys.argv[0]]
        unittest.main()
        return

    try:
        with open(args.filename, "r", encoding="utf-8") as file:
            stats = {}
            for line in file:
                if ":" in line:
                    key, val = line.split(":")
                    stats[key.strip()] = int(val.strip())
            boss_hp = stats["Hit Points"]
            boss_damage = stats["Damage"]
    except FileNotFoundError:
        print(f"Error: {args.filename} not found.")
        sys.exit(1)
    except (KeyError, ValueError) as error:
        raise ValueError(f"Error parsing file: {error}") from error

    mode = " (HARD MODE)" if args.hard else ""
    print(f"Boss HP: {boss_hp}, Damage: {boss_damage}{mode}")
    result = find_min_mana(boss_hp, boss_damage, args.hard)
    print(f"Least amount of mana to win: {result}")


if __name__ == "__main__":
    main()
