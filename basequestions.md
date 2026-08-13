# LightningRAG — Base Question Set

## Purpose

This file defines the base question format for manual RAG validation.

The initial benchmark uses **five questions per document**.

Questions must have answers that are explicitly supported by the source PDF.

Do not create questions whose answers require outside knowledge.

---

# Question 1 — Direct Fact

### Objective

Test straightforward retrieval of a clearly stated fact.

```yaml
type: direct_fact
question: ""
expected_answer: ""
source_page: null
source_section: ""
```

### Example

```yaml
type: direct_fact
question: "What dataset is used in the study?"
expected_answer: ""
source_page: 5
source_section: "3.1 Dataset"
```

---

# Question 2 — Conceptual Understanding

### Objective

Test whether the system can retrieve and synthesize a concept described in the document.

```yaml
type: conceptual
question: ""
expected_answer: ""
source_page: null
source_section: ""
```

### Example

```yaml
type: conceptual
question: "What does the author mean by semantic retrieval?"
expected_answer: ""
source_page: 12
source_section: "4.2 Semantic Retrieval"
```

---

# Question 3 — Contextual Question

### Objective

Test whether retrieval returns enough surrounding context rather than an isolated sentence.

```yaml
type: contextual
question: ""
expected_answer: ""
source_page: null
source_section: ""
```

### Example

```yaml
type: contextual
question: "Why does the author argue that chunk size affects retrieval quality?"
expected_answer: ""
source_page: 19
source_section: "5.1 Chunking"
```

---

# Question 4 — Structured/Table Question

### Objective

Test structured information extraction.

This question should preferably target a table, figure, list, or other structured region.

```yaml
type: structured
question: ""
expected_answer: ""
source_page: null
source_section: ""
```

### Example

```yaml
type: structured
question: "Which model has the highest F1 score, and what is its accuracy?"
expected_answer: ""
source_page: 23
source_section: "Table 4"
```

---

# Question 5 — Cross-Context Question

### Objective

Test whether the system can combine information from a broader section or multiple nearby chunks.

```yaml
type: cross_context
question: ""
expected_answer: ""
source_page: null
source_section: ""
```

### Example

```yaml
type: cross_context
question: "How does the approach described in Chapter 3 address the limitation identified in Chapter 2?"
expected_answer: ""
source_page: null
source_section: ""
```

---

# Evaluation Record

For every question, create an evaluation record.

```yaml
question_id: Q1
question: ""
expected_answer: ""
expected_page: null
expected_section: ""
retrieved_chunks: []
generated_answer: ""
answer_correct: null
citation_correct: null
notes: ""
```

---

# Manual Evaluation Rules

## Answer Correctness

Use:

- `YES`
- `PARTIAL`
- `NO`

### YES

The answer is materially correct and supported by the document.

### PARTIAL

The answer contains some correct information but misses important information or contains a minor error.

### NO

The answer is unsupported, substantially incorrect, or hallucinates information.

## Citation Correctness

Use:

- `YES`
- `NO`

A citation is correct only when the cited page/section actually contains the evidence supporting the answer.

---

# Question Design Rules

Questions should:

- Be answerable from the PDF.
- Have a clearly identifiable source location.
- Cover different retrieval behaviors.
- Avoid ambiguous wording.
- Avoid outside knowledge.
- Avoid questions whose answer is simply the title.
- Include at least one structured-data question when the document contains tables.
- Be difficult enough to expose retrieval failures.

Do not make all five questions simple keyword lookups.

---

# Base Five-Question Pattern

Every initial document should ideally contain:

```text
Q1 → Direct factual retrieval
Q2 → Conceptual retrieval
Q3 → Context-dependent retrieval
Q4 → Table/structured retrieval
Q5 → Broader/cross-context retrieval
```

This provides a small but meaningful first validation of the RAG pipeline.
