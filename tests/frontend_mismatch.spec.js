const { test, expect } = require("@playwright/test");

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
