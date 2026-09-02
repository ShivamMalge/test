# LightningParse Observations

Observed against **lightningparse 0.5.0** (PyPI), with differences from 0.4.1 noted inline.

## What changed in 0.5.0
Verified by diffing full parser output across both versions on the benchmark corpus:
- **Pages gained `page_width` and `page_height`.**
- **Section classification improved.** Blocks previously misfiled as `section_id: "header"` are now `body` with `block_role: "heading"`. On the synthetic corpus `header` blocks fell 60 -> 32; on the VTU document 2 -> 0, and `heading` roles rose 32 -> 35 and 19 -> 21 respectively.
- **Table extraction is byte-for-byte unchanged.** Same 1 table / 3 rows on the synthetic corpus, same 0 tables on the VTU document, same contaminated cell. The table work is still outstanding.
- **Parsing speed is unchanged.** An interleaved same-session A/B over three rounds gave 70.3 / 75.3 / 72.2 ms for 0.4.1 against 66.1 / 68.8 / 73.3 ms for 0.5.0 — indistinguishable.

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
- **Table recall is far behind the alternatives — still open as of 0.5.0.** Across the 20-page benchmark corpus, pdfplumber and PyMuPDF each recovered 7 tables with intact header rows; LightningParse recovered 1. In particular it found none of the six module comparison tables in the VTU document, emitting them as flattened text instead (`Module M1:Hardware Difficulty (1=Hardest) 4 Academic Importance Moderate ...`). This is unchanged in 0.5.0; see the scorecard in the README.
- **Table extraction is partial, and this measurably costs RAG accuracy (0.4.1 and 0.5.0 alike).** On the synthetic corpus, the header row and the first data row are emitted as ordinary text blocks, and only the remaining rows land in the `table` block. One `table` row also absorbed a stray cell of adjacent right-column prose. The data is recoverable but the row/column grouping is not exact — and because the resulting table chunk has no header cells, it carries no term that matches a query about its columns and is effectively unretrievable (rank 46 of 86 for the benchmark's table question). Attaching the preceding heading to a table chunk would be a downstream workaround; the fix belongs in row grouping.
- **Spaces are sometimes dropped** between words on some documents (the VTU PDF extracts `StrategicAcademicMastery:An`). The chunker applies `wordninja` when a block's average token length exceeds 15 characters, and skips that repair for table blocks.
- ASCII85-encoded content streams parse correctly in 0.4.1 and 0.5.0 (`tier: digital`, no OCR fallback), so the synthetic corpus no longer needs pre-cleaning.
- The GIL is released during parsing, which allows concurrent parsing if needed.
- Reading order is preserved in the order of the blocks returned in the `blocks` array; the two-column synthetic corpus is reconstructed column-by-column rather than line-interleaved.
