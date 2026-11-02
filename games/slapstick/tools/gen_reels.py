"""Generate 3-reel strips for slapstick (BR0 base, FR0 freegame, FRWCAP wincap).

Symbols are placed with short stacks of low/high symbols to lift the multi-line
hit rate on a 3x3 board, and scatters are spaced so at most one is visible per
reel. Deterministic (fixed seed) so strips are reproducible.
Usage: python tools/gen_reels.py [--mc N]  (--mc runs a quick raw Monte Carlo)
"""

import csv
import random
import sys
from pathlib import Path

REELS_DIR = Path(__file__).resolve().parents[1] / "reels"
ROWS = 3
LINES = [[0, 0, 0], [1, 1, 1], [2, 2, 2], [0, 1, 2], [2, 1, 0]]
PAY = {"W": 50, "H1": 20, "H2": 10, "H3": 5, "L1": 2, "L2": 1, "L3": 0.5}

STRIPS = {
    # name: (per-symbol counts per reel, stack sizes, seed)
    "BR0": ({"H1": 4, "H2": 6, "H3": 8, "L1": 10, "L2": 13, "L3": 16, "W": 4, "S": 4}, {"L": 3, "H": 2}, 11),
    "FR0": ({"H1": 6, "H2": 8, "H3": 9, "L1": 11, "L2": 12, "L3": 13, "W": 6, "S": 3}, {"L": 3, "H": 2}, 23),
    "FRWCAP": ({"H1": 4, "H2": 4, "H3": 4, "L1": 4, "L2": 4, "L3": 4, "W": 24, "S": 0}, {"L": 1, "H": 1}, 37),
}


def build_reel(counts, stacks, rng):
    blocks = []
    for sym, n in counts.items():
        if sym == "S":
            continue
        size = 1 if sym == "W" else stacks[sym[0]]
        while n > 0:
            take = min(size, n)
            blocks.append([sym] * take)
            n -= take
    rng.shuffle(blocks)
    reel = [s for b in blocks for s in b]
    # Insert scatters evenly spaced so two never share a 3-row window.
    n_s = counts.get("S", 0)
    if n_s:
        step = len(reel) // n_s
        for i in range(n_s):
            reel.insert(i * (step + 1) + rng.randrange(step // 2), "S")
    return reel


def build(name):
    counts, stacks, seed = STRIPS[name]
    rng = random.Random(seed)
    return [build_reel(counts, stacks, rng) for _ in range(3)]


def write(name, reels):
    length = max(len(r) for r in reels)
    with open(REELS_DIR / f"{name}.csv", "w", newline="") as f:
        w = csv.writer(f)
        for i in range(length):
            w.writerow([r[i % len(r)] for r in reels])


def line_win(syms):
    if "S" in syms:
        return 0
    base = next((s for s in syms if s != "W"), "W")
    if all(s in (base, "W") for s in syms):
        return PAY[base]
    return 0


def monte_carlo(reels, n, rng):
    hits = trig = 0
    total = 0.0
    for _ in range(n):
        board = []
        for r in reels:
            p = rng.randrange(len(r))
            board.append([r[(p + k) % len(r)] for k in range(ROWS)])
        win = sum(line_win([board[c][row[c]] for c in range(3)]) for row in LINES)
        total += win
        hits += win > 0
        trig += all("S" in col for col in board)
    return total / n, hits / n, trig / n


if __name__ == "__main__":
    REELS_DIR.mkdir(exist_ok=True)
    all_reels = {name: build(name) for name in STRIPS}
    for name, reels in all_reels.items():
        write(name, reels)
    if "--mc" in sys.argv:
        n = int(sys.argv[sys.argv.index("--mc") + 1])
        rng = random.Random(1)
        for name in ("BR0", "FR0"):
            rtp, hr, tr = monte_carlo(all_reels[name], n, rng)
            print(f"{name}: raw line RTP {rtp:.3f}  hit rate {hr:.3f}  3S {tr:.5f} (1/{1/tr if tr else 0:.0f})")
