#!/usr/bin/env python3
"""
Simple Text-Based Adventure Game
Save as adventure.py and run: python adventure.py
"""

import random
import sys

# -------------------------
# Game object definitions
# -------------------------

class Item:
    def __init__(self, name: str, description: str, heal: int = 0, attack_bonus: int = 0):
        self.name = name.lower()
        self.description = description
        self.heal = heal
        self.attack_bonus = attack_bonus

    def __str__(self):
        parts = [self.name]
        if self.heal:
            parts.append(f"(heals {self.heal})")
        if self.attack_bonus:
            parts.append(f"(atk +{self.attack_bonus})")
        return " ".join(parts)


class Enemy:
    def __init__(self, name: str, hp: int, attack: int, description: str = ""):
        self.name = name.lower()
        self.hp = hp
        self.attack = attack
        self.description = description

    def is_alive(self):
        return self.hp > 0

    def take_damage(self, dmg: int):
        self.hp -= dmg
        return self.hp

    def __str__(self):
        return f"{self.name} (HP: {self.hp}, ATK: {self.attack})"


class Room:
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.items = []         # list of Item
        self.enemies = []       # list of Enemy
        self.exits = {}         # direction -> Room

    def add_item(self, item: Item):
        self.items.append(item)

    def add_enemy(self, enemy: Enemy):
        self.enemies.append(enemy)

    def connect(self, other_room, direction: str):
        """
        Connect self to other_room. direction is from self -> other_room.
        Allowed directions: 'north','south','east','west','up','down'
        This convenience method does NOT auto-create the reverse connection.
        """
        self.exits[direction.lower()] = other_room

    def get_description(self):
        lines = [f"You are in {self.name}.", self.description]
        if self.items:
            lines.append("You see the following items: " + ", ".join(i.name for i in self.items))
        if self.enemies:
            alive = [e.name for e in self.enemies if e.is_alive()]
            if alive:
                lines.append("Enemies here: " + ", ".join(alive))
        if self.exits:
            lines.append("Exits: " + ", ".join(self.exits.keys()))
        return "\n".join(lines)


class Player:
    def __init__(self, starting_room: Room, name: str = "Player"):
        self.name = name
        self.current_room = starting_room
        self.hp = 30
        self.base_attack = 5
        self.inventory = []

    def is_alive(self):
        return self.hp > 0

    def attack_value(self):
        # Attack value = base + any attack bonuses from items in inventory
        bonus = sum(i.attack_bonus for i in self.inventory)
        return self.base_attack + bonus

    def add_item(self, item: Item):
        self.inventory.append(item)

    def use_healing(self):
        # Use the first healing item in inventory automatically (for convenience)
        for i, it in enumerate(self.inventory):
            if it.heal > 0:
                self.hp += it.heal
                used = self.inventory.pop(i)
                return used
        return None

    def __str__(self):
        return f"{self.name} (HP: {self.hp}, ATK: {self.attack_value()})"

# -------------------------
# Game engine
# -------------------------

class Game:
    def __init__(self):
        self.rooms = {}
        self.player = None
        self.create_world()
        self._intro_shown = False

    def create_world(self):
        # Create rooms
        foyer = Room("Foyer", "A small entrance hall. Dusty, with old portraits.")
        hall = Room("Great Hall", "A wide hall with a long table. Shadows flicker.")
        armory = Room("Armory", "Racks of old weapons; one looks usable.")
        kitchen = Room("Kitchen", "A greasy kitchen with broken pots.")
        cellar = Room("Cellar", "Damp and dark. You can hear something moving.")
        tower = Room("Tower Top", "A windy top of the tower with a view of the land.")

        # Connect rooms (two-way where appropriate)
        foyer.connect(hall, "north"); hall.connect(foyer, "south")
        hall.connect(armory, "east"); armory.connect(hall, "west")
        hall.connect(kitchen, "west"); kitchen.connect(hall, "east")
        kitchen.connect(cellar, "down"); cellar.connect(kitchen, "up")
        hall.connect(tower, "up"); tower.connect(hall, "down")

        # Items
        potion = Item("Small Potion", "A red potion. Restores 10 HP.", heal=10)
        big_potion = Item("Large Potion", "A larger potion. Restores 20 HP.", heal=20)
        rusty_sword = Item("Rusty Sword", "An old rusty sword. Adds to attack.", attack_bonus=3)
        gem = Item("Glowing Gem", "A strange gem. Maybe valuable?")


        # Place items
        foyer.add_item(potion)
        armory.add_item(rusty_sword)
        kitchen.add_item(big_potion)
        tower.add_item(gem)

        # Enemies
        rat = Enemy("Giant Rat", hp=8, attack=2, description="A big gnawing rat.")
        goblin = Enemy("Goblin", hp=14, attack=4, description="Sneaky and mean.")
        wraith = Enemy("Wraith", hp=25, attack=7, description="An eerie shadow-like thing guarding the top.")

        cellar.add_enemy(rat)
        hall.add_enemy(goblin)
        tower.add_enemy(wraith)

        # Register rooms
        self.rooms = {
            "foyer": foyer,
            "hall": hall,
            "armory": armory,
            "kitchen": kitchen,
            "cellar": cellar,
            "tower": tower
        }

        # Create player and set starting room
        self.player = Player(starting_room=foyer, name="Adventurer")

    def start(self):
        if not self._intro_shown:
            print("Welcome to the Text Adventure! Type 'help' for a list of commands.\n")
            self._intro_shown = True
        print(self.player.current_room.get_description())

        while True:
            if not self.player.is_alive():
                print("You have perished. Game over.")
                break

            user = input("\n> ").strip()
            if not user:
                continue
            if user.lower() in ("quit", "exit"):
                print("Thanks for playing — goodbye!")
                break
            self.handle_command(user.lower())

    def handle_command(self, cmd_line: str):
        parts = cmd_line.split()
        cmd = parts[0]

        if cmd == "help":
            self.cmd_help()
        elif cmd == "look":
            print(self.player.current_room.get_description())
        elif cmd == "inventory":
            self.cmd_inventory()
        elif cmd == "go":
            if len(parts) < 2:
                print("Go where? Usage: go <direction>")
            else:
                self.cmd_go(parts[1])
        elif cmd == "take":
            if len(parts) < 2:
                print("Take what? Usage: take <item>")
            else:
                self.cmd_take(" ".join(parts[1:]))
        elif cmd == "fight":
            if len(parts) < 2:
                print("Fight whom? Usage: fight <enemy>")
            else:
                self.cmd_fight(" ".join(parts[1:]))
        elif cmd == "use":
            # use <itemname> - currently only healing items supported
            if len(parts) < 2:
                print("Use what? Usage: use <itemname>")
            else:
                self.cmd_use(" ".join(parts[1:]))
        else:
            print("Unknown command. Type 'help' for commands.")

    def cmd_help(self):
        print(
            "Commands:\n"
            "  go <direction>      Move to a room (north, south, east, west, up, down).\n"
            "  look                Show the current room description again.\n"
            "  take <item>         Pick up an item.\n"
            "  inventory           Show your items and stats.\n"
            "  use <item>          Use an item from inventory (e.g. potion).\n"
            "  fight <enemy>       Engage an enemy in the room.\n"
            "  help                Show this help text.\n"
            "  quit                Quit the game."
        )

    def cmd_inventory(self):
        print(self.player)
        if not self.player.inventory:
            print("Inventory is empty.")
        else:
            print("Inventory:")
            for it in self.player.inventory:
                print(" -", it)

    def cmd_go(self, direction: str):
        room = self.player.current_room
        if direction not in room.exits:
            print("You can't go that way.")
            return
        new_room = room.exits[direction]
        self.player.current_room = new_room
        print(f"You go {direction} to the {new_room.name}.")
        print(new_room.get_description())

    def cmd_take(self, item_name: str):
        room = self.player.current_room
        item_name = item_name.lower()
        for i, it in enumerate(room.items):
            if it.name == item_name:
                self.player.add_item(it)
                room.items.pop(i)
                print(f"You took the {it.name}.")
                return
        print("No such item here.")

    def cmd_use(self, item_name: str):
        item_name = item_name.lower()
        for i, it in enumerate(self.player.inventory):
            if it.name == item_name:
                if it.heal > 0:
                    self.player.hp += it.heal
                    self.player.inventory.pop(i)
                    print(f"You used {it.name} and restored {it.heal} HP. Current HP: {self.player.hp}")
                else:
                    print(f"You used {it.name}, but nothing notable happened.")
                return
        print("You don't have that item.")

    def find_enemy_in_room(self, enemy_name: str):
        room = self.player.current_room
        enemy_name = enemy_name.lower()
        for e in room.enemies:
            if e.name == enemy_name and e.is_alive():
                return e
        return None

    def cmd_fight(self, enemy_name: str):
        enemy = self.find_enemy_in_room(enemy_name)
        if not enemy:
            print("No such enemy here.")
            return

        print(f"You engage the {enemy.name}!")
        # Simple turn-based combat: player attacks first
        while enemy.is_alive() and self.player.is_alive():
            # Player attack
            player_atk = self.player.attack_value() + random.randint(0, 3)  # small randomness
            dmg_to_enemy = max(1, player_atk)
            enemy.take_damage(dmg_to_enemy)
            print(f"You hit the {enemy.name} for {dmg_to_enemy} damage. {enemy.name} HP is now {max(0, enemy.hp)}.")

            if not enemy.is_alive():
                print(f"You defeated the {enemy.name}!")
                # Maybe drop item or reward (simple: chance of potion)
                if random.random() < 0.4:
                    loot = Item("Small Potion", "A potion dropped by the enemy.", heal=8)
                    self.player.current_room.add_item(loot)
                    print(f"The {enemy.name} dropped a Small Potion.")
                return

            # Enemy turn
            enemy_atk = enemy.attack + random.randint(0, 2)
            dmg_to_player = max(1, enemy_atk)
            self.player.hp -= dmg_to_player
            print(f"The {enemy.name} hits you for {dmg_to_player}. Your HP is now {max(0, self.player.hp)}.")

            if not self.player.is_alive():
                print("You were slain in battle...")
                return

            # Prompt: allow player to choose to continue or use item
            action = input("Type 'c' to continue fighting, 'use <item>' to use an item, or 'flee' to run: ").strip().lower()
            if action == "flee":
                # attempt to flee back to previous room if possible; set to foyer for simplicity
                # For a slightly better approach, we could track previous room; here we send to foyer.
                self.player.current_room = self.rooms.get("foyer", self.player.current_room)
                print("You flee back to the foyer to safety.")
                print(self.player.current_room.get_description())
                return
            elif action.startswith("use "):
                self.handle_command(action)
                # continue loop; enemy may attack again in next iteration
            elif action == "c" or action == "":
                continue
            else:
                print("Unknown option; continuing the fight.")

# -------------------------
# Entry point
# -------------------------

def main():
    game = Game()
    try:
        game.start()
    except KeyboardInterrupt:
        print("\nGoodbye!")
        sys.exit(0)

if __name__ == "__main__":
    main()
