# LightningRAG

LightningRAG is a minimal, transparent Retrieval-Augmented Generation (RAG) pipeline designed around the [LightningParse](https://github.com/Lightning-AI/lightningparse) PDF extraction library. 

This project serves as a V0.1 validation environment to demonstrate that by preserving semantic layout boundaries and utilizing robust page/section provenance during parsing, a downstream RAG pipeline can achieve higher correctness and fewer hallucinations.

## Core Architecture

The pipeline avoids heavy frameworks like LangChain in favor of transparent, debuggable Python logic:

1. **Extraction**: `LightningParse` (layout-aware, block-level extraction) or a raw `PyPDF` baseline.
2. **Chunking**: Section-aware hierarchical chunking that preserves semantic boundaries. Space restoration via `wordninja` is applied.
3. **Embedding**: `all-MiniLM-L6-v2` (SentenceTransformers) running locally.
4. **Vector Store**: `FAISS` for fast local similarity search.
5. **Generation**: `google/gemini-2.5-flash` with strict grounding prompts to prevent hallucination.

Every retrieved chunk strictly preserves its source filename and page number, enabling full provenance tracking for the LLM.

## Benchmark: LightningParse vs PyPDF

We benchmarked the pipeline's performance using LightningParse against a naive PyPDF baseline (which extracts raw text streams without layout understanding). 

The benchmark was run across two documents (20 pages total):
1. **VTU 7th Sem Study Strategy**: A standard text-heavy PDF.
2. **Synthetic Document**: A complex, multi-column PDF. *(Note: This document was cleaned of unsupported `ASCII85Decode` filters prior to testing to avoid documented OCR fallback penalties).*

### Results

| Metric | LightningParse | Baseline (PyPDF) |
| :--- | :--- | :--- |
| **Parsing latency** | **3.10s** | 6.47s |
| **Pages/sec** | **6.45** | 3.09 |
| **Retrieval Recall@5** | 6/10 | 6/10 |
| **Answer correctness** | **5/10** | 4/10 |
| **Citation correctness** | 6/10 | 6/10 |

**Key Takeaways:**
- **Speed**: LightningParse is over **2x faster** than PyPDF when parsing standard, native PDFs. 
- **Quality**: Because LightningParse returns structured blocks rather than a single jumbled text stream per page, the resulting RAG chunks are cleaner. This prevents "garbage in, garbage out", resulting in higher Answer Correctness from the LLM, despite both systems successfully retrieving the correct pages.

## Setup Instructions

### Prerequisites
- Python 3.11+
- A Google Gemini API Key

### Installation

```bash
# Clone the repository
git clone https://github.com/ShivamMalge/test.git
cd test

# Create and activate a virtual environment
python -m venv .venv
.\.venv\Scripts\activate  # Windows
# source .venv/bin/activate # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### Environment Setup
Create a `.env` file in the root directory and add your API key:
```env
GEMINI_API_KEYS=["your-api-key-here"]
```

## Running the Project

### Running the Evaluation Suite
To run the automated RAG evaluation against the pre-authored grading criteria:
```bash
python tests/evaluate_rag.py
python tests/evaluate_vtu.py
```

### Running the Benchmark
To run the latency and quality benchmark comparing LightningParse to PyPDF:
```bash
python tests/benchmark.py
```

### Inspecting the Parser
To see the raw JSON output of LightningParse for a specific document:
```bash
python inspect_parser.py
```
