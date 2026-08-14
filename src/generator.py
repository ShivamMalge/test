import os
from typing import List, Dict, Any
from google import genai
from dotenv import load_dotenv

load_dotenv()

class Generator:
    def __init__(self, model: str = "gemini-2.5-flash"):
        self.model = model
        # We assume the GEMINI_API_KEY environment variable is set
        api_keys_str = os.environ.get("GEMINI_API_KEY", "")
        self.api_keys = [k.strip() for k in api_keys_str.split(",") if k.strip()]
        self.current_key_idx = 0
        if not self.api_keys:
            raise ValueError("GEMINI_API_KEY environment variable not set.")
        self.client = genai.Client(api_key=self.api_keys[self.current_key_idx])
        
    def generate(self, question: str, retrieved_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generates an answer based on retrieved chunks.
        """
        # Format the context
        context_parts = []
        for idx, chunk in enumerate(retrieved_chunks):
            # Include minimal metadata in the prompt to help the LLM cite if needed
            source_info = f"Source: {os.path.basename(chunk['source'])}, Page: {chunk['page']}, Section: {chunk['section']}"
            context_parts.append(f"--- Context {idx + 1} ({source_info}) ---\n{chunk['text']}\n")
            
        context_str = "\n".join(context_parts)
        
        system_prompt = (
            "You are a helpful assistant answering questions based solely on the provided document context. "
            "Follow these strict rules:\n"
            "1. Answer using ONLY the supplied context.\n"
            "2. Do NOT invent or hallucinate unsupported facts.\n"
            "3. If the context does not contain enough information to answer the question, say clearly "
            "'The answer cannot be determined from the retrieved material.'\n"
            "4. When you provide an answer, briefly mention the source or page number based on the context headers."
        )
        
        user_prompt = f"Context:\n\n{context_str}\n\nQuestion: {question}"
        
        import time
        retries = max(3, len(self.api_keys) * 2)
        answer_text = ""
        while retries > 0:
            try:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=user_prompt,
                    config=genai.types.GenerateContentConfig(
                        system_instruction=system_prompt,
                        temperature=0.0
                    )
                )
                answer_text = response.text
                break
            except Exception as e:
                print(f"Error calling LLM (retry {retries}): {str(e)}")
                if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                    if len(self.api_keys) > 1:
                        print("Key exhausted. Switching to next key...")
                        self.current_key_idx = (self.current_key_idx + 1) % len(self.api_keys)
                        self.client = genai.Client(api_key=self.api_keys[self.current_key_idx])
                        time.sleep(2)
                        retries -= 1
                        continue
                    else:
                        import re
                        match = re.search(r'retry in ([\d\.]+)s', str(e))
                        delay = float(match.group(1)) + 5 if match else 65
                        print(f"Sleeping for {delay} seconds...")
                        time.sleep(delay)
                else:
                    time.sleep(10)
                retries -= 1
        
        if not answer_text:
            answer_text = "Failed to generate answer after multiple retries."
            
        # Return the generated answer along with the exact source metadata 
        # so provenance is never lost.
        return {
            "answer": answer_text,
            "sources": [
                {
                    "source": chunk["source"],
                    "page": chunk["page"],
                    "section": chunk["section"],
                    "score": chunk.get("score")
                }
                for chunk in retrieved_chunks
            ]
        }
