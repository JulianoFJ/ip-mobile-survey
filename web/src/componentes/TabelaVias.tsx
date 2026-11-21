"use client";

import Link from "next/link";
import { mediana } from "@/dados/geometria";
import { FONTES, type Captura, type CampoVia, type Fonte } from "@/dados/tipos";
import { Balao } from "@/ui/Ajuda";
import { Icone } from "@/ui/Icone";
import { cn } from "@/ui/lib/cn";

/** Colunas da planilha de simulação mostradas na tabela, na ordem de leitura. */
export const COLUNAS_TABELA = ["R", "T", "W", "Y", "S", "X", "AD", "AF", "AL", "AJ", "AH", "AI"] as const;

const CURTO: Record<string, string> = {
  R: "Faixas",
  T: "Via 1",
  W: "Via 2",
  S: "Passeio 1",
  X: "Passeio 2",
  Y: "Canteiro",
  AD: "Posteação",
  AF: "Vão",
  AL: "Alt. instalação",
  AJ: "Braço",
  AH: "Lâmp./ponto",
  AI: "Poste–via",
};

const COR_FONTE: Record<Fonte, string> = {
  imagem: "text-acao-texto",
  cadastro: "text-sucesso",
  mapa: "text-navy",
};

function campo(c: Captura, col: string): CampoVia | undefined {
  return c.via.campos.find((f) => f.coluna === col);
}

/** Valor de um campo com o ícone da fonte e o aviso de divergência. */
export function ValorCampo({ f, compacto }: { f: CampoVia | undefined; compacto?: boolean }) {
  if (!f || f.valor == null) {
    return (
      <Balao conteudo={f?.metodo ?? "Sem dado"}>
        <span tabIndex={0} className="cursor-default text-texto-suave">—</span>
      </Balao>
    );
  }
  const txt = typeof f.valor === "number" ? f.valor.toLocaleString("pt-BR") : f.valor;
  return (
    <Balao
      conteudo={
        <div className="max-w-xs space-y-1">
          {f.candidatos.map((c, i) => (
            <p key={c.fonte}>
              <strong>
                {FONTES[c.fonte].rotulo}
                {i === 0 ? " (usada)" : ""}:
              </strong>{" "}
              {String(c.valor)}
              {f.unidade && typeof c.valor === "number" ? ` ${f.unidade}` : ""} — {c.detalhe}
            </p>
          ))}
        </div>
      }
    >
      <span tabIndex={0} className="inline-flex cursor-default items-center gap-1 whitespace-nowrap">
        <span className={cn("font-semibold text-navy num", compacto && "text-[0.82rem]")}>
          {txt}
          {f.unidade && <span className="ml-0.5 font-normal text-texto-fraco">{f.unidade}</span>}
        </span>
        {f.fonte && <Icone nome={FONTES[f.fonte].icone} tamanho={14} className={COR_FONTE[f.fonte]} rotulo={FONTES[f.fonte].rotulo} />}
        {f.divergente && <Icone nome="warning" tamanho={14} cheio className="text-atencao" rotulo="Fontes divergentes" />}
      </span>
    </Balao>
  );
}

/** Cobertura e mediana de cada medida no conjunto de capturas. */
export function ResumoMedidas({ capturas }: { capturas: Captura[] }) {
  const itens: { col: string; rotulo: string; un: string }[] = [
    { col: "AF", rotulo: "Distância entre postes", un: "m" },
    { col: "AL", rotulo: "Altura de instalação", un: "m" },
    { col: "AJ", rotulo: "Projeção do braço", un: "m" },
    { col: "R", rotulo: "Faixas de rodagem", un: "" },
    { col: "T", rotulo: "Largura da via", un: "m" },
    { col: "S", rotulo: "Passeio (lado 1)", un: "m" },
  ];
  return (
    <div className="grid grid-cols-2 gap-3 md:grid-cols-4 xl:grid-cols-7">
      {itens.map((it) => {
        const fs = capturas.map((c) => campo(c, it.col)).filter((f): f is CampoVia => !!f && typeof f.valor === "number");
        const med = mediana(fs.map((f) => f.valor as number));
        const porFonte = fs.reduce<Record<string, number>>((a, f) => ((a[f.fonte ?? "?"] = (a[f.fonte ?? "?"] ?? 0) + 1), a), {});
        return (
          <div key={it.col} className="cartao p-4">
            <p className="flex items-center gap-1.5 text-[0.78rem] font-medium text-texto-fraco">
              <span className="rounded bg-superficie-alt px-1 font-mono text-[0.68rem]">{it.col}</span> {it.rotulo}
            </p>
            <p className="mt-1 text-[1.5rem] font-semibold leading-none text-texto num">
              {med != null ? med.toLocaleString("pt-BR", { maximumFractionDigits: 1 }) : "—"}
              {med != null && it.un && <span className="ml-1 text-[0.8rem] font-medium text-texto-fraco">{it.un}</span>}
            </p>
            <p className="mt-1 text-[0.76rem] text-texto-fraco">
              {fs.length ? (
                <>
                  mediana · {fs.length} de {capturas.length} capturas
                  <span className="mt-0.5 flex flex-wrap gap-x-2">
                    {Object.entries(porFonte).map(([k, n]) => (
                      <span key={k} className="flex items-center gap-0.5">
                        <Icone nome={FONTES[k as Fonte]?.icone ?? "help"} tamanho={13} className={COR_FONTE[k as Fonte]} /> {n}
                      </span>
                    ))}
                  </span>
                </>
              ) : (
                "pendente: satélite e segmentação"
              )}
            </p>
          </div>
        );
      })}
      <div className="cartao p-4">
        <p className="text-[0.78rem] font-medium text-texto-fraco">Posteação (AD)</p>
        <ul className="mt-1 space-y-0.5 text-[0.8rem]">
          {Object.entries(
            capturas.reduce<Record<string, number>>((a, c) => {
              const v = campo(c, "AD")?.valor;
              if (typeof v === "string") a[v] = (a[v] ?? 0) + 1;
              return a;
            }, {}),
          )
            .sort((a, b) => b[1] - a[1])
            .map(([k, n]) => (
              <li key={k} className="flex justify-between gap-2">
                <span className="truncate">{k}</span>
                <span className="font-semibold num">{n}</span>
              </li>
            ))}
        </ul>
      </div>
    </div>
  );
}

/** Tabela captura × campo da planilha de simulação. */
export function TabelaVias({ capturas, base, aoSelecionar, impressao }: {
  capturas: Captura[];
  /** Rota da inspeção, para o link "revisar". */
  base?: string;
  aoSelecionar?: (id: string) => void;
  impressao?: boolean;
}) {
  return (
    <div className={cn("overflow-x-auto", !impressao && "cartao")}>
      <table className="w-full text-[0.84rem]">
        <thead>
          <tr className="border-b border-borda-forte text-left text-[0.74rem] text-texto-fraco">
            <th className="px-3 py-2 font-medium">Logradouro</th>
            {COLUNAS_TABELA.map((c) => (
              <th key={c} className="px-2 py-2 text-right font-medium">
                <span className="block font-mono text-[0.66rem] text-texto-suave">{c}</span>
                {CURTO[c]}
              </th>
            ))}
            {!impressao && <th className="px-2 py-2" />}
          </tr>
        </thead>
        <tbody>
          {capturas.map((c) => (
            <tr key={c.id} className="border-b border-borda hover:bg-superficie-alt/60">
              <td className="max-w-[240px] px-3 py-1.5">
                <button type="button" onClick={() => aoSelecionar?.(c.id)} className="block w-full truncate text-left font-medium text-texto hover:text-acao-texto" disabled={!aoSelecionar}>
                  {c.via.logradouro ?? <span className="text-texto-suave">sem nome no mapa</span>}
                </button>
                <span className="block truncate text-[0.72rem] text-texto-fraco">
                  {c.cidade}
                  {c.via.classeOsm ? ` · ${c.via.classeOsm}` : ""}
                  {c.via.postesCadastroNaVia ? ` · ${c.via.postesCadastroNaVia} postes BDGD` : ""}
                </span>
              </td>
              {COLUNAS_TABELA.map((col) => (
                <td key={col} className="px-2 py-1.5 text-right">
                  <ValorCampo f={campo(c, col)} compacto />
                </td>
              ))}
              {!impressao && base && (
                <td className="px-2 py-1.5">
                  <Link href={`${base}/revisao?captura=${encodeURIComponent(c.id)}&painel=via`} className="text-acao-texto hover:underline" aria-label="Abrir na revisão">
                    <Icone nome="panorama_photosphere" tamanho={18} />
                  </Link>
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
      <p className="flex flex-wrap gap-x-4 gap-y-1 border-t border-borda px-3 py-2 text-[0.72rem] text-texto-fraco print:border-0">
        {(Object.keys(FONTES) as Fonte[]).map((k) => (
          <span key={k} className="flex items-center gap-1">
            <Icone nome={FONTES[k].icone} tamanho={14} className={COR_FONTE[k]} /> {FONTES[k].rotulo}
          </span>
        ))}
        <span className="flex items-center gap-1">
          <Icone nome="warning" tamanho={14} cheio className="text-atencao" /> fontes divergem (passe o mouse)
        </span>
        <span>— pendente</span>
      </p>
    </div>
  );
}
