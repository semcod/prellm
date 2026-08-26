from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _legacy_transport_for_existing_tests(monkeypatch: pytest.MonkeyPatch) -> None:
    """Existing unit tests mock LiteLLM explicitly; production does not opt in."""
    monkeypatch.setenv("PRELLM_USE_LEGACY_LITELLM", "1")
