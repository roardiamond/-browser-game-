import pygame
import random
import math
import asyncio

# --- Constants ---
WIDTH, HEIGHT = 800, 600
FPS = 60
DAY_LENGTH = 60
NIGHT_LENGTH = 30
TOTAL_NIGHTS_TO_WIN = 3

# Colors
GREEN = (34, 139, 34)
DARK_GREEN = (0, 100, 0)
BROWN = (139, 69, 19)
GRAY = (128, 128, 128)
BLUE = (0, 0, 255)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
PURPLE = (128, 0, 128)
ORANGE = (255, 165, 0)
GOLD = (255, 220, 100)
MENU_BG = (18, 38, 22)


def clamp(value, min_val, max_val):
    return max(min_val, min(value, max_val))


def distance(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


# ---------- UI Button ----------
class Button:
    def __init__(self, text, x, y, w, h):
        self.text = text
        self.rect = pygame.Rect(x, y, w, h)
        self.hover = False

    def draw(self, screen, font):
        color = (75, 175, 85) if self.hover else (35, 110, 50)
        pygame.draw.rect(screen, color, self.rect, border_radius=12)
        pygame.draw.rect(screen, (220, 255, 220), self.rect, 2, border_radius=12)
        txt = font.render(self.text, True, WHITE)
        screen.blit(txt, (self.rect.centerx - txt.get_width() // 2,
                          self.rect.centery - txt.get_height() // 2))

    def check_hover(self, pos):
        self.hover = self.rect.collidepoint(pos)

    def clicked(self, pos):
        return self.rect.collidepoint(pos)


# ---------- Game Entities ----------
class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.size = 20
        self.speed = 3
        self.health = 100
        self.hunger = 100
        self.thirst = 100
        self.inventory = {"wood": 0, "stone": 0, "water": 3, "food": 0}
        self.has_spear = False
        self.has_campfire = False
        self.has_storage = False
        self.facing = (1, 0)
        self.invulnerable_timer = 0

    def move(self, dx, dy):
        self.x = clamp(self.x + dx * self.speed, 0, WIDTH - self.size)
        self.y = clamp(self.y + dy * self.speed, 0, HEIGHT - self.size)
        if dx != 0 or dy != 0:
            length = math.hypot(dx, dy)
            self.facing = (dx / length, dy / length)

    def update(self, dt):
        self.hunger = clamp(self.hunger - 0.5 * dt, 0, 100)
        self.thirst = clamp(self.thirst - 0.7 * dt, 0, 100)
        if self.hunger <= 0 or self.thirst <= 0:
            self.health -= 10 * dt
        if self.invulnerable_timer > 0:
            self.invulnerable_timer -= dt

    def take_damage(self, amount):
        if self.invulnerable_timer <= 0:
            self.health -= amount
            self.invulnerable_timer = 1.0

    def draw(self, screen):
        color = BLUE if self.invulnerable_timer <= 0 else WHITE
        pygame.draw.rect(screen, color, (self.x, self.y, self.size, self.size))
        if self.has_spear:
            start = (self.x + self.size // 2, self.y + self.size // 2)
            end = (start[0] + self.facing[0] * 30, start[1] + self.facing[1] * 30)
            pygame.draw.line(screen, BROWN, start, end, 4)


class Resource:
    def __init__(self, x, y, kind):
        self.x = x
        self.y = y
        self.kind = kind
        self.size = 15
        self.infected = False

    def draw(self, screen):
        if self.kind == "wood":
            color = BROWN
        elif self.kind == "stone":
            color = GRAY
        elif self.kind == "water":
            color = BLUE
        elif self.kind == "food":
            color = PURPLE if self.infected else GREEN
        else:
            color = WHITE
        pygame.draw.rect(screen, color, (self.x, self.y, self.size, self.size))
        if self.kind == "food" and self.infected:
            pygame.draw.line(screen, BLACK, (self.x, self.y),
                             (self.x + self.size, self.y + self.size), 2)
            pygame.draw.line(screen, BLACK, (self.x + self.size, self.y),
                             (self.x, self.y + self.size), 2)


class Zombie:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.size = 20
        self.speed = 1.5
        self.health = 30

    def update(self, dt, player, resources):
        nearest_food = None
        min_dist = float("inf")
        for res in resources:
            if res.kind == "food" and not res.infected:
                d = distance((self.x, self.y), (res.x, res.y))
                if d < min_dist:
                    min_dist = d
                    nearest_food = res

        if nearest_food:
            target = (nearest_food.x, nearest_food.y)
            target_obj = nearest_food
        else:
            target = (player.x, player.y)
            target_obj = player

        dx = target[0] - self.x
        dy = target[1] - self.y
        dist = math.hypot(dx, dy)
        if dist > 0:
            self.x += (dx / dist) * self.speed * dt * 60
            self.y += (dy / dist) * self.speed * dt * 60

        if target_obj == player:
            if distance((self.x, self.y), (player.x, player.y)) < self.size:
                player.take_damage(10)
        else:
            if distance((self.x, self.y),
                        (nearest_food.x, nearest_food.y)) < self.size:
                nearest_food.infected = True

    def draw(self, screen):
        pygame.draw.rect(screen, RED, (self.x, self.y, self.size, self.size))


# ---------- Main Game ----------
class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Jungle Survival - test v1")
        self.clock = pygame.time.Clock()

        self.font = pygame.font.SysFont("Arial", 20)
        self.small_font = pygame.font.SysFont("Arial", 16)
        self.mid_font = pygame.font.SysFont("Arial", 32, bold=True)
        self.big_font = pygame.font.SysFont("Arial", 58, bold=True)

        # Menu UI
        self.menu_buttons = [
            Button("PLAY",          WIDTH // 2 - 150, 300, 300, 60),
            Button("HOW TO PLAY",   WIDTH // 2 - 150, 380, 300, 60),
            Button("QUIT",          WIDTH // 2 - 150, 460, 300, 60),
        ]
        self.menu_selection = 0
        self.howto_back = Button("BACK", WIDTH // 2 - 110, HEIGHT - 110, 220, 60)
        self.gameover_buttons = [
            Button("PLAY AGAIN", WIDTH // 2 - 150, 370, 300, 60),
            Button("MAIN MENU",  WIDTH // 2 - 150, 450, 300, 60),
        ]

        self.reset()
        self.state = "menu"
        self.update_menu_hover()

    # ---------- State reset ----------
    def reset(self):
        self.player = Player(WIDTH // 2, HEIGHT // 2)
        self.resources = []
        self.zombies = []
        self.missions = [
            {"desc": "Collect 5 wood",     "done": False},
            {"desc": "Build a campfire",   "done": False},
            {"desc": "Survive 1 night",    "done": False},
        ]
        self.nights_survived = 0
        self.day_timer = DAY_LENGTH
        self.is_day = True
        self.game_over = False
        self.win = False
        self.message = ""
        self.message_timer = 0
        self.spawn_resources()
        self.spawn_zombies()

    def spawn_resources(self):
        for _ in range(15):
            kind = random.choice(["wood", "wood", "stone", "water", "food"])
            x = random.randint(50, WIDTH - 50)
            y = random.randint(50, HEIGHT - 50)
            self.resources.append(Resource(x, y, kind))

    def spawn_zombies(self):
        self.zombies = []
        for _ in range(3):
            side = random.randint(0, 3)
            if side == 0:
                x, y = random.randint(0, WIDTH), -20
            elif side == 1:
                x, y = random.randint(0, WIDTH), HEIGHT + 20
            elif side == 2:
                x, y = -20, random.randint(0, HEIGHT)
            else:
                x, y = WIDTH + 20, random.randint(0, HEIGHT)
            self.zombies.append(Zombie(x, y))

    # ---------- Menu helpers ----------
    def update_menu_hover(self):
        for i, b in enumerate(self.menu_buttons):
            b.hover = (i == self.menu_selection)

    def show_message(self, msg, duration=2):
        self.message = msg
        self.message_timer = duration

    # ---------- Missions ----------
    def update_missions(self):
        if not self.missions[0]["done"] and self.player.inventory["wood"] >= 5:
            self.missions[0]["done"] = True
            self.show_message("Mission Complete: Collect 5 wood!")
        if not self.missions[1]["done"] and self.player.has_campfire:
            self.missions[1]["done"] = True
            self.show_message("Mission Complete: Build a campfire!")
        if not self.missions[2]["done"] and self.nights_survived >= 1:
            self.missions[2]["done"] = True
            self.show_message("Mission Complete: Survive 1 night!")

    # ---------- Gameplay ----------
    def handle_gameplay_input(self, dt):
        keys = pygame.key.get_pressed()
        dx, dy = 0, 0
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx = -1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx = 1
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy = -1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy = 1
        self.player.move(dx, dy)
        self.player.update(dt)

        for res in self.resources[:]:
            if distance((self.player.x, self.player.y), (res.x, res.y)) < self.player.size:
                if res.kind == "food" and res.infected:
                    self.show_message("Picked up infected food!")
                self.player.inventory[res.kind] = self.player.inventory.get(res.kind, 0) + 1
                self.resources.remove(res)
                self.show_message(f"Collected {res.kind}")

    def handle_gameplay_keydown(self, key):
        if key == pygame.K_ESCAPE:
            self.state = "menu"
            return
        if key == pygame.K_e:
            if self.player.inventory["food"] > 0:
                self.player.inventory["food"] -= 1
                self.player.hunger = clamp(self.player.hunger + 30, 0, 100)
                self.show_message("Ate food (+30 hunger)")
            else:
                self.show_message("No food!")
        elif key == pygame.K_q:
            if self.player.inventory["water"] > 0:
                self.player.inventory["water"] -= 1
                self.player.thirst = clamp(self.player.thirst + 40, 0, 100)
                self.show_message("Drank water (+40 thirst)")
            else:
                self.show_message("No water!")
        elif key == pygame.K_1:
            if self.player.inventory["wood"] >= 5:
                self.player.inventory["wood"] -= 5
                self.player.has_campfire = True
                self.show_message("Crafted Campfire!")
            else:
                self.show_message("Need 5 wood for campfire")
        elif key == pygame.K_2:
            if self.player.inventory["wood"] >= 3 and self.player.inventory["stone"] >= 2:
                self.player.inventory["wood"] -= 3
                self.player.inventory["stone"] -= 2
                self.player.has_spear = True
                self.show_message("Crafted Spear!")
            else:
                self.show_message("Need 3 wood, 2 stone for spear")
        elif key == pygame.K_3:
            if self.player.inventory["wood"] >= 4:
                self.player.inventory["wood"] -= 4
                self.player.has_storage = True
                self.show_message("Crafted Food Storage!")
            else:
                self.show_message("Need 4 wood for storage")
        elif key == pygame.K_SPACE and self.player.has_spear:
            for z in self.zombies[:]:
                if distance((self.player.x, self.player.y), (z.x, z.y)) < 40:
                    z.health -= 20
                    if z.health <= 0:
                        self.zombies.remove(z)
                        self.show_message("Zombie killed!")

    def update_gameplay(self, dt):
        self.day_timer -= dt
        if self.day_timer <= 0:
            if self.is_day:
                self.is_day = False
                self.day_timer = NIGHT_LENGTH
                self.spawn_zombies()
                self.show_message("Night falls! Zombies approach!")
            else:
                self.is_day = True
                self.day_timer = DAY_LENGTH
                self.nights_survived += 1
                self.zombies = []
                self.show_message(f"Morning! Survived night {self.nights_survived}")
                if self.nights_survived >= TOTAL_NIGHTS_TO_WIN:
                    self.win = True

        if not self.is_day:
            for z in self.zombies[:]:
                z.update(dt, self.player, self.resources)

        if self.player.health <= 0:
            self.game_over = True

        self.update_missions()

        if self.message_timer > 0:
            self.message_timer -= dt

    # ---------- Events ----------
    def handle_events(self):
        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if event.type == pygame.MOUSEMOTION:
                if self.state == "menu":
                    for i, b in enumerate(self.menu_buttons):
                        if b.rect.collidepoint(mouse_pos):
                            self.menu_selection = i
                            break
                    self.update_menu_hover()
                elif self.state == "howto":
                    self.howto_back.check_hover(mouse_pos)
                elif self.state in ("gameover", "win"):
                    for b in self.gameover_buttons:
                        b.check_hover(mouse_pos)

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = event.pos
                if self.state == "menu":
                    if self.menu_buttons[0].clicked(pos):
                        self.reset(); self.state = "playing"
                    elif self.menu_buttons[1].clicked(pos):
                        self.state = "howto"
                    elif self.menu_buttons[2].clicked(pos):
                        return False
                elif self.state == "howto":
                    if self.howto_back.clicked(pos):
                        self.state = "menu"
                elif self.state in ("gameover", "win"):
                    if self.gameover_buttons[0].clicked(pos):
                        self.reset(); self.state = "playing"
                    elif self.gameover_buttons[1].clicked(pos):
                        self.state = "menu"

            elif event.type == pygame.KEYDOWN:
                if self.state == "menu":
                    if event.key in (pygame.K_UP, pygame.K_w):
                        self.menu_selection = (self.menu_selection - 1) % len(self.menu_buttons)
                        self.update_menu_hover()
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        self.menu_selection = (self.menu_selection + 1) % len(self.menu_buttons)
                        self.update_menu_hover()
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        if self.menu_selection == 0:
                            self.reset(); self.state = "playing"
                        elif self.menu_selection == 1:
                            self.state = "howto"
                        else:
                            return False
                    elif event.key == pygame.K_ESCAPE:
                        return False
                elif self.state == "howto":
                    if event.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE):
                        self.state = "menu"
                elif self.state == "playing":
                    self.handle_gameplay_keydown(event.key)
                elif self.state in ("gameover", "win"):
                    if event.key == pygame.K_r:
                        self.reset(); self.state = "playing"
                    elif event.key in (pygame.K_m, pygame.K_ESCAPE):
                        self.state = "menu"
        return True

    # ---------- Drawing ----------
    def draw_menu(self):
        self.screen.fill(MENU_BG)
        # Decorative jungle silhouettes
        for i in range(8):
            x = i * 110
            pygame.draw.rect(self.screen, (14, 55, 25), (x, 0, 80, HEIGHT))
            pygame.draw.circle(self.screen, (22, 85, 38),
                               (x + 40, 60 + (i % 3) * 25), 95)

        # Title
        shadow = self.big_font.render("JUNGLE SURVIVAL", True, BLACK)
        title = self.big_font.render("JUNGLE SURVIVAL", True, GOLD)
        tx = WIDTH // 2 - title.get_width() // 2
        self.screen.blit(shadow, (tx + 4, 134))
        self.screen.blit(title, (tx, 130))

        sub = self.mid_font.render("test v1", True, (200, 255, 200))
        self.screen.blit(sub, (WIDTH // 2 - sub.get_width() // 2, 205))

        for b in self.menu_buttons:
            b.draw(self.screen, self.font)

        hint = self.small_font.render(
            "Use mouse or arrow keys + Enter", True, (180, 220, 180))
        self.screen.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT - 40))

    def draw_howto(self):
        self.screen.fill(MENU_BG)
        title = self.mid_font.render("HOW TO PLAY", True, GOLD)
        self.screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 40))

        lines = [
            "WASD / Arrows     Move",
            "E                 Eat food",
            "Q                 Drink water",
            "1                 Craft Campfire  (5 wood)",
            "2                 Craft Spear     (3 wood, 2 stone)",
            "3                 Craft Food Storage (4 wood)",
            "SPACE             Attack (needs spear)",
            "ESC               Return to menu",
            "",
            "Survive 3 nights. Zombies spawn at night,",
            "attack you, and try to infect your food.",
            "",
            "Collect resources, complete missions,",
            "and stay alive!",
        ]
        y = 110
        for line in lines:
            surf = self.font.render(line, True, WHITE)
            self.screen.blit(surf, (WIDTH // 2 - surf.get_width() // 2, y))
            y += 28

        self.howto_back.draw(self.screen, self.font)

    def draw_game(self):
        if self.is_day:
            self.screen.fill(GREEN)
        else:
            self.screen.fill(DARK_GREEN)

        for res in self.resources:
            res.draw(self.screen)
        self.player.draw(self.screen)
        for z in self.zombies:
            z.draw(self.screen)

        bar_w, bar_h = 200, 20
        pygame.draw.rect(self.screen, RED, (10, 10, bar_w, bar_h))
        pygame.draw.rect(self.screen, GREEN,
                         (10, 10, bar_w * (self.player.health / 100), bar_h))
        self.screen.blit(
            self.small_font.render(f"Health: {int(self.player.health)}", True, WHITE),
            (10, 12))

        pygame.draw.rect(self.screen, ORANGE, (10, 40, bar_w, bar_h))
        pygame.draw.rect(self.screen, YELLOW,
                         (10, 40, bar_w * (self.player.hunger / 100), bar_h))
        self.screen.blit(
            self.small_font.render(f"Hunger: {int(self.player.hunger)}", True, BLACK),
            (10, 42))

        pygame.draw.rect(self.screen, BLUE, (10, 70, bar_w, bar_h))
        pygame.draw.rect(self.screen, (0, 255, 255),
                         (10, 70, bar_w * (self.player.thirst / 100), bar_h))
        self.screen.blit(
            self.small_font.render(f"Thirst: {int(self.player.thirst)}", True, BLACK),
            (10, 72))

        inv = (f"Wood: {self.player.inventory['wood']}  "
               f"Stone: {self.player.inventory['stone']}  "
               f"Water: {self.player.inventory['water']}  "
               f"Food: {self.player.inventory['food']}")
        self.screen.blit(self.small_font.render(inv, True, WHITE), (10, 100))

        craft = (f"Spear: {'Yes' if self.player.has_spear else 'No'}  "
                 f"Campfire: {'Yes' if self.player.has_campfire else 'No'}  "
                 f"Storage: {'Yes' if self.player.has_storage else 'No'}")
        self.screen.blit(self.small_font.render(craft, True, WHITE), (10, 125))

        time_txt = (f"{'Day' if self.is_day else 'Night'}: {int(self.day_timer)}s  "
                    f"Nights: {self.nights_survived}/{TOTAL_NIGHTS_TO_WIN}")
        self.screen.blit(self.font.render(time_txt, True, WHITE), (WIDTH - 350, 10))

        y = 160
        self.screen.blit(self.font.render("Missions:", True, WHITE), (10, y))
        y += 25
        for m in self.missions:
            status = "DONE" if m["done"] else "..."
            col = (100, 255, 120) if m["done"] else WHITE
            self.screen.blit(
                self.small_font.render(f"[{status}] {m['desc']}", True, col),
                (20, y))
            y += 20

        if self.message_timer > 0:
            msg = self.font.render(self.message, True, YELLOW)
            self.screen.blit(msg, (WIDTH // 2 - msg.get_width() // 2, HEIGHT - 50))

    def draw_overlay(self, title_text, color):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        self.screen.blit(overlay, (0, 0))

        title = self.big_font.render(title_text, True, color)
        self.screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 240))

        for b in self.gameover_buttons:
            b.draw(self.screen, self.font)

        hint = self.small_font.render(
            "R = restart    M = main menu", True, (200, 200, 200))
        self.screen.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT - 40))

    def draw(self):
        if self.state == "menu":
            self.draw_menu()
        elif self.state == "howto":
            self.draw_howto()
        elif self.state == "playing":
            self.draw_game()
        elif self.state == "gameover":
            self.draw_game()
            self.draw_overlay("GAME OVER", RED)
        elif self.state == "win":
            self.draw_game()
            self.draw_overlay("YOU WIN!", YELLOW)
        pygame.display.flip()

    # ---------- Main loop ----------
    async def run(self):
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000.0
            running = self.handle_events()

            if running and self.state == "playing":
                if not self.game_over and not self.win:
                    self.handle_gameplay_input(dt)
                    self.update_gameplay(dt)
                else:
                    self.state = "gameover" if self.game_over else "win"

            if running:
                self.draw()

            await asyncio.sleep(0)

        pygame.quit()


async def main():
    game = Game()
    await game.run()


if __name__ == "__main__":
    asyncio.run(main())
