// Cópia de @apphouer/ui (HouerIgnis, packages/ui). Na integração ao Ignis, importar do pacote.
"use client";

import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import { forwardRef, type ButtonHTMLAttributes } from "react";
import { cn } from "./lib/cn";
import { Icone } from "./Icone";

/**
 * Hierarquia de botões do portal (tema/estilo.py): **um primário por tela** — a ação
 * principal —, secundário para as demais, terciário só texto, download com texto teal.
 * O primário é preenchido com `acao-fundo` (teal escuro, 4,95:1 com branco; ver
 * scripts/tokens_web.py); o teal da marca é só acento. Rótulo é verbo + objeto. `perigo` é para ação destrutiva (revogar acesso, arquivar).
 */
export const botao = cva(
  "inline-flex select-none items-center justify-center gap-2 whitespace-nowrap rounded-pi font-semibold " +
    "text-[0.92rem] transition-colors disabled:pointer-events-none disabled:opacity-50 " +
    "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-teal",
  {
    variants: {
      variante: {
        primario: "bg-acao-fundo text-sobre-acao shadow-botao hover:bg-acao-fundo-hover",
        secundario:
          "border border-borda-forte bg-superficie text-navy shadow-botao hover:bg-acao-suave hover:border-acao",
        terciario: "text-acao-texto hover:bg-acao-suave",
        download:
          "border border-borda-forte bg-superficie text-acao-texto shadow-botao hover:bg-acao-suave hover:border-acao",
        perigo: "border border-erro/50 bg-superficie text-erro-texto hover:bg-erro-suave",
      },
      tamanho: {
        normal: "min-h-botao px-4",
        compacto: "h-8 px-3 text-[0.85rem]",
        icone: "h-9 w-9 p-0",
      },
    },
    defaultVariants: { variante: "secundario", tamanho: "normal" },
  },
);

export type VarianteBotao = NonNullable<VariantProps<typeof botao>["variante"]>;

export interface BotaoProps
  extends ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof botao> {
  icone?: string;
  iconeDireita?: string;
  carregando?: boolean;
  asChild?: boolean;
}

export const Botao = forwardRef<HTMLButtonElement, BotaoProps>(function Botao(
  { className, variante, tamanho, icone, iconeDireita, carregando, asChild, children, disabled, ...resto },
  ref,
) {
  const Comp = asChild ? Slot : "button";
  // Sem `type`, um botão dentro de <form> envia o formulário; aqui só envia quem pedir.
  const tipo = asChild ? undefined : resto.type ?? "button";
  const iconeEsq = carregando ? "progress_activity" : icone ?? (variante === "download" ? "download" : undefined);
  return (
    <Comp
      ref={ref}
      className={cn(botao({ variante, tamanho }), className)}
      disabled={asChild ? undefined : disabled || carregando}
      aria-busy={carregando || undefined}
      {...resto}
      type={tipo}
    >
      {asChild ? (
        children
      ) : (
        <>
          {iconeEsq && <Icone nome={iconeEsq} tamanho={18} className={carregando ? "animate-spin" : undefined} />}
          {children}
          {iconeDireita && <Icone nome={iconeDireita} tamanho={18} />}
        </>
      )}
    </Comp>
  );
});
