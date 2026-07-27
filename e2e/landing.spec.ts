import { expect, test } from "@playwright/test";

test.describe("Landing page", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
  });

  test("shows brand name", async ({ page }) => {
    await expect(page.getByText("Топливный Дозор").first()).toBeVisible();
  });

  test("has link to site in brand name", async ({ page }) => {
    const link = page.locator("a.tgn-link").first();
    await expect(link).toHaveAttribute("href", "https://dozor-fuel.online");
  });

  test("shows open map button", async ({ page }) => {
    await expect(page.getByRole("button", { name: /Открыть карту/i }).first()).toBeVisible();
  });

  test("shows Telegram bot link", async ({ page }) => {
    const botLinks = page.locator("a[href*='t.me']");
    await expect(botLinks.first()).toBeVisible();
  });

  test("mobile layout looks correct", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto("/");
    // Brand name should still be visible on mobile
    await expect(page.getByText("Топливный Дозор").first()).toBeVisible();
  });
});
