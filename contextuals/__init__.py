"""Contextuals - A library for contextual information in AI applications."""

__version__ = "0.2.1"

from contextuals.core.contextual import Contextuals

# Optional benchmarks import (requires pydantic-ai)
try:
    from contextuals.benchmarks import ModelBenchmark
    __all__ = ["Contextuals", "ModelBenchmark"]
except ImportError:
    # pydantic-ai not installed, benchmarks not available
    __all__ = ["Contextuals"]

# For backward compatibility
ContextualCC = Contextuals
