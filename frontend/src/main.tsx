import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { RouterProvider } from "@tanstack/react-router";
import { CardPreferencesProvider } from "./features/library/CardPreferences";
import { router } from "./routes";
import "./styles.css";

const queryClient = new QueryClient();

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <CardPreferencesProvider>
        <RouterProvider router={router} />
      </CardPreferencesProvider>
    </QueryClientProvider>
  </StrictMode>,
);
