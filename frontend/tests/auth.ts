import type { Page } from "@playwright/test";

export const TEST_USERNAME = "user";
export const TEST_PASSWORD = "password";

export async function loginViaApi(page: Page) {
  const response = await page.request.post("/api/login", {
    data: { username: TEST_USERNAME, password: TEST_PASSWORD },
  });
  if (!response.ok()) {
    throw new Error(`Login failed: ${response.status()}`);
  }
}
