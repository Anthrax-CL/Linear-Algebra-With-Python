"""
WORLD RESCUE REMASTERED
========================
An interactive linear algebra adventure game.
Solve matrix missions to save the world from Dr. Chaos!

Usage: python3 world_rescue_remastered.py
"""

import random
import sys
import time
import os

# ---------------------------------------------------------------------------
# Terminal colours (colorama is available on this machine)
# ---------------------------------------------------------------------------
try:
    from colorama import Fore, Back, Style, init as _cinit
    _cinit(autoreset=True)
    RED     = Fore.RED
    GREEN   = Fore.GREEN
    YELLOW  = Fore.YELLOW
    CYAN    = Fore.CYAN
    MAGENTA = Fore.MAGENTA
    BLUE    = Fore.BLUE
    WHITE   = Fore.WHITE
    BOLD    = Style.BRIGHT
    RESET   = Style.RESET_ALL
    BG_RED  = Back.RED
    BG_GREEN = Back.GREEN
except ImportError:
    RED = GREEN = YELLOW = CYAN = MAGENTA = BLUE = WHITE = ""
    BOLD = RESET = BG_RED = BG_GREEN = ""

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def clear():
    os.system("cls" if os.name == "nt" else "clear")

def slow_print(text, delay=0.025, end="\n"):
    for ch in text:
        sys.stdout.write(ch)
        sys.stdout.flush()
        time.sleep(delay)
    sys.stdout.write(end)

def header(title: str, color=CYAN):
    width = 60
    print(color + BOLD + "=" * width)
    print(title.center(width))
    print("=" * width + RESET)

def press_enter():
    input(YELLOW + "\n  [Press ENTER to continue]" + RESET)

def pause(sec=1.0):
    time.sleep(sec)

def ask_float(prompt: str) -> float:
    """Prompt until the user enters a valid number."""
    while True:
        try:
            raw = input(prompt).strip()
            return float(raw)
        except ValueError:
            print(RED + "  ✗ Enter a numeric value (e.g. 3 or -2.5)." + RESET)

def close_enough(got: float, expected: float, tol=0.05) -> bool:
    if abs(expected) < 1e-9:
        return abs(got) < tol
    return abs(got - expected) / abs(expected) < tol

# ---------------------------------------------------------------------------
# Linear-algebra helpers (pure Python + standard math)
# ---------------------------------------------------------------------------

def det2(a, b, c, d):
    return a * d - b * c

def solve2x2(a, b, e, c, d, f):
    """Solve [[a,b],[c,d]] * [x,y] = [e,f] via Cramer's rule."""
    D  = det2(a, b, c, d)
    Dx = det2(e, b, f, d)
    Dy = det2(a, e, c, f)
    return Dx / D, Dy / D

def matmul2(A, B):
    """2×2 matrix multiply."""
    return [
        [A[0][0]*B[0][0] + A[0][1]*B[1][0],
         A[0][0]*B[0][1] + A[0][1]*B[1][1]],
        [A[1][0]*B[0][0] + A[1][1]*B[1][0],
         A[1][0]*B[0][1] + A[1][1]*B[1][1]],
    ]

def det3(M):
    a,b,c = M[0]; d,e,f = M[1]; g,h,i_ = M[2]
    return a*(e*i_-f*h) - b*(d*i_-f*g) + c*(d*h-e*g)

def trace2(A):
    return A[0][0] + A[1][1]

def eigen2(A):
    """Eigenvalues of a 2×2 matrix via characteristic polynomial."""
    t = trace2(A)
    d = det2(A[0][0], A[0][1], A[1][0], A[1][1])
    disc = t*t - 4*d
    import math
    if disc < 0:
        return None, None
    sq = math.sqrt(disc)
    return (t + sq) / 2, (t - sq) / 2

# ---------------------------------------------------------------------------
# Problem generators — each returns (description_lines, answer, hint)
# ---------------------------------------------------------------------------

def gen_system_2x2():
    """Mission 1: solve a 2×2 linear system."""
    while True:
        a = random.randint(-5, 5)
        b = random.randint(-5, 5)
        c = random.randint(-5, 5)
        d = random.randint(-5, 5)
        D = det2(a, b, c, d)
        if abs(D) < 1e-9:
            continue
        x = random.randint(-4, 4)
        y = random.randint(-4, 4)
        e = a*x + b*y
        f = c*x + d*y
        desc = [
            f"  Solve the system:",
            f"    {a:+}x  {b:+}y  =  {e}",
            f"    {c:+}x  {d:+}y  =  {f}",
            f"",
            f"  Enter the value of  x:",
        ]
        hint = (
            f"Use Cramer's rule:  x = det([e,b; f,d]) / det([a,b; c,d])\n"
            f"  det = {D},  det_x = {det2(e,b,f,d)}"
        )
        return desc, float(x), float(y), hint

def gen_determinant_2x2():
    """Mission 2: compute a 2×2 determinant."""
    a = random.randint(-6, 6)
    b = random.randint(-6, 6)
    c = random.randint(-6, 6)
    d = random.randint(-6, 6)
    ans = det2(a, b, c, d)
    desc = [
        f"  Compute the determinant of the matrix:",
        f"    | {a:3}  {b:3} |",
        f"    | {c:3}  {d:3} |",
        f"",
        f"  det(A) =",
    ]
    hint = f"det = a·d − b·c = {a}·{d} − ({b})·({c}) = {a*d} − {b*c}"
    return desc, float(ans), hint

def gen_matrix_product():
    """Mission 3: one entry of a 2×2 matrix product."""
    A = [[random.randint(-3, 3) for _ in range(2)] for _ in range(2)]
    B = [[random.randint(-3, 3) for _ in range(2)] for _ in range(2)]
    C = matmul2(A, B)
    r, col = random.randint(0,1), random.randint(0,1)
    ans = C[r][col]
    rn, cn = r+1, col+1
    desc = [
        "  Compute  C = A · B  and find entry  C[{},{}]:".format(rn, cn),
        "    A = [ [{}, {}], [{}, {}] ]".format(A[0][0],A[0][1],A[1][0],A[1][1]),
        "    B = [ [{}, {}], [{}, {}] ]".format(B[0][0],B[0][1],B[1][0],B[1][1]),
        "",
        "  C[{},{}] =".format(rn, cn),
    ]
    row_vals = A[r]
    col_vals = [B[0][col], B[1][col]]
    hint = ("Row {} of A · Col {} of B = {}·{} + {}·{} = {}".format(
        rn, cn,
        row_vals[0], col_vals[0],
        row_vals[1], col_vals[1],
        ans))
    return desc, float(ans), hint

def gen_trace():
    """Mission 4: trace of a 2×2 matrix."""
    A = [[random.randint(-8, 8) for _ in range(2)] for _ in range(2)]
    ans = trace2(A)
    desc = [
        "  Find the  trace  of:",
        "    [ [{}, {}], [{}, {}] ]".format(A[0][0],A[0][1],A[1][0],A[1][1]),
        "",
        "  tr(A) =",
    ]
    hint = "trace = sum of diagonal elements = {} + {} = {}".format(
        A[0][0], A[1][1], ans)
    return desc, float(ans), hint

def gen_eigenvalue():
    """Mission 5: larger eigenvalue of a 2×2 symmetric matrix."""
    while True:
        a = random.randint(-5, 5)
        b = random.randint(-3, 3)
        A = [[a, b], [b, a + random.randint(0,4)]]
        lam1, lam2 = eigen2(A)
        if lam1 is None:
            continue
        ans = max(lam1, lam2)
        desc = [
            "  Find the LARGER eigenvalue of:",
            "    [ [{}, {}], [{}, {}] ]".format(A[0][0],A[0][1],A[1][0],A[1][1]),
            "",
            "  λ_max =",
        ]
        t = trace2(A)
        d = det2(A[0][0],A[0][1],A[1][0],A[1][1])
        hint = (
            "Characteristic eqn: λ² − tr·λ + det = 0\n"
            "  tr = {}, det = {}\n"
            "  λ = (tr ± √(tr²−4·det)) / 2".format(t, d)
        )
        return desc, round(ans, 4), hint

# ---------------------------------------------------------------------------
# Mission definitions
# ---------------------------------------------------------------------------

MISSIONS = [
    {
        "id": 1,
        "name": "POWER GRID",
        "location": "New York City",
        "story": (
            "The city's power grid is controlled by a linear system.\n"
            "Dr. Chaos scrambled the parameters — solve them to restore power!"
        ),
        "generator": "system2x2",
        "answer_label": "x",
        "second_part": True,   # system returns (x, y)
        "win_msg": "Power restored! Times Square lights up again.",
    },
    {
        "id": 2,
        "name": "VAULT DOOR",
        "location": "Swiss Bank, Geneva",
        "story": (
            "The vault holding the world's gold reserve is locked.\n"
            "The combination is the determinant of a matrix Dr. Chaos left behind."
        ),
        "generator": "det2x2",
        "win_msg": "Vault opened! The gold is safe.",
    },
    {
        "id": 3,
        "name": "SATELLITE ARRAY",
        "location": "Cape Canaveral",
        "story": (
            "Satellite re-alignment requires matrix multiplication.\n"
            "Calculate the correct entry to aim the dish."
        ),
        "generator": "matprod",
        "win_msg": "Satellites aligned! Global comms restored.",
    },
    {
        "id": 4,
        "name": "NEURAL FIREWALL",
        "location": "Silicon Valley HQ",
        "story": (
            "Dr. Chaos's AI uses the trace of a matrix as its unlock code.\n"
            "Compute the trace to gain root access!"
        ),
        "generator": "trace",
        "win_msg": "Firewall breached! AI neutralised.",
    },
    {
        "id": 5,
        "name": "FINAL BOSS — DR. CHAOS",
        "location": "Secret Bunker",
        "story": (
            "Dr. Chaos's doomsday device oscillates at the dominant eigenvalue\n"
            "of its control matrix.  Compute it to set the jamming frequency!"
        ),
        "generator": "eigen",
        "win_msg": "Device jammed! Dr. Chaos is defeated. THE WORLD IS SAVED!",
    },
]

# ---------------------------------------------------------------------------
# ASCII art
# ---------------------------------------------------------------------------

LOGO = r"""
  ██╗    ██╗ ██████╗ ██████╗ ██╗     ██████╗
  ██║    ██║██╔═══██╗██╔══██╗██║     ██╔══██╗
  ██║ █╗ ██║██║   ██║██████╔╝██║     ██║  ██║
  ██║███╗██║██║   ██║██╔══██╗██║     ██║  ██║
  ╚███╔███╔╝╚██████╔╝██║  ██║███████╗██████╔╝
   ╚══╝╚══╝  ╚═════╝ ╚═╝  ╚═╝╚══════╝╚═════╝
       ██████╗ ███████╗███████╗ ██████╗██╗   ██╗███████╗
       ██╔══██╗██╔════╝██╔════╝██╔════╝██║   ██║██╔════╝
       ██████╔╝█████╗  ███████╗██║     ██║   ██║█████╗
       ██╔══██╗██╔══╝  ╚════██║██║     ██║   ██║██╔══╝
       ██║  ██║███████╗███████║╚██████╗╚██████╔╝███████╗
       ╚═╝  ╚═╝╚══════╝╚══════╝ ╚═════╝ ╚═════╝ ╚══════╝
                    ✦ REMASTERED ✦
"""

SKULL = r"""
      ░░░░░░░░░░░░░░░░░░░░
    ░░  ██████████████  ░░
   ░░  ██  ██      ██  ██  ░░
   ░░  ██  ██      ██  ██  ░░
    ░░  ██████████████  ░░
      ░░  ████  ████  ░░
        ░░████████████░░
"""

TROPHY = r"""
        _________
       /         \
      | () () () |
      |  \  |  / |
      |   \_|_/  |
       \_________/
           |||
        ___|||___
       |_________|
"""

# ---------------------------------------------------------------------------
# Core game state
# ---------------------------------------------------------------------------

class GameState:
    def __init__(self):
        self.lives = 3
        self.score = 0
        self.missions_won = 0
        self.player_name = "Hero"

gs = GameState()

# ---------------------------------------------------------------------------
# Problem runner
# ---------------------------------------------------------------------------

def run_problem(mission: dict) -> bool:
    """
    Display and run one problem.
    Returns True if solved correctly, False otherwise.
    """
    gen = mission["generator"]

    if gen == "system2x2":
        desc, ans_x, ans_y, hint = gen_system_2x2()
        for line in desc:
            print(CYAN + line + RESET)
        got_x = ask_float(YELLOW + "  x = " + RESET)
        if not close_enough(got_x, ans_x):
            print(RED + BOLD + f"\n  ✗ Wrong!  x should be {ans_x:.4g}" + RESET)
            return False
        print(GREEN + f"  ✓ Correct!  x = {ans_x:.4g}" + RESET)
        got_y = ask_float(YELLOW + "  y = " + RESET)
        if not close_enough(got_y, ans_y):
            print(RED + BOLD + f"\n  ✗ Wrong!  y should be {ans_y:.4g}" + RESET)
            return False
        print(GREEN + f"  ✓ Correct!  y = {ans_y:.4g}" + RESET)
        return True

    elif gen == "det2x2":
        desc, ans, hint = gen_determinant_2x2()
        for line in desc:
            print(CYAN + line + RESET)
        got = ask_float(YELLOW + "  = " + RESET)
        if close_enough(got, ans):
            print(GREEN + f"  ✓ Correct!  det = {ans:.4g}" + RESET)
            return True
        print(RED + BOLD + f"\n  ✗ Wrong!  det = {ans:.4g}" + RESET)
        return False

    elif gen == "matprod":
        desc, ans, hint = gen_matrix_product()
        for line in desc:
            print(CYAN + line + RESET)
        got = ask_float(YELLOW + "  = " + RESET)
        if close_enough(got, ans):
            print(GREEN + f"  ✓ Correct!  Entry = {ans:.4g}" + RESET)
            return True
        print(RED + BOLD + f"\n  ✗ Wrong!  Entry = {ans:.4g}" + RESET)
        return False

    elif gen == "trace":
        desc, ans, hint = gen_trace()
        for line in desc:
            print(CYAN + line + RESET)
        got = ask_float(YELLOW + "  = " + RESET)
        if close_enough(got, ans):
            print(GREEN + f"  ✓ Correct!  tr = {ans:.4g}" + RESET)
            return True
        print(RED + BOLD + f"\n  ✗ Wrong!  tr = {ans:.4g}" + RESET)
        return False

    elif gen == "eigen":
        desc, ans, hint = gen_eigenvalue()
        for line in desc:
            print(CYAN + line + RESET)
        got = ask_float(YELLOW + "  λ_max = " + RESET)
        if close_enough(got, ans, tol=0.1):
            print(GREEN + f"  ✓ Correct!  λ_max ≈ {ans:.4g}" + RESET)
            return True
        print(RED + BOLD + f"\n  ✗ Wrong!  λ_max ≈ {ans:.4g}" + RESET)
        return False

    return False


def get_hint(mission: dict):
    """Print a hint (costs one life)."""
    gen = mission["generator"]
    print(MAGENTA + "\n  Generating hint…" + RESET)
    pause(0.5)
    if gen == "system2x2":
        _, _, _, hint = gen_system_2x2()
    elif gen == "det2x2":
        _, _, hint = gen_determinant_2x2()
    elif gen == "matprod":
        _, _, hint = gen_matrix_product()
    elif gen == "trace":
        _, _, hint = gen_trace()
    elif gen == "eigen":
        _, _, hint = gen_eigenvalue()
    else:
        hint = "No hint available."
    print(MAGENTA + "  HINT: " + hint + RESET)

# ---------------------------------------------------------------------------
# Mission screen
# ---------------------------------------------------------------------------

PROBLEMS_PER_MISSION = 3

def run_mission(mission: dict) -> bool:
    """Returns True if the player clears the mission."""
    clear()
    header(f"MISSION {mission['id']}: {mission['name']}", MAGENTA)
    print(YELLOW + f"  📍 Location: {mission['location']}" + RESET)
    print()
    slow_print(CYAN + "  " + mission["story"].replace("\n", "\n  ") + RESET)
    print()

    problems_solved = 0
    for p_num in range(1, PROBLEMS_PER_MISSION + 1):
        print(BLUE + BOLD + f"\n  ── Problem {p_num} of {PROBLEMS_PER_MISSION} ──" + RESET)
        print(f"  Lives: {'❤️ ' * gs.lives}    Score: {gs.score}")
        print()

        while True:
            cmd = input(
                YELLOW + "  [ENTER] Attempt  |  [H] Hint (-1 life)  |  [Q] Quit: " + RESET
            ).strip().lower()
            if cmd == "q":
                print(RED + "\n  Mission abandoned." + RESET)
                return False
            if cmd == "h":
                if gs.lives <= 1:
                    print(RED + "  Not enough lives for a hint!" + RESET)
                    continue
                gs.lives -= 1
                get_hint(mission)
                continue
            break   # attempt the problem

        ok = run_problem(mission)
        if ok:
            gs.score += 100
            problems_solved += 1
            print(GREEN + f"  Score: {gs.score}  (+100)" + RESET)
            pause(0.8)
        else:
            gs.lives -= 1
            print(RED + f"  Lives remaining: {gs.lives}" + RESET)
            pause(0.8)
            if gs.lives <= 0:
                return False

    if problems_solved == PROBLEMS_PER_MISSION:
        gs.score += 200   # mission bonus
        print()
        print(GREEN + BOLD + "  ★ MISSION COMPLETE! " + mission["win_msg"] + RESET)
        print(GREEN + f"  Bonus +200 points!  Total: {gs.score}" + RESET)
        return True
    elif problems_solved > 0:
        # partial clear still counts
        gs.score += 50
        print()
        print(YELLOW + "  ⚠ Partial clear — mission passed with losses." + RESET)
        return True
    return False

# ---------------------------------------------------------------------------
# Game-over / victory screens
# ---------------------------------------------------------------------------

def show_game_over():
    clear()
    print(RED + BOLD)
    print(SKULL)
    header("G A M E   O V E R", RED)
    print(RED + f"\n  Dr. Chaos has won.  Final score: {gs.score}\n" + RESET)
    slow_print(RED + "  Better luck next time, " + gs.player_name + "…" + RESET)
    print()

def show_victory():
    clear()
    print(GREEN + BOLD)
    print(TROPHY)
    header("YOU SAVED THE WORLD!", GREEN)
    print(GREEN + f"\n  Congratulations, {gs.player_name}!" + RESET)
    print(GREEN + f"  Final Score: {BOLD}{gs.score}{RESET}{GREEN}" + RESET)
    print(CYAN + "\n  Missions completed: {}/5".format(gs.missions_won) + RESET)
    print()
    slow_print(YELLOW + "  Dr. Chaos is behind bars. The world sleeps safely tonight." + RESET)
    print()

# ---------------------------------------------------------------------------
# Intro / menu
# ---------------------------------------------------------------------------

def show_intro():
    clear()
    print(MAGENTA + BOLD + LOGO + RESET)
    slow_print(CYAN + "  A linear-algebra adventure by the Math Heroes Guild.\n" + RESET, delay=0.015)
    print(YELLOW + "  " + "─" * 56 + RESET)
    slow_print(
        WHITE +
        "  Dr. Chaos has hacked five of the world's critical\n"
        "  systems. Each one is locked behind a mathematical\n"
        "  puzzle.  Only a master of Linear Algebra can save us.\n"
        "  Will YOU rise to the challenge?\n" + RESET,
        delay=0.02,
    )
    print(YELLOW + "  " + "─" * 56 + RESET)
    gs.player_name = input(CYAN + "\n  Enter your hero name: " + RESET).strip() or "Hero"
    print(GREEN + f"\n  Welcome, {gs.player_name}. Your mission begins NOW.\n" + RESET)
    press_enter()

def show_rules():
    clear()
    header("HOW TO PLAY", CYAN)
    rules = [
        "• There are 5 missions, each with 3 math problems.",
        "• Solve each problem correctly to advance.",
        "• You start with 3 lives ❤️  — wrong answers cost 1 life.",
        "• Hints cost 1 life — use them wisely!",
        "• Correct answer     = +100 points.",
        "• Full mission clear = +200 bonus points.",
        "• Run out of lives and the game ends.",
        "• Answers within 5 % tolerance are accepted.",
    ]
    for r in rules:
        print(CYAN + "  " + r + RESET)
    press_enter()

def show_main_menu():
    clear()
    print(MAGENTA + BOLD + LOGO + RESET)
    print(CYAN + "  " + "─" * 56 + RESET)
    print(CYAN + "  [1]  Start Game" + RESET)
    print(CYAN + "  [2]  How to Play" + RESET)
    print(CYAN + "  [3]  Quit" + RESET)
    print(CYAN + "  " + "─" * 56 + RESET)
    return input(YELLOW + "  Choice: " + RESET).strip()

# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main():
    random.seed()

    while True:
        choice = show_main_menu()
        if choice == "3":
            print(CYAN + "\n  Farewell, hero. The world awaits.\n" + RESET)
            break
        elif choice == "2":
            show_rules()
            continue
        elif choice != "1":
            continue

        # Reset state for a new game
        gs.lives  = 3
        gs.score  = 0
        gs.missions_won = 0

        show_intro()

        for mission in MISSIONS:
            if gs.lives <= 0:
                break

            won = run_mission(mission)
            if won:
                gs.missions_won += 1
                press_enter()
            else:
                if gs.lives <= 0:
                    show_game_over()
                    break
                # player quit mid-mission
                print(RED + "\n  You retreated from the mission." + RESET)
                press_enter()

        else:
            # All missions attempted
            if gs.lives > 0:
                show_victory()
            else:
                show_game_over()

        again = input(YELLOW + "\n  Play again? [Y/N]: " + RESET).strip().lower()
        if again != "y":
            print(CYAN + "\n  Thanks for playing WORLD RESCUE REMASTERED!\n" + RESET)
            break

if __name__ == "__main__":
    main()
