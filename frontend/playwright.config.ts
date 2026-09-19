import { defineConfig } from "@playwright/test";
export default defineConfig({
  testDir: "./e2e",
  workers: 1,
  use: {
    baseURL: "http://localhost:5174",
    viewport: { width: 1366, height: 768 },
    trace: "retain-on-failure",
  },
  webServer: [
    {
      command:
        '"' +
        (process.env.CIBERQUANT_TEST_PYTHON || "python") +
        '" -m uvicorn e2e_app:app --app-dir tests --port 8010',
      cwd: "../backend",
      url: "http://localhost:8010/openapi.json",
      reuseExistingServer: false,
    },
    {
      command: "npm run dev -- --port 5174 --strictPort",
      url: "http://localhost:5174",
      env: { VITE_API_BASE_URL: "http://localhost:8010/api/v1" },
      reuseExistingServer: false,
    },
  ],
});
