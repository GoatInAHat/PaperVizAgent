"""Check distributed source provenance and local documentation links."""

import hashlib
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


class DistributionTest(unittest.TestCase):
    def test_vendored_prompts_and_guides_match_recorded_hashes(self):
        provenance = json.loads((ROOT / "UPSTREAM.json").read_text())
        for resource in provenance["vendored_resources"]:
            with self.subTest(path=resource["path"]):
                content = (ROOT / resource["path"]).read_bytes()
                self.assertEqual(hashlib.sha256(content).hexdigest(), resource["sha256"])
        for path in provenance["adapted_resources"]:
            self.assertTrue((ROOT / path).is_file(), path)

    def test_relative_documentation_links_resolve(self):
        for directory in (ROOT / "skills", ROOT / "evals"):
            for document in directory.rglob("*.md"):
                for target in re.findall(r"\]\(([^\s)]+)", document.read_text()):
                    target = target.split("#", 1)[0]
                    if not target or ":" in target:
                        continue
                    with self.subTest(document=str(document.relative_to(ROOT)), target=target):
                        self.assertTrue((document.parent / target).exists())


if __name__ == "__main__":
    unittest.main()
