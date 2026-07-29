import { expect, test } from "@playwright/test";
import { loginViaApi } from "./auth";

test.beforeEach(async ({ page }) => {
  await loginViaApi(page);
});

test("loads the kanban board", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Kanban Studio" })).toBeVisible();
  await expect(page.locator('[data-testid^="column-"]')).toHaveCount(5);
});

test("adds a card to a column", async ({ page }) => {
  await page.goto("/");
  const firstColumn = page.locator('[data-testid^="column-"]').first();
  await firstColumn.getByRole("button", { name: /add a card/i }).click();
  await firstColumn.getByPlaceholder("Card title").fill("Playwright card");
  await firstColumn.getByPlaceholder("Details").fill("Added via e2e.");
  await firstColumn.getByRole("button", { name: /add card/i }).click();
  await expect(firstColumn.getByText("Playwright card")).toBeVisible();
});

test("persists state across a reload", async ({ page }) => {
  await page.goto("/");
  const firstColumn = page.locator('[data-testid^="column-"]').first();
  await firstColumn.getByRole("button", { name: /add a card/i }).click();
  await firstColumn.getByPlaceholder("Card title").fill("Reload persistence card");
  await firstColumn.getByPlaceholder("Details").fill("Should survive a reload.");

  const [response] = await Promise.all([
    page.waitForResponse(
      (res) => res.request().method() === "POST" && res.url().includes("/cards")
    ),
    firstColumn.getByRole("button", { name: /add card/i }).click(),
  ]);
  expect(response.ok()).toBeTruthy();

  await expect(firstColumn.getByText("Reload persistence card")).toBeVisible();

  await page.reload();

  await expect(
    page
      .locator('[data-testid^="column-"]')
      .first()
      .getByText("Reload persistence card")
  ).toBeVisible();
});

test("moves a card between columns", async ({ page }) => {
  await page.goto("/");
  const card = page.getByTestId("card-card-1");
  // Adjacent to the source column (col-backlog) so both stay within the
  // viewport at once — the columns row scrolls horizontally now that it
  // has a fixed comfortable width per column, so a distant target column
  // can be scrolled out of view depending on viewport width.
  const targetColumn = page.getByTestId("column-col-discovery");
  const cardBox = await card.boundingBox();
  const columnBox = await targetColumn.boundingBox();
  if (!cardBox || !columnBox) {
    throw new Error("Unable to resolve drag coordinates.");
  }

  await page.mouse.move(
    cardBox.x + cardBox.width / 2,
    cardBox.y + cardBox.height / 2
  );
  await page.mouse.down();
  await page.mouse.move(
    columnBox.x + columnBox.width / 2,
    columnBox.y + 120,
    { steps: 12 }
  );
  await page.mouse.up();
  await expect(targetColumn.getByTestId("card-card-1")).toBeVisible();
});
