"use client";

import { useCallback, useSyncExternalStore } from "react";
import type { Revisao } from "./tipos";

/**
 * Decisões de revisão (confirmar ou rejeitar cada detecção).
 *
 * Provisório: ficam no navegador de quem revisa. Quando a API existir, cada decisão vira
 * um POST e passa a ser rótulo de treino. Por isso há `exportar()`: o JSON baixado já tem
 * o formato que a API vai receber.
 */
type Mapa = Record<string, Revisao>;

const ouvintes = new Set<() => void>();
const cache = new Map<string, Mapa>();
const VAZIO: Mapa = {};

function chave(campanha: string) {
  return `ipsurvey-revisao-${campanha}`;
}

function ler(campanha: string): Mapa {
  const c = cache.get(campanha);
  if (c) return c;
  let m: Mapa = {};
  try {
    m = JSON.parse(localStorage.getItem(chave(campanha)) ?? "{}") as Mapa;
  } catch {
    m = {};
  }
  cache.set(campanha, m);
  return m;
}

function gravar(campanha: string, m: Mapa) {
  cache.set(campanha, m);
  try {
    localStorage.setItem(chave(campanha), JSON.stringify(m));
  } catch {
    /* navegação privada: a decisão vale só nesta aba */
  }
  ouvintes.forEach((f) => f());
}

function assinar(f: () => void) {
  ouvintes.add(f);
  return () => ouvintes.delete(f);
}

export function useRevisoes(campanha: string) {
  const mapa = useSyncExternalStore(assinar, () => ler(campanha), () => VAZIO);
  const decidir = useCallback(
    (id: string, r: Revisao | null) => {
      const novo = { ...ler(campanha) };
      if (r) novo[id] = r;
      else delete novo[id];
      gravar(campanha, novo);
    },
    [campanha],
  );
  const exportar = useCallback(() => {
    const blob = new Blob(
      [JSON.stringify({ campanha, exportadoEm: new Date().toISOString(), revisoes: ler(campanha) }, null, 2)],
      { type: "application/json" },
    );
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `revisoes-${campanha}.json`;
    a.click();
    URL.revokeObjectURL(a.href);
  }, [campanha]);
  return { mapa, decidir, exportar };
}
