import {
  Link,
  Outlet,
  createRootRoute,
  createRoute,
  createRouter,
} from "@tanstack/react-router";
import { CardSwiper } from "./features/cards/CardSwiper";
import { useCardQueue } from "./features/cards/useCardQueue";
import { CardList } from "./features/library/CardList";
import { useCardPreferences } from "./features/library/CardPreferences";

const rootRoute = createRootRoute({ component: Layout });
const swipeRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/",
  component: SwipeRoute,
});
const likesRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/likes",
  component: LikesRoute,
});
const dislikesRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/dislikes",
  component: DislikesRoute,
});
const historyRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/history",
  component: HistoryRoute,
});

const routeTree = rootRoute.addChildren([
  swipeRoute,
  likesRoute,
  dislikesRoute,
  historyRoute,
]);
export const router = createRouter({ routeTree });

declare module "@tanstack/react-router" {
  interface Register {
    router: typeof router;
  }
}

function Layout() {
  const { storageWarning } = useCardPreferences();
  return (
    <main className="app-shell">
      <header>
        <Link to="/" className="brand">
          Scryfall Matching
        </Link>
        <nav aria-label="Hoofdnavigatie">
          <Link to="/">Ontdek</Link>
          <Link to="/likes">Likes</Link>
          <Link to="/dislikes">Dislikes</Link>
          <Link to="/history">Historie</Link>
        </nav>
      </header>
      {storageWarning && (
        <p className="storage-warning" role="alert">
          {storageWarning}
        </p>
      )}
      <Outlet />
    </main>
  );
}

function SwipeRoute() {
  const queue = useCardQueue();
  const preferences = useCardPreferences();
  const activeCard = queue.activeCard;
  if (!activeCard && queue.error) {
    return (
      <section role="alert">
        <p>Kaarten laden mislukte.</p>
        <button type="button" onClick={queue.retry}>
          Opnieuw proberen
        </button>
      </section>
    );
  }
  if (!activeCard) {
    return (
      <p>{queue.isLoading ? "Kaarten laden…" : "Geen kaarten beschikbaar."}</p>
    );
  }
  return (
    <section aria-live="polite">
      <p>{queue.isRefreshing ? "Nieuwe kaarten worden opgehaald." : ""}</p>
      <CardSwiper
        card={activeCard}
        queuedCards={queue.queuedCards}
        onViewed={() => preferences.markSeen(activeCard)}
        onLike={() => {
          preferences.like(activeCard);
          queue.dismissActiveCard();
        }}
        onDislike={() => {
          preferences.dislike(activeCard);
          queue.dismissActiveCard();
        }}
      />
      <p>{queue.cardsRemaining} kaarten in de actieve queue.</p>
    </section>
  );
}

function LikesRoute() {
  const preferences = useCardPreferences();
  return (
    <ListPage title="Likes">
      <CardList
        cards={preferences.likedCards}
        emptyMessage="Nog geen gelikete kaarten."
        onRemove={(cardId) => preferences.remove("likedCards", cardId)}
      />
    </ListPage>
  );
}

function DislikesRoute() {
  const preferences = useCardPreferences();
  return (
    <ListPage title="Dislikes">
      <CardList
        cards={preferences.dislikedCards}
        emptyMessage="Nog geen afgewezen kaarten."
        onRemove={(cardId) => preferences.remove("dislikedCards", cardId)}
      />
    </ListPage>
  );
}

function HistoryRoute() {
  const preferences = useCardPreferences();
  return (
    <ListPage title="Historie">
      <CardList
        cards={preferences.seenCards}
        emptyMessage="Nog geen kaarten bekeken."
        onRemove={(cardId) => preferences.remove("seenCards", cardId)}
      />
    </ListPage>
  );
}

function ListPage({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section>
      <h1>{title}</h1>
      {children}
    </section>
  );
}
