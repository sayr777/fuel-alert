import { expect, test } from "@playwright/test";

// Moderation panel uses mock data (VITE_USE_MOCKS=true in dev)
// Token check is done against the real API in prod, but mocks skip the real call

test.describe("Moderation panel", () => {
  test("shows login screen at /moderation", async ({ page }) => {
    await page.goto("/moderation");
    await expect(page.getByPlaceholder("Токен")).toBeVisible({ timeout: 5000 });
  });

  test("login button disabled without token", async ({ page }) => {
    await page.goto("/moderation");
    const btn = page.getByRole("button", { name: /Войти/i });
    await expect(btn).toBeDisabled();
  });

  test("login button enabled when token typed", async ({ page }) => {
    await page.goto("/moderation");
    await page.getByPlaceholder("Токен").fill("test-token");
    await expect(page.getByRole("button", { name: /Войти/i })).toBeEnabled();
  });

  test("can log in with mock token and see tabs", async ({ page }) => {
    // In mock mode, any token triggers loadAll with mock data
    await page.goto("/moderation");
    await page.getByPlaceholder("Токен").fill("any-mock-token");
    await page.getByRole("button", { name: /Войти/i }).click();

    // After successful mock login, sidebar tab buttons appear
    await expect(page.getByRole("button", { name: /Очередь/ })).toBeVisible({ timeout: 3000 });
    await expect(page.getByRole("button", { name: /Опубликованные/ })).toBeVisible();
    await expect(page.getByRole("button", { name: /Удалённые/ })).toBeVisible();
    await expect(page.getByRole("button", { name: /Мониторинг/ })).toBeVisible();
  });

  test("monitoring tab shows service cards", async ({ page }) => {
    await page.goto("/moderation");
    await page.getByPlaceholder("Токен").fill("any-mock-token");
    await page.getByRole("button", { name: /Войти/i }).click();
    await page.getByText("Мониторинг").click();
    await expect(page.getByText("Статус сервисов")).toBeVisible({ timeout: 3000 });
    await expect(page.getByText("База данных")).toBeVisible();
    await expect(page.getByText(/Telegram/)).toBeVisible();
  });

  test("published tab has date filter inputs", async ({ page }) => {
    await page.goto("/moderation");
    await page.getByPlaceholder("Токен").fill("any-mock-token");
    await page.getByRole("button", { name: /Войти/i }).click();
    await page.getByText("Опубликованные").click();
    // Date inputs should appear in the toolbar
    const dateInputs = page.locator('input[type="date"]');
    await expect(dateInputs.first()).toBeVisible({ timeout: 3000 });
  });

  test("← Карта button returns to map", async ({ page }) => {
    await page.goto("/moderation");
    await page.getByPlaceholder("Токен").fill("any-mock-token");
    await page.getByRole("button", { name: /Войти/i }).click();
    await page.getByText("← Карта").click();
    await expect(page).toHaveURL(/\/map|\/$/);
  });
});
