#!/usr/bin/env python3
"""
Comprehensive analysis of benchmark results.
Processes the comprehensive_results.json file and generates detailed metrics.
"""

import json
import statistics
from pathlib import Path
from typing import Dict, List, Tuple, Any

def load_results() -> Tuple[List[Dict], Dict[str, Any]]:
    """Load comprehensive results from JSON file."""
    results_file = Path("tests/benchmarks/comprehensive_results.json")
    with open(results_file, 'r') as f:
        data = json.load(f)
    return data["benchmark_results"], data["judge_evaluation"]

def calculate_average_scores(judge_eval: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
    """Calculate average scores across all questions and perspectives for each model-prompt combination."""
    model_scores = {}
    
    # Process each question
    for question, responses in judge_eval.items():
        if not responses or question in ["Q2", "Q4", "Q5", "Q9"]:  # Skip empty questions
            continue
            
        for model_prompt, scores in responses.items():
            if isinstance(scores, list) and len(scores) == 3:  # Valid 3-perspective scores
                if model_prompt not in model_scores:
                    model_scores[model_prompt] = {
                        "contextual_scores": [],
                        "accuracy_scores": [],
                        "utility_scores": [],
                        "question_count": 0
                    }
                
                model_scores[model_prompt]["contextual_scores"].append(scores[0])
                model_scores[model_prompt]["accuracy_scores"].append(scores[1])
                model_scores[model_prompt]["utility_scores"].append(scores[2])
                model_scores[model_prompt]["question_count"] += 1
    
    # Calculate averages
    final_scores = {}
    for model_prompt, data in model_scores.items():
        if data["question_count"] > 0:
            final_scores[model_prompt] = {
                "avg_contextual": round(statistics.mean(data["contextual_scores"]), 2),
                "avg_accuracy": round(statistics.mean(data["accuracy_scores"]), 2),
                "avg_utility": round(statistics.mean(data["utility_scores"]), 2),
                "overall_avg": round(statistics.mean(
                    data["contextual_scores"] + data["accuracy_scores"] + data["utility_scores"]
                ), 2),
                "question_count": data["question_count"]
            }
    
    return final_scores

def analyze_prompt_performance(scores: Dict[str, Dict[str, float]], 
                             performance: List[Dict]) -> Dict[str, Any]:
    """Analyze which prompt variant performs best across different metrics."""
    
    # Group by prompt variant
    prompt_analysis = {
        "DEFAULT": {"models": [], "scores": [], "performance": []},
        "STRUCTURED": {"models": [], "scores": [], "performance": []},
        "COMPACT": {"models": [], "scores": [], "performance": []}
    }
    
    # Collect data by prompt variant
    for model_prompt, score_data in scores.items():
        for variant in ["DEFAULT", "STRUCTURED", "COMPACT"]:
            if variant in model_prompt:
                model_name = model_prompt.replace(f"_{variant}", "")
                prompt_analysis[variant]["models"].append(model_name)
                prompt_analysis[variant]["scores"].append(score_data)
                
                # Find corresponding performance data
                perf_data = next((p for p in performance if 
                                p["model_name"] == model_name and 
                                p["prompt_variant"] == variant), None)
                if perf_data:
                    prompt_analysis[variant]["performance"].append(perf_data)
                break
    
    # Calculate averages for each prompt variant
    variant_summary = {}
    for variant, data in prompt_analysis.items():
        if data["scores"]:
            variant_summary[variant] = {
                "avg_contextual": round(statistics.mean([s["avg_contextual"] for s in data["scores"]]), 2),
                "avg_accuracy": round(statistics.mean([s["avg_accuracy"] for s in data["scores"]]), 2),
                "avg_utility": round(statistics.mean([s["avg_utility"] for s in data["scores"]]), 2),
                "avg_overall": round(statistics.mean([s["overall_avg"] for s in data["scores"]]), 2),
                "avg_tokens_per_sec": round(statistics.mean([p["avg_tokens_per_second"] for p in data["performance"]]), 2),
                "avg_total_time": round(statistics.mean([p["total_time"] for p in data["performance"]]), 2),
                "model_count": len(data["models"])
            }
    
    return variant_summary

def analyze_model_categories(scores: Dict[str, Dict[str, float]], 
                           performance: List[Dict]) -> Dict[str, Any]:
    """Analyze performance by model category (SLM, MLM, LLM)."""
    
    categories = {
        "SLM": ["granite3.3:2b", "cogito:3b", "gemma3:1b"],
        "MLM": ["granite3.3:8b", "cogito:8b", "gemma3:12b"]
    }
    
    category_analysis = {}
    
    for category, models in categories.items():
        category_data = {"scores": [], "performance": []}
        
        for model in models:
            # Collect all prompt variants for this model
            for variant in ["DEFAULT", "STRUCTURED", "COMPACT"]:
                model_prompt = f"{model}_{variant}"
                if model_prompt in scores:
                    category_data["scores"].append(scores[model_prompt])
                    
                    perf_data = next((p for p in performance if 
                                    p["model_name"] == model and 
                                    p["prompt_variant"] == variant), None)
                    if perf_data:
                        category_data["performance"].append(perf_data)
        
        if category_data["scores"]:
            category_analysis[category] = {
                "avg_contextual": round(statistics.mean([s["avg_contextual"] for s in category_data["scores"]]), 2),
                "avg_accuracy": round(statistics.mean([s["avg_accuracy"] for s in category_data["scores"]]), 2),
                "avg_utility": round(statistics.mean([s["avg_utility"] for s in category_data["scores"]]), 2),
                "avg_overall": round(statistics.mean([s["overall_avg"] for s in category_data["scores"]]), 2),
                "avg_tokens_per_sec": round(statistics.mean([p["avg_tokens_per_second"] for p in category_data["performance"]]), 2),
                "avg_total_time": round(statistics.mean([p["total_time"] for p in category_data["performance"]]), 2),
                "data_points": len(category_data["scores"])
            }
    
    return category_analysis

def find_best_performers(scores: Dict[str, Dict[str, float]], 
                        performance: List[Dict]) -> Dict[str, Any]:
    """Find best performing model-prompt combinations across different metrics."""
    
    best_performers = {
        "highest_contextual": max(scores.items(), key=lambda x: x[1]["avg_contextual"]),
        "highest_accuracy": max(scores.items(), key=lambda x: x[1]["avg_accuracy"]),
        "highest_utility": max(scores.items(), key=lambda x: x[1]["avg_utility"]),
        "highest_overall": max(scores.items(), key=lambda x: x[1]["overall_avg"]),
        "fastest_tokens": max(performance, key=lambda x: x["avg_tokens_per_second"]),
        "fastest_total": min(performance, key=lambda x: x["total_time"])
    }
    
    return best_performers

def generate_insights(variant_summary: Dict[str, Any], 
                     category_analysis: Dict[str, Any],
                     best_performers: Dict[str, Any]) -> List[str]:
    """Generate key insights from the analysis."""
    
    insights = []
    
    # Prompt variant insights
    best_variant_overall = max(variant_summary.items(), key=lambda x: x[1]["avg_overall"])
    best_variant_speed = max(variant_summary.items(), key=lambda x: x[1]["avg_tokens_per_sec"])
    
    insights.append(f"**Best Overall Prompt Variant**: {best_variant_overall[0]} with {best_variant_overall[1]['avg_overall']}/10 average score")
    insights.append(f"**Fastest Prompt Variant**: {best_variant_speed[0]} with {best_variant_speed[1]['avg_tokens_per_sec']} tokens/sec")
    
    # Model category insights
    if "SLM" in category_analysis and "MLM" in category_analysis:
        slm_score = category_analysis["SLM"]["avg_overall"]
        mlm_score = category_analysis["MLM"]["avg_overall"]
        insights.append(f"**Model Size Impact**: MLM models score {mlm_score}/10 vs SLM {slm_score}/10 (+{mlm_score - slm_score:.1f} improvement)")
    
    # Performance insights
    contextual_leader = best_performers["highest_contextual"]
    insights.append(f"**Best Contextual Awareness**: {contextual_leader[0]} with {contextual_leader[1]['avg_contextual']}/10")
    
    # Speed vs quality trade-offs
    speed_leader = best_performers["fastest_tokens"]
    insights.append(f"**Speed Champion**: {speed_leader['model_name']}_{speed_leader['prompt_variant']} at {speed_leader['avg_tokens_per_second']:.1f} tokens/sec")
    
    return insights

def main():
    """Main analysis function."""
    print("COMPREHENSIVE BENCHMARK ANALYSIS")
    print("=" * 80)
    
    # Load data
    performance_data, judge_eval = load_results()
    
    # Calculate scores
    print("Calculating average scores across all questions and perspectives...")
    scores = calculate_average_scores(judge_eval)
    
    # Analyze prompt variants
    print("Analyzing prompt variant performance...")
    variant_summary = analyze_prompt_performance(scores, performance_data)
    
    # Analyze model categories
    print("Analyzing model category performance...")
    category_analysis = analyze_model_categories(scores, performance_data)
    
    # Find best performers
    print("Identifying best performers...")
    best_performers = find_best_performers(scores, performance_data)
    
    # Generate insights
    insights = generate_insights(variant_summary, category_analysis, best_performers)
    
    # Print results
    print("\n" + "=" * 80)
    print("PROMPT VARIANT ANALYSIS")
    print("=" * 80)
    for variant, data in variant_summary.items():
        print(f"\n{variant}:")
        print(f"  Overall Score: {data['avg_overall']}/10")
        print(f"  Contextual: {data['avg_contextual']}/10")
        print(f"  Accuracy: {data['avg_accuracy']}/10") 
        print(f"  Utility: {data['avg_utility']}/10")
        print(f"  Speed: {data['avg_tokens_per_sec']} tokens/sec")
        print(f"  Time: {data['avg_total_time']:.1f}s")
        print(f"  Models tested: {data['model_count']}")
    
    print("\n" + "=" * 80)
    print("MODEL CATEGORY ANALYSIS")
    print("=" * 80)
    for category, data in category_analysis.items():
        print(f"\n{category} (Small/Medium Language Models):")
        print(f"  Overall Score: {data['avg_overall']}/10")
        print(f"  Contextual: {data['avg_contextual']}/10")
        print(f"  Accuracy: {data['avg_accuracy']}/10")
        print(f"  Utility: {data['avg_utility']}/10")
        print(f"  Speed: {data['avg_tokens_per_sec']} tokens/sec")
        print(f"  Time: {data['avg_total_time']:.1f}s")
    
    print("\n" + "=" * 80)
    print("KEY INSIGHTS")
    print("=" * 80)
    for i, insight in enumerate(insights, 1):
        print(f"{i}. {insight}")
    
    print("\n" + "=" * 80)
    print("DETAILED MODEL-PROMPT SCORES")
    print("=" * 80)
    for model_prompt, score_data in sorted(scores.items()):
        print(f"{model_prompt}: {score_data['overall_avg']}/10 "
              f"(C:{score_data['avg_contextual']}, A:{score_data['avg_accuracy']}, U:{score_data['avg_utility']}) "
              f"[{score_data['question_count']} questions]")
    
    # Save analysis results
    analysis_results = {
        "variant_summary": variant_summary,
        "category_analysis": category_analysis,
        "best_performers": {k: v for k, v in best_performers.items() if k not in ["fastest_tokens", "fastest_total"]},
        "insights": insights,
        "detailed_scores": scores
    }
    
    with open("tests/benchmarks/analysis_results.json", "w") as f:
        json.dump(analysis_results, f, indent=2)
    
    print(f"\nAnalysis complete! Results saved to tests/benchmarks/analysis_results.json")

if __name__ == "__main__":
    main() 