# LightningRAG — Agent Instructions

## 1. Mission

Build and validate a small RAG pipeline around LightningParse.

The agent's immediate objective is NOT to build a production platform.

The immediate objective is:

> Parse one difficult PDF, understand the extracted structure, build a minimal RAG pipeline, and validate it using five manually authored questions.

## 2. Core Principles

### Principle 1 — Small first

Do not expand the scope without a concrete reason.

If the current phase can be completed without a new dependency, framework, or abstraction, do not add one.

### Principle 2 — Inspect before abstracting

Always inspect raw LightningParse output before designing the chunking layer.

Do not assume the parser's schema.

### Principle 3 — Keep the pipeline transparent

Prefer direct Python implementations.

Initial flow:

```text
LightningParse
 -> Chunking
 -> Sentence Transformers
 -> FAISS
 -> LLM
```

Do not introduce LangChain in v0.1.

### Principle 4 — Preserve provenance

Never discard:

- Source filename
- Page number
- Section identifier when available
- Chunk identity

Every retrieved result must be traceable to its source.

### Principle 5 — No invented parser behavior

Do not assume LightningParse supports a feature.

If behavior is unclear:

1. Inspect the installed package.
2. Inspect its documentation/source if available.
3. Run a small experiment.
4. Record the result.

### Principle 6 — Separate failure stages

When an answer is incorrect, determine whether the failure came from:

```text
PDF extraction
    ↓
Structure detection
    ↓
Chunking
    ↓
Embedding
    ↓
Retrieval
    ↓
LLM generation
```

Do not immediately blame the LLM.

## 3. Phase Discipline

The agent should work in the current phase only.

Before implementing a later phase, verify that the current phase's deliverable exists.

Do not build:

- Automated benchmarks
- Parser comparisons
- Recall@k
- Production APIs
- Agents
- Complex UI

during the initial validation.

## 4. Coding Rules

- Keep modules small.
- Prefer readable Python.
- Avoid unnecessary classes.
- Use type hints where useful.
- Handle errors explicitly.
- Do not silently swallow extraction failures.
- Keep configuration separate from logic.
- Make experiments reproducible.
- Log useful intermediate information.

## 5. RAG Rules

The LLM must be instructed to answer using retrieved context.

If the context does not contain enough evidence, the model should say that the answer cannot be determined from the retrieved material.

The system should not encourage hallucination.

## 6. Evaluation Rules

For v0.1, evaluation is manual.

Each question should have:

- Question
- Expected answer
- Expected page
- Retrieved chunks
- Generated answer
- Correctness
- Citation correctness

Do not invent automated accuracy scores from an insufficient sample.

## 7. Agent Output Expectations

After completing a task, report:

### Changed

What files/code were changed.

### Verified

What was actually tested.

### Result

Whether the test passed.

### Issues

Any unresolved problems.

Never claim something works unless it was actually executed or verified.

## 8. Definition of Done

v0.1 is done when:

- One synthetic PDF works.
- One real book PDF works.
- Five questions can be evaluated.
- Retrieved evidence is inspectable.
- Answers can be traced to source pages.
- Major parser/RAG failures are documented.
