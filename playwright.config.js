const { defineConfig } = require("@playwright/test");

module.exports = defineConfig({
  testDir: "./tests",
  timeout: 30000,
  use: {
    baseURL: "http://127.0.0.1:8080",
    serviceWorkers: "block",
  },
  webServer: {
    command: "XIANGQI_FAKE_ENGINE=1 python3 -m web.backend.server",
    url: "http://127.0.0.1:8080/api/health",
    reuseExistingServer: true,
    timeout: 10000,
  },
});
