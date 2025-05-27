#!/usr/bin/env python3
"""
Enhanced Contextual Benchmark with Contextually-Aware Judge
Tests granite3.3:2b and gemma3:1b with all prompt variants.
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from contextuals.benchmarks.model_benchmark import ModelBenchmark


async def main():
    """Run the enhanced benchmark with contextually-aware judge."""
    print("🚀 ENHANCED CONTEXTUAL BENCHMARK")
    print("=" * 80)
    print("Features:")
    print("- Contextually-aware LLM-as-a-judge (reference implementation)")
    print("- Judge uses same contextual data as test models")
    print("- Detailed guidance on proper contextual usage")
    print("- Testing 8 models: SLM (granite3.3:2b, cogito:3b, gemma3:1b)")
    print("  MLM (granite3.3:8b, cogito:8b, gemma3:12b)")
    print("  LLM (qwen3:30b-a3b-q4_K_M, llama4:17b-scout-16e-instruct-q4_K_M)")
    print("- All prompt variants: DEFAULT, STRUCTURED, COMPACT")
    print("- News integration with full URLs")
    print("=" * 80)
    
    benchmark = ModelBenchmark()
    
    # Test all requested models across SLM, MLM, and LLM categories
    test_models = [
        # Small Language Models (SLM)
        "granite3.3:2b",
        "cogito:3b", 
        "gemma3:1b",
        # Medium Language Models (MLM)
        "granite3.3:8b",
        "cogito:8b",
        "gemma3:12b",
        # Large Language Models (LLM)
        "qwen3:30b-a3b-q4_K_M",
        "llama4:17b-scout-16e-instruct-q4_K_M"
    ]
    
    try:
        results, evaluations = await benchmark.run_benchmark(test_models)
        
        print(f"\n🎉 BENCHMARK COMPLETED!")
        print(f"Tested {len(results)} model-prompt combinations")
        print(f"Evaluated {len(evaluations)} question sets")
        print("\nResults saved to:")
        print("- Individual results: tests/benchmarks/*.results")
        print("- Comprehensive results: tests/benchmarks/comprehensive_results.json")
        
        # Show quick summary
        if results:
            print(f"\n📊 QUICK SUMMARY:")
            for result in results:
                print(f"- {result.model_name} ({result.prompt_variant}): {result.avg_tokens_per_second:.1f} tok/s, thinking: {result.has_thinking}")
        
    except Exception as e:
        print(f"❌ Benchmark failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 