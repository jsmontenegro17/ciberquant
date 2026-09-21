import { test, expect } from "@playwright/test";
test("real API: account selection, WIN/LOSS, limits, closure and persistent journal", async ({
  page,
}) => {
  async function saveTrade(expectedStatus = 200) {
    const response = page.waitForResponse(r => r.request().method() === 'POST' && new URL(r.url()).pathname === '/api/v1/trades');
    await page.getByRole('button', {name:"Guardar operación",exact:true}).click();
    expect((await response).status()).toBe(expectedStatus);
    if (expectedStatus === 200) {
      // Saving… removes the old button name BEFORE mutation completion.
      // Wait for the form lifecycle, not the transient button label.
      await expect(page.getByRole('heading',{name:"Registrar operación",exact:true})).toHaveCount(0);
    }
  }
  await page.goto("/sessions");
  await expect(page).toHaveURL(/login/);
  await page.getByLabel("Correo electrónico").fill("qa@example.com");
  await page.getByLabel("Contraseña").fill("browser-test-only");
  await page.getByRole("button", { name: "Iniciar sesión" }).click();
  await expect(page).toHaveURL(/start/);
  await page.locator("aside").getByRole("link", {name:"Resumen",exact:true}).click();
  await page
    .getByLabel("Cuenta de operaciones")
    .selectOption({ label: "QA EUR · EUR" });
  await expect(page.getByText(/750[.,]00/)).toBeVisible();
  await page
    .getByLabel("Cuenta de operaciones")
    .selectOption({ label: "QA USD · USD" });
  await page.getByRole("link", { name: "Iniciar sesión de operaciones" }).first().click();
  await expect(page.getByText(/20[.,]00/, { exact: true })).toBeVisible();
  const startRequest = page.waitForRequest(
    (request) =>
      request.method() === "POST" && request.url().endsWith("/sessions"),
  );
  await page
    .getByRole("button", { name: "Iniciar sesión de operaciones", exact: true })
    .click();
  await expect(page).toHaveURL(/sessions\/\d+/);
  expect((await startRequest).postDataJSON()).toEqual({
    trading_account_id: 1,
  });
  const sessionUrl = page.url();
  for (const result of ["WIN", "LOSS"]) {
    await page.getByRole("button", { name: "Registrar operación" }).click();
    await page.getByLabel("Símbolo", { exact: true }).fill("EURUSD");
    await page.getByLabel("Rendimiento %").fill("84");
    await page.getByLabel("Fecha de apertura").fill("2026-09-19T10:00");
    await page
      .getByRole("combobox", { name: "Resultado", exact: true })
      .selectOption(result);
    if (result === "WIN") {
      await page.getByLabel("Importe", { exact: true }).fill("20.01");
      await saveTrade(422);
      await expect(
        page.getByText("El importe supera el límite de riesgo por operación.", { exact: true }),
      ).toBeVisible();
      await page.getByLabel("Importe", { exact: true }).fill("20.00");
    }
    await saveTrade();
  }
  await expect(page.getByText(/Pérdida acumulada: 3[.,]37/)).toBeVisible();
  await expect(page.getByText(/Riesgo restante: 36[.,]63/)).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Registrar operación" }),
  ).toBeEnabled();
  const beforeLedger = await (
    await page.request.get("http://localhost:8010/api/v1/accounts/1/ledger")
  ).json();
  expect(beforeLedger).toHaveLength(3);
  for (const result of ["DRAW", "CANCELLED"]) {
    await page.getByRole("button", { name: "Registrar operación" }).click();
    await page.getByLabel("Símbolo", { exact: true }).fill("EURUSD");
    await page.getByLabel("Fecha de apertura").fill("2026-09-19T10:01");
    await page
      .getByRole("combobox", { name: "Resultado", exact: true })
      .selectOption(result);
    await saveTrade();
  }
  const afterLedger = await (
    await page.request.get("http://localhost:8010/api/v1/accounts/1/ledger")
  ).json();
  expect(afterLedger).toEqual(beforeLedger);
  await expect(
    page.getByRole("button", { name: "Registrar operación" }),
  ).toBeDisabled();
  await expect(page.getByText(/Límite de sesión alcanzado/)).toBeVisible();
  await expect(page.getByText(/1[.,]996[.,]63/, { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Añadir nota", exact: true }).click();
  await page
    .getByLabel("Nota", { exact: true })
    .fill("Respected the session limit.");
  await page.getByRole("button", { name: "Guardar nota" }).click();
  await expect(page.getByText("Respected the session limit.")).toBeVisible();
  await page
    .getByRole("button", { name: "Cerrar sesión de operaciones", exact: true })
    .click();
  await page.getByRole("button", { name: "Confirmar cierre" }).click();
  await expect(page.getByText("Cerrada (CLOSED)", { exact: true })).toBeVisible();
  await page.reload();
  await expect(page.getByText("Cerrada (CLOSED)", { exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "Registrar operación" })).toHaveCount(
    0,
  );
  await expect(page.getByText("Respected the session limit.")).toBeVisible();
  await page.screenshot({
    path: "test-results/req002-desktop.png",
    fullPage: true,
  });
  await page.locator("aside").getByRole("link", { name: "Diario", exact: true }).click();
  await expect(page.getByText("Respected the session limit.")).toBeVisible();
  await page.setViewportSize({ width: 768, height: 1024 });
  await page.goto(sessionUrl);
  await expect(page.getByText("Cerrada (CLOSED)", { exact: true })).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
  await page.screenshot({
    path: "test-results/req002-tablet.png",
    fullPage: true,
  });
  await page.locator("aside").getByRole("link", { name: "Sesiones", exact: true }).click();
  await page
    .getByRole("combobox", { name: "Estado", exact: true })
    .selectOption("CLOSED");
  await expect(
    page.getByRole("cell", { name: "Cerrada (CLOSED)", exact: true }),
  ).toBeVisible();
  await page
    .getByRole("combobox", { name: "Estado", exact: true })
    .selectOption("OPEN");
  await expect(page.getByText("No hay sesiones para estos filtros.")).toBeVisible();
  await page.locator("aside").getByRole("link", { name: "Cuentas", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "QA USD", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("cell", { name: "Ganancia de operación (TRADE_PROFIT)", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("cell", { name: "Pérdida de operación (TRADE_LOSS)", exact: true }),
  ).toBeVisible();
  const token = (await page.context().cookies()).find(
    (cookie) => cookie.name === "access_token",
  );
  expect(token?.httpOnly).toBe(true);
  await page.getByRole("button", { name: "Cerrar sesión", exact: true }).click();
  await expect(page).toHaveURL(/login/);
  await page.goto(sessionUrl);
  await expect(page).toHaveURL(/login/);
});
