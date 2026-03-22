from __future__ import annotations

import argparse
from pathlib import Path

from source_ingestion_tools.pipeline import run_ingest


def main() -> None:
    p = argparse.ArgumentParser(description="YasarNuri source ingestion")
    p.add_argument("--format", choices=["qa", "quran"], required=True)
    p.add_argument("--path", type=Path, required=True)
    p.add_argument("--book-title", type=str, default=None)
    args = p.parse_args()

    run_ingest(
        format_name=args.format,
        path=args.path,
        book_title_override=args.book_title,
    )


if __name__ == "__main__":
    main()
