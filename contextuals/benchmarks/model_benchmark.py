#!/usr/bin/env python3
"""
Comprehensive Model Benchmark for Contextual Awareness
Tests multiple models with DEFAULT and STRUCTURED prompts, includes LLM-as-a-judge evaluation.
"""

import sys
import os
import asyncio
import json
import time
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

from contextuals.core.contextual import Contextuals
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider


@dataclass
class BenchmarkQuestion:
    """A benchmark question with expected answer hints."""
    id: int
    question: str
    expected_hints: List[str]
    description: str


@dataclass
class ModelResult:
    """Results from testing a specific model."""
    model_name: str
    prompt_variant: str
    total_time: float
    avg_tokens_per_second: float
    responses: List[Tuple[str, str, float]]  # (question, answer, response_time)
    has_thinking: bool
    thinking_count: int


class ModelBenchmark:
    """Comprehensive benchmark suite for testing multiple models."""
    
    def __init__(self):
        self.contextuals = Contextuals()
        
        # Test questions with expected answer hints for evaluation
        self.questions = [
            BenchmarkQuestion(
                id=1,
                question="What should I wear outside today?",
                expected_hints=["17°", "chilly", "sweater", "light jacket", "temperature"],
                description="Weather-based clothing recommendation"
            ),
            BenchmarkQuestion(
                id=2,
                question="I feel like visiting a cool place today, any suggestions?",
                expected_hints=["Paris", "France", "famous", "place", "location"],
                description="Location-based recommendation"
            ),
            BenchmarkQuestion(
                id=3,
                question="Is it a good time to go for a run right now?",
                expected_hints=["daylight", "not raining", "ok", "yes", "good time"],
                description="Activity timing assessment"
            ),
            BenchmarkQuestion(
                id=4,
                question="What's a good local greeting for a business email I'm writing?",
                expected_hints=["Cher Monsieur", "Cher Madame", "french", "français", "plaisir"],
                description="Cultural and linguistic appropriateness"
            ),
            BenchmarkQuestion(
                id=5,
                question="My computer feels slow. What might be causing this?",
                expected_hints=["memory", "disk", "occupied", "storage", "RAM"],
                description="System performance diagnosis"
            ),
            BenchmarkQuestion(
                id=6,
                question="When would be the best time to schedule a video call with someone in New York?",
                expected_hints=["14:50", "20h50", "time zone", "NY time", "now", "tomorrow"],
                description="Time zone and scheduling awareness"
            ),
            BenchmarkQuestion(
                id=7,
                question="Should I open my windows right now?",
                expected_hints=["open", "window", "cold", "not raining", "no strong wind"],
                description="Environmental decision"
            ),
            BenchmarkQuestion(
                id=8,
                question="What's happening in the world that I should know about?",
                expected_hints=["Fed Chair Powell", "Brent Fire", "Russia", "Ukraine", "news", "power outage", "budget bill"],
                description="Current events awareness"
            ),
            BenchmarkQuestion(
                id=9,
                question="Plan my evening activities based on current conditions.",
                expected_hints=["cold", "colder", "stay inside", "temperature", "evening"],
                description="Multi-factor activity planning"
            ),
            BenchmarkQuestion(
                id=10,
                question="When is the golden hour to take photos?",
                expected_hints=["20:30", "21:00", "sunset", "05:50", "06:50", "sunrise", "golden hour", "photography"],
                description="Photography timing"
            ),
            BenchmarkQuestion(
                id=11,
                question="When was your knowledge cutoff ? How many months was that ?",
                expected_hints=["months", "year", "training", "cutoff", "data"],
                description="Model training awareness"
            )
        ]
        
        # Models to test (organized by category)
        self.models = {
            "SLM": [
                "granite3.3:2b",
                "cogito:3b", 
                "gemma3:1b"
            ],
            "MLM": [
                "granite3.3:8b",
                "cogito:8b",
                "gemma3:12b"
            ],
            "LLM": [
                "cogito:32b",
                "gemma3:27b"
            ],
            "LLM_MoE": [
                "qwen3:30b-a3b-q4_K_M",
                "llama4:17b-scout-16e-instruct-q4_K_M",
                "llama4:maverick"
            ]
        }
        
        # Prompt variants to test
        self.prompt_variants = {
            "DEFAULT": self.contextuals.get_context_prompt,
            "STRUCTURED": self.contextuals.get_context_prompt_structured,
            "COMPACT": self.contextuals.get_context_prompt_compact
        }
        
        # Judge model for evaluation
        self.judge_model = OpenAIModel(
            model_name='qwen3:30b-a3b-q4_K_M',
            provider=OpenAIProvider(base_url='http://localhost:11434/v1')
        )
    
    def count_tokens_approximate(self, text: str) -> int:
        """Approximate token count."""
        return int(len(text.split()) * 1.3)
    
    def detect_thinking(self, response: str) -> Tuple[bool, int]:
        """Detect if the response contains thinking tags."""
        thinking_pattern = r'<think>.*?</think>'
        matches = re.findall(thinking_pattern, response, re.DOTALL | re.IGNORECASE)
        return len(matches) > 0, len(matches)
    
    async def test_model_variant(self, model_name: str, prompt_variant: str) -> ModelResult:
        """Test a specific model with a specific prompt variant."""
        print(f"\n{'='*80}")
        print(f"TESTING: {model_name} with {prompt_variant} prompt")
        print(f"{'='*80}")
        
        try:
            # Get the prompt
            prompt_func = self.prompt_variants[prompt_variant]
            context_prompt = prompt_func()
            
            # Create model and agent
            model = OpenAIModel(
                model_name=model_name,
                provider=OpenAIProvider(base_url='http://localhost:11434/v1')
            )
            
            agent = Agent(model=model, system_prompt=context_prompt)
            
            responses = []
            total_start_time = time.time()
            total_tokens = 0
            has_thinking = False
            thinking_count = 0
            
            for question in self.questions:
                print(f"\nQ{question.id}: {question.question}")
                
                try:
                    start_time = time.time()
                    result = await agent.run(question.question)
                    response_time = time.time() - start_time
                    
                    response = result.data
                    responses.append((question.question, response, response_time))
                    
                    # Count tokens and detect thinking
                    response_tokens = self.count_tokens_approximate(response)
                    total_tokens += response_tokens
                    
                    think_detected, think_count = self.detect_thinking(response)
                    if think_detected:
                        has_thinking = True
                        thinking_count += think_count
                    
                    print(f"Response time: {response_time:.2f}s")
                    print(f"Tokens: {response_tokens}")
                    print(f"Thinking tags: {think_count}")
                    print(f"Response: {response[:150]}...")
                    
                except Exception as e:
                    print(f"Error with Q{question.id}: {e}")
                    responses.append((question.question, f"ERROR: {e}", 0.0))
            
            total_time = time.time() - total_start_time
            avg_tokens_per_second = total_tokens / total_time if total_time > 0 else 0
            
            print(f"\nMODEL SUMMARY:")
            print(f"Total time: {total_time:.2f}s")
            print(f"Average tokens/second: {avg_tokens_per_second:.2f}")
            print(f"Has thinking: {has_thinking}")
            print(f"Total thinking tags: {thinking_count}")
            
            return ModelResult(
                model_name=model_name,
                prompt_variant=prompt_variant,
                total_time=total_time,
                avg_tokens_per_second=avg_tokens_per_second,
                responses=responses,
                has_thinking=has_thinking,
                thinking_count=thinking_count
            )
            
        except Exception as e:
            print(f"Failed to test {model_name}: {e}")
            return ModelResult(
                model_name=model_name,
                prompt_variant=prompt_variant,
                total_time=0.0,
                avg_tokens_per_second=0.0,
                responses=[(q.question, f"ERROR: {e}", 0.0) for q in self.questions],
                has_thinking=False,
                thinking_count=0
            )
    
    def save_model_results(self, result: ModelResult):
        """Save individual model results to file."""
        results_dir = Path("tests/benchmarks")
        results_dir.mkdir(parents=True, exist_ok=True)
        
        filename = f"{result.model_name.replace(':', '_').replace('/', '_')}_{result.prompt_variant}.results"
        filepath = results_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"Model: {result.model_name}\n")
            f.write(f"Prompt Variant: {result.prompt_variant}\n")
            f.write(f"Total Time: {result.total_time:.2f}s\n")
            f.write(f"Avg Tokens/Second: {result.avg_tokens_per_second:.2f}\n")
            f.write(f"Has Thinking: {result.has_thinking}\n")
            f.write(f"Thinking Count: {result.thinking_count}\n")
            f.write(f"{'='*80}\n\n")
            
            for i, (question, answer, response_time) in enumerate(result.responses, 1):
                f.write(f"Q{i}: {question}\n")
                f.write(f"Response Time: {response_time:.2f}s\n")
                f.write(f"Answer: {answer}\n")
                f.write(f"{'-'*80}\n\n")
        
        print(f"Results saved to: {filepath}")
    
    async def evaluate_with_judge(self, all_results: List[ModelResult]) -> Dict[str, Any]:
        """Use LLM-as-a-judge to evaluate all model responses."""
        print(f"\n{'='*80}")
        print("LLM-AS-A-JUDGE EVALUATION")
        print(f"{'='*80}")
        
        judge_agent = Agent(
            model=self.judge_model,
            system_prompt="""You are an expert evaluator of AI model responses. You will evaluate how well different models answer contextual questions from THREE DIFFERENT PERSPECTIVES.

For each question, you will receive:
1. The question
2. Expected answer hints
3. Multiple model responses

Evaluate each response from these 3 perspectives (scale 0-10):
1. CONTEXTUAL AWARENESS: How well does the response use provided environmental context (time, weather, location, etc.)?
2. ACCURACY & RELEVANCE: How accurate and relevant is the response to the question and expected hints?
3. PRACTICAL UTILITY: How useful and actionable is the response for the user?

Return your evaluation as a JSON object with arrays of 3 scores for each model.
Format: {"model_name_prompt": [contextual_score, accuracy_score, utility_score], ...}

Be critical and consider different angles. The same response might score differently on each dimension."""
        )
        
        evaluation_results = {}
        
        for question in self.questions:
            print(f"\nEvaluating Q{question.id}: {question.question}")
            
            # Prepare evaluation prompt
            eval_prompt = f"""
Question {question.id}: {question.question}
Description: {question.description}
Expected answer hints: {', '.join(question.expected_hints)}

Model Responses:
"""
            
            model_responses = {}
            for result in all_results:
                if question.id <= len(result.responses):
                    _, answer, _ = result.responses[question.id - 1]
                    model_key = f"{result.model_name}_{result.prompt_variant}"
                    model_responses[model_key] = answer
                    eval_prompt += f"\n{model_key}: {answer}\n"
            
            eval_prompt += f"""
Please evaluate each response from 3 perspectives on a scale of 0-10:
1. CONTEXTUAL AWARENESS: Use of environmental context (time, weather, location, etc.)
2. ACCURACY & RELEVANCE: Accuracy and relevance to question and expected hints
3. PRACTICAL UTILITY: Usefulness and actionability for the user

Return a JSON object with arrays of 3 scores for each model.
Format: {{"model_name_prompt": [contextual_score, accuracy_score, utility_score], ...}}
Be critical and consider different angles for each dimension.
"""
            
            try:
                result = await judge_agent.run(eval_prompt)
                response = result.data
                
                # Try to extract JSON from response
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    scores = json.loads(json_match.group())
                    evaluation_results[f"Q{question.id}"] = scores
                    print(f"Scores: {scores}")
                else:
                    print(f"Could not parse JSON from judge response: {response}")
                    evaluation_results[f"Q{question.id}"] = {}
                    
            except Exception as e:
                print(f"Error evaluating Q{question.id}: {e}")
                evaluation_results[f"Q{question.id}"] = {}
        
        return evaluation_results
    
    async def run_benchmark(self, test_models: List[str] = None):
        """Run the complete benchmark."""
        print("CONTEXTUAL AWARENESS MODEL BENCHMARK")
        print("=" * 80)
        print("Testing models with DEFAULT, STRUCTURED, and COMPACT prompts")
        print("Measuring: performance, contextual awareness, thinking capabilities")
        print()
        
        # Use provided models or default to granite3.3:2b for testing
        if test_models is None:
            test_models = ["granite3.3:2b"]
        
        all_results = []
        
        for model_name in test_models:
            for prompt_variant in self.prompt_variants.keys():
                try:
                    result = await self.test_model_variant(model_name, prompt_variant)
                    all_results.append(result)
                    self.save_model_results(result)
                    
                    # Small delay between tests
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    print(f"Error testing {model_name} with {prompt_variant}: {e}")
        
        # Evaluate with judge
        if all_results:
            evaluation_results = await self.evaluate_with_judge(all_results)
            
            # Save comprehensive results
            self.save_comprehensive_results(all_results, evaluation_results)
            
            return all_results, evaluation_results
        
        return [], {}

    def load_existing_results(self) -> Tuple[List[Dict], Dict[str, Any]]:
        """Load existing comprehensive results if they exist."""
        results_file = Path("tests/benchmarks/comprehensive_results.json")
        if results_file.exists():
            try:
                with open(results_file, 'r') as f:
                    data = json.load(f)
                    return data.get("benchmark_results", []), data.get("judge_evaluation", {})
            except Exception as e:
                print(f"Warning: Could not load existing results: {e}")
        return [], {}
    
    def save_comprehensive_results(self, new_results: List[ModelResult], new_evaluations: Dict[str, Any]):
        """Save comprehensive results, merging with existing ones."""
        # Load existing results
        existing_results, existing_evaluations = self.load_existing_results()
        
        # Convert new results to dict format
        new_results_dict = [
            {
                "model_name": r.model_name,
                "prompt_variant": r.prompt_variant,
                "total_time": r.total_time,
                "avg_tokens_per_second": r.avg_tokens_per_second,
                "has_thinking": r.has_thinking,
                "thinking_count": r.thinking_count
            }
            for r in new_results
        ]
        
        # Merge results (avoid duplicates)
        all_results = existing_results.copy()
        for new_result in new_results_dict:
            # Check if this model-prompt combination already exists
            exists = any(
                r["model_name"] == new_result["model_name"] and 
                r["prompt_variant"] == new_result["prompt_variant"]
                for r in all_results
            )
            if not exists:
                all_results.append(new_result)
        
        # Merge evaluations
        all_evaluations = existing_evaluations.copy()
        all_evaluations.update(new_evaluations)
        
        # Save merged results
        comprehensive_results = {
            "benchmark_results": all_results,
            "judge_evaluation": all_evaluations
        }
        
        with open("tests/benchmarks/comprehensive_results.json", "w") as f:
            json.dump(comprehensive_results, f, indent=2)
        
        print(f"Comprehensive results updated: {len(all_results)} total model-prompt combinations")


 