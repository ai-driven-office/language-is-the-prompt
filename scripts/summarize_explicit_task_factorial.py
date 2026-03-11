#!/usr/bin/env python3

from __future__ import annotations

import csv
import json
from collections import defaultdict
from math import comb, sqrt
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCORED_PATH = REPO_ROOT / "outputs" / "explicit_task_factorial" / "gpt-5-4-medium.exec.jsonl"
RESULTS_DIR = REPO_ROOT / "results" / "explicit_task_factorial"

Z_95 = 1.96
FACTOR_NAMES = ["docs_rich", "examples", "contracts_explicit", "state_guidance"]
ALIASED_INTERACTIONS = [
    ("docs_rich*examples", "contracts_explicit*state_guidance"),
    ("docs_rich*contracts_explicit", "examples*state_guidance"),
    ("docs_rich*state_guidance", "examples*contracts_explicit"),
]


def holm_adjust(rows: list[dict], *, group_key: str | None = None) -> list[dict]:
    grouped: dict[str, list[tuple[int, dict]]] = defaultdict(list)
    if group_key is None:
        for idx, row in enumerate(rows):
            grouped["all"].append((idx, row))
    else:
        for idx, row in enumerate(rows):
            grouped[str(row[group_key])].append((idx, row))

    adjusted = [dict(row) for row in rows]
    for entries in grouped.values():
        ranked = sorted(entries, key=lambda item: float(item[1]["sign_test_p"]))
        m = len(ranked)
        running_max = 0.0
        adjusted_p_values: list[float] = []
        for rank, (_, row) in enumerate(ranked):
            raw_p = float(row["sign_test_p"])
            candidate = min(1.0, raw_p * (m - rank))
            running_max = max(running_max, candidate)
            adjusted_p_values.append(round(running_max, 6))
        for (original_idx, _), adjusted_p in zip(ranked, adjusted_p_values):
            adjusted[original_idx]["holm_adjusted_p"] = adjusted_p
    return adjusted


def load_rows() -> list[dict]:
    rows: list[dict] = []
    with SCORED_PATH.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            original = row["original_data"]
            rows.append(
                {
                    "experiment_id": original["experiment_id"],
                    "task_id": original["task_id"],
                    "title": original["title"],
                    "language": original["language"],
                    "condition_id": original["condition_id"],
                    "condition_label": original["condition_label"],
                    "factor_levels": original["factor_levels"],
                    "success": int(bool(row["success"])),
                }
            )
    return rows


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


def percent(passed: int, total: int) -> float:
    return 0.0 if total == 0 else round(100.0 * passed / total, 1)


def wilson_interval(successes: int, total: int, z: float = Z_95) -> tuple[float, float]:
    if total == 0:
        return 0.0, 0.0
    p = successes / total
    denom = 1.0 + z**2 / total
    center = (p + z**2 / (2 * total)) / denom
    margin = z * sqrt((p * (1 - p) + z**2 / (4 * total)) / total) / denom
    low = max(0.0, center - margin)
    high = min(1.0, center + margin)
    return round(low * 100.0, 1), round(high * 100.0, 1)


def exact_sign_p_value(wins: int, losses: int) -> float:
    discordant = wins + losses
    if discordant == 0:
        return 1.0
    tail = min(wins, losses)
    probability = sum(comb(discordant, k) for k in range(0, tail + 1)) / (2**discordant)
    return min(1.0, round(2.0 * probability, 6))


def grouped_pass_rows(rows: list[dict], keys: list[str]) -> list[dict]:
    grouped: dict[tuple, list[int]] = defaultdict(list)
    for row in rows:
        grouped[tuple(row[key] for key in keys)].append(row["success"])
    out: list[dict] = []
    for key_tuple, values in sorted(grouped.items()):
        passed = sum(values)
        total = len(values)
        record = dict(zip(keys, key_tuple))
        ci_low, ci_high = wilson_interval(passed, total)
        record.update(
            {
                "passed": passed,
                "total": total,
                "pass_rate": percent(passed, total),
                "ci_low": ci_low,
                "ci_high": ci_high,
            }
        )
        out.append(record)
    return out


def matched_factor_effects(rows: list[dict], *, by_language: bool) -> list[dict]:
    grouped: dict[tuple[str, str] | tuple[str, str, str], list[dict]] = defaultdict(list)
    for row in rows:
        if by_language:
            key = (row["language"], row["task_id"], row["title"])
        else:
            key = (row["task_id"], row["title"])
        grouped[key].append(row)

    out: list[dict] = []
    for factor in FACTOR_NAMES:
        deltas: list[float] = []
        wins = 0
        losses = 0
        ties = 0
        per_language_acc: dict[str, list[float]] = defaultdict(list)

        for key, unit_rows in grouped.items():
            high = [row["success"] for row in unit_rows if row["factor_levels"][factor] == 1]
            low = [row["success"] for row in unit_rows if row["factor_levels"][factor] == 0]
            if not high or not low:
                continue
            delta = (sum(high) / len(high)) - (sum(low) / len(low))
            deltas.append(delta)
            if delta > 0:
                wins += 1
            elif delta < 0:
                losses += 1
            else:
                ties += 1
            if by_language:
                per_language_acc[key[0]].append(delta)

        if by_language:
            for language, language_deltas in sorted(per_language_acc.items()):
                out.append(
                    {
                        "scope": language,
                        "factor": factor,
                        "matched_mean_delta": round(sum(language_deltas) / len(language_deltas), 3) if language_deltas else 0.0,
                        "wins": sum(1 for value in language_deltas if value > 0),
                        "losses": sum(1 for value in language_deltas if value < 0),
                        "ties": sum(1 for value in language_deltas if value == 0),
                        "unit_count": len(language_deltas),
                        "sign_test_p": exact_sign_p_value(
                            sum(1 for value in language_deltas if value > 0),
                            sum(1 for value in language_deltas if value < 0),
                        ),
                    }
                )
        else:
            out.append(
                {
                    "scope": "all_languages",
                    "factor": factor,
                    "matched_mean_delta": round(sum(deltas) / len(deltas), 3) if deltas else 0.0,
                    "wins": wins,
                    "losses": losses,
                    "ties": ties,
                    "unit_count": len(deltas),
                    "sign_test_p": exact_sign_p_value(wins, losses),
                }
            )
    return out


def aliased_interaction_effects(rows: list[dict]) -> list[dict]:
    grouped: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
    for row in rows:
        grouped[(row["language"], row["task_id"], row["title"])].append(row)

    out: list[dict] = []
    for left, right in ALIASED_INTERACTIONS:
        left_a, left_b = left.split("*")
        pair_deltas: list[float] = []
        for unit_rows in grouped.values():
            plus = []
            minus = []
            for row in unit_rows:
                sign = (1 if row["factor_levels"][left_a] else -1) * (1 if row["factor_levels"][left_b] else -1)
                if sign == 1:
                    plus.append(row["success"])
                else:
                    minus.append(row["success"])
            if plus and minus:
                pair_deltas.append((sum(plus) / len(plus)) - (sum(minus) / len(minus)))
        out.append(
            {
                "alias_pair": f"{left} == {right}",
                "matched_mean_delta": round(sum(pair_deltas) / len(pair_deltas), 3) if pair_deltas else 0.0,
                "wins": sum(1 for value in pair_deltas if value > 0),
                "losses": sum(1 for value in pair_deltas if value < 0),
                "ties": sum(1 for value in pair_deltas if value == 0),
                "unit_count": len(pair_deltas),
                "sign_test_p": exact_sign_p_value(
                    sum(1 for value in pair_deltas if value > 0),
                    sum(1 for value in pair_deltas if value < 0),
                ),
            }
        )
    return out


def build_summary(
    rows: list[dict],
    condition_rows: list[dict],
    condition_language_rows: list[dict],
    effect_rows: list[dict],
    effect_language_rows: list[dict],
    interaction_rows: list[dict],
) -> str:
    lines = [
        "# Explicit Task Factorial Results",
        "",
        "## Aggregate Conditions",
        "",
    ]
    for row in condition_rows:
        lines.append(
            f"- `{row['condition_id']}`: `{row['passed']}/{row['total']} = {row['pass_rate']}%` "
            f"(95% Wilson CI `{row['ci_low']}%` to `{row['ci_high']}%`)."
        )

    lines.extend(["", "## Main Effects (All Languages)", ""])
    for row in effect_rows:
        lines.append(
            f"- `{row['factor']}`: matched mean delta `{row['matched_mean_delta']}`, "
            f"wins `{row['wins']}` vs losses `{row['losses']}`, ties `{row['ties']}`, "
            f"exact sign p `{row['sign_test_p']}`, Holm-adjusted p `{row['holm_adjusted_p']}`."
        )

    lines.extend(["", "## Main Effects By Language", ""])
    for row in effect_language_rows:
        lines.append(
            f"- `{row['scope']} / {row['factor']}`: matched mean delta `{row['matched_mean_delta']}`, "
            f"wins `{row['wins']}` vs losses `{row['losses']}`, ties `{row['ties']}`, "
            f"exact sign p `{row['sign_test_p']}`, Holm-adjusted p `{row['holm_adjusted_p']}`."
        )

    lines.extend(["", "## Aliased Two-Factor Contrasts", ""])
    for row in interaction_rows:
        lines.append(
            f"- `{row['alias_pair']}`: matched mean delta `{row['matched_mean_delta']}`, "
            f"wins `{row['wins']}` vs losses `{row['losses']}`, exact sign p `{row['sign_test_p']}`."
        )

    lines.extend(["", "## Language By Condition", ""])
    for row in condition_language_rows:
        lines.append(
            f"- `{row['language']} / {row['condition_id']}`: `{row['passed']}/{row['total']} = {row['pass_rate']}%`."
        )

    return "\n".join(lines) + "\n"


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    rows = load_rows()

    condition_rows = grouped_pass_rows(rows, ["condition_id", "condition_label"])
    condition_language_rows = grouped_pass_rows(rows, ["language", "condition_id", "condition_label"])
    effect_rows = holm_adjust(matched_factor_effects(rows, by_language=False))
    effect_language_rows = holm_adjust(matched_factor_effects(rows, by_language=True), group_key="scope")
    interaction_rows = aliased_interaction_effects(rows)

    write_csv(RESULTS_DIR / "condition_overall.csv", condition_rows)
    write_csv(RESULTS_DIR / "condition_by_language.csv", condition_language_rows)
    write_csv(RESULTS_DIR / "main_effects.csv", effect_rows)
    write_csv(RESULTS_DIR / "main_effects_by_language.csv", effect_language_rows)
    write_csv(RESULTS_DIR / "aliased_interactions.csv", interaction_rows)
    write_csv(
        RESULTS_DIR / "row_level_results.csv",
        [
            {
                "experiment_id": row["experiment_id"],
                "task_id": row["task_id"],
                "title": row["title"],
                "language": row["language"],
                "condition_id": row["condition_id"],
                "condition_label": row["condition_label"],
                "docs_rich": row["factor_levels"]["docs_rich"],
                "examples": row["factor_levels"]["examples"],
                "contracts_explicit": row["factor_levels"]["contracts_explicit"],
                "state_guidance": row["factor_levels"]["state_guidance"],
                "success": row["success"],
            }
            for row in rows
        ],
    )

    summary = build_summary(
        rows,
        condition_rows,
        condition_language_rows,
        effect_rows,
        effect_language_rows,
        interaction_rows,
    )
    (RESULTS_DIR / "summary.md").write_text(summary, encoding="utf-8")
    (RESULTS_DIR / "factorial_stats.json").write_text(
        json.dumps(
            {
                "condition_overall": condition_rows,
                "condition_by_language": condition_language_rows,
                "main_effects": effect_rows,
                "main_effects_by_language": effect_language_rows,
                "aliased_interactions": interaction_rows,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
