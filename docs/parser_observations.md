# LightningParse Observations

Observed against **lightningparse 0.4.1** (PyPI).

## Observed schema
`parse_pdf(path)` returns a JSON **string**, which when parsed contains two keys:
- `pages`: A list of objects representing each page.
- `metadata`: Top-level document metadata.

## Metadata
```json
{"tier": "digital", "page_count": 8, "parse_time_ms": 4}
```
- `tier`: extraction tier used for the document (e.g. `digital`).
- `page_count`: number of pages.
- `parse_time_ms`: the parser's own timing for the extraction work.

There is **no `warnings` key** in 0.4.1; code must not assume one exists.

## Page representation
Each page in the `pages` list has:
- `page_num`: Integer, 1-based page number.
- `blocks`: A list of content blocks found on that page.

## Block representation
Blocks are line-level rather than paragraph-level (8 pages → ~467 blocks).

Text blocks contain:
- `type`: `"text"`.
- `text`: The extracted text content.
- `spans`: A list of styling runs — `start`, `end`, `bold`, `font_size`, `is_monospace`.
- `bbox`: `[x0, y0, x1, y1]`.
- `section_id`: Structural section, e.g. `"header"` or `"body"`.
- `block_role`: Present only on some blocks, e.g. `"heading"`.
- `source`: How it was extracted, e.g. `"digital"`, `"ocr"`.

Table blocks have a **different shape**:
- `type`: `"table"`.
- `rows`: A list of row arrays of cell strings.
- `bbox`, `section_id`, `source`.
- **No `text` key.**

```json
{"type": "table",
 "rows": [["Borealis", "94.2%", "93.5%", "92.1%"],
          ["Cirrus", "96.1%", "95.0%", "95.4%"]],
 "section_id": "body", "source": "digital"}
```

## Known issues / Notes
- The parser returns a raw JSON string rather than a parsed dictionary. We must run `json.loads(raw_result)` inside the wrapper.
- **Table blocks carry no `text`.** Reading `block["text"]` alone silently drops every table from the pipeline. `Chunker._block_text` renders `rows` into a markdown table instead.
- **Table recall is far behind the alternatives — a known 0.4.1 limitation, planned for 0.5.0.** Across the 20-page benchmark corpus, pdfplumber and PyMuPDF each recovered 7 tables with intact header rows; LightningParse recovered 1. In particular it found none of the six module comparison tables in the VTU document, emitting them as flattened text instead (`Module M1:Hardware Difficulty (1=Hardest) 4 Academic Importance Moderate ...`). The README's "Regression targets for 0.5.0" section records the exact per-signal baselines to compare against after the fix.
- **Table extraction is partial, and this measurably costs RAG accuracy.** On the synthetic corpus, the header row and the first data row are emitted as ordinary text blocks, and only the remaining rows land in the `table` block. One `table` row also absorbed a stray cell of adjacent right-column prose. The data is recoverable but the row/column grouping is not exact — and because the resulting table chunk has no header cells, it carries no term that matches a query about its columns and is effectively unretrievable (rank 46 of 86 for the benchmark's table question). Attaching the preceding heading to a table chunk would be a downstream workaround; the fix belongs in row grouping.
- **Spaces are sometimes dropped** between words on some documents (the VTU PDF extracts `StrategicAcademicMastery:An`). The chunker applies `wordninja` when a block's average token length exceeds 15 characters, and skips that repair for table blocks.
- ASCII85-encoded content streams parse correctly in 0.4.1 (`tier: digital`, no OCR fallback), so the synthetic corpus no longer needs pre-cleaning.
- The GIL is released during parsing, which allows concurrent parsing if needed.
- Reading order is preserved in the order of the blocks returned in the `blocks` array; the two-column synthetic corpus is reconstructed column-by-column rather than line-interleaved.
