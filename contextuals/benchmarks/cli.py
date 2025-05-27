#!/usr/bin/env python3
"""
CLI for running Contextuals library benchmarks.
"""

import asyncio
import sys
from .model_benchmark import ModelBenchmark


async def main():
    """Main benchmark execution."""
    benchmark = ModelBenchmark()
    
    # Accept models as command line arguments, default to granite3.3:2b
    if len(sys.argv) > 1:
        test_models = sys.argv[1:]
    else:
        test_models = ["granite3.3:2b"]
    
    print(f"Starting benchmark with models: {', '.join(test_models)}")
    
    try:
        results, evaluations = await benchmark.run_benchmark(test_models)
        
        if results:
            print(f"\n{'='*80}")
            print("BENCHMARK COMPLETE")
            print(f"{'='*80}")
            print(f"Tested {len(results)} model-prompt combinations")
            print("Results saved to tests/benchmarks/")
            if len(test_models) == 1:
                print(f"Single model test complete. Ready to test with more models.")
            else:
                print("Multi-model benchmark complete.")
        else:
            print("No results obtained. Check Ollama connection and model availability.")
            
    except Exception as e:
        print(f"Benchmark execution failed: {e}")


if __name__ == "__main__":
    asyncio.run(main()) 