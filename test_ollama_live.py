#!/usr/bin/env python3
"""Quick test of Ollama integration with the actual service."""

from src.worker import get_worker

def test_ollama_live():
    """Test real Ollama worker."""
    print("Testing Ollama worker...")
    
    worker = get_worker(use_ollama=True)
    
    # Test basic generation
    print("\n1. Testing basic text generation...")
    response = worker.generate("What is sustainable investment? Answer in one sentence.")
    print(f"Response: {response[:200]}...")
    
    # Test JSON generation
    print("\n2. Testing JSON generation...")
    json_prompt = """Extract the SFDR article number from this text: 
    "This fund is classified under Article 8 of SFDR."
    
    Return JSON with: {"article": "8", "confidence": "0.9"}"""
    
    json_response = worker.generate_json(json_prompt)
    print(f"JSON Response: {json_response}")
    
    print("\n✅ Ollama integration working!")

if __name__ == "__main__":
    test_ollama_live()
