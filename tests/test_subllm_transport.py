from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from pydantic import BaseModel

from prellm.llm_provider import LLMProvider
from prellm.models import LLMProviderConfig


class StructuredAnswer(BaseModel):
    answer: str


@pytest.mark.asyncio
@pytest.mark.parametrize("function", ("preprocess", "execute"))
async def test_default_transport_uses_registered_subllm_route(
    monkeypatch: pytest.MonkeyPatch,
    function: str,
) -> None:
    monkeypatch.delenv("PRELLM_USE_LEGACY_LITELLM", raising=False)
    response = SimpleNamespace(
        content="policy response",
        provider="zai",
        model="glm-5.3",
        usage={"prompt_tokens": 7, "completion_tokens": 3},
    )
    provider = LLMProvider(LLMProviderConfig(timeout=12), function=function)

    with patch("subllm.complete", return_value=response) as complete:
        result = await provider.complete("route this", system_prompt="Be concise")

    assert result == "policy response"
    complete.assert_called_once_with(
        "prellm",
        function,
        [
            {"role": "system", "content": "Be concise"},
            {"role": "user", "content": "route this"},
        ],
        timeout_seconds=12.0,
        request_id=None,
    )


@pytest.mark.asyncio
async def test_incompatible_subllm_package_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    import subllm

    monkeypatch.delenv("PRELLM_USE_LEGACY_LITELLM", raising=False)
    monkeypatch.delattr(subllm, "complete")
    provider = LLMProvider(LLMProviderConfig())

    with pytest.raises(RuntimeError, match="subactor-subllm>=1.4.1"):
        await provider.complete("do not fall back")


@pytest.mark.asyncio
async def test_structured_completion_uses_subllm_once(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PRELLM_USE_LEGACY_LITELLM", raising=False)
    provider = LLMProvider(LLMProviderConfig(), function="execute")

    with patch.object(provider, "complete", new=AsyncMock(return_value='{"answer":"ok"}')) as complete:
        result = await provider.complete_structured("answer", StructuredAnswer)

    assert result == StructuredAnswer(answer="ok")
    complete.assert_awaited_once_with(
        user_message="answer",
        system_prompt="",
        response_format="json",
    )
