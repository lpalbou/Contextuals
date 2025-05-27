#!/usr/bin/env python3
"""
Test script to verify the contextually-aware judge works correctly.
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from contextuals import Contextuals
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider


async def test_judge_context():
    """Test that the judge receives and uses contextual information."""
    print("🧪 TESTING CONTEXTUALLY-AWARE JUDGE")
    print("=" * 60)
    
    # Get contextual information
    contextuals = Contextuals()
    judge_context_prompt = contextuals.get_context_prompt_structured(include_news=3)
    
    print("📋 CONTEXTUAL DATA PROVIDED TO JUDGE:")
    print("-" * 40)
    print(judge_context_prompt[:500] + "..." if len(judge_context_prompt) > 500 else judge_context_prompt)
    print("-" * 40)
    
    # Create judge system prompt (simplified version for testing)
    judge_system_prompt = f"""{judge_context_prompt}

=== EXPERT CONTEXTUAL AI EVALUATOR ===

You are the REFERENCE IMPLEMENTATION for contextual AI responses. Demonstrate how to properly use the contextual information provided above.

TASK: Answer this question using the contextual data: "What should I wear outside today?"

Show how to integrate:
1. Temperature and weather conditions
2. Location and cultural context  
3. Time of day considerations
4. Any other relevant contextual factors

Provide a comprehensive, contextually-aware response that serves as the gold standard."""
    
    # Create judge model and agent
    judge_model = OpenAIModel(
        model_name='qwen3:30b-a3b-q4_K_M',
        provider=OpenAIProvider(base_url='http://localhost:11434/v1')
    )
    
    judge_agent = Agent(
        model=judge_model,
        system_prompt=judge_system_prompt
    )
    
    print("\n🤖 JUDGE RESPONSE (Reference Implementation):")
    print("-" * 60)
    
    try:
        result = await judge_agent.run("Demonstrate contextual awareness for clothing recommendation.")
        response = result.data
        print(response)
        
        print("\n✅ CONTEXTUAL ELEMENTS TO VERIFY:")
        print("- Temperature mentioned (12.82°C)")
        print("- Weather condition (clear sky)")
        print("- Location awareness (Paris)")
        print("- Cultural context (French)")
        print("- Time considerations")
        print("- Practical recommendations")
        
        # Check for key contextual elements
        context_checks = {
            "Temperature": any(temp in response for temp in ["12.82", "12.8", "13°", "cool", "chilly"]),
            "Weather": any(weather in response.lower() for weather in ["clear", "sky", "sunny"]),
            "Location": any(loc in response for loc in ["Paris", "France", "French"]),
            "Practical": any(item in response.lower() for item in ["jacket", "sweater", "layer", "coat"])
        }
        
        print(f"\n📊 CONTEXTUAL INTEGRATION CHECK:")
        for element, found in context_checks.items():
            status = "✅" if found else "❌"
            print(f"{status} {element}: {'Found' if found else 'Missing'}")
        
        overall_score = sum(context_checks.values()) / len(context_checks)
        print(f"\n🎯 Overall Contextual Integration: {overall_score:.1%}")
        
        if overall_score >= 0.75:
            print("🎉 Judge demonstrates excellent contextual awareness!")
        elif overall_score >= 0.5:
            print("⚠️  Judge shows moderate contextual awareness")
        else:
            print("❌ Judge needs improvement in contextual integration")
            
    except Exception as e:
        print(f"❌ Error testing judge: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(test_judge_context())
    sys.exit(exit_code) 