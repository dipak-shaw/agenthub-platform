import { expect, test } from "@playwright/test";

test("offline chat streams sources, regenerates, stops, renames, and deletes", async ({
  page,
}) => {
  await page.goto("/");
  await expect(page.getByText("What are we exploring today?")).toBeVisible();
  await page
    .getByRole("link")
    .filter({ has: page.getByRole("heading", { name: "Search Bot" }) })
    .click();
  await expect(page.getByText(/Demo mode ·/)).toBeVisible();
  await page
    .getByRole("button", { name: "Search the latest research" })
    .click();
  await expect(
    page.getByRole("button", { name: "Stop response" }),
  ).toBeVisible();
  await expect(page.getByLabel("Sources")).toContainText(
    "Lumen Research Notes",
  );
  await expect(
    page.getByRole("button", { name: "Send message" }),
  ).toBeVisible();
  await expect(
    page.getByRole("link", { name: "1", exact: true }),
  ).toHaveAttribute("href", "https://lumen.example/notes");
  await page.getByRole("button", { name: "Regenerate response" }).click();
  await expect(
    page.getByRole("button", { name: "Stop response" }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Send message" }),
  ).toBeVisible();
  await page
    .getByRole("textbox", { name: "Message" })
    .fill("Explain something thoughtfully");
  await page.getByRole("textbox", { name: "Message" }).press("Enter");
  await expect(page.getByLabel("Generating")).toBeVisible();
  await page.getByRole("button", { name: "Stop response" }).click();
  await expect(page.getByText("Response stopped")).toBeVisible();
  await page.getByLabel("Actions for Search the latest research").click();
  await page.getByRole("button", { name: "Rename", exact: true }).click();
  await page
    .getByRole("textbox", { name: "Conversation title" })
    .fill("Fictional learning notes");
  await page.getByRole("button", { name: "Save", exact: true }).click();
  await expect(
    page.getByRole("link", { name: "Fictional learning notes" }),
  ).toBeVisible();
  await page.reload();
  await expect(page.getByText("Response stopped")).toBeVisible();
  await page.getByLabel("Actions for Fictional learning notes").click();
  await page.getByRole("button", { name: "Delete", exact: true }).click();
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Delete", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Meet Search Bot" }),
  ).toBeVisible();
  await expect(
    page.getByRole("link", { name: "Fictional learning notes" }),
  ).toHaveCount(0);
});

test("mobile navigation and themes work without overflow", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/agents/plain-bot");
  await page.getByRole("button", { name: "Open navigation" }).click();
  await expect(page.getByRole("link", { name: "All agents" })).toBeVisible();
  await page.getByRole("button", { name: "Close navigation" }).click();
  await page.getByRole("button", { name: "Use dark theme" }).click();
  await expect(page.locator("html")).toHaveClass("dark");
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBeTruthy();
});
