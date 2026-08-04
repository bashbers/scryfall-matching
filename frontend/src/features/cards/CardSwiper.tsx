import { useEffect, useRef, useState } from "react";
import type { Card } from "../../api/generated";

const cardBackUrl = new URL("../../assets/card-back.svg", import.meta.url).href;

type CardSwiperProps = {
  card: Card;
  onLike: () => void;
  onDislike: () => void;
  onViewed: () => void;
};

const SWIPE_DISTANCE = 80;

export function CardSwiper({ card, onLike, onDislike, onViewed }: CardSwiperProps) {
  const [isFlipped, setIsFlipped] = useState(false);
  const [failedImageUrl, setFailedImageUrl] = useState<string | null>(null);
  const startX = useRef<number | null>(null);

  useEffect(() => {
    setIsFlipped(false);
    setFailedImageUrl(null);
    onViewed();
  }, [card.id, onViewed]);

  const imageUrl = isFlipped
    ? card.isDoubleSided
      ? (card.backImageUrl ?? cardBackUrl)
      : cardBackUrl
    : card.frontImageUrl;
  const toggleFlip = () => setIsFlipped((current) => !current);
  const finishSwipe = (endX: number) => {
    if (startX.current === null) {
      return;
    }
    const distance = endX - startX.current;
    startX.current = null;
    if (distance >= SWIPE_DISTANCE) {
      onLike();
    } else if (distance <= -SWIPE_DISTANCE) {
      onDislike();
    }
  };

  return (
    <article
      className="card-swiper"
      onKeyDown={(event) => {
        if (event.target !== event.currentTarget) {
          return;
        }
        if (event.key === "ArrowRight") {
          event.preventDefault();
          onLike();
        }
        if (event.key === "ArrowLeft") {
          event.preventDefault();
          onDislike();
        }
        if (event.key === " " || event.key === "Enter") {
          event.preventDefault();
          toggleFlip();
        }
      }}
      tabIndex={0}
      aria-label={`${card.name}. Pijl-rechts liken, pijl-links afwijzen, spatie omdraaien.`}
    >
      <div
        className="card-image-wrap"
        onPointerDown={(event) => {
          if (event.pointerType === "mouse" && event.button > 0) {
            return;
          }
          startX.current = event.clientX;
          event.currentTarget.setPointerCapture(event.pointerId);
        }}
        onPointerUp={(event) => finishSwipe(event.clientX)}
        onPointerCancel={() => {
          startX.current = null;
        }}
      >
        {failedImageUrl === imageUrl ? (
          <div className="image-placeholder" role="img" aria-label="Kaartafbeelding niet beschikbaar">
            Afbeelding niet beschikbaar
          </div>
        ) : (
          <img src={imageUrl} alt={card.name} onError={() => setFailedImageUrl(imageUrl)} />
        )}
      </div>
      <div className="card-details">
        <div>
          <h1>{card.name}</h1>
          {card.commanderLegal && <span className="badge">Commander-legal</span>}
        </div>
        <a href={card.scryfallUrl} target="_blank" rel="noreferrer">
          Bekijk op Scryfall
        </a>
      </div>
      <div className="card-actions" aria-label="Kaartacties">
        <button type="button" onClick={onDislike}>Afwijzen</button>
        <button type="button" onClick={toggleFlip}>Draai om</button>
        <button type="button" onClick={onLike}>Liken</button>
      </div>
    </article>
  );
}
