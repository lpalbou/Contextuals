#!/usr/bin/env python3
"""
Objective LLM Test for Contextual Awareness
Tests different prompt variants with Qwen 3 30B via Ollama to determine which provides best contextual awareness.
"""

import sys
import os
import asyncio
import json
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pydantic import BaseModel

sys.path.insert(0, os.path.abspath('.'))

from contextuals import Contextuals
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider


@dataclass
class TestQuestion:
    """A test question with expected contextual elements."""
    question: str
    expected_context_types: List[str]
    context_weight: Dict[str, float]  # How important each context type is (0-1)
    description: str


class ContextualResponse(BaseModel):
    """Structured response from the LLM."""
    answer: str
    confidence: float  # 0-1 scale
    context_used: List[str]  # Which contextual elements were referenced
    reasoning: str


@dataclass
class TestResult:
    """Results from testing a prompt variant."""
    variant_name: str
    prompt_tokens: int
    total_score: float
    individual_scores: List[float]
    response_times: List[float]
    context_coverage: float
    responses: List[str]


class ContextualAwarenessTest:
    """Test suite for evaluating contextual awareness of different prompt variants."""
    
    def __init__(self):
        self.contextuals = Contextuals()
        
        # Initialize Ollama model
        self.model = OpenAIModel(
            model_name='qwen3:30b-a3b-q4_K_M',
            provider=OpenAIProvider(base_url='http://localhost:11434/v1')
        )
        
        # Define test questions that require different types of contextual awareness
        self.test_questions = [
            TestQuestion(
                question="What should I wear outside today?",
                expected_context_types=["weather", "temperature", "location", "time"],
                context_weight={"weather": 0.4, "temperature": 0.3, "location": 0.2, "time": 0.1},
                description="Weather-based clothing recommendation"
            ),
            TestQuestion(
                question="Is it a good time to go for a run right now?",
                expected_context_types=["air_quality", "weather", "time", "astronomy"],
                context_weight={"air_quality": 0.3, "weather": 0.3, "time": 0.2, "astronomy": 0.2},
                description="Health and safety assessment for outdoor activity"
            ),
            TestQuestion(
                question="What's a good local greeting for a business email I'm writing?",
                expected_context_types=["location", "language", "user", "time"],
                context_weight={"location": 0.4, "language": 0.3, "user": 0.2, "time": 0.1},
                description="Cultural and linguistic appropriateness"
            ),
            TestQuestion(
                question="My computer feels slow. What might be causing this?",
                expected_context_types=["machine", "system", "memory", "disk"],
                context_weight={"machine": 0.3, "system": 0.3, "memory": 0.2, "disk": 0.2},
                description="System performance diagnosis"
            ),
            TestQuestion(
                question="When would be the best time to schedule a video call with someone in New York?",
                expected_context_types=["time", "location", "timezone"],
                context_weight={"time": 0.4, "location": 0.3, "timezone": 0.3},
                description="Time zone and scheduling awareness"
            ),
            TestQuestion(
                question="Should I open my windows right now?",
                expected_context_types=["air_quality", "weather", "temperature"],
                context_weight={"air_quality": 0.4, "weather": 0.3, "temperature": 0.3},
                description="Environmental health decision"
            ),
            TestQuestion(
                question="What's happening in the world that I should know about?",
                expected_context_types=["news", "location", "language"],
                context_weight={"news": 0.6, "location": 0.2, "language": 0.2},
                description="Current events awareness"
            ),
            TestQuestion(
                question="Plan my evening activities based on current conditions.",
                expected_context_types=["weather", "time", "astronomy", "location"],
                context_weight={"weather": 0.3, "time": 0.3, "astronomy": 0.2, "location": 0.2},
                description="Multi-factor activity planning"
            ),
            TestQuestion(
                question="How should I adjust my workspace for optimal productivity?",
                expected_context_types=["machine", "system", "user", "time"],
                context_weight={"machine": 0.3, "system": 0.3, "user": 0.2, "time": 0.2},
                description="Personalized productivity optimization"
            ),
            TestQuestion(
                question="What's the best way to commute to work today?",
                expected_context_types=["weather", "location", "time", "air_quality"],
                context_weight={"weather": 0.3, "location": 0.3, "time": 0.2, "air_quality": 0.2},
                description="Transportation decision with multiple factors"
            )
        ]
        
        # Prompt variants to test
        self.prompt_variants = {
            "minimal": self.contextuals.get_context_prompt_minimal,
            "compact": self.contextuals.get_context_prompt_compact,
            "default": self.contextuals.get_context_prompt,
            "structured": self.contextuals.get_context_prompt_structured,
            "detailed": self.contextuals.get_context_prompt_detailed
        }
    
    def count_tokens_approximate(self, text: str) -> int:
        """Approximate token count."""
        return int(len(text.split()) * 1.3)
    
    def score_contextual_awareness(self, response: str, question: TestQuestion) -> float:
        """Score how well the response demonstrates contextual awareness."""
        response_lower = response.lower()
        total_score = 0.0
        
        # Check for each expected context type
        for context_type in question.expected_context_types:
            weight = question.context_weight.get(context_type, 0.25)
            
            # Define keywords for each context type
            keywords = self._get_context_keywords(context_type)
            
            # Check if any keywords are present
            context_found = any(keyword in response_lower for keyword in keywords)
            
            if context_found:
                total_score += weight
        
        return min(total_score, 1.0)  # Cap at 1.0
    
    def _get_context_keywords(self, context_type: str) -> List[str]:
        """Get relevant keywords for each context type."""
        keyword_map = {
            "weather": ["temperature", "°c", "weather", "rain", "sunny", "cloudy", "wind", "humidity"],
            "temperature": ["°c", "temperature", "warm", "cold", "hot", "cool"],
            "location": ["paris", "france", "city", "country", "local", "area"],
            "time": ["time", "hour", "morning", "afternoon", "evening", "now", "current"],
            "air_quality": ["air quality", "aqi", "pollution", "air", "breathe", "health"],
            "astronomy": ["sunrise", "sunset", "sun", "moon", "daylight", "dark"],
            "machine": ["computer", "system", "memory", "ram", "disk", "cpu", "performance"],
            "system": ["macos", "operating system", "platform", "machine"],
            "memory": ["memory", "ram", "gb", "usage"],
            "disk": ["disk", "storage", "space", "gb"],
            "user": ["user", "username", "albou", "laurent", "personal"],
            "language": ["language", "english", "french", "locale"],
            "timezone": ["timezone", "time zone", "utc", "gmt"],
            "news": ["news", "current events", "headlines", "happening"]
        }
        return keyword_map.get(context_type, [context_type])
    
    async def test_variant(self, variant_name: str, prompt_func) -> TestResult:
        """Test a specific prompt variant with all questions."""
        print(f"\n{'='*60}")
        print(f"TESTING VARIANT: {variant_name.upper()}")
        print(f"{'='*60}")
        
        # Get the prompt
        context_prompt = prompt_func()
        prompt_tokens = self.count_tokens_approximate(context_prompt)
        
        print(f"Prompt tokens: {prompt_tokens}")
        print(f"Prompt preview: {context_prompt[:200]}...")
        
        # Create agent with this context
        agent = Agent(
            model=self.model,
            system_prompt=context_prompt
        )
        
        scores = []
        response_times = []
        responses = []
        
        for i, question in enumerate(self.test_questions, 1):
            print(f"\nQuestion {i}: {question.question}")
            
            try:
                start_time = time.time()
                result = await agent.run(question.question)
                response_time = time.time() - start_time
                
                response = result.data
                responses.append(response)
                response_times.append(response_time)
                
                # Score the response
                score = self.score_contextual_awareness(response, question)
                scores.append(score)
                
                print(f"Response time: {response_time:.2f}s")
                print(f"Context score: {score:.2f}")
                print(f"Response: {response[:150]}...")
                
            except Exception as e:
                print(f"Error with question {i}: {e}")
                scores.append(0.0)
                response_times.append(0.0)
                responses.append(f"Error: {e}")
        
        # Calculate overall metrics
        total_score = sum(scores) / len(scores) if scores else 0.0
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0.0
        
        # Calculate context coverage (how many different context types were used)
        all_responses_text = " ".join(responses).lower()
        all_context_types = set()
        for question in self.test_questions:
            all_context_types.update(question.expected_context_types)
        
        covered_contexts = 0
        for context_type in all_context_types:
            keywords = self._get_context_keywords(context_type)
            if any(keyword in all_responses_text for keyword in keywords):
                covered_contexts += 1
        
        context_coverage = covered_contexts / len(all_context_types)
        
        print(f"\nVARIANT SUMMARY:")
        print(f"Average score: {total_score:.3f}")
        print(f"Average response time: {avg_response_time:.2f}s")
        print(f"Context coverage: {context_coverage:.3f}")
        
        return TestResult(
            variant_name=variant_name,
            prompt_tokens=prompt_tokens,
            total_score=total_score,
            individual_scores=scores,
            response_times=response_times,
            context_coverage=context_coverage,
            responses=responses
        )
    
    async def run_all_tests(self) -> Dict[str, TestResult]:
        """Run tests for all prompt variants."""
        print("CONTEXTUAL AWARENESS TEST WITH QWEN 3 30B")
        print("=" * 80)
        print("Testing 5 prompt variants with 10 contextual questions")
        print("Measuring: contextual awareness, response quality, efficiency")
        print()
        
        results = {}
        
        for variant_name, prompt_func in self.prompt_variants.items():
            try:
                result = await self.test_variant(variant_name, prompt_func)
                results[variant_name] = result
                
                # Small delay between variants
                await asyncio.sleep(2)
                
            except Exception as e:
                print(f"Error testing variant {variant_name}: {e}")
        
        return results
    
    def analyze_results(self, results: Dict[str, TestResult]):
        """Analyze and compare results from all variants."""
        print(f"\n{'='*80}")
        print("COMPREHENSIVE ANALYSIS")
        print(f"{'='*80}")
        
        # Sort by total score
        sorted_results = sorted(results.values(), key=lambda x: x.total_score, reverse=True)
        
        print("\nRANKING BY CONTEXTUAL AWARENESS SCORE:")
        for i, result in enumerate(sorted_results, 1):
            efficiency = result.total_score / (result.prompt_tokens / 100)  # Score per 100 tokens
            avg_time = sum(result.response_times) / len(result.response_times) if result.response_times else 0
            
            print(f"{i}. {result.variant_name:12} | Score: {result.total_score:.3f} | "
                  f"Coverage: {result.context_coverage:.3f} | "
                  f"Tokens: {result.prompt_tokens:3d} | "
                  f"Efficiency: {efficiency:.3f} | "
                  f"Avg Time: {avg_time:.1f}s")
        
        print(f"\nDETAILED COMPARISON:")
        print(f"{'Variant':<12} {'Score':<8} {'Coverage':<10} {'Tokens':<8} {'Efficiency':<12} {'Avg Time':<10}")
        print("-" * 80)
        
        for result in sorted_results:
            efficiency = result.total_score / (result.prompt_tokens / 100)
            avg_time = sum(result.response_times) / len(result.response_times) if result.response_times else 0
            
            print(f"{result.variant_name:<12} {result.total_score:<8.3f} {result.context_coverage:<10.3f} "
                  f"{result.prompt_tokens:<8d} {efficiency:<12.3f} {avg_time:<10.1f}")
        
        # Question-by-question analysis
        print(f"\nQUESTION-BY-QUESTION PERFORMANCE:")
        for i, question in enumerate(self.test_questions):
            print(f"\nQ{i+1}: {question.description}")
            print(f"Question: {question.question}")
            
            question_scores = []
            for variant_name in self.prompt_variants.keys():
                if variant_name in results and i < len(results[variant_name].individual_scores):
                    score = results[variant_name].individual_scores[i]
                    question_scores.append((variant_name, score))
            
            # Sort by score for this question
            question_scores.sort(key=lambda x: x[1], reverse=True)
            
            for variant_name, score in question_scores:
                print(f"  {variant_name:12}: {score:.3f}")
        
        # Best variant analysis
        best_variant = sorted_results[0]
        print(f"\n{'='*80}")
        print("WINNER ANALYSIS")
        print(f"{'='*80}")
        print(f"Best performing variant: {best_variant.variant_name.upper()}")
        print(f"Overall score: {best_variant.total_score:.3f}")
        print(f"Context coverage: {best_variant.context_coverage:.3f}")
        print(f"Token efficiency: {best_variant.total_score / (best_variant.prompt_tokens / 100):.3f}")
        
        # Strengths and weaknesses
        print(f"\nSTRENGTHS:")
        strong_questions = [i for i, score in enumerate(best_variant.individual_scores) if score > 0.7]
        for q_idx in strong_questions:
            print(f"  • {self.test_questions[q_idx].description} (score: {best_variant.individual_scores[q_idx]:.3f})")
        
        print(f"\nWEAKNESSES:")
        weak_questions = [i for i, score in enumerate(best_variant.individual_scores) if score < 0.3]
        for q_idx in weak_questions:
            print(f"  • {self.test_questions[q_idx].description} (score: {best_variant.individual_scores[q_idx]:.3f})")
        
        # Recommendations
        print(f"\nRECOMMENDATIONS:")
        
        if best_variant.variant_name == "minimal":
            print("  • Minimal variant wins: Use for token-constrained environments")
            print("  • Trade-off: Lower context coverage but highest efficiency")
        elif best_variant.variant_name == "compact":
            print("  • Compact variant wins: Best balance of efficiency and awareness")
            print("  • Recommended for most production applications")
        elif best_variant.variant_name == "default":
            print("  • Default variant wins: Good all-around performance")
            print("  • Suitable for standard applications without strict token limits")
        elif best_variant.variant_name == "structured":
            print("  • Structured variant wins: Best for programmatic parsing")
            print("  • Recommended for API integrations and structured workflows")
        elif best_variant.variant_name == "detailed":
            print("  • Detailed variant wins: Highest contextual awareness")
            print("  • Use when context richness is more important than efficiency")
        
        return sorted_results


async def main():
    """Main test execution."""
    test_suite = ContextualAwarenessTest()
    
    try:
        # Run all tests
        results = await test_suite.run_all_tests()
        
        # Analyze results
        if results:
            test_suite.analyze_results(results)
            
            # Save results to file
            results_data = {}
            for variant_name, result in results.items():
                results_data[variant_name] = {
                    "total_score": result.total_score,
                    "context_coverage": result.context_coverage,
                    "prompt_tokens": result.prompt_tokens,
                    "individual_scores": result.individual_scores,
                    "response_times": result.response_times
                }
            
            with open("llm_contextual_test_results.json", "w") as f:
                json.dump(results_data, f, indent=2)
            
            print(f"\nResults saved to: llm_contextual_test_results.json")
        else:
            print("No results obtained. Check Ollama connection and model availability.")
            
    except Exception as e:
        print(f"Test execution failed: {e}")
        print("Make sure Ollama is running and qwen3:30b-a3b-q4_K_M is available")


if __name__ == "__main__":
    asyncio.run(main()) 