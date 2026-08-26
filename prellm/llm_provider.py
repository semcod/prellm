"""LLMProvider — SubLLM-routed abstraction for preprocessing and execution.

Public SubLLM owns provider, model, credential and paid fallback policy. The
old LiteLLM transport remains available only through an explicit environment
opt-in for compatibility.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import warnings
from typing import Any

from nfo.decorators import log_call

from prellm.models import LLMProviderConfig

# Suppress Pydantic serialization warnings from litellm response objects
# (Message/Choices/StreamingChoices field count mismatches during @log_call serialization)
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")

logger = logging.getLogger("prellm.llm_provider")


class LLMProvider:
    """Policy-routed LLM caller with an explicit semantic function.

    Usage:
        provider = LLMProvider(LLMProviderConfig(model="phi3:mini", fallback=["qwen2:1.5b"]))
        result = await provider.complete("Classify this query", system_prompt="You are a classifier.")
    """

    def __init__(self, config: LLMProviderConfig, *, function: str = "preprocess"):
        if function not in {"preprocess", "execute"}:
            raise ValueError("PreLLM route function must be 'preprocess' or 'execute'")
        self.config = config
        self.function = function
        self._budget_tracker = None

    @staticmethod
    def _use_legacy_litellm() -> bool:
        return os.getenv("PRELLM_USE_LEGACY_LITELLM", "").strip().lower() in {
            "1",
            "true",
            "yes",
            "on",
        }

    async def _complete_subllm(self, messages: list[dict[str, str]], **kwargs: Any) -> str:
        try:
            from subllm import complete as subllm_complete
        except (ImportError, AttributeError) as exc:
            raise RuntimeError(
                "subactor-subllm>=1.4.1 with complete() is required for PreLLM"
            ) from exc

        request_id = kwargs.pop("request_id", None)
        if kwargs:
            logger.debug(
                "SubLLM owns request parameters; ignored PreLLM keys: %s",
                ", ".join(sorted(kwargs)),
            )
        response = await asyncio.to_thread(
            subllm_complete,
            "prellm",
            self.function,
            messages,
            timeout_seconds=float(self.config.timeout),
            request_id=request_id,
        )

        budget = self._get_budget()
        if budget and budget.monthly_limit is not None:
            usage = response.usage
            budget.record(
                model=response.model,
                prompt_tokens=int(usage.get("prompt_tokens", 0) or 0),
                completion_tokens=int(usage.get("completion_tokens", 0) or 0),
            )
        logger.debug("SubLLM response from %s/%s", response.provider, response.model)
        return response.content

    def _get_budget(self):
        """Lazy-load budget tracker if configured."""
        if self._budget_tracker is None:
            from prellm.budget import get_budget_tracker
            self._budget_tracker = get_budget_tracker()
        return self._budget_tracker

    @log_call
    async def complete(
        self,
        user_message: str,
        system_prompt: str = "",
        response_format: str | None = None,
        **kwargs: Any,
    ) -> str:
        """Send a completion request through SubLLM by default.

        Args:
            user_message: The user message content.
            system_prompt: Optional system prompt prepended to messages.
            response_format: If "json", hint the model to return JSON.
            **kwargs: Legacy LiteLLM arguments. SubLLM accepts only request_id;
                provider/model parameters are centrally owned.

        Returns:
            The response content string.
        """
        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_message})

        models_to_try = [self.config.model] + [
            m for m in self.config.fallback if m != self.config.model
        ]

        # Budget check before making any calls
        budget = self._get_budget()
        if budget and budget.monthly_limit is not None:
            budget.check(model=models_to_try[0])

        if not self._use_legacy_litellm():
            return await self._complete_subllm(messages, **kwargs)

        import litellm

        last_error: Exception | None = None

        for model in models_to_try:
            for attempt in range(self.config.max_retries):
                try:
                    completion_kwargs: dict[str, Any] = {
                        "model": model,
                        "messages": messages,
                        "max_tokens": self.config.max_tokens,
                        "timeout": self.config.timeout,
                        "temperature": self.config.temperature,
                        **kwargs,
                    }

                    if response_format == "json":
                        completion_kwargs["response_format"] = {"type": "json_object"}

                    resp = await litellm.acompletion(**completion_kwargs)
                    content = resp.choices[0].message.content or ""

                    # Record cost
                    if budget and budget.monthly_limit is not None:
                        budget.record_from_response(resp, model=model)

                    logger.debug(f"LLM response from {model} (attempt {attempt + 1}): {content[:100]}...")
                    return content

                except Exception as e:
                    last_error = e
                    logger.warning(f"Attempt {attempt + 1} with {model} failed: {e}")

        raise RuntimeError(
            f"All models failed after retries. Last error: {last_error}"
        )

    @log_call
    async def complete_json(
        self,
        user_message: str,
        system_prompt: str = "",
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Complete and parse response as JSON.

        Falls back to extracting JSON from the response text if the model
        doesn't return clean JSON.
        """
        raw = await self.complete(
            user_message=user_message,
            system_prompt=system_prompt,
            response_format="json",
            **kwargs,
        )
        return self._parse_json(raw)

    async def complete_structured(
        self,
        user_message: str,
        response_model: type,
        system_prompt: str = "",
        max_retries: int = 2,
        **kwargs: Any,
    ):
        """Complete and return a validated Pydantic model using instructor.

        Requires: pip install prellm[structured]

        Args:
            user_message: The user message content.
            response_model: A Pydantic BaseModel class to validate against.
            system_prompt: Optional system prompt.
            max_retries: Number of instructor retries for validation failures.
            **kwargs: Extra kwargs passed to the LLM call.

        Returns:
            An instance of response_model, validated by instructor.

        Raises:
            ImportError: If instructor is not installed.
        """
        if not self._use_legacy_litellm():
            raw = await self.complete(
                user_message=user_message,
                system_prompt=system_prompt,
                response_format="json",
                **kwargs,
            )
            payload = self._parse_json(raw)
            validator = getattr(response_model, "model_validate", None)
            return validator(payload) if validator else response_model(**payload)

        try:
            import instructor
        except ImportError:
            raise ImportError(
                "instructor is required for structured outputs. "
                "Install with: pip install prellm[structured]"
            )
        import litellm

        client = instructor.from_litellm(litellm.acompletion)

        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_message})

        models_to_try = [self.config.model] + [
            m for m in self.config.fallback if m != self.config.model
        ]

        last_error: Exception | None = None

        for model in models_to_try:
            try:
                result = await client.chat.completions.create(
                    model=model,
                    messages=messages,
                    response_model=response_model,
                    max_retries=max_retries,
                    max_tokens=self.config.max_tokens,
                    temperature=self.config.temperature,
                    **kwargs,
                )
                logger.debug(f"Structured response from {model}: {result}")
                return result

            except Exception as e:
                last_error = e
                logger.warning(f"Structured completion with {model} failed: {e}")

        raise RuntimeError(
            f"All models failed for structured output. Last error: {last_error}"
        )

    @staticmethod
    def _parse_json(text: str) -> dict[str, Any]:
        """Best-effort JSON extraction from LLM output."""
        text = text.strip()

        # Try direct parse
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Try extracting from markdown code block
        if "```" in text:
            for block in text.split("```"):
                block = block.strip()
                if block.startswith("json"):
                    block = block[4:].strip()
                try:
                    return json.loads(block)
                except json.JSONDecodeError:
                    continue

        # Try finding first { ... } or [ ... ]
        for start_char, end_char in [("{", "}"), ("[", "]")]:
            start = text.find(start_char)
            end = text.rfind(end_char)
            if start != -1 and end > start:
                try:
                    return json.loads(text[start:end + 1])
                except json.JSONDecodeError:
                    pass

        logger.warning(f"Could not parse JSON from LLM output: {text[:200]}")
        return {}
