import { motion, useReducedMotion } from "motion/react";
import { useEffect, useRef, useState } from "react";
import type { Card } from "../../api/generated";

const cardBackUrl = new URL("../../assets/card-back.svg", import.meta.url).href;

type CardSwiperProps = {
  card: Card;
  onLike: () => void;
  onDislike: () => void;
  onViewed: () => void;
  queuedCards: readonly Card[];
};

const SWIPE_OFFSET = 110;
const SWIPE_VELOCITY = 650;
const STACK_SIZE = 3;

export function CardSwiper({
  card,
  onLike,
  onDislike,
  onViewed,
  queuedCards,
}: CardSwiperProps) {
  const [isFlipped, setIsFlipped] = useState(false);
  const [failedImageUrl, setFailedImageUrl] = useState<string | null>(null);
  const [dragIntent, setDragIntent] = useState<"like" | "dislike" | null>(null);
  const [selection, setSelection] = useState<"like" | "dislike" | null>(null);
  const restoreFocusAfterSelection = useRef(false);
  const shouldReduceMotion = useReducedMotion();

  useEffect(() => {
    setIsFlipped(false);
    setFailedImageUrl(null);
    setSelection(null);
    onViewed();
  }, [card.id, onViewed]);

  const imageUrl = isFlipped
    ? card.isDoubleSided
      ? (card.backImageUrl ?? cardBackUrl)
      : cardBackUrl
    : card.frontImageUrl;
  const toggleFlip = () => setIsFlipped((current) => !current);
  const selectCard = (direction: "like" | "dislike", restoreFocus = false) => {
    if (selection) {
      return;
    }
    restoreFocusAfterSelection.current = restoreFocus;
    setDragIntent(direction);
    setSelection(direction);
  };
  const finishDrag = (offsetX: number, velocityX: number) => {
    if (offsetX >= SWIPE_OFFSET || velocityX >= SWIPE_VELOCITY) {
      selectCard("like");
    } else if (offsetX <= -SWIPE_OFFSET || velocityX <= -SWIPE_VELOCITY) {
      selectCard("dislike");
    } else {
      setDragIntent(null);
    }
  };
  const completeSelection = () => {
    if (!selection) {
      return;
    }
    const completedSelection = selection;
    setSelection(null);
    setDragIntent(null);
    if (completedSelection === "like") {
      onLike();
    } else {
      onDislike();
    }
    if (restoreFocusAfterSelection.current) {
      restoreFocusAfterSelection.current = false;
      window.requestAnimationFrame(() =>
        document.querySelector<HTMLElement>(".card-swiper")?.focus(),
      );
    }
  };

  return (
    <div className="card-stack" aria-label="Actieve kaartstapel">
      {queuedCards
        .slice(0, STACK_SIZE)
        .reverse()
        .map((queuedCard, reverseIndex) => {
          const stackIndex =
            queuedCards.slice(0, STACK_SIZE).length - reverseIndex;
          return (
            <div
              key={queuedCard.id}
              aria-hidden="true"
              className="card-stack-preview"
              style={{ "--stack-index": stackIndex } as React.CSSProperties}
            >
              <img src={queuedCard.frontImageUrl} alt="" />
            </div>
          );
        })}
      <article
        className="card-swiper"
        onKeyDown={(event) => {
          if (event.target !== event.currentTarget) {
            return;
          }
          if (event.key === "ArrowRight") {
            event.preventDefault();
            selectCard("like", true);
          }
          if (event.key === "ArrowLeft") {
            event.preventDefault();
            selectCard("dislike", true);
          }
          if (event.key === " " || event.key === "Enter") {
            event.preventDefault();
            toggleFlip();
          }
        }}
        tabIndex={0}
        aria-label={`${card.name}. Pijl-rechts liken, pijl-links afwijzen, spatie omdraaien.`}
      >
        <motion.div
          key={card.id}
          className="card-image-wrap"
          drag={selection ? false : "x"}
          dragElastic={0.18}
          dragMomentum={false}
          animate={
            selection
              ? {
                  x: selection === "like" ? 520 : -520,
                  opacity: 0,
                  rotate: selection === "like" ? 16 : -16,
                }
              : { x: 0, opacity: 1, rotate: 0 }
          }
          transition={
            shouldReduceMotion
              ? { duration: 0 }
              : { type: "tween", duration: 0.28, ease: "easeOut" }
          }
          whileDrag={{ cursor: "grabbing", scale: 1.015 }}
          onPan={(_event, info) => {
            if (Math.abs(info.offset.x) < 24) {
              setDragIntent(null);
              return;
            }
            setDragIntent(info.offset.x > 0 ? "like" : "dislike");
          }}
          onPanEnd={() => !selection && setDragIntent(null)}
          onDragEnd={(_event, info) =>
            finishDrag(info.offset.x, info.velocity.x)
          }
          onAnimationComplete={completeSelection}
        >
          {failedImageUrl === imageUrl ? (
            <div
              className="image-placeholder"
              role="img"
              aria-label="Kaartafbeelding niet beschikbaar"
            >
              Afbeelding niet beschikbaar
            </div>
          ) : (
            <img
              src={imageUrl}
              alt={card.name}
              onError={() => setFailedImageUrl(imageUrl)}
            />
          )}
          {dragIntent && (
            <span className={`drag-intent drag-intent-${dragIntent}`}>
              {dragIntent === "like" ? "LIKE" : "NEE"}
            </span>
          )}
        </motion.div>
        <div className="card-details" key={`metadata-${card.id}`}>
          <h1>{card.name}</h1>
          <div className="card-meta-row">
            {card.commanderLegal && (
              <span className="badge">Commander-legal</span>
            )}
            <a href={card.scryfallUrl} target="_blank" rel="noreferrer">
              Bekijk op Scryfall
            </a>
          </div>
        </div>
        <div className="card-actions" aria-label="Kaartacties">
          <button
            className="button-dislike"
            type="button"
            onClick={() => selectCard("dislike")}
          >
            Afwijzen
          </button>
          <button type="button" onClick={toggleFlip}>
            Draai om
          </button>
          <button
            className="button-like"
            type="button"
            onClick={() => selectCard("like")}
          >
            Liken
          </button>
        </div>
      </article>
    </div>
  );
}
