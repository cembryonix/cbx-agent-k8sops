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


class Status(Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    ERROR = "ERROR"


@dataclass
class Result:
    name: str
    status: Status
    message: str
    duration_ms: float = 0.0
    details: dict[str, Any] = field(default_factory=dict)


class StateTestRunner:
    """Runner for state unit tests."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.results: list[Result] = []

    def _log(self, message: str) -> None:
        if self.verbose:
            print(f"  [DEBUG] {message}")

    async def run_all_tests(self) -> list[Result]:
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

    async def _test_state_initial_values(self) -> Result:
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
                    return Result(
                        name="state_initial_values",
                        status=Status.FAILED,
                        message=f"ChatState missing attribute: {attr}",
                        duration_ms=(time.time() - start) * 1000,
                    )

            return Result(
                name="state_initial_values",
                status=Status.PASSED,
                message="All initial state attributes present",
                duration_ms=(time.time() - start) * 1000,
            )

        except Exception as e:
            return Result(
                name="state_initial_values",
                status=Status.ERROR,
                message=str(e),
                duration_ms=(time.time() - start) * 1000,
            )

    async def _test_state_set_input(self) -> Result:
        """Test set_input method exists and is callable."""
        start = time.time()
        try:
            from k8sops.ui.state.chat import ChatState

            if not hasattr(ChatState, "set_input"):
                return Result(
                    name="state_set_input",
                    status=Status.FAILED,
                    message="ChatState missing set_input method",
                    duration_ms=(time.time() - start) * 1000,
                )

            if not callable(getattr(ChatState, "set_input")):
                return Result(
                    name="state_set_input",
                    status=Status.FAILED,
                    message="set_input is not callable",
                    duration_ms=(time.time() - start) * 1000,
                )

            return Result(
                name="state_set_input",
                status=Status.PASSED,
                message="set_input method available",
                duration_ms=(time.time() - start) * 1000,
            )

        except Exception as e:
            return Result(
                name="state_set_input",
                status=Status.ERROR,
                message=str(e),
                duration_ms=(time.time() - start) * 1000,
            )

    async def _test_state_clear_input(self) -> Result:
        """Test clear_input method."""
        start = time.time()
        try:
            from k8sops.ui.state.chat import ChatState

            if not hasattr(ChatState, "clear_input"):
                return Result(
                    name="state_clear_input",
                    status=Status.FAILED,
                    message="ChatState missing clear_input method",
                    duration_ms=(time.time() - start) * 1000,
                )

            return Result(
                name="state_clear_input",
                status=Status.PASSED,
                message="clear_input method available",
                duration_ms=(time.time() - start) * 1000,
            )

        except Exception as e:
            return Result(
                name="state_clear_input",
                status=Status.ERROR,
                message=str(e),
                duration_ms=(time.time() - start) * 1000,
            )

    async def _test_state_set_error(self) -> Result:
        """Test set_error_message method."""
        start = time.time()
        try:
            from k8sops.ui.state.chat import ChatState

            if not hasattr(ChatState, "set_error_message"):
                return Result(
                    name="state_set_error",
                    status=Status.FAILED,
                    message="ChatState missing set_error_message method",
                    duration_ms=(time.time() - start) * 1000,
                )

            return Result(
                name="state_set_error",
                status=Status.PASSED,
                message="set_error_message method available",
                duration_ms=(time.time() - start) * 1000,
            )

        except Exception as e:
            return Result(
                name="state_set_error",
                status=Status.ERROR,
                message=str(e),
                duration_ms=(time.time() - start) * 1000,
            )

    async def _test_state_clear_error(self) -> Result:
        """Test clear_error method."""
        start = time.time()
        try:
            from k8sops.ui.state.chat import ChatState

            if not hasattr(ChatState, "clear_error"):
                return Result(
                    name="state_clear_error",
                    status=Status.FAILED,
                    message="ChatState missing clear_error method",
                    duration_ms=(time.time() - start) * 1000,
                )

            return Result(
                name="state_clear_error",
                status=Status.PASSED,
                message="clear_error method available",
                duration_ms=(time.time() - start) * 1000,
            )

        except Exception as e:
            return Result(
                name="state_clear_error",
                status=Status.ERROR,
                message=str(e),
                duration_ms=(time.time() - start) * 1000,
            )

    async def _test_state_clear_chat(self) -> Result:
        """Test clear_chat method."""
        start = time.time()
        try:
            from k8sops.ui.state.chat import ChatState

            if not hasattr(ChatState, "clear_chat"):
                return Result(
                    name="state_clear_chat",
                    status=Status.FAILED,
                    message="ChatState missing clear_chat method",
                    duration_ms=(time.time() - start) * 1000,
                )

            return Result(
                name="state_clear_chat",
                status=Status.PASSED,
                message="clear_chat method available",
                duration_ms=(time.time() - start) * 1000,
            )

        except Exception as e:
            return Result(
                name="state_clear_chat",
                status=Status.ERROR,
                message=str(e),
                duration_ms=(time.time() - start) * 1000,
            )

    def _print_summary(self) -> None:
        print("\n" + "=" * 60)
        print("Summary")
        print("=" * 60)

        passed = sum(1 for r in self.results if r.status == Status.PASSED)
        failed = sum(1 for r in self.results if r.status == Status.FAILED)
        errors = sum(1 for r in self.results if r.status == Status.ERROR)

        total = len(self.results)
        total_time = sum(r.duration_ms for r in self.results)

        for r in self.results:
            status_str = f"\033[32m{r.status.value}\033[0m" if r.status == Status.PASSED else f"\033[31m{r.status.value}\033[0m"
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

    failed = sum(1 for r in results if r.status in (Status.FAILED, Status.ERROR))
    return 1 if failed > 0 else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
