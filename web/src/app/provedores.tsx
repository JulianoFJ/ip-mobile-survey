"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import * as Tooltip from "@radix-ui/react-tooltip";
import { useState, type ReactNode } from "react";

export function Provedores({ children }: { children: ReactNode }) {
  const [cliente] = useState(() => new QueryClient({ defaultOptions: { queries: { retry: 1, refetchOnWindowFocus: false } } }));
  return (
    <QueryClientProvider client={cliente}>
      <Tooltip.Provider delayDuration={250}>{children}</Tooltip.Provider>
    </QueryClientProvider>
  );
}
