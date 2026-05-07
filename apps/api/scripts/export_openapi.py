"""Export the FastAPI OpenAPI schema as JSON to stdout.

Usage (from apps/api with .venv active):
    python scripts/export_openapi.py > ../../docs/api/openapi-w1.json
"""

import json
import sys

from app.main import app


def main() -> None:
    schema = app.openapi()
    json.dump(schema, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
