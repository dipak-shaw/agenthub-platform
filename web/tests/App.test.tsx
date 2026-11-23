import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { expect, test, vi } from "vitest";
import App from "../src/App";

test("empty workspace explains how to add an agent", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(
      async (url: string) =>
        new Response(
          JSON.stringify(
            url === "/health"
              ? { model_mode: "demo", search_provider: "fake" }
              : [],
          ),
        ),
    ),
  );
  render(
    <QueryClientProvider
      client={
        new QueryClient({ defaultOptions: { queries: { retry: false } } })
      }
    >
      <MemoryRouter
        future={{ v7_startTransition: true, v7_relativeSplatPath: true }}
      >
        <App />
      </MemoryRouter>
    </QueryClientProvider>,
  );
  expect(await screen.findByText(/No agents are bundled/)).toBeInTheDocument();
  expect(screen.getByText(/agent_hub\/agents/)).toBeInTheDocument();
});
