"""Anthropic API provider — direct API access with tool-use support."""

from __future__ import annotations

import logging

from ..core_types import AgentSpec, ReviewResult
from .base import BaseProvider
from .provider_config import get_provider_config
from .tools import TOOL_DEFINITIONS, execute_tool

_MAX_TOOL_OUTPUT_CHARS = 50000


def _get_anthropic_client():
    """Lazy import and create Anthropic client."""
    try:
        from anthropic import Anthropic
    except ImportError:
        raise ImportError(
            "The 'anthropic' package is required for direct Anthropic API access.\n"
            "Install: pip install anthropic"
        )

    config = get_provider_config("anthropic-api")
    api_key = config.get("api_key")
    if not api_key:
        raise RuntimeError(
            "No Anthropic API key configured.\n"
            "Set ANTHROPIC_API_KEY env var or add api_key to ~/.revisica/config.json"
        )
    return Anthropic(api_key=api_key)


class AnthropicApiProvider(BaseProvider):
    """Access Claude models via the Anthropic Messages API (requires API key)."""

    @property
    def name(self) -> str:
        return "anthropic-api"

    @property
    def display_name(self) -> str:
        return "Anthropic API"

    @property
    def model_family(self) -> str:
        return "claude"

    def is_available(self) -> bool:
        config = get_provider_config("anthropic-api")
        return bool(config.get("api_key"))

    def run_prompt(
        self,
        prompt: str,
        model: str | None = None,
        timeout_seconds: int = 120,
    ) -> ReviewResult:
        client = _get_anthropic_client()
        resolved_model = model or "claude-sonnet-4-20250514"

        try:
            response = client.messages.create(
                model=resolved_model,
                max_tokens=8192,
                messages=[{"role": "user", "content": prompt}],
                timeout=timeout_seconds,
            )
            output_text = ""
            for block in response.content:
                if block.type == "text":
                    output_text += block.text
            return ReviewResult(
                provider="anthropic-api",
                model=resolved_model,
                command=[f"anthropic.messages.create(model={resolved_model})"],
                returncode=0 if output_text.strip() else 1,
                output=output_text,
                stderr="",
            )
        except Exception as error:
            return ReviewResult(
                provider="anthropic-api",
                model=resolved_model,
                command=[f"anthropic.messages.create(model={resolved_model})"],
                returncode=1,
                output="",
                stderr=str(error),
            )

    def run_agent(
        self,
        task_prompt: str,
        agent_spec: AgentSpec,
        model: str | None = None,
        timeout_seconds: int = 120,
        working_dir: str | None = None,
    ) -> ReviewResult:
        """Run a tool-use agent loop using the Anthropic Messages API.

        Sends the task prompt with tool definitions.  When the model
        requests tool calls, we execute them locally and send results
        back.  Repeats until the model returns a final text response.
        """
        client = _get_anthropic_client()
        resolved_model = model or "claude-sonnet-4-20250514"

        system_prompt = ""
        if agent_spec.claude_agent_def:
            system_prompt = agent_spec.claude_agent_def.get("instructions", "")

        # Build Anthropic tool definitions from our abstract tool list
        anthropic_tools = _build_anthropic_tools(agent_spec)

        messages = [{"role": "user", "content": task_prompt}]
        max_iterations = 20
        accumulated_text = ""

        try:
            for _ in range(max_iterations):
                create_kwargs = {
                    "model": resolved_model,
                    "max_tokens": 8192,
                    "messages": messages,
                    "timeout": timeout_seconds,
                }
                if system_prompt:
                    create_kwargs["system"] = system_prompt
                if anthropic_tools:
                    create_kwargs["tools"] = anthropic_tools

                response = client.messages.create(**create_kwargs)

                # Collect text and tool_use blocks
                tool_use_blocks = []
                for block in response.content:
                    if block.type == "text":
                        accumulated_text += block.text
                    elif block.type == "tool_use":
                        tool_use_blocks.append(block)

                if not tool_use_blocks:
                    # No more tool calls — we're done
                    break

                # Execute tool calls and build tool_result message
                messages.append({"role": "assistant", "content": response.content})
                tool_results = []
                for tool_block in tool_use_blocks:
                    result_text = execute_tool(tool_block.name, tool_block.input)
                    if len(result_text) > _MAX_TOOL_OUTPUT_CHARS:
                        dropped = len(result_text) - _MAX_TOOL_OUTPUT_CHARS
                        logging.getLogger(__name__).warning(
                            "Anthropic tool %s output truncated: kept %d chars, dropped %d",
                            tool_block.name, _MAX_TOOL_OUTPUT_CHARS, dropped,
                        )
                        result_text = (
                            result_text[:_MAX_TOOL_OUTPUT_CHARS]
                            + f"\n[... truncated {dropped} chars; original output was "
                            f"{len(result_text)} chars — request a narrower range or a smaller slice]"
                        )
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_block.id,
                        "content": result_text,
                    })
                messages.append({"role": "user", "content": tool_results})

            return ReviewResult(
                provider="anthropic-api",
                model=resolved_model,
                command=[f"anthropic.messages.create(model={resolved_model}, tools={len(anthropic_tools)})"],
                returncode=0 if accumulated_text.strip() else 1,
                output=accumulated_text,
                stderr="",
            )
        except Exception as error:
            return ReviewResult(
                provider="anthropic-api",
                model=resolved_model,
                command=[f"anthropic.messages.create(model={resolved_model})"],
                returncode=1,
                output=accumulated_text,
                stderr=str(error),
            )


def _build_anthropic_tools(agent_spec: AgentSpec) -> list[dict]:
    """Convert abstract tool names to Anthropic tool definitions."""
    requested_tools = set()
    if agent_spec.claude_agent_def:
        requested_tools = set(agent_spec.claude_agent_def.get("tools", []))

    if not requested_tools:
        # Default: give all tools
        return TOOL_DEFINITIONS

    return [
        tool_def for tool_def in TOOL_DEFINITIONS
        if tool_def["name"] in requested_tools
    ]
