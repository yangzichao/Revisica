"""OpenAI API provider — direct API access with function calling support."""

from __future__ import annotations

import json

from ..core_types import AgentSpec, ReviewResult
from .base import BaseProvider
from .provider_config import get_provider_config
from .tools import TOOL_DEFINITIONS, execute_tool


def _get_openai_client():
    """Lazy import and create OpenAI client."""
    try:
        from openai import OpenAI
    except ImportError:
        raise ImportError(
            "The 'openai' package is required for direct OpenAI API access.\n"
            "Install: pip install openai"
        )

    config = get_provider_config("openai-api")
    api_key = config.get("api_key")
    if not api_key:
        raise RuntimeError(
            "No OpenAI API key configured.\n"
            "Set OPENAI_API_KEY env var or add api_key to ~/.revisica/config.json"
        )
    return OpenAI(api_key=api_key)


class OpenAiApiProvider(BaseProvider):
    """Access GPT models via the OpenAI Chat Completions API (requires API key)."""

    @property
    def name(self) -> str:
        return "openai-api"

    @property
    def display_name(self) -> str:
        return "OpenAI API"

    @property
    def model_family(self) -> str:
        return "gpt"

    def is_available(self) -> bool:
        config = get_provider_config("openai-api")
        return bool(config.get("api_key"))

    def run_prompt(
        self,
        prompt: str,
        model: str | None = None,
        timeout_seconds: int = 120,
    ) -> ReviewResult:
        client = _get_openai_client()
        resolved_model = model or "gpt-4o"

        try:
            response = client.chat.completions.create(
                model=resolved_model,
                messages=[{"role": "user", "content": prompt}],
                timeout=timeout_seconds,
            )
            output_text = response.choices[0].message.content or ""
            return ReviewResult(
                provider="openai-api",
                model=resolved_model,
                command=[f"openai.chat.completions.create(model={resolved_model})"],
                returncode=0 if output_text.strip() else 1,
                output=output_text,
                stderr="",
            )
        except Exception as error:
            return ReviewResult(
                provider="openai-api",
                model=resolved_model,
                command=[f"openai.chat.completions.create(model={resolved_model})"],
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
        """Run a function-calling agent loop using the OpenAI Chat API."""
        client = _get_openai_client()
        resolved_model = model or "gpt-4o"

        system_message = ""
        if agent_spec.claude_agent_def:
            system_message = agent_spec.claude_agent_def.get("instructions", "")

        openai_tools = _build_openai_tools(agent_spec)

        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": task_prompt})

        max_iterations = 20
        accumulated_text = ""

        try:
            for _ in range(max_iterations):
                create_kwargs = {
                    "model": resolved_model,
                    "messages": messages,
                    "timeout": timeout_seconds,
                }
                if openai_tools:
                    create_kwargs["tools"] = openai_tools

                response = client.chat.completions.create(**create_kwargs)
                choice = response.choices[0]

                if choice.message.content:
                    accumulated_text += choice.message.content

                tool_calls = choice.message.tool_calls
                if not tool_calls:
                    break

                # Add assistant message with tool calls
                messages.append(choice.message)

                # Execute each tool call and add results
                for tool_call in tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    result_text = execute_tool(function_name, function_args)
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result_text[:50000],
                    })

            return ReviewResult(
                provider="openai-api",
                model=resolved_model,
                command=[f"openai.chat.completions.create(model={resolved_model}, tools={len(openai_tools)})"],
                returncode=0 if accumulated_text.strip() else 1,
                output=accumulated_text,
                stderr="",
            )
        except Exception as error:
            return ReviewResult(
                provider="openai-api",
                model=resolved_model,
                command=[f"openai.chat.completions.create(model={resolved_model})"],
                returncode=1,
                output=accumulated_text,
                stderr=str(error),
            )


def _build_openai_tools(agent_spec: AgentSpec) -> list[dict]:
    """Convert abstract tool definitions to OpenAI function calling format."""
    requested_tools = set()
    if agent_spec.claude_agent_def:
        requested_tools = set(agent_spec.claude_agent_def.get("tools", []))

    source_tools = TOOL_DEFINITIONS
    if requested_tools:
        source_tools = [
            tool_def for tool_def in TOOL_DEFINITIONS
            if tool_def["name"] in requested_tools
        ]

    return [
        {
            "type": "function",
            "function": {
                "name": tool_def["name"],
                "description": tool_def["description"],
                "parameters": tool_def["input_schema"],
            },
        }
        for tool_def in source_tools
    ]
