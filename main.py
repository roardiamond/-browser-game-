import pygame
import random
import math
import asyncio

# --- Constants ---
WIDTH, HEIGHT = 800, 600
FPS = 60
DAY_LENGTH = 60      # seconds
NIGHT_LENGTH = 30    # seconds
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
PURPLE = (128, 0, 128)   # infected food
ORANGE = (255, 165, 0)


def clamp(value, min_val, max_val):
    return max(min_val, min(value, max_val))


def distance(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


# --- Classes ---
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


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("test v1 - Jungle Survival")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 20)
        self.small_font = pygame.font.SysFont("Arial", 16)
        self.reset()

    def reset(self):
        self.player = Player(WIDTH // 2, HEIGHT // 2)
        self.resources = []
        self.zombies = []
        self.missions = [
            {"desc": "Collect 5 wood", "done": False},
            {"desc": "Build a campfire", "done": False},
            {"desc": "Survive 1 night", "done": False},
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

    def show_message(self, msg, duration=2):
        self.message = msg
        self.message_timer = duration

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

    def handle_input(self, dt):
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
                    self.show_message("Picked up infected food! (Eat with caution)")
                self.player.inventory[res.kind] = self.player.inventory.get(res.kind, 0) + 1
                self.resources.remove(res)
                self.show_message(f"Collected {res.kind}")

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                if event.key == pygame.K_e:
                    if self.player.inventory["food"] > 0:
                        self.player.inventory["food"] -= 1
                        self.player.hunger = clamp(self.player.hunger + 30, 0, 100)
                        self.show_message("Ate food (+30 hunger)")
                    else:
                        self.show_message("No food!")
                if event.key == pygame.K_q:
                    if self.player.inventory["water"] > 0:
                        self.player.inventory["water"] -= 1
                        self.player.thirst = clamp(self.player.thirst + 40, 0, 100)
                        self.show_message("Drank water (+40 thirst)")
                    else:
                        self.show_message("No water!")
                if event.key == pygame.K_1:
                    if self.player.inventory["wood"] >= 5:
                        self.player.inventory["wood"] -= 5
                        self.player.has_campfire = True
                        self.show_message("Crafted Campfire!")
                    else:
                        self.show_message("Need 5 wood for campfire")
                if event.key == pygame.K_2:
                    if self.player.inventory["wood"] >= 3 and self.player.inventory["stone"] >= 2:
                        self.player.inventory["wood"] -= 3
                        self.player.inventory["stone"] -= 2
                        self.player.has_spear = True
                        self.show_message("Crafted Spear!")
                    else:
                        self.show_message("Need 3 wood, 2 stone for spear")
                if event.key == pygame.K_3:
                    if self.player.inventory["wood"] >= 4:
                        self.player.inventory["wood"] -= 4
                        self.player.has_storage = True
                        self.show_message("Crafted Food Storage!")
                    else:
                        self.show_message("Need 4 wood for storage")
                if event.key == pygame.K_SPACE and self.player.has_spear:
                    for z in self.zombies[:]:
                        if distance((self.player.x, self.player.y), (z.x, z.y)) < 40:
                            z.health -= 20
                            if z.health <= 0:
                                self.zombies.remove(z)
                                self.show_message("Zombie killed!")
                if event.key == pygame.K_r and (self.game_over or self.win):
                    self.reset()
        return True

    def update(self, dt):
        if self.game_over or self.win:
            return
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

    def draw(self):
        if self.is_day:
            self.screen.fill(GREEN)
        else:
            self.screen.fill(DARK_GREEN)

        for res in self.resources:
            res.draw(self.screen)
        self.player.draw(self.screen)
        for z in self.zombies:
            z.draw(self.screen)

        bar_width, bar_height = 200, 20
        pygame.draw.rect(self.screen, RED, (10, 10, bar_width, bar_height))
        pygame.draw.rect(self.screen, GREEN,
                         (10, 10, bar_width * (self.player.health / 100), bar_height))
        self.screen.blit(
            self.small_font.render(f"Health: {int(self.player.health)}", True, WHITE),
            (10, 12))

        pygame.draw.rect(self.screen, ORANGE, (10, 40, bar_width, bar_height))
        pygame.draw.rect(self.screen, YELLOW,
                         (10, 40, bar_width * (self.player.hunger / 100), bar_height))
        self.screen.blit(
            self.small_font.render(f"Hunger: {int(self.player.hunger)}", True, BLACK),
            (10, 42))

        pygame.draw.rect(self.screen, BLUE, (10, 70, bar_width, bar_height))
        pygame.draw.rect(self.screen, (0, 255, 255),
                         (10, 70, bar_width * (self.player.thirst / 100), bar_height))
        self.screen.blit(
            self.small_font.render(f"Thirst: {int(self.player.thirst)}", True, BLACK),
            (10, 72))

        inv_text = (f"Wood: {self.player.inventory['wood']}  "
                    f"Stone: {self.player.inventory['stone']}  "
                    f"Water: {self.player.inventory['water']}  "
                    f"Food: {self.player.inventory['food']}")
        self.screen.blit(self.small_font.render(inv_text, True, WHITE), (10, 100))

        craft_text = (f"Spear: {'Yes' if self.player.has_spear else 'No'}  "
                      f"Campfire: {'Yes' if self.player.has_campfire else 'No'}  "
                      f"Storage: {'Yes' if self.player.has_storage else 'No'}")
        self.screen.blit(self.small_font.render(craft_text, True, WHITE), (10, 125))

        time_text = (f"{'Day' if self.is_day else 'Night'}: {int(self.day_timer)}s  "
                     f"Nights survived: {self.nights_survived}/{TOTAL_NIGHTS_TO_WIN}")
        self.screen.blit(self.font.render(time_text, True, WHITE), (WIDTH - 380, 10))

        y_offset = 160
        self.screen.blit(self.font.render("Missions:", True, WHITE), (10, y_offset))
        y_offset += 25
        for m in self.missions:
            status = "DONE" if m["done"] else "..."
            color = GREEN if m["done"] else WHITE
            self.screen.blit(
                self.small_font.render(f"[{status}] {m['desc']}", True, color),
                (20, y_offset))
            y_offset += 20

        if self.message_timer > 0:
            msg_surf = self.font.render(self.message, True, YELLOW)
            self.screen.blit(msg_surf,
                             (WIDTH // 2 - msg_surf.get_width() // 2, HEIGHT - 50))

        if self.game_over:
            text = self.font.render("GAME OVER - Press R to restart", True, RED)
            self.screen.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2))
        if self.win:
            text = self.font.render("YOU WIN! Press R to restart", True, YELLOW)
            self.screen.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2))

        pygame.display.flip()

    async def run(self):
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000.0
            running = self.handle_events()
            if running and not self.game_over and not self.win:
                self.handle_input(dt)
                self.update(dt)
            self.draw()
            await asyncio.sleep(0)   # required for pygbag
        pygame.quit()


async def main():
    game = Game()
    await game.run()


if __name__ == "__main__":
    asyncio.run(main())
