### Parsing performance

| Metric | pypdf | pdfplumber | pymupdf | lightningparse |
| :--- | ---: | ---: | ---: | ---: |
| **Parse latency, median total (20 pages)** | 3138.26 ms | 7656.4 ms | 3290.11 ms | 50.25 ms |
| Synthetic — median ms | 118.15 | 1365.62 | 1062.4 | 10.33 |
| Synthetic — min / max | 117.93 / 127.28 | 1010.95 / 1443.03 | 1052.27 / 1451.26 | 9.26 / 10.92 |
| VTU — median ms | 3020.11 | 6290.78 | 2227.71 | 39.92 |
| VTU — min / max | 2846.19 / 3206.13 | 6279.98 / 6311.04 | 2216.53 / 2517.02 | 39.56 / 43.8 |
| **Pages/sec** | 6.37 | 2.61 | 6.08 | 398.01 |
| Blocks extracted | 20 | 26 | 191 | 1168 |
| Tables extracted | 0 | 7 | 7 | 1 |
| Characters extracted | 66480 | 58366 | 58835 | 53380 |
| Extraction failures | 0 | 0 | 0 | 0 |
| Full ingest (parse+chunk+embed+index) | 5.67 s | 11.15 s | 6.12 s | 2.95 s |

### Downstream RAG quality

| Metric | pypdf | pdfplumber | pymupdf | lightningparse |
| :--- | ---: | ---: | ---: | ---: |
| **Retrieval Recall@5** | 9/9 | 9/9 | 9/9 | 9/9 |
| **Answer correctness** | 10/11 | 10/11 | 9/11 | 9/11 |
| **Citation correctness** | 9/9 | 9/9 | 9/9 | 9/9 |
| Correct abstention (unanswerable) | 2/2 | 2/2 | 2/2 | 2/2 |
| Indexed chunks | 83 | 74 | 76 | 86 |
