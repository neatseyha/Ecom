#!/usr/bin/env python
"""Export database rows into a portable JSON snapshot.

Usage:
  python scripts/db_export.py --output data-backup.json
"""

from __future__ import annotations

import argparse
import json
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from sqlalchemy import select

from app import app, db


def serialize_value(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    return value


def export_snapshot(output_path: Path) -> None:
    snapshot: dict[str, Any] = {
        "metadata": {
            "database_uri": str(db.engine.url),
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "format": "greenbean-db-snapshot-v1",
        },
        "tables": {},
    }

    # Include real tables only and keep deterministic order.
    tables = sorted(db.metadata.sorted_tables, key=lambda table: table.name)

    with app.app_context():
        for table in tables:
            rows = db.session.execute(select(table)).mappings().all()
            serialized_rows = []
            for row in rows:
                serialized_rows.append({key: serialize_value(value) for key, value in row.items()})
            snapshot["tables"][table.name] = serialized_rows

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
    print(f"Exported {len(snapshot['tables'])} tables to {output_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export DB data to JSON snapshot")
    parser.add_argument(
        "--output",
        default="db_snapshot.json",
        help="Path to output JSON file (default: db_snapshot.json)",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    export_snapshot(Path(args.output).resolve())
