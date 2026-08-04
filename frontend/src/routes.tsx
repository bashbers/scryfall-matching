import { Link, Outlet, createRootRoute, createRoute, createRouter } from "@tanstack/react-router";
import { useCardQueue } from "./features/cards/useCardQueue";

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

const routeTree = rootRoute.addChildren([swipeRoute, likesRoute, dislikesRoute, historyRoute]);
export const router = createRouter({ routeTree });

declare module "@tanstack/react-router" {
  interface Register {
    router: typeof router;
  }
}

function Layout() {
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
      <Outlet />
    </main>
  );
}

function SwipeRoute() {
  const queue = useCardQueue();
  if (!queue.activeCard && queue.error) {
    return (
      <section role="alert">
        <p>Kaarten laden mislukte.</p>
        <button type="button" onClick={queue.retry}>
          Opnieuw proberen
        </button>
      </section>
    );
  }
  if (!queue.activeCard) {
    return <p>{queue.isLoading ? "Kaarten laden…" : "Geen kaarten beschikbaar."}</p>;
  }
  return (
    <section aria-live="polite">
      <p>{queue.isRefreshing ? "Nieuwe kaarten worden opgehaald." : ""}</p>
      <h1>{queue.activeCard.name}</h1>
      <p>{queue.cardsRemaining} kaarten in de actieve queue.</p>
      <button type="button" onClick={queue.dismissActiveCard}>
        Volgende kaart
      </button>
    </section>
  );
}

function LikesRoute() {
  return <Placeholder title="Likes" />;
}

function DislikesRoute() {
  return <Placeholder title="Dislikes" />;
}

function HistoryRoute() {
  return <Placeholder title="Historie" />;
}

function Placeholder({ title }: { title: string }) {
  return (
    <section>
      <h1>{title}</h1>
      <p>Deze lijst wordt in de volgende fase ingevuld.</p>
    </section>
  );
}
