# LightningParse Observations

## Observed schema
The parser returns a JSON string, which when parsed contains two main keys:
- `pages`: A list of objects representing each page.
- `metadata`: Contains top-level document metadata.

## Page representation
Each page in the `pages` list has:
- `page_num`: Integer representing the 1-based page number.
- `blocks`: A list of content blocks found on that page.

## Block representation
Each block contains:
- `type`: String indicating block type (e.g., "text", "table", "heading").
- `text`: The extracted text content.
- `bbox`: Array of coordinates representing the bounding box `[x0, y0, x1, y1]`.
- `section_id`: String identifying the structural section (e.g., "header", "2.1").
- `source`: How it was extracted (e.g., "ocr").

## Known issues / Notes
- The parser returns a raw JSON string rather than a parsed dictionary. We must run `json.loads(raw_result)` inside the wrapper.
- The GIL is released during parsing, which allows concurrent parsing if needed.
- Reading order is preserved in the order of the blocks returned in the `blocks` array.
