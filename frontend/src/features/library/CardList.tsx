import type { Card } from "../../api/generated";

type CardListProps = {
  cards: Card[];
  emptyMessage: string;
  onRemove: (cardId: string) => void;
};

export function CardList({ cards, emptyMessage, onRemove }: CardListProps) {
  if (!cards.length) {
    return <p>{emptyMessage}</p>;
  }
  return (
    <ul className="card-list">
      {cards.map((card) => (
        <li key={card.id}>
          <a href={card.scryfallUrl} target="_blank" rel="noreferrer">
            {card.name}
          </a>
          <button type="button" onClick={() => onRemove(card.id)} aria-label={`${card.name} verwijderen`}>
            Verwijderen
          </button>
        </li>
      ))}
    </ul>
  );
}
