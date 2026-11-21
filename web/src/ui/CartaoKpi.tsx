// Cópia de @apphouer/ui (HouerIgnis, packages/ui). Na integração ao Ignis, importar do pacote.
"use client";

import type { ReactNode } from "react";
import { cn } from "./lib/cn";
import { BotaoAjuda } from "./Ajuda";

export type Variacao = { texto: string; sentido: "melhor" | "pior" | "neutro" };

/**
 * Indicador (tema/ui.kpi): rótulo, valor grande com unidade, linha de apoio. Sem seta colorida solta.
 * O valor encolhe com a largura (`clamp`) em vez de cortar, e nada quebra no meio da palavra:
 * no Streamlit o rótulo e o valor eram cortados com reticências.
 */
export function CartaoKpi({ rotulo, valor, unidade, apoio, variacao, ajuda, compacto, semMoldura, className }: {
  rotulo: string; valor: ReactNode; unidade?: string; apoio?: ReactNode; variacao?: Variacao;
  ajuda?: ReactNode; compacto?: boolean; semMoldura?: boolean; className?: string;
}) {
  return (
    <div className={cn("min-w-0 [overflow-wrap:normal] [word-break:normal]", !semMoldura && "cartao p-4", className)}>
      <div className="flex items-center gap-1">
        <span className="text-[0.78rem] font-medium leading-tight text-texto-fraco">{rotulo}</span>
        {ajuda && <BotaoAjuda texto={ajuda} termo={rotulo} />}
      </div>
      <div className={cn("mt-1 flex items-baseline gap-1 font-semibold text-texto num", compacto ? "text-[clamp(1rem,1.6vw,1.25rem)]" : "text-[clamp(1.25rem,2.4vw,1.7rem)] leading-none", "flex-wrap")}>
        <span>{valor}</span>
        {unidade && <span className="text-[0.8rem] font-medium text-texto-fraco">{unidade}</span>}
      </div>
      {(variacao || apoio) && (
        <div className="mt-1 flex flex-wrap items-center gap-x-2 text-[0.78rem] text-texto-fraco">
          {variacao && (
            <span
              className={cn(
                "font-semibold num",
                variacao.sentido === "melhor" && "text-sucesso-texto",
                variacao.sentido === "pior" && "text-erro-texto",
              )}
            >
              {variacao.texto}
              <span className="sr-only">{variacao.sentido === "melhor" ? " (melhora)" : variacao.sentido === "pior" ? " (piora)" : ""}</span>
            </span>
          )}
          {apoio && <span>{apoio}</span>}
        </div>
      )}
    </div>
  );
}
