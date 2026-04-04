from __future__ import annotations

import sys

from src.converter import convert_pdf_to_markdown


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if len(args) != 1:
        print("usage: python -m server.app.adapters.opendataloader_cli <pdf_path>", file=sys.stderr)
        return 2

    pdf_path = args[0]
    markdown = convert_pdf_to_markdown(pdf_path)
    sys.stdout.write(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
