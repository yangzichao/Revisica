"""OpenAI API provider — direct API access with function calling support.

Uses the Responses API. OpenAI recommends it for function calling on GPT-6
models, and gpt-6.1-sol only supports tool calling there.
"""

from __future__ import annotations

import json

from ..core_types import AgentSpec, ReviewResult
from .base import BaseProvider
from .provider_config import get_provider_config
from .tools import TOOL_DEFINITIONS, execute_tool

# Used only when the caller did not resolve a model via model_router.
_DEFAULT_MODEL = "gpt-6.1-sol"


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
    """Access GPT models via the OpenAI Responses API (requires API key)."""

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
        codex_reasoning_effort: str | None = None,
    ) -> ReviewResult:
        client = _get_openai_client()
        resolved_model = model or _DEFAULT_MODEL

        create_kwargs: dict[str, object] = {
            "model": resolved_model,
            "input": prompt,
            # Responses are stored server-side by default; manuscripts under
            # review should not be.
            "store": False,
            "timeout": timeout_seconds,
        }
        reasoning = _build_reasoning_param(resolved_model, codex_reasoning_effort)
        if reasoning:
            create_kwargs["reasoning"] = reasoning

        try:
            response = client.responses.create(**create_kwargs)
            output_text = response.output_text
            return ReviewResult(
                provider="openai-api",
                model=resolved_model,
                command=[f"openai.responses.create(model={resolved_model})"],
                returncode=0 if output_text.strip() else 1,
                output=output_text,
                stderr="",
            )
        except Exception as error:
            return ReviewResult(
                provider="openai-api",
                model=resolved_model,
                command=[f"openai.responses.create(model={resolved_model})"],
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
        codex_reasoning_effort: str | None = None,
    ) -> ReviewResult:
        """Run a function-calling agent loop using the OpenAI Responses API."""
        client = _get_openai_client()
        resolved_model = model or _DEFAULT_MODEL

        effective_effort = codex_reasoning_effort or agent_spec.codex_reasoning_effort
        reasoning = _build_reasoning_param(resolved_model, effective_effort)

        system_message = agent_spec.system_prompt

        openai_tools = _build_openai_tools(agent_spec)

        input_items: list[object] = [{"role": "user", "content": task_prompt}]

        max_iterations = 20
        accumulated_text = ""

        try:
            for _ in range(max_iterations):
                create_kwargs: dict[str, object] = {
                    "model": resolved_model,
                    "input": input_items,
                    # See run_prompt: keep manuscripts out of server-side storage.
                    "store": False,
                    "timeout": timeout_seconds,
                }
                if system_message:
                    create_kwargs["instructions"] = system_message
                if openai_tools:
                    create_kwargs["tools"] = openai_tools
                if reasoning:
                    create_kwargs["reasoning"] = reasoning

                response = client.responses.create(**create_kwargs)
                accumulated_text += response.output_text

                function_calls = [
                    output_item for output_item in response.output
                    if output_item.type == "function_call"
                ]
                if not function_calls:
                    break

                # With store=False the API keeps no history, so replay every
                # output item. Reasoning items must come back alongside the
                # function call outputs or the model loses its reasoning.
                input_items.extend(response.output)

                for function_call in function_calls:
                    try:
                        function_args = json.loads(function_call.arguments)
                    except json.JSONDecodeError:
                        function_args = {}
                    result_text = execute_tool(function_call.name, function_args)
                    input_items.append({
                        "type": "function_call_output",
                        "call_id": function_call.call_id,
                        "output": result_text[:50000],
                    })

            return ReviewResult(
                provider="openai-api",
                model=resolved_model,
                command=[f"openai.responses.create(model={resolved_model}, tools={len(openai_tools)})"],
                returncode=0 if accumulated_text.strip() else 1,
                output=accumulated_text,
                stderr="",
            )
        except Exception as error:
            return ReviewResult(
                provider="openai-api",
                model=resolved_model,
                command=[f"openai.responses.create(model={resolved_model})"],
                returncode=1,
                output=accumulated_text,
                stderr=str(error),
            )


def _build_openai_tools(agent_spec: AgentSpec) -> list[dict]:
    """Convert abstract tool definitions to Responses API function tools."""
    requested_tools = set(agent_spec.tools)

    source_tools = TOOL_DEFINITIONS
    if requested_tools:
        source_tools = [
            tool_def for tool_def in TOOL_DEFINITIONS
            if tool_def["name"] in requested_tools
        ]

    return [
        {
            "type": "function",
            "name": tool_def["name"],
            "description": tool_def["description"],
            "parameters": tool_def["input_schema"],
            # Strict mode (the API default) requires every property to be
            # required; our schemas have optional ones (e.g. Glob's `path`).
            "strict": False,
        }
        for tool_def in source_tools
    ]


# Codex accepts: none|minimal|low|medium|high|xhigh. What the API accepts
# depends on the model generation (per OpenAI model docs, 2026-10):
#   gpt-6-*: low|medium|high|xhigh|max (gpt-6-luna also takes none)
#   older reasoning models (o-series, gpt-5): minimal|low|medium|high
_GPT6_EFFORT_MAP = {
    "none": "low",
    "minimal": "low",
    "low": "low",
    "medium": "medium",
    "high": "high",
    "xhigh": "xhigh",
}

_LEGACY_REASONING_EFFORT_MAP = {
    "minimal": "minimal",
    "low": "low",
    "medium": "medium",
    "high": "high",
    "xhigh": "high",
}


def _build_reasoning_param(model: str, codex_effort: str | None) -> dict[str, str] | None:
    """Translate a Codex effort level into the Responses API `reasoning` param.

    Returns None when no effort was requested or the model is not a
    reasoning model (e.g. gpt-4o rejects the parameter).
    """
    if not codex_effort:
        return None
    lowered_model = model.lower()
    if lowered_model.startswith("gpt-6"):
        effort = _GPT6_EFFORT_MAP.get(codex_effort)
    elif lowered_model.startswith(("o1", "o3", "o4", "gpt-5")):
        effort = _LEGACY_REASONING_EFFORT_MAP.get(codex_effort)
    else:
        return None
    return {"effort": effort} if effort else None
