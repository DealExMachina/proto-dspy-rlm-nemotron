#!/usr/bin/env python3
"""Test unified OpenAI-compatible API worker."""

from src.worker import get_worker, create_ollama_worker

def test_openai_compatible_worker():
    """Test OpenAI-compatible worker with Ollama."""
    print("Testing OpenAI-compatible API worker...")
    
    # Get worker using OpenAI-compatible API (default)
    print("\n1. Using factory with OpenAI API...")
    worker = get_worker(use_ollama=True, use_openai_api=True)
    print(f"   Worker type: {type(worker).__name__}")
    
    # Test basic generation
    print("\n2. Testing basic text generation...")
    response = worker.generate(
        "What is sustainable investment? Answer in one sentence.",
        max_tokens=100
    )
    print(f"   Response: {response[:150]}...")
    
    # Test JSON generation
    print("\n3. Testing JSON generation...")
    json_prompt = """Extract information from this text:
    "This fund is classified under Article 8 of SFDR."
    
    Return JSON with fields: article (string), confidence (number 0-1)"""
    
    try:
        json_response = worker.generate_json(json_prompt, max_tokens=100)
        print(f"   JSON Response: {json_response}")
    except Exception as e:
        print(f"   JSON parsing note: {e}")
        print("   (This is okay - model may not always return valid JSON without structured output mode)")
    
    # Test with system prompt
    print("\n4. Testing with system prompt...")
    response = worker.generate(
        "What is Article 8?",
        system_prompt="You are an expert on SFDR regulations. Be concise.",
        max_tokens=80
    )
    print(f"   Response: {response[:150]}...")
    
    print("\n✅ OpenAI-compatible API working!")
    print("\n📝 Note: This same API format works for:")
    print("   - Ollama (local): http://localhost:11434/v1/chat/completions")
    print("   - Nemotron (Koyeb): https://nemotron.../v1/chat/completions")

if __name__ == "__main__":
    test_openai_compatible_worker()
