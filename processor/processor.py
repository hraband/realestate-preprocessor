#!/usr/bin/env python3
import argparse
import json
import sys

import requests


def post_batch(batch: list, url: str, fout):
    resp = requests.post(url, json=batch)
    if resp.status_code != 200:
        print(
            "Error: failed to normalize batch",
            file=sys.stderr
        )
        print(f"Status code: {resp.status_code}", file=sys.stderr)
        print(f"Response body: {resp.text}", file=sys.stderr)
        sys.exit(1)

    for rec in resp.json():
        fout.write(json.dumps(rec, ensure_ascii=False) + "\n")


def normalize(
    input_path: str,
    output_path: str,
    url: str,
    batch_size: int,
):
    with open(input_path, "r") as fin, open(output_path, "w") as fout:
        batch = []

        for line in fin:
            record = json.loads(line)

            # Force these two fields to be strings if present
            if record.get("additional_costs") is not None:
                record["additional_costs"] = str(record["additional_costs"])
            if record.get("plot_area") is not None:
                record["plot_area"] = str(record["plot_area"])

            batch.append(record)

            if len(batch) >= batch_size:
                post_batch(batch, url, fout)
                batch.clear()

        # send any leftover
        if batch:
            post_batch(batch, url, fout)


def main():
    parser = argparse.ArgumentParser(
        description="Read raw JSONL listings, send to normalization service, write normalized output."
    )
    parser.add_argument(
        "--input", "-i", required=True,
        help="Path to your raw_listings.jsonl"
    )
    parser.add_argument(
        "--output", "-o", required=True,
        help="Path where normalized_listings.jsonl will be written"
    )
    parser.add_argument(
        "--url", "-u", default="http://localhost:8000/normalize",
        help="Normalization service endpoint"
    )
    parser.add_argument(
        "--batch-size", "-b", type=int, default=50,
        help="Number of records per HTTP request"
    )
    args = parser.parse_args()

    normalize(
        input_path=args.input,
        output_path=args.output,
        url=args.url,
        batch_size=args.batch_size,
    )


if __name__ == "__main__":
    main()

