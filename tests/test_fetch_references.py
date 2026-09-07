"""Network-free contract tests with authored synthetic reference records/images."""

import importlib.util
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import URLError
import zlib

SCRIPT = Path(__file__).resolve().parents[1] / "skills/papervizagent/scripts/fetch_references.py"
SPEC = importlib.util.spec_from_file_location("fetch_references", SCRIPT)
fetch = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(fetch)


def png():
    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 2, 1, 8, 2, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(b"\x00\xff\x00\x00\x00\xff\x00")) + chunk(b"IEND", b"")


def records(count):
    return [{"id": f"ref_{i}", "content": f"Full synthetic method {i}.\nDetails preserved.", "visual_intent": f"Synthetic pipeline {i}", "path_to_gt_image": f"images/Example {i}.png", "additional_info": {"authored_fixture": True}} for i in range(count)]


class ReferencesTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.output = Path(self.temp.name) / "run"
        self.cache = Path(self.temp.name) / "cache"
        self.raw = json.dumps(records(205)).encode()
        self.image = png()
        self.hashes = patch.dict(fetch.METADATA_HASHES, {"diagram": fetch.digest(self.raw), "plot": fetch.digest(self.raw)})
        self.hashes.start()
        self.addCleanup(self.hashes.stop)
        self.network = patch.object(fetch, "download", side_effect=lambda url, limit: self.raw if url.endswith("ref.json") else self.image)
        self.download = self.network.start()
        self.addCleanup(self.network.stop)

    def test_full_content_pool_matches_upstream_scope_and_batches(self):
        result = fetch.pool("diagram", self.output, self.cache)
        manifest = json.loads(Path(result["pool"]).read_text())
        actual = [record for batch in manifest["batches"] for record in json.loads(Path(batch).read_text())["candidates"]]
        self.assertEqual(actual, records(205)[:200])
        self.assertEqual(result["batches"], 20)
        self.assertEqual(fetch.pool("plot", self.output, self.cache)["candidate_count"], 205)

    def test_select_materializes_ranked_complete_examples_and_reuses_valid_cache(self):
        result = fetch.select("diagram", self.output, self.cache, ["ref_9", "ref_1"])
        manifest = json.loads(Path(result["selected_references"]).read_text())
        self.assertEqual(manifest["top10_references"], ["ref_9", "ref_1"])
        first = manifest["retrieved_examples"][0]
        self.assertEqual(first["content"], records(10)[9]["content"])
        self.assertEqual(first["image"]["width"], 2)
        self.assertIn("Example%209.png", first["image"]["source_url"])
        self.assertEqual(Path(first["image"]["local_path"]).read_bytes(), self.image)
        self.download.side_effect = ValueError("offline")
        fetch.select("diagram", self.output, self.cache, ["ref_9", "ref_1"])

    def test_invalid_selection_cannot_fetch_images(self):
        for ids in (["ref_204"], ["unknown"], ["ref_1", "ref_1"], [], [f"ref_{i}" for i in range(11)]):
            with self.subTest(ids=ids), self.assertRaises(ValueError):
                fetch.select("diagram", self.output, self.cache, ids)
        self.assertTrue(all(call.args[0].endswith("ref.json") for call in self.download.call_args_list))

    def test_modified_metadata_or_image_cache_is_refetched(self):
        fetch.select("diagram", self.output, self.cache, ["ref_1"])
        cached_metadata = self.cache / fetch.REVISION / "diagram/ref.json"
        cached_metadata.write_text("[]")
        cached_image = next(self.cache.rglob("*.png"))
        cached_image.write_bytes(b"invalid image")
        self.download.reset_mock()
        fetch.select("diagram", self.output, self.cache, ["ref_1"])
        self.assertEqual(self.download.call_count, 2)
        self.assertEqual(cached_metadata.read_bytes(), self.raw)
        self.assertEqual(cached_image.read_bytes(), self.image)

    def test_bad_download_hash_or_image_never_becomes_valid_cache(self):
        self.download.side_effect = None
        self.download.return_value = b"[]"
        with self.assertRaisesRegex(ValueError, "checksum mismatch"):
            fetch.pool("diagram", self.output, self.cache)
        self.assertFalse(self.cache.exists())
        self.download.side_effect = lambda url, limit: self.raw if url.endswith("ref.json") else b"<html>not an image</html>"
        with self.assertRaisesRegex(ValueError, "PNG/JPEG"):
            fetch.select("diagram", self.output, self.cache, ["ref_1"])
        self.assertFalse(list(self.cache.rglob("*.png")))
        self.assertFalse((self.output / "diagram-selected-references.json").exists())

    def test_traversal_and_symlink_escape_rejected(self):
        for value in ("../private.png", "/private.png", "images/../../private.png", "images\\private.png", "images/private.txt"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                fetch.safe_image_path(value)
        self.output.mkdir()
        outside = Path(self.temp.name) / "outside"
        outside.mkdir()
        (self.output / "reference-images").symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "escapes"):
            fetch.select("diagram", self.output, self.cache, ["ref_1"])
        self.assertEqual(list(outside.iterdir()), [])

    def test_offline_failure_does_not_manufacture_pool(self):
        self.download.side_effect = ValueError("Reference download unavailable (network/offline)")
        with self.assertRaisesRegex(ValueError, "offline"):
            fetch.pool("diagram", self.output, self.cache)
        self.assertFalse(self.output.exists())

    def test_metadata_rejects_invalid_records_and_image_rejects_corrupt_png(self):
        for data in ({}, [], [{"id": "ref_1"}], records(1) * 2):
            with self.subTest(data=data), self.assertRaises(ValueError):
                fetch.parse_metadata(json.dumps(data).encode())
        corrupt = bytearray(self.image)
        corrupt[20] ^= 1
        with self.assertRaises(ValueError):
            fetch.image_dimensions(corrupt)

    def test_http_download_is_bounded_and_network_error_is_explicit(self):
        # Exercise real download() rather than the synthetic fixture transport.
        self.network.stop()
        with patch.object(fetch, "urlopen", side_effect=URLError("offline")):
            with self.assertRaisesRegex(ValueError, "network/offline"):
                fetch.download("https://example.invalid/reference", 10)
        with patch.object(fetch, "urlopen") as opener:
            response = opener.return_value.__enter__.return_value
            response.headers = {"Content-Length": "11"}
            with self.assertRaisesRegex(ValueError, "exceeds"):
                fetch.download("https://example.invalid/reference", 10)
            response.read.assert_not_called()
            response.headers = {}
            response.read.return_value = b"x" * 11
            with self.assertRaisesRegex(ValueError, "oversized"):
                fetch.download("https://example.invalid/reference", 10)
            response.read.assert_called_once_with(11)


if __name__ == "__main__":
    unittest.main()
