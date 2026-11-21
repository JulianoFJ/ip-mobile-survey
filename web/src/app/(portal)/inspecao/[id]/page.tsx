"use client";

import dynamic from "next/dynamic";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useMemo, useState } from "react";
import { CabecalhoCampanha, Carregando, ComCampanha } from "@/componentes/Campanha";
import { urlPublica } from "@/dados/api";
import { contarPorClasse, fmt, mediana } from "@/dados/geometria";
import { useRevisoes } from "@/dados/revisao";
import { CLASSES, type Campanha, type Classe } from "@/dados/tipos";
import { Botao } from "@/ui/Botao";
import { CartaoKpi } from "@/ui/CartaoKpi";
import { Icone } from "@/ui/Icone";
import { cn } from "@/ui/lib/cn";

// O MapLibre precisa do navegador (window/WebGL).
const MapaResultados = dynamic(() => import("@/componentes/MapaResultados"), {
  ssr: false,
  loading: () => <Carregando texto="Carregando o mapa…" />,
});

export default function PainelCampanha() {
  const { id } = useParams<{ id: string }>();
  return <ComCampanha id={decodeURIComponent(id)}>{(c) => <Painel campanha={c} />}</ComCampanha>;
}

function Painel({ campanha }: { campanha: Campanha }) {
  const { mapa: revisoes } = useRevisoes(campanha.id);
  const [selecionada, setSelecionada] = useState<string | null>(null);
  const [cidade, setCidade] = useState<string>("");

  const cidades = useMemo(() => [...new Set(campanha.capturas.map((c) => c.cidade))].sort(), [campanha]);
  const capturas = useMemo(() => campanha.capturas.filter((c) => !cidade || c.cidade === cidade), [campanha, cidade]);
  const todas = capturas.flatMap((c) => c.deteccoes);
  const n = contarPorClasse(todas);
  const alturas = todas.filter((d) => d.classe === "poste" && d.alturaM != null && !d.alturaMinima).map((d) => d.alturaM as number);
  const comPosicao = todas.filter((d) => d.classe === "poste" && d.lat != null).length;
  const revisadas = todas.filter((d) => revisoes[d.id]).length;
  const confirmadas = todas.filter((d) => revisoes[d.id] === "confirmada").length;
  const sel = campanha.capturas.find((c) => c.id === selecionada) ?? null;
  const base = `/inspecao/${encodeURIComponent(campanha.id)}`;

  return (
    <>
      <CabecalhoCampanha
        campanha={campanha}
        acoes={
          <Botao asChild variante="primario">
            <Link href={`${base}/revisao`}>
              <Icone nome="rule" tamanho={18} /> Revisar detecções
            </Link>
          </Botao>
        }
      />
      <div className="space-y-5 p-6">
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-[0.84rem] text-texto-fraco">Cidade</span>
          <select
            value={cidade}
            onChange={(e) => {
              setCidade(e.target.value);
              setSelecionada(null);
            }}
            className="h-9 rounded-pi border border-borda-campo bg-superficie px-2 text-[0.88rem]"
          >
            <option value="">Todas ({cidades.length})</option>
            {cidades.map((c) => <option key={c}>{c}</option>)}
          </select>
        </div>

        <div className="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-6">
          <CartaoKpi rotulo="Panoramas" valor={fmt.n(capturas.length)} apoio={`${new Set(capturas.map((c) => c.cidade)).size} cidade(s)`} />
          <CartaoKpi rotulo="Postes detectados" valor={fmt.n(n.poste)} apoio={`${fmt.n(comPosicao)} com posição no mapa`} />
          <CartaoKpi
            rotulo="Altura mediana"
            valor={mediana(alturas)?.toLocaleString("pt-BR", { maximumFractionDigits: 1 }) ?? "—"}
            unidade="m"
            apoio={`${fmt.n(alturas.length)} postes com pé e topo visíveis`}
            ajuda="Estimativa de um quadro só, pelo plano do chão. Erra em rampa e quando o pé está atrás de um carro. A triangulação entre quadros substitui esta estimativa."
          />
          <CartaoKpi rotulo="Braços" valor={fmt.n(n.braco)} />
          <CartaoKpi rotulo="Luminárias" valor={fmt.n(n.luminaria)} />
          <CartaoKpi
            rotulo="Revisadas"
            valor={todas.length ? fmt.pct(revisadas / todas.length) : "—"}
            apoio={`${fmt.n(confirmadas)} confirmadas de ${fmt.n(revisadas)}`}
          />
        </div>

        <div className="grid gap-4 xl:grid-cols-[1fr_360px]">
          <MapaResultados capturas={capturas} revisoes={revisoes} cadastro={campanha.cadastro} selecionada={selecionada} aoSelecionar={setSelecionada} altura="min(68vh, 640px)" />
          <aside className="cartao flex max-h-[min(68vh,640px)] min-h-[320px] flex-col overflow-hidden">
            {sel ? (
              <div className="flex min-h-0 flex-1 flex-col">
                <div className="flex items-center justify-between border-b border-borda px-4 py-2.5">
                  <button type="button" onClick={() => setSelecionada(null)} className="flex items-center gap-1 text-[0.84rem] font-medium text-acao-texto hover:underline">
                    <Icone nome="arrow_back" tamanho={16} /> Lista
                  </button>
                  <span className="text-[0.8rem] text-texto-fraco">{fmt.data(sel.data)}</span>
                </div>
                <div className="min-h-0 flex-1 overflow-y-auto p-4">
                  <p className="font-semibold text-navy">{sel.cidade}</p>
                  <p className="text-[0.8rem] text-texto-fraco num">
                    {sel.lat.toFixed(6)}, {sel.lon.toFixed(6)} · rumo {Math.round(sel.rumo)}°
                  </p>
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src={urlPublica(sel.imagem)} alt={`Panorama de ${sel.cidade}`} className="mt-3 aspect-[2/1] w-full rounded-pi object-cover" />
                  <ul className="mt-3 space-y-1.5 text-[0.88rem]">
                    {(Object.keys(CLASSES) as Classe[]).map((k) => (
                      <li key={k} className="flex items-center justify-between">
                        <span className="flex items-center gap-2">
                          <span className="h-2.5 w-2.5 rounded-sm" style={{ background: CLASSES[k].cor }} /> {CLASSES[k].plural}
                        </span>
                        <span className="font-semibold num">{contarPorClasse(sel.deteccoes)[k]}</span>
                      </li>
                    ))}
                  </ul>
                  <p className="mt-3 text-[0.75rem] text-texto-fraco">
                    Imagem: {sel.autor}, {sel.licenca} ·{" "}
                    <a href={sel.origem} target="_blank" rel="noreferrer" className="text-acao-texto hover:underline">original</a>
                  </p>
                </div>
                <div className="border-t border-borda p-3">
                  <Botao asChild variante="secundario" className="w-full">
                    <Link href={`${base}/revisao?captura=${encodeURIComponent(sel.id)}`}>
                      <Icone nome="panorama_photosphere" tamanho={18} /> Abrir no visualizador
                    </Link>
                  </Botao>
                </div>
              </div>
            ) : (
              <>
                <p className="border-b border-borda px-4 py-2.5 text-[0.84rem] font-semibold text-navy">
                  Capturas <span className="font-normal text-texto-fraco">· clique no mapa ou na lista</span>
                </p>
                <ul className="min-h-0 flex-1 divide-y divide-borda overflow-y-auto">
                  {capturas.map((c) => {
                    const k = contarPorClasse(c.deteccoes);
                    const feitas = c.deteccoes.filter((d) => revisoes[d.id]).length;
                    return (
                      <li key={c.id}>
                        <button type="button" onClick={() => setSelecionada(c.id)} className="flex w-full items-center gap-3 px-4 py-2 text-left hover:bg-superficie-alt">
                          <Icone nome="panorama_photosphere" className="text-texto-suave" />
                          <span className="min-w-0 flex-1">
                            <span className="block truncate text-[0.88rem] font-medium text-texto">{c.cidade}</span>
                            <span className="block text-[0.76rem] text-texto-fraco">
                              {k.poste} postes · {k.luminaria} luminárias
                            </span>
                          </span>
                          <span className={cn("text-[0.72rem] font-semibold num", feitas === c.deteccoes.length && feitas > 0 ? "text-sucesso-texto" : "text-texto-suave")}>
                            {feitas}/{c.deteccoes.length}
                          </span>
                        </button>
                      </li>
                    );
                  })}
                </ul>
              </>
            )}
          </aside>
        </div>
      </div>
    </>
  );
}
