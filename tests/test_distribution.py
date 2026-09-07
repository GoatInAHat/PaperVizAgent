"""Check distributed source provenance and local documentation links."""

import hashlib
import ast
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


class DistributionTest(unittest.TestCase):
    def test_runtime_prompts_equal_preserved_upstream_prompts(self):
        provenance = json.loads((ROOT / 'UPSTREAM.json').read_text())
        for resource in provenance['vendored_resources']:
            if 'symbol' not in resource:
                continue
            source = ROOT / 'src/papervizagent/upstream' / resource['source']
            if not source.exists():
                continue
            values = {node.targets[0].id: ast.literal_eval(node.value)
                      for node in ast.parse(source.read_text()).body
                      if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name)
                      and isinstance(node.value, ast.Constant)}
            prompt = re.sub(r'\A<!--.*?-->\s*', '', (ROOT / resource['path']).read_text(), flags=re.DOTALL)
            self.assertEqual(values[resource['symbol']].strip(), prompt.strip())

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

    def test_skill_documents_portable_capability_resolution(self):
        skill = (ROOT / "skills/papervizagent/SKILL.md").read_text()
        roles = (ROOT / "skills/papervizagent/references/roles.md").read_text()

        self.assertIn("`status`", skill)
        self.assertIn("`infer(role, modality, system, contents,\noptions)`", skill)
        self.assertIn("`generate(data, settings)`", skill)
        self.assertIn("explicit runtime\nconfiguration", skill)
        self.assertIn("fresh\nrequest/thread per role", roles)
        self.assertIn("Codex\n  only if", roles)
        self.assertNotIn("tools with no API keys or model configuration", skill)
        self.assertNotIn("uses built-in image generation, never a\n  provider SDK", roles)


if __name__ == "__main__":
    unittest.main()
