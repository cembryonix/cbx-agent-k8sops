#!/usr/bin/env python3
"""
MCP Client Integration Tests

Tests that the MCP client works correctly with a given MCP server.
Validates connectivity and tool execution (not MCP protocol spec compliance -
that's tested in the sister project cbx-mcp-server-k8s).

Usage:
    # Test against default config
    python test_mcp_client.py

    # Test against custom URL
    python test_mcp_client.py --url https://cbx-mcp-k8s.example.com/mcp

    # Test specific categories
    python test_mcp_client.py --category read-only

    # Verbose output
    python test_mcp_client.py -v

    # List available tests
    python test_mcp_client.py --list
"""

import argparse
import asyncio
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

import yaml

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from k8sops.mcp_client import MCPClient


class TestStatus(Enum):
    """Status of a test."""

    PASSED = "PASSED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    ERROR = "ERROR"


@dataclass
class TestResult:
    """Result of a single test."""

    name: str
    status: TestStatus
    message: str
    duration_ms: float = 0.0
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class TestCase:
    """A single test case loaded from YAML."""

    name: str
    description: str
    category: str
    tool: str | None = None
    command: str | None = None
    action: str | None = None  # For protocol tests
    expect: dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationConfig:
    """Configuration for validation client."""

    url: str = "https://cbx-mcp-k8s.vvklab.cloud.cembryonix.com/mcp"
    transport: str = "http"
    ssl_verify: bool = False  # For self-signed certs
    timeout: int = 30
    verbose: bool = False
    fail_fast: bool = False
    categories: list[str] = field(default_factory=list)
    expected_tools: list[str] = field(default_factory=list)

    @classmethod
    def from_yaml(cls, path: Path) -> "ValidationConfig":
        """Load config from YAML file."""
        with open(path) as f:
            data = yaml.safe_load(f)

        server = data.get("server", {})
        tests = data.get("tests", {})

        return cls(
            url=server.get("url", cls.url),
            transport=server.get("transport", cls.transport),
            ssl_verify=server.get("ssl_verify", cls.ssl_verify),
            timeout=server.get("timeout", cls.timeout),
            verbose=tests.get("verbose", cls.verbose),
            fail_fast=tests.get("fail_fast", cls.fail_fast),
            categories=tests.get("categories", []),
            expected_tools=data.get("expected_tools", []),
        )


class MCPValidationClient:
    """
    Integration test client for MCP client layer.

    Tests that our MCPClient can connect to an MCP server and
    execute tools correctly. Does not test MCP protocol compliance
    (that's done in cbx-mcp-server-k8s).
    """

    def __init__(self, config: ValidationConfig):
        self.config = config
        self.results: list[TestResult] = []
        self._client: MCPClient | None = None
        self._tools: list[dict] = []
        self._tools_by_name: dict[str, dict] = {}
        self._lc_tools: list[Any] = []
        self._lc_tools_by_name: dict[str, Any] = {}

    def _log(self, message: str) -> None:
        """Log message if verbose mode enabled."""
        if self.config.verbose:
            print(f"  [DEBUG] {message}")

    async def connect(self) -> bool:
        """Connect to the MCP server."""
        try:
            self._log(f"Connecting to {self.config.url} (ssl_verify={self.config.ssl_verify})")

            self._client = MCPClient(
                server_url=self.config.url,
                transport=self.config.transport,
                ssl_verify=self.config.ssl_verify,
            )

            # Connect and get tools
            self._tools = await self._client.connect()
            self._tools_by_name = {t["name"]: t for t in self._tools}

            # Also get LangChain tools for compatibility testing
            self._lc_tools = self._client.get_langchain_tools()
            self._lc_tools_by_name = {t.name: t for t in self._lc_tools}

            self._log(f"Connected, found {len(self._tools)} tools")
            return True

        except Exception as e:
            self._log(f"Connection failed: {e}")
            import traceback
            if self.config.verbose:
                traceback.print_exc()
            return False

    async def disconnect(self) -> None:
        """Disconnect from the MCP server."""
        if self._client:
            await self._client.disconnect()
        self._client = None
        self._tools = []
        self._tools_by_name = {}
        self._lc_tools = []
        self._lc_tools_by_name = {}

    async def _get_tools(self) -> list[dict]:
        """Get available tools from the server."""
        if not self._client:
            raise RuntimeError("Not connected")
        return self._tools

    async def _call_tool(self, tool_name: str, arguments: dict) -> dict:
        """Call a tool and return the result."""
        if not self._client:
            raise RuntimeError("Not connected")

        if tool_name not in self._tools_by_name:
            raise ValueError(f"Tool not found: {tool_name}")

        # Use the client's call_tool method
        try:
            result = await self._client.call_tool(tool_name, arguments)
            return {"content": result, "is_error": False}
        except Exception as e:
            return {"content": str(e), "is_error": True}

    # =========================================================================
    # K8s Tool Tests
    # =========================================================================

    async def run_tool_test(self, test: TestCase) -> TestResult:
        """Run a K8s tool test."""
        import time

        start = time.time()

        try:
            # Check if tool exists
            tools = await self._get_tools()
            if test.tool not in self._tools_by_name:
                return TestResult(
                    name=test.name,
                    status=TestStatus.SKIPPED,
                    message=f"Tool not available: {test.tool}",
                    duration_ms=(time.time() - start) * 1000,
                )

            # Build arguments - only include command if specified
            args = {}
            if test.command is not None:
                args["command"] = test.command

            # Call the tool
            self._log(f"Calling {test.tool}: {test.command or '(no args)'}")
            result = await self._call_tool(test.tool, args)

            content = result.get("content", "")
            is_error = result.get("is_error", False)

            # Check expectations
            expect_success = test.expect.get("success", True)
            output_contains = test.expect.get("output_contains")

            if expect_success and is_error:
                return TestResult(
                    name=test.name,
                    status=TestStatus.FAILED,
                    message="Expected success but got error",
                    duration_ms=(time.time() - start) * 1000,
                    details={"output": str(content)[:500]},
                )

            if output_contains and output_contains not in str(content):
                return TestResult(
                    name=test.name,
                    status=TestStatus.FAILED,
                    message=f"Output missing expected: '{output_contains}'",
                    duration_ms=(time.time() - start) * 1000,
                    details={"output": str(content)[:500]},
                )

            return TestResult(
                name=test.name,
                status=TestStatus.PASSED,
                message=test.description,
                duration_ms=(time.time() - start) * 1000,
            )

        except Exception as e:
            return TestResult(
                name=test.name,
                status=TestStatus.ERROR,
                message=str(e),
                duration_ms=(time.time() - start) * 1000,
            )

    # =========================================================================
    # Test Loading and Running
    # =========================================================================

    def load_test_cases(self, test_dir: Path) -> list[TestCase]:
        """Load MCP client tool test cases (read-only.yaml only)."""
        test_cases = []

        # Only load read-only.yaml - agent tests are in test_agent.py
        for yaml_file in sorted(test_dir.glob("read-only.yaml")):
            self._log(f"Loading {yaml_file.name}")

            with open(yaml_file) as f:
                data = yaml.safe_load(f)

            category = data.get("category", yaml_file.stem)
            tests = data.get("tests", [])

            for test_data in tests:
                test = TestCase(
                    name=test_data.get("name", "unnamed"),
                    description=test_data.get("description", ""),
                    category=category,
                    tool=test_data.get("tool"),
                    command=test_data.get("command"),
                    action=test_data.get("action"),
                    expect=test_data.get("expect", {}),
                )
                test_cases.append(test)

        return test_cases

    async def run_test(self, test: TestCase) -> TestResult:
        """Run a single test case."""
        return await self.run_tool_test(test)

    async def run_all_tests(self, test_dir: Path) -> list[TestResult]:
        """Run all integration tests."""
        print("\n" + "=" * 60)
        print("MCP Client Integration Tests")
        print("=" * 60)
        print(f"Server: {self.config.url}")
        print(f"Transport: {self.config.transport}")
        print("=" * 60)

        # Connect
        print("\n[Connecting]")
        if not await self.connect():
            self.results.append(
                TestResult(
                    name="connection",
                    status=TestStatus.FAILED,
                    message=f"Failed to connect to {self.config.url}",
                )
            )
            self._print_summary()
            return self.results

        print(f"  Connected successfully, found {len(self._tools)} tools")

        try:
            # Load test cases
            test_cases = self.load_test_cases(test_dir)
            print(f"\nLoaded {len(test_cases)} test cases")

            # Filter by category if specified
            if self.config.categories:
                test_cases = [
                    t for t in test_cases if t.category in self.config.categories
                ]
                print(f"Filtered to {len(test_cases)} tests (categories: {self.config.categories})")

            # Group by category
            categories: dict[str, list[TestCase]] = {}
            for test in test_cases:
                if test.category not in categories:
                    categories[test.category] = []
                categories[test.category].append(test)

            # Run tests by category
            for category, tests in categories.items():
                print(f"\n[{category}]")

                for test in tests:
                    result = await self.run_test(test)
                    self.results.append(result)

                    # Print result
                    icon = {
                        TestStatus.PASSED: "\033[32m✓\033[0m",
                        TestStatus.FAILED: "\033[31m✗\033[0m",
                        TestStatus.SKIPPED: "\033[33m○\033[0m",
                        TestStatus.ERROR: "\033[31m!\033[0m",
                    }.get(result.status, "?")

                    print(f"  {icon} {result.name}: {result.message}")

                    if self.config.verbose and result.details:
                        for key, value in result.details.items():
                            print(f"      {key}: {value}")

                    if self.config.fail_fast and result.status in (
                        TestStatus.FAILED,
                        TestStatus.ERROR,
                    ):
                        print("\n  [Stopping due to fail_fast]")
                        break

        finally:
            await self.disconnect()

        self._print_summary()
        return self.results

    def _print_summary(self) -> None:
        """Print test summary."""
        print("\n" + "=" * 60)
        print("Summary")
        print("=" * 60)

        passed = sum(1 for r in self.results if r.status == TestStatus.PASSED)
        failed = sum(1 for r in self.results if r.status == TestStatus.FAILED)
        skipped = sum(1 for r in self.results if r.status == TestStatus.SKIPPED)
        errors = sum(1 for r in self.results if r.status == TestStatus.ERROR)

        total = len(self.results)
        total_time = sum(r.duration_ms for r in self.results)

        print(f"  Passed:  {passed}/{total}")
        print(f"  Failed:  {failed}/{total}")
        print(f"  Skipped: {skipped}/{total}")
        print(f"  Errors:  {errors}/{total}")
        print(f"  Time:    {total_time:.0f}ms")

        if failed > 0 or errors > 0:
            print("\n  \033[31mStatus: FAILED\033[0m")
            print("\n  Failed tests:")
            for r in self.results:
                if r.status in (TestStatus.FAILED, TestStatus.ERROR):
                    print(f"    - {r.name}: {r.message}")
        else:
            print("\n  \033[32mStatus: PASSED\033[0m")


def list_tests(test_dir: Path) -> None:
    """List available tests."""
    print("Available MCP client tool tests:")
    print("-" * 40)

    # Only list read-only.yaml - agent tests are in test_agent.py
    for yaml_file in sorted(test_dir.glob("read-only.yaml")):
        with open(yaml_file) as f:
            data = yaml.safe_load(f)

        category = data.get("category", yaml_file.stem)
        description = data.get("description", "")
        tests = data.get("tests", [])

        print(f"\n[{category}] {description}")
        for test in tests:
            print(f"  - {test.get('name')}: {test.get('description', '')}")


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="MCP Client Layer Validation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "--url",
        type=str,
        help="Server URL (overrides config)",
    )
    parser.add_argument(
        "--transport",
        choices=["http", "stdio"],
        default="http",
        help="Transport protocol",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path(__file__).parent / "config.yaml",
        help="Path to config file",
    )
    parser.add_argument(
        "--category",
        action="append",
        dest="categories",
        help="Test category to run (can be repeated)",
    )
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Stop on first failure",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available tests",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Verbose output",
    )

    return parser.parse_args()


async def main() -> int:
    """Main entry point."""
    args = parse_args()

    # Determine test directory (use validation test-cases for MCP tests)
    test_dir = Path(__file__).parent.parent / "validation" / "test-cases"

    # List tests if requested
    if args.list:
        list_tests(test_dir)
        return 0

    # Load config
    if args.config.exists():
        config = ValidationConfig.from_yaml(args.config)
    else:
        config = ValidationConfig()

    # Apply CLI overrides
    if args.url:
        config.url = args.url
    if args.transport:
        config.transport = args.transport
    if args.verbose:
        config.verbose = True
    if args.fail_fast:
        config.fail_fast = True
    if args.categories:
        config.categories = args.categories

    # Run validation
    client = MCPValidationClient(config)
    results = await client.run_all_tests(test_dir)

    # Exit code based on results
    failed = sum(
        1 for r in results if r.status in (TestStatus.FAILED, TestStatus.ERROR)
    )
    return 1 if failed > 0 else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
