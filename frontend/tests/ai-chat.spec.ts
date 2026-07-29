import { expect, test } from "@playwright/test";
import { loginViaApi } from "./auth";

test.beforeEach(async ({ page }) => {
  await loginViaApi(page);
});

test("adds a card via the AI chat widget", async ({ page }) => {
  test.setTimeout(90_000);
  await page.goto("/");

  // Minimized by default — expand it before interacting.
  await page.getByTestId("chat-toggle").click();
  await page
    .getByTestId("chat-input")
    .fill("Add a card titled 'Chat-created card' to the Review column");
  await page.getByTestId("chat-send").click();

  await expect(page.getByTestId("chat-message-assistant")).toBeVisible({
    timeout: 60_000,
  });
  await expect(
    page.getByTestId("column-col-review").getByText("Chat-created card")
  ).toBeVisible();

  await page.getByTestId("chat-minimize").click();
  await expect(page.getByTestId("chat-toggle")).toBeVisible();
  await expect(page.getByTestId("chat-input")).not.toBeVisible();
});
