import { useQuery } from "@tanstack/react-query";
import { useEffect, useMemo, useState } from "react";
import { getRandomCards } from "../../api/client";
import type { Card } from "../../api/generated";

const RETRY_DELAYS = [500, 1_000, 2_000] as const;
const PREFETCH_THRESHOLD = 2;

export type CardQueue = {
  activeCard: Card | undefined;
  cardsRemaining: number;
  dismissActiveCard: () => void;
  isLoading: boolean;
  isRefreshing: boolean;
  error: Error | null;
  retry: () => void;
};

export function useCardQueue(): CardQueue {
  const [queue, setQueue] = useState<Card[]>([]);
  const [requestNumber, setRequestNumber] = useState(0);
  const [appliedRequest, setAppliedRequest] = useState(-1);
  const shouldFetch = queue.length <= PREFETCH_THRESHOLD;
  const { data, error, isFetching, isLoading, refetch } = useQuery({
    queryKey: ["cards", "random-batch", requestNumber],
    queryFn: ({ signal }) => getRandomCards(signal),
    enabled: shouldFetch && requestNumber !== appliedRequest,
    retry: RETRY_DELAYS.length,
    retryDelay: (attemptIndex) => RETRY_DELAYS[attemptIndex] ?? RETRY_DELAYS[2],
  });

  useEffect(() => {
    if (!shouldFetch || isFetching || requestNumber !== appliedRequest) {
      return;
    }
    setRequestNumber((current) => current + 1);
  }, [appliedRequest, isFetching, requestNumber, shouldFetch]);

  useEffect(() => {
    if (!data || appliedRequest === requestNumber) {
      return;
    }
    setQueue((current) => {
      const activeIds = new Set(current.map((card) => card.id));
      const uniqueCards = data.cards.filter((card) => {
        if (activeIds.has(card.id)) {
          return false;
        }
        activeIds.add(card.id);
        return true;
      });
      return [...current, ...uniqueCards];
    });
    setAppliedRequest(requestNumber);
  }, [appliedRequest, data, requestNumber]);

  const activeCard = queue[0];
  return useMemo(
    () => ({
      activeCard,
      cardsRemaining: queue.length,
      dismissActiveCard: () => setQueue((current) => current.slice(1)),
      isLoading: !activeCard && isLoading,
      isRefreshing: isFetching,
      error,
      retry: () => void refetch(),
    }),
    [activeCard, error, isFetching, isLoading, queue.length, refetch],
  );
}
