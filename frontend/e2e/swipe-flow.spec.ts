import { expect, test } from "@playwright/test";

const cards = [
  {
    id: "e2e-one",
    name: "E2E One",
    frontImageUrl: "https://images.example.test/one.jpg",
    backImageUrl: null,
    isDoubleSided: false,
    commanderLegal: true,
    scryfallUrl: "https://scryfall.com/card/test/1",
  },
  {
    id: "e2e-two",
    name: "E2E Two",
    frontImageUrl: "https://images.example.test/two.jpg",
    backImageUrl: null,
    isDoubleSided: false,
    commanderLegal: false,
    scryfallUrl: "https://scryfall.com/card/test/2",
  },
  {
    id: "e2e-three",
    name: "E2E Three",
    frontImageUrl: "https://images.example.test/three.jpg",
    backImageUrl: null,
    isDoubleSided: false,
    commanderLegal: false,
    scryfallUrl: "https://scryfall.com/card/test/3",
  },
  {
    id: "e2e-four",
    name: "E2E Four",
    frontImageUrl: "https://images.example.test/four.jpg",
    backImageUrl: null,
    isDoubleSided: false,
    commanderLegal: false,
    scryfallUrl: "https://scryfall.com/card/test/4",
  },
  {
    id: "e2e-five",
    name: "E2E Five",
    frontImageUrl: "https://images.example.test/five.jpg",
    backImageUrl: null,
    isDoubleSided: false,
    commanderLegal: false,
    scryfallUrl: "https://scryfall.com/card/test/5",
  },
];

test("likes, dislikes, and shows history without relying on image delivery", async ({
  page,
}) => {
  await page.route("**/api/v1/cards/random", (route) =>
    route.fulfill({ json: { cards } }),
  );
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "E2E One" })).toBeVisible();

  await page.getByRole("button", { name: "Liken" }).click();
  await expect(page.getByRole("heading", { name: "E2E Two" })).toBeVisible();
  await page.getByRole("button", { name: "Afwijzen" }).click();
  await expect(page.getByRole("heading", { name: "E2E Three" })).toBeVisible();

  await page.reload();

  await page.getByRole("link", { name: "Likes", exact: true }).click();
  await expect(page.getByRole("link", { name: "E2E One" })).toBeVisible();
  await page.getByRole("link", { name: "Dislikes" }).click();
  await expect(page.getByRole("link", { name: "E2E Two" })).toBeVisible();
  await page.getByRole("link", { name: "Historie" }).click();
  await expect(page.getByRole("link", { name: "E2E One" })).toBeVisible();
  await expect(page.getByRole("link", { name: "E2E Two" })).toBeVisible();
});

test("shows retry UI after a network failure", async ({ page }) => {
  await page.route("**/api/v1/cards/random", (route) => route.abort("failed"));
  await page.goto("/");

  await expect(
    page.getByRole("button", { name: "Opnieuw proberen" }),
  ).toBeVisible({ timeout: 10_000 });
});

test("supports mouse swipe on the card image", async ({ page }) => {
  await page.route("**/api/v1/cards/random", (route) =>
    route.fulfill({ json: { cards } }),
  );
  await page.goto("/");
  const image = page.locator(".card-image-wrap");
  const box = await image.boundingBox();
  if (!box) {
    throw new Error("Card image did not render.");
  }

  await page.mouse.move(box.x + 40, box.y + box.height / 2);
  await page.mouse.down();
  await page.mouse.move(box.x + 160, box.y + box.height / 2);
  await page.mouse.up();

  await expect(page.getByRole("heading", { name: "E2E Two" })).toBeVisible();
  await expect(page.locator(".card-image-wrap")).toHaveCSS("transform", "none");
  await expect(page.getByRole("article")).toHaveCSS("transform", "none");
});

test("keeps a visible stack and keyboard focus while selecting cards", async ({
  page,
}) => {
  await page.route("**/api/v1/cards/random", (route) =>
    route.fulfill({ json: { cards } }),
  );
  await page.goto("/");

  await expect(page.locator(".card-stack-preview")).toHaveCount(3);
  const activeCard = page.getByRole("article");
  await activeCard.press("ArrowRight");
  await expect(page.getByRole("heading", { name: "E2E Two" })).toBeVisible();
  await expect(activeCard).toBeFocused();
});

test("does not overflow the header on a narrow viewport", async ({ page }) => {
  await page.setViewportSize({ width: 320, height: 700 });
  await page.route("**/api/v1/cards/random", (route) =>
    route.fulfill({ json: { cards } }),
  );
  await page.goto("/");

  const widths = await page.evaluate(() => ({
    viewport: window.innerWidth,
    document: document.documentElement.scrollWidth,
  }));
  expect(widths.document).toBeLessThanOrEqual(widths.viewport);
});

test("honors reduced-motion preferences", async ({ page }) => {
  await page.route("**/api/v1/cards/random", (route) =>
    route.fulfill({ json: { cards } }),
  );
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/");

  const transitionDuration = await page
    .locator(".card-swiper")
    .evaluate((element) => getComputedStyle(element).transitionDuration);
  expect(Number.parseFloat(transitionDuration)).toBeCloseTo(0.00001);
});
