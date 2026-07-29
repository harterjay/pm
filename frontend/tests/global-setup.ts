import { execSync } from "node:child_process";
import { rmSync } from "node:fs";
import path from "node:path";

const ROOT = path.resolve(__dirname, "..", "..");

async function waitForHealth(url: string, timeoutMs: number) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    try {
      const response = await fetch(url);
      if (response.ok) return;
    } catch {
      // Not up yet.
    }
    await new Promise((resolve) => setTimeout(resolve, 1000));
  }
  throw new Error(`Timed out waiting for ${url}`);
}

export default async function globalSetup() {
  // Stop any leftover container first — otherwise it can keep holding the
  // old DB file open even after we delete the directory below.
  execSync("docker compose down", { cwd: ROOT, stdio: "inherit" });

  // Start every e2e run from a clean, freshly-seeded DB so tests don't
  // depend on (or accumulate) state left over from previous runs.
  rmSync(path.join(ROOT, "backend", "data"), { recursive: true, force: true });

  execSync("docker compose up --build -d", { cwd: ROOT, stdio: "inherit" });

  await waitForHealth("http://127.0.0.1:8000/api/health", 120_000);
}
