# LightningRAG

LightningRAG is a minimal, transparent Retrieval-Augmented Generation (RAG) pipeline designed around the [LightningParse](https://github.com/Lightning-AI/lightningparse) PDF extraction library. 

This project serves as a V0.1 validation environment to demonstrate that by preserving semantic layout boundaries and utilizing robust page/section provenance during parsing, a downstream RAG pipeline can achieve higher correctness and fewer hallucinations.

## Core Architecture

The pipeline avoids heavy frameworks like LangChain in favor of transparent, debuggable Python logic:

1. **Extraction**: `LightningParse` (layout-aware, block-level extraction), or any of the `pypdf` / `pdfplumber` / `pymupdf` baselines, selected by name through `src/parser_registry.py`.
2. **Chunking**: Section-aware hierarchical chunking that preserves semantic boundaries. Table blocks are rendered to markdown rows, and space restoration via `wordninja` is applied.
3. **Embedding**: `all-MiniLM-L6-v2` (SentenceTransformers) running locally.
4. **Retrieval**: Hybrid `FAISS` (dense) + `BM25Plus` (lexical), fused with Reciprocal Rank Fusion.
5. **Generation**: `google/gemini-2.5-flash` via OpenRouter, with strict grounding prompts to prevent hallucination.

Every retrieved chunk strictly preserves its source filename and page number, enabling full provenance tracking for the LLM.

## Benchmark: four PDF parsers

The primary goal of this benchmark is to establish **how fast LightningParse is** under a fair, parser-only measurement, with downstream RAG quality tracked alongside so that a speed claim can never be bought with silent extraction loss.

We benchmarked `lightningparse==0.5.0` against three Python baselines, chosen to cover the range rather than only the weakest option:

| Parser | Why it is here |
| :--- | :--- |
| **pypdf** | Naive baseline: raw text streams, no layout model, no table API. |
| **pdfplumber** | Layout-aware, built on `pdfminer.six`, with a real `extract_tables()` API. |
| **pymupdf** (fitz) | Block-level extraction plus `find_tables()`; the closest structural analogue to LightningParse. AGPL-licensed, unlike the others. |
| **lightningparse** | The parser under test. |

Everything except the parser is held constant: same documents, chunker, embedding model, index, retrieval configuration, and questions. All four are driven through one registry (`src/parser_registry.py`) that returns the same block schema, and the benchmark times **that same callable** — no arm gets a hand-written fast path. Each parser is used in its best reasonable configuration: where a table API exists it is used, and table regions are excluded from the text pass so their content is not counted twice.

The corpus is two documents, 20 pages total:
1. **VTU 7th Sem Study Strategy** (12 pages): text-heavy, with six module comparison tables.
2. **Synthetic Document** (8 pages): two-column technical paper with a benchmark table. Parsed as distributed — LightningParse reads its `ASCII85Decode` streams natively (`tier: digital`, no OCR fallback), so no pre-cleaning is applied.

**Parsing latency is measured for the parser alone** — one warm-up run, then 5 timed repetitions, no chunking, embedding, or indexing inside the timed region.

### Parsing performance

| Metric | pypdf | pdfplumber | pymupdf | lightningparse |
| :--- | ---: | ---: | ---: | ---: |
| **Parse latency, median total (20 pages)** | 3328.9 ms | 8186.1 ms | 4640.8 ms | **68.6 ms** |
| Synthetic — median ms | 181.4 | 1514.6 | 1056.3 | **12.9** |
| Synthetic — min / max | 165.8 / 192.8 | 1191.2 / 1596.7 | 1026.7 / 1391.3 | 10.9 / 16.6 |
| VTU — median ms | 3147.5 | 6671.5 | 3584.4 | **55.7** |
| VTU — min / max | 3042.4 / 3824.1 | 6462.2 / 7247.3 | 2938.8 / 3958.4 | 49.5 / 76.9 |
| **Pages/sec** | 6.0 | 2.4 | 4.3 | **291.5** |
| Blocks extracted | 20 | 26 | 191 | 1168 |
| **Tables extracted** | 0 | **7** | **7** | 1 |
| Characters extracted | 66480 | 58366 | 58835 | 53380 |
| Extraction failures | 0 | 0 | 0 | 0 |
| Full ingest (parse+chunk+embed+index) | 5.67 s | 11.15 s | 6.12 s | **2.95 s** |

**The headline speed ratio needs a caveat.** Most of PyMuPDF's time is table detection, not text extraction:

| PyMuPDF configuration | Synthetic | VTU | Total |
| :--- | ---: | ---: | ---: |
| `get_text("blocks")` only (no tables) | 21.6 ms | 75.0 ms | **96.6 ms** |
| with `find_tables()` (as benchmarked) | 1056.3 ms | 3584.4 ms | 4640.8 ms |

So LightningParse is ~68x faster than PyMuPDF *with table detection*, but only about **1.4x faster than PyMuPDF's text extraction alone** — while still doing its own structure and table detection within that budget. pdfplumber is slow either way, because the cost is `pdfminer`, not tables. PyPDF's cost is genuinely in extraction, not file opening (`PdfReader()` 3.6 ms, `extract_text()` the remainder). LightningParse's self-reported `parse_time_ms` matches the externally measured figure, so the JSON round-trip is not hiding work.

**Absolute latencies are only comparable within a single run.** This machine measured LightningParse at 50 ms in an earlier session and 69 ms here, for identical parser output. An interleaved A/B of 0.4.1 against 0.5.0 run back-to-back gave 70.3 / 75.3 / 72.2 ms versus 66.1 / 68.8 / 73.3 ms — indistinguishable, so **0.5.0 did not change parsing speed**. Only ratios measured inside one run should be quoted; PyMuPDF's text-only figure is the exception, landing at 96.5 and 96.6 ms across both sessions.

### Downstream RAG quality

Eleven questions with human-authored expected answers and verified gold pages. Two are negative controls whose subject matter is verifiably absent from both documents; recall and citation are scored over the nine answerable questions, answers over all eleven.

> **Provenance:** these quality scores were measured under 0.4.1 and have **not** been re-measured under 0.5.0 — the OpenRouter key ran out of credits mid-run (HTTP 402). Parser table output is byte-identical between the two versions, but 0.5.0 changed `section_id` classification, which shifts chunk boundaries (86 chunks to 84), so these numbers could move by a question on re-measurement. The parsing latencies above *were* re-measured under 0.5.0. `benchmark_results.json` records this under `_meta`.

| Metric | pypdf | pdfplumber | pymupdf | lightningparse |
| :--- | ---: | ---: | ---: | ---: |
| **Retrieval Recall@5** | 9/9 | 9/9 | 9/9 | 9/9 |
| **Answer correctness** | 10/11 | 10/11 | 9/11 | 9/11 |
| **Citation correctness** | 9/9 | 9/9 | 9/9 | 9/9 |
| Correct abstention (unanswerable) | 2/2 | 2/2 | 2/2 | 2/2 |
| Indexed chunks | 83 | 74 | 76 | 86 |

**Key Takeaways:**
- **Speed is where LightningParse wins decisively.** In this run it is 49x faster than pypdf, 119x faster than pdfplumber, and 68x faster than PyMuPDF-with-tables — or ~1.4x against PyMuPDF's text-only path, which is the honest like-for-like figure since that path does no table detection. 0.5.0 is no faster or slower than 0.4.1; an interleaved A/B put them within noise of each other.
- **Downstream quality is a wash on this corpus.** All four parsers score identical recall (9/9), identical citation accuracy (9/9), and full marks on both hallucination controls. Answer correctness spans 9/11 to 10/11 — a one-question spread on an eleven-question set, which is well inside noise. **This benchmark cannot distinguish these parsers on RAG quality**; it can only distinguish them on speed and on specific mechanical failures.
- **Table extraction is still the open limitation as of 0.5.0.** It was expected to land in this release and did not: the parser's table output is byte-for-byte identical to 0.4.1. The benchmark quantifies the gap rather than discovering it. pdfplumber and PyMuPDF each recovered 7 tables with intact header rows; LightningParse recovered 1, and that one was missing its header and first data row (they were emitted as ordinary text blocks) and had a cell of adjacent prose bleeding into it. The downstream consequence is concrete: the resulting header-less table chunk carries no term matching a query about "recall", ranks 46th of 86, and the model answered "Atlas, 88.7%" instead of "Cirrus, 95.4%". Both table-capable parsers answered it correctly. On the VTU document LightningParse found **zero** of the six module tables the other two recovered cleanly. See the [0.5.0 scorecard](#050-scorecard).
- **Extracted character counts are not directly comparable.** LightningParse returns 30,059 characters for the VTU document against pypdf's 42,676, largely because it drops inter-word spaces there (`StrategicAcademicMastery:An`). The chunker repairs this with `wordninja`.

### 0.5.0 scorecard

The 0.4.1 numbers were published as acceptance criteria for the table work planned in 0.5.0. Re-running against `lightningparse==0.5.0` gives:

| Signal | 0.4.1 baseline | 0.5.0 target | 0.5.0 actual | |
| :--- | :--- | :--- | :--- | :--- |
| Tables extracted (20-page corpus) | 1 | 7 | 1 | not met |
| VTU module tables | 0 of 6 | 6 of 6 | 0 of 6 | not met |
| Header row retained | no | `System / Accuracy / Precision / Recall` | no | not met |
| Cell contamination | prose leaked into the Borealis row | none | unchanged | not met |
| `syn_4` answer | "Atlas, 88.7%" | "Cirrus, 95.4%" | not re-measured (credits) | — |
| Table chunk retrieval rank | 46 of 86 | top 5 | unchanged | not met |
| Parse latency (the guard) | — | no material regression | within noise of 0.4.1 | met |

**The table work did not land in 0.5.0.** Diffing full parser output across the two versions shows the table blocks are byte-for-byte identical — same single table, same three rows, same missing header, same contaminated cell, same zero tables on the VTU document.

What 0.5.0 *did* change, verified the same way:

- **`page_width` and `page_height`** added to every page object.
- **Better section classification.** Blocks previously misfiled as `section_id: "header"` are now `body` with `block_role: "heading"`. Synthetic `header` blocks fell 60 to 32; VTU 2 to 0. This is a real improvement — the synthetic document's right-hand column was being labelled a page header — and it shifts chunk boundaries slightly (86 chunks to 84).
- **No speed change**, per the interleaved A/B above.

The criteria above stand unchanged as the target for whichever release carries the table fix.

### Limitations

- Eleven questions over two documents is too small to resolve one-question differences. Treat the quality table as "no measurable difference", not as a ranking.
- The quality table was last measured under 0.4.1. Under 0.5.0 only the parsing latencies were re-measured; see the provenance note above.
- Answers are graded by required-keyword matching against human-authored expected answers. This is deterministic and auditable, but it rewards phrasing that contains the key terms.
- Both documents are digital-tier. No scanned or OCR-requiring document is exercised, so the OCR paths of all four parsers are untested.
- `find_tables()` and `extract_tables()` are used at default settings; tuning them would change both the latency and the table counts.

### A note on pipeline symmetry

All arms run the same chunker, embedding model, index, retrieval configuration, and prompts; only the parser function differs. But *identical code is not identical behaviour*: the chunker was originally written against PyPDF-shaped output, which is one block per page, and it handled LightningParse's line-level blocks (467 and 701 of them) badly. Two defects were fixed before the numbers above were recorded:

- Blocks were joined with a blank line, so every visual line became its own paragraph — 418 and 658 spurious separators in the LightningParse arm versus zero in the PyPDF arm. Blocks are now joined by continuation (space), sentence boundary (newline), or hyphenation.
- Table blocks were merged into whatever prose preceded them, which stranded the benchmark table's rows inside a chunk about the right-hand column. Tables are now emitted as their own chunk.

Both fixes are parser-agnostic and left the head-to-head result unchanged, which is the reason for reporting them: the remaining gap is attributable to table extraction, not to chunker bias.

Two grading defects were also corrected, both of which had been penalising the *better* answer:

- Abstention was detected by one literal phrase (`"cannot be determined"`), so a model that correctly refused in different words — "the provided document does not contain information on…" — was scored as a hallucination. Any of several refusal phrasings now count.
- The question "What resources are suggested for studying?" was graded as unanswerable, but pages 4-5 do name question papers, formula sheets and compressed notes. Parsers that surfaced them were being marked wrong for answering correctly. It is now an answerable question, and a verified-absent control ("minimum attendance requirement" — zero occurrences of *attendance*, *viva*, *laboratory* or *placement* in the document) replaces it as the second negative control.

Raw per-question records — retrieved locations and generated answers for every question — are written to `benchmark_transcript.json`, and the metrics to `benchmark_results.json`.

## Setup Instructions

### Prerequisites
- Python 3.11+
- An OpenRouter API key (generation is routed to `google/gemini-2.5-flash` through OpenRouter)

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
Create a `.env` file in the root directory and add your API key. Multiple comma-separated keys are supported; the generator rotates to the next one on a 402 or 429 response:
```env
OPENROUTER_API_KEY=your-api-key-here
```

## Running the Project

### Running the Evaluation Suite
To run the automated RAG evaluation against the pre-authored grading criteria:
```bash
python tests/evaluate_rag.py
python tests/evaluate_vtu.py
```

### Running the Benchmark
To run the latency and quality benchmark across all four parsers:
```bash
python tests/benchmark.py
```
This makes 44 LLM calls (11 questions x 4 parsers) and writes `benchmark_results.json` (metrics), `benchmark_transcript.json` (per-question records: retrieved locations and generated answers), and `benchmark_table.md` (the markdown tables reproduced above, generated from the results rather than hand-transcribed).

Ground truth lives in the `GOLD` dictionary at the top of `tests/benchmark.py`; the parsers under test are listed in `PARSER_TYPES`. To add a parser, write a wrapper returning the shared block schema and register it in `src/parser_registry.py`.

### Inspecting the Parser
To see the raw JSON output of LightningParse for a specific document:
```bash
python inspect_parser.py
```
