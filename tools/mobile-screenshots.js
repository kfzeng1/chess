const { chromium } = require("@playwright/test");

const viewports = [
  { name: "mobile-390", width: 390, height: 844 },
  { name: "mobile-360", width: 360, height: 740 },
  { name: "mobile-landscape", width: 844, height: 390 },
];

(async () => {
  const browser = await chromium.launch();
  try {
    for (const viewport of viewports) {
      const page = await browser.newPage({ viewport });
      await page.goto("http://127.0.0.1:8080/");
      await page.waitForLoadState("networkidle");
      const file = `/tmp/xiangqi-${viewport.name}.png`;
      await page.screenshot({ path: file, fullPage: false });
      console.log(file);
      await page.close();
    }
  } finally {
    await browser.close();
  }
})().catch((error) => {
  console.error(error);
  process.exit(1);
});
