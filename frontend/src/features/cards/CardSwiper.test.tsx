import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expect, test, vi } from "vitest";
import { sampleCard } from "../../test/fixtures";
import { CardSwiper } from "./CardSwiper";

function renderSwiper(card = sampleCard, queuedCards = [] as typeof sampleCard[]) {
  const onLike = vi.fn();
  const onDislike = vi.fn();
  const onViewed = vi.fn();
  const rendered = render(
    <CardSwiper
      card={card}
      queuedCards={queuedCards}
      onLike={onLike}
      onDislike={onDislike}
      onViewed={onViewed}
    />,
  );
  return { ...rendered, onLike, onDislike, onViewed };
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

test("starts the matching swipe animation for keyboard actions", () => {
  renderSwiper();
  const card = screen.getByRole("article");

  fireEvent.keyDown(card, { key: "ArrowRight" });

  expect(screen.getByText("LIKE")).toBeInTheDocument();
});

test("keeps the active card focused after the card changes", () => {
  const onLike = vi.fn();
  const onDislike = vi.fn();
  const onViewed = vi.fn();
  const { rerender } = render(
    <CardSwiper card={sampleCard} queuedCards={[]} onLike={onLike} onDislike={onDislike} onViewed={onViewed} />,
  );
  screen.getByRole("article").focus();

  rerender(
    <CardSwiper
      card={{ ...sampleCard, id: "next-card", name: "Next Card" }}
      queuedCards={[]}
      onLike={onLike}
      onDislike={onDislike}
      onViewed={onViewed}
    />,
  );

  expect(screen.getByRole("article")).toHaveFocus();
});

test("shows already fetched cards as previews underneath the active card", () => {
  const { container } = renderSwiper(sampleCard, [
    { ...sampleCard, id: "queued-one", name: "Queued One" },
    { ...sampleCard, id: "queued-two", name: "Queued Two" },
  ]);

  expect(container.querySelectorAll(".card-stack-preview")).toHaveLength(2);
});

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
