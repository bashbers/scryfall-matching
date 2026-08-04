import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, renderHook, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { beforeEach, expect, test, vi } from "vitest";
import { getRandomCards } from "../../api/client";
import { sampleCard } from "../../test/fixtures";
import { useCardQueue } from "./useCardQueue";

vi.mock("../../api/client", () => ({ getRandomCards: vi.fn() }));

const mockedGetRandomCards = vi.mocked(getRandomCards);

beforeEach(() => {
  mockedGetRandomCards.mockReset();
});

function wrapper({ children }: { children: ReactNode }) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}

function cards(prefix: string) {
  return Array.from({ length: 5 }, (_, index) => ({
    ...sampleCard,
    id: `${prefix}-${index}`,
    name: `${prefix} ${index}`,
  }));
}

test("keeps duplicate cards out of the active queue and prefetches at two remaining cards", async () => {
  const firstBatch = cards("first");
  const secondBatch = [firstBatch[4], ...cards("second").slice(1)];
  mockedGetRandomCards.mockResolvedValueOnce({ cards: firstBatch }).mockResolvedValueOnce({ cards: secondBatch });

  const { result } = renderHook(() => useCardQueue(), { wrapper });
  await waitFor(() => expect(result.current.cardsRemaining).toBe(5));

  act(() => {
    result.current.dismissActiveCard();
    result.current.dismissActiveCard();
    result.current.dismissActiveCard();
  });
  await waitFor(() => expect(mockedGetRandomCards).toHaveBeenCalledTimes(2));
  await waitFor(() => expect(result.current.cardsRemaining).toBe(6));
});

test("shows its error only while no active card is available", async () => {
  mockedGetRandomCards.mockRejectedValue(new Error("offline"));
  const { result } = renderHook(() => useCardQueue({ retryDelays: [1, 1, 1] }), { wrapper });

  await waitFor(() => expect(result.current.error?.message).toBe("offline"));

  expect(result.current.activeCard).toBeUndefined();
  expect(result.current.isLoading).toBe(false);
});
