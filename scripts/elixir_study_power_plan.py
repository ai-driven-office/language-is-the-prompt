#!/usr/bin/env python3

from __future__ import annotations

import csv
import math
import random
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
INPUT_DIR = REPO_ROOT / "results" / "elixir_active_suites"
OUTPUT_DIR = REPO_ROOT / "results" / "elixir_power_plan"
SEED = 54
SIMULATIONS = 4000


def exact_mcnemar_pvalue(baseline_only: int, condition_only: int) -> float:
    n = baseline_only + condition_only
    if n == 0:
        return 1.0
    k = min(baseline_only, condition_only)
    cumulative = 0.0
    for value in range(0, k + 1):
        cumulative += math.comb(n, value) * (0.5**n)
    return min(1.0, 2.0 * cumulative)


def load_rows() -> list[dict]:
    rows: list[dict] = []
    for name in [
        "suite_a_paired_stats.csv",
        "suite_d_paired_stats.csv",
        "suite_e_paired_stats.csv",
        "suite_f_paired_stats.csv",
    ]:
        path = INPUT_DIR / name
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                n_shared = int(row["n_shared"])
                baseline_only = int(row["baseline_only_wins"])
                condition_only = int(row["condition_only_wins"])
                rows.append(
                    {
                        "suite_id": row["suite_id"],
                        "condition": row["condition"],
                        "n_shared": n_shared,
                        "baseline_only_wins": baseline_only,
                        "condition_only_wins": condition_only,
                        "observed_delta_points": round(100.0 * (condition_only - baseline_only) / n_shared, 2),
                        "discordance_rate": round(100.0 * (baseline_only + condition_only) / n_shared, 2),
                    }
                )
    return rows


def simulate_power(n: int, p10: float, p01: float, seed_offset: int = 0) -> float:
    rng = random.Random(SEED + seed_offset + n)
    significant = 0
    p_same = max(0.0, 1.0 - p10 - p01)
    for _ in range(SIMULATIONS):
        b = 0
        c = 0
        for _ in range(n):
            value = rng.random()
            if value < p10:
                b += 1
            elif value < p10 + p01:
                c += 1
            else:
                _ = p_same
        if exact_mcnemar_pvalue(b, c) < 0.05:
            significant += 1
    return significant / SIMULATIONS


def find_n_for_power(p10: float, p01: float, target_power: float = 0.8) -> int | None:
    for n in [198, 240, 300, 360, 480, 600, 800, 1000, 1200, 1600, 2000]:
        if simulate_power(n, p10, p01, seed_offset=100) >= target_power:
            return n
    return None


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_markdown(rows: list[dict]) -> None:
    lines = [
        "# Active-Suite Power Plan",
        "",
        "This report estimates how much sample size is needed to turn directional active-suite results into higher-power follow-up studies without rerunning the full benchmark.",
        "",
        "## Method",
        "",
        "- Use observed discordant-pair rates from the completed paper-grade suites.",
        "- Simulate paired Bernoulli outcomes at larger `N` while keeping the same discordance structure.",
        "- Use exact McNemar p-values and estimate power as the share of simulations with `p < 0.05`.",
        "",
        "## Summary",
        "",
    ]
    for row in rows:
        lines.append(
            f"- `{row['suite_id']} / {row['condition']}`: observed delta `{row['observed_delta_points']}` points, "
            f"discordance `{row['discordance_rate']}%`, current estimated power `{row['estimated_current_power']:.2f}`, "
            f"N for 80% power `{row['n_for_80_power_same_effect']}`."
        )
    (OUTPUT_DIR / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    rows = load_rows()
    output_rows: list[dict] = []
    for index, row in enumerate(rows):
        n_shared = row["n_shared"]
        p10 = row["baseline_only_wins"] / n_shared
        p01 = row["condition_only_wins"] / n_shared
        current_power = simulate_power(n_shared, p10, p01, seed_offset=index)
        n_for_80 = find_n_for_power(p10, p01)
        output_rows.append(
            {
                **row,
                "estimated_current_power": round(current_power, 3),
                "n_for_80_power_same_effect": n_for_80 if n_for_80 is not None else ">2000",
            }
        )
    write_csv(OUTPUT_DIR / "power_plan.csv", output_rows)
    write_markdown(output_rows)


if __name__ == "__main__":
    main()
