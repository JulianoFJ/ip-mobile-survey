"use client";

import { useParams, useRouter, useSearchParams } from "next/navigation";
import { Suspense, useCallback, useEffect, useMemo, useState } from "react";
import { CabecalhoCampanha, Carregando, ComCampanha } from "@/componentes/Campanha";
import { ViaMalha } from "@/componentes/ViaMalha";
import { VisualizadorPanorama } from "@/componentes/VisualizadorPanorama";
import { fmt } from "@/dados/geometria";
import { useRevisoes } from "@/dados/revisao";
import { CLASSES, type Campanha, type Classe, type Revisao } from "@/dados/tipos";
import { Botao } from "@/ui/Botao";
import { Icone } from "@/ui/Icone";
import { cn } from "@/ui/lib/cn";

export default function PaginaRevisao() {
  return (
    <Suspense fallback={<Carregando />}>
      <Conteudo />
    </Suspense>
  );
}

function Conteudo() {
  const { id } = useParams<{ id: string }>();
  return <ComCampanha id={decodeURIComponent(id)}>{(c) => <TelaRevisao campanha={c} />}</ComCampanha>;
}

function TelaRevisao({ campanha }: { campanha: Campanha }) {
  const busca = useSearchParams();
  const router = useRouter();
  const { mapa: revisoes, decidir, exportar } = useRevisoes(campanha.id);
  const [visiveis, setVisiveis] = useState<Record<Classe, boolean>>({ poste: true, braco: true, luminaria: true });
  const [selDet, setSelDet] = useState<string | null>(null);
  const [painel, setPainel] = useState<"deteccoes" | "via">(busca.get("painel") === "via" ? "via" : "deteccoes");

  const idCaptura = busca.get("captura") ?? campanha.capturas[0]?.id ?? "";
  const idx = Math.max(0, campanha.capturas.findIndex((c) => c.id === idCaptura));
  const captura = campanha.capturas[idx];

  const irPara = useCallback(
    (i: number) => {
      const c = campanha.capturas[(i + campanha.capturas.length) % campanha.capturas.length];
      if (c) router.replace(`?captura=${encodeURIComponent(c.id)}`, { scroll: false });
      setSelDet(null);
    },
    [campanha, router],
  );

  const dets = useMemo(
    () =>
      (captura?.deteccoes ?? [])
        .filter((d) => visiveis[d.classe])
        .sort((a, b) => a.az - b.az),
    [captura, visiveis],
  );
  const posSel = dets.findIndex((d) => d.id === selDet);

  const decidirSel = useCallback(
    (r: Revisao | null) => {
      const d = dets[posSel];
      if (!d) return;
      decidir(d.id, r);
      const prox = dets[posSel + 1];
      if (r && prox) setSelDet(prox.id);
    },
    [dets, posSel, decidir],
  );

  useEffect(() => {
    const tecla = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLSelectElement || e.metaKey || e.ctrlKey) return;
      const k = e.key.toLowerCase();
      if (k === "arrowright") irPara(idx + 1);
      else if (k === "arrowleft") irPara(idx - 1);
      else if (k === "j") setSelDet(dets[Math.min(dets.length - 1, posSel + 1)]?.id ?? null);
      else if (k === "k") setSelDet(dets[Math.max(0, posSel - 1)]?.id ?? null);
      else if (k === "c") decidirSel("confirmada");
      else if (k === "r") decidirSel("rejeitada");
      else if (k === "u") decidirSel(null);
      else return;
      e.preventDefault();
    };
    window.addEventListener("keydown", tecla);
    return () => window.removeEventListener("keydown", tecla);
  }, [idx, dets, posSel, irPara, decidirSel]);

  if (!captura) return null;
  const todas = campanha.capturas.flatMap((c) => c.deteccoes);
  const feitas = todas.filter((d) => revisoes[d.id]).length;

  return (
    <>
      <CabecalhoCampanha
        campanha={campanha}
        acoes={
          <Botao variante="download" onClick={exportar} title="Baixa as decisões em JSON (formato que a API vai receber)">
            Exportar revisões
          </Botao>
        }
      />
      <div className="space-y-4 p-6">
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-1">
            <Botao variante="secundario" tamanho="icone" icone="chevron_left" aria-label="Captura anterior" onClick={() => irPara(idx - 1)} />
            <select
              value={captura.id}
              onChange={(e) => irPara(campanha.capturas.findIndex((c) => c.id === e.target.value))}
              className="h-9 max-w-[260px] rounded-pi border border-borda-campo bg-superficie px-2 text-[0.88rem]"
              aria-label="Captura"
            >
              {campanha.capturas.map((c, i) => (
                <option key={c.id} value={c.id}>
                  {i + 1}. {c.cidade} — {c.deteccoes.filter((d) => revisoes[d.id]).length}/{c.deteccoes.length}
                </option>
              ))}
            </select>
            <Botao variante="secundario" tamanho="icone" icone="chevron_right" aria-label="Próxima captura" onClick={() => irPara(idx + 1)} />
          </div>
          <span className="text-[0.84rem] text-texto-fraco num">
            Captura {idx + 1} de {campanha.capturas.length}
          </span>
          <div className="flex flex-wrap gap-1.5" role="group" aria-label="Classes visíveis">
            {(Object.keys(CLASSES) as Classe[]).map((k) => (
              <button
                key={k}
                type="button"
                aria-pressed={visiveis[k]}
                onClick={() => setVisiveis((v) => ({ ...v, [k]: !v[k] }))}
                className={cn(
                  "flex items-center gap-1.5 rounded-chip border px-2.5 py-1 text-[0.8rem] font-medium",
                  visiveis[k] ? "border-borda-forte bg-superficie text-texto" : "border-borda text-texto-suave line-through",
                )}
              >
                <span className="h-2.5 w-2.5 rounded-sm" style={{ background: CLASSES[k].cor }} /> {CLASSES[k].plural}
              </button>
            ))}
          </div>
          <div className="ml-auto flex min-w-[200px] items-center gap-2">
            <span className="text-[0.8rem] text-texto-fraco num">
              {fmt.n(feitas)}/{fmt.n(todas.length)} revisadas
            </span>
            <span className="h-2 flex-1 overflow-hidden rounded-full bg-borda">
              <span className="block h-full bg-sucesso" style={{ width: `${todas.length ? (100 * feitas) / todas.length : 0}%` }} />
            </span>
          </div>
        </div>

        <div className="grid items-start gap-4 xl:grid-cols-[1fr_340px]">
          <VisualizadorPanorama captura={captura} revisoes={revisoes} classesVisiveis={visiveis} selecionada={selDet} aoSelecionar={setSelDet} />
          <aside className="cartao flex max-h-[78vh] flex-col overflow-hidden">
            <div className="flex items-center justify-between border-b border-borda px-2">
              <div role="tablist" aria-label="Painel lateral" className="flex">
                {([
                  ["deteccoes", `Detecções (${dets.length})`],
                  ["via", "Via e malha"],
                ] as const).map(([k, rot]) => (
                  <button
                    key={k}
                    role="tab"
                    type="button"
                    aria-selected={painel === k}
                    onClick={() => setPainel(k)}
                    className={cn(
                      "-mb-px border-b-2 px-2.5 py-2.5 text-[0.86rem] font-medium",
                      painel === k ? "border-teal font-semibold text-navy" : "border-transparent text-texto-fraco hover:text-texto",
                    )}
                  >
                    {rot}
                  </button>
                ))}
              </div>
              {painel === "deteccoes" && <Atalhos />}
            </div>
            {painel === "via" && (
              <div className="min-h-0 flex-1 overflow-y-auto p-3">
                <ViaMalha campanhaId={campanha.id} captura={captura} revisoes={revisoes} />
              </div>
            )}
            <ul className={cn("min-h-0 flex-1 divide-y divide-borda overflow-y-auto", painel !== "deteccoes" && "hidden")}>
              {dets.map((d) => {
                const rev = revisoes[d.id];
                const sel = d.id === selDet;
                return (
                  <li key={d.id} className={cn("px-4 py-2.5", sel && "bg-acao-suave")}>
                    <button type="button" onClick={() => setSelDet(d.id)} className="flex w-full items-center gap-2 text-left">
                      <span className="h-3 w-3 shrink-0 rounded-sm" style={{ background: CLASSES[d.classe].cor }} />
                      <span className="min-w-0 flex-1">
                        <span className="block text-[0.88rem] font-medium text-texto">
                          {CLASSES[d.classe].rotulo}{" "}
                          <span className="font-normal text-texto-fraco num">· confiança {fmt.score(d.score)}</span>
                        </span>
                        <span className="block text-[0.76rem] text-texto-fraco num">
                          {d.classe === "poste"
                            ? d.alturaM != null
                              ? `${d.alturaMinima ? "≥ " : ""}${fmt.m(d.alturaM)} de altura · a ${fmt.m(d.distanciaM, 0)}${
                                  d.triangulado ? ` · triangulado em ${d.triangulado.quadros} fotos` : ""
                                }`
                              : "pé não visível: sem altura"
                            : `azimute ${Math.round((d.az * 180) / Math.PI)}°`}
                        </span>
                      </span>
                      {rev && (
                        <Icone
                          nome={rev === "confirmada" ? "check_circle" : "cancel"}
                          cheio
                          className={rev === "confirmada" ? "text-sucesso" : "text-erro"}
                          rotulo={rev === "confirmada" ? "Confirmada" : "Rejeitada"}
                        />
                      )}
                    </button>
                    {sel && (
                      <div className="mt-2 flex gap-2">
                        <Botao variante="secundario" tamanho="compacto" icone="check" onClick={() => decidirSel("confirmada")} className="flex-1">
                          Confirmar
                        </Botao>
                        <Botao variante="perigo" tamanho="compacto" icone="close" onClick={() => decidirSel("rejeitada")} className="flex-1">
                          Rejeitar
                        </Botao>
                        {rev && <Botao variante="terciario" tamanho="compacto" icone="undo" aria-label="Desfazer" onClick={() => decidirSel(null)} />}
                      </div>
                    )}
                  </li>
                );
              })}
            </ul>
          </aside>
        </div>
      </div>
    </>
  );
}

function Atalhos() {
  return (
    <details className="relative text-[0.78rem]">
      <summary className="flex cursor-pointer list-none items-center gap-1 text-acao-texto">
        <Icone nome="keyboard" tamanho={16} /> Atalhos
      </summary>
      <dl className="absolute right-0 z-10 mt-1 grid w-56 grid-cols-[auto_1fr] gap-x-3 gap-y-1 rounded-pi border border-borda bg-superficie p-3 shadow-card">
        {[
          ["J / K", "próxima / anterior"],
          ["C", "confirmar"],
          ["R", "rejeitar"],
          ["U", "desfazer"],
          ["← / →", "captura anterior / próxima"],
        ].map(([k, v]) => (
          <div key={k} className="contents">
            <dt>
              <kbd className="rounded border border-borda bg-superficie-alt px-1 font-mono">{k}</kbd>
            </dt>
            <dd className="text-texto-fraco">{v}</dd>
          </div>
        ))}
      </dl>
    </details>
  );
}
