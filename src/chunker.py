import os
from typing import List, Dict, Any

class Chunker:
    def __init__(self, max_chunk_size: int = 1500, min_chunk_size: int = 50):
        self.max_chunk_size = max_chunk_size
        self.min_chunk_size = min_chunk_size

    def _split_into_sentences(self, text: str) -> List[str]:
        import re
        # Split on common sentence boundaries (period, question, exclamation) followed by space
        # Also split on double newlines
        parts = re.split(r'(\n\n|(?<=[.!?])\s+)', text)
        
        # re.split with capture groups returns the delimiters too. Recombine them.
        sentences = []
        current = ""
        for part in parts:
            if part in ("\n\n", " ") or re.match(r'^\s+$', part):
                current += part
            else:
                if current:
                    sentences.append(current)
                current = part
        if current:
            sentences.append(current)
        
        # Clean up
        sentences = [s.strip() for s in sentences if s.strip()]
        return sentences

    def chunk_document(self, parsed_doc: Dict[str, Any], source_name: str) -> List[Dict[str, Any]]:
        """
        Converts a parsed document into a list of retrieval-ready chunks.
        """
        chunks = []
        
        pages = parsed_doc.get("pages", [])
        for page in pages:
            page_num = page.get("page_num")
            blocks = page.get("blocks", [])
            
            current_chunk_text = ""
            current_section = None
            
            def finalize_chunk():
                nonlocal current_chunk_text
                if current_chunk_text and len(current_chunk_text) >= self.min_chunk_size:
                    chunks.append({
                        "text": current_chunk_text.strip(),
                        "source": source_name,
                        "page": page_num,
                        "section": current_section
                    })
                current_chunk_text = ""

            for block in blocks:
                block_text = block.get("text", "").strip()
                block_section = block.get("section_id")
                
                if not block_text:
                    continue
                    
                # lightningparse v3.1.0 sometimes drops spaces in text extraction
                # We use wordninja to probabilistically restore spaces if it looks like a giant concatenated string
                import wordninja
                # If average word length is suspiciously high (e.g., > 15 chars), it's likely missing spaces
                if len(block_text.split()) > 0 and len(block_text) / len(block_text.split()) > 15:
                    block_text = " ".join(wordninja.split(block_text))
                    
                # If section changes, finalize the current chunk
                if current_chunk_text and block_section != current_section:
                    finalize_chunk()
                
                current_section = block_section
                
                # Check if adding the whole block exceeds max size
                if len(current_chunk_text) + len(block_text) > self.max_chunk_size:
                    # Finalize current if it's substantial
                    if len(current_chunk_text) > self.max_chunk_size // 2:
                        finalize_chunk()
                        
                    # Split block by sentences
                    sentences = self._split_into_sentences(block_text)
                    for sentence in sentences:
                        if len(current_chunk_text) + len(sentence) > self.max_chunk_size:
                            finalize_chunk()
                            
                        # If a single sentence is still larger than max_chunk_size, 
                        # we fall back to splitting by words to avoid dropping data.
                        if len(sentence) > self.max_chunk_size:
                            words = sentence.split()
                            for word in words:
                                if len(current_chunk_text) + len(word) + 1 > self.max_chunk_size:
                                    finalize_chunk()
                                current_chunk_text += (word + " ")
                        else:
                            if current_chunk_text:
                                current_chunk_text += " " + sentence
                            else:
                                current_chunk_text = sentence
                else:
                    if current_chunk_text:
                        current_chunk_text += "\n\n" + block_text
                    else:
                        current_chunk_text = block_text
            
            # End of page, finalize remaining text
            finalize_chunk()

        # Add chunk IDs
        for idx, chunk in enumerate(chunks):
            chunk["chunk_id"] = f"{os.path.basename(source_name)}_p{chunk['page']}_{idx}"

        return chunks

def print_chunks(chunks: List[Dict[str, Any]]):
    """
    Prints a summary of the chunks for inspection.
    """
    print(f"Total chunks: {len(chunks)}")
    print("-" * 50)
    for chunk in chunks:
        preview = chunk["text"].replace("\n", " ")[:60]
        print(f"Chunk ID: {chunk.get('chunk_id')}")
        print(f"Source:   {chunk['source']} (Page {chunk['page']}, Section: {chunk['section']})")
        print(f"Size:     {len(chunk['text'])} chars")
        print(f"Preview:  {preview}...")
        print("-" * 50)
