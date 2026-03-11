#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import requests
import time
import argparse
import os
import logging
import re
import shutil
import subprocess
import tempfile
import shlex
from typing import Dict, Any, List
from multiprocessing import Pool
from tqdm import tqdm
from prettytable import PrettyTable

try:
    import psutil
except ImportError:  # pragma: no cover - optional dependency
    psutil = None

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('unified_processor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# Global processor instance to avoid repeated creation
_global_processor = None


NATIVE_LANGUAGE_SPECS = {
    "elixir": {
        "file_name": "test.ex",
        "commands": [
            ["elixir", "{file_path}"],
        ],
    },
    "gleam": {
        "file_name": "acb_bench.gleam",
        "commands": [
            ["gleam", "run"],
        ],
    },
    "lean4": {
        "file_name": "Main.lean",
        "commands": [
            ["lean", "--run", "{file_path}"],
        ],
    },
    "racket": {
        "file_name": "test.rkt",
        "commands": [
            ["racket", "{file_path}"],
            ["raco", "test", "{file_path}"],
        ],
    },
    "typescript_effect": {
        "file_name": "test.ts",
        "commands": [
            ["{tsx_bin}", "{file_name}"],
        ],
    },
}


def sample_system_state() -> Dict[str, float]:
    cpu_percent = None
    memory_percent = None
    load_ratio = None

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


def should_reduce_target(state: Dict[str, float], cpu_high_watermark: float,
                         memory_high_watermark: float, load_high_watermark: float) -> bool:
    cpu_percent = state.get("cpu_percent")
    memory_percent = state.get("memory_percent")
    load_ratio = state.get("load_ratio")
    return (
        (cpu_percent is not None and cpu_percent >= cpu_high_watermark) or
        (memory_percent is not None and memory_percent >= memory_high_watermark) or
        (load_ratio is not None and load_ratio >= load_high_watermark)
    )


def should_increase_target(state: Dict[str, float], cpu_high_watermark: float,
                           memory_high_watermark: float, load_high_watermark: float) -> bool:
    cpu_percent = state.get("cpu_percent")
    memory_percent = state.get("memory_percent")
    load_ratio = state.get("load_ratio")
    cpu_ok = cpu_percent is None or cpu_percent <= cpu_high_watermark - 20
    memory_ok = memory_percent is None or memory_percent <= memory_high_watermark - 8
    load_ok = load_ratio is None or load_ratio <= load_high_watermark - 0.2
    return cpu_ok and memory_ok and load_ok


def format_system_state(state: Dict[str, float]) -> str:
    cpu = "n/a" if state.get("cpu_percent") is None else f"{state['cpu_percent']:.0f}%"
    mem = "n/a" if state.get("memory_percent") is None else f"{state['memory_percent']:.0f}%"
    load = "n/a" if state.get("load_ratio") is None else f"{state['load_ratio']:.2f}"
    return f"cpu={cpu} mem={mem} load={load}"


def parse_native_languages(raw_value: str) -> List[str]:
    if not raw_value:
        return []
    return sorted({item.strip().lower() for item in raw_value.split(",") if item.strip()})


def init_worker(server_ip, server_port, native_languages=None, native_timeout_seconds: float = 45.0):
    """Initialize worker process"""
    global _global_processor
    _global_processor = UnifiedProcessor(
        server_ip,
        server_port,
        native_languages=native_languages,
        native_timeout_seconds=native_timeout_seconds,
    )


def process_single_data_worker(args):
    """Multiprocess worker function to process a single data item"""
    data, index, debug = args
    global _global_processor

    # Use global processor instance
    result = _global_processor.process_data(data, debug)
    result["index"] = index
    result["original_data"] = data

    return result


def process_single_data_worker(data, index, debug, print_code=False):
    """Single task worker function to process one data item"""
    global _global_processor

    result = _global_processor.process_data(data, debug, print_code)
    result["index"] = index
    result["original_data"] = data

    time.sleep(0.2)  # Appropriate delay to avoid API overload
    return result


class UnifiedProcessor:
    def __init__(self, server_ip: str = "localhost", server_port: int = 8080,
                 native_languages: List[str] = None, native_timeout_seconds: float = 45.0):
        self.server_ip = server_ip
        self.server_port = server_port
        self.submit_url = f"http://{server_ip}:{server_port}/submit"
        self.headers = {
            "Content-Type": "application/json"
        }
        self.native_languages = set(native_languages or [])
        self.native_timeout_seconds = native_timeout_seconds
        self.repo_root = os.path.dirname(os.path.abspath(__file__))

    
    def read_jsonl_file(self, file_path: str, line_number: int = None, target_language: str = None) -> List[Dict[str, Any]]:
        """Read JSONL file and return data list"""
        data_list = []
        total_count = 0
        filtered_count = 0

        with open(file_path, 'r', encoding='utf-8') as file:
            for line_num, line in enumerate(file, 1):
                line = line.strip()
                if line:
                    try:
                        data = json.loads(line)

                        total_count += 1

                        # Language filtering
                        if target_language:
                            data_language = data.get("language", "").lower()
                            if data_language != target_language.lower():
                                continue
                            filtered_count += 1
                        else:
                            filtered_count += 1

                        # Add absolute and relative line number information
                        data['_absolute_line_number'] = line_num
                        data['_relative_line_number'] = filtered_count
                        data_list.append(data)
                    except json.JSONDecodeError as e:
                        logger.error(f"JSON parsing error at line {line_num}: {e}")
                        continue

            if target_language:
                logger.info(f"Language filter: {target_language} - Total {total_count} items, matched {filtered_count} items, finally read {len(data_list)} items")
            else:
                logger.info(f"Successfully read {len(data_list)} items")
            return data_list


    def extract_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract required fields"""
        return {
            "language": data.get("language", "").lower(),
            "full_test_func": data.get("full_test_func", ""),
            "demo_test_func": data.get("demo_test_func", ""),
            "main_test_func": data.get("extracted_code", "")
        }
    
    def call_submit_api(self, data: Dict[str, Any], test_type: str = "full", debug: bool = False, print_code: bool = False) -> Dict[str, Any]:
        """Call submit API"""
        try:
            language = data["language"]

            # Select test code based on test type
            if test_type == "full":
                test_code = data["full_test_func"]
            elif test_type == "demo":
                test_code = data["demo_test_func"]
            else:
                raise ValueError(f"Unsupported test type: {test_type}")

            if language in self.native_languages:
                return self.call_submit_native(data, language, test_code, test_type)

            payload = {
                "src_uid": f"0710_bench_test_{test_type}_{int(time.time())}",
                "func_code": data["main_test_func"],  # code solution
                "main_code": test_code,  # test function
                "lang": language,
                "show_log": "true",
                "request_extensions": {"timeout": 30, "debug": str(debug).lower()}
            }
            
            response = requests.post(self.submit_url, headers=self.headers, json=payload, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "response": result,
                    "status_code": response.status_code
                }
            else:
                logger.error(f"API call failed, status code: {response.status_code}, response: {response.text}")
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "status_code": response.status_code
                }
        except Exception as e:
            logger.error(f"Error occurred while processing data: {e}")
            return {
                "success": False,
                "error": str(e),
                "status_code": None
            }

    def call_submit_native(self, data: Dict[str, Any], language: str, test_code: str,
                           test_type: str) -> Dict[str, Any]:
        spec = NATIVE_LANGUAGE_SPECS.get(language)
        if spec is None:
            return {
                "success": False,
                "error": f"Native execution is not implemented for language '{language}'",
                "status_code": None,
            }

        missing_commands = []
        selected_command = None
        extra_formats = {}
        if language == "typescript_effect":
            tsx_bin = self._resolve_typescript_effect_tsx_bin()
            if not tsx_bin:
                return {
                    "success": False,
                    "error": (
                        "TypeScript Effect runtime is not prepared. "
                        "Expected tmp/native_runtimes/typescript_effect/node_modules/.bin/tsx"
                    ),
                    "status_code": None,
                }
            extra_formats["tsx_bin"] = tsx_bin

        for command in spec["commands"]:
            executable = command[0]
            if executable.startswith("{") and executable.endswith("}"):
                selected_command = command
                break
            if shutil.which(executable):
                selected_command = command
                break
            missing_commands.append(executable)

        if selected_command is None:
            return {
                "success": False,
                "error": (
                    f"No native runtime found for '{language}'. "
                    f"Tried: {', '.join(missing_commands)}"
                ),
                "status_code": None,
            }

        source_code = self._combine_native_source(language, data["main_test_func"], test_code)
        with tempfile.TemporaryDirectory(prefix=f"acb-native-{language}-") as tmpdir:
            file_path, working_dir = self._prepare_native_workspace(language, tmpdir, spec["file_name"], source_code)
            rendered_command = [
                part.format(file_path=file_path, file_name=os.path.basename(file_path), **extra_formats)
                for part in selected_command
            ]
            try:
                completed = subprocess.run(
                    rendered_command,
                    cwd=working_dir,
                    capture_output=True,
                    text=True,
                    timeout=self.native_timeout_seconds,
                    check=False,
                )
                response_extensions = {
                    "stdout": completed.stdout,
                    "stderr": completed.stderr,
                    "exit_code": completed.returncode,
                    "native_execution": True,
                    "native_language": language,
                    "command": shlex.join(rendered_command),
                }
                return {
                    "success": True,
                    "response": {
                        "exec_outcome": "PASSED" if completed.returncode == 0 else "RUNTIME_ERROR",
                        "response_extensions": response_extensions,
                    },
                    "status_code": 200,
                }
            except subprocess.TimeoutExpired as exc:
                stdout = exc.stdout or ""
                stderr = exc.stderr or ""
                return {
                    "success": True,
                    "response": {
                        "exec_outcome": "TIME_LIMIT_EXCEEDED",
                        "response_extensions": {
                            "stdout": stdout,
                            "stderr": stderr,
                            "exit_code": None,
                            "native_execution": True,
                            "native_language": language,
                            "command": shlex.join(rendered_command),
                            "timeout_seconds": self.native_timeout_seconds,
                        },
                    },
                    "status_code": 200,
                }

    def _combine_native_source(self, language: str, solution_code: str, test_code: str) -> str:
        solution = solution_code.rstrip()
        tests = test_code.rstrip()

        if language == "racket":
            test_lines = tests.lstrip().splitlines()
            if test_lines and test_lines[0].startswith("#lang "):
                tests = "\n".join(test_lines[1:]).lstrip()

        return f"{solution}\n\n{tests}\n"

    def _prepare_native_workspace(self, language: str, tmpdir: str, file_name: str, source_code: str) -> tuple[str, str]:
        if language == "gleam":
            project_dir = os.path.join(tmpdir, "gleam_project")
            os.makedirs(os.path.join(project_dir, "src"), exist_ok=True)
            gleam_toml = """name = "acb_bench"\nversion = "1.0.0"\n\n[dependencies]\ngleam_stdlib = ">= 0.44.0 and < 2.0.0"\n\n[dev-dependencies]\ngleeunit = ">= 1.0.0 and < 2.0.0"\n"""
            with open(os.path.join(project_dir, "gleam.toml"), "w", encoding="utf-8") as handle:
                handle.write(gleam_toml)
            file_path = os.path.join(project_dir, "src", file_name)
            with open(file_path, "w", encoding="utf-8") as handle:
                handle.write(source_code)
            return file_path, project_dir

        if language == "typescript_effect":
            runtime_root = self._typescript_effect_runtime_root()
            case_dir = os.path.join(runtime_root, os.path.basename(tmpdir))
            os.makedirs(case_dir, exist_ok=True)
            file_path = os.path.join(case_dir, file_name)
            with open(file_path, "w", encoding="utf-8") as handle:
                handle.write(source_code)
            return file_path, case_dir

        file_path = os.path.join(tmpdir, file_name)
        with open(file_path, "w", encoding="utf-8") as handle:
            handle.write(source_code)
        return file_path, tmpdir

    def _typescript_effect_runtime_root(self) -> str:
        return os.path.join(self.repo_root, "tmp", "native_runtimes", "typescript_effect")

    def _resolve_typescript_effect_tsx_bin(self) -> str | None:
        runtime_root = self._typescript_effect_runtime_root()
        tsx_bin = os.path.join(runtime_root, "node_modules", ".bin", "tsx")
        if os.path.exists(tsx_bin):
            return tsx_bin
        return None
    
    def process_data(self, data: Dict[str, Any], debug: bool = False, print_code: bool = False) -> Dict[str, Any]:
        """Process single data item, call submit API twice"""
        extracted_data = self.extract_fields(data)
        
        # Check if necessary fields exist
        if not all(extracted_data.values()):
            logger.warning("Data missing required fields, skipping processing")
            return {
                "success": False,
                "error": "Missing required fields",
                "full_test_result": None,
                "demo_test_result": None,
                "language": extracted_data["language"]
            }
        
        # Call full_test_func
        full_test_result = self.call_submit_api(extracted_data, "full", debug, print_code)
        time.sleep(0.5)
        # Call demo_test_func
        demo_test_result = self.call_submit_api(extracted_data, "demo", debug, print_code)

        # Determine overall success (both API calls succeed and code execution passes)
        full_api_success = full_test_result.get("success", False)
        demo_api_success = demo_test_result.get("success", False)
        full_exec_passed = (full_api_success and 
                           full_test_result.get("response", {}).get("exec_outcome") == "PASSED")
        demo_exec_passed = (demo_api_success and 
                           demo_test_result.get("response", {}).get("exec_outcome") == "PASSED")
        overall_success = full_exec_passed and demo_exec_passed

        return {
            "success": overall_success,
            "full_test_result": full_test_result,
            "demo_test_result": demo_test_result,
            "language": extracted_data["language"],
            "full_test_detail": full_test_result.get("response", {}),
            "demo_test_detail": demo_test_result.get("response", {})
        }
    
    def process_file(self, file_path: str, max_items: int = None, line_number: int = None,
                     debug: bool = False, concurrency: int = 5, target_language: str = None,
                     solution_key: str = 'output', adaptive_concurrency: bool = False,
                     min_concurrency: int = 2, adjust_interval_seconds: float = 5.0,
                     cpu_high_watermark: float = 85.0,
                     memory_high_watermark: float = 85.0,
                     load_high_watermark: float = 1.15) -> List[Dict[str, Any]]:
        """Process entire JSONL file"""
        logger.info(f"Start processing file: {file_path}")
        if target_language:
            logger.info(f"Language filter: only processing {target_language} language data")

        # Read data
        data_list = self.read_jsonl_file(file_path, line_number, target_language)

        def _extract_code_blocks(output: str, language: str, solution: str) -> str:
            """Extract code blocks from output field, format: ```{language}\n{code}```"""
            if not output:
                return ""

            # Use regex to match code blocks
            matches = re.finditer(r'```(\w+)\n(.*?)```', output, flags=re.DOTALL)

            extract_code = ""
            for match in matches:
                language = match.group(1)
                code = match.group(2).strip()
                if code:  # If code is extracted, return the first non-empty code block
                    extract_code = code
                    break

            if language == "elixir":
                code_list = extract_code.split("\n")
                solution_list = solution.strip().split("\n")
                assert solution_list[0].startswith("defmodule") and solution_list[-1].startswith("end")
                if code_list[0].startswith("defmodule") and code_list[-1].startswith("end"):
                    code_list = code_list[1:-1]
                    code_list = [solution_list[0]] + code_list + [solution_list[-1]]
                else:  # No defmodule generated, append directly
                    code_list = ["  " + line for line in code_list]
                    code_list = [solution_list[0]] + code_list + [solution_list[-1]]
                extract_code = "\n".join(code_list)

            if extract_code != "": return extract_code

            # If no standard format matched, try simple first line removal
            # First remove starting and ending ``` symbols
            cleaned_output = output.strip()
            if cleaned_output.startswith('```'):
                cleaned_output = cleaned_output[3:]
            if cleaned_output.endswith('```'):
                cleaned_output = cleaned_output[:-3]

            lines = cleaned_output.strip().split('\n')
            if len(lines) > 1:
                # Remove first line, return remaining content
                return '\n'.join(lines[1:]).strip()

            return cleaned_output.strip()

        for data in data_list:
            if solution_key == "canonical_solution":
                extract_code = data[solution_key]
            else:
                extract_code = _extract_code_blocks(data[solution_key], data["language"],data["canonical_solution"])
            data["extracted_code"] = extract_code if extract_code else "error! no code extracted"

        # Use multiprocess mode
        logger.info(f"Using multiprocess mode, concurrency: {concurrency}")
        return self._process_file_multiprocess(
            data_list,
            debug,
            concurrency,
            adaptive_concurrency,
            min_concurrency,
            adjust_interval_seconds,
            cpu_high_watermark,
            memory_high_watermark,
            load_high_watermark,
        )

    def _process_file_serial(self, data_list: List[Dict[str, Any]], line_number: int = None,
                           debug: bool = False) -> List[Dict[str, Any]]:
        """Process file serially"""
        results = []

        # Check if single line mode (for printing code)
        is_single_line_mode = line_number is not None

        # Use tqdm to show progress
        desc = f"Processing line {line_number} data" if line_number else "Serial processing"
        with tqdm(total=len(data_list), desc=desc, unit="items") as pbar:
            for i, data in enumerate(data_list, 1):
                result = self.process_data(data, debug, print_code=is_single_line_mode)
                result["index"] = i
                result["original_data"] = data
                results.append(result)

                # Update progress bar
                pbar.update(1)
                pbar.set_postfix({
                    "Success": sum(1 for r in results if r.get("success", False)),
                    "Failed": sum(1 for r in results if not r.get("success", False))
                })

                # Wait slightly between each processing to avoid too frequent requests
                if i < len(data_list):
                    time.sleep(0.1)

        logger.info(f"Serial processing completed, processed {len(results)} items")
        return results
    
    def _process_file_multiprocess(self, data_list: List[Dict[str, Any]], debug: bool = False,
                                 concurrency: int = 5, adaptive_concurrency: bool = False,
                                 min_concurrency: int = 2, adjust_interval_seconds: float = 5.0,
                                 cpu_high_watermark: float = 85.0,
                                 memory_high_watermark: float = 85.0,
                                 load_high_watermark: float = 1.15) -> List[Dict[str, Any]]:
        """Process file with multiprocessing - simplified version"""
        total_items = len(data_list)
        max_concurrency = max(1, concurrency)
        min_concurrency = max(1, min(min_concurrency, max_concurrency))
        target_concurrency = min_concurrency if adaptive_concurrency else max_concurrency

        logger.info(f"Starting up to {max_concurrency} processes to handle {total_items} items")

        results = []
        try:
            # Use process pool, each task processes one data item
            with Pool(
                processes=max_concurrency,
                initializer=init_worker,
                initargs=(
                    self.server_ip,
                    self.server_port,
                    sorted(self.native_languages),
                    self.native_timeout_seconds,
                ),
            ) as pool:
                # Use tqdm to show progress
                with tqdm(total=total_items, desc=f"Multiprocess (up to {max_concurrency} processes)", unit="items") as pbar:
                    futures = []
                    next_index = 0
                    completed_count = 0
                    last_adjustment_at = time.monotonic()
                    sample_system_state()

                    def submit_until_target():
                        nonlocal next_index
                        while len(futures) < target_concurrency and next_index < total_items:
                            data = data_list[next_index]
                            future = pool.apply_async(process_single_data_worker, (data, next_index + 1, debug, False))
                            futures.append(future)
                            next_index += 1

                    submit_until_target()
                    pbar.set_postfix({"Success": 0, "Failed": 0, "InFlight": len(futures), "Target": target_concurrency})

                    # Collect results
                    while futures:
                        if adaptive_concurrency and time.monotonic() - last_adjustment_at >= adjust_interval_seconds:
                            state = sample_system_state()
                            previous_target = target_concurrency
                            if should_reduce_target(state, cpu_high_watermark, memory_high_watermark, load_high_watermark):
                                target_concurrency = max(min_concurrency, target_concurrency - 2)
                            elif should_increase_target(state, cpu_high_watermark, memory_high_watermark, load_high_watermark):
                                target_concurrency = min(max_concurrency, target_concurrency + 1)
                            if target_concurrency != previous_target:
                                logger.info(
                                    f"[adaptive] target_concurrency {previous_target} -> {target_concurrency} "
                                    f"({format_system_state(state)})"
                                )
                            last_adjustment_at = time.monotonic()

                        future = futures[0]
                        try:
                            result = future.get(timeout=300)  # 5 minutes timeout
                            results.append(result)
                            pbar.update(1)
                            completed_count += 1

                            # Update progress bar statistics
                            pbar.set_postfix({
                                "Success": sum(1 for r in results if r.get("success", False)),
                                "Failed": sum(1 for r in results if not r.get("success", False)),
                                "InFlight": len(futures) - 1,
                                "Target": target_concurrency
                            })
                        except Exception as e:
                            logger.error(f"Task failed: {e}")
                            # Create failed result
                            failed_result = {
                                "index": completed_count + 1,
                                "success": False,
                                "error": str(e),
                                "original_data": {}
                            }
                            results.append(failed_result)
                            pbar.update(1)
                            completed_count += 1
                        finally:
                            futures.pop(0)
                            submit_until_target()

        except Exception as e:
            logger.error(f"Error occurred during multiprocess processing: {e}")
            # If multiprocessing fails, fallback to serial processing
            logger.info("Falling back to serial processing mode")
            return self._process_file_serial(data_list, debug=debug)

        # Sort results by index
        results.sort(key=lambda x: x.get("index", 0))

        logger.info(f"Multiprocess processing completed, processed {len(results)} items")
        return results

    def save_results(self, results: List[Dict[str, Any]], output_file: str):
        """Save processing results to file"""
        def _sanitize_jsonable(value):
            if isinstance(value, bytes):
                return value.decode('utf-8', errors='replace')
            if isinstance(value, dict):
                return {str(k): _sanitize_jsonable(v) for k, v in value.items()}
            if isinstance(value, list):
                return [_sanitize_jsonable(v) for v in value]
            if isinstance(value, tuple):
                return [_sanitize_jsonable(v) for v in value]
            if isinstance(value, set):
                return [_sanitize_jsonable(v) for v in sorted(value, key=repr)]
            return value

        with open(output_file, 'w', encoding='utf-8') as f:
            for result in results:
                # Simplify output format, keep only necessary information
                simplified_result = {
                    "index": result.get("index", 0),
                    "language": result.get("language", ""),
                    "success": result.get("success", False),
                    "full_test_result": _sanitize_jsonable(result.get("full_test_result", {})),
                    "demo_test_result": _sanitize_jsonable(result.get("demo_test_result", {})),
                    "original_data": _sanitize_jsonable(result.get("original_data", {}))
                }
                f.write(json.dumps(simplified_result, ensure_ascii=False) + '\n')
        logger.info(f"Results saved to: {output_file}")

    def print_detailed_statistics(self, results: List[Dict[str, Any]]):
        """Print detailed statistics report table"""
        if not results:
            print("\n❌ No data processed")
            return

        # Group statistics by language
        language_stats = {}
        failed_items = []

        for result in results:
            try:
                language = result.get("language", "unknown")
                success = result.get("success", False)
                index = result.get("index", 0)

                # Initialize language statistics
                if language not in language_stats:
                    language_stats[language] = {
                        "total": 0,
                        "success": 0,
                        "failed": 0,
                        "full_passed": 0,
                        "demo_passed": 0,
                        "both_passed": 0,
                        "failed_indices": []
                    }

                # Update statistics
                stats = language_stats[language]
                stats["total"] += 1

                if success:
                    stats["success"] += 1
                else:
                    stats["failed"] += 1
                    # Get absolute and relative line numbers
                    absolute_line = result.get("original_data", {}).get("_absolute_line_number", index)
                    relative_line = result.get("original_data", {}).get("_relative_line_number", index)

                    stats["failed_indices"].append({
                        "absolute_line": absolute_line,
                        "relative_line": relative_line
                    })
                    failed_items.append({
                        "index": index,
                        "absolute_line": absolute_line,
                        "relative_line": relative_line,
                        "language": language,
                        "full_outcome": result.get("full_test_result", {}).get("response", {}).get("exec_outcome", "unknown"),
                        "demo_outcome": result.get("demo_test_result", {}).get("response", {}).get("exec_outcome", "unknown"),
                        "full_error": result.get("full_test_result", {}).get("error", ""),
                        "demo_error": result.get("demo_test_result", {}).get("error", "")
                    })

                # Detailed test result statistics
                full_outcome = result.get("full_test_result", {}).get("response", {}).get("exec_outcome", "")
                demo_outcome = result.get("demo_test_result", {}).get("response", {}).get("exec_outcome", "")

                if full_outcome == "PASSED":
                    stats["full_passed"] += 1
                if demo_outcome == "PASSED":
                    stats["demo_passed"] += 1
                if full_outcome == "PASSED" and demo_outcome == "PASSED":
                    stats["both_passed"] += 1
            except Exception as e:
                logger.error(f"Error occurred while calculating test statistics: {e} data:\n {result}")
                continue

        # Print overall statistics
        total_items = len(results)
        total_success = sum(1 for r in results if r.get("success", False))
        total_failed = total_items - total_success

        print("\n" + "="*80)
        print("🎯 Execution Results Statistics Report")
        print("="*80)

        print(f"\n📊 Overall Statistics:")
        print(f"   Total Processed: {total_items} items")
        print(f"   Success:        {total_success} items ({total_success/total_items*100:.1f}%)")
        print(f"   Failed:         {total_failed} items ({total_failed/total_items*100:.1f}%)")

        # Use PrettyTable to print detailed statistics by language
        print(f"\n📋 Detailed Statistics by Language:")
        language_table = PrettyTable()
        language_table.field_names = ["Language", "Total", "Success", "Failed", "Success Rate", "Demo Passed", "Full Passed", "Both Passed"]
        language_table.align = "l"
        language_table.align["Total"] = "r"
        language_table.align["Success"] = "r"
        language_table.align["Failed"] = "r"
        language_table.align["Success Rate"] = "r"
        language_table.align["Demo Passed"] = "r"
        language_table.align["Full Passed"] = "r"
        language_table.align["Both Passed"] = "r"

        # Add data sorted by language name
        for language in sorted(language_stats.keys()):
            stats = language_stats[language]
            success_rate = stats["success"] / stats["total"] * 100 if stats["total"] > 0 else 0

            language_table.add_row([
                language,
                stats["total"],
                stats["success"],
                stats["failed"],
                f"{success_rate:.1f}%",
                stats["demo_passed"],
                stats["full_passed"],
                stats["both_passed"]
            ])

        print(language_table)

        
def main():
    parser = argparse.ArgumentParser(description='Unified JSONL file processor (supports all languages)')
    parser.add_argument('-i', '--input_file', help='Input JSONL file path')
    parser.add_argument('-o', '--output', help='Output file path')
    parser.add_argument('-m', '--max-items', type=int, help='Maximum number of items to process')
    parser.add_argument('-l', '--line', type=int, help='Specify which line to process (starting from 1)')
    parser.add_argument('--server_ip', help='Server IP address', default='localhost')
    parser.add_argument('--server_port', type=int, help='Server port', default=8080)
    parser.add_argument('-d', '--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('-c', '--concurrency', type=int, default=30, help='Number of concurrent processes (default 30)')
    parser.add_argument('--lang', help='Specify programming language to process, only process data of that language')
    parser.add_argument('--solution_key', default='output', help='Specify the key name where the solution is located')
    parser.add_argument('--adaptive-concurrency', action='store_true', help='Adapt scorer concurrency based on host load')
    parser.add_argument('--min-concurrency', type=int, default=2, help='Minimum scorer concurrency when adaptive mode is enabled')
    parser.add_argument('--adjust-interval-seconds', type=float, default=5.0, help='How often to reevaluate adaptive scorer concurrency')
    parser.add_argument('--cpu-high-watermark', type=float, default=85.0, help='Reduce scorer concurrency above this CPU percent')
    parser.add_argument('--memory-high-watermark', type=float, default=85.0, help='Reduce scorer concurrency above this memory percent')
    parser.add_argument('--load-high-watermark', type=float, default=1.15, help='Reduce scorer concurrency above this 1m load ratio')
    parser.add_argument(
        '--native-langs',
        default=os.environ.get('ACB_NATIVE_LANGS', ''),
        help='Comma-separated languages to run natively instead of through the sandbox, e.g. elixir,racket',
    )
    parser.add_argument(
        '--native-timeout-seconds',
        type=float,
        default=float(os.environ.get('ACB_NATIVE_TIMEOUT_SECONDS', '45')),
        help='Timeout for native language execution when --native-langs is enabled',
    )

    args = parser.parse_args()
    
    if args.concurrency > 20:
        logger.warning("High concurrency may put pressure on the server, recommended not to exceed 20")

    native_languages = parse_native_languages(args.native_langs)
    if native_languages:
        logger.info(f"Native execution enabled for languages: {', '.join(native_languages)}")

    # Create processor
    processor = UnifiedProcessor(
        args.server_ip,
        args.server_port,
        native_languages=native_languages,
        native_timeout_seconds=args.native_timeout_seconds,
    )

    # Process file
    results = processor.process_file(
        args.input_file,
        args.max_items,
        args.line,
        args.debug,
        args.concurrency,
        args.lang,
        args.solution_key,
        args.adaptive_concurrency,
        args.min_concurrency,
        args.adjust_interval_seconds,
        args.cpu_high_watermark,
        args.memory_high_watermark,
        args.load_high_watermark,
    )

    # Determine output filename
    if args.output:
        output_file = args.output
    else:
        # Extract language information from input filename, generate output filename with language prefix
        input_basename = os.path.basename(args.input_file)
        base_name = input_basename.replace('.jsonl', '')  # e.g.: typescript.jsonl -> typescript

        # If language filter is specified, reflect it in the filename
        if args.lang:
            output_file = f"{base_name}_{args.lang}_results.jsonl"
        else:
            output_file = f"{base_name}_results.jsonl"

    # Save results
    if results:
        processor.save_results(results, output_file)
        
        # Generate detailed statistics report
        processor.print_detailed_statistics(results)
    else:
        logger.warning("No data processed")


if __name__ == "__main__":
    # Execute main function
    main()
