import { test, expect } from "@playwright/test";
test("real API: account selection, WIN/LOSS, limits, closure and persistent journal", async ({
  page,
}) => {
  await page.goto("/sessions");
  await expect(page).toHaveURL(/login/);
  await page.getByLabel("Email").fill("qa@example.com");
  await page.getByLabel("Password").fill("browser-test-only");
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page).toHaveURL(/dashboard/);
  await page
    .getByLabel("Trading account")
    .selectOption({ label: "QA EUR · EUR" });
  await expect(page.getByText(/750[.,]00/)).toBeVisible();
  await page
    .getByLabel("Trading account")
    .selectOption({ label: "QA USD · USD" });
  await page.getByRole("link", { name: "Start session" }).first().click();
  await expect(page.getByText(/20[.,]00/, { exact: true })).toBeVisible();
  const startRequest = page.waitForRequest(
    (request) =>
      request.method() === "POST" && request.url().endsWith("/sessions"),
  );
  await page
    .getByRole("button", { name: "Start session", exact: true })
    .click();
  await expect(page).toHaveURL(/sessions\/\d+/);
  expect((await startRequest).postDataJSON()).toEqual({
    trading_account_id: 1,
  });
  const sessionUrl = page.url();
  for (const result of ["WIN", "LOSS"]) {
    await page.getByRole("button", { name: "Record trade" }).click();
    await page.getByLabel("Symbol", { exact: true }).fill("EURUSD");
    await page.getByLabel("Payout %").fill("84");
    await page.getByLabel("Opened at").fill("2026-09-19T10:00");
    await page
      .getByRole("combobox", { name: "Result", exact: true })
      .selectOption(result);
    if (result === "WIN") {
      await page.getByLabel("Stake", { exact: true }).fill("20.01");
      await page.getByRole("button", { name: "Save trade" }).click();
      await expect(
        page.getByText("Stake exceeds per-trade risk limit", { exact: true }),
      ).toBeVisible();
      await page.getByLabel("Stake", { exact: true }).fill("20.00");
    }
    await page.getByRole("button", { name: "Save trade" }).click();
    await expect(page.getByRole("button", { name: "Save trade" })).toHaveCount(
      0,
    );
  }
  await expect(page.getByText(/Loss consumed: 3[.,]37/)).toBeVisible();
  await expect(page.getByText(/Remaining risk: 36[.,]63/)).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Record trade" }),
  ).toBeEnabled();
  const beforeLedger = await (
    await page.request.get("http://localhost:8010/api/v1/accounts/1/ledger")
  ).json();
  expect(beforeLedger).toHaveLength(3);
  for (const result of ["DRAW", "CANCELLED"]) {
    await page.getByRole("button", { name: "Record trade" }).click();
    await page.getByLabel("Symbol", { exact: true }).fill("EURUSD");
    await page.getByLabel("Opened at").fill("2026-09-19T10:01");
    await page
      .getByRole("combobox", { name: "Result", exact: true })
      .selectOption(result);
    await page.getByRole("button", { name: "Save trade" }).click();
    await expect(page.getByRole("button", { name: "Save trade" })).toHaveCount(
      0,
    );
  }
  const afterLedger = await (
    await page.request.get("http://localhost:8010/api/v1/accounts/1/ledger")
  ).json();
  expect(afterLedger).toEqual(beforeLedger);
  await expect(
    page.getByRole("button", { name: "Record trade" }),
  ).toBeDisabled();
  await expect(page.getByText(/Session limit reached/)).toBeVisible();
  await expect(page.getByText(/1[.,]996[.,]63/, { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Add note", exact: true }).click();
  await page
    .getByLabel("Note", { exact: true })
    .fill("Respected the session limit.");
  await page.getByRole("button", { name: "Save note" }).click();
  await expect(page.getByText("Respected the session limit.")).toBeVisible();
  await page
    .getByRole("button", { name: "Close session", exact: true })
    .click();
  await page.getByRole("button", { name: "Confirm close" }).click();
  await expect(page.getByText("CLOSED", { exact: true })).toBeVisible();
  await page.reload();
  await expect(page.getByText("CLOSED", { exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "Record trade" })).toHaveCount(
    0,
  );
  await expect(page.getByText("Respected the session limit.")).toBeVisible();
  await page.screenshot({
    path: "test-results/req002-desktop.png",
    fullPage: true,
  });
  await page.getByRole("link", { name: "Journal", exact: true }).click();
  await expect(page.getByText("Respected the session limit.")).toBeVisible();
  await page.setViewportSize({ width: 768, height: 1024 });
  await page.goto(sessionUrl);
  await expect(page.getByText("CLOSED", { exact: true })).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
  await page.screenshot({
    path: "test-results/req002-tablet.png",
    fullPage: true,
  });
  await page.getByRole("link", { name: "Sessions", exact: true }).click();
  await page
    .getByRole("combobox", { name: "Status", exact: true })
    .selectOption("CLOSED");
  await expect(
    page.getByRole("cell", { name: "CLOSED", exact: true }),
  ).toBeVisible();
  await page
    .getByRole("combobox", { name: "Status", exact: true })
    .selectOption("OPEN");
  await expect(page.getByText("No sessions for these filters.")).toBeVisible();
  await page.getByRole("link", { name: "Accounts", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "QA USD", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("cell", { name: "TRADE_PROFIT", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("cell", { name: "TRADE_LOSS", exact: true }),
  ).toBeVisible();
  const token = (await page.context().cookies()).find(
    (cookie) => cookie.name === "access_token",
  );
  expect(token?.httpOnly).toBe(true);
  await page.getByRole("button", { name: "Sign out", exact: true }).click();
  await expect(page).toHaveURL(/login/);
  await page.goto(sessionUrl);
  await expect(page).toHaveURL(/login/);
});
