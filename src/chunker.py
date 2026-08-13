import os
from typing import List, Dict, Any

class Chunker:
    def __init__(self, max_chunk_size: int = 1500, min_chunk_size: int = 50):
        self.max_chunk_size = max_chunk_size
        self.min_chunk_size = min_chunk_size

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
            
            for block in blocks:
                block_text = block.get("text", "").strip()
                block_section = block.get("section_id")
                
                if not block_text:
                    continue
                    
                # If section changes or we exceed max size, finalize the current chunk
                if current_chunk_text and (block_section != current_section or len(current_chunk_text) + len(block_text) > self.max_chunk_size):
                    if len(current_chunk_text) >= self.min_chunk_size:
                        chunks.append({
                            "text": current_chunk_text,
                            "source": source_name,
                            "page": page_num,
                            "section": current_section
                        })
                    current_chunk_text = ""
                
                # If a single block is larger than max_chunk_size, we need to split it
                if len(block_text) > self.max_chunk_size:
                    # Finalize current if any
                    if current_chunk_text and len(current_chunk_text) >= self.min_chunk_size:
                        chunks.append({
                            "text": current_chunk_text,
                            "source": source_name,
                            "page": page_num,
                            "section": current_section
                        })
                        current_chunk_text = ""
                    
                    # Split the large block
                    words = block_text.split()
                    temp_text = ""
                    for word in words:
                        if len(temp_text) + len(word) + 1 > self.max_chunk_size:
                            if len(temp_text) >= self.min_chunk_size:
                                chunks.append({
                                    "text": temp_text.strip(),
                                    "source": source_name,
                                    "page": page_num,
                                    "section": block_section
                                })
                            temp_text = word + " "
                        else:
                            temp_text += word + " "
                    
                    if temp_text.strip():
                        current_chunk_text = temp_text.strip()
                        current_section = block_section
                else:
                    if current_chunk_text:
                        current_chunk_text += "\n\n" + block_text
                    else:
                        current_chunk_text = block_text
                    current_section = block_section
            
            # End of page, finalize remaining text
            if current_chunk_text and len(current_chunk_text) >= self.min_chunk_size:
                chunks.append({
                    "text": current_chunk_text,
                    "source": source_name,
                    "page": page_num,
                    "section": current_section
                })
                current_chunk_text = ""

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
