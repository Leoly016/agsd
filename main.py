import pygame
import json
import numpy as np
from PIL import Image
import sys
import subprocess

try:
    import pyperclip
except ImportError:
    pyperclip = None

try:
    import tkinter as tk
except ImportError:
    tk = None

SPRITE_PATH = "sprite (2).webp"

CELL = 56
MENU_COLS = 7
SCREEN_W = 1200
SCREEN_H = 820

pygame.init()
if not pygame.scrap.get_init():
    try:
        pygame.scrap.init()
    except Exception:
        pass
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("CRAFT EDITOR")

font = pygame.font.SysFont("consolas", 16)

# ================= SLICE =======================

def slice_auto(path):
    img = Image.open(path).convert("RGBA")
    arr = np.array(img)

    h, w = arr.shape[:2]
    visited = np.zeros((h, w), bool)

    tiles = []
    tid = 0

    def flood(sy, sx):
        stack = [(sy, sx)]
        visited[sy, sx] = True

        minx = maxx = sx
        miny = maxy = sy

        while stack:
            y, x = stack.pop()

            for ny in range(y-1, y+2):
                for nx in range(x-1, x+2):
                    if 0 <= ny < h and 0 <= nx < w:
                        if not visited[ny, nx] and arr[ny, nx, 3] > 20:
                            visited[ny, nx] = True
                            stack.append((ny, nx))

                            minx = min(minx, nx)
                            maxx = max(maxx, nx)
                            miny = min(miny, ny)
                            maxy = max(maxy, ny)

        return minx, miny, maxx, maxy

    for y in range(h):
        for x in range(w):
            if not visited[y, x] and arr[y, x, 3] > 20:
                minx, miny, maxx, maxy = flood(y, x)

                crop = img.crop((minx, miny, maxx+1, maxy+1))

                # центрируем в квадрат
                size = max(crop.size)
                square = Image.new("RGBA", (size, size), (0,0,0,0))
                square.paste(
                    crop,
                    ((size - crop.size[0])//2,
                     (size - crop.size[1])//2)
                )

                surf = pygame.image.fromstring(
                    square.tobytes(),
                    square.size,
                    "RGBA"
                )

                tiles.append((tid, surf))
                tid += 1

    return tiles

tiles = slice_auto(SPRITE_PATH)
TOTAL = len(tiles)

# ================= MENU =======================

scroll = 0
menu_rect = pygame.Rect(0, 0, 420, SCREEN_H)
scroll_down_button_rect = pygame.Rect(430, SCREEN_H - 60, 50, 50)
scroll_up_button_rect = pygame.Rect(430, SCREEN_H - 120, 50, 50)

def draw_scroll_button():
    hover = scroll_down_button_rect.collidepoint(pygame.mouse.get_pos())
    color = (120, 120, 120) if hover else (90, 90, 90)
    pygame.draw.rect(screen, color, scroll_down_button_rect)
    pygame.draw.rect(screen, (220, 220, 220), scroll_down_button_rect, 2)
    center = scroll_down_button_rect.center
    pygame.draw.polygon(screen, (255,255,255), [
        (center[0]-10, center[1]-3),
        (center[0]+10, center[1]-3),
        (center[0], center[1]+8)
    ])

def draw_scroll_up_button():
    hover = scroll_up_button_rect.collidepoint(pygame.mouse.get_pos())
    color = (120, 120, 120) if hover else (90, 90, 90)
    pygame.draw.rect(screen, color, scroll_up_button_rect)
    pygame.draw.rect(screen, (220, 220, 220), scroll_up_button_rect, 2)
    center = scroll_up_button_rect.center
    pygame.draw.polygon(screen, (255,255,255), [
        (center[0]-10, center[1]+3),
        (center[0]+10, center[1]+3),
        (center[0], center[1]-8)
    ])

def draw_menu():
    pygame.draw.rect(screen, (30,30,30), menu_rect)

    for i, (tid, surf) in enumerate(tiles):

        col = i % MENU_COLS
        row = i // MENU_COLS

        x = 10 + col * CELL
        y = 10 + row * CELL - scroll

        rect = pygame.Rect(x, y, CELL-4, CELL-4)

        if rect.colliderect(menu_rect):

            pygame.draw.rect(screen, (70,70,70), rect, 1)

            img = pygame.transform.smoothscale(
                surf, (CELL-12, CELL-12)
            )

            screen.blit(img, (x+4, y+4))

            txt = font.render(str(tid), True, (200,200,200))
            screen.blit(txt, (x+2, y+2))

def get_menu_tile(pos):
    x, y = pos
    if not menu_rect.collidepoint(pos):
        return None

    y += scroll

    col = (x-10) // CELL
    row = (y-10) // CELL

    idx = row * MENU_COLS + col

    if 0 <= idx < TOTAL:
        return idx
    return None

# ================= GRID =======================

grid = [-1]*9
result = -1

grid_rects = []
start = (480, 150)

for r in range(3):
    for c in range(3):
        rect = pygame.Rect(
            start[0] + c*CELL,
            start[1] + r*CELL,
            CELL,
            CELL
        )
        grid_rects.append(rect)

result_rect = pygame.Rect(700, 180, CELL, CELL)

clear_button_rect = pygame.Rect(start[0], start[1] - 60, 180, 40)
copy_button_rect = pygame.Rect(start[0] + 200, start[1] - 60, 120, 40)
copy_status = ""
copy_status_timer = 0

json_line = ""
copy_status = ""
copy_status_timer = 0

def draw_clear_button():
    hover = clear_button_rect.collidepoint(pygame.mouse.get_pos())
    color = (180, 80, 80) if hover else (140, 40, 40)
    pygame.draw.rect(screen, color, clear_button_rect)
    pygame.draw.rect(screen, (220, 220, 220), clear_button_rect, 2)
    txt = font.render("Очистить верстак", True, (255, 255, 255))
    txt_rect = txt.get_rect(center=clear_button_rect.center)
    screen.blit(txt, txt_rect)


def draw_copy_button():
    hover = copy_button_rect.collidepoint(pygame.mouse.get_pos())
    color = (80, 160, 80) if hover else (70, 140, 70)
    pygame.draw.rect(screen, color, copy_button_rect)
    pygame.draw.rect(screen, (220, 220, 220), copy_button_rect, 2)
    txt = font.render("Копировать", True, (255, 255, 255))
    txt_rect = txt.get_rect(center=copy_button_rect.center)
    screen.blit(txt, txt_rect)


def draw_grid():
    for i, rect in enumerate(grid_rects):
        pygame.draw.rect(screen, (120,120,120), rect, 2)

        if grid[i] != -1:
            surf = tiles[grid[i]][1]
            img = pygame.transform.smoothscale(
                surf, (CELL-10, CELL-10)
            )
            screen.blit(img, (rect.x+5, rect.y+5))

    pygame.draw.rect(screen, (200,180,60), result_rect, 2)

    if result != -1:
        surf = tiles[result][1]
        img = pygame.transform.smoothscale(
            surf, (CELL-10, CELL-10)
        )
        screen.blit(img, (result_rect.x+5, result_rect.y+5))

    draw_clear_button()
    draw_copy_button()

# ================= JSON =======================

def copy_line_to_clipboard(line):
    """Попытка копирования в буфер обмена разными способами."""
    if pyperclip:
        try:
            pyperclip.copy(line)
            return True, "Скопировано в буфер (pyperclip)"
        except Exception:
            pass

    if tk:
        try:
            root = tk.Tk()
            root.withdraw()
            root.clipboard_clear()
            root.clipboard_append(line)
            root.update()
            root.destroy()
            return True, "Скопировано в буфер (tkinter)"
        except Exception:
            pass

    if sys.platform.startswith("win"):
        try:
            subprocess.run(["clip"], input=line.encode("utf-8"), check=True)
            return True, "Скопировано в буфер (clip)"
        except Exception:
            pass

    if pygame.scrap.get_init():
        try:
            pygame.scrap.put(pygame.SCRAP_TEXT, line.encode("utf-8"))
            return True, "Скопировано в буфер (pygame.scrap)"
        except Exception:
            pass

    return False, "Не удалось скопировать: установите pyperclip или проверьте clipboard API" 


def draw_json():
    global copy_status, copy_status_timer, json_line

    json_line = '{"id": %s, "craft": [%s]}' % (
        result,
        ','.join(str(x) for x in grid)
    )

    line_surface = font.render(json_line, True, (220,220,220))
    screen.blit(line_surface, (460, 420))
    tip = font.render("Нажмите кнопку 'Копировать' или Ctrl+C", True, (180,180,180))
    screen.blit(tip, (460, 440))

    if copy_status:
        status_text = font.render(copy_status, True, (255, 220, 120))
        screen.blit(status_text, (460, 460))
        copy_status_timer += 1
        if copy_status_timer > 120:
            copy_status = ""
            copy_status_timer = 0

# ================= DRAG =======================

drag = False
drag_id = -1
drag_img = None

clock = pygame.time.Clock()
run = True

while run:
    screen.fill((50,50,60))

    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            run = False

        if e.type == pygame.MOUSEWHEEL:
            scroll -= e.y * 40
            scroll = max(scroll, 0)

        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            t = get_menu_tile(e.pos)
            if t is not None:
                drag = True
                drag_id = t
                drag_img = tiles[t][1]

        if e.type == pygame.MOUSEBUTTONUP and e.button == 1:
            if clear_button_rect.collidepoint(e.pos):
                grid = [-1]*9
                result = -1
            elif copy_button_rect.collidepoint(e.pos):
                copied, copy_status = copy_line_to_clipboard(json_line)
                copy_status_timer = 0

            elif drag:
                drag = False

                for i, rect in enumerate(grid_rects):
                    if rect.collidepoint(e.pos):
                        grid[i] = drag_id

                if result_rect.collidepoint(e.pos):
                    result = drag_id

        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_DELETE:
                grid = [-1]*9
                result = -1
            if e.key == pygame.K_c and pygame.key.get_mods() & pygame.KMOD_CTRL:
                copied, copy_status = copy_line_to_clipboard(json_line)
                copy_status_timer = 0

    # прокрутка при зажатии кнопки
    if pygame.mouse.get_pressed()[0] and scroll_up_button_rect.collidepoint(pygame.mouse.get_pos()):
        scroll -= 5
        scroll = max(scroll, 0)
    if pygame.mouse.get_pressed()[0] and scroll_down_button_rect.collidepoint(pygame.mouse.get_pos()):
        scroll += 5

    draw_menu()
    draw_scroll_button()
    draw_scroll_up_button()
    draw_grid()
    draw_json()

    if drag and drag_img:
        mx, my = pygame.mouse.get_pos()
        img = pygame.transform.smoothscale(
            drag_img, (CELL-10, CELL-10)
        )
        screen.blit(img, (mx-20, my-20))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()