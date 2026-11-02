"""Raw (unoptimized) per-criteria report from lookup tables: avg win, hit rate."""
import csv
from collections import defaultdict
from pathlib import Path

LT = Path(__file__).resolve().parents[1] / "library" / "lookup_tables"
for mode, cost in (("base", 1.0), ("bonus", 55.0)):
    crit = {}
    with open(LT / f"lookUpTableSegmented_{mode}.csv") as f:
        for row in csv.reader(f):
            crit[int(row[0])] = row[1]
    agg = defaultdict(lambda: [0, 0.0, 0, 0.0])
    with open(LT / f"lookUpTable_{mode}.csv") as f:
        for sid, _w, pay in csv.reader(f):
            win = int(pay) / 100
            a = agg[crit[int(sid)]]
            a[0] += 1; a[1] += win; a[2] += win > 0; a[3] = max(a[3], win)
    print(f"== {mode} (cost {cost})")
    for c, (n, tot, hits, mx) in sorted(agg.items()):
        print(f"  {c:9s} n={n:6d} avg={tot/n:9.3f}x  hit={hits/n:6.3f}  max={mx:.1f}x")
