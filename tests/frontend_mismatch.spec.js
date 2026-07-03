const { test, expect } = require("@playwright/test");

test.use({ serviceWorkers: "block" });

test("mismatch alert disables auto mode and restores the checked position", async ({ page }) => {
  const alerts = [];
  page.on("dialog", async (dialog) => {
    alerts.push(dialog.message());
    await dialog.accept();
  });

  await page.goto("http://127.0.0.1:8080/");
  await page.waitForLoadState("networkidle");
  await page.getByRole("button", { name: "自动代走：开" }).click();
  await expect(page.locator("#autoMode")).toHaveText("自动代走：关");

  let corrupted = false;
  await page.route("**/api/analyze", async (route) => {
    const response = await route.fetch();
    const data = await response.json();
    if (!corrupted) {
      data.positionId = "forced-mismatch";
      corrupted = true;
    }
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(data),
    });
  });

  await page.locator('.piece[data-square="h2"]').click();
  await page.locator('.square-target[data-square="e2"]').click();

  await expect.poll(() => alerts.length).toBe(1);
  expect(alerts[0]).toContain("检测到代走不匹配");
  await expect(page.locator("#autoMode")).toHaveText("自动代走：关");
  await expect(page.locator("#autoMode")).toHaveAttribute("aria-pressed", "false");
  await expect(page.locator("#moveCount")).toHaveText("1 步");
  await expect(page.locator("#turnStat")).toHaveText("黑方");
  await expect(page.locator("#mismatchCount")).toContainText("不匹配 1");
});

test("undo reruns analysis once after the debounce window", async ({ page }) => {
  let analyzeCalls = 0;
  await page.route("**/api/analyze", async (route) => {
    analyzeCalls += 1;
    await route.continue();
  });

  await page.goto("http://127.0.0.1:8080/");
  await page.waitForLoadState("networkidle");
  await page.getByRole("button", { name: "自动代走：开" }).click();
  await expect(page.locator("#autoMode")).toHaveText("自动代走：关");

  await expect.poll(() => analyzeCalls).toBe(1);
  await expect(page.locator("#depthText")).toContainText("depth");

  await page.locator('.piece[data-square="h2"]').click();
  await page.locator('.square-target[data-square="e2"]').click();
  await expect(page.locator("#moveCount")).toHaveText("1 步");
  await expect.poll(() => analyzeCalls).toBe(2);

  await page.getByTitle("撤销红方或黑方的一步").click();
  await expect(page.locator("#moveCount")).toHaveText("0 步");
  await page.waitForTimeout(250);
  expect(analyzeCalls).toBe(2);

  await expect.poll(() => analyzeCalls).toBe(3);
  await expect(page.locator("#depthText")).toContainText("depth");
});

test("mobile layout keeps board primary and controls usable", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.route("**/api/analyze", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        sideToMove: "red",
        positionId: "e3b0c44298fc1c14",
        limit: { mode: "movetime", value: 1000, command: "go movetime 1000" },
        bestmove: "h2e2",
        bestmove_cn: "炮二平五",
        lines: [{
          multipv: 1,
          depth: 8,
          nodes: 1200,
          nps: 40000,
          score: { display: "红方 +0.24" },
          wdl: [120, 820, 60],
          pv: ["h2e2", "h9g7"],
          bestmove: "h2e2",
          pv_cn: ["炮二平五", "马8进7"],
        }],
      }),
    });
  });

  await page.goto("http://127.0.0.1:8080/");
  await page.waitForLoadState("networkidle");

  const viewport = page.viewportSize();
  const board = await page.locator("#board").boundingBox();
  const bodyWidth = await page.evaluate(() => document.documentElement.scrollWidth);

  expect(viewport).toEqual({ width: 390, height: 844 });
  expect(bodyWidth).toBeLessThanOrEqual(390);
  expect(board.width).toBeGreaterThan(350);
  expect(board.y).toBeLessThan(230);
  await expect(page.locator(".mobile-board-actions")).toBeVisible();
  await expect(page.getByRole("button", { name: "新局" })).toBeVisible();
  await expect(page.getByRole("button", { name: "悔棋" })).toBeVisible();
  await expect(page.getByRole("button", { name: "翻转" })).toBeVisible();
  await expect(page.locator("#autoModeMobile")).toHaveText("自动代走：开");
  await expect(page.locator("#autoModeMobile")).toBeVisible();
  await expect(page.locator("#manualAiMobile")).toBeVisible();
  await expect(page.locator("#turnStatMobile")).toHaveText("红方");
  await expect(page.locator("#roundStatMobile")).toHaveText("0");
  await expect(page.locator("#redClockMobile")).toContainText("00:");
  await expect(page.locator("#blackClockMobile")).toHaveText("00:00");

  const closedLeft = await page.locator(".controls-panel").boundingBox();
  expect(closedLeft.x).toBeLessThan(-250);
  await page.getByRole("button", { name: "配置", exact: true }).click();
  await expect.poll(async () => (await page.locator(".controls-panel").boundingBox()).x).toBeGreaterThanOrEqual(-1);
  await expect(page.locator(".controls-panel #autoMode")).toBeHidden();
  await expect(page.locator(".controls-panel #manualAi")).toBeHidden();
  await expect(page.locator(".controls-panel .status-grid")).toBeHidden();
  await page.getByLabel("关闭配置").click();

  const closedRight = await page.locator(".panel.right").boundingBox();
  expect(closedRight.x).toBeGreaterThan(380);
  await page.getByRole("button", { name: "分析", exact: true }).click();
  await expect.poll(async () => {
    const box = await page.locator(".panel.right").boundingBox();
    return Math.round(box.x + box.width);
  }).toBeLessThanOrEqual(391);
  const openRight = await page.locator(".panel.right").boundingBox();
  expect(openRight.x + openRight.width).toBeLessThanOrEqual(391);
  await expect(page.locator("#auditSection")).toBeHidden();
  await expect(page.locator("#recommendations")).toBeVisible();
});
