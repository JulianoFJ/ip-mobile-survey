"use client";

import { fmt } from "@/dados/geometria";
import { FONTES, type Captura, type CampoVia, type Revisao } from "@/dados/tipos";
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
  const divergentes = captura.via.campos.filter((c) => c.divergente).length;
  const v = captura.via;
  return (
    <div className="space-y-4">
      <div className="rounded-pi border border-borda p-3 text-[0.84rem]">
        <p className="font-semibold text-navy">{v.logradouro ?? "Via sem nome no mapa"}</p>
        <p className="mt-0.5 text-[0.78rem] text-texto-fraco">
          {[
            v.classeOsm && `classe OSM ${v.classeOsm}`,
            v.maoUnica != null && (v.maoUnica ? "mão única" : "mão dupla"),
            v.postesCadastroNaVia ? `${v.postesCadastroNaVia} postes da BDGD na via` : "sem cadastro nesta via",
            v.tecnologia && `${v.tecnologia}${v.potenciaW ? ` ${v.potenciaW} W` : ""} (moda do cadastro)`,
          ]
            .filter(Boolean)
            .join(" · ")}
        </p>
      </div>
      <PlantaVia captura={captura} revisoes={revisoes} />
      <p className="text-[0.8rem] text-texto-fraco">
        {estimados} de {captura.via.campos.length} campos estimados
        {divergentes > 0 && <>, {divergentes} com fontes divergentes</>}. Passe o mouse num campo para ver a fonte e os outros valores.
      </p>
      <LegendaFontes />
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
  const fonte = campo.fonte ? FONTES[campo.fonte] : null;
  const balao = (
    <div className="max-w-xs space-y-1">
      {campo.candidatos.length ? (
        campo.candidatos.map((c, i) => (
          <p key={c.fonte}>
            <strong>{FONTES[c.fonte].rotulo}{i === 0 ? " (usada)" : ""}:</strong> {String(c.valor)}
            {campo.unidade && typeof c.valor === "number" ? ` ${campo.unidade}` : ""} — {c.detalhe}
          </p>
        ))
      ) : (
        <p>{campo.metodo}</p>
      )}
    </div>
  );
  return (
    <li>
      <Balao conteudo={balao} lado="left">
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
          {campo.divergente && <Icone nome="warning" tamanho={16} cheio className="text-atencao" rotulo="Fontes divergentes" />}
          {fonte ? (
            <Icone nome={fonte.icone} tamanho={16} className={campo.fonte === "cadastro" ? "text-sucesso" : campo.fonte === "mapa" ? "text-navy" : "text-acao-texto"} rotulo={fonte.rotulo} />
          ) : (
            <Icone nome="schedule" tamanho={16} className="text-texto-suave" />
          )}
        </div>
      </Balao>
    </li>
  );
}

function LegendaFontes() {
  return (
    <p className="flex flex-wrap gap-x-3 gap-y-1 text-[0.72rem] text-texto-fraco">
      <span className="flex items-center gap-1"><Icone nome={FONTES.imagem.icone} tamanho={14} className="text-acao-texto" /> imagem 360°</span>
      <span className="flex items-center gap-1"><Icone nome={FONTES.cadastro.icone} tamanho={14} className="text-sucesso" /> cadastro BDGD</span>
      <span className="flex items-center gap-1"><Icone nome={FONTES.mapa.icone} tamanho={14} className="text-navy" /> mapa OSM</span>
      <span className="flex items-center gap-1"><Icone nome="warning" tamanho={14} cheio className="text-atencao" /> fontes divergem</span>
      <span className="flex items-center gap-1"><Icone nome="schedule" tamanho={14} /> pendente</span>
    </p>
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
        {/* corte transversal medido: pista, passeios e canteiro como faixas ao longo do quadro */}
        {(() => {
          const c = captura.via.corte;
          if (!c) return null;
          const faixa = (x0: number, x1: number, cor: string, k: string) => {
            const [a] = P(Math.min(x0, x1), 0);
            const [b] = P(Math.max(x0, x1), 0);
            return <rect key={k} x={a} y={0} width={Math.max(b - a, 1)} height={H} fill={cor} />;
          };
          const els = [];
          const L = c.meioFioEsquerdaM;
          const R = c.meioFioDireitaM;
          if (L != null && R != null) els.push(faixa(-L, R, "#E66E9640", "pista"));
          if (L != null && c.passeioEsquerdaM) els.push(faixa(-L, -L - c.passeioEsquerdaM, "#F0C83C55", "pe"));
          if (R != null && c.passeioDireitaM) els.push(faixa(R, R + c.passeioDireitaM, "#F0C83C55", "pd"));
          if (c.canteiroM && c.canteiroLado) {
            const s = c.canteiroLado === "direita" ? 1 : -1;
            const borda = c.canteiroLado === "direita" ? R : L;
            if (borda != null) {
              els.push(faixa(s * borda, s * (borda + c.canteiroM), "#3CBE5A55", "ct"));
              if (c.pista2M) els.push(faixa(s * (borda + c.canteiroM), s * (borda + c.canteiroM + c.pista2M), "#E66E9640", "p2"));
            }
          }
          for (const [x, k] of [[L != null ? -L : null, "ml"], [R, "mr"]] as const) {
            if (x == null) continue;
            const [px] = P(x, 0);
            els.push(<line key={k} x1={px} x2={px} y1={0} y2={H} stroke="#B4285A" strokeWidth={1.2} />);
          }
          return <g>{els}</g>;
        })()}
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
        {captura.via.corte && (
          <span className="flex items-center gap-1">
            <span className="h-2 w-3 rounded-sm" style={{ background: "#E66E9666" }} /> pista medida
          </span>
        )}
        {captura.frente.fonte !== "eixo da pista" && (
          <span className="text-atencao-texto">sentido suposto ({captura.frente.fonte})</span>
        )}
      </figcaption>
    </figure>
  );
}
