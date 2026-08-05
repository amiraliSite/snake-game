import pygame
import random
import sys
import math
import json

pygame.init()

CELL = 25
COLS, ROWS = 24, 16
WIDTH, HEIGHT = COLS * CELL, ROWS * CELL
FPS = 7

BG = (18, 18, 24)
GRID_COLOR = (30, 30, 40)
FOOD_COLOR = (255, 70, 70)
FOOD_GLOW = (255, 120, 120, 40)
TEXT_COLOR = (240, 240, 240)
ACCENT = (100, 220, 160)
BTN_COLOR = (0, 180, 100)
BTN_HOVER = (0, 220, 130)
BTN_TEXT = (255, 255, 255)

RECORD_FILE = "snake_record.json"

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("🐍 Snake Game")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 30, bold=True)
small_font = pygame.font.SysFont("Arial", 18)
btn_font = pygame.font.SysFont("Arial", 22, bold=True)

particles = []
food_pulse = 0.0


def load_high_score():
    try:
        with open(RECORD_FILE, 'r') as f:
            return json.load(f).get('high_score', 0)
    except (FileNotFoundError, json.JSONDecodeError):
        return 0


def save_high_score(score):
    with open(RECORD_FILE, 'w') as f:
        json.dump({'high_score': score}, f)


high_score = load_high_score()


def lerp_color(c1, c2, t):
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))


def spawn_particles(x, y, color, count=12):
    px = x * CELL + CELL / 2
    py = y * CELL + CELL / 2
    for _ in range(count):
        angle = random.uniform(0, math.tau)
        speed = random.uniform(1.5, 4.5)
        particles.append({
            'x': px, 'y': py,
            'vx': math.cos(angle) * speed,
            'vy': math.sin(angle) * speed,
            'life': random.randint(15, 30),
            'color': color,
            'size': random.uniform(3, 6)
        })


def draw_particles():
    global particles
    alive = []
    for p in particles:
        p['x'] += p['vx']
        p['y'] += p['vy']
        p['life'] -= 1
        p['size'] *= 0.92
        if p['life'] > 0 and p['size'] > 0.5:
            alpha = min(255, p['life'] * 12)
            surf = pygame.Surface((int(p['size'] * 2), int(p['size'] * 2)), pygame.SRCALPHA)
            pygame.draw.circle(surf, (*p['color'], alpha),
                               (int(p['size']), int(p['size'])), int(p['size']))
            screen.blit(surf, (int(p['x'] - p['size']), int(p['y'] - p['size'])))
            alive.append(p)
    particles = alive


def draw_button(text, rect, mouse_pos):
    hovered = rect.collidepoint(mouse_pos)
    color = BTN_HOVER if hovered else BTN_COLOR
    pygame.draw.rect(screen, color, rect, border_radius=10)
    pygame.draw.rect(screen, (255, 255, 255, 80), rect, 2, border_radius=10)
    txt = btn_font.render(text, True, BTN_TEXT)
    screen.blit(txt, (rect.centerx - txt.get_width() // 2,
                       rect.centery - txt.get_height() // 2))
    return hovered


def get_snake_color(i, n):
    
    if i == 0:
        return (0, 255, 120)
    t = i / max(n - 1, 1)
    if t < 0.5:
        return lerp_color((0, 220, 100), (0, 180, 220), t * 2)
    else:
        return lerp_color((0, 180, 220), (80, 60, 200), (t - 0.5) * 2)


def draw_snake(snake, direction):
    n = len(snake)
    positions = []
    for i, (x, y) in enumerate(snake):
        cx = x * CELL + CELL // 2
        cy = y * CELL + CELL // 2
        positions.append((cx, cy))

    for i in range(len(positions) - 1):
        t = i / max(n - 1, 1)
        color = get_snake_color(i, n)
        width = max(int(CELL * 0.6 * (1 - t * 0.4)), 4)
        pygame.draw.line(screen, color, positions[i], positions[i + 1], width)

    for i, (cx, cy) in enumerate(positions):
        t = i / max(n - 1, 1)
        color = get_snake_color(i, n)
        radius = max(int(CELL // 2 * (1 - t * 0.35)), 4)

        if i % 3 == 0:
            glow = pygame.Surface((radius * 4, radius * 4), pygame.SRCALPHA)
            pygame.draw.circle(glow, (*color, 30), (radius * 2, radius * 2), radius * 2)
            screen.blit(glow, (cx - radius * 2, cy - radius * 2))

        pygame.draw.circle(screen, color, (cx, cy), radius)

   
        if i > 0 and i % 2 == 0 and radius > 5:
            scale_color = tuple(min(255, c + 40) for c in color)
            pygame.draw.circle(screen, scale_color, (cx, cy), max(radius // 2, 2))

   
    if positions:
        cx, cy = positions[0]
        dx, dy = direction

      
        head_glow = pygame.Surface((CELL * 2, CELL * 2), pygame.SRCALPHA)
        pygame.draw.circle(head_glow, (0, 255, 120, 50), (CELL, CELL), CELL)
        screen.blit(head_glow, (cx - CELL, cy - CELL))


        head_r = CELL // 2 + 1
        pygame.draw.circle(screen, (0, 255, 120), (cx, cy), head_r)

        for side in (-1, 1):
            ex = cx + dx * 5 + (-dy) * side * 5
            ey = cy + dy * 5 + dx * side * 5
            pygame.draw.circle(screen, (255, 255, 255), (int(ex), int(ey)), 4)
            pygame.draw.circle(screen, (0, 0, 0), (int(ex + dx * 2), int(ey + dy * 2)), 2)
            pygame.draw.circle(screen, (255, 255, 255), (int(ex - dx + dy * side), int(ey - dy - dx * side)), 1)

        tongue_len = 8 + math.sin(food_pulse * 3) * 3
        tx = cx + dx * (head_r + tongue_len)
        ty = cy + dy * (head_r + tongue_len)
        pygame.draw.line(screen, (255, 80, 80), (cx + dx * head_r, cy + dy * head_r),
                         (int(tx), int(ty)), 2)
        fork = 3
        pygame.draw.line(screen, (255, 80, 80),
                         (int(tx), int(ty)),
                         (int(tx + (-dy) * fork + dx * 3), int(ty + dx * fork + dy * 3)), 2)
        pygame.draw.line(screen, (255, 80, 80),
                         (int(tx), int(ty)),
                         (int(tx - (-dy) * fork + dx * 3), int(ty - dx * fork + dy * 3)), 2)


def main():
    global FPS, food_pulse, high_score

    snake = [(10, 8), (9, 8), (8, 8)]
    direction = (1, 0)
    next_dir = (1, 0)
    score = 0
    game_over = False

    restart_rect = pygame.Rect(WIDTH // 2 - 90, HEIGHT // 2 + 50, 180, 45)

    def spawn_food():
        while True:
            pos = (random.randint(0, COLS - 1), random.randint(0, ROWS - 1))
            if pos not in snake:
                return pos

    food = spawn_food()

    while True:
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                if game_over and event.key == pygame.K_SPACE:
                    return main()
                if not game_over:
                    if event.key in (pygame.K_UP, pygame.K_w) and direction != (0, 1):
                        next_dir = (0, -1)
                    elif event.key in (pygame.K_DOWN, pygame.K_s) and direction != (0, -1):
                        next_dir = (0, 1)
                    elif event.key in (pygame.K_LEFT, pygame.K_a) and direction != (1, 0):
                        next_dir = (-1, 0)
                    elif event.key in (pygame.K_RIGHT, pygame.K_d) and direction != (-1, 0):
                        next_dir = (1, 0)
            if event.type == pygame.MOUSEBUTTONDOWN and game_over:
                if restart_rect.collidepoint(event.pos):
                    return main()

        if not game_over:
            direction = next_dir
            hx, hy = snake[0]
            dx, dy = direction
            new_head = (hx + dx, hy + dy)
            nx, ny = new_head
            if nx < 0 or nx >= COLS or ny < 0 or ny >= ROWS or new_head in snake:
                game_over = True
                spawn_particles(hx, hy, (255, 100, 100), 20)
                if score > high_score:
                    high_score = score
                    save_high_score(high_score)
            else:
                snake.insert(0, new_head)
                if new_head == food:
                    score += 10
                    spawn_particles(*new_head, FOOD_COLOR, 15)
                    food = spawn_food()
                else:
                    snake.pop()

        food_pulse += 0.15

        screen.fill(BG)

        for x in range(0, WIDTH, CELL):
            pygame.draw.line(screen, GRID_COLOR, (x, 0), (x, HEIGHT))
        for y in range(0, HEIGHT, CELL):
            pygame.draw.line(screen, GRID_COLOR, (0, y), (WIDTH, y))

        draw_snake(snake, direction)

        fx = food[0] * CELL + CELL // 2
        fy = food[1] * CELL + CELL // 2
        pulse = math.sin(food_pulse) * 3
        glow_r = int(CELL // 2 + 4 + pulse)
        glow_surf = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, FOOD_GLOW, (glow_r, glow_r), glow_r)
        screen.blit(glow_surf, (fx - glow_r, fy - glow_r))
        food_r = int(CELL // 2 - 2 + pulse * 0.3)
        pygame.draw.circle(screen, FOOD_COLOR, (fx, fy), max(food_r, 4))

        draw_particles()

        score_txt = font.render(f"Score: {score}", True, TEXT_COLOR)
        high_txt = small_font.render(f"Best: {high_score}", True, ACCENT)
        screen.blit(score_txt, (12, 8))
        screen.blit(high_txt, (12, 42))

        if game_over:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))

            go = font.render("GAME OVER", True, (255, 90, 90))
            sc = font.render(f"Score: {score}", True, TEXT_COLOR)
            hint = small_font.render("or press SPACE", True, (150, 150, 150))

            screen.blit(go, (WIDTH // 2 - go.get_width() // 2, HEIGHT // 2 - 60))
            screen.blit(sc, (WIDTH // 2 - sc.get_width() // 2, HEIGHT // 2 - 15))

            hovered = draw_button("Restart", restart_rect, mouse_pos)
            screen.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT // 2 + 105))

            if hovered:
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
            else:
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
        else:
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)

        pygame.display.flip()
        clock.tick(FPS)


if __name__ == "__main__":
    main()
