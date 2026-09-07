#!/usr/bin/env node
import { spawnSync } from "node:child_process";

const child = spawnSync("uvx", ["--from", "papervizagent-codex==0.3.0", "papervizagent-codex", ...process.argv.slice(2)], {
  stdio: "inherit",
});
if (child.error) throw child.error;
process.exit(child.status ?? 1);
