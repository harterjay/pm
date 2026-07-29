import { execSync } from "node:child_process";
import path from "node:path";

const ROOT = path.resolve(__dirname, "..", "..");

export default async function globalTeardown() {
  execSync("docker compose down", { cwd: ROOT, stdio: "inherit" });
}
