import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expect, test, vi } from "vitest";
import { sampleCard } from "../../test/fixtures";
import { CardSwiper } from "./CardSwiper";

function renderSwiper(card = sampleCard) {
  const onLike = vi.fn();
  const onDislike = vi.fn();
  const onViewed = vi.fn();
  render(<CardSwiper card={card} onLike={onLike} onDislike={onDislike} onViewed={onViewed} />);
  return { onLike, onDislike, onViewed };
}

test("shows commander status, tracks viewing, and flips double-faced cards", async () => {
  const user = userEvent.setup();
  const { onViewed } = renderSwiper();

  expect(onViewed).toHaveBeenCalledOnce();
  expect(screen.getByText("Commander-legal")).toBeInTheDocument();
  expect(screen.getByRole("img", { name: "Sample Card" })).toHaveAttribute("src", sampleCard.frontImageUrl);

  await user.click(screen.getByRole("button", { name: "Draai om" }));

  expect(screen.getByRole("img", { name: "Sample Card" })).toHaveAttribute("src", sampleCard.backImageUrl);
});

test("supports keyboard swipe actions", () => {
  const { onLike, onDislike } = renderSwiper();
  const card = screen.getByRole("article");

  fireEvent.keyDown(card, { key: "ArrowRight" });
  fireEvent.keyDown(card, { key: "ArrowLeft" });

  expect(onLike).toHaveBeenCalledOnce();
  expect(onDislike).toHaveBeenCalledOnce();
});

test("supports touch swipes on the card image", () => {
  const { onLike } = renderSwiper();
  const image = screen.getByRole("img", { name: "Sample Card" });

  fireEvent(image, pointerEvent("pointerdown", 20));
  fireEvent(image, pointerEvent("pointerup", 120));

  expect(onLike).toHaveBeenCalledOnce();
});

function pointerEvent(type: string, clientX: number): Event {
  const event = new Event(type, { bubbles: true });
  Object.defineProperties(event, {
    clientX: { value: clientX },
    pointerId: { value: 1 },
    pointerType: { value: "touch" },
  });
  return event;
}

test("uses a local back and keeps the other face usable after an image error", async () => {
  const user = userEvent.setup();
  const { onViewed } = renderSwiper({ ...sampleCard, isDoubleSided: false, backImageUrl: null });
  const image = screen.getByRole("img", { name: "Sample Card" });

  fireEvent.error(image);
  expect(screen.getByText("Afbeelding niet beschikbaar")).toBeInTheDocument();
  await user.click(screen.getByRole("button", { name: "Draai om" }));

  expect(screen.getByRole("img", { name: "Sample Card" }).getAttribute("src")).toContain("card-back");
  expect(onViewed).toHaveBeenCalledOnce();
});
