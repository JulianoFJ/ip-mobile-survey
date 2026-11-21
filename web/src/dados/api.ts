"use client";

import { useQuery } from "@tanstack/react-query";
import type { Campanha, ResumoCampanha } from "./tipos";

/**
 * Acesso aos dados. Hoje lê os JSON estáticos de `public/demo/` (gerados por
 * `scripts/export_web_demo.py`); quando a API existir, só estas funções mudam.
 */
async function lerJson<T>(caminho: string): Promise<T> {
  const r = await fetch(caminho);
  if (!r.ok) throw new Error(`${caminho}: HTTP ${r.status}`);
  return (await r.json()) as T;
}

export function useCampanhas() {
  return useQuery({
    queryKey: ["campanhas"],
    queryFn: () => lerJson<ResumoCampanha[]>("/demo/campanhas.json"),
  });
}

export function useCampanha(id: string) {
  return useQuery({
    queryKey: ["campanha", id],
    queryFn: () => lerJson<Campanha>(`/demo/campanha-${encodeURIComponent(id)}.json`),
    staleTime: Infinity,
  });
}

/** URL pública de um arquivo de `public/`. */
export function urlPublica(caminho: string): string {
  return `/${caminho.replace(/^\/+/, "")}`;
}
