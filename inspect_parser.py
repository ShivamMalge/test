import lightningparse
import json

try:
    result = lightningparse.parse_pdf("data/synthetic/lightningparse_test_document_TRUE_2COL.pdf")
    print(type(result))
    if isinstance(result, str):
        # Maybe it returns a JSON string?
        print(result[:500])
        parsed = json.loads(result)
        print("Keys:", parsed.keys())
    elif hasattr(result, "keys"):
        # dict
        print("Keys:", result.keys())
        print(json.dumps(result, indent=2)[:500])
    else:
        print(result)
except Exception as e:
    print("Error:", e)
