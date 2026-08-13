# LightningRAG — Benchmark Plan

## 1. Purpose

This file defines the future benchmarking strategy.

Benchmarking is intentionally **out of scope for the first MVP**.

The initial goal is manual validation.

Benchmarking begins only after the basic pipeline works.

---

# 2. v0.1 Evaluation

For v0.1, use five manually authored questions.

For every question record:

```text
Question
Expected answer
Expected page
Retrieved chunks
Generated answer
Answer correct: YES/NO
Citation correct: YES/NO
```

Ground truth should be manually created from the source PDF.

Do not use the generated answer as its own ground truth.

---

# 3. Future v0.2 Parser Comparison

Compare:

```text
LightningParse
vs
pypdf
```

Keep everything else identical.

```text
Same PDF
   |
   +---- LightningParse -> Same Chunking -> Same Embeddings -> Same FAISS -> Same Questions
   |
   +---- pypdf          -> Same Chunking -> Same Embeddings -> Same FAISS -> Same Questions
```

The parser should be the primary changed variable.

---

# 4. Parsing Metrics

Future measurements may include:

- Total parsing time
- Time per page
- Pages per second
- Number of extracted blocks
- Number of extracted characters
- Table extraction success
- OCR time where applicable
- Failed pages
- Memory usage

Record the document characteristics:

- Filename
- Number of pages
- Approximate document type
- Digital/scanned/mixed
- Two-column or single-column
- Table presence

---

# 5. Retrieval Evaluation

A future benchmark can measure retrieval quality if a ground-truth dataset is created.

Each question should identify the expected evidence location.

Example:

```python
{
    "question": "What is X?",
    "gold_pages": [17, 18],
    "gold_sections": ["4.2"]
}
```

Then retrieval can be evaluated against known evidence.

Possible metrics:

- Recall@1
- Recall@3
- Recall@5
- Recall@10
- MRR

These should only be introduced once a sufficiently reliable ground-truth set exists.

---

# 6. Answer Evaluation

Answer correctness requires a known ground truth.

The preferred initial method is human-authored expected answers.

Example:

```text
Question:
What is the author's definition of X?

Expected:
...

Generated:
...

Human judgement:
Correct / Partially correct / Incorrect
```

A larger benchmark may later use:

- Human evaluation
- Exact-match for constrained answers
- LLM-as-judge with manually validated samples

Do not rely exclusively on LLM-as-judge.

---

# 7. Citation Evaluation

A citation is correct only if it points to the document location containing the evidence used for the answer.

Record:

```text
Expected page: 42
Returned page: 42
Citation correct: YES
```

If the answer is correct but the citation is wrong:

```text
Answer correct: YES
Citation correct: NO
```

Treat these as separate dimensions.

---

# 8. Performance Benchmarking

When performance testing is introduced:

### Warm-up

Run an initial request before timing.

### Repetitions

Run multiple repetitions instead of relying on one measurement.

### Separate stages

Measure independently:

```text
PDF parsing
Chunking
Embedding
Indexing
Retrieval
LLM generation
```

Do not report total RAG latency as parser latency.

### Report

- Mean
- Median
- Minimum
- Maximum
- Standard deviation where useful

---

# 9. Benchmark Corpus

A future corpus should contain different document types:

1. Single-column academic paper
2. Two-column academic paper
3. Long book
4. Technical manual
5. Table-heavy document
6. Scanned document
7. Mixed digital/scanned document
8. Document with footnotes
9. Document with figures/captions

Do not start with all of these.

Expand only after the one-book MVP works.

---

# 10. Benchmark Principle

The most important comparison is not:

> "Which parser is faster?"

It is:

> "Does the parser produce better downstream RAG behavior?"

Performance and quality should therefore be measured separately.

---

# 11. Future Benchmark Report

A final benchmark report may contain:

| Metric | LightningParse | Baseline |
|---|---:|---:|
| Parsing latency | — | — |
| Pages/sec | — | — |
| Extraction failures | — | — |
| Retrieval Recall@5 | — | — |
| Answer correctness | — | — |
| Citation correctness | — | — |

Do not populate this table with fabricated or unsupported values.
