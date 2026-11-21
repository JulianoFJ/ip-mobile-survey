"use client";

import { fmt } from "@/dados/geometria";
import type { Captura, CampoVia, Revisao } from "@/dados/tipos";
import { Balao } from "@/ui/Ajuda";
import { Icone } from "@/ui/Icone";
import { cn } from "@/ui/lib/cn";

/** Grupos de colunas da planilha de simulação, na ordem em que o engenheiro lê. */
const GRUPOS: { titulo: string; icone: string; colunas: string[] }[] = [
  { titulo: "Seção transversal", icone: "width", colunas: ["R", "S", "T", "U", "V", "W", "X", "Y", "Z", "AA", "AB", "AC"] },
  { titulo: "Posteação", icone: "vertical_align_top", colunas: ["AD", "AE", "AF", "AI"] },
  { titulo: "Luminária", icone: "lightbulb", colunas: ["AG", "AL", "AJ", "AH", "AM"] },
];

/** Atributos de via e malha de um panorama, com a planta vista de cima. */
export function ViaMalha({ captura, revisoes }: { captura: Captura; revisoes: Record<string, Revisao> }) {
  const porColuna = new Map(captura.via.campos.map((c) => [c.coluna, c]));
  const estimados = captura.via.campos.filter((c) => c.estado === "estimado").length;
  return (
    <div className="space-y-4">
      <PlantaVia captura={captura} revisoes={revisoes} />
      <p className="text-[0.8rem] text-texto-fraco">
        {estimados} de {captura.via.campos.length} campos de levantamento estimados neste panorama. Passe o mouse num campo para ver como foi
        obtido.
      </p>
      {GRUPOS.map((g) => (
        <section key={g.titulo}>
          <h3 className="rotulo-secao mb-1 flex items-center gap-1.5">
            <Icone nome={g.icone} tamanho={15} /> {g.titulo}
          </h3>
          <ul className="divide-y divide-borda rounded-pi border border-borda">
            {g.colunas.map((col) => {
              const c = porColuna.get(col);
              return c ? <LinhaCampo key={col} campo={c} /> : null;
            })}
          </ul>
        </section>
      ))}
    </div>
  );
}

function LinhaCampo({ campo }: { campo: CampoVia }) {
  const ok = campo.estado === "estimado";
  return (
    <li>
      <Balao conteudo={campo.metodo} lado="left">
        <div tabIndex={0} className="flex items-center gap-2 px-2.5 py-1.5 text-[0.84rem] outline-none focus-visible:bg-superficie-alt">
          <span className="w-7 shrink-0 rounded bg-superficie-alt text-center font-mono text-[0.7rem] text-texto-fraco">{campo.coluna}</span>
          <span className="min-w-0 flex-1 truncate text-texto">{campo.rotulo}</span>
          {ok ? (
            <span className="font-semibold text-navy num">
              {typeof campo.valor === "number" ? campo.valor.toLocaleString("pt-BR") : campo.valor}
              {campo.unidade && <span className="ml-0.5 font-normal text-texto-fraco">{campo.unidade}</span>}
            </span>
          ) : (
            <span className="text-[0.75rem] text-texto-suave">pendente</span>
          )}
          <Icone nome={ok ? "check_circle" : "schedule"} tamanho={16} cheio={ok} className={ok ? "text-sucesso" : "text-texto-suave"} />
        </div>
      </Balao>
    </li>
  );
}

/**
 * Planta vista de cima: câmera na origem, deslocamento para cima. Cada poste com o pé
 * visível aparece na posição estimada pelo plano do chão.
 */
function PlantaVia({ captura, revisoes }: { captura: Captura; revisoes: Record<string, Revisao> }) {
  const W = 300;
  const H = 300;
  const ESC = 3.4; // px por metro
  const cx = W / 2;
  const cy = H * 0.62;
  const P = (x: number, y: number): [number, number] => [cx + x * ESC, cy - y * ESC];
  const postes = captura.deteccoes.filter((d) => d.planta && revisoes[d.id] !== "rejeitada");
  const fora = postes.filter((d) => {
    const [px, py] = P(d.planta!.x, d.planta!.y);
    return px < 6 || px > W - 6 || py < 6 || py > H - 6;
  }).length;
  const alin = captura.via.larguraAlinhamentosM;
  const vao = captura.via.campos.find((c) => c.coluna === "AF");
  const cor = { esquerda: "#0EA5E9", direita: "#E8A24D", centro: "#8B5CF6" } as const;

  return (
    <figure className="rounded-pi border border-borda bg-superficie-alt p-2">
      <svg viewBox={`0 0 ${W} ${H}`} className="mx-auto block w-full max-w-[320px]" role="img" aria-label="Planta da via vista de cima com os postes estimados">
        {/* grade de 10 m */}
        {Array.from({ length: 9 }, (_, i) => (i - 4) * 10).map((m) => (
          <g key={m} className="text-borda-forte">
            <line x1={P(m, 0)[0]} x2={P(m, 0)[0]} y1={0} y2={H} stroke="currentColor" strokeOpacity={m === 0 ? 0.6 : 0.25} strokeDasharray={m === 0 ? "4 4" : undefined} />
            <line y1={cy - m * ESC} y2={cy - m * ESC} x1={0} x2={W} stroke="currentColor" strokeOpacity={0.25} />
            {m !== 0 && (
              <text x={4} y={cy - m * ESC - 2} fontSize={8} fill="currentColor" className="text-texto-suave">
                {m > 0 ? "+" : ""}
                {m} m
              </text>
            )}
          </g>
        ))}
        {/* veículo e sentido */}
        <rect x={cx - 4} y={cy - 7} width={8} height={14} rx={2} fill="#1B3664" />
        <path d={`M ${cx} ${cy - 22} l -5 8 h 10 z`} fill="#1B3664" />
        {/* cota dos alinhamentos */}
        {alin != null && (
          <text x={cx} y={H - 6} textAnchor="middle" fontSize={9} fill="#1B3664" fontWeight={600}>
            {fmt.m(alin)} entre alinhamentos de postes
          </text>
        )}
        {postes.map((d) => {
          const [px, py] = P(d.planta!.x, d.planta!.y);
          if (px < 6 || px > W - 6 || py < 6 || py > H - 6) return null;
          return (
            <g key={d.id}>
              <circle cx={px} cy={py} r={4.5} fill={cor[d.planta!.lado]} stroke="#1B3664" strokeWidth={revisoes[d.id] === "confirmada" ? 2 : 0.8} />
              {d.alturaM != null && (
                <text x={px + 6} y={py + 3} fontSize={8} fill="currentColor" className="text-texto-fraco">
                  {d.alturaM.toFixed(0)} m
                </text>
              )}
            </g>
          );
        })}
      </svg>
      <figcaption className="mt-1 flex flex-wrap justify-center gap-x-3 gap-y-1 text-[0.72rem] text-texto-fraco">
        <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-full" style={{ background: cor.esquerda }} /> esquerda</span>
        <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-full" style={{ background: cor.direita }} /> direita</span>
        <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-full" style={{ background: cor.centro }} /> canteiro</span>
        {vao?.valor != null && <span className="font-semibold text-navy">vão {fmt.m(vao.valor as number)}</span>}
        {fora > 0 && <span className={cn("text-texto-suave")}>{fora} fora do quadro</span>}
        {captura.rumoDeslocamento == null && <span className="text-atencao-texto">sentido suposto: centro da imagem</span>}
      </figcaption>
    </figure>
  );
}
