"""Benchmarking module for Contextuals library."""

from .model_benchmark import ModelBenchmark
from .analyzer import main as analyze_results

__all__ = ["ModelBenchmark", "analyze_results"]

# CLI entry point
def run_cli():
    """Entry point for the benchmark CLI."""
    from .cli import main
    import asyncio
    asyncio.run(main()) 