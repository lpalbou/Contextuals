"""Contextuals - A library for contextual information in AI applications."""

__version__ = "0.1.0"

from contextuals.core.contextual import Contextuals
from contextuals.benchmarks import ModelBenchmark

__all__ = ["Contextuals", "ModelBenchmark"]

# For backward compatibility
ContextualCC = Contextuals
