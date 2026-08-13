import os
from typing import List, Dict, Any
from google import genai
from dotenv import load_dotenv

load_dotenv()

class Generator:
    def __init__(self, model: str = "gemini-2.5-flash"):
        self.model = model
        # We assume the GEMINI_API_KEY environment variable is set
        api_key = os.environ.get("GEMINI_API_KEY")
        self.client = genai.Client(api_key=api_key)
        
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
        except Exception as e:
            answer_text = f"Error calling LLM: {str(e)}"
            
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
