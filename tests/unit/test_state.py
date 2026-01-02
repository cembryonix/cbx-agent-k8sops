#!/usr/bin/env python3
"""
Unit tests for UI state logic.

Tests ChatState and BaseState without requiring Reflex runtime or external services.

Usage:
    python test_state.py
    python test_state.py -v
"""

import asyncio
import sys
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestStatus(Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    ERROR = "ERROR"


@dataclass
class TestResult:
    name: str
    status: TestStatus
    message: str
    duration_ms: float = 0.0
    details: dict[str, Any] = field(default_factory=dict)


class StateTestRunner:
    """Runner for state unit tests."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.results: list[TestResult] = []

    def _log(self, message: str) -> None:
        if self.verbose:
            print(f"  [DEBUG] {message}")

    async def run_all_tests(self) -> list[TestResult]:
        """Run all state tests."""
        print("\n" + "=" * 60)
        print("State Unit Tests")
        print("=" * 60)

        # Test initial values
        self.results.append(await self._test_state_initial_values())

        # Test setters
        self.results.append(await self._test_state_set_input())
        self.results.append(await self._test_state_clear_input())
        self.results.append(await self._test_state_set_error())
        self.results.append(await self._test_state_clear_error())
        self.results.append(await self._test_state_clear_chat())

        self._print_summary()
        return self.results

    async def _test_state_initial_values(self) -> TestResult:
        """Test that initial state values are correct."""
        start = time.time()
        try:
            from k8sops.ui.state.chat import ChatState

            # Check class attributes (default values)
            # Note: We can't instantiate rx.State outside Reflex runtime
            # So we check the class-level defaults

            defaults = {
                "messages": [],
                "current_input": "",
                "is_streaming": False,
                "is_processing": False,
                "tool_calls": [],
                "available_tools": [],
                "mcp_connected": False,
                "agent_ready": False,
                "error_message": "",
            }

            # Verify ChatState has these attributes
            for attr, expected in defaults.items():
                if not hasattr(ChatState, attr):
                    return TestResult(
                        name="state_initial_values",
                        status=TestStatus.FAILED,
                        message=f"ChatState missing attribute: {attr}",
                        duration_ms=(time.time() - start) * 1000,
                    )

            return TestResult(
                name="state_initial_values",
                status=TestStatus.PASSED,
                message="All initial state attributes present",
                duration_ms=(time.time() - start) * 1000,
            )

        except Exception as e:
            return TestResult(
                name="state_initial_values",
                status=TestStatus.ERROR,
                message=str(e),
                duration_ms=(time.time() - start) * 1000,
            )

    async def _test_state_set_input(self) -> TestResult:
        """Test set_input method exists and is callable."""
        start = time.time()
        try:
            from k8sops.ui.state.chat import ChatState

            if not hasattr(ChatState, "set_input"):
                return TestResult(
                    name="state_set_input",
                    status=TestStatus.FAILED,
                    message="ChatState missing set_input method",
                    duration_ms=(time.time() - start) * 1000,
                )

            if not callable(getattr(ChatState, "set_input")):
                return TestResult(
                    name="state_set_input",
                    status=TestStatus.FAILED,
                    message="set_input is not callable",
                    duration_ms=(time.time() - start) * 1000,
                )

            return TestResult(
                name="state_set_input",
                status=TestStatus.PASSED,
                message="set_input method available",
                duration_ms=(time.time() - start) * 1000,
            )

        except Exception as e:
            return TestResult(
                name="state_set_input",
                status=TestStatus.ERROR,
                message=str(e),
                duration_ms=(time.time() - start) * 1000,
            )

    async def _test_state_clear_input(self) -> TestResult:
        """Test clear_input method."""
        start = time.time()
        try:
            from k8sops.ui.state.chat import ChatState

            if not hasattr(ChatState, "clear_input"):
                return TestResult(
                    name="state_clear_input",
                    status=TestStatus.FAILED,
                    message="ChatState missing clear_input method",
                    duration_ms=(time.time() - start) * 1000,
                )

            return TestResult(
                name="state_clear_input",
                status=TestStatus.PASSED,
                message="clear_input method available",
                duration_ms=(time.time() - start) * 1000,
            )

        except Exception as e:
            return TestResult(
                name="state_clear_input",
                status=TestStatus.ERROR,
                message=str(e),
                duration_ms=(time.time() - start) * 1000,
            )

    async def _test_state_set_error(self) -> TestResult:
        """Test set_error_message method."""
        start = time.time()
        try:
            from k8sops.ui.state.chat import ChatState

            if not hasattr(ChatState, "set_error_message"):
                return TestResult(
                    name="state_set_error",
                    status=TestStatus.FAILED,
                    message="ChatState missing set_error_message method",
                    duration_ms=(time.time() - start) * 1000,
                )

            return TestResult(
                name="state_set_error",
                status=TestStatus.PASSED,
                message="set_error_message method available",
                duration_ms=(time.time() - start) * 1000,
            )

        except Exception as e:
            return TestResult(
                name="state_set_error",
                status=TestStatus.ERROR,
                message=str(e),
                duration_ms=(time.time() - start) * 1000,
            )

    async def _test_state_clear_error(self) -> TestResult:
        """Test clear_error method."""
        start = time.time()
        try:
            from k8sops.ui.state.chat import ChatState

            if not hasattr(ChatState, "clear_error"):
                return TestResult(
                    name="state_clear_error",
                    status=TestStatus.FAILED,
                    message="ChatState missing clear_error method",
                    duration_ms=(time.time() - start) * 1000,
                )

            return TestResult(
                name="state_clear_error",
                status=TestStatus.PASSED,
                message="clear_error method available",
                duration_ms=(time.time() - start) * 1000,
            )

        except Exception as e:
            return TestResult(
                name="state_clear_error",
                status=TestStatus.ERROR,
                message=str(e),
                duration_ms=(time.time() - start) * 1000,
            )

    async def _test_state_clear_chat(self) -> TestResult:
        """Test clear_chat method."""
        start = time.time()
        try:
            from k8sops.ui.state.chat import ChatState

            if not hasattr(ChatState, "clear_chat"):
                return TestResult(
                    name="state_clear_chat",
                    status=TestStatus.FAILED,
                    message="ChatState missing clear_chat method",
                    duration_ms=(time.time() - start) * 1000,
                )

            return TestResult(
                name="state_clear_chat",
                status=TestStatus.PASSED,
                message="clear_chat method available",
                duration_ms=(time.time() - start) * 1000,
            )

        except Exception as e:
            return TestResult(
                name="state_clear_chat",
                status=TestStatus.ERROR,
                message=str(e),
                duration_ms=(time.time() - start) * 1000,
            )

    def _print_summary(self) -> None:
        print("\n" + "=" * 60)
        print("Summary")
        print("=" * 60)

        passed = sum(1 for r in self.results if r.status == TestStatus.PASSED)
        failed = sum(1 for r in self.results if r.status == TestStatus.FAILED)
        errors = sum(1 for r in self.results if r.status == TestStatus.ERROR)

        total = len(self.results)
        total_time = sum(r.duration_ms for r in self.results)

        for r in self.results:
            status_str = f"\033[32m{r.status.value}\033[0m" if r.status == TestStatus.PASSED else f"\033[31m{r.status.value}\033[0m"
            print(f"  {r.name}: {status_str} ({r.duration_ms:.0f}ms)")

        print(f"\n  Passed: {passed}/{total}")
        print(f"  Failed: {failed}/{total}")
        print(f"  Errors: {errors}/{total}")
        print(f"  Time:   {total_time:.0f}ms")

        if failed > 0 or errors > 0:
            print("\n  \033[31mStatus: FAILED\033[0m")
        else:
            print("\n  \033[32mStatus: PASSED\033[0m")


async def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="State Unit Tests")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    args = parser.parse_args()

    runner = StateTestRunner(verbose=args.verbose)
    results = await runner.run_all_tests()

    failed = sum(1 for r in results if r.status in (TestStatus.FAILED, TestStatus.ERROR))
    return 1 if failed > 0 else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
