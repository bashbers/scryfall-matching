import { getRandomCards as generatedGetRandomCards } from "./generated";
import type { RandomCardsResponse } from "./generated";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "";

export async function getRandomCards(
  signal?: AbortSignal,
): Promise<RandomCardsResponse> {
  return generatedGetRandomCards(API_BASE_URL, signal);
}
