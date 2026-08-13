import sys
import os

# Add src to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Set a dummy key for testing so OpenAI doesn't crash on initialization
if "OPENAI_API_KEY" not in os.environ:
    os.environ["OPENAI_API_KEY"] = "dummy"

from src.generator import Generator

class MockOpenAIClient:
    class Chat:
        class Completions:
            def create(self, model, messages, temperature):
                class MockMessage:
                    content = "This is a mock answer based on the provided context."
                class MockChoice:
                    message = MockMessage()
                class MockResponse:
                    choices = [MockChoice()]
                return MockResponse()
        def __init__(self):
            self.completions = self.Completions()
            
    def __init__(self):
        self.chat = self.Chat()

def test_generator():
    print("Testing LLM generation flow...")
    
    gen = Generator()
    
    # Mock the client if no API key is present
    if not os.environ.get("OPENAI_API_KEY"):
        print("OPENAI_API_KEY not found. Using Mock client for testing.")
        gen.client = MockOpenAIClient()
        
    mock_chunks = [
        {
            "text": "Retrieval-augmented generation, commonly abbreviated RAG, combines a retrieval system with a generative model.",
            "source": "synthetic.pdf",
            "page": 3,
            "section": "body",
            "score": 0.5
        }
    ]
    
    question = "What does RAG stand for?"
    result = gen.generate(question, mock_chunks)
    
    assert "answer" in result
    assert "sources" in result
    assert len(result["sources"]) == 1
    
    print("\n--- Answer ---")
    print(result["answer"])
    print("\n--- Sources ---")
    for s in result["sources"]:
        print(s)
        
    print("\ntest_generator passed!")

if __name__ == "__main__":
    test_generator()
