import os
from typing import List, Dict, Any, Tuple
import numpy as np
from google import genai
from dotenv import load_dotenv

load_dotenv()

class EmbeddingPipeline:
    def __init__(self, model_name: str = "gemini-embedding-2"):
        """
        Initializes the embedding pipeline using Google Gemini.
        """
        self.model_name = model_name
        api_keys_str = os.environ.get("GEMINI_API_KEY", "")
        self.api_keys = [k.strip() for k in api_keys_str.split(",") if k.strip()]
        self.current_key_idx = 0
        if not self.api_keys:
            raise ValueError("GEMINI_API_KEY environment variable not set.")
        self.client = genai.Client(api_key=self.api_keys[self.current_key_idx])

    def embed_chunks(self, chunks: List[Dict[str, Any]]) -> Tuple[np.ndarray, List[Dict[str, Any]]]:
        """
        Embeds a list of chunks.
        
        Args:
            chunks: A list of chunk dictionaries.
            
        Returns:
            A tuple of (embeddings, chunks) where embeddings is a numpy array
            of shape (num_chunks, embedding_dim), and chunks is the list of 
            the original chunks.
        """
        if not chunks:
            return np.array([]), []
            
        texts = [chunk["text"] for chunk in chunks]
        
        # Call the Google GenAI embedding API
        # Batch to handle API limits
        import time
        embeddings_list = []
        batch_size = 50 # smaller batch
        
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            retries = max(3, len(self.api_keys) * 2)
            while retries > 0:
                try:
                    response = self.client.models.embed_content(
                        model=self.model_name,
                        contents=batch_texts
                    )
                    for emb in response.embeddings:
                        embeddings_list.append(emb.values)
                    break # Success, exit retry loop
                except Exception as e:
                    if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                        if len(self.api_keys) > 1:
                            print("Embedding key exhausted. Switching to next key...")
                            self.current_key_idx = (self.current_key_idx + 1) % len(self.api_keys)
                            self.client = genai.Client(api_key=self.api_keys[self.current_key_idx])
                            time.sleep(2)
                            retries -= 1
                            continue
                        else:
                            print(f"Rate limit or error: {e}. Retrying in 45s...")
                            time.sleep(45)
                    else:
                        print(f"Error: {e}. Retrying in 10s...")
                        time.sleep(10)
                    retries -= 1
            if retries == 0:
                print("Failed to embed chunk batch after retries.")
                return np.array([]), []
                
        embeddings = np.array(embeddings_list, dtype=np.float32)
            
        return embeddings, chunks
