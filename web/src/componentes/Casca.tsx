"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";
import { Icone } from "@/ui/Icone";
import { cn } from "@/ui/lib/cn";

/**
 * Casca do módulo, no padrão da casca do Ignis (apps/web/src/componentes/casca/Casca.tsx):
 * barra lateral com a marca e o menu por seção. Na integração, este arquivo some e as
 * rotas de `inspecao/` entram na seção "Diagnóstico (DTO)" do portal.
 */
const MENU = [
  {
    titulo: "Inspeção de campo",
    itens: [
      { href: "/inspecao", titulo: "Inspeções", icone: "photo_camera", exato: true },
      { href: "/inspecao/nova", titulo: "Nova inspeção", icone: "add_a_photo", exato: true },
    ],
  },
];

export function Casca({ children }: { children: ReactNode }) {
  const caminho = usePathname();
  return (
    <div className="flex h-full min-h-0">
      <aside aria-label="Menu principal" className="hidden w-[248px] shrink-0 flex-col border-r border-borda bg-superficie lg:flex print:hidden">
        <div className="flex h-16 shrink-0 items-center border-b border-borda px-5">
          <Marca />
        </div>
        <nav aria-label="Ferramentas" className="min-h-0 flex-1 overflow-y-auto px-3 py-3">
          {MENU.map((s) => (
            <div key={s.titulo}>
              <p className="rotulo-secao px-2 py-1.5">{s.titulo}</p>
              <ul className="flex flex-col gap-0.5">
                {s.itens.map((i) => {
                  const ativo = i.exato
                    ? caminho === i.href || (i.href === "/inspecao" && /^\/inspecao\/(?!nova)/.test(caminho))
                    : caminho.startsWith(i.href);
                  return (
                    <li key={i.href}>
                      <Link
                        href={i.href}
                        aria-current={ativo ? "page" : undefined}
                        className={cn(
                          "relative flex h-9 items-center gap-3 rounded-pi px-2.5 text-[0.9rem] font-medium text-texto-fraco transition-colors hover:bg-superficie-alt hover:text-texto",
                          ativo && "bg-acao-suave font-semibold text-navy",
                        )}
                      >
                        {ativo && <span className="absolute inset-y-1.5 left-0 w-[3px] rounded-full bg-teal" aria-hidden />}
                        <Icone nome={i.icone} cheio={ativo} className={ativo ? "text-acao-texto" : undefined} />
                        <span className="truncate">{i.titulo}</span>
                      </Link>
                    </li>
                  );
                })}
              </ul>
            </div>
          ))}
        </nav>
        <div className="border-t border-borda px-4 py-3 text-[0.78rem] text-texto-fraco">
          <p className="flex items-center gap-1.5 font-semibold text-atencao-texto">
            <Icone nome="science" tamanho={16} /> Módulo em desenvolvimento
          </p>
          <p className="mt-0.5">Dados de demonstração. O envio ao servidor ainda não está ligado.</p>
        </div>
      </aside>
      <main id="conteudo" className="relative min-h-0 flex-1 overflow-y-auto">
        {children}
      </main>
    </div>
  );
}

function Marca() {
  return (
    <Link href="/inspecao" className="flex flex-col justify-center rounded-pi leading-none" aria-label="Ignis — Inspeção de campo">
      <span className="font-display text-[1.3rem] font-semibold tracking-tight text-navy" aria-hidden>
        Ign
        <span className="relative">
          ı
          <span className="absolute left-1/2 top-[0.05em] h-[0.16em] w-[0.16em] -translate-x-1/2 -translate-y-[55%] rounded-full bg-teal shadow-[0_0_0.5em_0.02em_rgba(232,162,77,0.55)]" />
        </span>
        s
      </span>
      <span className="mt-1 text-[0.6rem] uppercase tracking-[0.14em] text-texto-fraco" aria-hidden>
        Head de Energia
      </span>
    </Link>
  );
}

/** Cabeçalho de página (equivalente ao `ui.hero` do portal). */
export function Cabecalho({ titulo, descricao, acoes, trilha, children }: {
  titulo: ReactNode;
  descricao?: ReactNode;
  acoes?: ReactNode;
  trilha?: { href: string; rotulo: string }[];
  children?: ReactNode;
}) {
  return (
    <header className="border-b border-borda bg-superficie px-6 pt-5 print:border-0 print:px-0">
      {trilha && (
        <nav aria-label="Trilha" className="mb-2 flex items-center gap-1 text-[0.8rem] text-texto-fraco print:hidden">
          {trilha.map((t, i) => (
            <span key={t.href} className="flex items-center gap-1">
              {i > 0 && <Icone nome="chevron_right" tamanho={16} />}
              <Link href={t.href} className="hover:text-acao-texto hover:underline">{t.rotulo}</Link>
            </span>
          ))}
        </nav>
      )}
      <div className="flex flex-wrap items-start justify-between gap-4 pb-4">
        <div className="min-w-0">
          <h1 className="text-[1.45rem] font-semibold leading-tight text-navy">{titulo}</h1>
          {descricao && <p className="mt-1 max-w-3xl text-[0.92rem] text-texto-fraco">{descricao}</p>}
        </div>
        {acoes && <div className="flex flex-wrap items-center gap-2 print:hidden">{acoes}</div>}
      </div>
      {children}
    </header>
  );
}
