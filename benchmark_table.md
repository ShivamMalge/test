### Parsing performance

| Metric | pypdf | pdfplumber | pymupdf | lightningparse |
| :--- | ---: | ---: | ---: | ---: |
| **Parse latency, median total (20 pages)** | 3328.92 ms | 8186.08 ms | 4640.77 ms | 68.61 ms |
| Synthetic — median ms | 181.41 | 1514.63 | 1056.34 | 12.89 |
| Synthetic — min / max | 165.82 / 192.76 | 1191.15 / 1596.67 | 1026.74 / 1391.28 | 10.9 / 16.63 |
| VTU — median ms | 3147.51 | 6671.45 | 3584.43 | 55.72 |
| VTU — min / max | 3042.37 / 3824.12 | 6462.18 / 7247.3 | 2938.84 / 3958.44 | 49.45 / 76.91 |
| **Pages/sec** | 6.01 | 2.44 | 4.31 | 291.5 |
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
