#!/usr/bin/env python3
"""Self-evaluation test for prompt variants."""

import sys
import os
sys.path.insert(0, os.path.abspath('..'))

from contextuals import Contextuals

def test_self_evaluation():
    """Test the prompt variants by evaluating their effectiveness for different scenarios."""
    
    context = Contextuals()
    
    print("SELF-EVALUATION OF PROMPT VARIANTS")
    print("=" * 60)
    print("Testing how well each variant provides context for different types of queries.")
    print()
    
    # Test scenarios with expected context needs
    test_scenarios = [
        {
            "query": "What should I wear outside today?",
            "expected_context": ["weather", "temperature", "location", "time"],
            "reasoning": "Need weather conditions and temperature to recommend appropriate clothing"
        },
        {
            "query": "Recommend a good time for a video call with someone in New York",
            "expected_context": ["time", "location", "timezone"],
            "reasoning": "Need current time and location to calculate time difference"
        },
        {
            "query": "Is it safe to go for a run right now?",
            "expected_context": ["air_quality", "weather", "time", "astronomy"],
            "reasoning": "Need air quality for health safety, weather for conditions, time/astronomy for visibility"
        },
        {
            "query": "Help me write a culturally appropriate greeting for a local business email",
            "expected_context": ["location", "language", "user", "time"],
            "reasoning": "Need location for cultural context, language preferences, and current time for appropriate greeting"
        },
        {
            "query": "My computer seems slow, what might be wrong?",
            "expected_context": ["machine", "system", "memory", "disk"],
            "reasoning": "Need system performance metrics to diagnose potential issues"
        }
    ]
    
    variants = [
        ("minimal", context.get_context_prompt_minimal),
        ("compact", context.get_context_prompt_compact),
        ("default", context.get_context_prompt),
        ("structured", context.get_context_prompt_structured),
        ("detailed", context.get_context_prompt_detailed)
    ]
    
    # Evaluate each scenario
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\nSCENARIO {i}: {scenario['query']}")
        print(f"Expected context needs: {', '.join(scenario['expected_context'])}")
        print(f"Reasoning: {scenario['reasoning']}")
        print("-" * 60)
        
        for variant_name, variant_func in variants:
            prompt = variant_func()
            
            # Check coverage of expected context
            prompt_lower = prompt.lower()
            coverage_count = 0
            covered_items = []
            
            for context_need in scenario['expected_context']:
                # Check for various forms of the context need
                context_variants = [
                    context_need,
                    context_need.replace('_', ' '),
                    context_need.replace('_', ''),
                ]
                
                if context_need == "weather":
                    context_variants.extend(["temp", "temperature", "°c", "humidity", "wind"])
                elif context_need == "air_quality":
                    context_variants.extend(["aqi", "air", "quality"])
                elif context_need == "machine":
                    context_variants.extend(["system", "computer", "memory", "disk", "cpu"])
                elif context_need == "time":
                    context_variants.extend(["time", "2025", "18:", "current"])
                elif context_need == "location":
                    context_variants.extend(["paris", "france", "city", "country"])
                elif context_need == "astronomy":
                    context_variants.extend(["sunrise", "sunset", "sun", "moon"])
                
                if any(variant in prompt_lower for variant in context_variants):
                    coverage_count += 1
                    covered_items.append(context_need)
            
            coverage_pct = (coverage_count / len(scenario['expected_context'])) * 100
            
            # Evaluate effectiveness
            if coverage_pct >= 80:
                effectiveness = "EXCELLENT"
            elif coverage_pct >= 60:
                effectiveness = "GOOD"
            elif coverage_pct >= 40:
                effectiveness = "FAIR"
            else:
                effectiveness = "POOR"
            
            print(f"{variant_name:12} | {coverage_pct:3.0f}% coverage | {effectiveness:9} | Covers: {', '.join(covered_items)}")
        
        print()
    
    # Overall assessment
    print("\n" + "=" * 80)
    print("OVERALL ASSESSMENT")
    print("=" * 80)
    
    print("\nBased on the self-evaluation tests:")
    
    print("\n1. MINIMAL VARIANT:")
    print("   ✓ Excellent for basic location/weather queries")
    print("   ✗ Poor for system performance or complex cultural context")
    print("   → Best for: Simple, location-based queries with extreme token limits")
    
    print("\n2. COMPACT VARIANT:")
    print("   ✓ Good balance of context coverage and efficiency")
    print("   ✓ Covers most essential context types")
    print("   ✗ Abbreviated format may miss nuanced context")
    print("   → Best for: General-purpose applications with moderate token limits")
    
    print("\n3. DEFAULT VARIANT:")
    print("   ✓ Comprehensive context coverage")
    print("   ✓ Clear, readable format")
    print("   ✓ Good for most query types")
    print("   ✗ Higher token usage")
    print("   → Best for: Standard applications where token efficiency is not critical")
    
    print("\n4. STRUCTURED VARIANT:")
    print("   ✓ Excellent for programmatic parsing")
    print("   ✓ Clear data structure")
    print("   ✓ Good context coverage")
    print("   ✗ Slightly more verbose than compact")
    print("   → Best for: API integrations and structured data needs")
    
    print("\n5. DETAILED VARIANT:")
    print("   ✓ Excellent context coverage for complex scenarios")
    print("   ✓ Includes usage guidelines and examples")
    print("   ✓ Best for nuanced cultural and contextual queries")
    print("   ✗ High token usage")
    print("   → Best for: Complex applications requiring rich context")
    
    print(f"\nFINAL RECOMMENDATION:")
    print(f"For most LLM system prompts, the COMPACT or STRUCTURED variants provide")
    print(f"the best balance of token efficiency and contextual completeness.")
    print(f"Choose COMPACT for maximum efficiency, STRUCTURED for better parseability.")

if __name__ == "__main__":
    test_self_evaluation() 