import { createContext, useContext, useEffect, useState } from "react";
import type { Card } from "../../api/generated";

type StoredListName = "likedCards" | "dislikedCards" | "seenCards";

type CardPreferences = {
  likedCards: Card[];
  dislikedCards: Card[];
  seenCards: Card[];
  storageWarning: string | null;
  like: (card: Card) => void;
  dislike: (card: Card) => void;
  markSeen: (card: Card) => void;
  remove: (list: StoredListName, cardId: string) => void;
};

const CardPreferencesContext = createContext<CardPreferences | null>(null);

export function CardPreferencesProvider({ children }: { children: React.ReactNode }) {
  const [likedCards, setLikedCards] = useStoredCards("likedCards");
  const [dislikedCards, setDislikedCards] = useStoredCards("dislikedCards");
  const [seenCards, setSeenCards] = useStoredCards("seenCards");
  const [storageWarning, setStorageWarning] = useState<string | null>(null);

  const update = (setter: React.Dispatch<React.SetStateAction<Card[]>>, card: Card) => {
    setter((current) => appendUnique(current, card));
  };
  const value: CardPreferences = {
    likedCards,
    dislikedCards,
    seenCards,
    storageWarning,
    like: (card) => {
      update(setLikedCards, card);
      setDislikedCards((current) => current.filter((item) => item.id !== card.id));
    },
    dislike: (card) => {
      update(setDislikedCards, card);
      setLikedCards((current) => current.filter((item) => item.id !== card.id));
    },
    markSeen: (card) => update(setSeenCards, card),
    remove: (list, cardId) => {
      const setter = { likedCards: setLikedCards, dislikedCards: setDislikedCards, seenCards: setSeenCards }[
        list
      ];
      setter((current) => current.filter((card) => card.id !== cardId));
    },
  };

  useEffect(() => {
    let storageFailed = false;
    for (const [key, cards] of Object.entries({ likedCards, dislikedCards, seenCards })) {
      try {
        window.localStorage.setItem(key, JSON.stringify(cards));
      } catch {
        storageFailed = true;
      }
    }
    setStorageWarning(
      storageFailed ? "Lokale opslag is vol; je keuzes blijven alleen in deze sessie beschikbaar." : null,
    );
  }, [dislikedCards, likedCards, seenCards]);

  return <CardPreferencesContext.Provider value={value}>{children}</CardPreferencesContext.Provider>;
}

export function useCardPreferences(): CardPreferences {
  const preferences = useContext(CardPreferencesContext);
  if (!preferences) {
    throw new Error("useCardPreferences must be used inside CardPreferencesProvider.");
  }
  return preferences;
}

function useStoredCards(key: StoredListName): [Card[], React.Dispatch<React.SetStateAction<Card[]>>] {
  const [cards, setCards] = useState<Card[]>(() => {
    try {
      const value = window.localStorage.getItem(key);
      return value ? parseCards(value) : [];
    } catch {
      return [];
    }
  });
  return [cards, setCards];
}

function appendUnique(cards: Card[], card: Card): Card[] {
  return cards.some((item) => item.id === card.id) ? cards : [...cards, card];
}

function parseCards(value: string): Card[] {
  const parsed = JSON.parse(value);
  if (!Array.isArray(parsed)) {
    return [];
  }
  return parsed.filter(isCard).reduce<Card[]>(appendUnique, []);
}

function isCard(value: unknown): value is Card {
  if (!value || typeof value !== "object") {
    return false;
  }
  const card = value as Record<string, unknown>;
  return (
    typeof card.id === "string" &&
    typeof card.name === "string" &&
    typeof card.frontImageUrl === "string" &&
    (typeof card.backImageUrl === "string" || card.backImageUrl === null) &&
    typeof card.isDoubleSided === "boolean" &&
    typeof card.commanderLegal === "boolean" &&
    typeof card.scryfallUrl === "string"
  );
}
