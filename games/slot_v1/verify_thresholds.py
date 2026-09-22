#!/usr/bin/env python3
"""Automated threshold check against CLAUDE.md section 2 approval rules.

Run after the optimized 1M-sim pass (run.py with run_optimization=True).
Reads the FINAL, RTP-optimized lookup tables in library/publish_files/ (the
weight column there is what actually drives real-play selection odds - not
the raw stats_summary.json, which reflects the unweighted/raw simulation
distribution and is not the number that matters for compliance).

Exits non-zero and prints every violation if any threshold fails, per
CLAUDE.md section 0 rule 6 ("propose un ajustement chiffre au lieu de le
changer silencieusement").
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

GAME_DIR = Path(__file__).resolve().parent
PUBLISH_DIR = GAME_DIR / "library" / "publish_files"

# CLAUDE.md section 2 thresholds.
RTP_MIN = 0.90
RTP_MAX = 0.98
RTP_MODE_GAP_MAX = 0.005  # 0.5 percentage point
MAX_WIN_MIN_FREQUENCY = 1 / 10_000_000
BASE_HIT_RATE_MIN = 1 / 20
SIM_COUNT_MIN = 100_000
SIM_COUNT_MAX = 1_000_000

WINCAP_MULTIPLIER = 5000.0  # config.wincap, kept in sync manually with game_config.py


def load_lookup_table(mode: str) -> list[tuple[int, int]]:
    """Returns [(weight, payout_cents), ...] from the final published LUT."""
    path = PUBLISH_DIR / f"lookUpTable_{mode}_0.csv"
    if not path.exists():
        raise FileNotFoundError(f"Missing published lookup table: {path}")
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.reader(f):
            _, weight, payout = row
            rows.append((int(weight), int(payout)))
    return rows


MODE_COST = {"base": 1.0, "bonus": 100.0}  # kept in sync manually with game_config.py bet_modes


def compute_stats(rows: list[tuple[int, int]], cost: float) -> dict:
    total_weight = sum(w for w, _ in rows)
    if total_weight == 0:
        raise ValueError("Total weight is zero - lookup table is empty or malformed.")

    # payout is stored in cents of the *base* bet unit; RTP is what was paid
    # back relative to what was actually wagered for this mode (its cost).
    rtp = sum(w * payout for w, payout in rows) / (total_weight * 100.0 * cost)
    hit_weight = sum(w for w, payout in rows if payout > 0)
    hit_rate = hit_weight / total_weight

    wincap_cents = int(round(WINCAP_MULTIPLIER * 100))
    wincap_weight = sum(w for w, payout in rows if payout >= wincap_cents)
    max_win_frequency = wincap_weight / total_weight if wincap_weight else 0.0

    return {
        "rtp": rtp,
        "hit_rate": hit_rate,
        "max_win_frequency": max_win_frequency,
        "num_entries": len(rows),
        "total_weight": total_weight,
    }


def main() -> int:
    modes = ["base", "bonus"]
    stats_by_mode = {}
    violations: list[str] = []

    for mode in modes:
        rows = load_lookup_table(mode)
        stats = compute_stats(rows, MODE_COST[mode])
        stats_by_mode[mode] = stats

        print(f"[{mode}] entries={stats['num_entries']} rtp={stats['rtp']:.4f} "
              f"hit_rate={stats['hit_rate']:.4f} max_win_freq={stats['max_win_frequency']:.2e}")

        if not (RTP_MIN <= stats["rtp"] <= RTP_MAX):
            violations.append(
                f"[{mode}] RTP {stats['rtp']:.4f} outside [{RTP_MIN}, {RTP_MAX}]"
            )

        if not (SIM_COUNT_MIN <= stats["num_entries"] <= SIM_COUNT_MAX):
            violations.append(
                f"[{mode}] simulation count {stats['num_entries']} outside "
                f"[{SIM_COUNT_MIN}, {SIM_COUNT_MAX}]"
            )

        if stats["max_win_frequency"] > 0 and stats["max_win_frequency"] < MAX_WIN_MIN_FREQUENCY:
            violations.append(
                f"[{mode}] max win frequency {stats['max_win_frequency']:.2e} is rarer than "
                f"the {MAX_WIN_MIN_FREQUENCY:.2e} floor (wincap effectively unreachable)"
            )
        elif stats["max_win_frequency"] == 0:
            violations.append(f"[{mode}] max win (wincap) never occurs in the final weighted table")

    if "base" in stats_by_mode:
        base_hit_rate = stats_by_mode["base"]["hit_rate"]
        if base_hit_rate < BASE_HIT_RATE_MIN:
            violations.append(
                f"[base] hit rate {base_hit_rate:.4f} below the {BASE_HIT_RATE_MIN} (1/20) floor"
            )

    if "base" in stats_by_mode and "bonus" in stats_by_mode:
        rtp_gap = abs(stats_by_mode["base"]["rtp"] - stats_by_mode["bonus"]["rtp"])
        print(f"RTP gap base/bonus: {rtp_gap:.4f}")
        if rtp_gap > RTP_MODE_GAP_MAX:
            violations.append(
                f"RTP gap between base ({stats_by_mode['base']['rtp']:.4f}) and bonus "
                f"({stats_by_mode['bonus']['rtp']:.4f}) is {rtp_gap:.4f}, exceeds "
                f"the {RTP_MODE_GAP_MAX} (0.5pt) limit"
            )

    print()
    if violations:
        print(f"{len(violations)} threshold violation(s):")
        for v in violations:
            print(f"  - {v}")
        return 1

    print("All CLAUDE.md section 2 thresholds passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
