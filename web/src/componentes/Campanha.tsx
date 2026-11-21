"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";
import { useCampanha } from "@/dados/api";
import { STATUS, type Campanha } from "@/dados/tipos";
import { Icone } from "@/ui/Icone";
import { cn } from "@/ui/lib/cn";
import { Selo } from "@/ui/Selo";
import { Cabecalho } from "./Casca";

const ABAS = [
  { sufixo: "", rotulo: "Painel e mapa", icone: "map" },
  { sufixo: "/revisao", rotulo: "Revisão", icone: "rule" },
  { sufixo: "/relatorio", rotulo: "Relatório", icone: "description" },
];

/** Cabeçalho comum das telas de uma inspeção, com as abas. */
export function CabecalhoCampanha({ campanha, acoes }: { campanha: Campanha; acoes?: ReactNode }) {
  const caminho = usePathname();
  const base = `/inspecao/${encodeURIComponent(campanha.id)}`;
  const st = STATUS[campanha.status];
  return (
    <Cabecalho
      trilha={[{ href: "/inspecao", rotulo: "Inspeções" }]}
      titulo={
        <span className="flex flex-wrap items-center gap-3">
          {campanha.nome}
          <Selo tom={st.tom} icone={st.icone}>{st.rotulo}</Selo>
        </span>
      }
      descricao={`${campanha.municipio} · ${campanha.capturas.length} panoramas · detector ${campanha.modelo}`}
      acoes={acoes}
    >
      <nav aria-label="Seções da inspeção" className="-mb-px flex gap-1 overflow-x-auto print:hidden">
        {ABAS.map((a) => {
          const href = base + a.sufixo;
          const ativo = caminho === href;
          return (
            <Link
              key={a.sufixo}
              href={href}
              aria-current={ativo ? "page" : undefined}
              className={cn(
                "flex items-center gap-2 whitespace-nowrap border-b-2 px-3 pb-2.5 pt-1 text-[0.9rem] font-medium text-texto-fraco hover:text-texto",
                ativo ? "border-teal font-semibold text-navy" : "border-transparent",
              )}
            >
              <Icone nome={a.icone} tamanho={18} cheio={ativo} className={ativo ? "text-acao-texto" : undefined} />
              {a.rotulo}
            </Link>
          );
        })}
      </nav>
    </Cabecalho>
  );
}

/** Carrega a inspeção e cuida dos estados de espera e erro. */
export function ComCampanha({ id, children }: { id: string; children: (c: Campanha) => ReactNode }) {
  const q = useCampanha(id);
  if (q.isPending) return <Carregando />;
  if (q.isError)
    return (
      <EstadoVazio
        icone="cloud_off"
        titulo="Não encontrei os dados desta inspeção"
        descricao={
          <>
            Gere os dados de demonstração com{" "}
            <code className="rounded bg-superficie-alt px-1">uv run --extra vision python scripts/export_web_demo.py panoramax-br-v0</code>.
          </>
        }
      />
    );
  return <>{children(q.data)}</>;
}

export function Carregando({ texto = "Carregando…" }: { texto?: string }) {
  return (
    <div className="grid min-h-[50vh] place-items-center text-texto-fraco" role="status">
      <span className="flex items-center gap-2">
        <Icone nome="progress_activity" className="animate-spin" /> {texto}
      </span>
    </div>
  );
}

export function EstadoVazio({ icone, titulo, descricao, acao }: {
  icone: string; titulo: string; descricao?: ReactNode; acao?: ReactNode;
}) {
  return (
    <div className="grid min-h-[50vh] place-items-center p-6">
      <div className="max-w-md text-center">
        <span className="mx-auto grid h-12 w-12 place-items-center rounded-full bg-acao-suave text-acao-texto">
          <Icone nome={icone} tamanho={26} />
        </span>
        <h2 className="mt-3 text-[1.1rem] font-semibold text-navy">{titulo}</h2>
        {descricao && <p className="mt-1 text-[0.9rem] text-texto-fraco">{descricao}</p>}
        {acao && <div className="mt-4">{acao}</div>}
      </div>
    </div>
  );
}
