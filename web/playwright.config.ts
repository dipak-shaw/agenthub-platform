import { defineConfig } from "@playwright/test";
import { randomUUID } from "node:crypto";
import { tmpdir } from "node:os";
import { join } from "node:path";
export default defineConfig({
  testDir: "./e2e",
  workers: 1,
  use: {
    baseURL: "http://127.0.0.1:8080",
    browserName: "chromium",
    trace: "retain-on-failure",
  },
  webServer: {
    command: "cd .. && uv run --locked agent-hub run --port 8080",
    url: "http://127.0.0.1:8080/health",
    env: {
      APP_MODE: "offline",
      AGENTS_DIR: "tests/fixtures/agents",
      DATABASE_URL: `sqlite+aiosqlite:///${join(tmpdir(), `agent-hub-e2e-${randomUUID()}.db`)}`,
    },
  },
});
