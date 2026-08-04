import type { Card } from "../api/generated";

export const sampleCard: Card = {
  id: "card-one",
  name: "Sample Card",
  frontImageUrl: "https://images.example.test/front.jpg",
  backImageUrl: "https://images.example.test/back.jpg",
  isDoubleSided: true,
  commanderLegal: true,
  scryfallUrl: "https://scryfall.com/card/test/1",
};
