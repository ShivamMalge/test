# LightningRAG — Agent Execution Phases

## Purpose

This file is the **execution contract for the coding agent**.

The agent must execute the project **phase by phase**.

Each phase contains:

- Objective
- Required tasks
- Files to create/modify
- Verification steps
- Deliverables
- Exit criteria
- Explicit scope restrictions

The agent MUST NOT skip ahead simply because a later phase appears easy.

The agent may proceed to the next phase only when the current phase's exit criteria are satisfied.

---

# Global Execution Rules

Before starting any phase:

1. Read `prd.md`.
2. Read `agents.md`.
3. Read the relevant sections of `benchmark.md` and `basequestions.md` when evaluation becomes relevant.
4. Inspect the existing repository before creating files.
5. Reuse existing working code when appropriate.
6. Do not duplicate functionality that already exists.
7. Do not invent LightningParse APIs. Inspect the installed package or documentation.
8. Run code/tests after meaningful changes.
9. Do not claim a task is complete without verification.
10. Keep changes limited to the current phase.

## Scope Rule

The initial project is a **small validation project**.

Do not introduce:

- LangChain
- Agents
- Complex orchestration
- Multiple vector databases
- Automated benchmark frameworks
- Distributed infrastructure
- Production deployment
- Unnecessary frontend work

unless a later phase explicitly requires them.

---

# Phase 0 — Repository and Environment Setup

## Objective

Prepare a clean, runnable Python project without implementing the RAG pipeline yet.

## Agent Tasks

### 0.1 Inspect the repository

Determine:

- Existing project structure
- Existing Python version
- Existing dependency manager
- Existing configuration
- Existing source code
- Existing tests
- Whether `lightningparse-api` or related code already exists

Do not overwrite existing working code.

### 0.2 Create or verify project structure

The target structure should approximately be:

```text
lightning-rag/
│
├── data/
│   ├── synthetic/
│   └── books/
│
├── src/
│   ├── parser.py
│   ├── chunker.py
│   ├── embeddings.py
│   ├── retriever.py
│   ├── generator.py
│   └── pipeline.py
│
├── tests/
│
├── app.py
├── requirements.txt
├── README.md
│
└── docs/
```

Adapt this structure if the existing repository already has an appropriate organization.

### 0.3 Install dependencies

The initial stack is:

- Python
- LightningParse
- Sentence Transformers
- FAISS
- Selected LLM SDK

Do not add unnecessary dependencies.

### 0.4 Verify LightningParse

Confirm that the intended package is actually installed:

```bash
python -c "import lightningparse; print(lightningparse)"
```

Inspect its available API before writing parser code.

## Files

Create or modify only the minimum required setup files.

## Verification

The agent must verify:

- Python environment works.
- LightningParse imports successfully.
- Sentence Transformers imports successfully.
- FAISS imports successfully.
- LLM dependency imports successfully if applicable.

## Deliverable

A clean project that can execute Python code and import the required dependencies.

## Exit Criteria

All required dependencies import successfully and the repository structure is ready.

## Do NOT

- Implement chunking.
- Implement embeddings.
- Implement FAISS retrieval.
- Build UI.
- Build evaluation infrastructure.

---

# Phase 1 — LightningParse Inspection

## Objective

Understand and validate LightningParse's output before building any RAG functionality.

## Input

Use the synthetic two-column PDF:

```text
data/synthetic/lightningparse_test_document_TRUE_2COL.pdf
```

If the file is not available in the repository, place the generated test PDF into the expected location before continuing.

## Agent Tasks

### 1.1 Implement parser wrapper

Create:

```text
src/parser.py
```

Implement a thin wrapper around LightningParse.

The wrapper should:

- Accept a PDF path.
- Call LightningParse.
- Return the parser's structured result.
- Avoid unnecessary transformation at this stage.

Do not hide useful parser metadata.

### 1.2 Create an inspection script

Create a small executable script or CLI that prints:

- Number of pages
- Page identifiers
- Number of blocks per page
- Block text
- Section identifiers
- Table information where available
- Other useful metadata

### 1.3 Inspect the two-column document

Explicitly verify:

- Left column content
- Right column content
- Reading order
- Section boundaries
- Page boundaries
- Heading detection
- Table extraction

### 1.4 Record parser observations

Create or update a small development note documenting:

```text
Observed schema:
...

Page representation:
...

Block representation:
...

Table representation:
...

Metadata available:
...

Known issues:
...
```

Do not modify LightningParse to compensate for problems during this phase.

## Files

Expected:

```text
src/parser.py
tests/test_parser.py
```

Additional inspection scripts may be added if useful.

## Verification

Run the parser against the synthetic PDF.

Confirm that:

- The PDF loads.
- Pages are returned.
- Blocks are returned.
- Text is recoverable.
- Two-column content is present.
- The parser output can be serialized/inspected.

## Deliverable

A working parser wrapper plus an inspection/test script.

## Exit Criteria

The agent understands the actual LightningParse output schema and has verified that the synthetic PDF can be parsed.

## Do NOT

- Implement chunking.
- Implement embeddings.
- Implement FAISS.
- Add an LLM.
- Add automated RAG evaluation.

---

# Phase 2 — Metadata-Aware Chunking

## Objective

Transform LightningParse output into clean retrieval-ready chunks while preserving provenance.

## Agent Tasks

### 2.1 Define a chunk representation

Create:

```text
src/chunker.py
```

Each chunk should contain at minimum:

```python
{
    "text": "...",
    "source": "document.pdf",
    "page": 1,
    "section": "...",
}
```

Add other metadata only when it is actually available and useful.

### 2.2 Design chunking logic

Prefer semantic/document boundaries over blindly splitting every N characters.

Use:

- Page boundaries
- Section boundaries
- Block boundaries

as primary signals.

Only split large blocks when necessary.

### 2.3 Prevent bad chunks

The chunker should avoid:

- Empty chunks
- Whitespace-only chunks
- Extremely tiny fragments
- Extremely large chunks
- Chunks containing unrelated column content
- Loss of source metadata

### 2.4 Create chunk inspection output

The agent should be able to print:

```text
Chunk ID
Source
Page
Section
Character count
Text preview
```

### 2.5 Test the chunker

Create:

```text
tests/test_chunker.py
```

Test at minimum:

- Metadata preservation
- Empty block handling
- Chunk creation
- Large-block splitting
- Source/page retention

## Files

```text
src/chunker.py
tests/test_chunker.py
```

## Verification

Run the chunker against the parsed synthetic PDF.

Inspect several chunks manually.

Verify that every chunk can be traced back to a source page.

## Deliverable

A deterministic metadata-aware chunking module.

## Exit Criteria

- Parsed blocks become usable chunks.
- Metadata is preserved.
- No empty chunks are produced.
- Tests pass.
- Sample chunks have coherent semantic content.

## Do NOT

- Add embeddings.
- Add FAISS.
- Add LLM code.
- Implement hybrid retrieval.

---

# Phase 3 — Embedding Pipeline

## Objective

Convert chunks into vector embeddings.

## Agent Tasks

### 3.1 Select an embedding model

Use a lightweight Sentence Transformers model suitable for local testing.

Do not over-optimize model selection.

Document the selected model.

### 3.2 Implement embedding module

Create:

```text
src/embeddings.py
```

The module should:

- Load the embedding model.
- Accept chunks.
- Generate one embedding per chunk.
- Return embeddings in deterministic order.

### 3.3 Preserve vector-to-chunk mapping

The system MUST preserve:

```text
Vector ID → Chunk ID → Chunk metadata
```

This mapping is essential for citations.

### 3.4 Test embedding generation

Create:

```text
tests/test_embeddings.py
```

Verify:

- Model loads.
- Embeddings are generated.
- Embedding count equals chunk count.
- Embedding dimensions are consistent.
- Metadata mapping remains intact.

## Verification

Embed a small sample of chunks.

Print:

```text
Number of chunks
Embedding shape
Embedding dimension
```

## Deliverable

A working embedding layer with deterministic chunk/vector mapping.

## Exit Criteria

The same number of embeddings as chunks can be generated and each vector can be mapped back to its source chunk.

## Do NOT

- Add multiple embedding models.
- Add reranking.
- Add hybrid search.
- Add external vector databases.

---

# Phase 4 — FAISS Retrieval

## Objective

Implement semantic retrieval over the generated embeddings.

## Agent Tasks

### 4.1 Implement retriever

Create:

```text
src/retriever.py
```

The retriever should:

1. Accept chunk embeddings.
2. Build a FAISS index.
3. Add vectors.
4. Accept a user query.
5. Embed the query.
6. Search the FAISS index.
7. Return top-k chunks with metadata.

### 4.2 Define retrieval result

A retrieval result should contain:

```python
{
    "score": 0.0,
    "text": "...",
    "source": "document.pdf",
    "page": 1,
    "section": "..."
}
```

### 4.3 Test retrieval

Create:

```text
tests/test_retriever.py
```

Test that:

- The index builds.
- A query returns results.
- `k` is respected.
- Scores are returned.
- Source metadata is preserved.

### 4.4 Run manual retrieval tests

Ask several obvious questions whose answers are present in the synthetic PDF.

Inspect whether the expected chunks appear near the top.

## Deliverable

A minimal FAISS semantic retrieval layer.

## Exit Criteria

A natural-language query successfully returns relevant chunks and their source metadata.

## Do NOT

- Implement reranking.
- Implement hybrid search.
- Implement Recall@k benchmarking.
- Compare against pypdf yet.

---

# Phase 5 — LLM Generation

## Objective

Use retrieved chunks to generate an answer.

## Agent Tasks

### 5.1 Implement generator

Create:

```text
src/generator.py
```

The generator should:

- Accept a question.
- Accept retrieved chunks.
- Construct a concise context prompt.
- Call the configured LLM.
- Return the answer.
- Preserve the retrieved source information.

### 5.2 Prompt behavior

The LLM should be instructed:

- Use the supplied context.
- Do not invent unsupported facts.
- If the context is insufficient, say so.
- Identify source/page information when appropriate.

### 5.3 Test generation

Create a minimal test or manual execution path.

Use one known question from the synthetic PDF.

Verify that the answer is supported by retrieved context.

## Deliverable

A working:

```text
Question
  ↓
Retriever
  ↓
Context
  ↓
LLM
  ↓
Answer + Sources
```

flow.

## Exit Criteria

The LLM can answer at least one known question using retrieved context and the answer can be traced back to the source PDF.

## Do NOT

- Add agents.
- Add tool calling.
- Add conversational memory.
- Add autonomous workflows.

---

# Phase 6 — End-to-End Pipeline

## Objective

Connect all components into one minimal RAG pipeline.

## Agent Tasks

### 6.1 Implement pipeline

Create:

```text
src/pipeline.py
```

The pipeline should connect:

```text
PDF
 ↓
LightningParse
 ↓
Chunking
 ↓
Embeddings
 ↓
FAISS
 ↓
Query
 ↓
Retrieval
 ↓
LLM
 ↓
Answer
```

### 6.2 Expose a simple API

Provide a simple function such as:

```python
answer = ask(
    pdf_path="document.pdf",
    question="..."
)
```

or an equivalent clean interface.

### 6.3 Add source information

The result should expose:

```python
{
    "answer": "...",
    "sources": [
        {
            "source": "document.pdf",
            "page": 4,
            "section": "..."
        }
    ]
}
```

### 6.4 Test the complete pipeline

Run at least three questions against the synthetic PDF.

Inspect:

- Answer
- Retrieved chunks
- Sources
- Pages
- Retrieval scores

## Deliverable

A working end-to-end RAG pipeline.

## Exit Criteria

The complete pipeline can answer known questions against the synthetic PDF and expose traceable source information.

## Do NOT

- Add the book yet.
- Add benchmarks.
- Add pypdf.
- Build a large UI.

---

# Phase 7 — Five-Question Validation

## Objective

Perform the first controlled manual evaluation.

## Agent Tasks

### 7.1 Create five questions

Use `basequestions.md`.

Create exactly five questions covering:

1. Direct fact
2. Conceptual understanding
3. Context-dependent retrieval
4. Table/structured information
5. Broader/cross-context retrieval

### 7.2 Establish ground truth

For every question manually record:

- Expected answer
- Expected page
- Expected section

Do not generate ground truth from the RAG system.

### 7.3 Run evaluation

For every question record:

```text
Question
Expected answer
Retrieved chunks
Generated answer
Expected page
Returned page
Answer correctness
Citation correctness
Notes
```

### 7.4 Diagnose failures

If a question fails, determine the first failed stage:

```text
Parsing
 ↓
Chunking
 ↓
Embedding
 ↓
Retrieval
 ↓
Generation
```

Do not simply mark the final answer incorrect without identifying the likely cause.

## Deliverable

A five-question manual evaluation report.

## Exit Criteria

All five questions have documented results.

The agent has identified whether failures are primarily caused by parsing, chunking, retrieval, or generation.

## Do NOT

- Create automated accuracy metrics.
- Introduce Recall@k.
- Add a baseline parser.

---

# Phase 8 — Real Book Validation

## Objective

Test the exact same pipeline on one real book PDF.

## Input

One real book PDF supplied by the developer.

Place it under:

```text
data/books/
```

## Agent Tasks

### 8.1 Parse the book

Use the existing parser module without modifying its behavior specifically for the book.

### 8.2 Inspect representative pages

Inspect:

- Beginning
- Chapter boundaries
- Dense text
- Any tables
- Any unusual layouts
- Random interior pages

### 8.3 Run the existing chunker

Do not create a book-specific chunking implementation unless a documented parser/layout issue requires it.

### 8.4 Index the book

Generate embeddings and build FAISS using the existing pipeline.

### 8.5 Create five questions

Create five questions using `basequestions.md`.

### 8.6 Run manual evaluation

Record the same evaluation information used in Phase 7.

## Deliverable

A real-book validation report.

## Exit Criteria

- The book parses successfully.
- The pipeline indexes it successfully.
- Five questions can be evaluated.
- Retrieved evidence is inspectable.
- Source/page metadata remains available.
- Major failures are documented.

---

# Phase 9 — MVP Review

## Objective

Determine whether LightningParse successfully served as the PDF ingestion layer for the RAG pipeline.

## Agent Tasks

Create a short report containing:

### Parser

- What worked?
- What failed?
- How good was reading order?
- How useful was the structure?

### Chunking

- Were chunks coherent?
- Was metadata preserved?

### Retrieval

- Did relevant chunks appear?
- Which questions failed retrieval?

### Generation

- Were answers grounded?
- Were citations useful?

### Overall

Answer:

> Is LightningParse good enough to continue using as the ingestion layer?

## Decision

Choose exactly one:

```text
PASS
```

The MVP validates the approach.

or:

```text
PASS WITH ISSUES
```

The approach works but specific problems need fixing.

or:

```text
FAIL
```

The current pipeline cannot reliably use LightningParse for the intended task.

## Deliverable

`MVP_REVIEW.md`

---

# Phase 10 — Only If MVP Passes: v0.2 Benchmarking

This phase is NOT part of the initial MVP.

Proceed only after Phase 9.

## Objective

Compare LightningParse with a baseline parser.

Initial baseline:

```text
pypdf
```

## Agent Tasks

Build two pipelines:

```text
LightningParse -> same chunking -> same embeddings -> same FAISS -> same questions
pypdf          -> same chunking -> same embeddings -> same FAISS -> same questions
```

Keep all downstream components identical.

Measure:

- Parsing latency
- Extraction failures
- Reading-order quality
- Retrieval quality
- Answer correctness
- Citation correctness

Refer to `benchmark.md`.

## Do NOT

Do not change multiple variables simultaneously.

Do not claim that LightningParse is better based on parsing speed alone.

---

# Phase 11 — Optional Automated Benchmark

Only implement this phase if the v0.2 comparison produces useful results.

## Possible Metrics

- Recall@1
- Recall@3
- Recall@5
- Recall@10
- MRR
- Parsing latency
- Pages/second
- Answer correctness
- Citation correctness

## Requirement

Every automated metric must have a clearly defined evaluation procedure and ground truth.

Do not add a metric merely because it sounds useful.

---

# Final Execution Order

The agent MUST follow this order:

```text
Phase 0
Setup
  ↓
Phase 1
Inspect LightningParse
  ↓
Phase 2
Chunking
  ↓
Phase 3
Embeddings
  ↓
Phase 4
FAISS Retrieval
  ↓
Phase 5
LLM Generation
  ↓
Phase 6
End-to-End Pipeline
  ↓
Phase 7
Five-Question Validation
  ↓
Phase 8
Real Book Validation
  ↓
Phase 9
MVP Review
  ↓
┌──────────────────────────────┐
│ MVP PASS / PASS WITH ISSUES  │
└──────────────┬───────────────┘
               ↓
          Phase 10+
          Benchmarking
```

# Mandatory Agent Behavior

At the end of every phase, the agent must report:

```text
PHASE: <number and name>

Implemented:
- ...

Files changed:
- ...

Verified:
- ...

Tests:
- ...

Result:
PASS / PASS WITH ISSUES / FAIL

Issues:
- ...

Next phase:
<next phase>
```

The agent must never silently move past a failed exit criterion.

If a phase fails, fix the phase before continuing.

The agent must prefer a small verified implementation over a large speculative implementation.
