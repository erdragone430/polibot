import argparse
from pathlib import Path

from polibot.ingestion.pipeline import ingest_pdf


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest a folder of PDFs into Qdrant.")
    parser.add_argument("--source", required=True, help="Folder containing PDF files")
    parser.add_argument("--course", required=True, help="Course name to tag chunks with")
    parser.add_argument(
        "--no-caption", action="store_true", help="Skip image captioning (fast demo/validation ingestion)"
    )
    args = parser.parse_args()

    pdfs = sorted(Path(args.source).glob("*.pdf"))
    if not pdfs:
        print(f"No PDFs found in {args.source}")
        return

    for pdf in pdfs:
        count = ingest_pdf(str(pdf), course=args.course, caption=not args.no_caption)
        print(f"{pdf.name}: {count} vectors inserted")


if __name__ == "__main__":
    main()
