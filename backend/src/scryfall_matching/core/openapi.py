import argparse
import json
from pathlib import Path

from fastapi import FastAPI


def export_openapi_contract(app: FastAPI) -> None:
    app.openapi_version = "3.1.0"
    app.state.openapi_output_path = Path("openapi.json")


def write_openapi_contract(app: FastAPI, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(app.openapi(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return output_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Export the Scryfall Matching OpenAPI contract.")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("openapi.json"),
        help="Path where the OpenAPI document should be written.",
    )
    args = parser.parse_args(argv)

    from scryfall_matching.main import create_app

    write_openapi_contract(create_app(), args.output)
    return 0
