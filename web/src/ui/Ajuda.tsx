// Cópia de @apphouer/ui (HouerIgnis, packages/ui). Na integração ao Ignis, importar do pacote.
"use client";

import * as Tooltip from "@radix-ui/react-tooltip";
import type { ReactNode } from "react";
import { Icone } from "./Icone";

/** Balão de ajuda. O termo técnico mora aqui, nunca no rótulo. */
export function Balao({ conteudo, children, lado = "top" }: {
  conteudo: ReactNode; children: ReactNode; lado?: "top" | "right" | "bottom" | "left";
}) {
  return (
    <Tooltip.Root delayDuration={200}>
      <Tooltip.Trigger asChild>{children}</Tooltip.Trigger>
      <Tooltip.Portal>
        <Tooltip.Content
          side={lado}
          sideOffset={6}
          collisionPadding={12}
          className="z-50 max-w-xs rounded-pi border border-borda bg-superficie px-3 py-2 text-[0.82rem] leading-snug text-texto shadow-lg animate-entra-baixo"
        >
          {conteudo}
          <Tooltip.Arrow className="fill-superficie" />
        </Tooltip.Content>
      </Tooltip.Portal>
    </Tooltip.Root>
  );
}

/** Botão "?" ao lado do rótulo, focável por teclado. */
export function BotaoAjuda({ texto, termo }: { texto: ReactNode; termo?: string }) {
  return (
    <Balao conteudo={texto}>
      <button
        type="button"
        className="inline-flex h-5 w-5 items-center justify-center rounded-full text-texto-fraco hover:text-acao-texto"
        aria-label={termo ? `O que é ${termo}?` : "Ajuda"}
      >
        <Icone nome="help" tamanho={16} />
      </button>
    </Balao>
  );
}

/** Termo técnico sublinhado dentro do texto corrido, com a explicação no balão. */
export function Termo({ children, explicacao }: { children: ReactNode; explicacao: ReactNode }) {
  return (
    <Balao conteudo={explicacao}>
      <button type="button" className="cursor-help border-b border-dotted border-texto-suave text-inherit">
        {children}
      </button>
    </Balao>
  );
}
