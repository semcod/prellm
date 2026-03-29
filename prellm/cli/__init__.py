"""prellm/cli package — Command-line interface implementation.

This package contains the CLI implementation for prellm, split into
focused submodules by functionality.
"""

# Re-export main entry point for backward compatibility
from prellm.cli.main import app

__all__ = ["app"]
