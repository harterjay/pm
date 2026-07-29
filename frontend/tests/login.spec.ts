import { expect, test } from "@playwright/test";
import { TEST_PASSWORD, TEST_USERNAME } from "./auth";

test("redirects unauthenticated visits to /login", async ({ page }) => {
  await page.goto("/");
  await expect(page).toHaveURL(/\/login$/);
  await expect(
    page.getByRole("heading", { name: "Kanban Studio" })
  ).toBeVisible();
});

test("rejects the wrong password", async ({ page }) => {
  await page.goto("/login");
  await page.getByLabel("Username").fill(TEST_USERNAME);
  await page.getByLabel("Password").fill("wrong-password");
  await page.getByRole("button", { name: /log in/i }).click();

  await expect(page.getByTestId("login-error")).toHaveText(
    "Invalid username or password."
  );
  await expect(page).toHaveURL(/\/login$/);
});

test("logs in, sees the board, logs out, and lands back on /login", async ({
  page,
}) => {
  await page.goto("/login");
  await page.getByLabel("Username").fill(TEST_USERNAME);
  await page.getByLabel("Password").fill(TEST_PASSWORD);
  await page.getByRole("button", { name: /log in/i }).click();

  await expect(page).toHaveURL(/\/$/);
  await expect(
    page.getByRole("heading", { name: "Kanban Studio" })
  ).toBeVisible();

  await page.getByRole("button", { name: /log out/i }).click();
  await expect(page).toHaveURL(/\/login$/);
});

test("redirects authenticated visits away from /login", async ({ page }) => {
  await page.goto("/login");
  await page.getByLabel("Username").fill(TEST_USERNAME);
  await page.getByLabel("Password").fill(TEST_PASSWORD);
  await page.getByRole("button", { name: /log in/i }).click();
  await expect(page).toHaveURL(/\/$/);

  await page.goto("/login");
  await expect(page).toHaveURL(/\/$/);
});
