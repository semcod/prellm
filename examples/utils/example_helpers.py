"""Utility functions for examples to reduce code duplication."""

from __future__ import annotations

import asyncio
from typing import Any


async def run_provider_example(name: str, small_llm: str, large_llm: str, **kwargs: Any) -> None:
    """Run a single provider example with standardized output format.
    
    Args:
        name: Display name for the provider example
        small_llm: Small model identifier
        large_llm: Large model identifier
        **kwargs: Additional arguments passed to preprocess_and_execute
    """
    from prellm import preprocess_and_execute

    print(f"\n{'='*60}")
    print(f"  {name}")
    print(f"  small: {small_llm}")
    print(f"  large: {large_llm}")
    print(f"{'='*60}")

    try:
        result = await preprocess_and_execute(
            query="Explain how to deploy a Python app to Kubernetes",
            small_llm=small_llm,
            large_llm=large_llm,
            strategy="classify",
            **kwargs,
        )
        print(f"  Status: OK")
        print(f"  Model used: {result.model_used}")
        print(f"  Response: {result.content[:150]}...")
    except Exception as e:
        print(f"  Status: SKIPPED ({type(e).__name__}: {e})")


async def run_quick_start_example(
    query: str,
    small_llm: str,
    large_llm: str,
    example_name: str,
    strategy: str | None = None,
    pipeline: str | None = None,
    **kwargs: Any
) -> None:
    """Run a quick start example with standardized output format.
    
    Args:
        query: Query to process
        small_llm: Small model identifier
        large_llm: Large model identifier
        example_name: Display name for the example
        strategy: Optional strategy to use
        pipeline: Optional pipeline to use
        **kwargs: Additional arguments passed to preprocess_and_execute
    """
    from prellm import preprocess_and_execute

    result = await preprocess_and_execute(
        query=query,
        small_llm=small_llm,
        large_llm=large_llm,
        strategy=strategy,
        pipeline=pipeline,
        **kwargs,
    )
    print(f"[{example_name}] {result.content[:100]}...")
    
    # Print additional info if available
    if hasattr(result, 'decomposition') and result.decomposition:
        if hasattr(result.decomposition, 'classification'):
            print(f"  classification: {result.decomposition.classification}")
        if hasattr(result.decomposition, 'composed_prompt'):
            print(f"  composed_prompt: {result.decomposition.composed_prompt[:80]}...")
        if hasattr(result.decomposition, 'missing_fields') and result.decomposition.missing_fields:
            print(f"  missing fields: {result.decomposition.missing_fields}")
