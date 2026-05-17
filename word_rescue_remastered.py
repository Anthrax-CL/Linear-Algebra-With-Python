#!/usr/bin/env python3
"""
WORD RESCUE REMASTERED
======================
Terminal remake of the beloved 1992 Apogee / Redwood Games classic.
The Gruzzles stole words from every book in the world — rescue them all!

Controls:
  A / ← Arrow   Move left          D / → Arrow   Move right
  W / ↑ Arrow   Jump               SPACE         Slime a nearby Gruzzle
  ESC / Q       Quit to main menu

Rules:
  • Walk into a [?] block to collect a word.
  • A word-matching puzzle appears — pick the correct description.
  • A wrong match spawns a Gruzzle enemy.
  • Press SPACE near a Gruzzle to slime it (costs 1 slime bucket).
  • Collect mystery letters (shown at bottom) in order for a big bonus.
  • Get all words → the KEY appears → reach the EXIT to finish the level.
"""

import curses
import random
import time
import sys
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

# ══════════════════════════════════════════════════════════════════════════════
#  CONSTANTS
# ══════════════════════════════════════════════════════════════════════════════

MAP_W       = 80          # map columns (= terminal width)
MAP_H       = 14          # map rows used for gameplay
HUD_LINES   = 3           # rows 0-2 = heads-up display
GAME_TOP    = HUD_LINES   # first row of the game map on screen
TICK        = 0.08        # seconds per game tick

GRAVITY     = 1           # applied each tick if airborne
JUMP_VY     = -5          # initial jump velocity (negative = upward)
MAX_FALL    = 4           # terminal fall velocity

# ─── Colour pair IDs ──────────────────────────────────────────────────────────
C_NORMAL  = 1   # default text
C_HUD     = 2   # HUD bar
C_WALL    = 3   # '#' tiles
C_BLOCK   = 4   # word blocks [?]
C_PLAYER  = 5   # '@' player
C_GRUZZLE = 6   # 'G' enemies
C_SLIME   = 7   # slime bucket
C_KEY     = 8   # key item
C_EXIT    = 9   # exit door
C_MYSTERY = 10  # mystery letters
C_GOOD    = 11  # correct answer flash
C_BAD     = 12  # wrong answer flash
C_BOOK    = 13  # book bonus item
C_TITLE   = 14  # title screen

# ══════════════════════════════════════════════════════════════════════════════
#  WORD DATABASE
#  Each entry: (WORD, correct_description, [wrong1, wrong2, wrong3])
# ══════════════════════════════════════════════════════════════════════════════

WORD_DB = {
    1: [   # Episode 1 — Gruzzleville
        ("CAT",  "a furry pet that purrs and meows",
         ["a loyal barking pet", "a swimming scaly creature", "a flying feathered animal"]),
        ("DOG",  "a loyal pet that barks and fetches",
         ["a purring animal that climbs", "an animal with a hard shell", "a tiny buzzing insect"]),
        ("SUN",  "the giant star that warms the Earth",
         ["the rocky ball orbiting Earth", "the shiny ball seen at night", "the colour arc after rain"]),
        ("BOOK", "many pages bound together to read",
         ["a stick you write with", "a flat board you write on", "a folded paper message"]),
        ("TREE", "a tall plant with a trunk and leaves",
         ["a small colourful flower", "a flat carpet of grass", "a spiky desert plant"]),
        ("FISH", "a scaly animal that breathes underwater",
         ["a furry animal that hops on land", "a slimy legless ground animal", "a hard-shelled ocean creature"]),
        ("BIRD", "a feathered animal that lays eggs and flies",
         ["a furry gliding animal", "a scaly leaping animal", "a buzzing insect"]),
        ("RAIN", "water drops falling from dark clouds",
         ["frozen flakes falling from sky", "a rush of water in a channel", "thick grey mist"]),
    ],
    2: [   # Episode 2 — Gruzzlebad Caverns
        ("CAVE", "a dark hollow chamber inside a rock",
         ["a trench dug under a river", "a narrow road tunnel", "a hollow space inside a tree"]),
        ("GEMS", "rare sparkling precious stones",
         ["smooth pearls from the sea", "shiny metal coins", "rough chunks of iron ore"]),
        ("FROG", "a leaping green amphibian near ponds",
         ["a slow crawling brown reptile", "a tiny flying insect", "a long slippery eel"]),
        ("ECHO", "a sound that bounces back from a hard surface",
         ["a sound absorbed by soft walls", "a sound growing louder", "a sound only animals hear"]),
        ("MOSS", "soft spongy green plant on damp rocks",
         ["dry crinkly yellow lichen", "tall swaying green seaweed", "sharp thorny brown bark"]),
        ("BATS", "furry mammals that fly at night using echolocation",
         ["feathered birds that soar by day", "buzzing insects at dusk", "small rodents that leap"]),
        ("LAKE", "a large body of still fresh water",
         ["a channel of flowing salt water", "a frozen sheet of ice", "a hot-spring geyser"]),
        ("MOLE", "a small furry animal that digs underground tunnels",
         ["a tiny insect that builds mounds", "a small bird that digs nests", "a worm in soil"]),
    ],
    3: [   # Episode 3 — The Haunted House
        ("GHOST", "the spirit of a dead person that haunts places",
         ["a person in a white costume", "a trick of light on glass", "a floating round balloon"]),
        ("WITCH", "a person who practises magic and casts spells",
         ["a wise person who tells stories", "a sword-wielding warrior", "a healer who makes potions"]),
        ("BRAVE", "showing courage when facing danger",
         ["showing skill in solving puzzles", "showing speed in running away", "showing strength in lifting"]),
        ("HAUNT", "for a ghost to appear repeatedly in a place",
         ["for a person to hide in a place", "for a monster to wreck a place", "for a shadow to follow someone"]),
        ("CRYPT", "an underground vault where the dead are buried",
         ["an underground room full of gold", "an underground escape passage", "an underground prison cell"]),
        ("CURSE", "a magical spell that brings misfortune",
         ["a magical spell that grants wishes", "a magic word that opens doors", "a potion that heals wounds"]),
        ("HOWL",  "a long mournful cry made by a wolf",
         ["a short sharp bark from a dog", "a soft gentle hoot from an owl", "a quiet hiss from a snake"]),
        ("QUEST", "a long dangerous journey to seek something",
         ["a short errand to the market", "a quick race to the finish line", "a slow walk in the garden"]),
    ],
}

EPISODE_NAMES = {
    1: "GRUZZLEVILLE",
    2: "GRUZZLEBAD CAVERNS",
    3: "THE HAUNTED HOUSE",
}

# ══════════════════════════════════════════════════════════════════════════════
#  MAP TEMPLATES  (MAP_W × MAP_H each)
#  '#' solid  ' ' empty  '@' player start  'E' exit door
# ══════════════════════════════════════════════════════════════════════════════

_MAPS = [
    [   # MAP 0
        "                                                                                ",
        "  ########                    ########                    ########             ",
        "                                                                                ",
        "          ########                    ########                   ######         ",
        "                                                                                ",
        "  ######     ########     ########     ########     ########       ##           ",
        "                                                                                ",
        "      #######       ######       ######       ######       #######              ",
        "                                                                                ",
        "  ####                                                              ####        ",
        "                                                                                ",
        "################################################################################",
        "@                                                                             E ",
        "################################################################################",
    ],
    [   # MAP 1
        "                                                                                ",
        " ######                    ######                    ######                    ",
        "                                                                                ",
        "       ######                    ######                    ######               ",
        "                                                                                ",
        "  ###   ###   ###   ###   ###   ###   ###   ###   ###   ###   ###               ",
        "                                                                                ",
        "     ########       ########       ########       ########       ####           ",
        "                                                                                ",
        "  ####                                                              ####        ",
        "                                                                                ",
        "################################################################################",
        "@                                                                             E ",
        "################################################################################",
    ],
    [   # MAP 2
        "                                                                                ",
        "  ##  ##  ##  ##  ##  ##  ##  ##  ##  ##  ##  ##  ##  ##  ##  ##  ##           ",
        "                                                                                ",
        "    ##  ##  ##  ##  ##  ##  ##  ##  ##  ##  ##  ##  ##  ##  ##  ##  ##         ",
        "                                                                                ",
        "  #########    #########    #########    #########    #########                 ",
        "                                                                                ",
        "         ######        ######        ######        ######        ######         ",
        "                                                                                ",
        "  ####                                                              ####        ",
        "                                                                                ",
        "################################################################################",
        "@                                                                             E ",
        "################################################################################",
    ],
]

LEVEL_MAP_IDX = [0,1,2, 1,2,0, 2,0,1]   # 9 levels → which template


# ══════════════════════════════════════════════════════════════════════════════
#  DATA CLASSES
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class Gruzzle:
    x: int
    y: int
    dir: int = 1          # +1 right, -1 left
    move_counter: float = 0.0
    slimed: bool = False
    slime_timer: int = 0  # ticks remaining while slimed

@dataclass
class LevelState:
    map_grid: List[List[str]]       # mutable copy of the map
    words: List[Tuple]              # (WORD, correct_desc, [wrong...]) per block
    block_positions: List[Tuple[int,int]]  # (x,y) of each word block
    matched: List[bool]             # which words have been matched
    gruzzles: List[Gruzzle]
    slime_positions: List[Tuple[int,int]]
    book_positions: List[Tuple[int,int]]
    mystery_word: str
    mystery_letters: List[Tuple[int,int,str]]  # (x, y, letter)
    mystery_collected: List[bool]
    key_visible: bool
    key_pos: Tuple[int,int]
    exit_pos: Tuple[int,int]


@dataclass
class Player:
    x: int
    y: int
    vx: int = 0
    vy: int = 0
    on_ground: bool = False
    facing: int = 1       # +1 right, -1 left


@dataclass
class GameState:
    score: int = 0
    lives: int = 3
    slime: int = 5
    episode: int = 1
    level_num: int = 1    # 1-9 overall
    message: str = ""
    message_timer: int = 0


# ══════════════════════════════════════════════════════════════════════════════
#  LEVEL GENERATION
# ══════════════════════════════════════════════════════════════════════════════

def _platform_tops(grid: List[List[str]]) -> List[Tuple[int,int]]:
    """Return list of (x,y) positions that are empty but have solid below."""
    tops = []
    for y in range(MAP_H - 1):
        for x in range(MAP_W):
            if grid[y][x] == ' ' and grid[y+1][x] == '#':
                tops.append((x, y))
    return tops


def build_level(level_num: int, episode: int, gs: GameState) -> Tuple[LevelState, Player]:
    rng = random.Random(level_num * 1337 + episode * 17)

    template = _MAPS[LEVEL_MAP_IDX[level_num - 1]]
    grid: List[List[str]] = [list(row[:MAP_W].ljust(MAP_W)) for row in template]

    # Find player start & exit from template
    px, py = 1, MAP_H - 2
    exit_x, exit_y = MAP_W - 3, MAP_H - 2
    for y, row in enumerate(grid):
        for x, ch in enumerate(row):
            if ch == '@':
                px, py = x, y
                grid[y][x] = ' '
            elif ch == 'E':
                exit_x, exit_y = x, y

    player = Player(x=px, y=py)

    tops = _platform_tops(grid)
    rng.shuffle(tops)

    # Pick words for this level (4 words per level)
    ep_words = list(WORD_DB[episode])
    rng.shuffle(ep_words)
    level_words = ep_words[:4]

    # Place word blocks on platform tops (not too close to exit/start)
    block_positions: List[Tuple[int,int]] = []
    used_spots: set = set()
    candidates = [t for t in tops if t[0] > 5 and t[0] < MAP_W - 5 and t not in used_spots]
    for i, word_entry in enumerate(level_words):
        if not candidates:
            break
        pos = candidates[rng.randint(0, min(len(candidates)-1, 6))]
        candidates.remove(pos)
        used_spots.add(pos)
        block_positions.append(pos)
        grid[pos[1]][pos[0]] = '?'   # word block marker

    # Mystery word = first level word
    mystery_word = level_words[0][0] if level_words else "WORD"
    # Place mystery letters scattered around
    letter_candidates = [t for t in tops if t not in used_spots and t[0] > 3 and t[0] < MAP_W-3]
    rng.shuffle(letter_candidates)
    mystery_letters: List[Tuple[int,int,str]] = []
    for i, ch in enumerate(mystery_word):
        if i < len(letter_candidates):
            pos = letter_candidates[i]
            used_spots.add(pos)
            grid[pos[1]][pos[0]] = 'L'
            mystery_letters.append((pos[0], pos[1], ch))

    # Slime buckets (2)
    slime_positions = []
    slime_candidates = [t for t in tops if t not in used_spots and t[0] > 3]
    for _ in range(2):
        if slime_candidates:
            pos = rng.choice(slime_candidates[:10])
            slime_candidates.remove(pos)
            used_spots.add(pos)
            grid[pos[1]][pos[0]] = 'S'
            slime_positions.append(pos)

    # Books (2 for bonus points)
    book_positions = []
    book_candidates = [t for t in tops if t not in used_spots]
    for _ in range(2):
        if book_candidates:
            pos = rng.choice(book_candidates[:10])
            book_candidates.remove(pos)
            used_spots.add(pos)
            grid[pos[1]][pos[0]] = 'b'
            book_positions.append(pos)

    # Gruzzles (1-2 depending on level)
    n_gruzzles = 1 + (level_num // 4)
    gruzzles: List[Gruzzle] = []
    for _ in range(n_gruzzles):
        candidates_g = [t for t in tops if t not in used_spots and t[0] > 10 and t[0] < MAP_W-10]
        if candidates_g:
            pos = rng.choice(candidates_g[:8])
            used_spots.add(pos)
            gruzzles.append(Gruzzle(x=pos[0], y=pos[1], dir=rng.choice([-1, 1])))

    key_pos = (exit_x - 5, MAP_H - 2)

    return LevelState(
        map_grid=grid,
        words=level_words,
        block_positions=block_positions,
        matched=[False] * len(block_positions),
        gruzzles=gruzzles,
        slime_positions=slime_positions,
        book_positions=book_positions,
        mystery_word=mystery_word,
        mystery_letters=mystery_letters,
        mystery_collected=[False] * len(mystery_letters),
        key_visible=False,
        key_pos=key_pos,
        exit_pos=(exit_x, exit_y),
    ), player


# ══════════════════════════════════════════════════════════════════════════════
#  COLOUR INIT
# ══════════════════════════════════════════════════════════════════════════════

def init_colours():
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(C_NORMAL,  curses.COLOR_WHITE,   -1)
    curses.init_pair(C_HUD,     curses.COLOR_BLACK,   curses.COLOR_CYAN)
    curses.init_pair(C_WALL,    curses.COLOR_WHITE,   curses.COLOR_WHITE)
    curses.init_pair(C_BLOCK,   curses.COLOR_BLACK,   curses.COLOR_YELLOW)
    curses.init_pair(C_PLAYER,  curses.COLOR_BLACK,   curses.COLOR_GREEN)
    curses.init_pair(C_GRUZZLE, curses.COLOR_BLACK,   curses.COLOR_RED)
    curses.init_pair(C_SLIME,   curses.COLOR_BLACK,   curses.COLOR_GREEN)
    curses.init_pair(C_KEY,     curses.COLOR_BLACK,   curses.COLOR_YELLOW)
    curses.init_pair(C_EXIT,    curses.COLOR_BLACK,   curses.COLOR_MAGENTA)
    curses.init_pair(C_MYSTERY, curses.COLOR_YELLOW,  -1)
    curses.init_pair(C_GOOD,    curses.COLOR_BLACK,   curses.COLOR_GREEN)
    curses.init_pair(C_BAD,     curses.COLOR_WHITE,   curses.COLOR_RED)
    curses.init_pair(C_BOOK,    curses.COLOR_CYAN,    -1)
    curses.init_pair(C_TITLE,   curses.COLOR_YELLOW,  curses.COLOR_BLUE)


# ══════════════════════════════════════════════════════════════════════════════
#  RENDERING
# ══════════════════════════════════════════════════════════════════════════════

def render_hud(stdscr, gs: GameState, lv: LevelState):
    h, w = stdscr.getmaxyx()
    ep = ((gs.level_num - 1) // 3) + 1
    lv_in_ep = ((gs.level_num - 1) % 3) + 1
    ep_name = EPISODE_NAMES.get(ep, "???")

    # Row 0 — title bar
    title = f" WORD RESCUE REMASTERED  |  {ep_name}  Ep{ep} Lv{lv_in_ep}  |  Score: {gs.score:06d}  |  Lives: {'@' * gs.lives}  |  Slime: {gs.slime} "
    try:
        stdscr.addstr(0, 0, title[:w-1].ljust(w-1), curses.color_pair(C_HUD) | curses.A_BOLD)
    except curses.error:
        pass

    # Row 1 — mystery word progress
    mystery_prog = ""
    for i, ch in enumerate(lv.mystery_word):
        if i < len(lv.mystery_collected) and lv.mystery_collected[i]:
            mystery_prog += ch
        else:
            mystery_prog += "_"
    words_left = sum(1 for m in lv.matched if not m)
    status = f" Mystery: {' '.join(mystery_prog)}   Words left: {words_left}   {'KEY FOUND! Reach the EXIT!' if lv.key_visible else ''}"
    try:
        stdscr.addstr(1, 0, status[:w-1], curses.color_pair(C_MYSTERY) | curses.A_BOLD)
    except curses.error:
        pass

    # Row 2 — separator + message
    sep = "─" * (w - 1)
    try:
        stdscr.addstr(2, 0, sep[:w-1], curses.color_pair(C_NORMAL))
    except curses.error:
        pass
    if gs.message and gs.message_timer > 0:
        msg = f"  {gs.message}"
        try:
            color = C_GOOD if "[+]" in gs.message else C_BAD if "[!]" in gs.message else C_NORMAL
            stdscr.addstr(2, 0, msg[:w-1], curses.color_pair(color) | curses.A_BOLD)
        except curses.error:
            pass


def render_map(stdscr, player: Player, lv: LevelState):
    h, w = stdscr.getmaxyx()
    grid = lv.map_grid

    # Build a display overlay: start from the map grid
    for row in range(MAP_H):
        screen_row = GAME_TOP + row
        if screen_row >= h:
            break
        for col in range(MAP_W):
            if col >= w - 1:
                break
            ch = grid[row][col]
            if ch == '#':
                attr = curses.color_pair(C_WALL)
                draw_ch = ' '
            elif ch == '?':
                attr = curses.color_pair(C_BLOCK) | curses.A_BOLD
                draw_ch = '?'
            elif ch == 'S':
                attr = curses.color_pair(C_SLIME) | curses.A_BOLD
                draw_ch = 's'
            elif ch == 'b':
                attr = curses.color_pair(C_BOOK) | curses.A_BOLD
                draw_ch = chr(0x03D2) if False else 'B'   # book icon
            elif ch == 'L':
                attr = curses.color_pair(C_MYSTERY) | curses.A_BOLD
                draw_ch = '*'
            elif ch == 'K':
                attr = curses.color_pair(C_KEY) | curses.A_BOLD
                draw_ch = 'K'
            elif ch == 'E':
                attr = curses.color_pair(C_EXIT) | curses.A_BOLD
                draw_ch = 'E'
            else:
                attr = curses.color_pair(C_NORMAL)
                draw_ch = ch if ch != ' ' else ' '
            try:
                stdscr.addch(screen_row, col, draw_ch, attr)
            except curses.error:
                pass

    # Draw Gruzzles
    for g in lv.gruzzles:
        sr = GAME_TOP + g.y
        if 0 <= sr < h and 0 <= g.x < w-1:
            sym = 'G' if not g.slimed else '~'
            attr = curses.color_pair(C_GRUZZLE) | curses.A_BOLD
            try:
                stdscr.addch(sr, g.x, sym, attr)
            except curses.error:
                pass

    # Draw key if visible
    if lv.key_visible:
        kx, ky = lv.key_pos
        sr = GAME_TOP + ky
        if 0 <= sr < h and 0 <= kx < w-1:
            try:
                stdscr.addch(sr, kx, 'K', curses.color_pair(C_KEY) | curses.A_BOLD)
            except curses.error:
                pass

    # Draw player
    sr = GAME_TOP + player.y
    if 0 <= sr < h and 0 <= player.x < w-1:
        try:
            stdscr.addch(sr, player.x, '@', curses.color_pair(C_PLAYER) | curses.A_BOLD)
        except curses.error:
            pass


# ══════════════════════════════════════════════════════════════════════════════
#  PHYSICS
# ══════════════════════════════════════════════════════════════════════════════

def is_solid(grid: List[List[str]], x: int, y: int) -> bool:
    if y < 0 or y >= MAP_H or x < 0 or x >= MAP_W:
        return True   # out-of-bounds = solid
    return grid[y][x] == '#'


def update_physics(player: Player, grid: List[List[str]]):
    # Horizontal movement
    new_x = player.x + player.vx
    if 0 <= new_x < MAP_W and not is_solid(grid, new_x, player.y):
        player.x = new_x
    player.vx = 0

    # Gravity
    if not player.on_ground:
        player.vy = min(player.vy + GRAVITY, MAX_FALL)

    # Vertical movement
    new_y = player.y + (1 if player.vy > 0 else (-1 if player.vy < 0 else 0))
    if player.vy != 0:
        if is_solid(grid, player.x, new_y):
            if player.vy > 0:   # landing
                player.on_ground = True
            player.vy = 0
        else:
            player.y = new_y
            player.on_ground = is_solid(grid, player.x, player.y + 1)
    else:
        player.on_ground = is_solid(grid, player.x, player.y + 1)


# ══════════════════════════════════════════════════════════════════════════════
#  WORD MATCHING MINI-GAME
# ══════════════════════════════════════════════════════════════════════════════

def run_word_puzzle(stdscr, word_entry: Tuple, gs: GameState) -> bool:
    """Shows a full-screen puzzle. Returns True if correct answer given."""
    word, correct, wrongs = word_entry
    options = [(correct, True)] + [(w, False) for w in wrongs]
    random.shuffle(options)

    h, w = stdscr.getmaxyx()
    stdscr.clear()

    # Box
    box_w = min(70, w - 4)
    box_h = 14
    start_x = (w - box_w) // 2
    start_y = (h - box_h) // 2

    def draw_box():
        stdscr.clear()
        # Title bar
        try:
            banner = " WORD RESCUE — MATCH THE WORD! "
            stdscr.addstr(start_y, start_x, "╔" + "═" * (box_w-2) + "╗",
                          curses.color_pair(C_TITLE) | curses.A_BOLD)
            stdscr.addstr(start_y+1, start_x, "║" + banner.center(box_w-2) + "║",
                          curses.color_pair(C_TITLE) | curses.A_BOLD)
            stdscr.addstr(start_y+2, start_x, "╠" + "═" * (box_w-2) + "╣",
                          curses.color_pair(C_TITLE) | curses.A_BOLD)
        except curses.error:
            pass

        # Word display
        word_line = f"  You found the word:  {word}  "
        try:
            stdscr.addstr(start_y+3, start_x, "║" + word_line.ljust(box_w-2)[:box_w-2] + "║",
                          curses.color_pair(C_BLOCK) | curses.A_BOLD)
            stdscr.addstr(start_y+4, start_x, "║" + "".ljust(box_w-2) + "║",
                          curses.color_pair(C_NORMAL))
            stdscr.addstr(start_y+5, start_x, "║" + "  Which picture matches?".ljust(box_w-2)[:box_w-2] + "║",
                          curses.color_pair(C_NORMAL))
            stdscr.addstr(start_y+6, start_x, "║" + "".ljust(box_w-2) + "║",
                          curses.color_pair(C_NORMAL))
        except curses.error:
            pass

        # Options
        for i, (desc, _) in enumerate(options):
            line = f"  [{i+1}]  {desc}"
            try:
                stdscr.addstr(start_y+7+i, start_x, "║" + line.ljust(box_w-2)[:box_w-2] + "║",
                              curses.color_pair(C_NORMAL))
            except curses.error:
                pass

        # Bottom
        try:
            stdscr.addstr(start_y+11, start_x, "║" + "".ljust(box_w-2) + "║",
                          curses.color_pair(C_NORMAL))
            prompt = "  Press 1, 2, 3 or 4 to choose:"
            stdscr.addstr(start_y+12, start_x, "║" + prompt.ljust(box_w-2)[:box_w-2] + "║",
                          curses.color_pair(C_NORMAL) | curses.A_BOLD)
            stdscr.addstr(start_y+13, start_x, "╚" + "═" * (box_w-2) + "╝",
                          curses.color_pair(C_TITLE) | curses.A_BOLD)
        except curses.error:
            pass

        stdscr.refresh()

    draw_box()
    curses.cbreak()
    stdscr.nodelay(False)

    while True:
        key = stdscr.getch()
        if key in (ord('1'), ord('2'), ord('3'), ord('4')):
            idx = key - ord('1')
            if idx < len(options):
                _, is_correct = options[idx]
                # Flash feedback
                result_line = "  ✓ CORRECT! Great job!" if is_correct else f"  ✗ Wrong! It was: {correct}"
                color = C_GOOD if is_correct else C_BAD
                try:
                    stdscr.addstr(start_y+12, start_x,
                                  "║" + result_line.ljust(box_w-2)[:box_w-2] + "║",
                                  curses.color_pair(color) | curses.A_BOLD)
                    stdscr.refresh()
                except curses.error:
                    pass
                time.sleep(1.0)
                stdscr.nodelay(True)
                return is_correct
        elif key in (27, ord('q'), ord('Q')):
            stdscr.nodelay(True)
            return False


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN GAME LOOP
# ══════════════════════════════════════════════════════════════════════════════

def play_level(stdscr, gs: GameState) -> str:
    """
    Runs one level. Returns:
      'win'   — reached the exit after all words matched
      'die'   — touched a Gruzzle with no lives left
      'quit'  — player pressed ESC
    """
    ep = ((gs.level_num - 1) // 3) + 1
    lv, player = build_level(gs.level_num, ep, gs)

    stdscr.nodelay(True)
    curses.cbreak()

    has_key = False    # player is carrying the key

    while True:
        t0 = time.monotonic()

        # ── Input ──────────────────────────────────────────────────────────
        key = stdscr.getch()

        move_x = 0
        if key in (ord('a'), ord('A'), curses.KEY_LEFT):
            move_x = -1
            player.facing = -1
        elif key in (ord('d'), ord('D'), curses.KEY_RIGHT):
            move_x = 1
            player.facing = 1
        elif key in (ord('w'), ord('W'), curses.KEY_UP):
            if player.on_ground:
                player.vy = JUMP_VY
                player.on_ground = False
        elif key == ord(' '):
            # Use slime on adjacent Gruzzle
            if gs.slime > 0:
                for g in lv.gruzzles:
                    if not g.slimed and abs(g.x - player.x) <= 2 and abs(g.y - player.y) <= 1:
                        g.slimed = True
                        g.slime_timer = 80
                        gs.slime -= 1
                        gs.score += 50
                        gs.message = "[+] Gruzzle slimed! +50"
                        gs.message_timer = 40
                        break
                else:
                    gs.message = "[!] No Gruzzle nearby!"
                    gs.message_timer = 20
            else:
                gs.message = "[!] No slime left!"
                gs.message_timer = 20
        elif key in (27, ord('q'), ord('Q')):
            return 'quit'

        player.vx = move_x

        # ── Physics ─────────────────────────────────────────────────────────
        update_physics(player, lv.map_grid)

        # ── Check tile under player ─────────────────────────────────────────
        px, py = player.x, player.y
        tile = lv.map_grid[py][px] if 0 <= py < MAP_H else ' '

        # Word block
        if tile == '?':
            # Find which word block this is
            try:
                idx = lv.block_positions.index((px, py))
            except ValueError:
                idx = -1
            if idx >= 0 and not lv.matched[idx]:
                lv.map_grid[py][px] = ' '
                # Run puzzle
                stdscr.nodelay(False)
                correct = run_word_puzzle(stdscr, lv.words[idx], gs)
                stdscr.nodelay(True)
                if correct:
                    lv.matched[idx] = True
                    gs.score += 100
                    gs.message = f"[+] {lv.words[idx][0]} matched! +100"
                    gs.message_timer = 40
                    # Check if all words matched → reveal key
                    if all(lv.matched):
                        lv.key_visible = True
                        gs.message = "[+] All words rescued! Find the KEY!"
                        gs.message_timer = 60
                else:
                    # Wrong answer → spawn a Gruzzle near player
                    gx = min(max(px + random.choice([-3, 3]), 1), MAP_W - 2)
                    lv.gruzzles.append(Gruzzle(x=gx, y=py, dir=random.choice([-1, 1])))
                    lv.map_grid[py][px] = '?'   # put block back
                    gs.message = "[!] Wrong! A Gruzzle appeared!"
                    gs.message_timer = 40

        # Slime bucket
        elif tile == 'S':
            if (px, py) in lv.slime_positions:
                lv.slime_positions.remove((px, py))
                lv.map_grid[py][px] = ' '
                gs.slime = min(gs.slime + 3, 10)
                gs.score += 25
                gs.message = "[+] Slime bucket! +3 slime, +25"
                gs.message_timer = 30

        # Book
        elif tile == 'b':
            if (px, py) in lv.book_positions:
                lv.book_positions.remove((px, py))
                lv.map_grid[py][px] = ' '
                gs.score += 75
                gs.message = "[+] Book rescued! +75"
                gs.message_timer = 30

        # Mystery letter
        elif tile == 'L':
            # Find next uncollected letter
            next_idx = next((i for i, c in enumerate(lv.mystery_collected) if not c), None)
            if next_idx is not None:
                mx, my, mch = lv.mystery_letters[next_idx]
                if (px, py) == (mx, my):
                    lv.mystery_collected[next_idx] = True
                    lv.map_grid[py][px] = ' '
                    gs.message = f"[+] Mystery letter '{mch}'!"
                    gs.message_timer = 25
                    # Full mystery word?
                    if all(lv.mystery_collected):
                        gs.score += 300
                        gs.slime = min(gs.slime + 5, 10)
                        gs.message = f"[+] MYSTERY WORD COMPLETE! +300 & slime refill!"
                        gs.message_timer = 60
                else:
                    gs.message = f"[!] Collect letters in order! Next: '{mch}'"
                    gs.message_timer = 25
            # Remove letter tile so it doesn't keep triggering
            lv.map_grid[py][px] = ' '

        # Key
        elif tile == 'K' or (lv.key_visible and (px, py) == lv.key_pos):
            if lv.key_visible and not has_key:
                has_key = True
                lv.key_visible = False
                lv.map_grid[lv.key_pos[1]][lv.key_pos[0]] = ' '
                gs.score += 150
                gs.message = "[+] KEY collected! Find the EXIT! +150"
                gs.message_timer = 50

        # Exit
        elif tile == 'E':
            if has_key or all(lv.matched):
                gs.score += 200 + gs.lives * 50
                return 'win'
            else:
                gs.message = "[!] Find all words and the KEY first!"
                gs.message_timer = 30

        # ── Gruzzle updates ─────────────────────────────────────────────────
        for g in lv.gruzzles:
            if g.slimed:
                g.slime_timer -= 1
                if g.slime_timer <= 0:
                    g.slimed = False
                continue

            # Simple patrol AI: move left/right, reverse at walls or edges
            g.move_counter += 0.35
            if g.move_counter >= 1.0:
                g.move_counter = 0.0
                nx = g.x + g.dir
                if (nx < 0 or nx >= MAP_W or
                        is_solid(lv.map_grid, nx, g.y) or
                        not is_solid(lv.map_grid, nx, g.y + 1)):
                    g.dir *= -1
                else:
                    g.x = nx

            # Collision with player
            if abs(g.x - player.x) <= 1 and abs(g.y - player.y) <= 1:
                gs.lives -= 1
                # Flash
                try:
                    stdscr.addstr(GAME_TOP + player.y, player.x, 'X',
                                  curses.color_pair(C_BAD) | curses.A_BOLD)
                    stdscr.refresh()
                    time.sleep(0.5)
                except curses.error:
                    pass
                if gs.lives <= 0:
                    return 'die'
                # Respawn player at start
                player.x, player.y = 1, MAP_H - 2
                player.vy = 0
                gs.message = "[!] Caught by a Gruzzle! Lives left: " + "@" * gs.lives
                gs.message_timer = 50

        # ── Message timer ───────────────────────────────────────────────────
        if gs.message_timer > 0:
            gs.message_timer -= 1
        else:
            gs.message = ""

        # ── Render ──────────────────────────────────────────────────────────
        stdscr.erase()
        render_hud(stdscr, gs, lv)
        render_map(stdscr, player, lv)
        stdscr.refresh()

        # ── Tick timing ─────────────────────────────────────────────────────
        elapsed = time.monotonic() - t0
        sleep_t = max(0.0, TICK - elapsed)
        time.sleep(sleep_t)


# ══════════════════════════════════════════════════════════════════════════════
#  TITLE SCREEN & MENUS
# ══════════════════════════════════════════════════════════════════════════════

TITLE_ART = r"""
 __        __           _   ____
 \ \      / /__  _ __ __| | |  _ \ ___  ___  ___ _   _  ___
  \ \ /\ / / _ \| '__/ _` | | |_) / _ \/ __|/ __| | | |/ _ \
   \ V  V / (_) | | | (_| | |  _ <  __/\__ \ (__| |_| |  __/
    \_/\_/ \___/|_|  \__,_| |_| \_\___||___/\___|\__,_|\___|

        R E M A S T E R E D   ( 2 0 2 4 )
"""

def show_title(stdscr):
    h, w = stdscr.getmaxyx()
    stdscr.clear()
    lines = TITLE_ART.strip("\n").split("\n")
    start_y = max(0, (h - len(lines) - 8) // 2)
    for i, line in enumerate(lines):
        x = max(0, (w - len(line)) // 2)
        try:
            stdscr.addstr(start_y + i, x, line[:w-1],
                          curses.color_pair(C_TITLE) | curses.A_BOLD)
        except curses.error:
            pass

    credits = "Based on the 1992 classic by Karen Crowther / Apogee Software"
    story = [
        "",
        "The Gruzzles cannot read — so they stole every word",
        "from every book in the world!",
        "",
        "Help BENNY the Bookworm rescue the stolen words,",
        "match them with their meanings, and slime the Gruzzles!",
    ]
    y = start_y + len(lines) + 1
    try:
        stdscr.addstr(y, max(0,(w-len(credits))//2), credits[:w-1],
                      curses.color_pair(C_BOOK))
    except curses.error:
        pass
    for i, line in enumerate(story):
        try:
            stdscr.addstr(y+1+i, max(0,(w-len(line))//2), line[:w-1],
                          curses.color_pair(C_NORMAL))
        except curses.error:
            pass

    menu_y = y + len(story) + 2
    menu = ["[S] Start Game", "[H] How to Play", "[Q] Quit"]
    for i, item in enumerate(menu):
        try:
            stdscr.addstr(menu_y+i, max(0,(w-len(item))//2), item[:w-1],
                          curses.color_pair(C_HUD) | curses.A_BOLD)
        except curses.error:
            pass
    stdscr.refresh()


def show_help(stdscr):
    h, w = stdscr.getmaxyx()
    stdscr.clear()
    lines = [
        "═" * 60,
        "           HOW TO PLAY  —  WORD RESCUE REMASTERED",
        "═" * 60,
        "",
        "  A / ←   Move left          D / →   Move right",
        "  W / ↑   Jump               SPACE   Slime a Gruzzle",
        "  ESC     Quit to menu",
        "",
        "  [?]  Walk into a word block to reveal a word.",
        "       A puzzle appears — pick the correct description!",
        "",
        "  G    Gruzzles patrol the level. Touch one = lose a life!",
        "       Press SPACE near a Gruzzle to dump slime on it.",
        "",
        "  *    Collect the mystery letters in ORDER for a big bonus.",
        "  s    Slime bucket — refills your slime supply.",
        "  B    Book — bonus points!",
        "",
        "  Match ALL words → KEY appears → reach EXIT to finish!",
        "",
        "═" * 60,
        "           Press any key to return to the menu…",
        "═" * 60,
    ]
    start_y = max(0, (h - len(lines)) // 2)
    for i, line in enumerate(lines):
        try:
            x = max(0, (w - len(line)) // 2)
            stdscr.addstr(start_y+i, x, line[:w-1], curses.color_pair(C_NORMAL))
        except curses.error:
            pass
    stdscr.refresh()
    stdscr.nodelay(False)
    stdscr.getch()
    stdscr.nodelay(True)


def show_level_intro(stdscr, gs: GameState):
    ep = ((gs.level_num - 1) // 3) + 1
    lv_in_ep = ((gs.level_num - 1) % 3) + 1
    ep_name = EPISODE_NAMES.get(ep, "???")
    h, w = stdscr.getmaxyx()
    stdscr.clear()
    lines = [
        "",
        f"  EPISODE {ep}:  {ep_name}",
        f"  Level {lv_in_ep} of 3",
        "",
        f"  Score: {gs.score:06d}   Lives: {'@' * gs.lives}   Slime: {gs.slime}",
        "",
        "  Find all the stolen words and match them!",
        "  Watch out for Gruzzles!",
        "",
        "  Press any key to start…",
    ]
    y = max(0, (h - len(lines)) // 2)
    for i, line in enumerate(lines):
        try:
            stdscr.addstr(y+i, 2, line[:w-3], curses.color_pair(C_TITLE) | curses.A_BOLD)
        except curses.error:
            pass
    stdscr.refresh()
    stdscr.nodelay(False)
    stdscr.getch()
    stdscr.nodelay(True)


def show_game_over(stdscr, gs: GameState):
    h, w = stdscr.getmaxyx()
    stdscr.clear()
    lines = [
        "",
        " ██████╗  █████╗ ███╗   ███╗███████╗",
        "██╔════╝ ██╔══██╗████╗ ████║██╔════╝",
        "██║  ███╗███████║██╔████╔██║█████╗  ",
        "██║   ██║██╔══██║██║╚██╔╝██║██╔══╝  ",
        "╚██████╔╝██║  ██║██║ ╚═╝ ██║███████╗",
        " ╚═════╝ ╚═╝  ╚═╝╚═╝     ╚═╝╚══════╝",
        "        ██████╗ ██╗   ██╗███████╗██████╗ ",
        "       ██╔═══██╗██║   ██║██╔════╝██╔══██╗",
        "       ██║   ██║██║   ██║█████╗  ██████╔╝",
        "       ██║   ██║╚██╗ ██╔╝██╔══╝  ██╔══██╗",
        "       ╚██████╔╝ ╚████╔╝ ███████╗██║  ██║",
        "        ╚═════╝   ╚═══╝  ╚══════╝╚═╝  ╚═╝",
        "",
        f"  The Gruzzles won this time…   Final score: {gs.score:06d}",
        "",
        "  Press any key to return to the main menu.",
    ]
    y = max(0, (h - len(lines)) // 2)
    for i, line in enumerate(lines):
        try:
            stdscr.addstr(y+i, max(0,(w-len(line))//2), line[:w-1],
                          curses.color_pair(C_BAD) | curses.A_BOLD)
        except curses.error:
            pass
    stdscr.refresh()
    stdscr.nodelay(False)
    stdscr.getch()
    stdscr.nodelay(True)


def show_victory(stdscr, gs: GameState):
    h, w = stdscr.getmaxyx()
    stdscr.clear()
    lines = [
        "",
        " __   ______  _   _  __        _____ _   _ _ ",
        " \\ \\ / / __ \\| | | | \\ \\      / /_ _| \\ | | |",
        "  \\ V / |  | | | | |  \\ \\ /\\ / / | ||  \\| | |",
        "   | || |  | | |_| |   \\ V  V /  | || |\\  |_|",
        "   |_| \\____/ \\___/     \\_/\\_/  |___|_| \\_(_)",
        "",
        "  All words have been rescued from the Gruzzles!",
        "  Benny the Bookworm can finally put them back in the books!",
        "",
        f"  FINAL SCORE:  {gs.score:06d}",
        "",
        "  Thanks for playing  WORD RESCUE REMASTERED!",
        "",
        "  Press any key to return to the main menu.",
    ]
    y = max(0, (h - len(lines)) // 2)
    for i, line in enumerate(lines):
        try:
            stdscr.addstr(y+i, max(0,(w-len(line))//2), line[:w-1],
                          curses.color_pair(C_GOOD) | curses.A_BOLD)
        except curses.error:
            pass
    stdscr.refresh()
    stdscr.nodelay(False)
    stdscr.getch()
    stdscr.nodelay(True)


def show_level_clear(stdscr, gs: GameState):
    h, w = stdscr.getmaxyx()
    stdscr.clear()
    lines = [
        "",
        "  ★  LEVEL COMPLETE!  ★",
        "",
        f"  Score so far: {gs.score:06d}",
        f"  Lives: {'@' * gs.lives}",
        f"  Slime: {gs.slime}",
        "",
        "  Press any key for the next level…",
    ]
    y = max(0, (h - len(lines)) // 2)
    for i, line in enumerate(lines):
        try:
            stdscr.addstr(y+i, max(0,(w-len(line))//2), line[:w-1],
                          curses.color_pair(C_GOOD) | curses.A_BOLD)
        except curses.error:
            pass
    stdscr.refresh()
    stdscr.nodelay(False)
    stdscr.getch()
    stdscr.nodelay(True)


# ══════════════════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

def main(stdscr):
    curses.curs_set(0)
    curses.cbreak()
    stdscr.keypad(True)
    stdscr.nodelay(True)
    init_colours()

    TOTAL_LEVELS = 9

    while True:   # main menu loop
        show_title(stdscr)
        stdscr.nodelay(False)
        key = stdscr.getch()
        stdscr.nodelay(True)

        if key in (ord('q'), ord('Q'), 27):
            break
        elif key in (ord('h'), ord('H')):
            show_help(stdscr)
            continue
        elif key not in (ord('s'), ord('S')):
            continue

        # Start a new game
        gs = GameState()

        for level_num in range(1, TOTAL_LEVELS + 1):
            gs.level_num = level_num
            show_level_intro(stdscr, gs)

            result = play_level(stdscr, gs)

            if result == 'quit':
                break
            elif result == 'die':
                show_game_over(stdscr, gs)
                break
            elif result == 'win':
                if level_num == TOTAL_LEVELS:
                    show_victory(stdscr, gs)
                else:
                    show_level_clear(stdscr, gs)
        # back to main menu


def run():
    """Entry point — wraps curses.wrapper for clean terminal restore."""
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        pass
    print("\nThanks for playing Word Rescue Remastered!")


if __name__ == "__main__":
    run()
