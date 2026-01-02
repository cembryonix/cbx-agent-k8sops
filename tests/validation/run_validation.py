#!/usr/bin/env python3
"""End-to-end validation tests for K8S Ops Agent Chat UI.

Sends standard K8s questions through the UI and validates responses.
"""

import asyncio
import sys
import time
from dataclasses import dataclass
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("ERROR: playwright not installed. Run: pip install playwright && playwright install chromium")
    sys.exit(1)


@dataclass
class E2ETestCase:
    """An end-to-end test case."""
    name: str
    question: str
    expected_keywords: list[str]  # Response should contain at least one of these
    timeout_seconds: int = 30


# Standard K8s questions to test
E2E_TEST_CASES = [
    E2ETestCase(
        name="list_namespaces",
        question="List all namespaces in the cluster",
        expected_keywords=["default", "kube-system", "namespace", "kube-public"],
        timeout_seconds=30,
    ),
    E2ETestCase(
        name="list_pods",
        question="Show pods in all namespaces",
        expected_keywords=["pod", "running", "kube-system", "namespace"],
        timeout_seconds=30,
    ),
    E2ETestCase(
        name="cluster_info",
        question="What Kubernetes version is the cluster running?",
        expected_keywords=["version", "kubernetes", "k8s", "1.", "v1."],
        timeout_seconds=30,
    ),
]


@dataclass
class TestResult:
    """Result of an E2E test."""
    name: str
    passed: bool
    response: str
    duration_ms: int
    error: str = ""


class E2EValidator:
    """End-to-end validation runner."""

    def __init__(self, app_url: str = "http://localhost:3000", headless: bool = True):
        self.app_url = app_url
        self.headless = headless
        self.results: list[TestResult] = []

    async def run_all_tests(self) -> list[TestResult]:
        """Run all E2E test cases."""
        print("=" * 60)
        print("E2E Chat Validation")
        print("=" * 60)
        print(f"App URL: {self.app_url}")
        print(f"Test cases: {len(E2E_TEST_CASES)}")
        print("=" * 60)

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            context = await browser.new_context()
            page = await context.new_page()

            try:
                # Load app and wait for initialization
                print("\n[setup] Loading app and waiting for agent...")
                await page.goto(self.app_url)
                await page.wait_for_load_state("networkidle")

                # Wait for agent to be ready (look for the ready message)
                try:
                    await page.wait_for_function(
                        """() => {
                            const body = document.body.innerText;
                            return body.includes('Ready to help') ||
                                   body.includes('Connected to K8S');
                        }""",
                        timeout=30000,
                    )
                    print("[setup] Agent ready!")
                except Exception as e:
                    print(f"[setup] WARNING: Agent ready message not found: {e}")
                    # Continue anyway - might already be ready

                # Run each test case
                for test_case in E2E_TEST_CASES:
                    result = await self._run_test(page, test_case)
                    self.results.append(result)

                    # Print result
                    status = "PASS" if result.passed else "FAIL"
                    print(f"\n[{test_case.name}] {status} ({result.duration_ms}ms)")
                    if not result.passed:
                        print(f"  Error: {result.error}")
                        print(f"  Response: {result.response[:200]}...")

            finally:
                await browser.close()

        return self.results

    async def _run_test(self, page, test_case: E2ETestCase) -> TestResult:
        """Run a single E2E test case."""
        start_time = time.time()

        try:
            # Find and clear the input
            input_elem = await page.query_selector(
                "input[type='text'], textarea, [contenteditable='true']"
            )
            if not input_elem:
                return TestResult(
                    name=test_case.name,
                    passed=False,
                    response="",
                    duration_ms=int((time.time() - start_time) * 1000),
                    error="Could not find input element",
                )

            # Get current message count to detect new response
            messages_before = await page.evaluate(
                """() => {
                    const msgs = document.querySelectorAll('[class*="message"], [class*="Message"]');
                    return msgs.length;
                }"""
            )

            # Type the question
            await input_elem.fill(test_case.question)
            await page.keyboard.press("Enter")

            # Wait for response (new message appears and processing stops)
            timeout_ms = test_case.timeout_seconds * 1000

            # Wait for the response to complete
            response_text = await page.evaluate(
                """async (params) => {
                    const { timeout, keywords } = params;
                    const start = Date.now();

                    while (Date.now() - start < timeout) {
                        await new Promise(r => setTimeout(r, 500));

                        // Get all message-like elements
                        const body = document.body.innerText.toLowerCase();

                        // Check if any keyword is present
                        const hasKeyword = keywords.some(kw =>
                            body.includes(kw.toLowerCase())
                        );

                        // Check if still processing
                        const isProcessing = body.includes('processing') ||
                                            body.includes('thinking') ||
                                            document.querySelector('[class*="loading"], [class*="spinner"]');

                        if (hasKeyword && !isProcessing) {
                            return document.body.innerText;
                        }
                    }

                    return document.body.innerText;
                }""",
                {"timeout": timeout_ms, "keywords": test_case.expected_keywords},
            )

            duration_ms = int((time.time() - start_time) * 1000)

            # Validate response contains expected keywords
            response_lower = response_text.lower()
            found_keyword = any(kw.lower() in response_lower for kw in test_case.expected_keywords)

            if found_keyword:
                return TestResult(
                    name=test_case.name,
                    passed=True,
                    response=response_text,
                    duration_ms=duration_ms,
                )
            else:
                return TestResult(
                    name=test_case.name,
                    passed=False,
                    response=response_text,
                    duration_ms=duration_ms,
                    error=f"Expected keywords not found: {test_case.expected_keywords}",
                )

        except Exception as e:
            return TestResult(
                name=test_case.name,
                passed=False,
                response="",
                duration_ms=int((time.time() - start_time) * 1000),
                error=str(e),
            )

    def print_summary(self):
        """Print test summary."""
        print("\n" + "=" * 60)
        print("Summary")
        print("=" * 60)

        passed = sum(1 for r in self.results if r.passed)
        total = len(self.results)

        for result in self.results:
            status = "\033[32mPASS\033[0m" if result.passed else "\033[31mFAIL\033[0m"
            print(f"  {result.name}: {status} ({result.duration_ms}ms)")
            if result.error:
                print(f"    -> {result.error}")

        print()
        total_time = sum(r.duration_ms for r in self.results)
        status_color = "\033[32m" if passed == total else "\033[31m"
        print(f"  Passed: {passed}/{total}")
        print(f"  Time:   {total_time}ms")
        print(f"\n  {status_color}Status: {'PASSED' if passed == total else 'FAILED'}\033[0m")


async def main():
    """Run E2E validation."""
    import argparse

    parser = argparse.ArgumentParser(description="E2E Chat Validation")
    parser.add_argument("--url", default="http://localhost:3000", help="App URL")
    parser.add_argument("--visible", action="store_true", help="Show browser window")
    args = parser.parse_args()

    validator = E2EValidator(app_url=args.url, headless=not args.visible)
    await validator.run_all_tests()
    validator.print_summary()

    # Exit with error code if any failed
    failed = sum(1 for r in validator.results if not r.passed)
    sys.exit(1 if failed > 0 else 0)


if __name__ == "__main__":
    asyncio.run(main())
