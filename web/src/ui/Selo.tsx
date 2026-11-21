// Cópia de @apphouer/ui (HouerIgnis, packages/ui). Na integração ao Ignis, importar do pacote.
"use client";

import type { ReactNode } from "react";
import { cn } from "./lib/cn";
import { Balao } from "./Ajuda";
import { Icone } from "./Icone";
import type { Tom } from "./tokens";


const TOM: Record<Tom, string> = {
  marca: "bg-acao-suave text-acao-texto border-teal/50",
  sucesso: "bg-sucesso-suave text-sucesso-texto border-sucesso/50",
  atencao: "bg-atencao-suave text-atencao-texto border-atencao/50",
  erro: "bg-erro-suave text-erro-texto border-erro/50",
  neutro: "bg-superficie-alt text-texto-fraco border-borda-campo",
};

/** Selo de estado (tema/ui.badge). Cor nunca sozinha: sempre texto, e ícone quando ajuda. */
export function Selo({ tom = "neutro", icone, children, className }: {
  tom?: Tom; icone?: string; children: ReactNode; className?: string;
}) {
  return (
    <span className={cn("inline-flex items-center gap-1 rounded-chip border px-2 py-0.5 text-[0.75rem] font-semibold leading-5", TOM[tom], className)}>
      {icone && <Icone nome={icone} tamanho={14} />}
      {children}
    </span>
  );
}

export type Origem = "real" | "calibrado" | "hipotese";

export const ORIGEM: Record<Origem, { texto: string; tom: Tom; icone: string; explica: string }> = {
  real: { texto: "Dado real", tom: "sucesso", icone: "verified", explica: "Medido e publicado por uma fonte oficial ou aberta." },
  calibrado: { texto: "Calibrado", tom: "marca", icone: "tune", explica: "Hipótese ajustada a um dado real do município." },
  hipotese: { texto: "Hipótese", tom: "neutro", icone: "lightbulb", explica: "Valor padrão de pesquisa. Pode ser editado." },
};

/** Selo de origem de uma premissa: de onde o número veio. */
export function SeloOrigem({ origem, fonte, className }: { origem: Origem; fonte?: string; className?: string }) {
  const o = ORIGEM[origem];
  return (
    <Balao conteudo={<><strong>{o.texto}.</strong> {o.explica}{fonte ? <><br />Fonte: {fonte}</> : null}</>}>
      <span tabIndex={0} className={cn("inline-flex cursor-default rounded-chip", className)}>
        <Selo tom={o.tom} icone={o.icone}>
          {o.texto}
          {fonte && <span className="font-normal">· {fonte}</span>}
        </Selo>
      </span>
    </Balao>
  );
}
