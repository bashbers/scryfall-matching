/* This file is generated from backend/openapi.json. Do not edit manually. */

export type ApiError = {
  "code": string;
  "message": string;
};

export type CardResponse = {
  "id": string;
  "name": string;
  "frontImageUrl": string;
  "backImageUrl": string | unknown;
  "isDoubleSided": boolean;
  "commanderLegal": boolean;
  "scryfallUrl": string;
};

export type LiveHealthResponse = {
  "status": "live";
};

export type RandomCardsResponse = {
  "cards": Array<CardResponse>;
};

export type ReadyHealthResponse = {
  "status": "ready" | "empty" | "unavailable";
  "datasetVersion": string;
  "cardCount": number;
  "loadedAt": string | unknown;
};

export type Card = CardResponse;

export async function getRandomCards(
  baseUrl: string,
  signal?: AbortSignal,
): Promise<RandomCardsResponse> {
  const response = await fetch(baseUrl + "/api/v1/cards/random", { signal });
  if (!response.ok) {
    const detail = (await response.json().catch(() => undefined)) as ApiError | undefined;
    throw new ApiRequestError(response.status, detail);
  }
  return (await response.json()) as RandomCardsResponse;
}

export class ApiRequestError extends Error {
  public constructor(
    public readonly status: number,
    public readonly detail: ApiError | undefined,
  ) {
    super(detail?.message ?? "API request failed with status " + status + ".");
  }
}
