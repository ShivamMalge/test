"""
LightningParse vs pypdf benchmark.

Follows the methodology in benchmark.md:
  - parsing latency is measured for the PARSER ALONE, with a warm-up run and
    repetitions (benchmark.md section 8), never as end-to-end RAG latency;
  - retrieval / answer / citation quality are graded against human-authored
    ground truth recorded in GOLD below (sections 5-7);
  - answer correctness is graded independently of citation correctness.

Everything except the parser is held constant between the two arms.
"""

import sys
import os
import re
import time
import json
import timeit
import statistics

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.pipeline import LightningRAG
from src.parser_registry import get_parser

SYNTHETIC_PDF = "data/synthetic/lightningparse_test_document_TRUE_2COL.pdf"
VTU_PDF = "data/books/VTU 7th Sem Study Strategy.pdf"

# Order matters only for readability of the printed report.
PARSER_TYPES = ["pypdf", "pdfplumber", "pymupdf", "lightningparse"]

PARSE_REPS = 5          # timed repetitions per document, after one warm-up run
QUESTION_DELAY_S = 5    # spacing between LLM calls to stay under rate limits

ABSTENTION_MARKER = "cannot be determined"

# The prompt asks for one specific refusal sentence, but a grounded model refuses
# in several equivalent ways. Grading only the literal phrase scores a correct
# abstention as a hallucination, so any of these count as a refusal.
ABSTENTION_PATTERNS = re.compile(
    r"cannot be determined|cannot be answered|can not be determined"
    r"|does not contain|do not contain|doesn't contain"
    r"|does not provide|does not specify|does not mention|does not discuss"
    r"|no information|not mentioned|not specified|not addressed|not provided"
)


# ---------------------------------------------------------------------------
# Ground truth
#
# gold_pages holds every page that actually carries the evidence, verified by
# reading the extracted text of both documents. answer_keys is a list of groups;
# an answer counts as correct only when it matches at least one variant in
# EVERY group, so grading looks at the answer itself rather than at retrieval.
# ---------------------------------------------------------------------------
GOLD = {
    "synthetic": {
        "pdf": SYNTHETIC_PDF,
        "questions": [
            {
                "id": "syn_1",
                "q": "Which stage of the pipeline can lose evidence before the embedding model ever sees it?",
                "expected_answer": "Extraction or chunking can discard or corrupt evidence before retrieval begins.",
                # The 'Continuation and Test Notes' column repeats verbatim on every page.
                "gold_pages": [1, 2, 3, 4, 5, 6, 7, 8],
                "answer_keys": [["extraction", "extract"], ["chunking", "chunk"]],
            },
            {
                "id": "syn_2",
                "q": "Why do boundaries matter in a layered design according to the document?",
                "expected_answer": "Boundaries make assumptions visible; a layer can expose its guarantees "
                                   "without exposing its implementation, so components can be replaced.",
                "gold_pages": [1],
                "answer_keys": [["assumption"], ["visible"]],
            },
            {
                "id": "syn_3",
                "q": "Why is semantic similarity not the same thing as factual correctness?",
                "expected_answer": "A retrieved passage can be topically related but still fail to contain the answer.",
                "gold_pages": [4],
                "answer_keys": [["topically", "topical", "related"], ["contain"]],
            },
            {
                "id": "syn_4",
                "q": "According to the test table, which system achieved the highest recall and what was its value?",
                "expected_answer": "Cirrus, with a recall of 95.4%.",
                "gold_pages": [5],
                "answer_keys": [["cirrus"], ["95.4"]],
            },
            {
                "id": "syn_5",
                "q": "How does the document suggest keyword retrieval and semantic retrieval interact?",
                "expected_answer": "They complement each other: exact terms help for identifiers, numbers and "
                                   "names, embeddings help when query wording differs, and a production system "
                                   "may combine both signals.",
                "gold_pages": [4],
                "answer_keys": [["complement", "combine", "hybrid", "both signals"]],
            },
        ],
    },
    "vtu": {
        "pdf": VTU_PDF,
        "questions": [
            {
                "id": "vtu_1",
                "q": "What is the overall study strategy recommended?",
                "expected_answer": "An active, output-oriented approach that avoids passive reading, tackling "
                                   "modules by conceptual dependency and return on investment rather than by "
                                   "sequential numbering.",
                "gold_pages": [4],
                "answer_keys": [["active"], ["output", "passive"]],
            },
            {
                "id": "vtu_2",
                "q": "How should one prepare for the internal exams?",
                # Negative control: the document only covers the Semester End Examination.
                "expected_answer": ABSTENTION_MARKER,
                "gold_pages": [],
                "unanswerable": True,
            },
            {
                "id": "vtu_3",
                # Previously graded as unanswerable, which was wrong: pages 4-5 name
                # question papers, formula sheets and compressed notes. Parsers that
                # surfaced them were being penalised for the better answer.
                "q": "What resources are suggested for studying?",
                "expected_answer": "Historical VTU question papers, single-sheet formula and syntax "
                                   "notes, and skeletal diagrams; notes are compressed cognitive "
                                   "triggers rather than transcriptions of textbooks.",
                "gold_pages": [4, 5],
                "answer_keys": [["question paper", "formula", "note", "diagram"]],
            },
            {
                "id": "vtu_6",
                # Negative control: verified absent. "attendance", "viva", "laboratory"
                # and "placement" each occur zero times in the document.
                "q": "What is the minimum attendance requirement to sit for the exam?",
                "expected_answer": ABSTENTION_MARKER,
                "gold_pages": [],
                "unanswerable": True,
            },
            {
                "id": "vtu_4",
                "q": "How is the syllabus divided?",
                "expected_answer": "Into five modules per subject (BCS702 and BCS703), analysed and ranked "
                                   "individually.",
                "gold_pages": [1, 2, 3],
                "answer_keys": [["module"]],
            },
            {
                "id": "vtu_5",
                "q": "What is the advice regarding previous year question papers?",
                "expected_answer": "Review historical VTU question papers about two weeks before the exam to "
                                   "extract patterns and identify recurring themes.",
                "gold_pages": [5],
                "answer_keys": [["recurring", "pattern", "theme"]],
            },
        ],
    },
}


def _normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower())


def grade_answer(answer: str, question: dict) -> bool:
    """
    Grades the generated answer against human-authored keys, not against retrieval.

    An unanswerable question is correct only when the model refuses. An answerable
    one is correct only when every key group is matched — a refusal simply fails to
    match, so the two cases never need to test the same condition twice.
    """
    normalised = _normalise(answer)

    if question.get("unanswerable"):
        return bool(ABSTENTION_PATTERNS.search(normalised))

    return all(
        any(variant in normalised for variant in group)
        for group in question["answer_keys"]
    )


def measure_parse_latency(parser_type: str, pdf_path: str) -> dict:
    """
    Times the parser in isolation: no chunking, embedding or indexing.

    Every parser is timed through the same registry callable the pipeline uses,
    so no arm gets a hand-written fast path. One warm-up run is discarded, then
    PARSE_REPS timed runs are recorded.
    """
    parse = get_parser(parser_type)

    def run():
        doc = parse(pdf_path)
        pages = doc.get("pages", [])
        blocks = [b for p in pages for b in p.get("blocks", [])]
        chars = sum(len(b.get("text") or "") for b in blocks)
        table_chars = sum(
            len(str(cell))
            for b in blocks
            for row in (b.get("rows") or [])
            for cell in row
        )
        tables = sum(1 for b in blocks if b.get("type") == "table")
        return len(pages), chars + table_chars, len(blocks), tables

    try:
        run()  # warm-up, discarded
    except Exception as exc:
        return {"failed": True, "error": f"{type(exc).__name__}: {exc}"}

    timings = []
    pages = chars = blocks = tables = 0
    for _ in range(PARSE_REPS):
        start = timeit.default_timer()
        pages, chars, blocks, tables = run()
        timings.append(timeit.default_timer() - start)

    median = statistics.median(timings)
    return {
        "failed": False,
        "pages": pages,
        "chars_extracted": chars,
        "blocks_extracted": blocks,
        "tables_extracted": tables,
        "reps": PARSE_REPS,
        "mean_ms": round(statistics.mean(timings) * 1000, 2),
        "median_ms": round(median * 1000, 2),
        "min_ms": round(min(timings) * 1000, 2),
        "max_ms": round(max(timings) * 1000, 2),
        "stdev_ms": round(statistics.stdev(timings) * 1000, 2) if len(timings) > 1 else 0.0,
        "pages_per_sec": round(pages / median, 2) if median > 0 else None,
    }


def evaluate_questions(rag, doc_key: str, records: list) -> dict:
    """Scores retrieval, answer and citation quality for one document's questions."""
    spec = GOLD[doc_key]
    expected_source = os.path.basename(spec["pdf"])
    questions = spec["questions"]

    answerable = [q for q in questions if not q.get("unanswerable")]
    unanswerable = [q for q in questions if q.get("unanswerable")]

    recall_hits = 0
    citation_hits = 0
    answer_hits = 0
    abstention_hits = 0

    for question in questions:
        print(f"\n  [{question['id']}] {question['q']}")
        result = rag.ask(question["q"], top_k=5)
        answer = result["answer"]

        # Retrieved locations, scoped to the document the evidence lives in.
        retrieved = [(os.path.basename(s["source"]), s["page"]) for s in result["sources"]]
        gold_hit = any(
            src == expected_source and page in question["gold_pages"]
            for src, page in retrieved
        )

        answer_correct = grade_answer(answer, question)

        if question.get("unanswerable"):
            # No page can be cited, so abstention is the only correct behaviour.
            citation_correct = answer_correct
            if answer_correct:
                abstention_hits += 1
                answer_hits += 1
        else:
            if gold_hit:
                recall_hits += 1
            citation_correct = gold_hit
            if citation_correct:
                citation_hits += 1
            if answer_correct:
                answer_hits += 1

        records.append({
            "document": doc_key,
            "question_id": question["id"],
            "question": question["q"],
            "expected_answer": question["expected_answer"],
            "gold_pages": question["gold_pages"],
            "retrieved": [{"source": s, "page": p} for s, p in retrieved],
            "generated_answer": answer.strip(),
            "answer_correct": answer_correct,
            "citation_correct": citation_correct,
        })

        print(f"      retrieved: {retrieved}")
        print(f"      answer_correct={answer_correct} citation_correct={citation_correct}")

        time.sleep(QUESTION_DELAY_S)

    return {
        # Recall is defined only over questions that have evidence to retrieve.
        "recall_at_5": f"{recall_hits}/{len(answerable)}",
        "answer_correctness": f"{answer_hits}/{len(questions)}",
        "citation_correctness": f"{citation_hits}/{len(answerable)}",
        "abstention": f"{abstention_hits}/{len(unanswerable)}" if unanswerable else "n/a",
        "_counts": {
            "recall": (recall_hits, len(answerable)),
            "answer": (answer_hits, len(questions)),
            "citation": (citation_hits, len(answerable)),
        },
    }


def main():
    pdfs = [SYNTHETIC_PDF, VTU_PDF]
    results = {}
    transcript = {}

    for parser_type in PARSER_TYPES:
        print(f"\n{'=' * 60}\nBenchmarking {parser_type}\n{'=' * 60}")
        results[parser_type] = {"aggregate": {}, "synthetic": {}, "vtu": {}}
        records = []

        # --- Stage 1: parser-only latency -----------------------------------
        total_median_s = 0.0
        total_pages = 0
        failures = 0
        for pdf_path in pdfs:
            key = "synthetic" if "synthetic" in pdf_path else "vtu"
            print(f"\nTiming parser on {pdf_path} ({PARSE_REPS} reps + warm-up)...")
            timing = measure_parse_latency(parser_type, pdf_path)
            results[parser_type][key]["parsing"] = timing

            if timing["failed"]:
                failures += 1
                print(f"  EXTRACTION FAILED: {timing['error']}")
                continue

            total_median_s += timing["median_ms"] / 1000
            total_pages += timing["pages"]
            print(f"  median={timing['median_ms']}ms  min={timing['min_ms']}ms  "
                  f"max={timing['max_ms']}ms  pages/s={timing['pages_per_sec']}  "
                  f"chars={timing['chars_extracted']}  blocks={timing['blocks_extracted']}  "
                  f"tables={timing['tables_extracted']}")

        # --- Stage 2: ingest both documents into one index ------------------
        rag = LightningRAG(parser_type=parser_type)
        ingest_start = timeit.default_timer()
        for pdf_path in pdfs:
            rag.ingest_document(pdf_path)
        ingest_s = timeit.default_timer() - ingest_start
        indexed_chunks = rag.retriever.index.ntotal if rag.retriever.index else 0
        print(f"\nIndexed {indexed_chunks} chunks from {len(pdfs)} documents "
              f"in {ingest_s:.2f}s (parse + chunk + embed + index).")

        # --- Stage 3: quality evaluation ------------------------------------
        print(f"\nEvaluating VTU questions with {parser_type}...")
        vtu_metrics = evaluate_questions(rag, "vtu", records)
        print(f"\nEvaluating synthetic questions with {parser_type}...")
        syn_metrics = evaluate_questions(rag, "synthetic", records)

        results[parser_type]["vtu"].update({k: v for k, v in vtu_metrics.items() if k != "_counts"})
        results[parser_type]["synthetic"].update({k: v for k, v in syn_metrics.items() if k != "_counts"})

        def combined(metric):
            a, b = vtu_metrics["_counts"][metric], syn_metrics["_counts"][metric]
            return f"{a[0] + b[0]}/{a[1] + b[1]}"

        results[parser_type]["aggregate"] = {
            "parse_latency_median_total_ms": round(total_median_s * 1000, 2),
            "pages_per_sec": round(total_pages / total_median_s, 2) if total_median_s > 0 else None,
            "pages": total_pages,
            "extraction_failures": failures,
            "indexed_chunks": indexed_chunks,
            "ingest_total_s": round(ingest_s, 2),
            "recall_at_5": combined("recall"),
            "answer_correctness": combined("answer"),
            "citation_correctness": combined("citation"),
        }
        transcript[parser_type] = records

    print("\n\n--- BENCHMARK RESULTS ---")
    print(json.dumps(results, indent=2))

    with open("benchmark_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    with open("benchmark_transcript.json", "w", encoding="utf-8") as f:
        json.dump(transcript, f, indent=2)

    tables = render_markdown(results)
    with open("benchmark_table.md", "w", encoding="utf-8") as f:
        f.write(tables)
    print("\n" + tables)
    print("Wrote benchmark_results.json, benchmark_transcript.json and benchmark_table.md")


def render_markdown(results: dict) -> str:
    """Renders the result tables in markdown, so the README is never hand-transcribed."""
    parsers = [p for p in PARSER_TYPES if p in results]
    header = "| Metric | " + " | ".join(parsers) + " |"
    divider = "| :--- | " + " | ".join("---:" for _ in parsers) + " |"

    def row(label, fn):
        return "| " + label + " | " + " | ".join(str(fn(results[p])) for p in parsers) + " |"

    def doc_timing(doc, field):
        return lambda r: r[doc]["parsing"].get(field, "-")

    perf = [
        "### Parsing performance", "", header, divider,
        row("**Parse latency, median total (20 pages)**",
            lambda r: f"{r['aggregate']['parse_latency_median_total_ms']} ms"),
        row("Synthetic — median ms", doc_timing("synthetic", "median_ms")),
        row("Synthetic — min / max", lambda r: f"{r['synthetic']['parsing']['min_ms']} / {r['synthetic']['parsing']['max_ms']}"),
        row("VTU — median ms", doc_timing("vtu", "median_ms")),
        row("VTU — min / max", lambda r: f"{r['vtu']['parsing']['min_ms']} / {r['vtu']['parsing']['max_ms']}"),
        row("**Pages/sec**", lambda r: r["aggregate"]["pages_per_sec"]),
        row("Blocks extracted", lambda r: r["synthetic"]["parsing"]["blocks_extracted"]
                                          + r["vtu"]["parsing"]["blocks_extracted"]),
        row("Tables extracted", lambda r: r["synthetic"]["parsing"]["tables_extracted"]
                                          + r["vtu"]["parsing"]["tables_extracted"]),
        row("Characters extracted", lambda r: r["synthetic"]["parsing"]["chars_extracted"]
                                              + r["vtu"]["parsing"]["chars_extracted"]),
        row("Extraction failures", lambda r: r["aggregate"]["extraction_failures"]),
        row("Full ingest (parse+chunk+embed+index)", lambda r: f"{r['aggregate']['ingest_total_s']} s"),
    ]

    quality = [
        "", "### Downstream RAG quality", "", header, divider,
        row("**Retrieval Recall@5**", lambda r: r["aggregate"]["recall_at_5"]),
        row("**Answer correctness**", lambda r: r["aggregate"]["answer_correctness"]),
        row("**Citation correctness**", lambda r: r["aggregate"]["citation_correctness"]),
        row("Correct abstention (unanswerable)", lambda r: r["vtu"]["abstention"]),
        row("Indexed chunks", lambda r: r["aggregate"]["indexed_chunks"]),
    ]

    return "\n".join(perf + quality) + "\n"


if __name__ == "__main__":
    main()
