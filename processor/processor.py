#!/usr/bin/env python3
"""
processor.py

This script reads a `.jsonl` file with raw real estate listings, sends them in batches
to a normalization API, and writes the normalized results to a new `.jsonl` file.

Usage:
    python python.py -i raw_listings.jsonl -o normalized_listings.jsonl
"""
import os
import argparse
import json
import sys
import requests
from tqdm import tqdm



def post_batch(batch: list, url: str, fout):
    """
    Sends a batch of records to the normalization API and writes the response to output.

    Args:
        batch (list): A list of raw records (dictionaries).
        url (str): The API endpoint to send the POST request to.
        fout (file object): Output file object to write the normalized records to.

    Raises:
        Exits with status code 1 if the POST request fails.
    """
    resp = requests.post(url, json=batch)
    if resp.status_code != 200:
        print("ERROR: Batch normalization failed", file=sys.stderr)
        print(f"Status code: {resp.status_code}", file=sys.stderr)
        print(f"Response body: {resp.text}", file=sys.stderr)
        sys.exit(1)

    for rec in resp.json():
        fout.write(json.dumps(rec, ensure_ascii=False) + "\n")


def normalize(input_path: str, output_path: str, url: str, batch_size: int):
    """
    Reads raw JSONL input, normalizes it via API, and writes normalized JSONL output.

    Args:
        input_path (str): Path to the raw JSONL input file.
        output_path (str): Path to save the normalized JSONL output.
        url (str): The normalization API endpoint.
        batch_size (int): Number of records to send per request.
    """
    if not os.path.isfile(input_path):
        print(f"\n❌ Input file not found: {input_path}", file=sys.stderr)
        print("➡️  Make sure the file exists at the specified path (e.g., data/raw_listings.jsonl)\n", file=sys.stderr)
        sys.exit(1)

    total_lines = sum(1 for _ in open(input_path, "r", encoding="utf-8"))

    batch = []
    print(f"\n📥 Normalizing {total_lines} records from {input_path}...\n")

    with open(input_path, "r", encoding="utf-8") as fin, open(output_path, "w", encoding="utf-8") as fout, tqdm(total=total_lines, unit="record") as pbar:
        for line in fin:
            record = json.loads(line)

            if record.get("additional_costs") is not None:
                record["additional_costs"] = str(record["additional_costs"])
            if record.get("plot_area") is not None:
                record["plot_area"] = str(record["plot_area"])

            batch.append(record)

            if len(batch) >= batch_size:
                post_batch(batch, url, fout)
                pbar.update(len(batch))
                batch.clear()

        if batch:
            post_batch(batch, url, fout)
            pbar.update(len(batch))

    print(f"\n✅ Done. Output written to: {output_path}")


def main():
    """
    Parses command-line arguments and starts the normalization process.
    """
    parser = argparse.ArgumentParser(
        description="Send RAW JSONL to normalization service and write NORMALIZED JSONL."
    )
    parser.add_argument("-i", "--input",    required=True, help="Path to input raw JSONL file")
    parser.add_argument("-o", "--output",   required=True, help="Path to output normalized JSONL file")
    parser.add_argument("-u", "--url",      default="http://localhost:8000/normalize",
                        help="Normalization API endpoint URL")
    parser.add_argument("-b", "--batch-size", type=int, default=50,
                        help="Number of records per request (batch size)")
    args = parser.parse_args()
    normalize(args.input, args.output, args.url, args.batch_size)


if __name__ == "__main__":
    main()
