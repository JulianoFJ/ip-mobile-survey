"use client";

import { useState } from "react";
import { urlPublica } from "@/dados/api";
import { fmt, retangulosDaDeteccao } from "@/dados/geometria";
import { CLASSES, type Captura, type Classe, type Revisao } from "@/dados/tipos";
import { Icone } from "@/ui/Icone";
import { cn } from "@/ui/lib/cn";

/** Tamanho da imagem exportada; as caixas são desenhadas nesse sistema de coordenadas. */
const L = 2048;
const A = 1024;

export interface VisualizadorProps {
  captura: Captura;
  revisoes: Record<string, Revisao>;
  classesVisiveis: Record<Classe, boolean>;
  selecionada?: string | null;
  aoSelecionar?: (deteccaoId: string) => void;
}

/**
 * Panorama equirretangular com as detecções desenhadas por cima (SVG no mesmo sistema de
 * coordenadas da imagem). Mostra a faixa de −35° a +75° de elevação, onde estão as
 * estruturas; o nadir (capô do carro) fica de fora.
 */
export function VisualizadorPanorama({ captura, revisoes, classesVisiveis, selecionada, aoSelecionar }: VisualizadorProps) {
  const [zoom, setZoom] = useState<1 | 2>(1);
  const [inteiro, setInteiro] = useState(false);
  // Recorte vertical: de +75° (v = 0,083) a −35° (v = 0,694).
  const y0 = inteiro ? 0 : Math.round(A * (15 / 180));
  const y1 = inteiro ? A : Math.round(A * (125 / 180));
  const dets = captura.deteccoes.filter((d) => classesVisiveis[d.classe]);
  // Desenha postes primeiro, para braço e luminária ficarem por cima.
  const ordem: Classe[] = ["poste", "braco", "luminaria"];
  dets.sort((a, b) => ordem.indexOf(a.classe) - ordem.indexOf(b.classe));

  return (
    <div className="overflow-hidden rounded-card border border-borda bg-navy-fixo">
      <div className="flex items-center justify-between gap-2 border-b border-white/10 px-3 py-2 text-[0.8rem] text-white/80">
        <span className="truncate">
          {captura.cidade} · {fmt.data(captura.data)} · {captura.camera} · rumo {Math.round(captura.rumo)}°
        </span>
        <span className="flex shrink-0 items-center gap-1">
          <BotaoBarra ativo={inteiro} aoClicar={() => setInteiro((x) => !x)} icone="height" rotulo={inteiro ? "Recortar" : "Imagem inteira"} />
          <BotaoBarra ativo={zoom === 2} aoClicar={() => setZoom((z) => (z === 1 ? 2 : 1))} icone={zoom === 1 ? "zoom_in" : "zoom_out"} rotulo={zoom === 1 ? "Ampliar" : "Reduzir"} />
          <a href={captura.origem} target="_blank" rel="noreferrer" className="flex items-center gap-1 rounded px-2 py-1 hover:bg-white/10">
            <Icone nome="open_in_new" tamanho={16} /> Original
          </a>
        </span>
      </div>
      <div className="overflow-x-auto">
        <div style={{ width: `${zoom * 100}%` }}>
          <svg viewBox={`0 ${y0} ${L} ${y1 - y0}`} className="block h-auto w-full select-none" role="img" aria-label={`Panorama de ${captura.cidade} com ${dets.length} detecções`}>
            <image href={urlPublica(captura.imagem)} x={0} y={0} width={L} height={A} preserveAspectRatio="none" />
            {dets.map((d) => {
              const rev = revisoes[d.id];
              const sel = d.id === selecionada;
              const cor = rev === "rejeitada" ? "#DC5B52" : CLASSES[d.classe].cor;
              return retangulosDaDeteccao(d, L, A).map((r, i) => (
                <g key={`${d.id}-${i}`} onClick={() => aoSelecionar?.(d.id)} className="cursor-pointer">
                  <rect
                    x={r.x}
                    y={r.y}
                    width={r.w}
                    height={r.h}
                    fill={sel ? `${cor}33` : "transparent"}
                    stroke={cor}
                    strokeWidth={sel ? 4 : 2.2}
                    strokeDasharray={rev === "rejeitada" ? "8 6" : d.classe === "poste" && (d.cortadoBase || d.cortadoTopo) ? "3 3" : undefined}
                    vectorEffect="non-scaling-stroke"
                  />
                  {rev === "confirmada" && i === 0 && (
                    <circle cx={r.x + r.w} cy={r.y} r={7} fill="#17A672" stroke="#fff" strokeWidth={1.5} />
                  )}
                  {(sel || d.classe === "poste") && i === 0 && (
                    <text x={r.x + 3} y={r.y - 5} fill={cor} fontSize={sel ? 17 : 13} fontWeight={600} paintOrder="stroke" stroke="#0b1530" strokeWidth={3}>
                      {d.classe === "poste" && d.alturaM != null
                        ? `${d.alturaMinima ? "≥" : ""}${d.alturaM.toFixed(1)} m`
                        : fmt.score(d.score)}
                    </text>
                  )}
                </g>
              ));
            })}
          </svg>
        </div>
      </div>
    </div>
  );
}

function BotaoBarra({ ativo, aoClicar, icone, rotulo }: { ativo: boolean; aoClicar: () => void; icone: string; rotulo: string }) {
  return (
    <button type="button" onClick={aoClicar} aria-pressed={ativo} className={cn("flex items-center gap-1 rounded px-2 py-1 hover:bg-white/10", ativo && "bg-white/15")}>
      <Icone nome={icone} tamanho={16} /> {rotulo}
    </button>
  );
}
