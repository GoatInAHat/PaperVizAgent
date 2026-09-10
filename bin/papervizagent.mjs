#!/usr/bin/env node
import { spawnSync } from "node:child_process";

const child = spawnSync("uvx", ["--from", "papervizagent==0.4.0", "papervizagent", ...process.argv.slice(2)], {
  stdio: "inherit",
});
if (child.error) throw child.error;
process.exit(child.status ?? 1);
