import os
from typing import List, Dict, Any
from openai import OpenAI

class Generator:
    def __init__(self, model: str = "gpt-3.5-turbo"):
        self.model = model
        # We assume the OPENAI_API_KEY environment variable is set
        self.client = OpenAI()
        
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
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.0
            )
            answer_text = response.choices[0].message.content
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
