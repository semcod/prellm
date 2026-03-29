"""preLLM CLI — small LLM preprocessing before large LLM execution.

This module is a thin wrapper around prellm.cli package for backward compatibility.
All implementation has been moved to the prellm.cli package.
"""

from __future__ import annotations

from prellm.cli.main import app

__all__ = ["app"]

if __name__ == "__main__":
    app()
