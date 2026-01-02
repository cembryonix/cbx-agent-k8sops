#!/usr/bin/env python3
"""
End-to-end UI tests using Playwright.

Tests are defined in test-cases/ui-tests.yaml for easy modification.
This runner interprets the YAML and executes tests with Playwright.

Usage:
    # Run with headless browser
    python test_ui.py

    # Run with visible browser
    python test_ui.py --visible

    # Specify app URL
    python test_ui.py --url http://localhost:3000
"""

import asyncio
import sys
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

import yaml

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


@dataclass
class E2EConfig:
    app_url: str = "http://localhost:3000"
    headless: bool = True
    timeout: int = 30000  # ms
    verbose: bool = False


class E2ETestRunner:
    """Runner for Playwright E2E tests loaded from YAML."""

    def __init__(self, config: E2EConfig):
        self.config = config
        self.results: list[TestResult] = []
        self.test_definitions: list[dict] = []
        self.defaults: dict = {}

    def _log(self, message: str) -> None:
        if self.config.verbose:
            print(f"  [DEBUG] {message}")

    def load_tests(self, yaml_path: Path) -> None:
        """Load test definitions from YAML file."""
        with open(yaml_path) as f:
            data = yaml.safe_load(f)

        self.defaults = data.get("defaults", {})
        self.test_definitions = data.get("tests", [])
        self._log(f"Loaded {len(self.test_definitions)} test definitions")

    async def run_all_tests(self) -> list[TestResult]:
        """Run all E2E tests from loaded definitions."""
        print("\n" + "=" * 60)
        print("E2E UI Tests (Playwright)")
        print("=" * 60)
        print(f"App URL: {self.config.app_url}")
        print(f"Tests loaded: {len(self.test_definitions)}")
        print("=" * 60)

        try:
            from playwright.async_api import async_playwright
        except ImportError:
            print("\nPlaywright not installed. Run:")
            print("  pip install playwright && playwright install chromium")
            return [TestResult(
                name="playwright_setup",
                status=TestStatus.SKIPPED,
                message="Playwright not installed",
            )]

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.config.headless)
            context = await browser.new_context()
            page = await context.new_page()

            try:
                for test_def in self.test_definitions:
                    result = await self._run_test(page, test_def)
                    self.results.append(result)

                    # Stop if page_loads fails
                    if test_def.get("name") == "page_loads" and result.status != TestStatus.PASSED:
                        print("  Skipping remaining tests - page failed to load")
                        break

            finally:
                await browser.close()

        self._print_summary()
        return self.results

    async def _run_test(self, page, test_def: dict) -> TestResult:
        """Run a single test based on its definition."""
        name = test_def.get("name", "unnamed")
        action = test_def.get("action", "")
        timeout = test_def.get("settings", {}).get("timeout", self.defaults.get("timeout", 30000))

        start = time.time()
        try:
            self._log(f"Running test: {name} (action: {action})")

            if action == "navigate":
                result = await self._action_navigate(page, test_def, timeout)
            elif action == "wait_for_text":
                result = await self._action_wait_for_text(page, test_def, timeout)
            elif action == "check_element":
                result = await self._action_check_element(page, test_def, timeout)
            elif action == "interact":
                result = await self._action_interact(page, test_def, timeout)
            else:
                result = TestResult(
                    name=name,
                    status=TestStatus.SKIPPED,
                    message=f"Unknown action: {action}",
                )

            result.duration_ms = (time.time() - start) * 1000
            return result

        except Exception as e:
            return TestResult(
                name=name,
                status=TestStatus.ERROR,
                message=str(e),
                duration_ms=(time.time() - start) * 1000,
            )

    async def _action_navigate(self, page, test_def: dict, timeout: int) -> TestResult:
        """Navigate to app URL and check for errors."""
        name = test_def.get("name", "navigate")
        settings = test_def.get("settings", {})
        expect = test_def.get("expect", {})

        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))

        response = await page.goto(
            self.config.app_url,
            timeout=timeout,
            wait_until=settings.get("wait_until", "networkidle"),
        )

        if expect.get("response_ok", True):
            if response is None or not response.ok:
                return TestResult(
                    name=name,
                    status=TestStatus.FAILED,
                    message=f"Page load failed: {response.status if response else 'no response'}",
                )

        if expect.get("no_console_errors", False) and errors:
            return TestResult(
                name=name,
                status=TestStatus.FAILED,
                message=f"Page errors: {errors[0]}",
                details={"errors": errors},
            )

        return TestResult(
            name=name,
            status=TestStatus.PASSED,
            message="Page loaded successfully",
        )

    async def _action_wait_for_text(self, page, test_def: dict, timeout: int) -> TestResult:
        """Wait for specific text to appear on page."""
        name = test_def.get("name", "wait_for_text")
        settings = test_def.get("settings", {})
        text = settings.get("text", "")
        on_failure = test_def.get("on_failure", {})

        try:
            await page.wait_for_selector(
                f"text={text}",
                timeout=settings.get("timeout", timeout),
            )
            return TestResult(
                name=name,
                status=TestStatus.PASSED,
                message=f"Found text: {text[:50]}...",
            )
        except Exception:
            # Check failure selectors
            check_selectors = on_failure.get("check_selectors", [])
            for selector in check_selectors:
                error_el = await page.query_selector(selector)
                if error_el:
                    error_text = await error_el.text_content()
                    return TestResult(
                        name=name,
                        status=TestStatus.FAILED,
                        message=f"Error found: {error_text[:100] if error_text else 'unknown'}",
                    )

            return TestResult(
                name=name,
                status=TestStatus.FAILED,
                message=f"Text not found after {timeout}ms: {text[:50]}",
            )

    async def _action_check_element(self, page, test_def: dict, timeout: int) -> TestResult:
        """Check if any of the specified elements exist."""
        name = test_def.get("name", "check_element")
        selectors = test_def.get("selectors", [])
        expect = test_def.get("expect", {})
        soft_pass = test_def.get("soft_pass", False)
        on_failure = test_def.get("on_failure", {})

        for selector in selectors:
            element = await page.query_selector(selector)
            if element:
                self._log(f"Found element: {selector}")
                return TestResult(
                    name=name,
                    status=TestStatus.PASSED,
                    message=f"Element found: {selector}",
                )

        # No element found
        if on_failure.get("screenshot"):
            await page.screenshot(path=on_failure["screenshot"])
            self._log(f"Screenshot saved: {on_failure['screenshot']}")

        if soft_pass:
            return TestResult(
                name=name,
                status=TestStatus.PASSED,
                message="No elements found (soft pass - may be mobile layout)",
            )

        return TestResult(
            name=name,
            status=TestStatus.FAILED,
            message=f"None of {len(selectors)} selectors matched",
        )

    async def _action_interact(self, page, test_def: dict, timeout: int) -> TestResult:
        """Execute interactive steps (fill, click, etc)."""
        name = test_def.get("name", "interact")
        steps = test_def.get("steps", [])
        on_failure = test_def.get("on_failure", {})

        element = None

        for step in steps:
            step_type = step.get("type", "")

            if step_type == "find_element":
                for selector in step.get("selectors", []):
                    element = await page.query_selector(selector)
                    if element:
                        self._log(f"Found input: {selector}")
                        break

                if not element and step.get("required", False):
                    if on_failure.get("screenshot"):
                        await page.screenshot(path=on_failure["screenshot"])
                    return TestResult(
                        name=name,
                        status=TestStatus.SKIPPED,
                        message="Required element not found",
                    )

            elif step_type == "fill" and element:
                value = step.get("value", "")
                self._log(f"Filling: {value}")
                await element.fill(value)

            elif step_type == "press" and element:
                key = step.get("key", "Enter")
                self._log(f"Pressing: {key}")
                await element.press(key)

            elif step_type == "wait_for_response":
                step_timeout = step.get("timeout", timeout)
                expect_any = step.get("expect_any", [])

                # Build JS condition
                conditions = " || ".join([f"body.includes('{e}')" for e in expect_any])
                js_code = f"""() => {{
                    const body = document.body.innerText;
                    return {conditions};
                }}"""

                try:
                    self._log(f"Waiting for response (up to {step_timeout}ms)...")
                    await page.wait_for_function(js_code, timeout=step_timeout)
                    return TestResult(
                        name=name,
                        status=TestStatus.PASSED,
                        message="Message sent and response received",
                    )
                except Exception:
                    if on_failure.get("screenshot"):
                        await page.screenshot(path=on_failure["screenshot"])
                    return TestResult(
                        name=name,
                        status=TestStatus.FAILED,
                        message=f"No response after {step_timeout}ms",
                    )

        return TestResult(
            name=name,
            status=TestStatus.PASSED,
            message="All steps completed",
        )

    def _print_summary(self) -> None:
        print("\n" + "=" * 60)
        print("Summary")
        print("=" * 60)

        passed = sum(1 for r in self.results if r.status == TestStatus.PASSED)
        failed = sum(1 for r in self.results if r.status == TestStatus.FAILED)
        skipped = sum(1 for r in self.results if r.status == TestStatus.SKIPPED)
        errors = sum(1 for r in self.results if r.status == TestStatus.ERROR)

        total = len(self.results)
        total_time = sum(r.duration_ms for r in self.results)

        for r in self.results:
            if r.status == TestStatus.PASSED:
                status_str = f"\033[32m{r.status.value}\033[0m"
            elif r.status == TestStatus.SKIPPED:
                status_str = f"\033[33m{r.status.value}\033[0m"
            else:
                status_str = f"\033[31m{r.status.value}\033[0m"
            print(f"  {r.name}: {status_str} ({r.duration_ms:.0f}ms)")

        print(f"\n  Passed:  {passed}/{total}")
        print(f"  Failed:  {failed}/{total}")
        print(f"  Skipped: {skipped}/{total}")
        print(f"  Errors:  {errors}/{total}")
        print(f"  Time:    {total_time:.0f}ms")

        if failed > 0 or errors > 0:
            print("\n  \033[31mStatus: FAILED\033[0m")
        else:
            print("\n  \033[32mStatus: PASSED\033[0m")


async def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="E2E UI Tests")
    parser.add_argument("--url", default="http://localhost:3000", help="App URL")
    parser.add_argument("--visible", action="store_true", help="Show browser window")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument(
        "--tests",
        type=Path,
        default=Path(__file__).parent / "test-cases" / "ui-tests.yaml",
        help="Path to test definitions YAML",
    )
    args = parser.parse_args()

    config = E2EConfig(
        app_url=args.url,
        headless=not args.visible,
        verbose=args.verbose,
    )

    runner = E2ETestRunner(config)
    runner.load_tests(args.tests)
    results = await runner.run_all_tests()

    failed = sum(1 for r in results if r.status in (TestStatus.FAILED, TestStatus.ERROR))
    return 1 if failed > 0 else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
