#!/usr/bin/env python
"""Import a JSON database snapshot into the configured database.

Usage:
  python scripts/db_import.py --input data-backup.json --mode replace
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from app import app, db


def import_snapshot(input_path: Path, mode: str) -> None:
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    table_data: dict[str, list[dict[str, Any]]] = payload.get("tables", {})

    tables_by_name = {table.name: table for table in db.metadata.sorted_tables}
    ordered_tables = list(db.metadata.sorted_tables)

    with app.app_context():
        if mode == "replace":
            # Delete children first to satisfy FK constraints.
            for table in reversed(ordered_tables):
                db.session.execute(table.delete())

        for table in ordered_tables:
            rows = table_data.get(table.name, [])
            if not rows:
                continue
            db.session.execute(table.insert(), rows)

        db.session.commit()

    inserted_count = sum(len(rows) for rows in table_data.values())
    print(f"Imported {inserted_count} rows from {input_path} using mode='{mode}'")
    unknown_tables = [name for name in table_data.keys() if name not in tables_by_name]
    if unknown_tables:
        print(f"Warning: snapshot includes unknown tables not imported: {', '.join(sorted(unknown_tables))}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import DB data from JSON snapshot")
    parser.add_argument("--input", required=True, help="Path to snapshot JSON file")
    parser.add_argument(
        "--mode",
        choices=["append", "replace"],
        default="replace",
        help="append: keep existing data, replace: clear then import (default: replace)",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    import_snapshot(Path(args.input).resolve(), args.mode)
