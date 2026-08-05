import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expect, test } from "vitest";
import { sampleCard } from "../../test/fixtures";
import { CardPreferencesProvider, useCardPreferences } from "./CardPreferences";

function PreferencesHarness() {
  const preferences = useCardPreferences();
  return (
    <>
      <button type="button" onClick={() => preferences.like(sampleCard)}>
        Like
      </button>
      <button type="button" onClick={() => preferences.dislike(sampleCard)}>
        Dislike
      </button>
      <button type="button" onClick={() => preferences.markSeen(sampleCard)}>
        Seen
      </button>
      <p>
        {preferences.likedCards.length}/{preferences.dislikedCards.length}/
        {preferences.seenCards.length}
      </p>
    </>
  );
}

test("persists deduplicated likes, dislikes, and seen cards", async () => {
  const user = userEvent.setup();
  render(
    <CardPreferencesProvider>
      <PreferencesHarness />
    </CardPreferencesProvider>,
  );

  await user.click(screen.getByRole("button", { name: "Like" }));
  await user.click(screen.getByRole("button", { name: "Like" }));
  await user.click(screen.getByRole("button", { name: "Seen" }));
  await user.click(screen.getByRole("button", { name: "Dislike" }));

  expect(screen.getByText("0/1/1")).toBeInTheDocument();
  expect(
    JSON.parse(window.localStorage.getItem("dislikedCards") ?? "[]"),
  ).toHaveLength(1);
  expect(
    JSON.parse(window.localStorage.getItem("seenCards") ?? "[]"),
  ).toHaveLength(1);
});

test("ignores malformed and duplicate persisted values", () => {
  window.localStorage.setItem(
    "likedCards",
    JSON.stringify([sampleCard, sampleCard, null]),
  );
  render(
    <CardPreferencesProvider>
      <PreferencesHarness />
    </CardPreferencesProvider>,
  );

  expect(screen.getByText("1/0/0")).toBeInTheDocument();
});
