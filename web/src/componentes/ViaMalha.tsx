"use client";

import { useRef, useState, type PointerEvent as RPointerEvent } from "react";
import { fmt } from "@/dados/geometria";
import { aplicarCorrecao, useCorrecoesLargura, type CorrecaoLargura } from "@/dados/revisao";
import { FONTES, type Captura, type CampoVia, type Revisao, type ViaMalha as TViaMalha } from "@/dados/tipos";
import { Botao } from "@/ui/Botao";
import { Balao } from "@/ui/Ajuda";
import { Icone } from "@/ui/Icone";
import { cn } from "@/ui/lib/cn";

/** Grupos de colunas da planilha de simulação, na ordem em que o engenheiro lê. */
const GRUPOS: { titulo: string; icone: string; colunas: string[] }[] = [
  { titulo: "Seção transversal", icone: "width", colunas: ["R", "S", "T", "U", "V", "W", "X", "Y", "Z", "AA", "AB", "AC"] },
  { titulo: "Posteação", icone: "vertical_align_top", colunas: ["AD", "AE", "AF", "AI"] },
  { titulo: "Luminária", icone: "lightbulb", colunas: ["AG", "AL", "AJ", "AH", "AM"] },
];

type Corte = NonNullable<TViaMalha["corte"]>;

const r1 = (x: number | null | undefined) => (x == null ? null : Math.round(x * 10) / 10);

function rascunhoDe(c: Captura): CorrecaoLargura {
  const k = c.via.corte;
  return {
    meioFioEsquerdaM: r1(k?.meioFioEsquerdaM) ?? 3,
    meioFioDireitaM: r1(k?.meioFioDireitaM) ?? 3,
    passeioEsquerdaM: r1(k?.passeioEsquerdaM),
    passeioDireitaM: r1(k?.passeioDireitaM),
    canteiroM: r1(k?.canteiroM),
    pista2M: r1(k?.pista2M),
    revisadoEm: new Date().toISOString(),
  };
}

/** Atributos de via e malha de um panorama, com a planta vista de cima e a correção de larguras. */
export function ViaMalha({ campanhaId, captura: original, revisoes }: {
  campanhaId: string;
  captura: Captura;
  revisoes: Record<string, Revisao>;
}) {
  const { correcoes, corrigir } = useCorrecoesLargura(campanhaId);
  const correcao = correcoes[original.id];
  const [rascunho, setRascunho] = useState<CorrecaoLargura | null>(null);
  const captura = aplicarCorrecao(original, rascunho ?? correcao);
  const porColuna = new Map(captura.via.campos.map((c) => [c.coluna, c]));
  const estimados = captura.via.campos.filter((c) => c.estado === "estimado").length;
  const divergentes = captura.via.campos.filter((c) => c.divergente).length;
  const v = captura.via;
  const editar = (k: keyof CorrecaoLargura, val: number | null) =>
    setRascunho((r) => (r ? { ...r, [k]: val == null ? null : Math.max(0, Math.round(val * 10) / 10) } : r));
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
      <PlantaVia
        captura={captura}
        revisoes={revisoes}
        editando={rascunho != null}
        aoArrastar={(lado, m) => editar(lado === "esquerda" ? "meioFioEsquerdaM" : "meioFioDireitaM", m)}
      />
      {rascunho ? (
        <div className="space-y-3 rounded-pi border border-destaque/40 bg-destaque/5 p-3">
          <p className="text-[0.8rem] text-texto">
            <strong>Corrigindo larguras.</strong> Arraste as linhas de meio-fio na planta ou digite os valores (metros, a partir do eixo do
            carro para o meio-fio).
          </p>
          <div className="grid grid-cols-2 gap-2 text-[0.8rem]">
            <CampoNum rotulo="Meio-fio esquerdo" valor={rascunho.meioFioEsquerdaM} aoMudar={(x) => editar("meioFioEsquerdaM", x)} />
            <CampoNum rotulo="Meio-fio direito" valor={rascunho.meioFioDireitaM} aoMudar={(x) => editar("meioFioDireitaM", x)} />
            <CampoNum rotulo="Passeio esquerdo (S)" valor={rascunho.passeioEsquerdaM} aoMudar={(x) => editar("passeioEsquerdaM", x)} />
            <CampoNum rotulo="Passeio direito (X)" valor={rascunho.passeioDireitaM} aoMudar={(x) => editar("passeioDireitaM", x)} />
            <CampoNum rotulo="Canteiro (Y)" valor={rascunho.canteiroM} aoMudar={(x) => editar("canteiroM", x)} />
            <CampoNum rotulo="Via 2 (W)" valor={rascunho.pista2M} aoMudar={(x) => editar("pista2M", x)} />
          </div>
          <p className="text-[0.8rem] font-semibold text-navy num">
            Largura da via 1 (T): {fmt.m((rascunho.meioFioEsquerdaM ?? 0) + (rascunho.meioFioDireitaM ?? 0))}
          </p>
          <div className="flex flex-wrap gap-2">
            <Botao
              variante="primario"
              tamanho="compacto"
              icone="check"
              onClick={() => {
                corrigir(original.id, { ...rascunho, revisadoEm: new Date().toISOString() });
                setRascunho(null);
              }}
            >
              Salvar correção
            </Botao>
            <Botao variante="secundario" tamanho="compacto" onClick={() => setRascunho(null)}>
              Descartar
            </Botao>
          </div>
        </div>
      ) : (
        <div className="flex flex-wrap items-center gap-2">
          <Botao variante="secundario" tamanho="compacto" icone="edit_square" onClick={() => setRascunho(correcao ? { ...correcao } : rascunhoDe(original))}>
            Corrigir larguras
          </Botao>
          {correcao && (
            <>
              <span className="text-[0.76rem] text-destaque">Corrigido em {new Date(correcao.revisadoEm).toLocaleDateString("pt-BR")}</span>
              <Botao variante="terciario" tamanho="compacto" icone="undo" onClick={() => corrigir(original.id, null)}>
                Voltar ao medido
              </Botao>
            </>
          )}
        </div>
      )}
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

function CampoNum({ rotulo, valor, aoMudar }: { rotulo: string; valor: number | null; aoMudar: (v: number | null) => void }) {
  return (
    <label className="block">
      <span className="text-texto-fraco">{rotulo}</span>
      <input
        type="number"
        step={0.1}
        min={0}
        value={valor ?? ""}
        placeholder="—"
        onChange={(e) => aoMudar(e.target.value === "" ? null : Number(e.target.value))}
        className="mt-0.5 h-8 w-full rounded-pi border border-borda-campo bg-superficie px-2 text-right num"
      />
    </label>
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
            <Icone
              nome={fonte.icone}
              tamanho={16}
              className={campo.fonte === "cadastro" ? "text-sucesso" : campo.fonte === "mapa" ? "text-navy" : campo.fonte === "revisao" ? "text-destaque" : "text-acao-texto"}
              rotulo={fonte.rotulo}
            />
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
      <span className="flex items-center gap-1"><Icone nome={FONTES.revisao.icone} tamanho={14} className="text-destaque" /> revisão</span>
      <span className="flex items-center gap-1"><Icone nome="warning" tamanho={14} cheio className="text-atencao" /> fontes divergem</span>
      <span className="flex items-center gap-1"><Icone nome="schedule" tamanho={14} /> pendente</span>
    </p>
  );
}

/**
 * Planta vista de cima: câmera na origem, deslocamento para cima. Cada poste com o pé
 * visível aparece na posição estimada pelo plano do chão.
 */
function PlantaVia({ captura, revisoes, editando, aoArrastar }: {
  captura: Captura;
  revisoes: Record<string, Revisao>;
  editando?: boolean;
  aoArrastar?: (lado: "esquerda" | "direita", metros: number) => void;
}) {
  const svg = useRef<SVGSVGElement>(null);
  const [arrastando, setArrastando] = useState<"esquerda" | "direita" | null>(null);
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
  const mover = (e: RPointerEvent<SVGSVGElement>) => {
    if (!arrastando || !svg.current) return;
    const m = svg.current.getScreenCTM();
    if (!m) return;
    const x = (e.clientX - m.e) / m.a; // px do viewBox
    const metros = (x - cx) / ESC;
    aoArrastar?.(arrastando, arrastando === "esquerda" ? Math.max(0.5, -metros) : Math.max(0.5, metros));
  };
  const corteAtual: Corte | null = captura.via.corte;

  return (
    <figure className="rounded-pi border border-borda bg-superficie-alt p-2">
      <svg
        ref={svg}
        viewBox={`0 0 ${W} ${H}`}
        className={cn("mx-auto block w-full max-w-[320px] touch-none", arrastando && "cursor-ew-resize")}
        role="img"
        aria-label="Planta da via vista de cima com os postes estimados"
        onPointerMove={mover}
        onPointerUp={() => setArrastando(null)}
        onPointerLeave={() => setArrastando(null)}
      >
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
          const c = corteAtual;
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
          for (const [x, k, lado] of [[L != null ? -L : null, "ml", "esquerda"], [R, "mr", "direita"]] as const) {
            if (x == null) continue;
            const [px] = P(x, 0);
            els.push(<line key={k} x1={px} x2={px} y1={0} y2={H} stroke={editando ? "#8B5CF6" : "#B4285A"} strokeWidth={editando ? 2 : 1.2} />);
            if (editando) {
              els.push(
                <g
                  key={`${k}-alca`}
                  className="cursor-ew-resize"
                  onPointerDown={(e) => {
                    (e.target as Element).setPointerCapture?.(e.pointerId);
                    setArrastando(lado);
                  }}
                >
                  <rect x={px - 8} y={0} width={16} height={H} fill="transparent" />
                  <rect x={px - 6} y={8} width={12} height={20} rx={3} fill="#8B5CF6" />
                  <text x={px} y={22} textAnchor="middle" fontSize={9} fill="#fff" fontWeight={700}>↔</text>
                </g>,
              );
            }
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
