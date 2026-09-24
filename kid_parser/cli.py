"""Command-line entry point. JSON is only written when explicitly asked for."""

import argparse
import json
import os

from .parser import parse_kids


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="kid-parser",
        description="Parse PRIIPs KID PDFs into structured data (no JSON written by default).",
    )
    parser.add_argument("paths", nargs="+", help="PDF file(s) and/or directories of PDFs")
    parser.add_argument(
        "--json-dir",
        metavar="DIR",
        help="write <isin>.kid.json per fund plus a combined kids_parsed.json into DIR",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="print the combined JSON array to stdout instead of one-line summaries",
    )
    args = parser.parse_args(argv)

    kids = parse_kids(args.paths)

    if args.json_dir:
        os.makedirs(args.json_dir, exist_ok=True)
        for kid in kids:
            stem = os.path.splitext(os.path.basename(kid.source_file))[0]
            with open(os.path.join(args.json_dir, f"{stem}.kid.json"), "w", encoding="utf-8") as f:
                f.write(kid.to_json())
        with open(os.path.join(args.json_dir, "kids_parsed.json"), "w", encoding="utf-8") as f:
            json.dump([kid.to_dict() for kid in kids], f, indent=2, ensure_ascii=False)

    if args.json:
        print(json.dumps([kid.to_dict() for kid in kids], indent=2, ensure_ascii=False))
    else:
        for kid in kids:
            print(f"{kid.isin}: {kid.product_name} | SRI {kid.sri}/7 | RHP {kid.rhp_years}y")

    if args.json_dir:
        print(f"Wrote {len(kids)} KID(s) to {args.json_dir}/")


if __name__ == "__main__":
    main()
