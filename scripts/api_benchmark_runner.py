#!/usr/bin/env python3

from __future__ import annotations

import argparse
from collections import deque
import json
import os
import random
import sys
import threading
import time
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from pathlib import Path
from typing import Any

from anthropic import Anthropic
from openai import OpenAI
from tqdm import tqdm

try:
    import psutil
except ImportError:  # pragma: no cover - optional dependency
    psutil = None

SYSTEM_PROMPT = (
    "You are an expert programmer. Your task is to provide a code solution within "
    "a single Markdown code block for the given programming problem. Do not include "
    "any direct execution commands, test cases, or usage examples within the code block."
)


def row_identity(row: dict[str, Any], key: str) -> str | None:
    value = row.get(key)
    if value is None:
        return None
    if isinstance(value, str):
        return value.strip()
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL at {path}:{line_number}: {exc}") from exc
    return rows


def load_completed_rows(path: Path, dedupe_key: str) -> set[str]:
    if not path.exists():
        return set()
    completed: set[str] = set()
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            output = row.get("output")
            identity = row_identity(row, dedupe_key)
            if identity and output:
                completed.add(identity)
    return completed


def normalize_openai_input(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for message in messages:
        role = message.get("role")
        content = message.get("content")
        if not role:
            raise ValueError(f"Invalid message without role: {message!r}")
        normalized.append({"role": role, "content": content})
    return normalized


def split_anthropic_messages(messages: list[dict[str, Any]]) -> tuple[str | None, list[dict[str, Any]]]:
    system_chunks: list[str] = []
    normalized: list[dict[str, Any]] = []
    for message in messages:
        role = message.get("role")
        content = message.get("content")
        if role == "system":
            if isinstance(content, str) and content.strip():
                system_chunks.append(content)
            continue
        if role not in {"user", "assistant"}:
            raise ValueError(f"Unsupported Anthropic message role: {role!r}")
        normalized.append({"role": role, "content": content})
    system_prompt = "\n\n".join(system_chunks).strip() or None
    return system_prompt, normalized


def resolve_generation_input(
    row: dict[str, Any],
    question_key: str,
    messages_key: str,
) -> tuple[str, str | list[dict[str, Any]]]:
    messages = row.get(messages_key)
    if isinstance(messages, list) and messages:
        return messages_key, messages

    question = row.get(question_key)
    if isinstance(question, str) and question.strip():
        return question_key, question

    raise ValueError(
        f"Row is missing a usable '{messages_key}' list or '{question_key}' string"
    )


def append_jsonl(path: Path, row: dict[str, Any], lock: threading.Lock) -> None:
    encoded = json.dumps(row, ensure_ascii=False)
    with lock:
        with path.open("a", encoding="utf-8") as handle:
            handle.write(encoded + "\n")


def sample_system_state() -> dict[str, float | None]:
    cpu_percent: float | None = None
    memory_percent: float | None = None
    load_ratio: float | None = None

    if psutil is not None:
        cpu_percent = psutil.cpu_percent(interval=None)
        memory_percent = psutil.virtual_memory().percent

    try:
        cpu_count = os.cpu_count() or 1
        load_ratio = os.getloadavg()[0] / cpu_count
    except (AttributeError, OSError):
        load_ratio = None

    return {
        "cpu_percent": cpu_percent,
        "memory_percent": memory_percent,
        "load_ratio": load_ratio,
    }


def should_reduce_target(
    state: dict[str, float | None],
    cpu_high_watermark: float,
    memory_high_watermark: float,
    load_high_watermark: float,
) -> bool:
    cpu_percent = state["cpu_percent"]
    memory_percent = state["memory_percent"]
    load_ratio = state["load_ratio"]
    return (
        (cpu_percent is not None and cpu_percent >= cpu_high_watermark)
        or (memory_percent is not None and memory_percent >= memory_high_watermark)
        or (load_ratio is not None and load_ratio >= load_high_watermark)
    )


def should_increase_target(
    state: dict[str, float | None],
    cpu_high_watermark: float,
    memory_high_watermark: float,
    load_high_watermark: float,
) -> bool:
    cpu_percent = state["cpu_percent"]
    memory_percent = state["memory_percent"]
    load_ratio = state["load_ratio"]
    cpu_ok = cpu_percent is None or cpu_percent <= cpu_high_watermark - 20
    memory_ok = memory_percent is None or memory_percent <= memory_high_watermark - 8
    load_ok = load_ratio is None or load_ratio <= load_high_watermark - 0.2
    return cpu_ok and memory_ok and load_ok


def format_state(state: dict[str, float | None]) -> str:
    cpu = "n/a" if state["cpu_percent"] is None else f"{state['cpu_percent']:.0f}%"
    mem = "n/a" if state["memory_percent"] is None else f"{state['memory_percent']:.0f}%"
    load = "n/a" if state["load_ratio"] is None else f"{state['load_ratio']:.2f}"
    return f"cpu={cpu} mem={mem} load={load}"


def rolling_average(values: deque[float]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)


def rolling_error_rate(events: deque[bool]) -> float | None:
    if not events:
        return None
    return sum(1 for item in events if item) / len(events)


def format_latency(seconds: float | None) -> str:
    if seconds is None:
        return "n/a"
    return f"{seconds:.1f}s"


def looks_like_rate_limit(error_text: str) -> bool:
    lowered = error_text.lower()
    return "rate limit" in lowered or "429" in lowered or "too many requests" in lowered


def normalize_openai_reasoning(reasoning_effort: str | None) -> str | None:
    if not reasoning_effort:
        return None
    effort = reasoning_effort.strip().lower().replace("_", "-")
    aliases = {
        "extra-high": "xhigh",
        "x-high": "xhigh",
        "very-high": "xhigh",
        "minimal": "none",
    }
    effort = aliases.get(effort, effort)
    if effort not in {"none", "low", "medium", "high", "xhigh"}:
        raise ValueError(
            "Unsupported OpenAI reasoning effort. Use one of: none, low, medium, high, xhigh, extra-high."
        )
    return effort


def openai_output_text(response: Any) -> str:
    output_text = getattr(response, "output_text", None)
    if output_text:
        return output_text

    parts: list[str] = []
    for item in getattr(response, "output", []) or []:
        for content in getattr(item, "content", []) or []:
            text = getattr(content, "text", None)
            if text:
                parts.append(text)
    return "\n".join(parts).strip()


def response_incomplete_reason(response: Any) -> str | None:
    details = getattr(response, "incomplete_details", None)
    if details is None:
        return None
    return getattr(details, "reason", None)


def response_reasoning_only(response: Any) -> bool:
    usage = getattr(response, "usage", None)
    if usage is None:
        return False
    output_tokens = getattr(usage, "output_tokens", None)
    output_details = getattr(usage, "output_tokens_details", None)
    reasoning_tokens = getattr(output_details, "reasoning_tokens", None) if output_details is not None else None
    return bool(output_tokens) and output_tokens == reasoning_tokens


class OpenAIRunner:
    def __init__(
        self,
        model: str,
        max_tokens: int,
        reasoning_effort: str | None,
        verbosity: str | None,
        base_url: str | None,
    ) -> None:
        self.model = model
        self.max_tokens = max_tokens
        self.reasoning_effort = normalize_openai_reasoning(reasoning_effort)
        self.verbosity = verbosity
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not set")
        client_kwargs: dict[str, Any] = {"api_key": api_key}
        if base_url:
            client_kwargs["base_url"] = base_url
        self.client = OpenAI(**client_kwargs)

    def _create_response(self, model_input: str | list[dict[str, Any]], reasoning_effort: str | None, max_tokens: int) -> Any:
        kwargs: dict[str, Any] = {
            "model": self.model,
            "max_output_tokens": max_tokens,
        }
        if isinstance(model_input, str):
            kwargs["input"] = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": model_input},
            ]
        else:
            kwargs["input"] = normalize_openai_input(model_input)
        if reasoning_effort:
            kwargs["reasoning"] = {"effort": reasoning_effort}
        if self.verbosity:
            kwargs["text"] = {"verbosity": self.verbosity}
        return self.client.responses.create(**kwargs)

    def generate(self, model_input: str | list[dict[str, Any]]) -> str:
        expanded_max_tokens = min(max(self.max_tokens * 2, self.max_tokens), 16384)
        attempts = [
            (self.reasoning_effort, self.max_tokens),
            ("low", self.max_tokens),
            ("none", self.max_tokens),
            ("low", expanded_max_tokens),
            ("none", expanded_max_tokens),
        ]
        seen: set[tuple[str | None, int]] = set()
        last_response: Any | None = None

        for reasoning_effort, max_tokens in attempts:
            key = (reasoning_effort, max_tokens)
            if key in seen:
                continue
            seen.add(key)
            response = self._create_response(model_input, reasoning_effort, max_tokens)
            last_response = response
            incomplete_reason = response_incomplete_reason(response)
            output = openai_output_text(response).strip()
            if output and incomplete_reason != "max_output_tokens":
                return output
            if output and incomplete_reason == "max_output_tokens":
                continue

            if incomplete_reason == "max_output_tokens" and response_reasoning_only(response):
                continue
            raise RuntimeError(
                f"OpenAI response did not contain text output "
                f"(status={getattr(response, 'status', None)}, incomplete_reason={incomplete_reason})"
            )

        raise RuntimeError(
            "OpenAI response used all output tokens for reasoning and never produced text "
            f"(status={getattr(last_response, 'status', None)}, "
            f"incomplete_reason={response_incomplete_reason(last_response)})"
        )


class AnthropicRunner:
    def __init__(
        self,
        model: str,
        max_tokens: int,
        thinking_budget: int,
        base_url: str | None,
    ) -> None:
        self.model = model
        self.max_tokens = max_tokens
        self.thinking_budget = thinking_budget
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is not set")
        client_kwargs: dict[str, Any] = {"api_key": api_key}
        if base_url:
            client_kwargs["base_url"] = base_url
        self.client = Anthropic(**client_kwargs)

    def generate(self, model_input: str | list[dict[str, Any]]) -> str:
        kwargs: dict[str, Any] = {
            "model": self.model,
            "max_tokens": self.max_tokens,
        }
        if isinstance(model_input, str):
            kwargs["system"] = SYSTEM_PROMPT
            kwargs["messages"] = [{"role": "user", "content": model_input}]
        else:
            system_prompt, messages = split_anthropic_messages(model_input)
            kwargs["system"] = system_prompt or ""
            kwargs["messages"] = messages
        if self.thinking_budget > 0:
            kwargs["thinking"] = {"type": "enabled", "budget_tokens": self.thinking_budget}
        response = self.client.messages.create(**kwargs)
        parts: list[str] = []
        for block in response.content:
            if getattr(block, "type", None) == "text":
                parts.append(block.text)
        output = "\n".join(parts).strip()
        if not output:
            raise RuntimeError("Anthropic response did not contain text output")
        return output


def build_runner(args: argparse.Namespace) -> Any:
    if args.provider == "openai":
        return OpenAIRunner(
            model=args.model,
            max_tokens=args.max_tokens,
            reasoning_effort=args.reasoning_effort,
            verbosity=args.verbosity,
            base_url=args.base_url,
        )
    if args.provider == "anthropic":
        return AnthropicRunner(
            model=args.model,
            max_tokens=args.max_tokens,
            thinking_budget=args.thinking_budget,
            base_url=args.base_url,
        )
    raise ValueError(f"Unsupported provider: {args.provider}")


def process_row(
    runner: Any,
    row: dict[str, Any],
    provider: str,
    model_label: str,
    question_key: str,
    messages_key: str,
    max_attempts: int,
    min_retry_seconds: float,
    max_retry_seconds: float,
) -> dict[str, Any]:
    input_kind, model_input = resolve_generation_input(row, question_key, messages_key)
    last_error: Exception | None = None
    started_at = time.monotonic()
    for attempt in range(1, max_attempts + 1):
        try:
            output = runner.generate(model_input)
            result = dict(row)
            result["output"] = output
            result["_benchmark_provider"] = provider
            result["_benchmark_model"] = model_label
            result["_benchmark_input_kind"] = input_kind
            result["_benchmark_latency_seconds"] = time.monotonic() - started_at
            return result
        except Exception as exc:  # pragma: no cover - network retry path
            last_error = exc
            if attempt == max_attempts:
                break
            base_delay = min(max_retry_seconds, min_retry_seconds * (2 ** (attempt - 1)))
            sleep_seconds = min(max_retry_seconds, base_delay + random.uniform(0, 1.0))
            time.sleep(sleep_seconds)
    elapsed = time.monotonic() - started_at
    raise RuntimeError(f"Failed after {max_attempts} attempts in {elapsed:.1f}s: {last_error}") from last_error


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate AutoCodeBench outputs with OpenAI or Anthropic APIs.")
    parser.add_argument("--provider", choices=["openai", "anthropic"], required=True)
    parser.add_argument("--model", required=True, help="Exact API model identifier to use.")
    parser.add_argument("--input-file", default="data/benchmarks/autocodebench.jsonl")
    parser.add_argument("--output-file", required=True)
    parser.add_argument("--error-file")
    parser.add_argument("--question-key", default="question")
    parser.add_argument("--messages-key", default="messages")
    parser.add_argument("--dedupe-key", default="question")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--concurrency", type=int, default=4, help="Target or maximum concurrency.")
    parser.add_argument("--min-concurrency", type=int, default=4)
    parser.add_argument("--adaptive-concurrency", action="store_true")
    parser.add_argument("--adjust-interval-seconds", type=float, default=5.0)
    parser.add_argument("--cpu-high-watermark", type=float, default=85.0)
    parser.add_argument("--memory-high-watermark", type=float, default=85.0)
    parser.add_argument("--load-high-watermark", type=float, default=1.15)
    parser.add_argument("--latency-high-watermark-seconds", type=float, default=18.0)
    parser.add_argument("--latency-low-watermark-seconds", type=float, default=10.0)
    parser.add_argument("--error-rate-high-watermark", type=float, default=0.12)
    parser.add_argument("--error-window-size", type=int, default=24)
    parser.add_argument("--latency-window-size", type=int, default=24)
    parser.add_argument("--max-tokens", type=int, default=8192)
    parser.add_argument("--max-attempts", type=int, default=5)
    parser.add_argument("--min-retry-seconds", type=float, default=2.0)
    parser.add_argument("--max-retry-seconds", type=float, default=30.0)
    parser.add_argument("--base-url")
    parser.add_argument("--label", help="Friendly model label stored in output metadata.")
    parser.add_argument(
        "--reasoning-effort",
        default="high",
        help="OpenAI reasoning effort: minimal, low, medium, high, or extra-high.",
    )
    parser.add_argument(
        "--verbosity",
        choices=["low", "medium", "high"],
        default="high",
        help="OpenAI text verbosity, if supported by the selected model.",
    )
    parser.add_argument(
        "--thinking-budget",
        type=int,
        default=16000,
        help="Anthropic extended thinking budget tokens. Set to 0 to disable.",
    )
    args = parser.parse_args()

    input_path = Path(args.input_file)
    output_path = Path(args.output_file)
    error_path = Path(args.error_file) if args.error_file else output_path.with_suffix(".errors.jsonl")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    error_path.parent.mkdir(parents=True, exist_ok=True)

    dataset = read_jsonl(input_path)
    completed = load_completed_rows(output_path, args.dedupe_key)
    pending = []
    for row in dataset:
        identity = row_identity(row, args.dedupe_key)
        if identity and identity in completed:
            continue
        pending.append(row)
    if args.limit is not None:
        pending = pending[: args.limit]

    if not pending:
        print(f"No pending rows for {output_path}")
        return 0

    max_concurrency = max(1, args.concurrency)
    min_concurrency = max(1, min(args.min_concurrency, max_concurrency))
    model_label = args.label or args.model
    runner = build_runner(args)
    write_lock = threading.Lock()
    sample_system_state()

    print(
        f"Starting {args.provider} benchmark run with model={args.model} "
        f"rows={len(pending)} concurrency={max_concurrency}"
    )
    with ThreadPoolExecutor(max_workers=max_concurrency) as executor:
        pending_iter = iter(pending)
        future_to_row: dict[Any, dict[str, Any]] = {}
        future_started_at: dict[Any, float] = {}
        target_concurrency = min_concurrency if args.adaptive_concurrency else max_concurrency
        last_adjustment_at = time.monotonic()
        completions_since_adjustment = 0
        recent_latencies: deque[float] = deque(maxlen=args.latency_window_size)
        recent_errors: deque[bool] = deque(maxlen=args.error_window_size)
        recent_rate_limits: deque[bool] = deque(maxlen=args.error_window_size)
        progress = tqdm(total=len(pending), unit="row")
        progress.set_postfix_str(f"inflight=0 target={target_concurrency}")

        def submit_until_target() -> None:
            while len(future_to_row) < target_concurrency:
                try:
                    row = next(pending_iter)
                except StopIteration:
                    return
                future = executor.submit(
                    process_row,
                    runner,
                    row,
                    args.provider,
                    model_label,
                    args.question_key,
                    args.messages_key,
                    args.max_attempts,
                    args.min_retry_seconds,
                    args.max_retry_seconds,
                )
                future_to_row[future] = row
                future_started_at[future] = time.monotonic()

        submit_until_target()
        while future_to_row:
            timeout = args.adjust_interval_seconds if args.adaptive_concurrency else None
            done, _ = wait(future_to_row, return_when=FIRST_COMPLETED, timeout=timeout)

            if args.adaptive_concurrency and time.monotonic() - last_adjustment_at >= args.adjust_interval_seconds:
                state = sample_system_state()
                previous_target = target_concurrency
                avg_latency = rolling_average(recent_latencies)
                error_rate = rolling_error_rate(recent_errors)
                rate_limit_rate = rolling_error_rate(recent_rate_limits)
                system_overloaded = should_reduce_target(
                    state,
                    args.cpu_high_watermark,
                    args.memory_high_watermark,
                    args.load_high_watermark,
                )
                latency_bad = avg_latency is not None and avg_latency >= args.latency_high_watermark_seconds
                error_bad = error_rate is not None and error_rate >= args.error_rate_high_watermark
                rate_limit_bad = rate_limit_rate is not None and rate_limit_rate > 0

                if system_overloaded or latency_bad or error_bad or rate_limit_bad:
                    reduction = 3 if rate_limit_bad or error_bad else 2
                    target_concurrency = max(min_concurrency, target_concurrency - reduction)
                elif should_increase_target(
                    state,
                    args.cpu_high_watermark,
                    args.memory_high_watermark,
                    args.load_high_watermark,
                ):
                    latency_good = avg_latency is None or avg_latency <= args.latency_low_watermark_seconds
                    error_good = error_rate is None or error_rate <= args.error_rate_high_watermark / 2
                    if latency_good and error_good and completions_since_adjustment > 0:
                        target_concurrency = min(max_concurrency, target_concurrency + 1)
                if target_concurrency != previous_target:
                    print(
                        f"[adaptive] target_concurrency {previous_target} -> {target_concurrency} "
                        f"({format_state(state)} avg_latency={format_latency(avg_latency)} "
                        f"error_rate={'n/a' if error_rate is None else f'{error_rate:.0%}'})"
                    )
                last_adjustment_at = time.monotonic()
                completions_since_adjustment = 0

            for future in done:
                row = future_to_row.pop(future)
                started_at = future_started_at.pop(future, None)
                try:
                    result = future.result()
                    recent_errors.append(False)
                    latency = result.get("_benchmark_latency_seconds")
                    if latency is None and started_at is not None:
                        latency = time.monotonic() - started_at
                    if latency is not None:
                        recent_latencies.append(float(latency))
                    recent_rate_limits.append(False)
                    append_jsonl(output_path, result, write_lock)
                except Exception as exc:  # pragma: no cover - network retry path
                    recent_errors.append(True)
                    recent_rate_limits.append(looks_like_rate_limit(str(exc)))
                    if started_at is not None:
                        recent_latencies.append(time.monotonic() - started_at)
                    error_row = {
                        args.question_key: row.get(args.question_key),
                        args.messages_key: row.get(args.messages_key),
                        "language": row.get("language"),
                        "provider": args.provider,
                        "model": args.model,
                        "dedupe_identity": row_identity(row, args.dedupe_key),
                        "error": str(exc),
                    }
                    append_jsonl(error_path, error_row, write_lock)
                    print(f"ERROR [{row.get('language')}]: {exc}", file=sys.stderr)
                completions_since_adjustment += 1
                progress.update(1)
            submit_until_target()
            avg_latency = rolling_average(recent_latencies)
            error_rate = rolling_error_rate(recent_errors)
            progress.set_postfix_str(
                f"inflight={len(future_to_row)} target={target_concurrency} "
                f"lat={format_latency(avg_latency)} "
                f"err={'n/a' if error_rate is None else f'{error_rate:.0%}'}"
            )
        progress.close()

    print(f"Wrote outputs to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
