#!/usr/bin/env python3

from __future__ import annotations

import csv
import json
import textwrap
from pathlib import Path
from typing import Any

from explicit_task_panel_additional_impls import (
    ADDITIONAL_RETURN_CONTRACT_NOTES,
    build_additional_implementations,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
STUDY_DIR = REPO_ROOT / "studies" / "explicit_task_panel"
GENERATED_DIR = STUDY_DIR / "generated"
DATA_DIR = REPO_ROOT / "data" / "explicit_task_panel"


def dedent(text: str) -> str:
    return textwrap.dedent(text).strip() + "\n"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def to_python_literal(value: Any) -> str:
    return repr(value)


def to_typescript_literal(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def to_elixir_literal(value: Any) -> str:
    if value is None:
        return "nil"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, (int, float)):
        return repr(value)
    if isinstance(value, list):
        return "[" + ", ".join(to_elixir_literal(item) for item in value) + "]"
    if isinstance(value, tuple):
        return "{" + ", ".join(to_elixir_literal(item) for item in value) + "}"
    if isinstance(value, dict):
        items = []
        for key, item in value.items():
            items.append(f"{to_elixir_literal(key)} => {to_elixir_literal(item)}")
        return "%{" + ", ".join(items) + "}"
    raise TypeError(f"Unsupported literal: {value!r}")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys()) if rows else []
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def language_note(language: str) -> str:
    if language == "elixir":
        return "Place the public function(s) inside `defmodule Solution do ... end`."
    if language == "typescript":
        return "Write plain TypeScript with top-level functions only. Do not rely on external packages."
    return "Write plain top-level Python functions only."


def return_contract_note(task_id: str) -> str:
    notes = {
        "acct_balance_rollup": "Return a map/object with fields `balances` and `malformed_seen`.",
        "threshold_bursts": "Return a list/array of inclusive `[start, end]` index pairs.",
        "csv_split_quoted": "Return a list/array of parsed field strings.",
        "dependency_batches": "On success return `{status: \"ok\", batches: [...]}`. On cycle return `{status: \"error\", reason: \"cycle_detected\"}`.",
        "inventory_reconcile": "Return `{stock: ..., rejected_indexes: [...]}` with zero-based rejected indexes.",
        "session_durations": "Return a map/object from user id to total active seconds.",
        "window_majority": "For invalid `k`, return `{status: \"error\", reason: \"invalid_k\"}`. Otherwise return `{status: \"ok\", values: [...]}` where missing majorities are null-like values.",
        "rule_based_discount": "Return `{applied_rule: rule_id_or_no_match, final_total: numeric_total}`.",
    }
    notes.update(ADDITIONAL_RETURN_CONTRACT_NOTES)
    return notes[task_id]


def augment_question(question: str, task_id: str, language: str) -> str:
    return (
        question.strip()
        + "\n\n## Implementation Notes\n"
        + f"- {language_note(language)}\n"
        + f"- {return_contract_note(task_id)}\n"
        + "- Do not include explanations outside the single code block.\n"
    )


def build_implementations() -> dict[str, dict[str, dict[str, str]]]:
    implementations = {
        "acct_balance_rollup": {
            "python": {
                "canonical_solution": dedent(
                    """
                    def rollup_balances(events):
                        if not isinstance(events, list):
                            return {"balances": {}, "malformed_seen": True}
                        balances = {}
                        malformed_seen = False
                        for event in events:
                            if isinstance(event, dict):
                                account = event.get("account")
                                delta = event.get("delta")
                                if isinstance(account, str) and account != "" and isinstance(delta, int) and not isinstance(delta, bool):
                                    balances[account] = balances.get(account, 0) + delta
                                    continue
                            malformed_seen = True
                        return {"balances": balances, "malformed_seen": malformed_seen}
                    """
                ),
                "demo_test_func": dedent(
                    """
                    def _assert_equal(actual, expected, label):
                        assert actual == expected, f"{label}: expected {expected!r}, got {actual!r}"

                    def test():
                        _assert_equal(
                            rollup_balances([
                                {"account": "cash", "delta": 5},
                                {"account": "cash", "delta": -2},
                                {"oops": True},
                            ]),
                            {"balances": {"cash": 3}, "malformed_seen": True},
                            "demo_1",
                        )
                        _assert_equal(
                            rollup_balances([]),
                            {"balances": {}, "malformed_seen": False},
                            "demo_2",
                        )

                    if __name__ == "__main__":
                        test()
                    """
                ),
                "full_test_func": dedent(
                    """
                    def _assert_equal(actual, expected, label):
                        assert actual == expected, f"{label}: expected {expected!r}, got {actual!r}"

                    def test():
                        cases = [
                            (
                                [
                                    {"account": "cash", "delta": 5},
                                    {"account": "cash", "delta": -2},
                                    {"oops": True},
                                ],
                                {"balances": {"cash": 3}, "malformed_seen": True},
                            ),
                            (
                                [
                                    {"account": "a", "delta": 1},
                                    {"account": "b", "delta": 4},
                                    {"account": "a", "delta": 3},
                                ],
                                {"balances": {"a": 4, "b": 4}, "malformed_seen": False},
                            ),
                            (
                                [],
                                {"balances": {}, "malformed_seen": False},
                            ),
                            (
                                [
                                    {"account": "", "delta": 2},
                                    {"account": "ok", "delta": 1},
                                    {"account": "bad", "delta": "3"},
                                ],
                                {"balances": {"ok": 1}, "malformed_seen": True},
                            ),
                            (
                                [
                                    {"account": "x", "delta": 0},
                                    {"account": "x", "delta": -5},
                                    {"account": "y", "delta": 8},
                                ],
                                {"balances": {"x": -5, "y": 8}, "malformed_seen": False},
                            ),
                        ]
                        for index, (events, expected) in enumerate(cases):
                            _assert_equal(rollup_balances(events), expected, f"full_{index}")

                    if __name__ == "__main__":
                        test()
                    """
                ),
            },
            "typescript": {
                "canonical_solution": dedent(
                    """
                    function rollupBalances(events: unknown): { balances: Record<string, number>; malformed_seen: boolean } {
                      if (!Array.isArray(events)) {
                        return { balances: {}, malformed_seen: true };
                      }
                      const balances: Record<string, number> = {};
                      let malformedSeen = false;
                      for (const event of events) {
                        if (
                          event !== null &&
                          typeof event === "object" &&
                          typeof (event as any).account === "string" &&
                          (event as any).account.length > 0 &&
                          typeof (event as any).delta === "number" &&
                          Number.isInteger((event as any).delta)
                        ) {
                          const account = (event as any).account as string;
                          const delta = (event as any).delta as number;
                          balances[account] = (balances[account] ?? 0) + delta;
                        } else {
                          malformedSeen = true;
                        }
                      }
                      return { balances, malformed_seen: malformedSeen };
                    }
                    """
                ),
                "demo_test_func": dedent(
                    """
                    function stable(value: any): any {
                      if (Array.isArray(value)) return value.map(stable);
                      if (value && typeof value === "object") {
                        const out: Record<string, any> = {};
                        for (const key of Object.keys(value).sort()) out[key] = stable(value[key]);
                        return out;
                      }
                      return value;
                    }
                    function assertDeepEqual(actual: any, expected: any, label: string): void {
                      const a = JSON.stringify(stable(actual));
                      const e = JSON.stringify(stable(expected));
                      if (a !== e) throw new Error(`${label}: expected ${e}, got ${a}`);
                    }
                    function demoTesting(): void {
                      assertDeepEqual(
                        rollupBalances([
                          { account: "cash", delta: 5 },
                          { account: "cash", delta: -2 },
                          { oops: true },
                        ]),
                        { balances: { cash: 3 }, malformed_seen: true },
                        "demo_1",
                      );
                      assertDeepEqual(rollupBalances([]), { balances: {}, malformed_seen: false }, "demo_2");
                    }
                    demoTesting();
                    """
                ),
                "full_test_func": dedent(
                    """
                    function stable(value: any): any {
                      if (Array.isArray(value)) return value.map(stable);
                      if (value && typeof value === "object") {
                        const out: Record<string, any> = {};
                        for (const key of Object.keys(value).sort()) out[key] = stable(value[key]);
                        return out;
                      }
                      return value;
                    }
                    function assertDeepEqual(actual: any, expected: any, label: string): void {
                      const a = JSON.stringify(stable(actual));
                      const e = JSON.stringify(stable(expected));
                      if (a !== e) throw new Error(`${label}: expected ${e}, got ${a}`);
                    }
                    function fullTesting(): void {
                      const cases: Array<[any, any]> = [
                        [
                          [{ account: "cash", delta: 5 }, { account: "cash", delta: -2 }, { oops: true }],
                          { balances: { cash: 3 }, malformed_seen: true },
                        ],
                        [
                          [{ account: "a", delta: 1 }, { account: "b", delta: 4 }, { account: "a", delta: 3 }],
                          { balances: { a: 4, b: 4 }, malformed_seen: false },
                        ],
                        [[], { balances: {}, malformed_seen: false }],
                        [
                          [{ account: "", delta: 2 }, { account: "ok", delta: 1 }, { account: "bad", delta: "3" }],
                          { balances: { ok: 1 }, malformed_seen: true },
                        ],
                        [
                          [{ account: "x", delta: 0 }, { account: "x", delta: -5 }, { account: "y", delta: 8 }],
                          { balances: { x: -5, y: 8 }, malformed_seen: false },
                        ],
                      ];
                      cases.forEach(([events, expected], index) => {
                        assertDeepEqual(rollupBalances(events), expected, `full_${index}`);
                      });
                    }
                    fullTesting();
                    """
                ),
            },
            "elixir": {
                "canonical_solution": dedent(
                    """
                    defmodule Solution do
                      def rollup_balances(events) when is_list(events) do
                        Enum.reduce(events, %{"balances" => %{}, "malformed_seen" => false}, fn event, acc ->
                          case normalize_event(event) do
                            {:ok, account, delta} ->
                              balances = Map.update(acc["balances"], account, delta, &(&1 + delta))
                              %{"balances" => balances, "malformed_seen" => acc["malformed_seen"]}

                            :error ->
                              %{"balances" => acc["balances"], "malformed_seen" => true}
                          end
                        end)
                      end

                      def rollup_balances(_), do: %{"balances" => %{}, "malformed_seen" => true}

                      defp normalize_event(%{"account" => account, "delta" => delta})
                           when is_binary(account) and account != "" and is_integer(delta),
                           do: {:ok, account, delta}

                      defp normalize_event(%{account: account, delta: delta})
                           when is_binary(account) and account != "" and is_integer(delta),
                           do: {:ok, account, delta}

                      defp normalize_event(_), do: :error
                    end
                    """
                ),
                "demo_test_func": dedent(
                    """
                    defmodule DemoTestHelper do
                      def get_key(map, key) when is_map(map) do
                        Map.get(map, key) || Map.get(map, String.to_atom(key)) || Map.get(map, Atom.to_string(String.to_atom(key)))
                      end

                      def normalize_map(map) when is_map(map) do
                        Enum.reduce(map, %{}, fn {key, value}, acc -> Map.put(acc, to_string(key), value) end)
                      end

                      def normalize_rollup(value) do
                        balances = get_key(value, "balances") |> normalize_map()
                        malformed_seen = get_key(value, "malformed_seen")
                        %{"balances" => balances, "malformed_seen" => malformed_seen}
                      end

                      def assert_equal(actual, expected, label) do
                        if actual != expected do
                          raise "#{label}: expected #{inspect(expected)}, got #{inspect(actual)}"
                        end
                      end
                    end

                    defmodule DemoTest do
                      def run do
                        DemoTestHelper.assert_equal(
                          DemoTestHelper.normalize_rollup(
                            Solution.rollup_balances([
                              %{"account" => "cash", "delta" => 5},
                              %{"account" => "cash", "delta" => -2},
                              %{"oops" => true}
                            ])
                          ),
                          %{"balances" => %{"cash" => 3}, "malformed_seen" => true},
                          "demo_1"
                        )

                        DemoTestHelper.assert_equal(
                          DemoTestHelper.normalize_rollup(Solution.rollup_balances([])),
                          %{"balances" => %{}, "malformed_seen" => false},
                          "demo_2"
                        )
                      end
                    end

                    DemoTest.run()
                    """
                ),
                "full_test_func": dedent(
                    """
                    defmodule FullTestHelper do
                      def get_key(map, key) when is_map(map) do
                        Map.get(map, key) || Map.get(map, String.to_atom(key)) || Map.get(map, Atom.to_string(String.to_atom(key)))
                      end

                      def normalize_map(map) when is_map(map) do
                        Enum.reduce(map, %{}, fn {key, value}, acc -> Map.put(acc, to_string(key), value) end)
                      end

                      def normalize_rollup(value) do
                        balances = get_key(value, "balances") |> normalize_map()
                        malformed_seen = get_key(value, "malformed_seen")
                        %{"balances" => balances, "malformed_seen" => malformed_seen}
                      end

                      def assert_equal(actual, expected, label) do
                        if actual != expected do
                          raise "#{label}: expected #{inspect(expected)}, got #{inspect(actual)}"
                        end
                      end
                    end

                    defmodule FullTest do
                      def run do
                        cases = [
                          {
                            [
                              %{"account" => "cash", "delta" => 5},
                              %{"account" => "cash", "delta" => -2},
                              %{"oops" => true}
                            ],
                            %{"balances" => %{"cash" => 3}, "malformed_seen" => true}
                          },
                          {
                            [
                              %{"account" => "a", "delta" => 1},
                              %{"account" => "b", "delta" => 4},
                              %{"account" => "a", "delta" => 3}
                            ],
                            %{"balances" => %{"a" => 4, "b" => 4}, "malformed_seen" => false}
                          },
                          {[], %{"balances" => %{}, "malformed_seen" => false}},
                          {
                            [
                              %{"account" => "", "delta" => 2},
                              %{"account" => "ok", "delta" => 1},
                              %{"account" => "bad", "delta" => "3"}
                            ],
                            %{"balances" => %{"ok" => 1}, "malformed_seen" => true}
                          },
                          {
                            [
                              %{"account" => "x", "delta" => 0},
                              %{"account" => "x", "delta" => -5},
                              %{"account" => "y", "delta" => 8}
                            ],
                            %{"balances" => %{"x" => -5, "y" => 8}, "malformed_seen" => false}
                          }
                        ]

                        Enum.with_index(cases)
                        |> Enum.each(fn {{events, expected}, index} ->
                          actual = Solution.rollup_balances(events) |> FullTestHelper.normalize_rollup()
                          FullTestHelper.assert_equal(actual, expected, "full_#{index}")
                        end)
                      end
                    end

                    FullTest.run()
                    """
                ),
            },
        },
        "threshold_bursts": {
            "python": {
                "canonical_solution": dedent(
                    """
                    def find_bursts(readings, threshold):
                        if not isinstance(readings, list):
                            return []
                        bursts = []
                        start = None
                        for index, value in enumerate(readings):
                            in_burst = isinstance(value, (int, float)) and value > threshold
                            if in_burst:
                                if start is None:
                                    start = index
                            elif start is not None:
                                bursts.append([start, index - 1])
                                start = None
                        if start is not None:
                            bursts.append([start, len(readings) - 1])
                        return bursts
                    """
                ),
                "demo_test_func": dedent(
                    """
                    def test():
                        assert find_bursts([1, 5, 6, 2, 7], 4) == [[1, 2], [4, 4]]
                        assert find_bursts([], 3) == []

                    if __name__ == "__main__":
                        test()
                    """
                ),
                "full_test_func": dedent(
                    """
                    def test():
                        cases = [
                            (([1, 5, 6, 2, 7], 4), [[1, 2], [4, 4]]),
                            (([], 3), []),
                            (([5, 5, 5], 5), []),
                            (([9, 8, 7], 6), [[0, 2]]),
                            (([1, 2, 3], 1), [[1, 2]]),
                            (([1, 6, 2, 8, 9, 1], 5), [[1, 1], [3, 4]]),
                        ]
                        for index, ((readings, threshold), expected) in enumerate(cases):
                            actual = find_bursts(readings, threshold)
                            assert actual == expected, f"case {index}: expected {expected!r}, got {actual!r}"

                    if __name__ == "__main__":
                        test()
                    """
                ),
            },
            "typescript": {
                "canonical_solution": dedent(
                    """
                    function findBursts(readings: unknown, threshold: number): number[][] {
                      if (!Array.isArray(readings)) return [];
                      const bursts: number[][] = [];
                      let start: number | null = null;
                      readings.forEach((value, index) => {
                        const inBurst = typeof value === "number" && value > threshold;
                        if (inBurst) {
                          if (start === null) start = index;
                        } else if (start !== null) {
                          bursts.push([start, index - 1]);
                          start = null;
                        }
                      });
                      if (start !== null) bursts.push([start, readings.length - 1]);
                      return bursts;
                    }
                    """
                ),
                "demo_test_func": dedent(
                    """
                    function assertDeepEqual(actual: any, expected: any, label: string): void {
                      const a = JSON.stringify(actual);
                      const e = JSON.stringify(expected);
                      if (a !== e) throw new Error(`${label}: expected ${e}, got ${a}`);
                    }
                    function demoTesting(): void {
                      assertDeepEqual(findBursts([1, 5, 6, 2, 7], 4), [[1, 2], [4, 4]], "demo_1");
                      assertDeepEqual(findBursts([], 3), [], "demo_2");
                    }
                    demoTesting();
                    """
                ),
                "full_test_func": dedent(
                    """
                    function assertDeepEqual(actual: any, expected: any, label: string): void {
                      const a = JSON.stringify(actual);
                      const e = JSON.stringify(expected);
                      if (a !== e) throw new Error(`${label}: expected ${e}, got ${a}`);
                    }
                    function fullTesting(): void {
                      const cases: Array<[[any[], number], number[][]]> = [
                        [[[1, 5, 6, 2, 7], 4], [[1, 2], [4, 4]]],
                        [[[], 3], []],
                        [[[5, 5, 5], 5], []],
                        [[[9, 8, 7], 6], [[0, 2]]],
                        [[[1, 2, 3], 1], [[1, 2]]],
                        [[[1, 6, 2, 8, 9, 1], 5], [[1, 1], [3, 4]]],
                      ];
                      cases.forEach((entry, index) => {
                        const [[readings, threshold], expected] = entry;
                        assertDeepEqual(findBursts(readings, threshold), expected, `full_${index}`);
                      });
                    }
                    fullTesting();
                    """
                ),
            },
            "elixir": {
                "canonical_solution": dedent(
                    """
                    defmodule Solution do
                      def find_bursts(readings, threshold) when is_list(readings) do
                        {start_index, bursts} =
                          readings
                          |> Enum.with_index()
                          |> Enum.reduce({nil, []}, fn {value, index}, {start_index, bursts} ->
                            in_burst = is_number(value) and value > threshold

                            cond do
                              in_burst and is_nil(start_index) ->
                                {index, bursts}

                              in_burst ->
                                {start_index, bursts}

                              is_nil(start_index) ->
                                {nil, bursts}

                              true ->
                                {nil, bursts ++ [[start_index, index - 1]]}
                            end
                          end)

                        if is_nil(start_index) do
                          bursts
                        else
                          bursts ++ [[start_index, length(readings) - 1]]
                        end
                      end

                      def find_bursts(_, _), do: []
                    end
                    """
                ),
                "demo_test_func": dedent(
                    """
                    defmodule DemoTestHelper do
                      def normalize_pairs(value) do
                        Enum.map(value, fn
                          [a, b] -> [a, b]
                          {a, b} -> [a, b]
                        end)
                      end

                      def assert_equal(actual, expected, label) do
                        if actual != expected, do: raise("#{label}: expected #{inspect(expected)}, got #{inspect(actual)}")
                      end
                    end

                    defmodule DemoTest do
                      def run do
                        DemoTestHelper.assert_equal(
                          Solution.find_bursts([1, 5, 6, 2, 7], 4) |> DemoTestHelper.normalize_pairs(),
                          [[1, 2], [4, 4]],
                          "demo_1"
                        )

                        DemoTestHelper.assert_equal(
                          Solution.find_bursts([], 3) |> DemoTestHelper.normalize_pairs(),
                          [],
                          "demo_2"
                        )
                      end
                    end

                    DemoTest.run()
                    """
                ),
                "full_test_func": dedent(
                    """
                    defmodule FullTestHelper do
                      def normalize_pairs(value) do
                        Enum.map(value, fn
                          [a, b] -> [a, b]
                          {a, b} -> [a, b]
                        end)
                      end

                      def assert_equal(actual, expected, label) do
                        if actual != expected, do: raise("#{label}: expected #{inspect(expected)}, got #{inspect(actual)}")
                      end
                    end

                    defmodule FullTest do
                      def run do
                        cases = [
                          {[1, 5, 6, 2, 7], 4, [[1, 2], [4, 4]]},
                          {[], 3, []},
                          {[5, 5, 5], 5, []},
                          {[9, 8, 7], 6, [[0, 2]]},
                          {[1, 2, 3], 1, [[1, 2]]},
                          {[1, 6, 2, 8, 9, 1], 5, [[1, 1], [3, 4]]}
                        ]

                        Enum.with_index(cases)
                        |> Enum.each(fn {{readings, threshold, expected}, index} ->
                          actual = Solution.find_bursts(readings, threshold) |> FullTestHelper.normalize_pairs()
                          FullTestHelper.assert_equal(actual, expected, "full_#{index}")
                        end)
                      end
                    end

                    FullTest.run()
                    """
                ),
            },
        },
        "csv_split_quoted": {
            "python": {
                "canonical_solution": dedent(
                    """
                    def split_csv_line(line):
                        if not isinstance(line, str):
                            return [""]
                        fields = []
                        current = []
                        quoted = False
                        index = 0
                        while index < len(line):
                            ch = line[index]
                            if ch == '"':
                                if quoted and index + 1 < len(line) and line[index + 1] == '"':
                                    current.append('"')
                                    index += 2
                                    continue
                                quoted = not quoted
                            elif ch == "," and not quoted:
                                fields.append("".join(current))
                                current = []
                            else:
                                current.append(ch)
                            index += 1
                        fields.append("".join(current))
                        return fields
                    """
                ),
                "demo_test_func": dedent(
                    """
                    def test():
                        assert split_csv_line('"a,b",c,"d""e"') == ["a,b", "c", 'd"e']
                        assert split_csv_line("") == [""]

                    if __name__ == "__main__":
                        test()
                    """
                ),
                "full_test_func": dedent(
                    """
                    def test():
                        cases = [
                            ('"a,b",c,"d""e"', ["a,b", "c", 'd"e']),
                            ("", [""]),
                            ("a,,b", ["a", "", "b"]),
                            ('"",x', ["", "x"]),
                            ('left,"middle,right",tail', ["left", "middle,right", "tail"]),
                            ('plain', ["plain"]),
                        ]
                        for index, (line, expected) in enumerate(cases):
                            actual = split_csv_line(line)
                            assert actual == expected, f"case {index}: expected {expected!r}, got {actual!r}"

                    if __name__ == "__main__":
                        test()
                    """
                ),
            },
            "typescript": {
                "canonical_solution": dedent(
                    """
                    function splitCsvLine(line: unknown): string[] {
                      if (typeof line !== "string") return [""];
                      const fields: string[] = [];
                      let current = "";
                      let quoted = false;
                      for (let index = 0; index < line.length; index += 1) {
                        const ch = line[index];
                        if (ch === '"') {
                          if (quoted && index + 1 < line.length && line[index + 1] === '"') {
                            current += '"';
                            index += 1;
                          } else {
                            quoted = !quoted;
                          }
                        } else if (ch === "," && !quoted) {
                          fields.push(current);
                          current = "";
                        } else {
                          current += ch;
                        }
                      }
                      fields.push(current);
                      return fields;
                    }
                    """
                ),
                "demo_test_func": dedent(
                    """
                    function assertDeepEqual(actual: any, expected: any, label: string): void {
                      const a = JSON.stringify(actual);
                      const e = JSON.stringify(expected);
                      if (a !== e) throw new Error(`${label}: expected ${e}, got ${a}`);
                    }
                    function demoTesting(): void {
                      assertDeepEqual(splitCsvLine('"a,b",c,"d""e"'), ["a,b", "c", 'd"e'], "demo_1");
                      assertDeepEqual(splitCsvLine(""), [""], "demo_2");
                    }
                    demoTesting();
                    """
                ),
                "full_test_func": dedent(
                    """
                    function assertDeepEqual(actual: any, expected: any, label: string): void {
                      const a = JSON.stringify(actual);
                      const e = JSON.stringify(expected);
                      if (a !== e) throw new Error(`${label}: expected ${e}, got ${a}`);
                    }
                    function fullTesting(): void {
                      const cases: Array<[string, string[]]> = [
                        ['"a,b",c,"d""e"', ["a,b", "c", 'd"e']],
                        ["", [""]],
                        ["a,,b", ["a", "", "b"]],
                        ['"",x', ["", "x"]],
                        ['left,"middle,right",tail', ["left", "middle,right", "tail"]],
                        ["plain", ["plain"]],
                      ];
                      cases.forEach(([line, expected], index) => {
                        assertDeepEqual(splitCsvLine(line), expected, `full_${index}`);
                      });
                    }
                    fullTesting();
                    """
                ),
            },
            "elixir": {
                "canonical_solution": dedent(
                    """
                    defmodule Solution do
                      @quote <<34>>

                      def split_csv_line(line) when is_binary(line) do
                        parse(String.graphemes(line), false, "", [])
                      end

                      def split_csv_line(_), do: [""]

                      defp parse([], _quoted, current, acc), do: Enum.reverse([current | acc])
                      defp parse([first, second | rest], true, current, acc) when first == @quote and second == @quote do
                        parse(rest, true, current <> @quote, acc)
                      end

                      defp parse([first | rest], quoted, current, acc) when first == @quote do
                        parse(rest, not quoted, current, acc)
                      end

                      defp parse(["," | rest], false, current, acc), do: parse(rest, false, "", [current | acc])
                      defp parse([ch | rest], quoted, current, acc), do: parse(rest, quoted, current <> ch, acc)
                    end
                    """
                ),
                "demo_test_func": dedent(
                    """
                    defmodule DemoTestHelper do
                      def assert_equal(actual, expected, label) do
                        if actual != expected, do: raise("#{label}: expected #{inspect(expected)}, got #{inspect(actual)}")
                      end
                    end

                    defmodule DemoTest do
                      def run do
                        DemoTestHelper.assert_equal(Solution.split_csv_line(~s|"a,b",c,"d""e"|), ["a,b", "c", ~s|d"e|], "demo_1")
                        DemoTestHelper.assert_equal(Solution.split_csv_line(""), [""], "demo_2")
                      end
                    end

                    DemoTest.run()
                    """
                ),
                "full_test_func": dedent(
                    """
                    defmodule FullTestHelper do
                      def assert_equal(actual, expected, label) do
                        if actual != expected, do: raise("#{label}: expected #{inspect(expected)}, got #{inspect(actual)}")
                      end
                    end

                    defmodule FullTest do
                      def run do
                        cases = [
                          {~s|"a,b",c,"d""e"|, ["a,b", "c", ~s|d"e|]},
                          {"", [""]},
                          {"a,,b", ["a", "", "b"]},
                          {~s|"",x|, ["", "x"]},
                          {~s|left,"middle,right",tail|, ["left", "middle,right", "tail"]},
                          {"plain", ["plain"]}
                        ]

                        Enum.with_index(cases)
                        |> Enum.each(fn {{line, expected}, index} ->
                          FullTestHelper.assert_equal(Solution.split_csv_line(line), expected, "full_#{index}")
                        end)
                      end
                    end

                    FullTest.run()
                    """
                ),
            },
        },
        "dependency_batches": {
            "python": {
                "canonical_solution": dedent(
                    """
                    def build_batches(tasks, edges):
                        task_list = [task for task in tasks if isinstance(task, str)]
                        nodes = list(dict.fromkeys(task_list))
                        edge_set = set()
                        for edge in edges:
                            if isinstance(edge, (list, tuple)) and len(edge) == 2 and all(isinstance(item, str) for item in edge):
                                pair = (edge[0], edge[1])
                                edge_set.add(pair)
                                if pair[0] not in nodes:
                                    nodes.append(pair[0])
                                if pair[1] not in nodes:
                                    nodes.append(pair[1])
                        adjacency = {node: [] for node in nodes}
                        indegree = {node: 0 for node in nodes}
                        for left, right in edge_set:
                            adjacency[left].append(right)
                            indegree[right] += 1
                        remaining = set(nodes)
                        batches = []
                        while remaining:
                            batch = sorted(node for node in remaining if indegree[node] == 0)
                            if not batch:
                                return {"status": "error", "reason": "cycle_detected"}
                            batches.append(batch)
                            for node in batch:
                                remaining.remove(node)
                                for nxt in adjacency[node]:
                                    indegree[nxt] -= 1
                        return {"status": "ok", "batches": batches}
                    """
                ),
                "demo_test_func": dedent(
                    """
                    def test():
                        assert build_batches(["a", "b", "c"], [["a", "c"], ["b", "c"]]) == {"status": "ok", "batches": [["a", "b"], ["c"]]}
                        assert build_batches(["a", "b"], [["a", "b"], ["b", "a"]]) == {"status": "error", "reason": "cycle_detected"}

                    if __name__ == "__main__":
                        test()
                    """
                ),
                "full_test_func": dedent(
                    """
                    def test():
                        cases = [
                            ((["a", "b", "c"], [["a", "c"], ["b", "c"]]), {"status": "ok", "batches": [["a", "b"], ["c"]]}),
                            ((["a", "b"], [["a", "b"], ["b", "a"]]), {"status": "error", "reason": "cycle_detected"}),
                            ((["x"], []), {"status": "ok", "batches": [["x"]]}),
                            ((["a", "b", "c", "d"], [["a", "c"], ["a", "d"], ["b", "d"]]), {"status": "ok", "batches": [["a", "b"], ["c", "d"]]}),
                            (([], [["m", "n"]]), {"status": "ok", "batches": [["m"], ["n"]]}),
                        ]
                        for index, ((tasks, edges), expected) in enumerate(cases):
                            actual = build_batches(tasks, edges)
                            assert actual == expected, f"case {index}: expected {expected!r}, got {actual!r}"

                    if __name__ == "__main__":
                        test()
                    """
                ),
            },
            "typescript": {
                "canonical_solution": dedent(
                    """
                    function buildBatches(tasks: unknown[], edges: unknown[]): { status: string; batches?: string[][]; reason?: string } {
                      const nodes: string[] = [];
                      for (const task of tasks) {
                        if (typeof task === "string" && !nodes.includes(task)) nodes.push(task);
                      }
                      const edgeSet = new Set<string>();
                      for (const edge of edges) {
                        if (Array.isArray(edge) && edge.length === 2 && typeof edge[0] === "string" && typeof edge[1] === "string") {
                          edgeSet.add(`${edge[0]}=>${edge[1]}`);
                          if (!nodes.includes(edge[0])) nodes.push(edge[0]);
                          if (!nodes.includes(edge[1])) nodes.push(edge[1]);
                        }
                      }
                      const adjacency: Record<string, string[]> = {};
                      const indegree: Record<string, number> = {};
                      for (const node of nodes) {
                        adjacency[node] = [];
                        indegree[node] = 0;
                      }
                      edgeSet.forEach((item) => {
                        const [left, right] = item.split("=>");
                        adjacency[left].push(right);
                        indegree[right] += 1;
                      });
                      const remaining = new Set(nodes);
                      const batches: string[][] = [];
                      while (remaining.size > 0) {
                        const batch = Array.from(remaining).filter((node) => indegree[node] === 0).sort();
                        if (batch.length === 0) return { status: "error", reason: "cycle_detected" };
                        batches.push(batch);
                        batch.forEach((node) => {
                          remaining.delete(node);
                          adjacency[node].forEach((next) => {
                            indegree[next] -= 1;
                          });
                        });
                      }
                      return { status: "ok", batches };
                    }
                    """
                ),
                "demo_test_func": dedent(
                    """
                    function stable(value: any): any {
                      if (Array.isArray(value)) return value.map(stable);
                      if (value && typeof value === "object") {
                        const out: Record<string, any> = {};
                        Object.keys(value).sort().forEach((key) => { out[key] = stable(value[key]); });
                        return out;
                      }
                      return value;
                    }
                    function assertDeepEqual(actual: any, expected: any, label: string): void {
                      const a = JSON.stringify(stable(actual));
                      const e = JSON.stringify(stable(expected));
                      if (a !== e) throw new Error(`${label}: expected ${e}, got ${a}`);
                    }
                    function demoTesting(): void {
                      assertDeepEqual(buildBatches(["a", "b", "c"], [["a", "c"], ["b", "c"]]), { status: "ok", batches: [["a", "b"], ["c"]] }, "demo_1");
                      assertDeepEqual(buildBatches(["a", "b"], [["a", "b"], ["b", "a"]]), { status: "error", reason: "cycle_detected" }, "demo_2");
                    }
                    demoTesting();
                    """
                ),
                "full_test_func": dedent(
                    """
                    function stable(value: any): any {
                      if (Array.isArray(value)) return value.map(stable);
                      if (value && typeof value === "object") {
                        const out: Record<string, any> = {};
                        Object.keys(value).sort().forEach((key) => { out[key] = stable(value[key]); });
                        return out;
                      }
                      return value;
                    }
                    function assertDeepEqual(actual: any, expected: any, label: string): void {
                      const a = JSON.stringify(stable(actual));
                      const e = JSON.stringify(stable(expected));
                      if (a !== e) throw new Error(`${label}: expected ${e}, got ${a}`);
                    }
                    function fullTesting(): void {
                      const cases: Array<[[string[], string[][]], any]> = [
                        [[["a", "b", "c"], [["a", "c"], ["b", "c"]]], { status: "ok", batches: [["a", "b"], ["c"]] }],
                        [[["a", "b"], [["a", "b"], ["b", "a"]]], { status: "error", reason: "cycle_detected" }],
                        [[["x"], []], { status: "ok", batches: [["x"]] }],
                        [[["a", "b", "c", "d"], [["a", "c"], ["a", "d"], ["b", "d"]]], { status: "ok", batches: [["a", "b"], ["c", "d"]] }],
                        [[[], [["m", "n"]]], { status: "ok", batches: [["m"], ["n"]] }],
                      ];
                      cases.forEach((entry, index) => {
                        const [[tasks, edges], expected] = entry;
                        assertDeepEqual(buildBatches(tasks, edges), expected, `full_${index}`);
                      });
                    }
                    fullTesting();
                    """
                ),
            },
            "elixir": {
                "canonical_solution": dedent(
                    """
                    defmodule Solution do
                      def build_batches(tasks, edges) when is_list(tasks) and is_list(edges) do
                        nodes =
                          tasks
                          |> Enum.filter(&is_binary/1)
                          |> Enum.reduce([], fn task, acc -> if task in acc, do: acc, else: acc ++ [task] end)

                        {nodes, edge_pairs} =
                          Enum.reduce(edges, {nodes, MapSet.new()}, fn edge, {node_acc, edge_acc} ->
                            case edge do
                              [left, right] when is_binary(left) and is_binary(right) ->
                                updated_nodes =
                                  node_acc
                                  |> then(fn acc -> if left in acc, do: acc, else: acc ++ [left] end)
                                  |> then(fn acc -> if right in acc, do: acc, else: acc ++ [right] end)

                                {updated_nodes, MapSet.put(edge_acc, {left, right})}

                              _ ->
                                {node_acc, edge_acc}
                            end
                          end)

                        adjacency = Enum.into(nodes, %{}, fn node -> {node, []} end)
                        indegree = Enum.into(nodes, %{}, fn node -> {node, 0} end)

                        {adjacency, indegree} =
                          Enum.reduce(edge_pairs, {adjacency, indegree}, fn {left, right}, {adj, indeg} ->
                            {Map.update!(adj, left, &(&1 ++ [right])), Map.update!(indeg, right, &(&1 + 1))}
                          end)

                        case build_batches_loop(MapSet.new(nodes), adjacency, indegree, []) do
                          {:ok, batches} -> %{"status" => "ok", "batches" => batches}
                          :error -> %{"status" => "error", "reason" => "cycle_detected"}
                        end
                      end

                      def build_batches(_, _), do: %{"status" => "error", "reason" => "cycle_detected"}

                      defp build_batches_loop(remaining, adjacency, indegree, acc) do
                        if MapSet.size(remaining) == 0 do
                          {:ok, acc}
                        else
                          batch =
                            remaining
                            |> MapSet.to_list()
                            |> Enum.filter(&(Map.get(indegree, &1, 0) == 0))
                            |> Enum.sort()

                          if batch == [] do
                            :error
                          else
                            next_remaining = Enum.reduce(batch, remaining, &MapSet.delete(&2, &1))

                            next_indegree =
                              Enum.reduce(batch, indegree, fn node, indeg ->
                                Enum.reduce(Map.get(adjacency, node, []), indeg, fn next, inner ->
                                  Map.update!(inner, next, &(&1 - 1))
                                end)
                              end)

                            build_batches_loop(next_remaining, adjacency, next_indegree, acc ++ [batch])
                          end
                        end
                      end
                    end
                    """
                ),
                "demo_test_func": dedent(
                    """
                    defmodule DemoTestHelper do
                      def get_key(map, key) when is_map(map) do
                        Map.get(map, key) || Map.get(map, String.to_atom(key))
                      end

                      def normalize_result(value) do
                        status = get_key(value, "status")
                        batches = get_key(value, "batches")
                        reason = get_key(value, "reason")

                        result = %{"status" => status}
                        result = if is_nil(batches), do: result, else: Map.put(result, "batches", batches)
                        if is_nil(reason), do: result, else: Map.put(result, "reason", reason)
                      end

                      def assert_equal(actual, expected, label) do
                        if actual != expected, do: raise("#{label}: expected #{inspect(expected)}, got #{inspect(actual)}")
                      end
                    end

                    defmodule DemoTest do
                      def run do
                        DemoTestHelper.assert_equal(
                          Solution.build_batches(["a", "b", "c"], [["a", "c"], ["b", "c"]]) |> DemoTestHelper.normalize_result(),
                          %{"status" => "ok", "batches" => [["a", "b"], ["c"]]},
                          "demo_1"
                        )

                        DemoTestHelper.assert_equal(
                          Solution.build_batches(["a", "b"], [["a", "b"], ["b", "a"]]) |> DemoTestHelper.normalize_result(),
                          %{"status" => "error", "reason" => "cycle_detected"},
                          "demo_2"
                        )
                      end
                    end

                    DemoTest.run()
                    """
                ),
                "full_test_func": dedent(
                    """
                    defmodule FullTestHelper do
                      def get_key(map, key) when is_map(map) do
                        Map.get(map, key) || Map.get(map, String.to_atom(key))
                      end

                      def normalize_result(value) do
                        status = get_key(value, "status")
                        batches = get_key(value, "batches")
                        reason = get_key(value, "reason")

                        result = %{"status" => status}
                        result = if is_nil(batches), do: result, else: Map.put(result, "batches", batches)
                        if is_nil(reason), do: result, else: Map.put(result, "reason", reason)
                      end

                      def assert_equal(actual, expected, label) do
                        if actual != expected, do: raise("#{label}: expected #{inspect(expected)}, got #{inspect(actual)}")
                      end
                    end

                    defmodule FullTest do
                      def run do
                        cases = [
                          {["a", "b", "c"], [["a", "c"], ["b", "c"]], %{"status" => "ok", "batches" => [["a", "b"], ["c"]]}},
                          {["a", "b"], [["a", "b"], ["b", "a"]], %{"status" => "error", "reason" => "cycle_detected"}},
                          {["x"], [], %{"status" => "ok", "batches" => [["x"]]}},
                          {["a", "b", "c", "d"], [["a", "c"], ["a", "d"], ["b", "d"]], %{"status" => "ok", "batches" => [["a", "b"], ["c", "d"]]}},
                          {[], [["m", "n"]], %{"status" => "ok", "batches" => [["m"], ["n"]]}}
                        ]

                        Enum.with_index(cases)
                        |> Enum.each(fn {{tasks, edges, expected}, index} ->
                          actual = Solution.build_batches(tasks, edges) |> FullTestHelper.normalize_result()
                          FullTestHelper.assert_equal(actual, expected, "full_#{index}")
                        end)
                      end
                    end

                    FullTest.run()
                    """
                ),
            },
        },
        "inventory_reconcile": {
            "python": {
                "canonical_solution": dedent(
                    """
                    def reconcile_inventory(initial_stock, operations):
                        stock = {}
                        if isinstance(initial_stock, dict):
                            for key, value in initial_stock.items():
                                if isinstance(key, str) and isinstance(value, int) and not isinstance(value, bool):
                                    stock[key] = value
                        rejected = []
                        for index, operation in enumerate(operations):
                            if not isinstance(operation, dict):
                                rejected.append(index)
                                continue
                            kind = operation.get("kind")
                            sku = operation.get("sku")
                            qty = operation.get("qty")
                            if not isinstance(sku, str) or not isinstance(qty, int) or isinstance(qty, bool) or qty <= 0:
                                rejected.append(index)
                                continue
                            current = stock.get(sku, 0)
                            if kind == "restock":
                                stock[sku] = current + qty
                            elif kind == "reserve":
                                if current >= qty:
                                    stock[sku] = current - qty
                                else:
                                    rejected.append(index)
                            else:
                                rejected.append(index)
                        return {"stock": stock, "rejected_indexes": rejected}
                    """
                ),
                "demo_test_func": dedent(
                    """
                    def test():
                        assert reconcile_inventory({"pen": 3}, [{"kind": "reserve", "sku": "pen", "qty": 2}, {"kind": "reserve", "sku": "pen", "qty": 5}]) == {"stock": {"pen": 1}, "rejected_indexes": [1]}
                        assert reconcile_inventory({}, []) == {"stock": {}, "rejected_indexes": []}

                    if __name__ == "__main__":
                        test()
                    """
                ),
                "full_test_func": dedent(
                    """
                    def test():
                        cases = [
                            (
                                {"pen": 3},
                                [{"kind": "reserve", "sku": "pen", "qty": 2}, {"kind": "reserve", "sku": "pen", "qty": 5}],
                                {"stock": {"pen": 1}, "rejected_indexes": [1]},
                            ),
                            (
                                {},
                                [{"kind": "restock", "sku": "book", "qty": 4}, {"kind": "reserve", "sku": "book", "qty": 1}],
                                {"stock": {"book": 3}, "rejected_indexes": []},
                            ),
                            (
                                {"toy": 2},
                                [{"kind": "reserve", "sku": "toy", "qty": 2}, {"kind": "restock", "sku": "toy", "qty": 1}],
                                {"stock": {"toy": 1}, "rejected_indexes": []},
                            ),
                            (
                                {"toy": 2},
                                [{"kind": "ship", "sku": "toy", "qty": 1}, {"kind": "restock", "sku": "toy", "qty": 0}],
                                {"stock": {"toy": 2}, "rejected_indexes": [0, 1]},
                            ),
                        ]
                        for index, (stock, operations, expected) in enumerate(cases):
                            actual = reconcile_inventory(stock, operations)
                            assert actual == expected, f"case {index}: expected {expected!r}, got {actual!r}"

                    if __name__ == "__main__":
                        test()
                    """
                ),
            },
            "typescript": {
                "canonical_solution": dedent(
                    """
                    function reconcileInventory(initialStock: any, operations: any[]): { stock: Record<string, number>; rejected_indexes: number[] } {
                      const stock: Record<string, number> = {};
                      if (initialStock && typeof initialStock === "object") {
                        Object.entries(initialStock).forEach(([key, value]) => {
                          if (typeof key === "string" && typeof value === "number" && Number.isInteger(value)) stock[key] = value;
                        });
                      }
                      const rejected: number[] = [];
                      operations.forEach((operation, index) => {
                        if (!operation || typeof operation !== "object") {
                          rejected.push(index);
                          return;
                        }
                        const kind = (operation as any).kind;
                        const sku = (operation as any).sku;
                        const qty = (operation as any).qty;
                        if (typeof sku !== "string" || typeof qty !== "number" || !Number.isInteger(qty) || qty <= 0) {
                          rejected.push(index);
                          return;
                        }
                        const current = stock[sku] ?? 0;
                        if (kind === "restock") {
                          stock[sku] = current + qty;
                        } else if (kind === "reserve") {
                          if (current >= qty) stock[sku] = current - qty;
                          else rejected.push(index);
                        } else {
                          rejected.push(index);
                        }
                      });
                      return { stock, rejected_indexes: rejected };
                    }
                    """
                ),
                "demo_test_func": dedent(
                    """
                    function stable(value: any): any {
                      if (Array.isArray(value)) return value.map(stable);
                      if (value && typeof value === "object") {
                        const out: Record<string, any> = {};
                        Object.keys(value).sort().forEach((key) => { out[key] = stable(value[key]); });
                        return out;
                      }
                      return value;
                    }
                    function assertDeepEqual(actual: any, expected: any, label: string): void {
                      const a = JSON.stringify(stable(actual));
                      const e = JSON.stringify(stable(expected));
                      if (a !== e) throw new Error(`${label}: expected ${e}, got ${a}`);
                    }
                    function demoTesting(): void {
                      assertDeepEqual(reconcileInventory({ pen: 3 }, [{ kind: "reserve", sku: "pen", qty: 2 }, { kind: "reserve", sku: "pen", qty: 5 }]), { stock: { pen: 1 }, rejected_indexes: [1] }, "demo_1");
                      assertDeepEqual(reconcileInventory({}, []), { stock: {}, rejected_indexes: [] }, "demo_2");
                    }
                    demoTesting();
                    """
                ),
                "full_test_func": dedent(
                    """
                    function stable(value: any): any {
                      if (Array.isArray(value)) return value.map(stable);
                      if (value && typeof value === "object") {
                        const out: Record<string, any> = {};
                        Object.keys(value).sort().forEach((key) => { out[key] = stable(value[key]); });
                        return out;
                      }
                      return value;
                    }
                    function assertDeepEqual(actual: any, expected: any, label: string): void {
                      const a = JSON.stringify(stable(actual));
                      const e = JSON.stringify(stable(expected));
                      if (a !== e) throw new Error(`${label}: expected ${e}, got ${a}`);
                    }
                    function fullTesting(): void {
                      const cases: Array<[any, any[], any]> = [
                        [{ pen: 3 }, [{ kind: "reserve", sku: "pen", qty: 2 }, { kind: "reserve", sku: "pen", qty: 5 }], { stock: { pen: 1 }, rejected_indexes: [1] }],
                        [{}, [{ kind: "restock", sku: "book", qty: 4 }, { kind: "reserve", sku: "book", qty: 1 }], { stock: { book: 3 }, rejected_indexes: [] }],
                        [{ toy: 2 }, [{ kind: "reserve", sku: "toy", qty: 2 }, { kind: "restock", sku: "toy", qty: 1 }], { stock: { toy: 1 }, rejected_indexes: [] }],
                        [{ toy: 2 }, [{ kind: "ship", sku: "toy", qty: 1 }, { kind: "restock", sku: "toy", qty: 0 }], { stock: { toy: 2 }, rejected_indexes: [0, 1] }],
                      ];
                      cases.forEach(([stock, operations, expected], index) => {
                        assertDeepEqual(reconcileInventory(stock, operations), expected, `full_${index}`);
                      });
                    }
                    fullTesting();
                    """
                ),
            },
            "elixir": {
                "canonical_solution": dedent(
                    """
                    defmodule Solution do
                      def reconcile_inventory(initial_stock, operations) do
                        stock = normalize_stock(initial_stock)

                        Enum.with_index(operations)
                        |> Enum.reduce({stock, []}, fn {operation, index}, {stock_acc, rejected_acc} ->
                          case normalize_operation(operation) do
                            {:restock, sku, qty} ->
                              {Map.update(stock_acc, sku, qty, &(&1 + qty)), rejected_acc}

                            {:reserve, sku, qty} ->
                              current = Map.get(stock_acc, sku, 0)

                              if current >= qty do
                                {Map.put(stock_acc, sku, current - qty), rejected_acc}
                              else
                                {stock_acc, rejected_acc ++ [index]}
                              end

                            :error ->
                              {stock_acc, rejected_acc ++ [index]}
                          end
                        end)
                        |> then(fn {final_stock, rejected} -> %{"stock" => final_stock, "rejected_indexes" => rejected} end)
                      end

                      defp normalize_stock(map) when is_map(map) do
                        Enum.reduce(map, %{}, fn {key, value}, acc ->
                          if is_binary(to_string(key)) and is_integer(value) do
                            Map.put(acc, to_string(key), value)
                          else
                            acc
                          end
                        end)
                      end

                      defp normalize_stock(_), do: %{}

                      defp normalize_operation(%{"kind" => kind, "sku" => sku, "qty" => qty}), do: normalize_operation(%{kind: kind, sku: sku, qty: qty})
                      defp normalize_operation(%{kind: kind, sku: sku, qty: qty})
                           when is_binary(kind) and is_binary(sku) and is_integer(qty) and qty > 0 do
                        case kind do
                          "restock" -> {:restock, sku, qty}
                          "reserve" -> {:reserve, sku, qty}
                          _ -> :error
                        end
                      end

                      defp normalize_operation(_), do: :error
                    end
                    """
                ),
                "demo_test_func": dedent(
                    """
                    defmodule DemoTestHelper do
                      def get_key(map, key) when is_map(map), do: Map.get(map, key) || Map.get(map, String.to_atom(key))
                      def normalize_map(map) when is_map(map), do: Enum.reduce(map, %{}, fn {key, value}, acc -> Map.put(acc, to_string(key), value) end)
                      def normalize_result(value), do: %{"stock" => normalize_map(get_key(value, "stock") || %{}), "rejected_indexes" => get_key(value, "rejected_indexes") || []}
                      def assert_equal(actual, expected, label), do: if(actual != expected, do: raise("#{label}: expected #{inspect(expected)}, got #{inspect(actual)}"))
                    end

                    defmodule DemoTest do
                      def run do
                        DemoTestHelper.assert_equal(
                          Solution.reconcile_inventory(%{"pen" => 3}, [%{"kind" => "reserve", "sku" => "pen", "qty" => 2}, %{"kind" => "reserve", "sku" => "pen", "qty" => 5}]) |> DemoTestHelper.normalize_result(),
                          %{"stock" => %{"pen" => 1}, "rejected_indexes" => [1]},
                          "demo_1"
                        )

                        DemoTestHelper.assert_equal(
                          Solution.reconcile_inventory(%{}, []) |> DemoTestHelper.normalize_result(),
                          %{"stock" => %{}, "rejected_indexes" => []},
                          "demo_2"
                        )
                      end
                    end

                    DemoTest.run()
                    """
                ),
                "full_test_func": dedent(
                    """
                    defmodule FullTestHelper do
                      def get_key(map, key) when is_map(map), do: Map.get(map, key) || Map.get(map, String.to_atom(key))
                      def normalize_map(map) when is_map(map), do: Enum.reduce(map, %{}, fn {key, value}, acc -> Map.put(acc, to_string(key), value) end)
                      def normalize_result(value), do: %{"stock" => normalize_map(get_key(value, "stock") || %{}), "rejected_indexes" => get_key(value, "rejected_indexes") || []}
                      def assert_equal(actual, expected, label), do: if(actual != expected, do: raise("#{label}: expected #{inspect(expected)}, got #{inspect(actual)}"))
                    end

                    defmodule FullTest do
                      def run do
                        cases = [
                          {%{"pen" => 3}, [%{"kind" => "reserve", "sku" => "pen", "qty" => 2}, %{"kind" => "reserve", "sku" => "pen", "qty" => 5}], %{"stock" => %{"pen" => 1}, "rejected_indexes" => [1]}},
                          {%{}, [%{"kind" => "restock", "sku" => "book", "qty" => 4}, %{"kind" => "reserve", "sku" => "book", "qty" => 1}], %{"stock" => %{"book" => 3}, "rejected_indexes" => []}},
                          {%{"toy" => 2}, [%{"kind" => "reserve", "sku" => "toy", "qty" => 2}, %{"kind" => "restock", "sku" => "toy", "qty" => 1}], %{"stock" => %{"toy" => 1}, "rejected_indexes" => []}},
                          {%{"toy" => 2}, [%{"kind" => "ship", "sku" => "toy", "qty" => 1}, %{"kind" => "restock", "sku" => "toy", "qty" => 0}], %{"stock" => %{"toy" => 2}, "rejected_indexes" => [0, 1]}}
                        ]

                        Enum.with_index(cases)
                        |> Enum.each(fn {{stock, operations, expected}, index} ->
                          actual = Solution.reconcile_inventory(stock, operations) |> FullTestHelper.normalize_result()
                          FullTestHelper.assert_equal(actual, expected, "full_#{index}")
                        end)
                      end
                    end

                    FullTest.run()
                    """
                ),
            },
        },
        "session_durations": {
            "python": {
                "canonical_solution": dedent(
                    """
                    def session_durations(events):
                        totals = {}
                        active = {}
                        for event in events:
                            if not isinstance(event, dict):
                                continue
                            user = event.get("user")
                            kind = event.get("kind")
                            ts = event.get("ts")
                            if not isinstance(user, str) or not isinstance(kind, str) or not isinstance(ts, int) or isinstance(ts, bool):
                                continue
                            if kind == "login":
                                active[user] = ts
                            elif kind == "logout" and user in active:
                                start = active.pop(user)
                                totals[user] = totals.get(user, 0) + max(0, ts - start)
                        return totals
                    """
                ),
                "demo_test_func": dedent(
                    """
                    def test():
                        assert session_durations([
                            {"user": "ana", "kind": "login", "ts": 10},
                            {"user": "ana", "kind": "logout", "ts": 13},
                            {"user": "ana", "kind": "logout", "ts": 20},
                        ]) == {"ana": 3}
                        assert session_durations([]) == {}

                    if __name__ == "__main__":
                        test()
                    """
                ),
                "full_test_func": dedent(
                    """
                    def test():
                        cases = [
                            (
                                [
                                    {"user": "ana", "kind": "login", "ts": 10},
                                    {"user": "ana", "kind": "logout", "ts": 13},
                                    {"user": "ana", "kind": "logout", "ts": 20},
                                ],
                                {"ana": 3},
                            ),
                            (
                                [
                                    {"user": "a", "kind": "login", "ts": 1},
                                    {"user": "b", "kind": "login", "ts": 2},
                                    {"user": "a", "kind": "logout", "ts": 5},
                                    {"user": "b", "kind": "logout", "ts": 7},
                                ],
                                {"a": 4, "b": 5},
                            ),
                            (
                                [
                                    {"user": "a", "kind": "login", "ts": 1},
                                    {"user": "a", "kind": "login", "ts": 3},
                                    {"user": "a", "kind": "logout", "ts": 8},
                                ],
                                {"a": 5},
                            ),
                            (
                                [
                                    {"user": "a", "kind": "login", "ts": 1},
                                    {"user": "a", "kind": "logout", "ts": 1},
                                    {"user": "a", "kind": "login", "ts": 2},
                                ],
                                {"a": 0},
                            ),
                        ]
                        for index, (events, expected) in enumerate(cases):
                            actual = session_durations(events)
                            assert actual == expected, f"case {index}: expected {expected!r}, got {actual!r}"

                    if __name__ == "__main__":
                        test()
                    """
                ),
            },
            "typescript": {
                "canonical_solution": dedent(
                    """
                    function sessionDurations(events: any[]): Record<string, number> {
                      const totals: Record<string, number> = {};
                      const active: Record<string, number> = {};
                      for (const event of events) {
                        if (!event || typeof event !== "object") continue;
                        const user = (event as any).user;
                        const kind = (event as any).kind;
                        const ts = (event as any).ts;
                        if (typeof user !== "string" || typeof kind !== "string" || typeof ts !== "number" || !Number.isInteger(ts)) continue;
                        if (kind === "login") {
                          active[user] = ts;
                        } else if (kind === "logout" && Object.prototype.hasOwnProperty.call(active, user)) {
                          const start = active[user];
                          delete active[user];
                          totals[user] = (totals[user] ?? 0) + Math.max(0, ts - start);
                        }
                      }
                      return totals;
                    }
                    """
                ),
                "demo_test_func": dedent(
                    """
                    function stable(value: any): any {
                      if (Array.isArray(value)) return value.map(stable);
                      if (value && typeof value === "object") {
                        const out: Record<string, any> = {};
                        Object.keys(value).sort().forEach((key) => { out[key] = stable(value[key]); });
                        return out;
                      }
                      return value;
                    }
                    function assertDeepEqual(actual: any, expected: any, label: string): void {
                      const a = JSON.stringify(stable(actual));
                      const e = JSON.stringify(stable(expected));
                      if (a !== e) throw new Error(`${label}: expected ${e}, got ${a}`);
                    }
                    function demoTesting(): void {
                      assertDeepEqual(sessionDurations([{ user: "ana", kind: "login", ts: 10 }, { user: "ana", kind: "logout", ts: 13 }, { user: "ana", kind: "logout", ts: 20 }]), { ana: 3 }, "demo_1");
                      assertDeepEqual(sessionDurations([]), {}, "demo_2");
                    }
                    demoTesting();
                    """
                ),
                "full_test_func": dedent(
                    """
                    function stable(value: any): any {
                      if (Array.isArray(value)) return value.map(stable);
                      if (value && typeof value === "object") {
                        const out: Record<string, any> = {};
                        Object.keys(value).sort().forEach((key) => { out[key] = stable(value[key]); });
                        return out;
                      }
                      return value;
                    }
                    function assertDeepEqual(actual: any, expected: any, label: string): void {
                      const a = JSON.stringify(stable(actual));
                      const e = JSON.stringify(stable(expected));
                      if (a !== e) throw new Error(`${label}: expected ${e}, got ${a}`);
                    }
                    function fullTesting(): void {
                      const cases: Array<[any[], any]> = [
                        [[{ user: "ana", kind: "login", ts: 10 }, { user: "ana", kind: "logout", ts: 13 }, { user: "ana", kind: "logout", ts: 20 }], { ana: 3 }],
                        [[{ user: "a", kind: "login", ts: 1 }, { user: "b", kind: "login", ts: 2 }, { user: "a", kind: "logout", ts: 5 }, { user: "b", kind: "logout", ts: 7 }], { a: 4, b: 5 }],
                        [[{ user: "a", kind: "login", ts: 1 }, { user: "a", kind: "login", ts: 3 }, { user: "a", kind: "logout", ts: 8 }], { a: 5 }],
                        [[{ user: "a", kind: "login", ts: 1 }, { user: "a", kind: "logout", ts: 1 }, { user: "a", kind: "login", ts: 2 }], { a: 0 }],
                      ];
                      cases.forEach(([events, expected], index) => {
                        assertDeepEqual(sessionDurations(events), expected, `full_${index}`);
                      });
                    }
                    fullTesting();
                    """
                ),
            },
            "elixir": {
                "canonical_solution": dedent(
                    """
                    defmodule Solution do
                      def session_durations(events) when is_list(events) do
                        {totals, _active} =
                          Enum.reduce(events, {%{}, %{}}, fn event, {totals, active} ->
                            case normalize_event(event) do
                              {:ok, user, "login", ts} ->
                                {totals, Map.put(active, user, ts)}

                              {:ok, user, "logout", ts} ->
                                case Map.fetch(active, user) do
                                  {:ok, start} ->
                                    updated_total = Map.get(totals, user, 0) + max(0, ts - start)
                                    {Map.put(totals, user, updated_total), Map.delete(active, user)}

                                  :error ->
                                    {totals, active}
                                end

                              :error ->
                                {totals, active}
                            end
                          end)

                        totals
                      end

                      def session_durations(_), do: %{}

                      defp normalize_event(%{"user" => user, "kind" => kind, "ts" => ts}), do: normalize_event(%{user: user, kind: kind, ts: ts})
                      defp normalize_event(%{user: user, kind: kind, ts: ts})
                           when is_binary(user) and is_binary(kind) and is_integer(ts),
                           do: {:ok, user, kind, ts}
                      defp normalize_event(_), do: :error
                    end
                    """
                ),
                "demo_test_func": dedent(
                    """
                    defmodule DemoTestHelper do
                      def normalize_map(map) when is_map(map), do: Enum.reduce(map, %{}, fn {key, value}, acc -> Map.put(acc, to_string(key), value) end)
                      def assert_equal(actual, expected, label), do: if(actual != expected, do: raise("#{label}: expected #{inspect(expected)}, got #{inspect(actual)}"))
                    end

                    defmodule DemoTest do
                      def run do
                        DemoTestHelper.assert_equal(
                          Solution.session_durations([
                            %{"user" => "ana", "kind" => "login", "ts" => 10},
                            %{"user" => "ana", "kind" => "logout", "ts" => 13},
                            %{"user" => "ana", "kind" => "logout", "ts" => 20}
                          ]) |> DemoTestHelper.normalize_map(),
                          %{"ana" => 3},
                          "demo_1"
                        )

                        DemoTestHelper.assert_equal(
                          Solution.session_durations([]) |> DemoTestHelper.normalize_map(),
                          %{},
                          "demo_2"
                        )
                      end
                    end

                    DemoTest.run()
                    """
                ),
                "full_test_func": dedent(
                    """
                    defmodule FullTestHelper do
                      def normalize_map(map) when is_map(map), do: Enum.reduce(map, %{}, fn {key, value}, acc -> Map.put(acc, to_string(key), value) end)
                      def assert_equal(actual, expected, label), do: if(actual != expected, do: raise("#{label}: expected #{inspect(expected)}, got #{inspect(actual)}"))
                    end

                    defmodule FullTest do
                      def run do
                        cases = [
                          {
                            [
                              %{"user" => "ana", "kind" => "login", "ts" => 10},
                              %{"user" => "ana", "kind" => "logout", "ts" => 13},
                              %{"user" => "ana", "kind" => "logout", "ts" => 20}
                            ],
                            %{"ana" => 3}
                          },
                          {
                            [
                              %{"user" => "a", "kind" => "login", "ts" => 1},
                              %{"user" => "b", "kind" => "login", "ts" => 2},
                              %{"user" => "a", "kind" => "logout", "ts" => 5},
                              %{"user" => "b", "kind" => "logout", "ts" => 7}
                            ],
                            %{"a" => 4, "b" => 5}
                          },
                          {
                            [
                              %{"user" => "a", "kind" => "login", "ts" => 1},
                              %{"user" => "a", "kind" => "login", "ts" => 3},
                              %{"user" => "a", "kind" => "logout", "ts" => 8}
                            ],
                            %{"a" => 5}
                          },
                          {
                            [
                              %{"user" => "a", "kind" => "login", "ts" => 1},
                              %{"user" => "a", "kind" => "logout", "ts" => 1},
                              %{"user" => "a", "kind" => "login", "ts" => 2}
                            ],
                            %{"a" => 0}
                          }
                        ]

                        Enum.with_index(cases)
                        |> Enum.each(fn {{events, expected}, index} ->
                          actual = Solution.session_durations(events) |> FullTestHelper.normalize_map()
                          FullTestHelper.assert_equal(actual, expected, "full_#{index}")
                        end)
                      end
                    end

                    FullTest.run()
                    """
                ),
            },
        },
        "window_majority": {
            "python": {
                "canonical_solution": dedent(
                    """
                    def window_majorities(values, k):
                        if not isinstance(k, int) or isinstance(k, bool) or k < 1 or k > len(values):
                            return {"status": "error", "reason": "invalid_k"}
                        outputs = []
                        for start in range(0, len(values) - k + 1):
                            window = values[start:start + k]
                            counts = {}
                            for item in window:
                                counts[item] = counts.get(item, 0) + 1
                            majority = None
                            for item, count in counts.items():
                                if count > k // 2:
                                    majority = item
                                    break
                            outputs.append(majority)
                        return {"status": "ok", "values": outputs}
                    """
                ),
                "demo_test_func": dedent(
                    """
                    def test():
                        assert window_majorities([1, 1, 2, 2, 2], 3) == {"status": "ok", "values": [1, 2, 2]}
                        assert window_majorities([1, 2], 3) == {"status": "error", "reason": "invalid_k"}

                    if __name__ == "__main__":
                        test()
                    """
                ),
                "full_test_func": dedent(
                    """
                    def test():
                        cases = [
                            (([1, 1, 2, 2, 2], 3), {"status": "ok", "values": [1, 2, 2]}),
                            (([1, 2], 3), {"status": "error", "reason": "invalid_k"}),
                            (([5], 1), {"status": "ok", "values": [5]}),
                            (([1, 2, 3, 4], 2), {"status": "ok", "values": [None, None, None]}),
                            ((["a", "a", "b", "a"], 3), {"status": "ok", "values": ["a", "a"]}),
                        ]
                        for index, ((values, k), expected) in enumerate(cases):
                            actual = window_majorities(values, k)
                            assert actual == expected, f"case {index}: expected {expected!r}, got {actual!r}"

                    if __name__ == "__main__":
                        test()
                    """
                ),
            },
            "typescript": {
                "canonical_solution": dedent(
                    """
                    function windowMajorities(values: any[], k: number): { status: string; values?: any[]; reason?: string } {
                      if (!Number.isInteger(k) || k < 1 || k > values.length) return { status: "error", reason: "invalid_k" };
                      const outputs: any[] = [];
                      for (let start = 0; start <= values.length - k; start += 1) {
                        const counts = new Map<any, number>();
                        for (const item of values.slice(start, start + k)) counts.set(item, (counts.get(item) ?? 0) + 1);
                        let majority: any = null;
                        for (const [item, count] of counts.entries()) {
                          if (count > Math.floor(k / 2)) {
                            majority = item;
                            break;
                          }
                        }
                        outputs.push(majority);
                      }
                      return { status: "ok", values: outputs };
                    }
                    """
                ),
                "demo_test_func": dedent(
                    """
                    function stable(value: any): any {
                      if (Array.isArray(value)) return value.map(stable);
                      if (value && typeof value === "object") {
                        const out: Record<string, any> = {};
                        Object.keys(value).sort().forEach((key) => { out[key] = stable(value[key]); });
                        return out;
                      }
                      return value;
                    }
                    function assertDeepEqual(actual: any, expected: any, label: string): void {
                      const a = JSON.stringify(stable(actual));
                      const e = JSON.stringify(stable(expected));
                      if (a !== e) throw new Error(`${label}: expected ${e}, got ${a}`);
                    }
                    function demoTesting(): void {
                      assertDeepEqual(windowMajorities([1, 1, 2, 2, 2], 3), { status: "ok", values: [1, 2, 2] }, "demo_1");
                      assertDeepEqual(windowMajorities([1, 2], 3), { status: "error", reason: "invalid_k" }, "demo_2");
                    }
                    demoTesting();
                    """
                ),
                "full_test_func": dedent(
                    """
                    function stable(value: any): any {
                      if (Array.isArray(value)) return value.map(stable);
                      if (value && typeof value === "object") {
                        const out: Record<string, any> = {};
                        Object.keys(value).sort().forEach((key) => { out[key] = stable(value[key]); });
                        return out;
                      }
                      return value;
                    }
                    function assertDeepEqual(actual: any, expected: any, label: string): void {
                      const a = JSON.stringify(stable(actual));
                      const e = JSON.stringify(stable(expected));
                      if (a !== e) throw new Error(`${label}: expected ${e}, got ${a}`);
                    }
                    function fullTesting(): void {
                      const cases: Array<[[any[], number], any]> = [
                        [[[1, 1, 2, 2, 2], 3], { status: "ok", values: [1, 2, 2] }],
                        [[[1, 2], 3], { status: "error", reason: "invalid_k" }],
                        [[[5], 1], { status: "ok", values: [5] }],
                        [[[1, 2, 3, 4], 2], { status: "ok", values: [null, null, null] }],
                        [[["a", "a", "b", "a"], 3], { status: "ok", values: ["a", "a"] }],
                      ];
                      cases.forEach((entry, index) => {
                        const [[values, k], expected] = entry;
                        assertDeepEqual(windowMajorities(values, k), expected, `full_${index}`);
                      });
                    }
                    fullTesting();
                    """
                ),
            },
            "elixir": {
                "canonical_solution": dedent(
                    """
                    defmodule Solution do
                      def window_majorities(values, k) when is_list(values) and is_integer(k) and k >= 1 and k <= length(values) do
                        outputs =
                          0..(length(values) - k)
                          |> Enum.map(fn start ->
                            window = Enum.slice(values, start, k)
                            counts = Enum.reduce(window, %{}, fn item, acc -> Map.update(acc, item, 1, &(&1 + 1)) end)
                            Enum.find_value(counts, nil, fn {item, count} -> if count > div(k, 2), do: item, else: nil end)
                          end)

                        %{"status" => "ok", "values" => outputs}
                      end

                      def window_majorities(_values, _k), do: %{"status" => "error", "reason" => "invalid_k"}
                    end
                    """
                ),
                "demo_test_func": dedent(
                    """
                    defmodule DemoTestHelper do
                      def get_key(map, key) when is_map(map), do: Map.get(map, key) || Map.get(map, String.to_atom(key))
                      def normalize_result(value) do
                        result = %{"status" => get_key(value, "status")}
                        result = if get_key(value, "values"), do: Map.put(result, "values", get_key(value, "values")), else: result
                        if get_key(value, "reason"), do: Map.put(result, "reason", get_key(value, "reason")), else: result
                      end
                      def assert_equal(actual, expected, label), do: if(actual != expected, do: raise("#{label}: expected #{inspect(expected)}, got #{inspect(actual)}"))
                    end

                    defmodule DemoTest do
                      def run do
                        DemoTestHelper.assert_equal(
                          Solution.window_majorities([1, 1, 2, 2, 2], 3) |> DemoTestHelper.normalize_result(),
                          %{"status" => "ok", "values" => [1, 2, 2]},
                          "demo_1"
                        )

                        DemoTestHelper.assert_equal(
                          Solution.window_majorities([1, 2], 3) |> DemoTestHelper.normalize_result(),
                          %{"status" => "error", "reason" => "invalid_k"},
                          "demo_2"
                        )
                      end
                    end

                    DemoTest.run()
                    """
                ),
                "full_test_func": dedent(
                    """
                    defmodule FullTestHelper do
                      def get_key(map, key) when is_map(map), do: Map.get(map, key) || Map.get(map, String.to_atom(key))
                      def normalize_result(value) do
                        result = %{"status" => get_key(value, "status")}
                        result = if get_key(value, "values"), do: Map.put(result, "values", get_key(value, "values")), else: result
                        if get_key(value, "reason"), do: Map.put(result, "reason", get_key(value, "reason")), else: result
                      end
                      def assert_equal(actual, expected, label), do: if(actual != expected, do: raise("#{label}: expected #{inspect(expected)}, got #{inspect(actual)}"))
                    end

                    defmodule FullTest do
                      def run do
                        cases = [
                          {[1, 1, 2, 2, 2], 3, %{"status" => "ok", "values" => [1, 2, 2]}},
                          {[1, 2], 3, %{"status" => "error", "reason" => "invalid_k"}},
                          {[5], 1, %{"status" => "ok", "values" => [5]}},
                          {[1, 2, 3, 4], 2, %{"status" => "ok", "values" => [nil, nil, nil]}},
                          {["a", "a", "b", "a"], 3, %{"status" => "ok", "values" => ["a", "a"]}}
                        ]

                        Enum.with_index(cases)
                        |> Enum.each(fn {{values, k, expected}, index} ->
                          actual = Solution.window_majorities(values, k) |> FullTestHelper.normalize_result()
                          FullTestHelper.assert_equal(actual, expected, "full_#{index}")
                        end)
                      end
                    end

                    FullTest.run()
                    """
                ),
            },
        },
        "rule_based_discount": {
            "python": {
                "canonical_solution": dedent(
                    """
                    def apply_discount(order, rules):
                        total = float(order.get("total", 0))
                        item_count = int(order.get("item_count", 0))
                        tier = order.get("tier")
                        for rule in rules:
                            if not isinstance(rule, dict):
                                continue
                            min_total = rule.get("min_total", 0)
                            min_item_count = rule.get("min_item_count", 0)
                            rule_tier = rule.get("tier")
                            if total < min_total or item_count < min_item_count:
                                continue
                            if rule_tier is not None and tier != rule_tier:
                                continue
                            discount_pct = rule.get("discount_pct", 0)
                            final_total = round(total * (100 - discount_pct) / 100, 2)
                            return {"applied_rule": rule.get("id", "unknown"), "final_total": final_total}
                        return {"applied_rule": "no_match", "final_total": round(total, 2)}
                    """
                ),
                "demo_test_func": dedent(
                    """
                    def _assert_close(actual, expected, label):
                        assert actual["applied_rule"] == expected["applied_rule"], f"{label}: rule mismatch"
                        assert abs(actual["final_total"] - expected["final_total"]) < 1e-9, f"{label}: total mismatch"

                    def test():
                        _assert_close(
                            apply_discount({"total": 120, "item_count": 3, "tier": "gold"}, [{"id": "gold10", "min_total": 100, "tier": "gold", "discount_pct": 10}]),
                            {"applied_rule": "gold10", "final_total": 108.0},
                            "demo_1",
                        )
                        _assert_close(
                            apply_discount({"total": 40, "item_count": 1, "tier": None}, []),
                            {"applied_rule": "no_match", "final_total": 40.0},
                            "demo_2",
                        )

                    if __name__ == "__main__":
                        test()
                    """
                ),
                "full_test_func": dedent(
                    """
                    def _assert_close(actual, expected, label):
                        assert actual["applied_rule"] == expected["applied_rule"], f"{label}: rule mismatch"
                        assert abs(actual["final_total"] - expected["final_total"]) < 1e-9, f"{label}: total mismatch"

                    def test():
                        cases = [
                            (
                                {"total": 120, "item_count": 3, "tier": "gold"},
                                [{"id": "gold10", "min_total": 100, "tier": "gold", "discount_pct": 10}],
                                {"applied_rule": "gold10", "final_total": 108.0},
                            ),
                            (
                                {"total": 50, "item_count": 1, "tier": None},
                                [{"id": "bulk20", "min_item_count": 3, "discount_pct": 20}],
                                {"applied_rule": "no_match", "final_total": 50.0},
                            ),
                            (
                                {"total": 90, "item_count": 4, "tier": "silver"},
                                [
                                    {"id": "tier5", "tier": "silver", "discount_pct": 5},
                                    {"id": "bulk20", "min_item_count": 3, "discount_pct": 20},
                                ],
                                {"applied_rule": "tier5", "final_total": 85.5},
                            ),
                            (
                                {"total": 200, "item_count": 5, "tier": "gold"},
                                [
                                    {"id": "first", "min_total": 150, "discount_pct": 0},
                                    {"id": "second", "min_total": 100, "discount_pct": 50},
                                ],
                                {"applied_rule": "first", "final_total": 200.0},
                            ),
                        ]
                        for index, (order, rules, expected) in enumerate(cases):
                            _assert_close(apply_discount(order, rules), expected, f"full_{index}")

                    if __name__ == "__main__":
                        test()
                    """
                ),
            },
            "typescript": {
                "canonical_solution": dedent(
                    """
                    function applyDiscount(order: any, rules: any[]): { applied_rule: string; final_total: number } {
                      const total = typeof order?.total === "number" ? order.total : 0;
                      const itemCount = typeof order?.item_count === "number" ? order.item_count : 0;
                      const tier = order?.tier ?? null;
                      for (const rule of rules) {
                        if (!rule || typeof rule !== "object") continue;
                        const minTotal = typeof rule.min_total === "number" ? rule.min_total : 0;
                        const minItemCount = typeof rule.min_item_count === "number" ? rule.min_item_count : 0;
                        const ruleTier = rule.tier ?? null;
                        if (total < minTotal || itemCount < minItemCount) continue;
                        if (ruleTier !== null && tier !== ruleTier) continue;
                        const discountPct = typeof rule.discount_pct === "number" ? rule.discount_pct : 0;
                        const finalTotal = Math.round(total * (100 - discountPct)) / 100;
                        return { applied_rule: typeof rule.id === "string" ? rule.id : "unknown", final_total: finalTotal };
                      }
                      return { applied_rule: "no_match", final_total: Math.round(total * 100) / 100 };
                    }
                    """
                ),
                "demo_test_func": dedent(
                    """
                    function assertClose(actual: any, expected: any, label: string): void {
                      if (actual.applied_rule !== expected.applied_rule) throw new Error(`${label}: rule mismatch`);
                      if (Math.abs(actual.final_total - expected.final_total) > 1e-9) throw new Error(`${label}: total mismatch`);
                    }
                    function demoTesting(): void {
                      assertClose(applyDiscount({ total: 120, item_count: 3, tier: "gold" }, [{ id: "gold10", min_total: 100, tier: "gold", discount_pct: 10 }]), { applied_rule: "gold10", final_total: 108.0 }, "demo_1");
                      assertClose(applyDiscount({ total: 40, item_count: 1, tier: null }, []), { applied_rule: "no_match", final_total: 40.0 }, "demo_2");
                    }
                    demoTesting();
                    """
                ),
                "full_test_func": dedent(
                    """
                    function assertClose(actual: any, expected: any, label: string): void {
                      if (actual.applied_rule !== expected.applied_rule) throw new Error(`${label}: rule mismatch`);
                      if (Math.abs(actual.final_total - expected.final_total) > 1e-9) throw new Error(`${label}: total mismatch`);
                    }
                    function fullTesting(): void {
                      const cases: Array<[any, any[], any]> = [
                        [{ total: 120, item_count: 3, tier: "gold" }, [{ id: "gold10", min_total: 100, tier: "gold", discount_pct: 10 }], { applied_rule: "gold10", final_total: 108.0 }],
                        [{ total: 50, item_count: 1, tier: null }, [{ id: "bulk20", min_item_count: 3, discount_pct: 20 }], { applied_rule: "no_match", final_total: 50.0 }],
                        [{ total: 90, item_count: 4, tier: "silver" }, [{ id: "tier5", tier: "silver", discount_pct: 5 }, { id: "bulk20", min_item_count: 3, discount_pct: 20 }], { applied_rule: "tier5", final_total: 85.5 }],
                        [{ total: 200, item_count: 5, tier: "gold" }, [{ id: "first", min_total: 150, discount_pct: 0 }, { id: "second", min_total: 100, discount_pct: 50 }], { applied_rule: "first", final_total: 200.0 }],
                      ];
                      cases.forEach(([order, rules, expected], index) => {
                        assertClose(applyDiscount(order, rules), expected, `full_${index}`);
                      });
                    }
                    fullTesting();
                    """
                ),
            },
            "elixir": {
                "canonical_solution": dedent(
                    """
                    defmodule Solution do
                      def apply_discount(order, rules) when is_map(order) and is_list(rules) do
                        total = numeric_field(order, "total")
                        item_count = integer_field(order, "item_count")
                        tier = map_field(order, "tier")

                        Enum.find_value(rules, fn rule ->
                          if rule_matches?(rule, total, item_count, tier) do
                            discount_pct = integer_field(rule, "discount_pct")
                            final_total = Float.round(total * (100 - discount_pct) / 100, 2)
                            %{"applied_rule" => map_field(rule, "id") || "unknown", "final_total" => final_total}
                          else
                            nil
                          end
                        end) || %{"applied_rule" => "no_match", "final_total" => Float.round(total, 2)}
                      end

                      def apply_discount(_order, _rules), do: %{"applied_rule" => "no_match", "final_total" => 0.0}

                      defp rule_matches?(rule, total, item_count, tier) when is_map(rule) do
                        total >= numeric_field(rule, "min_total") and
                          item_count >= integer_field(rule, "min_item_count") and
                          tier_matches?(map_field(rule, "tier"), tier)
                      end

                      defp rule_matches?(_, _, _, _), do: false

                      defp tier_matches?(nil, _tier), do: true
                      defp tier_matches?(expected, tier), do: expected == tier

                      defp map_field(map, key), do: Map.get(map, key) || Map.get(map, String.to_atom(key))

                      defp numeric_field(map, key) do
                        case map_field(map, key) do
                          number when is_number(number) -> number * 1.0
                          _ -> 0.0
                        end
                      end

                      defp integer_field(map, key) do
                        case map_field(map, key) do
                          number when is_integer(number) -> number
                          _ -> 0
                        end
                      end
                    end
                    """
                ),
                "demo_test_func": dedent(
                    """
                    defmodule DemoTestHelper do
                      def get_key(map, key) when is_map(map), do: Map.get(map, key) || Map.get(map, String.to_atom(key))
                      def assert_close(actual, expected, label) do
                        if get_key(actual, "applied_rule") != expected["applied_rule"], do: raise("#{label}: rule mismatch")
                        if abs(get_key(actual, "final_total") - expected["final_total"]) > 1.0e-9, do: raise("#{label}: total mismatch")
                      end
                    end

                    defmodule DemoTest do
                      def run do
                        DemoTestHelper.assert_close(
                          Solution.apply_discount(%{"total" => 120, "item_count" => 3, "tier" => "gold"}, [%{"id" => "gold10", "min_total" => 100, "tier" => "gold", "discount_pct" => 10}]),
                          %{"applied_rule" => "gold10", "final_total" => 108.0},
                          "demo_1"
                        )

                        DemoTestHelper.assert_close(
                          Solution.apply_discount(%{"total" => 40, "item_count" => 1, "tier" => nil}, []),
                          %{"applied_rule" => "no_match", "final_total" => 40.0},
                          "demo_2"
                        )
                      end
                    end

                    DemoTest.run()
                    """
                ),
                "full_test_func": dedent(
                    """
                    defmodule FullTestHelper do
                      def get_key(map, key) when is_map(map), do: Map.get(map, key) || Map.get(map, String.to_atom(key))
                      def assert_close(actual, expected, label) do
                        if get_key(actual, "applied_rule") != expected["applied_rule"], do: raise("#{label}: rule mismatch")
                        if abs(get_key(actual, "final_total") - expected["final_total"]) > 1.0e-9, do: raise("#{label}: total mismatch")
                      end
                    end

                    defmodule FullTest do
                      def run do
                        cases = [
                          {%{"total" => 120, "item_count" => 3, "tier" => "gold"}, [%{"id" => "gold10", "min_total" => 100, "tier" => "gold", "discount_pct" => 10}], %{"applied_rule" => "gold10", "final_total" => 108.0}},
                          {%{"total" => 50, "item_count" => 1, "tier" => nil}, [%{"id" => "bulk20", "min_item_count" => 3, "discount_pct" => 20}], %{"applied_rule" => "no_match", "final_total" => 50.0}},
                          {%{"total" => 90, "item_count" => 4, "tier" => "silver"}, [%{"id" => "tier5", "tier" => "silver", "discount_pct" => 5}, %{"id" => "bulk20", "min_item_count" => 3, "discount_pct" => 20}], %{"applied_rule" => "tier5", "final_total" => 85.5}},
                          {%{"total" => 200, "item_count" => 5, "tier" => "gold"}, [%{"id" => "first", "min_total" => 150, "discount_pct" => 0}, %{"id" => "second", "min_total" => 100, "discount_pct" => 50}], %{"applied_rule" => "first", "final_total" => 200.0}}
                        ]

                        Enum.with_index(cases)
                        |> Enum.each(fn {{order, rules, expected}, index} ->
                          FullTestHelper.assert_close(Solution.apply_discount(order, rules), expected, "full_#{index}")
                        end)
                      end
                    end

                    FullTest.run()
                    """
                ),
            },
        },
    }
    implementations.update(build_additional_implementations())
    return implementations


def build_rows() -> list[dict[str, Any]]:
    prompt_rows: list[dict[str, Any]] = []
    with (GENERATED_DIR / "prompt_records.jsonl").open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                prompt_rows.append(json.loads(line))

    implementations = build_implementations()
    benchmark_rows: list[dict[str, Any]] = []
    for row in prompt_rows:
        impl = implementations[row["task_id"]][row["language"]]
        benchmark_rows.append(
            {
                "study_id": row["study_id"],
                "experiment_id": f"{row['task_id']}:{row['language']}:{row['condition_id']}",
                "task_id": row["task_id"],
                "title": row["title"],
                "language": row["language"],
                "condition_id": row["condition_id"],
                "focus_dimensions": row["focus_dimensions"],
                "hypothesis_tags": row["hypothesis_tags"],
                "question": augment_question(row["question"], row["task_id"], row["language"]),
                "canonical_solution": impl["canonical_solution"],
                "demo_test_func": impl["demo_test_func"],
                "full_test_func": impl["full_test_func"],
            }
        )
    return benchmark_rows


def main() -> None:
    rows = build_rows()
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    write_jsonl(DATA_DIR / "benchmark.jsonl", rows)
    write_csv(
        DATA_DIR / "benchmark_manifest.csv",
        [
            {
                "experiment_id": row["experiment_id"],
                "task_id": row["task_id"],
                "language": row["language"],
                "condition_id": row["condition_id"],
                "title": row["title"],
            }
            for row in rows
        ],
    )
    (DATA_DIR / "summary.json").write_text(
        json.dumps(
            {
                "row_count": len(rows),
                "task_count": len({row["task_id"] for row in rows}),
                "language_count": len({row["language"] for row in rows}),
                "condition_count": len({row["condition_id"] for row in rows}),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
