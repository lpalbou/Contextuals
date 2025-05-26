#!/usr/bin/env python3
"""
Run full benchmark with all available models.
"""

import asyncio
from benchmark_models import ModelBenchmark

async def main():
    """Run full benchmark with all available models."""
    benchmark = ModelBenchmark()
    
    # All models to test
    all_models = [
        # SLM
        "granite3.3:2b",
        "cogito:3b", 
        "gemma3:1b",
        # MLM
        "granite3.3:8b",
        "cogito:8b",
        "gemma3:12b",
        # LLM
        "cogito:32b",
        "gemma3:27b",
        # LLM MoE
        "qwen3:30b-a3b-q4_K_M",
        "llama4:17b-scout-16e-instruct-q4_K_M",
        "llama4:maverick"
    ]
    
    print(f"Starting full benchmark with {len(all_models)} models...")
    print("This will take a significant amount of time.")
    print("Models to test:", all_models)
    
    try:
        results, evaluations = await benchmark.run_benchmark(all_models)
        
        if results:
            print(f"\n{'='*80}")
            print("FULL BENCHMARK COMPLETE")
            print(f"{'='*80}")
            print(f"Tested {len(results)} model-prompt combinations")
            print("Results saved to tests/benchmarks/")
        else:
            print("No results obtained. Check Ollama connection and model availability.")
            
    except Exception as e:
        print(f"Full benchmark execution failed: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 