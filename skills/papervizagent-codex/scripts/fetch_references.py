#!/usr/bin/env python3
"""Fetch pinned PaperBanana reference metadata and only selected images.

This helper performs no model inference. The native Codex Retriever selects IDs.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import struct
import sys
import tempfile
from urllib.error import URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

REVISION = "587f33ecd98649a4588ff22c1bc3a865f6d8e3b4"
SPACE = "https://huggingface.co/spaces/dwzhu/PaperBanana"
BASE_URL = f"{SPACE}/resolve/{REVISION}/data/PaperBananaBench"
METADATA_HASHES = {
    "diagram": "d978569bbd46c1d312cde669475b87ace868d80bfb7ffb0484464dbc6b8f5d6a",
    "plot": "f2f169f49ed84fc1b65cb5c5d48163d29b87e67a736721e6bf04dd4c5954da28",
}
METADATA_LIMIT = 6_000_000
IMAGE_LIMIT = 20_000_000


def digest(data):
    return hashlib.sha256(data).hexdigest()


def contained(root, relative):
    root = Path(root).resolve()
    target = root / relative
    if not target.resolve().is_relative_to(root):
        raise ValueError(f"Path escapes output/cache directory: {relative}")
    return target


def atomic_write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
            temp = Path(stream.name)
            stream.write(data)
        os.replace(temp, path)
    finally:
        if temp is not None:
            temp.unlink(missing_ok=True)


def write_json(path, value):
    atomic_write(path, (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode())


def download(url, limit):
    request = Request(url, headers={"User-Agent": "PaperVizAgent-codex-reference-fetcher/1"})
    try:
        with urlopen(request, timeout=30) as response:
            length = response.headers.get("Content-Length")
            if length and int(length) > limit:
                raise ValueError(f"Download exceeds {limit} bytes: {url}")
            data = response.read(limit + 1)
    except (URLError, TimeoutError, OSError) as error:
        raise ValueError(f"Reference download unavailable (network/offline): {url}: {error}") from error
    if not data or len(data) > limit:
        raise ValueError(f"Empty or oversized reference download: {url}")
    return data


def cached_download(cache, relative, url, limit, validate, expected_hash=None):
    path = contained(cache, relative)
    checksum_path = contained(cache, relative + ".sha256")
    if path.is_file() and path.stat().st_size <= limit:
        data = path.read_bytes()
        expected = expected_hash
        if expected is None and checksum_path.is_file():
            expected = checksum_path.read_text().strip() if checksum_path.stat().st_size < 100 else None
        if expected and digest(data) == expected:
            try:
                validate(data)
                return data
            except (ValueError, KeyError, TypeError, UnicodeError):
                pass
    data = download(url, limit)
    if expected_hash and digest(data) != expected_hash:
        raise ValueError(f"Pinned metadata checksum mismatch: {url}")
    validate(data)
    atomic_write(path, data)
    atomic_write(checksum_path, (digest(data) + "\n").encode())
    return data


def safe_image_path(value):
    if not isinstance(value, str) or "\\" in value or any(ord(c) < 32 for c in value):
        raise ValueError("Invalid reference image path")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or len(path.parts) != 2 or path.parts[0] != "images":
        raise ValueError(f"Unsafe reference image path: {value}")
    if path.suffix.lower() not in (".jpg", ".jpeg", ".png"):
        raise ValueError(f"Unsupported reference image format: {value}")
    return value


def parse_metadata(data):
    records = json.loads(data)
    if not isinstance(records, list) or not records:
        raise ValueError("Reference metadata must be a nonempty list")
    seen = set()
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("Invalid reference record")
        ref_id = record.get("id")
        if not isinstance(ref_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", ref_id) or ref_id in seen:
            raise ValueError(f"Invalid or duplicate reference ID: {ref_id}")
        seen.add(ref_id)
        if not isinstance(record.get("content"), (str, dict, list)) or not isinstance(record.get("visual_intent"), str):
            raise ValueError(f"Missing source content/caption: {ref_id}")
        safe_image_path(record.get("path_to_gt_image"))
    return records


def image_dimensions(data):
    """Check PNG/JPEG structure and dimensions; the Planner still opens each image."""
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        import zlib
        pos, dimensions, has_data = 8, None, False
        while pos + 12 <= len(data):
            size = int.from_bytes(data[pos:pos + 4], "big")
            kind = data[pos + 4:pos + 8]
            end = pos + 12 + size
            if end > len(data) or zlib.crc32(data[pos + 4:end - 4]) != int.from_bytes(data[end - 4:end], "big"):
                raise ValueError("Invalid PNG chunk")
            if pos == 8:
                if kind != b"IHDR" or size != 13:
                    raise ValueError("Invalid PNG header")
                dimensions = struct.unpack(">II", data[pos + 8:pos + 16])
            has_data = has_data or kind == b"IDAT"
            if kind == b"IEND":
                if not dimensions or not all(dimensions) or not has_data or end != len(data):
                    raise ValueError("Invalid PNG image")
                return dimensions
            pos = end
    elif data.startswith(b"\xff\xd8") and data.endswith(b"\xff\xd9"):
        pos = 2
        while pos + 4 <= len(data):
            if data[pos] != 255:
                break
            while pos < len(data) and data[pos] == 255:
                pos += 1
            if pos >= len(data):
                break
            marker = data[pos]
            pos += 1
            if marker in (0xDA, 0xD9):
                break
            if marker in (0x01, *range(0xD0, 0xD8)):
                continue
            size = int.from_bytes(data[pos:pos + 2], "big")
            if size < 2 or pos + size > len(data):
                break
            if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF) and size >= 8:
                height, width = struct.unpack(">HH", data[pos + 3:pos + 7])
                if width and height:
                    return width, height
            pos += size
    raise ValueError("Reference is not a supported PNG/JPEG with valid dimensions")


def metadata(task, cache):
    relative = f"{REVISION}/{task}/ref.json"
    url = f"{BASE_URL}/{task}/ref.json"
    raw = cached_download(cache, relative, url, METADATA_LIMIT, parse_metadata, METADATA_HASHES[task])
    records = parse_metadata(raw)
    # Preserve the exact candidate scope/order used by upstream auto retrieval.
    candidates = records[:200] if task == "diagram" else records
    return candidates, {
        "task": task,
        "source_space": SPACE,
        "source_revision": REVISION,
        "metadata_url": url,
        "metadata_sha256": digest(raw),
        "available_records": len(records),
        "candidate_count": len(candidates),
        "rights": "Author Space declares Apache-2.0; underlying paper figures retain their source rights. Downloaded for reference use, not bundled or relicensed by this plugin.",
    }


def pool(task, output, cache, batch_size=10):
    if not 1 <= batch_size <= 200:
        raise ValueError("Batch size must be between 1 and 200")
    candidates, provenance = metadata(task, cache)
    batches = []
    for start in range(0, len(candidates), batch_size):
        name = f"{task}-pool-{start // batch_size + 1:03d}.json"
        write_json(contained(output, name), {"source": provenance, "candidates": candidates[start:start + batch_size]})
        batches.append(str(contained(output, name)))
    path = contained(output, f"{task}-pool.json")
    write_json(path, {"source": provenance, "batches": batches, "candidate_ids": [item["id"] for item in candidates]})
    return {"pool": str(path), "candidate_count": len(candidates), "batches": len(batches)}


def select(task, output, cache, ids):
    if not 1 <= len(ids) <= 10 or len(set(ids)) != len(ids):
        raise ValueError("Select between 1 and 10 unique reference IDs in ranked order")
    candidates, provenance = metadata(task, cache)
    by_id = {item["id"]: item for item in candidates}
    unknown = [ref_id for ref_id in ids if ref_id not in by_id]
    if unknown:
        raise ValueError(f"IDs are outside the {task} candidate pool: {', '.join(unknown)}")
    selected = []
    for ref_id in ids:
        record = dict(by_id[ref_id])
        image_path = safe_image_path(record["path_to_gt_image"])
        url = f"{BASE_URL}/{task}/{quote(image_path, safe='/')}"
        suffix = PurePosixPath(image_path).suffix.lower()
        cache_name = f"{REVISION}/{task}/images/{digest(image_path.encode())}{suffix}"
        raw = cached_download(cache, cache_name, url, IMAGE_LIMIT, image_dimensions)
        width, height = image_dimensions(raw)
        actual_suffix = ".png" if raw.startswith(b"\x89PNG\r\n\x1a\n") else ".jpg"
        destination = contained(output, f"reference-images/{task}-{ref_id}{actual_suffix}")
        atomic_write(destination, raw)
        record["image"] = {"local_path": str(destination), "source_url": url, "sha256": digest(raw), "bytes": len(raw), "width": width, "height": height}
        selected.append(record)
    path = contained(output, f"{task}-selected-references.json")
    write_json(path, {"source": provenance, "selection_order": "caller-supplied ranked IDs", "top10_references": ids, "retrieved_examples": selected})
    return {"selected_references": str(path), "count": len(selected)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("pool", "select"))
    parser.add_argument("--task", choices=("diagram", "plot"), default="diagram")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--cache-dir", type=Path, help="Defaults to OUTPUT_DIR/.reference-cache")
    parser.add_argument("--batch-size", type=int, default=10, help="Pool records per full-content batch (default: 10)")
    parser.add_argument("--ids", nargs="+", help="Select stage: 1–10 exact IDs in native Retriever ranking order")
    args = parser.parse_args()
    if (args.stage == "select") != bool(args.ids):
        parser.error("--ids is required for select and is not accepted for pool")
    output = args.output_dir.resolve()
    cache = (args.cache_dir or output / ".reference-cache").resolve()
    try:
        result = pool(args.task, output, cache, args.batch_size) if args.stage == "pool" else select(args.task, output, cache, args.ids)
    except (ValueError, OSError) as error:
        print(f"Reference retrieval failed: {error}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
