#!/usr/bin/env python3
"""
Test enhanced benchmark with gemma3:1b model.
Tests DEFAULT, STRUCTURED, and COMPACT prompt variants with multi-perspective judge evaluation.
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath('.'))

from benchmark_models import ModelBenchmark

async def main():
    """Test enhanced benchmark with gemma3:1b."""
    print("ENHANCED BENCHMARK TEST - gemma3:1b")
    print("=" * 80)
    print("Testing: DEFAULT, STRUCTURED, and COMPACT prompt variants")
    print("Judge evaluation: 3 perspectives per response")
    print("Model: gemma3:1b")
    print()
    
    benchmark = ModelBenchmark()
    
    # Test with gemma3:1b
    test_models = ["gemma3:1b"]
    
    try:
        print("Starting enhanced benchmark with gemma3:1b...")
        print("This will test all 3 prompt variants with multi-perspective evaluation.")
        print()
        
        results, evaluations = await benchmark.run_benchmark(test_models)
        
        if results:
            print(f"\n{'='*80}")
            print("ENHANCED BENCHMARK COMPLETE")
            print(f"{'='*80}")
            print(f"Tested {len(results)} model-prompt combinations:")
            
            for result in results:
                print(f"- {result.model_name} with {result.prompt_variant} prompt")
                print(f"  Time: {result.total_time:.2f}s, Tokens/sec: {result.avg_tokens_per_second:.2f}")
            
            print(f"\nResults saved to tests/benchmarks/")
            print("Judge evaluation includes 3 perspectives per response:")
            print("1. Contextual Awareness")
            print("2. Accuracy & Relevance") 
            print("3. Practical Utility")
            
            # Show sample evaluation results
            if evaluations:
                print(f"\nSample evaluation (Q1):")
                q1_scores = evaluations.get("Q1", {})
                for model_prompt, scores in q1_scores.items():
                    if isinstance(scores, list) and len(scores) == 3:
                        print(f"  {model_prompt}: [Context:{scores[0]}, Accuracy:{scores[1]}, Utility:{scores[2]}]")
                    else:
                        print(f"  {model_prompt}: {scores}")
        else:
            print("No results obtained. Check:")
            print("1. Ollama is running: ollama serve")
            print("2. gemma3:1b model is available: ollama list")
            print("3. If not available: ollama pull gemma3:1b")
            
    except Exception as e:
        print(f"Enhanced benchmark execution failed: {e}")
        print("\nTroubleshooting:")
        print("1. Ensure Ollama is running: ollama serve")
        print("2. Check model availability: ollama list")
        print("3. Pull model if needed: ollama pull gemma3:1b")

if __name__ == "__main__":
    asyncio.run(main()) 