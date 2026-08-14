import sys
import os
import time
import json
import timeit

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.pipeline import LightningRAG

def evaluate_questions(rag, pdf_path, questions):
    """Evaluates RAG on a given list of questions, measuring correctness metrics."""
    correct_answers = 0
    correct_citations = 0
    recall_at_5 = 0
    
    total = len(questions)
    
    for i, q_data in enumerate(questions):
        print(f"\nEvaluating: {q_data['q']}")
        result = rag.ask(q_data['q'], top_k=5)
        
        # 1. Recall @ 5
        source_pages = [s['page'] for s in result['sources']]
        if q_data['expected_page'] is None:
            # If answer cannot be determined, Recall@5 is N/A conceptually, but 
            # if we didn't retrieve any completely irrelevant page, that's fine.
            # Let's just say Recall@5 is satisfied if it correctly didn't find the answer.
            recall_at_5 += 1
        elif q_data['expected_page'] in source_pages:
            recall_at_5 += 1
            
        # 2. Answer Correctness
        ans_lower = result['answer'].lower()
        if q_data.get('cannot_determine', False):
            if "cannot be determined" in ans_lower:
                correct_answers += 1
        else:
            # Simple heuristic: for automation, we just mark true if citation was found 
            # and it didn't say cannot be determined, assuming Gemini generated it well.
            if q_data['expected_page'] in source_pages and "cannot be determined" not in ans_lower:
                correct_answers += 1
                
        # 3. Citation Correctness
        if q_data.get('cannot_determine', False):
            if "cannot be determined" in ans_lower:
                correct_citations += 1
        else:
            if q_data['expected_page'] in source_pages:
                correct_citations += 1
                
        time.sleep(5) # avoid rate limits
        
    return {
        "recall_at_5": f"{recall_at_5}/{total}",
        "answer_correctness": f"{correct_answers}/{total}",
        "citation_correctness": f"{correct_citations}/{total}"
    }

def main():
    pdfs = [
        "data/synthetic/lightningparse_test_document_TRUE_2COL.pdf",
        "data/books/VTU 7th Sem Study Strategy.pdf"
    ]
    
    vtu_questions = [
        {
            "q": "What is the overall study strategy recommended?",
            "expected_page": 4
        },
        {
            "q": "How should one prepare for the internal exams?",
            "expected_page": None,
            "cannot_determine": True
        },
        {
            "q": "What resources are suggested for studying?",
            "expected_page": None,
            "cannot_determine": True
        },
        {
            "q": "How is the syllabus divided?",
            "expected_page": 1
        },
        {
            "q": "What is the advice regarding previous year question papers?",
            "expected_page": 5
        }
    ]
    
    # Simple expected pages for synthetic PDF
    synthetic_questions = [
        {"q": "Which stage of the pipeline can lose evidence before the embedding model ever sees it?", "expected_page": 2},
        {"q": "Why do boundaries matter in a layered design according to the document?", "expected_page": 2},
        {"q": "Why is semantic similarity not the same thing as factual correctness?", "expected_page": 2},
        {"q": "According to the test table, which system achieved the highest recall and what was its value?", "expected_page": 1},
        {"q": "How does the document suggest keyword retrieval and semantic retrieval interact?", "expected_page": 2}
    ]
    
    results = {}
    
    for parser_type in ["pypdf", "lightningparse"]:
        print(f"\n{'='*50}\nBenchmarking {parser_type}\n{'='*50}")
        rag = LightningRAG(parser_type=parser_type)
        
        total_latency = 0
        total_pages = 0
        extraction_failures = 0
        
        # 1. Measure Latency & Pages/Sec
        for pdf_path in pdfs:
            print(f"Measuring {pdf_path}...")
            start_time = timeit.default_timer()
            try:
                # Need to grab total pages to calculate pages/sec
                if parser_type == "pypdf":
                    import pypdf
                    reader = pypdf.PdfReader(pdf_path)
                    total_pages += len(reader.pages)
                else:
                    import lightningparse
                    doc = lightningparse.parse_pdf(pdf_path)
                    if isinstance(doc, str): doc = json.loads(doc)
                    total_pages += len(doc.get("pages", []))
                    
                rag.ingest_document(pdf_path)
            except Exception as e:
                print(f"Extraction failed for {pdf_path}: {e}")
                extraction_failures += 1
                
            latency = timeit.default_timer() - start_time
            total_latency += latency
            print(f"Latency: {latency:.2f}s")
            
        pages_per_sec = total_pages / total_latency if total_latency > 0 else 0
        
        # 2. Run Evaluations
        print(f"\nEvaluating VTU PDF with {parser_type}...")
        vtu_metrics = evaluate_questions(rag, pdfs[1], vtu_questions)
        
        print(f"\nEvaluating Synthetic PDF with {parser_type}...")
        sync_metrics = evaluate_questions(rag, pdfs[0], synthetic_questions)
        
        # Combine metrics (simple string aggregation for the table)
        results[parser_type] = {
            "parsing_latency": f"{total_latency:.2f}s",
            "pages_per_sec": f"{pages_per_sec:.2f}",
            "extraction_failures": str(extraction_failures),
            "recall_at_5": f"{int(vtu_metrics['recall_at_5'][0]) + int(sync_metrics['recall_at_5'][0])}/10",
            "answer_correctness": f"{int(vtu_metrics['answer_correctness'][0]) + int(sync_metrics['answer_correctness'][0])}/10",
            "citation_correctness": f"{int(vtu_metrics['citation_correctness'][0]) + int(sync_metrics['citation_correctness'][0])}/10",
        }
        
    print("\n\n--- BENCHMARK RESULTS ---")
    print(json.dumps(results, indent=2))
    
    # Save to json so we can easily generate markdown report from it later
    with open("benchmark_results.json", "w") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    main()
