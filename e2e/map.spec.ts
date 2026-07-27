import { expect, test } from "@playwright/test";

test.describe("Map page (mock data)", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/map");
  });

  test("page loads without error", async ({ page }) => {
    await expect(page).not.toHaveTitle(/error/i);
    await expect(page.locator("canvas").first()).toBeVisible({ timeout: 8000 });
  });

  test("shows filter panel toggle", async ({ page }) => {
    await expect(page.locator(".filter-panel, [class*='filter']").first()).toBeVisible({ timeout: 5000 });
  });

  test("region selector is present", async ({ page }) => {
    await expect(page.locator("select")).toBeVisible({ timeout: 5000 });
  });

  test("can select a region", async ({ page }) => {
    const select = page.locator("select").first();
    await select.selectOption({ label: "Москва" });
    await expect(select).toHaveValue("moscow_city");
  });

  test("filter panel toggle button is visible", async ({ page }) => {
    await expect(page.locator(".filter-panel-toggle")).toBeVisible({ timeout: 5000 });
  });
});
