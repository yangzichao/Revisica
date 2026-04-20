"""Abstract base class for LLM providers."""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..core_types import AgentSpec, ReviewResult


class BaseProvider(ABC):
    """Pluggable provider for running prompts and agents.

    Each provider represents a way to access an LLM: CLI subscription,
    direct API key, local model, etc.  The same model family (Claude, GPT)
    may be accessible through multiple providers.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier, e.g. 'claude-cli', 'anthropic-api'."""

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable name, e.g. 'Claude (CLI)', 'Anthropic API'."""

    @property
    @abstractmethod
    def model_family(self) -> str:
        """Which model family: 'claude' or 'gpt'."""

    @abstractmethod
    def is_available(self) -> bool:
        """Can this provider be used right now?

        CLI providers check if the binary is on PATH.
        API providers check if an API key is configured.
        Local providers check if the service is running.
        """

    @abstractmethod
    def run_prompt(
        self,
        prompt: str,
        model: str | None = None,
        timeout_seconds: int = 120,
        codex_reasoning_effort: str | None = None,
    ) -> ReviewResult:
        """Send a prompt and get a response. No tool access.

        ``codex_reasoning_effort`` is a runtime override for Codex's
        ``model_reasoning_effort`` config (none|minimal|low|medium|high|xhigh).
        Providers other than Codex ignore it.
        """

    @abstractmethod
    def run_agent(
        self,
        task_prompt: str,
        agent_spec: AgentSpec,
        model: str | None = None,
        timeout_seconds: int = 120,
        working_dir: str | None = None,
        codex_reasoning_effort: str | None = None,
    ) -> ReviewResult:
        """Run an agent with tool access.

        Providers that don't support agents should fall back to
        :meth:`run_prompt` with the agent's system prompt prepended.

        ``codex_reasoning_effort`` is a runtime override that takes
        precedence over ``agent_spec.codex_reasoning_effort``. Non-Codex
        providers ignore it.
        """
