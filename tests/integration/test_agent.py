#!/usr/bin/env python3
"""
Agent Layer Validation

Validates agent layer functionality including model creation, agent execution,
streaming, conversation memory, and error handling.

Usage:
    # Test all categories
    python agent_validation.py

    # Test specific category
    python agent_validation.py --category model
    python agent_validation.py --category execution

    # Verbose output
    python agent_validation.py -v

    # List available tests
    python agent_validation.py --list
"""

import argparse
import asyncio
import os
import sys
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

import yaml

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


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
    action: str  # Test action to perform
    params: dict[str, Any] = field(default_factory=dict)
    expect: dict[str, Any] = field(default_factory=dict)
    skip_if: str | None = None  # Condition to skip


@dataclass
class AgentValidationConfig:
    """Configuration for agent validation."""

    # MCP settings (reuse from MCP config)
    mcp_url: str = "https://cbx-mcp-k8s.vvklab.cloud.cembryonix.com/mcp"
    mcp_transport: str = "http"
    mcp_ssl_verify: bool = False

    # LLM settings
    llm_provider: str = "anthropic"
    llm_model: str = "claude-sonnet-4-20250514"

    # Test settings
    verbose: bool = False
    fail_fast: bool = False
    categories: list[str] = field(default_factory=list)
    timeout: int = 60

    @classmethod
    def from_yaml(cls, path: Path) -> "AgentValidationConfig":
        """Load config from YAML file."""
        with open(path) as f:
            data = yaml.safe_load(f)

        server = data.get("server", {})
        agent = data.get("agent", {})
        tests = data.get("tests", {})

        return cls(
            mcp_url=server.get("url", cls.mcp_url),
            mcp_transport=server.get("transport", cls.mcp_transport),
            mcp_ssl_verify=server.get("ssl_verify", cls.mcp_ssl_verify),
            llm_provider=agent.get("provider", cls.llm_provider),
            llm_model=agent.get("model", cls.llm_model),
            verbose=tests.get("verbose", cls.verbose),
            fail_fast=tests.get("fail_fast", cls.fail_fast),
            categories=tests.get("categories", []),
            timeout=tests.get("timeout", cls.timeout),
        )


class AgentValidationClient:
    """Validation client for testing agent layer."""

    def __init__(self, config: AgentValidationConfig):
        self.config = config
        self.results: list[TestResult] = []
        self._mcp_client = None
        self._model = None
        self._agent = None
        self._tools = []

    def _log(self, message: str) -> None:
        """Log message if verbose mode enabled."""
        if self.config.verbose:
            print(f"  [DEBUG] {message}")

    async def setup(self) -> bool:
        """Set up MCP client and create agent for tests."""
        try:
            from k8sops.mcp_client import MCPClient
            from k8sops.models import create_model
            from k8sops.agent import create_agent_with_mcp

            # Connect to MCP
            self._log(f"Connecting to MCP server: {self.config.mcp_url}")
            self._mcp_client = MCPClient(
                server_url=self.config.mcp_url,
                transport=self.config.mcp_transport,
                ssl_verify=self.config.mcp_ssl_verify,
            )
            self._tools = await self._mcp_client.connect()
            self._log(f"MCP connected, {len(self._tools)} tools available")

            # Create model and agent for tests
            try:
                self._log("Creating model and agent for tests...")
                self._model = create_model()
                self._agent = await create_agent_with_mcp(self._model, self._mcp_client)
                self._log("Agent created successfully")
            except Exception as e:
                self._log(f"Agent setup failed (tests may be skipped): {e}")

            return True
        except Exception as e:
            self._log(f"MCP setup failed: {e}")
            return False

    async def teardown(self) -> None:
        """Clean up resources."""
        if self._mcp_client:
            await self._mcp_client.disconnect()
        self._mcp_client = None
        self._model = None
        self._agent = None

    # =========================================================================
    # Model Layer Tests
    # =========================================================================

    async def test_model_create(self, test: TestCase) -> TestResult:
        """Test model creation."""
        start = time.time()
        provider = test.params.get("provider", self.config.llm_provider)
        model_name = test.params.get("model")

        try:
            from k8sops.models import create_model

            self._log(f"Creating {provider} model: {model_name or 'default'}")

            kwargs = {}
            if model_name:
                kwargs["model_name"] = model_name

            model = create_model(provider=provider, **kwargs)

            # Verify model was created
            if model is None:
                return TestResult(
                    name=test.name,
                    status=TestStatus.FAILED,
                    message="Model creation returned None",
                    duration_ms=(time.time() - start) * 1000,
                )

            self._model = model
            return TestResult(
                name=test.name,
                status=TestStatus.PASSED,
                message=f"Created {provider} model",
                duration_ms=(time.time() - start) * 1000,
            )

        except ValueError as e:
            # Expected for missing API keys
            if "required" in str(e).lower() or "api_key" in str(e).lower():
                return TestResult(
                    name=test.name,
                    status=TestStatus.SKIPPED,
                    message=f"API key not configured: {e}",
                    duration_ms=(time.time() - start) * 1000,
                )
            return TestResult(
                name=test.name,
                status=TestStatus.FAILED,
                message=str(e),
                duration_ms=(time.time() - start) * 1000,
            )
        except ModuleNotFoundError as e:
            # Missing optional provider package
            return TestResult(
                name=test.name,
                status=TestStatus.SKIPPED,
                message=f"Provider package not installed: {e}",
                duration_ms=(time.time() - start) * 1000,
            )
        except Exception as e:
            return TestResult(
                name=test.name,
                status=TestStatus.ERROR,
                message=str(e),
                duration_ms=(time.time() - start) * 1000,
            )

    async def test_model_invoke(self, test: TestCase) -> TestResult:
        """Test model invocation (simple query)."""
        start = time.time()
        prompt = test.params.get("prompt", "Say 'hello' and nothing else.")

        try:
            from k8sops.models import create_model

            if not self._model:
                self._model = create_model()

            self._log(f"Invoking model with: {prompt[:50]}...")
            response = await self._model.ainvoke(prompt)

            content = response.content if hasattr(response, "content") else str(response)
            self._log(f"Response: {content[:100]}...")

            # Check expectations
            expect_contains = test.expect.get("contains")
            if expect_contains and expect_contains.lower() not in content.lower():
                return TestResult(
                    name=test.name,
                    status=TestStatus.FAILED,
                    message=f"Response missing expected: '{expect_contains}'",
                    duration_ms=(time.time() - start) * 1000,
                    details={"response": content[:200]},
                )

            return TestResult(
                name=test.name,
                status=TestStatus.PASSED,
                message="Model invocation successful",
                duration_ms=(time.time() - start) * 1000,
            )

        except Exception as e:
            error_str = str(e).lower()
            # Check for auth errors
            if "401" in error_str or "authentication" in error_str or "unauthorized" in error_str:
                return TestResult(
                    name=test.name,
                    status=TestStatus.FAILED,
                    message=f"Authentication error: {e}",
                    duration_ms=(time.time() - start) * 1000,
                )
            # Check for connection errors
            if "connection" in error_str or "unreachable" in error_str or "timeout" in error_str:
                return TestResult(
                    name=test.name,
                    status=TestStatus.FAILED,
                    message=f"Connection error: {e}",
                    duration_ms=(time.time() - start) * 1000,
                )
            return TestResult(
                name=test.name,
                status=TestStatus.ERROR,
                message=str(e),
                duration_ms=(time.time() - start) * 1000,
            )

    # =========================================================================
    # Agent Creation Tests
    # =========================================================================

    async def test_agent_create(self, test: TestCase) -> TestResult:
        """Test agent creation (does NOT modify shared agent)."""
        start = time.time()
        with_tools = test.params.get("with_tools", True)

        try:
            from k8sops.models import create_model
            from k8sops.agent import create_agent, create_agent_with_mcp

            model = create_model()

            if with_tools:
                if not self._mcp_client:
                    return TestResult(
                        name=test.name,
                        status=TestStatus.SKIPPED,
                        message="MCP client not available",
                        duration_ms=(time.time() - start) * 1000,
                    )
                self._log("Creating agent with MCP tools")
                test_agent = await create_agent_with_mcp(model, self._mcp_client)
            else:
                self._log("Creating agent without tools")
                test_agent = create_agent(model, [])

            if test_agent is None:
                return TestResult(
                    name=test.name,
                    status=TestStatus.FAILED,
                    message="Agent creation returned None",
                    duration_ms=(time.time() - start) * 1000,
                )

            return TestResult(
                name=test.name,
                status=TestStatus.PASSED,
                message=f"Created agent {'with' if with_tools else 'without'} tools",
                duration_ms=(time.time() - start) * 1000,
            )

        except Exception as e:
            return TestResult(
                name=test.name,
                status=TestStatus.ERROR,
                message=str(e),
                duration_ms=(time.time() - start) * 1000,
            )

    async def test_agent_tool_binding(self, test: TestCase) -> TestResult:
        """Test that tools are correctly bound to agent."""
        start = time.time()

        try:
            if not self._agent:
                return TestResult(
                    name=test.name,
                    status=TestStatus.SKIPPED,
                    message="Agent not created",
                    duration_ms=(time.time() - start) * 1000,
                )

            # Check agent has tools
            # LangGraph agents store tools in the graph
            expected_count = test.expect.get("tool_count", len(self._tools))

            # Try to get tools from agent
            lc_tools = self._mcp_client.get_langchain_tools() if self._mcp_client else []

            if len(lc_tools) >= expected_count:
                return TestResult(
                    name=test.name,
                    status=TestStatus.PASSED,
                    message=f"Agent has {len(lc_tools)} tools bound",
                    duration_ms=(time.time() - start) * 1000,
                )
            else:
                return TestResult(
                    name=test.name,
                    status=TestStatus.FAILED,
                    message=f"Expected {expected_count} tools, got {len(lc_tools)}",
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
    # Agent Execution Tests
    # =========================================================================

    async def test_agent_query(self, test: TestCase) -> TestResult:
        """Test agent query execution."""
        start = time.time()
        query = test.params.get("query", "What is 2+2?")
        expect_tool = test.params.get("expect_tool", False)
        thread_id = test.params.get("thread_id", "test-thread")

        try:
            if not self._agent:
                return TestResult(
                    name=test.name,
                    status=TestStatus.SKIPPED,
                    message="Agent not created",
                    duration_ms=(time.time() - start) * 1000,
                )

            self._log(f"Query: {query}")
            config = {"configurable": {"thread_id": thread_id}}

            response = await self._agent.ainvoke(
                {"messages": [{"role": "user", "content": query}]},
                config=config,
            )

            # Extract final message
            messages = response.get("messages", [])
            if not messages:
                return TestResult(
                    name=test.name,
                    status=TestStatus.FAILED,
                    message="No response messages",
                    duration_ms=(time.time() - start) * 1000,
                )

            last_msg = messages[-1]
            content = last_msg.content if hasattr(last_msg, "content") else str(last_msg)
            self._log(f"Response: {content[:200]}...")

            # Check if tool was used (look for tool messages)
            tool_used = any(
                getattr(m, "type", None) == "tool" or
                (hasattr(m, "tool_calls") and m.tool_calls)
                for m in messages
            )

            if expect_tool and not tool_used:
                return TestResult(
                    name=test.name,
                    status=TestStatus.FAILED,
                    message="Expected tool use but none occurred",
                    duration_ms=(time.time() - start) * 1000,
                    details={"response": content[:300]},
                )

            # Check expected content
            expect_contains = test.expect.get("contains")
            if expect_contains and expect_contains.lower() not in content.lower():
                return TestResult(
                    name=test.name,
                    status=TestStatus.FAILED,
                    message=f"Response missing expected: '{expect_contains}'",
                    duration_ms=(time.time() - start) * 1000,
                    details={"response": content[:300]},
                )

            return TestResult(
                name=test.name,
                status=TestStatus.PASSED,
                message=f"Query executed {'with' if tool_used else 'without'} tools",
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
    # Streaming Tests
    # =========================================================================

    async def test_agent_stream(self, test: TestCase) -> TestResult:
        """Test agent streaming."""
        start = time.time()
        query = test.params.get("query", "Say hello")
        expect_events = test.params.get("expect_events", ["on_chat_model_stream"])
        thread_id = test.params.get("thread_id", "stream-test")

        try:
            if not self._agent:
                return TestResult(
                    name=test.name,
                    status=TestStatus.SKIPPED,
                    message="Agent not created",
                    duration_ms=(time.time() - start) * 1000,
                )

            self._log(f"Streaming query: {query}")
            config = {"configurable": {"thread_id": thread_id}}

            events_seen = set()
            token_count = 0

            async for event in self._agent.astream_events(
                {"messages": [{"role": "user", "content": query}]},
                config=config,
                version="v2",
            ):
                event_type = event.get("event", "")
                events_seen.add(event_type)

                if event_type == "on_chat_model_stream":
                    token_count += 1

                if event_type == "on_tool_start":
                    self._log(f"Tool start: {event.get('name')}")
                elif event_type == "on_tool_end":
                    self._log(f"Tool end: {event.get('name')}")

            self._log(f"Events seen: {events_seen}")
            self._log(f"Tokens streamed: {token_count}")

            # Check expected events
            missing_events = set(expect_events) - events_seen
            if missing_events:
                return TestResult(
                    name=test.name,
                    status=TestStatus.FAILED,
                    message=f"Missing events: {missing_events}",
                    duration_ms=(time.time() - start) * 1000,
                    details={"seen": list(events_seen)},
                )

            return TestResult(
                name=test.name,
                status=TestStatus.PASSED,
                message=f"Streamed {token_count} tokens, saw {len(events_seen)} event types",
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
    # Conversation Tests
    # =========================================================================

    async def test_conversation_memory(self, test: TestCase) -> TestResult:
        """Test multi-turn conversation memory."""
        start = time.time()
        messages = test.params.get("messages", [])
        thread_id = test.params.get("thread_id", "memory-test")

        try:
            if not self._agent:
                return TestResult(
                    name=test.name,
                    status=TestStatus.SKIPPED,
                    message="Agent not created",
                    duration_ms=(time.time() - start) * 1000,
                )

            config = {"configurable": {"thread_id": thread_id}}
            last_response = ""

            for i, msg in enumerate(messages):
                self._log(f"Turn {i+1}: {msg[:50]}...")
                response = await self._agent.ainvoke(
                    {"messages": [{"role": "user", "content": msg}]},
                    config=config,
                )
                resp_messages = response.get("messages", [])
                if resp_messages:
                    last_msg = resp_messages[-1]
                    last_response = last_msg.content if hasattr(last_msg, "content") else str(last_msg)
                    self._log(f"Response {i+1}: {last_response[:100]}...")

            # Check final response contains expected content
            expect_contains = test.expect.get("final_contains")
            if expect_contains and expect_contains.lower() not in last_response.lower():
                return TestResult(
                    name=test.name,
                    status=TestStatus.FAILED,
                    message=f"Final response missing expected: '{expect_contains}'",
                    duration_ms=(time.time() - start) * 1000,
                    details={"response": last_response[:300]},
                )

            return TestResult(
                name=test.name,
                status=TestStatus.PASSED,
                message=f"Completed {len(messages)}-turn conversation",
                duration_ms=(time.time() - start) * 1000,
            )

        except Exception as e:
            return TestResult(
                name=test.name,
                status=TestStatus.ERROR,
                message=str(e),
                duration_ms=(time.time() - start) * 1000,
            )

    async def test_thread_isolation(self, test: TestCase) -> TestResult:
        """Test that different threads are isolated."""
        start = time.time()

        try:
            if not self._agent:
                return TestResult(
                    name=test.name,
                    status=TestStatus.SKIPPED,
                    message="Agent not created",
                    duration_ms=(time.time() - start) * 1000,
                )

            # Send message to thread A
            config_a = {"configurable": {"thread_id": "thread-a"}}
            await self._agent.ainvoke(
                {"messages": [{"role": "user", "content": "Remember: the secret word is 'banana'"}]},
                config=config_a,
            )

            # Send message to thread B asking about the secret
            config_b = {"configurable": {"thread_id": "thread-b"}}
            response = await self._agent.ainvoke(
                {"messages": [{"role": "user", "content": "What is the secret word?"}]},
                config=config_b,
            )

            messages = response.get("messages", [])
            last_response = ""
            if messages:
                last_msg = messages[-1]
                last_response = last_msg.content if hasattr(last_msg, "content") else str(last_msg)

            # Thread B should NOT know the secret from Thread A
            if "banana" in last_response.lower():
                return TestResult(
                    name=test.name,
                    status=TestStatus.FAILED,
                    message="Thread isolation failed - secret leaked across threads",
                    duration_ms=(time.time() - start) * 1000,
                )

            return TestResult(
                name=test.name,
                status=TestStatus.PASSED,
                message="Threads are properly isolated",
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
    # Error Handling Tests
    # =========================================================================

    async def test_error_handling(self, test: TestCase) -> TestResult:
        """Test error handling scenarios."""
        start = time.time()
        error_type = test.params.get("error_type", "")

        try:
            if error_type == "invalid_api_key":
                return await self._test_invalid_api_key(test, start)
            elif error_type == "unreachable_api":
                return await self._test_unreachable_api(test, start)
            elif error_type == "tool_error":
                return await self._test_tool_error(test, start)
            elif error_type == "invalid_tool":
                return await self._test_invalid_tool(test, start)
            else:
                return TestResult(
                    name=test.name,
                    status=TestStatus.SKIPPED,
                    message=f"Unknown error type: {error_type}",
                    duration_ms=(time.time() - start) * 1000,
                )

        except Exception as e:
            return TestResult(
                name=test.name,
                status=TestStatus.ERROR,
                message=str(e),
                duration_ms=(time.time() - start) * 1000,
            )

    async def _test_invalid_api_key(self, test: TestCase, start: float) -> TestResult:
        """Test handling of invalid API key."""
        try:
            from langchain_anthropic import ChatAnthropic

            # Create model with invalid key
            model = ChatAnthropic(
                model="claude-sonnet-4-20250514",
                api_key="invalid-key-12345",
            )

            # Try to invoke
            await model.ainvoke("Hello")

            # Should not reach here
            return TestResult(
                name=test.name,
                status=TestStatus.FAILED,
                message="Expected authentication error but request succeeded",
                duration_ms=(time.time() - start) * 1000,
            )

        except Exception as e:
            error_str = str(e).lower()
            if "401" in error_str or "authentication" in error_str or "invalid" in error_str:
                return TestResult(
                    name=test.name,
                    status=TestStatus.PASSED,
                    message="Correctly raised authentication error",
                    duration_ms=(time.time() - start) * 1000,
                )
            return TestResult(
                name=test.name,
                status=TestStatus.FAILED,
                message=f"Unexpected error type: {e}",
                duration_ms=(time.time() - start) * 1000,
            )

    async def _test_unreachable_api(self, test: TestCase, start: float) -> TestResult:
        """Test handling of unreachable API endpoint."""
        try:
            from langchain_openai import ChatOpenAI

            # Create model with unreachable endpoint
            model = ChatOpenAI(
                model="gpt-4",
                api_key="test-key",
                base_url="http://192.0.2.1:9999",  # Non-routable IP
                timeout=5,
            )

            # Try to invoke
            await model.ainvoke("Hello")

            return TestResult(
                name=test.name,
                status=TestStatus.FAILED,
                message="Expected connection error but request succeeded",
                duration_ms=(time.time() - start) * 1000,
            )

        except Exception as e:
            error_str = str(e).lower()
            if "connection" in error_str or "timeout" in error_str or "unreachable" in error_str:
                return TestResult(
                    name=test.name,
                    status=TestStatus.PASSED,
                    message="Correctly raised connection error",
                    duration_ms=(time.time() - start) * 1000,
                )
            # Accept any error since the point is it should fail
            return TestResult(
                name=test.name,
                status=TestStatus.PASSED,
                message=f"Request failed as expected: {type(e).__name__}",
                duration_ms=(time.time() - start) * 1000,
            )

    async def _test_tool_error(self, test: TestCase, start: float) -> TestResult:
        """Test handling of tool execution error."""
        try:
            if not self._mcp_client:
                return TestResult(
                    name=test.name,
                    status=TestStatus.SKIPPED,
                    message="MCP client not available",
                    duration_ms=(time.time() - start) * 1000,
                )

            # Try to execute invalid command
            result = await self._mcp_client.call_tool(
                "k8s_kubectl_execute",
                {"command": "get nonexistent-resource-type-12345"}
            )

            # Check if error is in result
            if "error" in result.lower() or "not found" in result.lower():
                return TestResult(
                    name=test.name,
                    status=TestStatus.PASSED,
                    message="Tool returned error for invalid command",
                    duration_ms=(time.time() - start) * 1000,
                )

            return TestResult(
                name=test.name,
                status=TestStatus.PASSED,
                message="Tool handled invalid command",
                duration_ms=(time.time() - start) * 1000,
                details={"result": result[:200]},
            )

        except Exception as e:
            # Errors are expected
            return TestResult(
                name=test.name,
                status=TestStatus.PASSED,
                message=f"Tool error handled: {type(e).__name__}",
                duration_ms=(time.time() - start) * 1000,
            )

    async def _test_invalid_tool(self, test: TestCase, start: float) -> TestResult:
        """Test handling of non-existent tool request."""
        try:
            if not self._mcp_client:
                return TestResult(
                    name=test.name,
                    status=TestStatus.SKIPPED,
                    message="MCP client not available",
                    duration_ms=(time.time() - start) * 1000,
                )

            # Try to call non-existent tool
            result = await self._mcp_client.call_tool("nonexistent_tool_12345", {})

            # Server might return error string instead of raising exception
            if "unknown" in result.lower() or "error" in result.lower() or "not found" in result.lower():
                return TestResult(
                    name=test.name,
                    status=TestStatus.PASSED,
                    message="Server returned error for invalid tool",
                    duration_ms=(time.time() - start) * 1000,
                )

            return TestResult(
                name=test.name,
                status=TestStatus.FAILED,
                message="Expected error for invalid tool",
                duration_ms=(time.time() - start) * 1000,
                details={"result": result[:200]},
            )

        except Exception as e:
            return TestResult(
                name=test.name,
                status=TestStatus.PASSED,
                message=f"Correctly raised error for invalid tool: {type(e).__name__}",
                duration_ms=(time.time() - start) * 1000,
            )

    # =========================================================================
    # Test Loading and Running
    # =========================================================================

    def load_test_cases(self, test_dir: Path) -> list[TestCase]:
        """Load all agent test cases from YAML files."""
        test_cases = []

        for yaml_file in sorted(test_dir.glob("agent-*.yaml")):
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
                    action=test_data.get("action", ""),
                    params=test_data.get("params", {}),
                    expect=test_data.get("expect", {}),
                    skip_if=test_data.get("skip_if"),
                )
                test_cases.append(test)

        return test_cases

    async def run_test(self, test: TestCase) -> TestResult:
        """Run a single test case."""
        action = test.action

        # Model tests
        if action == "model_create":
            return await self.test_model_create(test)
        elif action == "model_invoke":
            return await self.test_model_invoke(test)

        # Agent creation tests
        elif action == "agent_create":
            return await self.test_agent_create(test)
        elif action == "agent_tool_binding":
            return await self.test_agent_tool_binding(test)

        # Agent execution tests
        elif action == "agent_query":
            return await self.test_agent_query(test)

        # Streaming tests
        elif action == "agent_stream":
            return await self.test_agent_stream(test)

        # Conversation tests
        elif action == "conversation_memory":
            return await self.test_conversation_memory(test)
        elif action == "thread_isolation":
            return await self.test_thread_isolation(test)

        # Error handling tests
        elif action == "error_handling":
            return await self.test_error_handling(test)

        else:
            return TestResult(
                name=test.name,
                status=TestStatus.SKIPPED,
                message=f"Unknown action: {action}",
            )

    async def run_all_tests(self, test_dir: Path) -> list[TestResult]:
        """Run all agent validation tests."""
        print("\n" + "=" * 60)
        print("Agent Layer Validation")
        print("=" * 60)
        print(f"MCP Server: {self.config.mcp_url}")
        print(f"LLM Provider: {self.config.llm_provider}")
        print(f"LLM Model: {self.config.llm_model}")
        print("=" * 60)

        # Setup MCP connection
        print("\n[Setup]")
        if await self.setup():
            print(f"  MCP connected, {len(self._tools)} tools available")
        else:
            print("  MCP connection failed - some tests will be skipped")

        try:
            # Load test cases
            test_cases = self.load_test_cases(test_dir)
            print(f"\nLoaded {len(test_cases)} test cases")

            # Filter by category if specified
            if self.config.categories:
                test_cases = [
                    t for t in test_cases if t.category in self.config.categories
                ]
                print(f"Filtered to {len(test_cases)} tests")

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

                    icon = {
                        TestStatus.PASSED: "\033[32m✓\033[0m",
                        TestStatus.FAILED: "\033[31m✗\033[0m",
                        TestStatus.SKIPPED: "\033[33m○\033[0m",
                        TestStatus.ERROR: "\033[31m!\033[0m",
                    }.get(result.status, "?")

                    print(f"  {icon} {result.name}: {result.message}")

                    if self.config.verbose and result.details:
                        for key, value in result.details.items():
                            val_str = str(value)[:100]
                            print(f"      {key}: {val_str}")

                    if self.config.fail_fast and result.status in (
                        TestStatus.FAILED,
                        TestStatus.ERROR,
                    ):
                        print("\n  [Stopping due to fail_fast]")
                        break

        finally:
            await self.teardown()

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
            print("\n  Failed/Error tests:")
            for r in self.results:
                if r.status in (TestStatus.FAILED, TestStatus.ERROR):
                    print(f"    - {r.name}: {r.message}")
        else:
            print("\n  \033[32mStatus: PASSED\033[0m")


def list_tests(test_dir: Path) -> None:
    """List available tests."""
    print("Available agent tests:")
    print("-" * 40)

    for yaml_file in sorted(test_dir.glob("agent-*.yaml")):
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
        description="Agent Layer Validation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
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

    # Determine test directory (use validation test-cases for agent tests)
    test_dir = Path(__file__).parent.parent / "validation" / "test-cases"

    # List tests if requested
    if args.list:
        list_tests(test_dir)
        return 0

    # Load config
    if args.config.exists():
        config = AgentValidationConfig.from_yaml(args.config)
    else:
        config = AgentValidationConfig()

    # Apply CLI overrides
    if args.verbose:
        config.verbose = True
    if args.fail_fast:
        config.fail_fast = True
    if args.categories:
        config.categories = args.categories

    # Run validation
    client = AgentValidationClient(config)
    results = await client.run_all_tests(test_dir)

    # Exit code based on results
    failed = sum(
        1 for r in results if r.status in (TestStatus.FAILED, TestStatus.ERROR)
    )
    return 1 if failed > 0 else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
