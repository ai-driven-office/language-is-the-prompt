#!/usr/bin/env python3

from __future__ import annotations

import textwrap


def dedent(text: str) -> str:
    return textwrap.dedent(text).strip() + "\n"


ADDITIONAL_RETURN_CONTRACT_NOTES = {
    "merge_intervals": "Return a list/array of inclusive [start, end] pairs.",
    "top_k_frequencies": "Return {status: \"ok\", items: [...]} or {status: \"error\", reason: \"invalid_k\"}.",
    "queue_wait_times": "Return a list/array of {id, wait} rows in valid-job order.",
    "normalize_phone_book": "Return a list/array of {phone, names} rows sorted by normalized phone.",
    "stable_group_runs": "Return a list/array of {value, count} rows.",
    "token_bucket_decisions": "Return {status: \"ok\", allowed: [...], remaining: n} or an error contract.",
    "dense_rankings": "Return a list/array of {name, rank} rows in sorted order.",
    "bracket_balance_report": "Return {balanced: boolean, first_error_index: integer_or_null}.",
}


def build_additional_implementations() -> dict[str, dict[str, dict[str, str]]]:
    return {
        "merge_intervals": {
            "python": {
                "canonical_solution": dedent(
                    """
                    def merge_intervals(intervals):
                        normalized = []
                        if not isinstance(intervals, list):
                            return normalized
                        for entry in intervals:
                            if (
                                isinstance(entry, (list, tuple))
                                and len(entry) == 2
                                and isinstance(entry[0], int)
                                and not isinstance(entry[0], bool)
                                and isinstance(entry[1], int)
                                and not isinstance(entry[1], bool)
                            ):
                                left, right = entry
                                if left > right:
                                    left, right = right, left
                                normalized.append([left, right])
                        normalized.sort()
                        merged = []
                        for start, end in normalized:
                            if not merged or start > merged[-1][1] + 1:
                                merged.append([start, end])
                            else:
                                merged[-1][1] = max(merged[-1][1], end)
                        return merged
                    """
                ),
                "demo_test_func": dedent(
                    """
                    def test():
                        assert merge_intervals([[1, 3], [2, 4], [6, 6]]) == [[1, 4], [6, 6]]
                        assert merge_intervals([]) == []

                    if __name__ == "__main__":
                        test()
                    """
                ),
                "full_test_func": dedent(
                    """
                    def test():
                        cases = [
                            ([[1, 3], [2, 4], [6, 6]], [[1, 4], [6, 6]]),
                            ([], []),
                            ([[5, 2], [8, 10], [10, 12]], [[2, 5], [8, 12]]),
                            ([[1, 1], [3, 5], [2, 2]], [[1, 5]]),
                            ([[0, 0], "bad", [4, 4], [2, 3]], [[0, 0], [2, 4]]),
                        ]
                        for index, (intervals, expected) in enumerate(cases):
                            actual = merge_intervals(intervals)
                            assert actual == expected, f"case {index}: expected {expected!r}, got {actual!r}"

                    if __name__ == "__main__":
                        test()
                    """
                ),
            },
            "typescript": {
                "canonical_solution": dedent(
                    """
                    function mergeIntervals(intervals: unknown): number[][] {
                      const normalized: number[][] = [];
                      if (!Array.isArray(intervals)) return normalized;
                      for (const entry of intervals) {
                        if (
                          Array.isArray(entry) &&
                          entry.length === 2 &&
                          Number.isInteger(entry[0]) &&
                          Number.isInteger(entry[1])
                        ) {
                          const left = entry[0] as number;
                          const right = entry[1] as number;
                          normalized.push(left <= right ? [left, right] : [right, left]);
                        }
                      }
                      normalized.sort((a, b) => (a[0] - b[0]) || (a[1] - b[1]));
                      const merged: number[][] = [];
                      for (const [start, end] of normalized) {
                        if (merged.length === 0 || start > merged[merged.length - 1][1] + 1) {
                          merged.push([start, end]);
                        } else {
                          merged[merged.length - 1][1] = Math.max(merged[merged.length - 1][1], end);
                        }
                      }
                      return merged;
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
                      assertDeepEqual(mergeIntervals([[1, 3], [2, 4], [6, 6]]), [[1, 4], [6, 6]], "demo_1");
                      assertDeepEqual(mergeIntervals([]), [], "demo_2");
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
                      const cases: Array<[any, any]> = [
                        [[[1, 3], [2, 4], [6, 6]], [[1, 4], [6, 6]]],
                        [[], []],
                        [[[5, 2], [8, 10], [10, 12]], [[2, 5], [8, 12]]],
                        [[[1, 1], [3, 5], [2, 2]], [[1, 5]]],
                        [[[0, 0], "bad", [4, 4], [2, 3]], [[0, 0], [2, 4]]],
                      ];
                      cases.forEach(([intervals, expected], index) => {
                        assertDeepEqual(mergeIntervals(intervals), expected, `full_${index}`);
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
                      def merge_intervals(intervals) when is_list(intervals) do
                        intervals
                        |> Enum.reduce([], fn
                          [left, right], acc when is_integer(left) and is_integer(right) ->
                            [{min(left, right), max(left, right)} | acc]

                          {left, right}, acc when is_integer(left) and is_integer(right) ->
                            [{min(left, right), max(left, right)} | acc]

                          _, acc ->
                            acc
                        end)
                        |> Enum.sort()
                        |> Enum.reduce([], fn {start, finish}, acc ->
                          case acc do
                            [] ->
                              [{start, finish}]

                            [{last_start, last_finish} | rest] when start <= last_finish + 1 ->
                              [{last_start, max(last_finish, finish)} | rest]

                            _ ->
                              [{start, finish} | acc]
                          end
                        end)
                        |> Enum.reverse()
                        |> Enum.map(fn {start, finish} -> [start, finish] end)
                      end

                      def merge_intervals(_), do: []
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
                        DemoTestHelper.assert_equal(Solution.merge_intervals([[1, 3], [2, 4], [6, 6]]), [[1, 4], [6, 6]], "demo_1")
                        DemoTestHelper.assert_equal(Solution.merge_intervals([]), [], "demo_2")
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
                          {[[1, 3], [2, 4], [6, 6]], [[1, 4], [6, 6]]},
                          {[], []},
                          {[[5, 2], [8, 10], [10, 12]], [[2, 5], [8, 12]]},
                          {[[1, 1], [3, 5], [2, 2]], [[1, 5]]},
                          {[[0, 0], "bad", [4, 4], [2, 3]], [[0, 0], [2, 4]]}
                        ]

                        Enum.with_index(cases)
                        |> Enum.each(fn {{intervals, expected}, index} ->
                          FullTestHelper.assert_equal(Solution.merge_intervals(intervals), expected, "full_#{index}")
                        end)
                      end
                    end

                    FullTest.run()
                    """
                ),
            },
        },
        "top_k_frequencies": {
            "python": {
                "canonical_solution": dedent(
                    """
                    def top_k_frequencies(values, k):
                        if not isinstance(k, int) or isinstance(k, bool) or k < 1:
                            return {"status": "error", "reason": "invalid_k"}
                        counts = {}
                        if isinstance(values, list):
                            for item in values:
                                if isinstance(item, str):
                                    counts[item] = counts.get(item, 0) + 1
                        ranked = [item for item, _count in sorted(counts.items(), key=lambda pair: (-pair[1], pair[0]))]
                        return {"status": "ok", "items": ranked[:k]}
                    """
                ),
                "demo_test_func": dedent(
                    """
                    def test():
                        assert top_k_frequencies(["a", "b", "a", "c", "b", "a"], 2) == {"status": "ok", "items": ["a", "b"]}
                        assert top_k_frequencies(["a"], 0) == {"status": "error", "reason": "invalid_k"}

                    if __name__ == "__main__":
                        test()
                    """
                ),
                "full_test_func": dedent(
                    """
                    def test():
                        cases = [
                            ((["a", "b", "a", "c", "b", "a"], 2), {"status": "ok", "items": ["a", "b"]}),
                            ((["a"], 0), {"status": "error", "reason": "invalid_k"}),
                            ((["x"], 1), {"status": "ok", "items": ["x"]}),
                            ((["b", "a", "b", "a"], 2), {"status": "ok", "items": ["a", "b"]}),
                            ((["a", "b"], 3), {"status": "ok", "items": ["a", "b"]}),
                        ]
                        for index, ((values, k), expected) in enumerate(cases):
                            actual = top_k_frequencies(values, k)
                            assert actual == expected, f"case {index}: expected {expected!r}, got {actual!r}"

                    if __name__ == "__main__":
                        test()
                    """
                ),
            },
            "typescript": {
                "canonical_solution": dedent(
                    """
                    function topKFrequencies(values: unknown, k: number): { status: string; items?: string[]; reason?: string } {
                      if (!Number.isInteger(k) || k < 1) return { status: "error", reason: "invalid_k" };
                      const counts = new Map<string, number>();
                      if (Array.isArray(values)) {
                        values.forEach((item) => {
                          if (typeof item === "string") counts.set(item, (counts.get(item) ?? 0) + 1);
                        });
                      }
                      const ranked = Array.from(counts.entries())
                        .sort((a, b) => (b[1] - a[1]) || a[0].localeCompare(b[0]))
                        .map(([item]) => item);
                      return { status: "ok", items: ranked.slice(0, k) };
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
                      assertDeepEqual(topKFrequencies(["a", "b", "a", "c", "b", "a"], 2), { status: "ok", items: ["a", "b"] }, "demo_1");
                      assertDeepEqual(topKFrequencies(["a"], 0), { status: "error", reason: "invalid_k" }, "demo_2");
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
                      const cases: Array<[[any, number], any]> = [
                        [[["a", "b", "a", "c", "b", "a"], 2], { status: "ok", items: ["a", "b"] }],
                        [[["a"], 0], { status: "error", reason: "invalid_k" }],
                        [[["x"], 1], { status: "ok", items: ["x"] }],
                        [[["b", "a", "b", "a"], 2], { status: "ok", items: ["a", "b"] }],
                        [[["a", "b"], 3], { status: "ok", items: ["a", "b"] }],
                      ];
                      cases.forEach((entry, index) => {
                        const [[values, k], expected] = entry;
                        assertDeepEqual(topKFrequencies(values, k), expected, `full_${index}`);
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
                      def top_k_frequencies(values, k) when is_list(values) and is_integer(k) and k >= 1 do
                        ranked =
                          values
                          |> Enum.reduce(%{}, fn
                            item, acc when is_binary(item) -> Map.update(acc, item, 1, &(&1 + 1))
                            _, acc -> acc
                          end)
                          |> Enum.sort_by(fn {item, count} -> {-count, item} end)
                          |> Enum.map(fn {item, _count} -> item end)

                        %{"status" => "ok", "items" => Enum.take(ranked, k)}
                      end

                      def top_k_frequencies(_values, _k), do: %{"status" => "error", "reason" => "invalid_k"}
                    end
                    """
                ),
                "demo_test_func": dedent(
                    """
                    defmodule DemoTestHelper do
                      def get_key(map, key) when is_map(map), do: Map.get(map, key) || Map.get(map, String.to_atom(key))
                      def normalize_result(value) do
                        result = %{"status" => get_key(value, "status")}
                        result = if get_key(value, "items"), do: Map.put(result, "items", get_key(value, "items")), else: result
                        if get_key(value, "reason"), do: Map.put(result, "reason", get_key(value, "reason")), else: result
                      end
                      def assert_equal(actual, expected, label), do: if(actual != expected, do: raise("#{label}: expected #{inspect(expected)}, got #{inspect(actual)}"))
                    end

                    defmodule DemoTest do
                      def run do
                        DemoTestHelper.assert_equal(
                          Solution.top_k_frequencies(["a", "b", "a", "c", "b", "a"], 2) |> DemoTestHelper.normalize_result(),
                          %{"status" => "ok", "items" => ["a", "b"]},
                          "demo_1"
                        )
                        DemoTestHelper.assert_equal(
                          Solution.top_k_frequencies(["a"], 0) |> DemoTestHelper.normalize_result(),
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
                        result = if get_key(value, "items"), do: Map.put(result, "items", get_key(value, "items")), else: result
                        if get_key(value, "reason"), do: Map.put(result, "reason", get_key(value, "reason")), else: result
                      end
                      def assert_equal(actual, expected, label), do: if(actual != expected, do: raise("#{label}: expected #{inspect(expected)}, got #{inspect(actual)}"))
                    end

                    defmodule FullTest do
                      def run do
                        cases = [
                          {["a", "b", "a", "c", "b", "a"], 2, %{"status" => "ok", "items" => ["a", "b"]}},
                          {["a"], 0, %{"status" => "error", "reason" => "invalid_k"}},
                          {["x"], 1, %{"status" => "ok", "items" => ["x"]}},
                          {["b", "a", "b", "a"], 2, %{"status" => "ok", "items" => ["a", "b"]}},
                          {["a", "b"], 3, %{"status" => "ok", "items" => ["a", "b"]}}
                        ]

                        Enum.with_index(cases)
                        |> Enum.each(fn {{values, k, expected}, index} ->
                          actual = Solution.top_k_frequencies(values, k) |> FullTestHelper.normalize_result()
                          FullTestHelper.assert_equal(actual, expected, "full_#{index}")
                        end)
                      end
                    end

                    FullTest.run()
                    """
                ),
            },
        },
        "queue_wait_times": {
            "python": {
                "canonical_solution": dedent(
                    """
                    def compute_waits(jobs):
                        if not isinstance(jobs, list):
                            return []
                        current_time = 0
                        outputs = []
                        for job in jobs:
                            if not isinstance(job, dict):
                                continue
                            job_id = job.get("id")
                            arrive = job.get("arrive")
                            duration = job.get("duration")
                            if (
                                isinstance(job_id, str)
                                and isinstance(arrive, int)
                                and not isinstance(arrive, bool)
                                and isinstance(duration, int)
                                and not isinstance(duration, bool)
                                and duration >= 0
                            ):
                                start = max(current_time, arrive)
                                outputs.append({"id": job_id, "wait": start - arrive})
                                current_time = start + duration
                        return outputs
                    """
                ),
                "demo_test_func": dedent(
                    """
                    def test():
                        assert compute_waits([
                            {"id": "a", "arrive": 0, "duration": 3},
                            {"id": "b", "arrive": 1, "duration": 2},
                            {"id": "c", "arrive": 5, "duration": 1},
                        ]) == [
                            {"id": "a", "wait": 0},
                            {"id": "b", "wait": 2},
                            {"id": "c", "wait": 0},
                        ]
                        assert compute_waits([]) == []

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
                                    {"id": "a", "arrive": 0, "duration": 3},
                                    {"id": "b", "arrive": 1, "duration": 2},
                                    {"id": "c", "arrive": 5, "duration": 1},
                                ],
                                [
                                    {"id": "a", "wait": 0},
                                    {"id": "b", "wait": 2},
                                    {"id": "c", "wait": 0},
                                ],
                            ),
                            (
                                [
                                    {"id": "a", "arrive": 0, "duration": 2},
                                    {"id": "b", "arrive": 0, "duration": 1},
                                    {"id": "c", "arrive": 1, "duration": 1},
                                ],
                                [
                                    {"id": "a", "wait": 0},
                                    {"id": "b", "wait": 2},
                                    {"id": "c", "wait": 2},
                                ],
                            ),
                            ([], []),
                            (
                                [
                                    {"id": "idle", "arrive": 4, "duration": 0},
                                    {"id": "next", "arrive": 6, "duration": 1},
                                ],
                                [
                                    {"id": "idle", "wait": 0},
                                    {"id": "next", "wait": 0},
                                ],
                            ),
                            (
                                [{"id": "ok", "arrive": 1, "duration": 1}, {"bad": True}, {"id": "later", "arrive": 5, "duration": 1}],
                                [
                                    {"id": "ok", "wait": 0},
                                    {"id": "later", "wait": 0},
                                ],
                            ),
                        ]
                        for index, (jobs, expected) in enumerate(cases):
                            actual = compute_waits(jobs)
                            assert actual == expected, f"case {index}: expected {expected!r}, got {actual!r}"

                    if __name__ == "__main__":
                        test()
                    """
                ),
            },
            "typescript": {
                "canonical_solution": dedent(
                    """
                    function computeWaits(jobs: unknown): Array<{ id: string; wait: number }> {
                      if (!Array.isArray(jobs)) return [];
                      let currentTime = 0;
                      const outputs: Array<{ id: string; wait: number }> = [];
                      for (const job of jobs) {
                        if (
                          job !== null &&
                          typeof job === "object" &&
                          typeof (job as any).id === "string" &&
                          Number.isInteger((job as any).arrive) &&
                          Number.isInteger((job as any).duration) &&
                          (job as any).duration >= 0
                        ) {
                          const arrive = (job as any).arrive as number;
                          const duration = (job as any).duration as number;
                          const start = Math.max(currentTime, arrive);
                          outputs.push({ id: (job as any).id as string, wait: start - arrive });
                          currentTime = start + duration;
                        }
                      }
                      return outputs;
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
                      assertDeepEqual(computeWaits([
                        { id: "a", arrive: 0, duration: 3 },
                        { id: "b", arrive: 1, duration: 2 },
                        { id: "c", arrive: 5, duration: 1 },
                      ]), [
                        { id: "a", wait: 0 },
                        { id: "b", wait: 2 },
                        { id: "c", wait: 0 },
                      ], "demo_1");
                      assertDeepEqual(computeWaits([]), [], "demo_2");
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
                      const cases: Array<[any, any]> = [
                        [[
                          { id: "a", arrive: 0, duration: 3 },
                          { id: "b", arrive: 1, duration: 2 },
                          { id: "c", arrive: 5, duration: 1 },
                        ], [
                          { id: "a", wait: 0 },
                          { id: "b", wait: 2 },
                          { id: "c", wait: 0 },
                        ]],
                        [[
                          { id: "a", arrive: 0, duration: 2 },
                          { id: "b", arrive: 0, duration: 1 },
                          { id: "c", arrive: 1, duration: 1 },
                        ], [
                          { id: "a", wait: 0 },
                          { id: "b", wait: 2 },
                          { id: "c", wait: 2 },
                        ]],
                        [[], []],
                        [[
                          { id: "idle", arrive: 4, duration: 0 },
                          { id: "next", arrive: 6, duration: 1 },
                        ], [
                          { id: "idle", wait: 0 },
                          { id: "next", wait: 0 },
                        ]],
                        [[
                          { id: "ok", arrive: 1, duration: 1 },
                          { bad: true },
                          { id: "later", arrive: 5, duration: 1 },
                        ], [
                          { id: "ok", wait: 0 },
                          { id: "later", wait: 0 },
                        ]],
                      ];
                      cases.forEach(([jobs, expected], index) => {
                        assertDeepEqual(computeWaits(jobs), expected, `full_${index}`);
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
                      def compute_waits(jobs) when is_list(jobs) do
                        {outputs, _current_time} =
                          Enum.reduce(jobs, {[], 0}, fn job, {outputs, current_time} ->
                            case normalize_job(job) do
                              {:ok, job_id, arrive, duration} ->
                                start = max(current_time, arrive)
                                output = %{"id" => job_id, "wait" => start - arrive}
                                {outputs ++ [output], start + duration}

                              :error ->
                                {outputs, current_time}
                            end
                          end)

                        outputs
                      end

                      def compute_waits(_), do: []

                      defp normalize_job(%{"id" => job_id, "arrive" => arrive, "duration" => duration}),
                        do: normalize_job(%{id: job_id, arrive: arrive, duration: duration})

                      defp normalize_job(%{id: job_id, arrive: arrive, duration: duration})
                           when is_binary(job_id) and is_integer(arrive) and is_integer(duration) and duration >= 0,
                           do: {:ok, job_id, arrive, duration}

                      defp normalize_job(_), do: :error
                    end
                    """
                ),
                "demo_test_func": dedent(
                    """
                    defmodule DemoTestHelper do
                      def get_key(map, key) when is_map(map), do: Map.get(map, key) || Map.get(map, String.to_atom(key))
                      def normalize_rows(rows), do: Enum.map(rows, fn row -> %{"id" => get_key(row, "id"), "wait" => get_key(row, "wait")} end)
                      def assert_equal(actual, expected, label), do: if(actual != expected, do: raise("#{label}: expected #{inspect(expected)}, got #{inspect(actual)}"))
                    end

                    defmodule DemoTest do
                      def run do
                        DemoTestHelper.assert_equal(
                          Solution.compute_waits([
                            %{"id" => "a", "arrive" => 0, "duration" => 3},
                            %{"id" => "b", "arrive" => 1, "duration" => 2},
                            %{"id" => "c", "arrive" => 5, "duration" => 1}
                          ]) |> DemoTestHelper.normalize_rows(),
                          [
                            %{"id" => "a", "wait" => 0},
                            %{"id" => "b", "wait" => 2},
                            %{"id" => "c", "wait" => 0}
                          ],
                          "demo_1"
                        )
                        DemoTestHelper.assert_equal(Solution.compute_waits([]) |> DemoTestHelper.normalize_rows(), [], "demo_2")
                      end
                    end

                    DemoTest.run()
                    """
                ),
                "full_test_func": dedent(
                    """
                    defmodule FullTestHelper do
                      def get_key(map, key) when is_map(map), do: Map.get(map, key) || Map.get(map, String.to_atom(key))
                      def normalize_rows(rows), do: Enum.map(rows, fn row -> %{"id" => get_key(row, "id"), "wait" => get_key(row, "wait")} end)
                      def assert_equal(actual, expected, label), do: if(actual != expected, do: raise("#{label}: expected #{inspect(expected)}, got #{inspect(actual)}"))
                    end

                    defmodule FullTest do
                      def run do
                        cases = [
                          {
                            [
                              %{"id" => "a", "arrive" => 0, "duration" => 3},
                              %{"id" => "b", "arrive" => 1, "duration" => 2},
                              %{"id" => "c", "arrive" => 5, "duration" => 1}
                            ],
                            [
                              %{"id" => "a", "wait" => 0},
                              %{"id" => "b", "wait" => 2},
                              %{"id" => "c", "wait" => 0}
                            ]
                          },
                          {
                            [
                              %{"id" => "a", "arrive" => 0, "duration" => 2},
                              %{"id" => "b", "arrive" => 0, "duration" => 1},
                              %{"id" => "c", "arrive" => 1, "duration" => 1}
                            ],
                            [
                              %{"id" => "a", "wait" => 0},
                              %{"id" => "b", "wait" => 2},
                              %{"id" => "c", "wait" => 2}
                            ]
                          },
                          {[], []},
                          {
                            [
                              %{"id" => "idle", "arrive" => 4, "duration" => 0},
                              %{"id" => "next", "arrive" => 6, "duration" => 1}
                            ],
                            [
                              %{"id" => "idle", "wait" => 0},
                              %{"id" => "next", "wait" => 0}
                            ]
                          },
                          {
                            [%{"id" => "ok", "arrive" => 1, "duration" => 1}, %{"bad" => true}, %{"id" => "later", "arrive" => 5, "duration" => 1}],
                            [
                              %{"id" => "ok", "wait" => 0},
                              %{"id" => "later", "wait" => 0}
                            ]
                          }
                        ]

                        Enum.with_index(cases)
                        |> Enum.each(fn {{jobs, expected}, index} ->
                          actual = Solution.compute_waits(jobs) |> FullTestHelper.normalize_rows()
                          FullTestHelper.assert_equal(actual, expected, "full_#{index}")
                        end)
                      end
                    end

                    FullTest.run()
                    """
                ),
            },
        },
        "normalize_phone_book": {
            "python": {
                "canonical_solution": dedent(
                    """
                    def normalize_phone_book(entries):
                        if not isinstance(entries, list):
                            return []
                        grouped = {}
                        for entry in entries:
                            if not isinstance(entry, dict):
                                continue
                            name = entry.get("name")
                            phone = entry.get("phone")
                            if not isinstance(name, str) or name == "" or not isinstance(phone, str):
                                continue
                            digits = "".join(ch for ch in phone if ch.isdigit())
                            if len(digits) != 10:
                                continue
                            grouped.setdefault(digits, set()).add(name)
                        return [
                            {"phone": phone, "names": sorted(names)}
                            for phone, names in sorted(grouped.items())
                        ]
                    """
                ),
                "demo_test_func": dedent(
                    """
                    def test():
                        assert normalize_phone_book([
                            {"name": "Ana", "phone": "(555) 111-2222"},
                            {"name": "Bob", "phone": "5551112222"},
                            {"name": "Cara", "phone": "5553334444"},
                        ]) == [
                            {"phone": "5551112222", "names": ["Ana", "Bob"]},
                            {"phone": "5553334444", "names": ["Cara"]},
                        ]
                        assert normalize_phone_book([]) == []

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
                                    {"name": "Ana", "phone": "(555) 111-2222"},
                                    {"name": "Bob", "phone": "5551112222"},
                                    {"name": "Cara", "phone": "5553334444"},
                                ],
                                [
                                    {"phone": "5551112222", "names": ["Ana", "Bob"]},
                                    {"phone": "5553334444", "names": ["Cara"]},
                                ],
                            ),
                            (
                                [
                                    {"name": "Ana", "phone": "5551112222"},
                                    {"name": "Ana", "phone": "555-111-2222"},
                                    {"name": "Bob", "phone": "5551112222"},
                                ],
                                [
                                    {"phone": "5551112222", "names": ["Ana", "Bob"]},
                                ],
                            ),
                            (
                                [
                                    {"name": "Bad", "phone": "123"},
                                    {"name": "", "phone": "5553334444"},
                                    {"name": "Ok", "phone": "555-333-4444"},
                                ],
                                [
                                    {"phone": "5553334444", "names": ["Ok"]},
                                ],
                            ),
                            ([], []),
                            ("bad", []),
                        ]
                        for index, (entries, expected) in enumerate(cases):
                            actual = normalize_phone_book(entries)
                            assert actual == expected, f"case {index}: expected {expected!r}, got {actual!r}"

                    if __name__ == "__main__":
                        test()
                    """
                ),
            },
            "typescript": {
                "canonical_solution": dedent(
                    """
                    function normalizePhoneBook(entries: unknown): Array<{ phone: string; names: string[] }> {
                      if (!Array.isArray(entries)) return [];
                      const grouped = new Map<string, Set<string>>();
                      for (const entry of entries) {
                        if (
                          entry !== null &&
                          typeof entry === "object" &&
                          typeof (entry as any).name === "string" &&
                          (entry as any).name.length > 0 &&
                          typeof (entry as any).phone === "string"
                        ) {
                          const digits = ((entry as any).phone as string).replace(/\\D/g, "");
                          if (digits.length !== 10) continue;
                          if (!grouped.has(digits)) grouped.set(digits, new Set<string>());
                          grouped.get(digits)!.add((entry as any).name as string);
                        }
                      }
                      return Array.from(grouped.entries())
                        .sort((a, b) => a[0].localeCompare(b[0]))
                        .map(([phone, names]) => ({ phone, names: Array.from(names).sort((a, b) => a.localeCompare(b)) }));
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
                      assertDeepEqual(normalizePhoneBook([
                        { name: "Ana", phone: "(555) 111-2222" },
                        { name: "Bob", phone: "5551112222" },
                        { name: "Cara", phone: "5553334444" },
                      ]), [
                        { phone: "5551112222", names: ["Ana", "Bob"] },
                        { phone: "5553334444", names: ["Cara"] },
                      ], "demo_1");
                      assertDeepEqual(normalizePhoneBook([]), [], "demo_2");
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
                      const cases: Array<[any, any]> = [
                        [[
                          { name: "Ana", phone: "(555) 111-2222" },
                          { name: "Bob", phone: "5551112222" },
                          { name: "Cara", phone: "5553334444" },
                        ], [
                          { phone: "5551112222", names: ["Ana", "Bob"] },
                          { phone: "5553334444", names: ["Cara"] },
                        ]],
                        [[
                          { name: "Ana", phone: "5551112222" },
                          { name: "Ana", phone: "555-111-2222" },
                          { name: "Bob", phone: "5551112222" },
                        ], [
                          { phone: "5551112222", names: ["Ana", "Bob"] },
                        ]],
                        [[
                          { name: "Bad", phone: "123" },
                          { name: "", phone: "5553334444" },
                          { name: "Ok", phone: "555-333-4444" },
                        ], [
                          { phone: "5553334444", names: ["Ok"] },
                        ]],
                        [[], []],
                        ["bad", []],
                      ];
                      cases.forEach(([entries, expected], index) => {
                        assertDeepEqual(normalizePhoneBook(entries), expected, `full_${index}`);
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
                      def normalize_phone_book(entries) when is_list(entries) do
                        entries
                        |> Enum.reduce(%{}, fn entry, acc ->
                          case normalize_entry(entry) do
                            {:ok, name, phone} ->
                              Map.update(acc, phone, MapSet.new([name]), &MapSet.put(&1, name))

                            :error ->
                              acc
                          end
                        end)
                        |> Enum.sort_by(fn {phone, _names} -> phone end)
                        |> Enum.map(fn {phone, names} ->
                          %{"phone" => phone, "names" => names |> MapSet.to_list() |> Enum.sort()}
                        end)
                      end

                      def normalize_phone_book(_), do: []

                      defp normalize_entry(%{"name" => name, "phone" => phone}), do: normalize_entry(%{name: name, phone: phone})

                      defp normalize_entry(%{name: name, phone: phone}) when is_binary(name) and name != "" and is_binary(phone) do
                        digits = String.replace(phone, ~r/\\D/, "")

                        if String.length(digits) == 10 do
                          {:ok, name, digits}
                        else
                          :error
                        end
                      end

                      defp normalize_entry(_), do: :error
                    end
                    """
                ),
                "demo_test_func": dedent(
                    """
                    defmodule DemoTestHelper do
                      def get_key(map, key) when is_map(map), do: Map.get(map, key) || Map.get(map, String.to_atom(key))
                      def normalize_rows(rows), do: Enum.map(rows, fn row -> %{"phone" => get_key(row, "phone"), "names" => get_key(row, "names")} end)
                      def assert_equal(actual, expected, label), do: if(actual != expected, do: raise("#{label}: expected #{inspect(expected)}, got #{inspect(actual)}"))
                    end

                    defmodule DemoTest do
                      def run do
                        DemoTestHelper.assert_equal(
                          Solution.normalize_phone_book([
                            %{"name" => "Ana", "phone" => "(555) 111-2222"},
                            %{"name" => "Bob", "phone" => "5551112222"},
                            %{"name" => "Cara", "phone" => "5553334444"}
                          ]) |> DemoTestHelper.normalize_rows(),
                          [
                            %{"phone" => "5551112222", "names" => ["Ana", "Bob"]},
                            %{"phone" => "5553334444", "names" => ["Cara"]}
                          ],
                          "demo_1"
                        )
                        DemoTestHelper.assert_equal(Solution.normalize_phone_book([]) |> DemoTestHelper.normalize_rows(), [], "demo_2")
                      end
                    end

                    DemoTest.run()
                    """
                ),
                "full_test_func": dedent(
                    """
                    defmodule FullTestHelper do
                      def get_key(map, key) when is_map(map), do: Map.get(map, key) || Map.get(map, String.to_atom(key))
                      def normalize_rows(rows), do: Enum.map(rows, fn row -> %{"phone" => get_key(row, "phone"), "names" => get_key(row, "names")} end)
                      def assert_equal(actual, expected, label), do: if(actual != expected, do: raise("#{label}: expected #{inspect(expected)}, got #{inspect(actual)}"))
                    end

                    defmodule FullTest do
                      def run do
                        cases = [
                          {
                            [
                              %{"name" => "Ana", "phone" => "(555) 111-2222"},
                              %{"name" => "Bob", "phone" => "5551112222"},
                              %{"name" => "Cara", "phone" => "5553334444"}
                            ],
                            [
                              %{"phone" => "5551112222", "names" => ["Ana", "Bob"]},
                              %{"phone" => "5553334444", "names" => ["Cara"]}
                            ]
                          },
                          {
                            [
                              %{"name" => "Ana", "phone" => "5551112222"},
                              %{"name" => "Ana", "phone" => "555-111-2222"},
                              %{"name" => "Bob", "phone" => "5551112222"}
                            ],
                            [
                              %{"phone" => "5551112222", "names" => ["Ana", "Bob"]}
                            ]
                          },
                          {
                            [
                              %{"name" => "Bad", "phone" => "123"},
                              %{"name" => "", "phone" => "5553334444"},
                              %{"name" => "Ok", "phone" => "555-333-4444"}
                            ],
                            [
                              %{"phone" => "5553334444", "names" => ["Ok"]}
                            ]
                          },
                          {[], []},
                          {"bad", []}
                        ]

                        Enum.with_index(cases)
                        |> Enum.each(fn {{entries, expected}, index} ->
                          actual = Solution.normalize_phone_book(entries) |> FullTestHelper.normalize_rows()
                          FullTestHelper.assert_equal(actual, expected, "full_#{index}")
                        end)
                      end
                    end

                    FullTest.run()
                    """
                ),
            },
        },
        "stable_group_runs": {
            "python": {
                "canonical_solution": dedent(
                    """
                    def group_runs(values):
                        outputs = []
                        current_value = None
                        current_count = 0
                        if not isinstance(values, list):
                            return outputs
                        for value in values:
                            if not isinstance(value, str):
                                if current_count:
                                    outputs.append({"value": current_value, "count": current_count})
                                    current_value = None
                                    current_count = 0
                                continue
                            if current_count == 0 or value != current_value:
                                if current_count:
                                    outputs.append({"value": current_value, "count": current_count})
                                current_value = value
                                current_count = 1
                            else:
                                current_count += 1
                        if current_count:
                            outputs.append({"value": current_value, "count": current_count})
                        return outputs
                    """
                ),
                "demo_test_func": dedent(
                    """
                    def test():
                        assert group_runs(["a", "a", "b", "b", "b", "a"]) == [
                            {"value": "a", "count": 2},
                            {"value": "b", "count": 3},
                            {"value": "a", "count": 1},
                        ]
                        assert group_runs([]) == []

                    if __name__ == "__main__":
                        test()
                    """
                ),
                "full_test_func": dedent(
                    """
                    def test():
                        cases = [
                            (
                                ["a", "a", "b", "b", "b", "a"],
                                [
                                    {"value": "a", "count": 2},
                                    {"value": "b", "count": 3},
                                    {"value": "a", "count": 1},
                                ],
                            ),
                            ([], []),
                            (["x"], [{"value": "x", "count": 1}]),
                            (
                                ["a", 1, "a", "a"],
                                [
                                    {"value": "a", "count": 1},
                                    {"value": "a", "count": 2},
                                ],
                            ),
                            (
                                ["q", "q", "q"],
                                [{"value": "q", "count": 3}],
                            ),
                        ]
                        for index, (values, expected) in enumerate(cases):
                            actual = group_runs(values)
                            assert actual == expected, f"case {index}: expected {expected!r}, got {actual!r}"

                    if __name__ == "__main__":
                        test()
                    """
                ),
            },
            "typescript": {
                "canonical_solution": dedent(
                    """
                    function groupRuns(values: unknown): Array<{ value: string; count: number }> {
                      if (!Array.isArray(values)) return [];
                      const outputs: Array<{ value: string; count: number }> = [];
                      let currentValue: string | null = null;
                      let currentCount = 0;
                      for (const value of values) {
                        if (typeof value !== "string") {
                          if (currentCount > 0 && currentValue !== null) {
                            outputs.push({ value: currentValue, count: currentCount });
                            currentValue = null;
                            currentCount = 0;
                          }
                          continue;
                        }
                        if (currentCount === 0 || value !== currentValue) {
                          if (currentCount > 0 && currentValue !== null) {
                            outputs.push({ value: currentValue, count: currentCount });
                          }
                          currentValue = value;
                          currentCount = 1;
                        } else {
                          currentCount += 1;
                        }
                      }
                      if (currentCount > 0 && currentValue !== null) outputs.push({ value: currentValue, count: currentCount });
                      return outputs;
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
                      assertDeepEqual(groupRuns(["a", "a", "b", "b", "b", "a"]), [
                        { value: "a", count: 2 },
                        { value: "b", count: 3 },
                        { value: "a", count: 1 },
                      ], "demo_1");
                      assertDeepEqual(groupRuns([]), [], "demo_2");
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
                      const cases: Array<[any, any]> = [
                        [["a", "a", "b", "b", "b", "a"], [
                          { value: "a", count: 2 },
                          { value: "b", count: 3 },
                          { value: "a", count: 1 },
                        ]],
                        [[], []],
                        [["x"], [{ value: "x", count: 1 }]],
                        [["a", 1, "a", "a"], [
                          { value: "a", count: 1 },
                          { value: "a", count: 2 },
                        ]],
                        [["q", "q", "q"], [{ value: "q", count: 3 }]],
                      ];
                      cases.forEach(([values, expected], index) => {
                        assertDeepEqual(groupRuns(values), expected, `full_${index}`);
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
                      def group_runs(values) when is_list(values) do
                        {outputs, current_value, current_count} =
                          Enum.reduce(values, {[], nil, 0}, fn value, {outputs, current_value, current_count} ->
                            cond do
                              not is_binary(value) ->
                                flush_run(outputs, current_value, current_count)

                              current_count == 0 ->
                                {outputs, value, 1}

                              value == current_value ->
                                {outputs, current_value, current_count + 1}

                              true ->
                                {outputs ++ [%{"value" => current_value, "count" => current_count}], value, 1}
                            end
                          end)

                        outputs
                        |> then(fn rows ->
                          if current_count > 0 do
                            rows ++ [%{"value" => current_value, "count" => current_count}]
                          else
                            rows
                          end
                        end)
                      end

                      def group_runs(_), do: []

                      defp flush_run(outputs, current_value, current_count) do
                        if current_count > 0 do
                          {outputs ++ [%{"value" => current_value, "count" => current_count}], nil, 0}
                        else
                          {outputs, nil, 0}
                        end
                      end
                    end
                    """
                ),
                "demo_test_func": dedent(
                    """
                    defmodule DemoTestHelper do
                      def get_key(map, key) when is_map(map), do: Map.get(map, key) || Map.get(map, String.to_atom(key))
                      def normalize_rows(rows), do: Enum.map(rows, fn row -> %{"value" => get_key(row, "value"), "count" => get_key(row, "count")} end)
                      def assert_equal(actual, expected, label), do: if(actual != expected, do: raise("#{label}: expected #{inspect(expected)}, got #{inspect(actual)}"))
                    end

                    defmodule DemoTest do
                      def run do
                        DemoTestHelper.assert_equal(
                          Solution.group_runs(["a", "a", "b", "b", "b", "a"]) |> DemoTestHelper.normalize_rows(),
                          [
                            %{"value" => "a", "count" => 2},
                            %{"value" => "b", "count" => 3},
                            %{"value" => "a", "count" => 1}
                          ],
                          "demo_1"
                        )
                        DemoTestHelper.assert_equal(Solution.group_runs([]) |> DemoTestHelper.normalize_rows(), [], "demo_2")
                      end
                    end

                    DemoTest.run()
                    """
                ),
                "full_test_func": dedent(
                    """
                    defmodule FullTestHelper do
                      def get_key(map, key) when is_map(map), do: Map.get(map, key) || Map.get(map, String.to_atom(key))
                      def normalize_rows(rows), do: Enum.map(rows, fn row -> %{"value" => get_key(row, "value"), "count" => get_key(row, "count")} end)
                      def assert_equal(actual, expected, label), do: if(actual != expected, do: raise("#{label}: expected #{inspect(expected)}, got #{inspect(actual)}"))
                    end

                    defmodule FullTest do
                      def run do
                        cases = [
                          {
                            ["a", "a", "b", "b", "b", "a"],
                            [
                              %{"value" => "a", "count" => 2},
                              %{"value" => "b", "count" => 3},
                              %{"value" => "a", "count" => 1}
                            ]
                          },
                          {[], []},
                          {["x"], [%{"value" => "x", "count" => 1}]},
                          {
                            ["a", 1, "a", "a"],
                            [
                              %{"value" => "a", "count" => 1},
                              %{"value" => "a", "count" => 2}
                            ]
                          },
                          {["q", "q", "q"], [%{"value" => "q", "count" => 3}]}
                        ]

                        Enum.with_index(cases)
                        |> Enum.each(fn {{values, expected}, index} ->
                          actual = Solution.group_runs(values) |> FullTestHelper.normalize_rows()
                          FullTestHelper.assert_equal(actual, expected, "full_#{index}")
                        end)
                      end
                    end

                    FullTest.run()
                    """
                ),
            },
        },
        "token_bucket_decisions": {
            "python": {
                "canonical_solution": dedent(
                    """
                    def apply_token_bucket(capacity, refill, requests):
                        if (
                            not isinstance(capacity, int)
                            or isinstance(capacity, bool)
                            or capacity < 1
                            or not isinstance(refill, int)
                            or isinstance(refill, bool)
                            or refill < 0
                        ):
                            return {"status": "error", "reason": "invalid_config"}
                        if not isinstance(requests, list) or any(
                            not isinstance(value, int) or isinstance(value, bool) or value < 0
                            for value in requests
                        ):
                            return {"status": "error", "reason": "invalid_requests"}
                        tokens = capacity
                        allowed = []
                        for index, request in enumerate(requests):
                            current = min(tokens, request)
                            allowed.append(current)
                            tokens -= current
                            if index != len(requests) - 1:
                                tokens = min(capacity, tokens + refill)
                        return {"status": "ok", "allowed": allowed, "remaining": tokens}
                    """
                ),
                "demo_test_func": dedent(
                    """
                    def test():
                        assert apply_token_bucket(3, 2, [2, 2, 2]) == {"status": "ok", "allowed": [2, 2, 2], "remaining": 1}
                        assert apply_token_bucket(0, 1, [1]) == {"status": "error", "reason": "invalid_config"}

                    if __name__ == "__main__":
                        test()
                    """
                ),
                "full_test_func": dedent(
                    """
                    def test():
                        cases = [
                            ((3, 2, [2, 2, 2]), {"status": "ok", "allowed": [2, 2, 2], "remaining": 1}),
                            ((0, 1, [1]), {"status": "error", "reason": "invalid_config"}),
                            ((1, 0, [2, 1]), {"status": "ok", "allowed": [1, 0], "remaining": 0}),
                            ((4, 1, []), {"status": "ok", "allowed": [], "remaining": 4}),
                            ((2, 1, [1, -1]), {"status": "error", "reason": "invalid_requests"}),
                        ]
                        for index, (args, expected) in enumerate(cases):
                            actual = apply_token_bucket(*args)
                            assert actual == expected, f"case {index}: expected {expected!r}, got {actual!r}"

                    if __name__ == "__main__":
                        test()
                    """
                ),
            },
            "typescript": {
                "canonical_solution": dedent(
                    """
                    function applyTokenBucket(capacity: number, refill: number, requests: unknown): { status: string; allowed?: number[]; remaining?: number; reason?: string } {
                      if (!Number.isInteger(capacity) || capacity < 1 || !Number.isInteger(refill) || refill < 0) {
                        return { status: "error", reason: "invalid_config" };
                      }
                      if (!Array.isArray(requests) || requests.some((value) => !Number.isInteger(value) || value < 0)) {
                        return { status: "error", reason: "invalid_requests" };
                      }
                      let tokens = capacity;
                      const allowed: number[] = [];
                      requests.forEach((request, index) => {
                        const current = Math.min(tokens, request as number);
                        allowed.push(current);
                        tokens -= current;
                        if (index !== requests.length - 1) tokens = Math.min(capacity, tokens + refill);
                      });
                      return { status: "ok", allowed, remaining: tokens };
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
                      assertDeepEqual(applyTokenBucket(3, 2, [2, 2, 2]), { status: "ok", allowed: [2, 2, 2], remaining: 1 }, "demo_1");
                      assertDeepEqual(applyTokenBucket(0, 1, [1]), { status: "error", reason: "invalid_config" }, "demo_2");
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
                        [[3, 2, [2, 2, 2]], { status: "ok", allowed: [2, 2, 2], remaining: 1 }],
                        [[0, 1, [1]], { status: "error", reason: "invalid_config" }],
                        [[1, 0, [2, 1]], { status: "ok", allowed: [1, 0], remaining: 0 }],
                        [[4, 1, []], { status: "ok", allowed: [], remaining: 4 }],
                        [[2, 1, [1, -1]], { status: "error", reason: "invalid_requests" }],
                      ];
                      cases.forEach(([args, expected], index) => {
                        assertDeepEqual(applyTokenBucket(args[0], args[1], args[2]), expected, `full_${index}`);
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
                      def apply_token_bucket(capacity, refill, requests)
                          when is_integer(capacity) and capacity >= 1 and is_integer(refill) and refill >= 0 and is_list(requests) do
                        if Enum.any?(requests, fn value -> not (is_integer(value) and value >= 0) end) do
                          %{"status" => "error", "reason" => "invalid_requests"}
                        else
                          {allowed, remaining} =
                            Enum.with_index(requests)
                            |> Enum.reduce({[], capacity}, fn {request, index}, {allowed, tokens} ->
                              current = min(tokens, request)
                              next_tokens = tokens - current
                              next_tokens =
                                if index == length(requests) - 1 do
                                  next_tokens
                                else
                                  min(capacity, next_tokens + refill)
                                end

                              {allowed ++ [current], next_tokens}
                            end)

                          %{"status" => "ok", "allowed" => allowed, "remaining" => remaining}
                        end
                      end

                      def apply_token_bucket(_capacity, _refill, _requests), do: %{"status" => "error", "reason" => "invalid_config"}
                    end
                    """
                ),
                "demo_test_func": dedent(
                    """
                    defmodule DemoTestHelper do
                      def get_key(map, key) when is_map(map), do: Map.get(map, key) || Map.get(map, String.to_atom(key))
                      def normalize_result(value) do
                        result = %{"status" => get_key(value, "status")}
                        result = if get_key(value, "allowed"), do: Map.put(result, "allowed", get_key(value, "allowed")), else: result
                        result = if is_nil(get_key(value, "remaining")), do: result, else: Map.put(result, "remaining", get_key(value, "remaining"))
                        if get_key(value, "reason"), do: Map.put(result, "reason", get_key(value, "reason")), else: result
                      end
                      def assert_equal(actual, expected, label), do: if(actual != expected, do: raise("#{label}: expected #{inspect(expected)}, got #{inspect(actual)}"))
                    end

                    defmodule DemoTest do
                      def run do
                        DemoTestHelper.assert_equal(
                          Solution.apply_token_bucket(3, 2, [2, 2, 2]) |> DemoTestHelper.normalize_result(),
                          %{"status" => "ok", "allowed" => [2, 2, 2], "remaining" => 1},
                          "demo_1"
                        )
                        DemoTestHelper.assert_equal(
                          Solution.apply_token_bucket(0, 1, [1]) |> DemoTestHelper.normalize_result(),
                          %{"status" => "error", "reason" => "invalid_config"},
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
                        result = if get_key(value, "allowed"), do: Map.put(result, "allowed", get_key(value, "allowed")), else: result
                        result = if is_nil(get_key(value, "remaining")), do: result, else: Map.put(result, "remaining", get_key(value, "remaining"))
                        if get_key(value, "reason"), do: Map.put(result, "reason", get_key(value, "reason")), else: result
                      end
                      def assert_equal(actual, expected, label), do: if(actual != expected, do: raise("#{label}: expected #{inspect(expected)}, got #{inspect(actual)}"))
                    end

                    defmodule FullTest do
                      def run do
                        cases = [
                          {3, 2, [2, 2, 2], %{"status" => "ok", "allowed" => [2, 2, 2], "remaining" => 1}},
                          {0, 1, [1], %{"status" => "error", "reason" => "invalid_config"}},
                          {1, 0, [2, 1], %{"status" => "ok", "allowed" => [1, 0], "remaining" => 0}},
                          {4, 1, [], %{"status" => "ok", "allowed" => [], "remaining" => 4}},
                          {2, 1, [1, -1], %{"status" => "error", "reason" => "invalid_requests"}}
                        ]

                        Enum.with_index(cases)
                        |> Enum.each(fn {{capacity, refill, requests, expected}, index} ->
                          actual = Solution.apply_token_bucket(capacity, refill, requests) |> FullTestHelper.normalize_result()
                          FullTestHelper.assert_equal(actual, expected, "full_#{index}")
                        end)
                      end
                    end

                    FullTest.run()
                    """
                ),
            },
        },
        "dense_rankings": {
            "python": {
                "canonical_solution": dedent(
                    """
                    def dense_ranks(entries):
                        if not isinstance(entries, list):
                            return []
                        ranked = []
                        for entry in entries:
                            if not isinstance(entry, dict):
                                continue
                            name = entry.get("name")
                            score = entry.get("score")
                            if isinstance(name, str) and name != "" and isinstance(score, int) and not isinstance(score, bool):
                                ranked.append((name, score))
                        ranked.sort(key=lambda item: (-item[1], item[0]))
                        outputs = []
                        rank = 0
                        previous_score = None
                        for name, score in ranked:
                            if previous_score != score:
                                rank += 1
                                previous_score = score
                            outputs.append({"name": name, "rank": rank})
                        return outputs
                    """
                ),
                "demo_test_func": dedent(
                    """
                    def test():
                        assert dense_ranks([
                            {"name": "Ana", "score": 9},
                            {"name": "Bo", "score": 9},
                            {"name": "Cid", "score": 7},
                        ]) == [
                            {"name": "Ana", "rank": 1},
                            {"name": "Bo", "rank": 1},
                            {"name": "Cid", "rank": 2},
                        ]
                        assert dense_ranks([]) == []

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
                                    {"name": "Ana", "score": 9},
                                    {"name": "Bo", "score": 9},
                                    {"name": "Cid", "score": 7},
                                ],
                                [
                                    {"name": "Ana", "rank": 1},
                                    {"name": "Bo", "rank": 1},
                                    {"name": "Cid", "rank": 2},
                                ],
                            ),
                            (
                                [
                                    {"name": "Zoe", "score": 5},
                                    {"name": "Ari", "score": 8},
                                    {"name": "Moe", "score": 8},
                                    {"bad": True},
                                ],
                                [
                                    {"name": "Ari", "rank": 1},
                                    {"name": "Moe", "rank": 1},
                                    {"name": "Zoe", "rank": 2},
                                ],
                            ),
                            ([], []),
                            ([{"name": "Solo", "score": 1}], [{"name": "Solo", "rank": 1}]),
                            (
                                [
                                    {"name": "A", "score": 3},
                                    {"name": "B", "score": 2},
                                    {"name": "C", "score": 1},
                                ],
                                [
                                    {"name": "A", "rank": 1},
                                    {"name": "B", "rank": 2},
                                    {"name": "C", "rank": 3},
                                ],
                            ),
                        ]
                        for index, (entries, expected) in enumerate(cases):
                            actual = dense_ranks(entries)
                            assert actual == expected, f"case {index}: expected {expected!r}, got {actual!r}"

                    if __name__ == "__main__":
                        test()
                    """
                ),
            },
            "typescript": {
                "canonical_solution": dedent(
                    """
                    function denseRanks(entries: unknown): Array<{ name: string; rank: number }> {
                      if (!Array.isArray(entries)) return [];
                      const ranked: Array<{ name: string; score: number }> = [];
                      for (const entry of entries) {
                        if (
                          entry !== null &&
                          typeof entry === "object" &&
                          typeof (entry as any).name === "string" &&
                          (entry as any).name.length > 0 &&
                          Number.isInteger((entry as any).score)
                        ) {
                          ranked.push({ name: (entry as any).name as string, score: (entry as any).score as number });
                        }
                      }
                      ranked.sort((a, b) => (b.score - a.score) || a.name.localeCompare(b.name));
                      const outputs: Array<{ name: string; rank: number }> = [];
                      let rank = 0;
                      let previousScore: number | null = null;
                      ranked.forEach((entry) => {
                        if (previousScore !== entry.score) {
                          rank += 1;
                          previousScore = entry.score;
                        }
                        outputs.push({ name: entry.name, rank });
                      });
                      return outputs;
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
                      assertDeepEqual(denseRanks([
                        { name: "Ana", score: 9 },
                        { name: "Bo", score: 9 },
                        { name: "Cid", score: 7 },
                      ]), [
                        { name: "Ana", rank: 1 },
                        { name: "Bo", rank: 1 },
                        { name: "Cid", rank: 2 },
                      ], "demo_1");
                      assertDeepEqual(denseRanks([]), [], "demo_2");
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
                      const cases: Array<[any, any]> = [
                        [[
                          { name: "Ana", score: 9 },
                          { name: "Bo", score: 9 },
                          { name: "Cid", score: 7 },
                        ], [
                          { name: "Ana", rank: 1 },
                          { name: "Bo", rank: 1 },
                          { name: "Cid", rank: 2 },
                        ]],
                        [[
                          { name: "Zoe", score: 5 },
                          { name: "Ari", score: 8 },
                          { name: "Moe", score: 8 },
                          { bad: true },
                        ], [
                          { name: "Ari", rank: 1 },
                          { name: "Moe", rank: 1 },
                          { name: "Zoe", rank: 2 },
                        ]],
                        [[], []],
                        [[{ name: "Solo", score: 1 }], [{ name: "Solo", rank: 1 }]],
                        [[
                          { name: "A", score: 3 },
                          { name: "B", score: 2 },
                          { name: "C", score: 1 },
                        ], [
                          { name: "A", rank: 1 },
                          { name: "B", rank: 2 },
                          { name: "C", rank: 3 },
                        ]],
                      ];
                      cases.forEach(([entries, expected], index) => {
                        assertDeepEqual(denseRanks(entries), expected, `full_${index}`);
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
                      def dense_ranks(entries) when is_list(entries) do
                        entries
                        |> Enum.reduce([], fn entry, acc ->
                          case normalize_entry(entry) do
                            {:ok, name, score} -> [%{name: name, score: score} | acc]
                            :error -> acc
                          end
                        end)
                        |> Enum.sort_by(fn %{name: name, score: score} -> {-score, name} end)
                        |> Enum.reduce({[], nil, 0}, fn %{name: name, score: score}, {outputs, previous_score, rank} ->
                          next_rank =
                            if previous_score == score do
                              rank
                            else
                              rank + 1
                            end

                          {outputs ++ [%{"name" => name, "rank" => next_rank}], score, next_rank}
                        end)
                        |> elem(0)
                      end

                      def dense_ranks(_), do: []

                      defp normalize_entry(%{"name" => name, "score" => score}), do: normalize_entry(%{name: name, score: score})
                      defp normalize_entry(%{name: name, score: score}) when is_binary(name) and name != "" and is_integer(score), do: {:ok, name, score}
                      defp normalize_entry(_), do: :error
                    end
                    """
                ),
                "demo_test_func": dedent(
                    """
                    defmodule DemoTestHelper do
                      def get_key(map, key) when is_map(map), do: Map.get(map, key) || Map.get(map, String.to_atom(key))
                      def normalize_rows(rows), do: Enum.map(rows, fn row -> %{"name" => get_key(row, "name"), "rank" => get_key(row, "rank")} end)
                      def assert_equal(actual, expected, label), do: if(actual != expected, do: raise("#{label}: expected #{inspect(expected)}, got #{inspect(actual)}"))
                    end

                    defmodule DemoTest do
                      def run do
                        DemoTestHelper.assert_equal(
                          Solution.dense_ranks([
                            %{"name" => "Ana", "score" => 9},
                            %{"name" => "Bo", "score" => 9},
                            %{"name" => "Cid", "score" => 7}
                          ]) |> DemoTestHelper.normalize_rows(),
                          [
                            %{"name" => "Ana", "rank" => 1},
                            %{"name" => "Bo", "rank" => 1},
                            %{"name" => "Cid", "rank" => 2}
                          ],
                          "demo_1"
                        )
                        DemoTestHelper.assert_equal(Solution.dense_ranks([]) |> DemoTestHelper.normalize_rows(), [], "demo_2")
                      end
                    end

                    DemoTest.run()
                    """
                ),
                "full_test_func": dedent(
                    """
                    defmodule FullTestHelper do
                      def get_key(map, key) when is_map(map), do: Map.get(map, key) || Map.get(map, String.to_atom(key))
                      def normalize_rows(rows), do: Enum.map(rows, fn row -> %{"name" => get_key(row, "name"), "rank" => get_key(row, "rank")} end)
                      def assert_equal(actual, expected, label), do: if(actual != expected, do: raise("#{label}: expected #{inspect(expected)}, got #{inspect(actual)}"))
                    end

                    defmodule FullTest do
                      def run do
                        cases = [
                          {
                            [
                              %{"name" => "Ana", "score" => 9},
                              %{"name" => "Bo", "score" => 9},
                              %{"name" => "Cid", "score" => 7}
                            ],
                            [
                              %{"name" => "Ana", "rank" => 1},
                              %{"name" => "Bo", "rank" => 1},
                              %{"name" => "Cid", "rank" => 2}
                            ]
                          },
                          {
                            [
                              %{"name" => "Zoe", "score" => 5},
                              %{"name" => "Ari", "score" => 8},
                              %{"name" => "Moe", "score" => 8},
                              %{"bad" => true}
                            ],
                            [
                              %{"name" => "Ari", "rank" => 1},
                              %{"name" => "Moe", "rank" => 1},
                              %{"name" => "Zoe", "rank" => 2}
                            ]
                          },
                          {[], []},
                          {[%{"name" => "Solo", "score" => 1}], [%{"name" => "Solo", "rank" => 1}]},
                          {
                            [
                              %{"name" => "A", "score" => 3},
                              %{"name" => "B", "score" => 2},
                              %{"name" => "C", "score" => 1}
                            ],
                            [
                              %{"name" => "A", "rank" => 1},
                              %{"name" => "B", "rank" => 2},
                              %{"name" => "C", "rank" => 3}
                            ]
                          }
                        ]

                        Enum.with_index(cases)
                        |> Enum.each(fn {{entries, expected}, index} ->
                          actual = Solution.dense_ranks(entries) |> FullTestHelper.normalize_rows()
                          FullTestHelper.assert_equal(actual, expected, "full_#{index}")
                        end)
                      end
                    end

                    FullTest.run()
                    """
                ),
            },
        },
        "bracket_balance_report": {
            "python": {
                "canonical_solution": dedent(
                    """
                    def check_brackets(text):
                        if not isinstance(text, str):
                            return {"balanced": False, "first_error_index": 0}
                        opening = {"(": ")", "[": "]", "{": "}"}
                        closing = {")": "(", "]": "[", "}": "{"}
                        stack = []
                        for index, ch in enumerate(text):
                            if ch in opening:
                                stack.append(ch)
                            elif ch in closing:
                                if not stack or stack[-1] != closing[ch]:
                                    return {"balanced": False, "first_error_index": index}
                                stack.pop()
                        if stack:
                            return {"balanced": False, "first_error_index": len(text)}
                        return {"balanced": True, "first_error_index": None}
                    """
                ),
                "demo_test_func": dedent(
                    """
                    def test():
                        assert check_brackets("(]") == {"balanced": False, "first_error_index": 1}
                        assert check_brackets("([]{})") == {"balanced": True, "first_error_index": None}

                    if __name__ == "__main__":
                        test()
                    """
                ),
                "full_test_func": dedent(
                    """
                    def test():
                        cases = [
                            ("(]", {"balanced": False, "first_error_index": 1}),
                            ("([]{})", {"balanced": True, "first_error_index": None}),
                            ("(()", {"balanced": False, "first_error_index": 3}),
                            ("a[b]{c}", {"balanced": True, "first_error_index": None}),
                            ("]", {"balanced": False, "first_error_index": 0}),
                        ]
                        for index, (text, expected) in enumerate(cases):
                            actual = check_brackets(text)
                            assert actual == expected, f"case {index}: expected {expected!r}, got {actual!r}"

                    if __name__ == "__main__":
                        test()
                    """
                ),
            },
            "typescript": {
                "canonical_solution": dedent(
                    """
                    function checkBrackets(text: unknown): { balanced: boolean; first_error_index: number | null } {
                      if (typeof text !== "string") return { balanced: false, first_error_index: 0 };
                      const closing: Record<string, string> = { ")": "(", "]": "[", "}": "{" };
                      const opening = new Set(["(", "[", "{"]);
                      const stack: string[] = [];
                      for (let index = 0; index < text.length; index += 1) {
                        const ch = text[index];
                        if (opening.has(ch)) {
                          stack.push(ch);
                        } else if (Object.prototype.hasOwnProperty.call(closing, ch)) {
                          if (stack.length === 0 || stack[stack.length - 1] !== closing[ch]) {
                            return { balanced: false, first_error_index: index };
                          }
                          stack.pop();
                        }
                      }
                      if (stack.length > 0) return { balanced: false, first_error_index: text.length };
                      return { balanced: true, first_error_index: null };
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
                      assertDeepEqual(checkBrackets("(]"), { balanced: false, first_error_index: 1 }, "demo_1");
                      assertDeepEqual(checkBrackets("([]{})"), { balanced: true, first_error_index: null }, "demo_2");
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
                      const cases: Array<[string, any]> = [
                        ["(]", { balanced: false, first_error_index: 1 }],
                        ["([]{})", { balanced: true, first_error_index: null }],
                        ["(()", { balanced: false, first_error_index: 3 }],
                        ["a[b]{c}", { balanced: true, first_error_index: null }],
                        ["]", { balanced: false, first_error_index: 0 }],
                      ];
                      cases.forEach(([text, expected], index) => {
                        assertDeepEqual(checkBrackets(text), expected, `full_${index}`);
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
                      def check_brackets(text) when is_binary(text) do
                        chars = String.graphemes(text)

                        case Enum.with_index(chars) |> Enum.reduce_while([], fn {char, index}, stack ->
                               case char do
                                 "(" -> {:cont, ["(" | stack]}
                                 "[" -> {:cont, ["[" | stack]}
                                 "{" -> {:cont, ["{" | stack]}
                             ")" -> close_or_error(stack, "(", index)
                             "]" -> close_or_error(stack, "[", index)
                             "}" -> close_or_error(stack, "{", index)
                                 _ -> {:cont, stack}
                               end
                             end) do
                          {:error, index} ->
                            %{"balanced" => false, "first_error_index" => index}

                          stack ->
                            if stack == [] do
                              %{"balanced" => true, "first_error_index" => nil}
                            else
                              %{"balanced" => false, "first_error_index" => String.length(text)}
                            end
                        end
                      end

                      def check_brackets(_), do: %{"balanced" => false, "first_error_index" => 0}

                      defp close_or_error([expected | rest], expected, _index), do: {:cont, rest}
                      defp close_or_error(_stack, _expected, index), do: {:halt, {:error, index}}
                    end
                    """
                ),
                "demo_test_func": dedent(
                    """
                    defmodule DemoTestHelper do
                      def get_key(map, key) when is_map(map) do
                        cond do
                          Map.has_key?(map, key) -> Map.get(map, key)
                          Map.has_key?(map, String.to_atom(key)) -> Map.get(map, String.to_atom(key))
                          true -> nil
                        end
                      end
                      def normalize_result(value), do: %{"balanced" => get_key(value, "balanced"), "first_error_index" => get_key(value, "first_error_index")}
                      def assert_equal(actual, expected, label), do: if(actual != expected, do: raise("#{label}: expected #{inspect(expected)}, got #{inspect(actual)}"))
                    end

                    defmodule DemoTest do
                      def run do
                        DemoTestHelper.assert_equal(
                          Solution.check_brackets("(]") |> DemoTestHelper.normalize_result(),
                          %{"balanced" => false, "first_error_index" => 1},
                          "demo_1"
                        )
                        DemoTestHelper.assert_equal(
                          Solution.check_brackets("([]{})") |> DemoTestHelper.normalize_result(),
                          %{"balanced" => true, "first_error_index" => nil},
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
                        cond do
                          Map.has_key?(map, key) -> Map.get(map, key)
                          Map.has_key?(map, String.to_atom(key)) -> Map.get(map, String.to_atom(key))
                          true -> nil
                        end
                      end
                      def normalize_result(value), do: %{"balanced" => get_key(value, "balanced"), "first_error_index" => get_key(value, "first_error_index")}
                      def assert_equal(actual, expected, label), do: if(actual != expected, do: raise("#{label}: expected #{inspect(expected)}, got #{inspect(actual)}"))
                    end

                    defmodule FullTest do
                      def run do
                        cases = [
                          {"(]", %{"balanced" => false, "first_error_index" => 1}},
                          {"([]{})", %{"balanced" => true, "first_error_index" => nil}},
                          {"(()", %{"balanced" => false, "first_error_index" => 3}},
                          {"a[b]{c}", %{"balanced" => true, "first_error_index" => nil}},
                          {"]", %{"balanced" => false, "first_error_index" => 0}}
                        ]

                        Enum.with_index(cases)
                        |> Enum.each(fn {{text, expected}, index} ->
                          actual = Solution.check_brackets(text) |> FullTestHelper.normalize_result()
                          FullTestHelper.assert_equal(actual, expected, "full_#{index}")
                        end)
                      end
                    end

                    FullTest.run()
                    """
                ),
            },
        },
    }
