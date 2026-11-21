"use client";

import Link from "next/link";
import { useRef, useState, type ReactNode } from "react";
import { Cabecalho } from "@/componentes/Casca";
import { conferirImagem, tamanhoLegivel, type ResultadoImagem } from "@/dados/conferencia";
import { Botao } from "@/ui/Botao";
import { Icone } from "@/ui/Icone";
import { cn } from "@/ui/lib/cn";
import { Selo } from "@/ui/Selo";

const PASSOS = ["Identificação", "Equipamento", "Arquivos", "Conferir e processar"] as const;

/** Segundos por panorama no detector (16 vistas, OWLv2 base, Apple M3). Só para a estimativa. */
const SEG_POR_PANORAMA = 20;

interface Dados {
  nome: string;
  municipio: string;
  projeto: string;
  data: string;
  equipe: string;
  camera: string;
  montagem: string;
  alturaCamera: string;
  gnss: string;
}

const INICIAL: Dados = {
  nome: "",
  municipio: "",
  projeto: "",
  data: "",
  equipe: "",
  camera: "GoPro Max",
  montagem: "Teto do veículo",
  alturaCamera: "1,90",
  gnss: "GPS da câmera",
};

export default function NovaInspecao() {
  const [passo, setPasso] = useState(0);
  const [dados, setDados] = useState<Dados>(INICIAL);
  const [panoramas, setPanoramas] = useState<File[]>([]);
  const [trajetoria, setTrajetoria] = useState<File[]>([]);
  const [cadastro, setCadastro] = useState<File[]>([]);
  const [conferidas, setConferidas] = useState<ResultadoImagem[]>([]);
  const [conferindo, setConferindo] = useState(false);

  const campo = (k: keyof Dados) => ({
    value: dados[k],
    onChange: (e: { target: { value: string } }) => setDados((d) => ({ ...d, [k]: e.target.value })),
  });

  const conferir = async (arquivos: File[]) => {
    setConferindo(true);
    setConferidas([]);
    const out: ResultadoImagem[] = [];
    for (const a of arquivos) {
      out.push(await conferirImagem(a));
      setConferidas([...out]);
    }
    setConferindo(false);
  };

  const okPasso = [
    dados.nome.trim() !== "" && dados.municipio.trim() !== "",
    Number(dados.alturaCamera.replace(",", ".")) > 0,
    panoramas.length > 0,
    true,
  ];

  return (
    <>
      <Cabecalho
        trilha={[{ href: "/inspecao", rotulo: "Inspeções" }]}
        titulo="Nova inspeção"
        descricao="Registre o levantamento e envie os arquivos. Antes do envio, as imagens são conferidas aqui mesmo, no navegador."
      />
      <div className="mx-auto max-w-4xl p-6">
        <ol className="mb-6 grid grid-cols-4 gap-2" aria-label="Passos">
          {PASSOS.map((p, i) => (
            <li key={p}>
              <button
                type="button"
                onClick={() => i <= passo && setPasso(i)}
                disabled={i > passo}
                aria-current={i === passo ? "step" : undefined}
                className={cn(
                  "flex w-full items-center gap-2 border-t-[3px] pt-2 text-left text-[0.84rem] font-medium",
                  i < passo && "border-sucesso text-sucesso-texto",
                  i === passo && "border-teal text-navy",
                  i > passo && "border-borda text-texto-suave",
                )}
              >
                <Icone nome={i < passo ? "check_circle" : "radio_button_unchecked"} tamanho={18} cheio={i < passo} />
                <span className="hidden sm:inline">{p}</span>
              </button>
            </li>
          ))}
        </ol>

        <section className="cartao p-6">
          {passo === 0 && (
            <div className="grid gap-4 sm:grid-cols-2">
              <Campo rotulo="Nome da inspeção" obrigatorio className="sm:col-span-2">
                <input {...campo("nome")} placeholder="Ex.: Inspeção de campo — Mafra, área urbana" className={entrada} />
              </Campo>
              <Campo rotulo="Município" obrigatorio>
                <input {...campo("municipio")} placeholder="Ex.: Mafra — SC" className={entrada} />
              </Campo>
              <Campo rotulo="Projeto no Ignis" ajuda="Liga a inspeção ao projeto, para os arquivos irem para o acervo dele.">
                <input {...campo("projeto")} placeholder="Ex.: BRDE05 — IP Planalto Norte" className={entrada} />
              </Campo>
              <Campo rotulo="Data do levantamento">
                <input type="date" {...campo("data")} className={entrada} />
              </Campo>
              <Campo rotulo="Equipe de campo">
                <input {...campo("equipe")} placeholder="Nomes ou empresa" className={entrada} />
              </Campo>
            </div>
          )}

          {passo === 1 && (
            <div className="grid gap-4 sm:grid-cols-2">
              <Campo rotulo="Câmera 360°">
                <select {...campo("camera")} className={entrada}>
                  {["GoPro Max", "Insta360 X3", "Insta360 X4", "Ricoh Theta", "Outra"].map((c) => <option key={c}>{c}</option>)}
                </select>
              </Campo>
              <Campo rotulo="Montagem">
                <select {...campo("montagem")} className={entrada}>
                  {["Teto do veículo", "Mochila / a pé", "Bastão na mão"].map((c) => <option key={c}>{c}</option>)}
                </select>
              </Campo>
              <Campo
                rotulo="Altura da câmera sobre o chão (m)"
                obrigatorio
                ajuda="Entra na estimativa da altura e da distância de cada poste. No teto de um carro de passeio, fica perto de 1,9 m."
              >
                <input inputMode="decimal" {...campo("alturaCamera")} className={entrada} />
              </Campo>
              <Campo rotulo="Posicionamento" ajuda="Com RTK, a posição dos postes no mapa fica na casa dos decímetros; com o GPS da câmera, na casa dos metros.">
                <select {...campo("gnss")} className={entrada}>
                  {["GPS da câmera", "GNSS RTK externo (arquivo de trajetória)"].map((c) => <option key={c}>{c}</option>)}
                </select>
              </Campo>
            </div>
          )}

          {passo === 2 && (
            <div className="space-y-4">
              <Envio
                titulo="Panoramas 360°"
                descricao="Imagens equirretangulares (.jpg), exportadas da câmera. Pode arrastar a pasta inteira."
                aceita="image/jpeg"
                icone="panorama_photosphere"
                obrigatorio
                arquivos={panoramas}
                aoMudar={(fs) => {
                  setPanoramas(fs);
                  void conferir(fs);
                }}
              />
              <Envio
                titulo="Trajetória GNSS"
                descricao="Opcional. .gpx, .csv ou .nmea do receptor RTK. Sem ele, vale o GPS gravado em cada foto."
                aceita=".gpx,.csv,.nmea,.txt"
                icone="route"
                arquivos={trajetoria}
                aoMudar={setTrajetoria}
              />
              <Envio
                titulo="Cadastro do município"
                descricao="Opcional. Planilha do cadastro de IP (.xlsx ou .csv), para o confronto ponto a ponto com o levantamento."
                aceita=".xlsx,.xls,.csv"
                icone="table_view"
                arquivos={cadastro}
                aoMudar={setCadastro}
              />
              {panoramas.length > 0 && <Conferencia resultados={conferidas} total={panoramas.length} conferindo={conferindo} />}
            </div>
          )}

          {passo === 3 && (
            <Resumo dados={dados} panoramas={panoramas} trajetoria={trajetoria} cadastro={cadastro} conferidas={conferidas} />
          )}
        </section>

        <div className="mt-4 flex items-center justify-between">
          <Botao variante="terciario" icone="arrow_back" onClick={() => setPasso((p) => Math.max(0, p - 1))} disabled={passo === 0}>
            Voltar
          </Botao>
          {passo < 3 ? (
            <Botao variante="primario" iconeDireita="arrow_forward" onClick={() => setPasso((p) => p + 1)} disabled={!okPasso[passo]}>
              Continuar
            </Botao>
          ) : (
            <Botao variante="primario" icone="play_arrow" disabled title="O envio ao servidor ainda não está ligado">
              Enviar e processar
            </Botao>
          )}
        </div>
      </div>
    </>
  );
}

const entrada =
  "h-10 w-full rounded-pi border border-borda-campo bg-superficie px-3 text-[0.92rem] text-texto placeholder:text-texto-suave focus:border-acao focus:outline-none";

function Campo({ rotulo, obrigatorio, ajuda, className, children }: {
  rotulo: string; obrigatorio?: boolean; ajuda?: string; className?: string; children: ReactNode;
}) {
  return (
    <label className={cn("block", className)}>
      <span className="mb-1 block text-[0.84rem] font-medium text-texto">
        {rotulo} {obrigatorio && <span className="text-erro-texto">*</span>}
      </span>
      {children}
      {ajuda && <span className="mt-1 block text-[0.78rem] text-texto-fraco">{ajuda}</span>}
    </label>
  );
}

function Envio({ titulo, descricao, aceita, icone, obrigatorio, arquivos, aoMudar }: {
  titulo: string; descricao: string; aceita: string; icone: string; obrigatorio?: boolean;
  arquivos: File[]; aoMudar: (fs: File[]) => void;
}) {
  const input = useRef<HTMLInputElement>(null);
  const [sobre, setSobre] = useState(false);
  const total = arquivos.reduce((s, f) => s + f.size, 0);
  return (
    <div
      onDragOver={(e) => {
        e.preventDefault();
        setSobre(true);
      }}
      onDragLeave={() => setSobre(false)}
      onDrop={(e) => {
        e.preventDefault();
        setSobre(false);
        aoMudar(Array.from(e.dataTransfer.files));
      }}
      className={cn(
        "flex flex-wrap items-center gap-4 rounded-card border-2 border-dashed p-4 transition-colors",
        sobre ? "border-acao bg-acao-suave" : arquivos.length ? "border-sucesso/60 bg-sucesso-suave/40" : "border-borda-campo",
      )}
    >
      <span className="grid h-11 w-11 shrink-0 place-items-center rounded-pi bg-superficie-alt text-acao-texto">
        <Icone nome={icone} tamanho={24} />
      </span>
      <div className="min-w-0 flex-1">
        <p className="font-semibold text-navy">
          {titulo} {obrigatorio && <span className="text-erro-texto">*</span>}
        </p>
        <p className="text-[0.84rem] text-texto-fraco">{descricao}</p>
        {arquivos.length > 0 && (
          <p className="mt-1 text-[0.84rem] font-medium text-sucesso-texto">
            {arquivos.length} arquivo{arquivos.length > 1 ? "s" : ""} · {tamanhoLegivel(total)}
          </p>
        )}
      </div>
      <input ref={input} type="file" multiple accept={aceita} className="sr-only" onChange={(e) => aoMudar(Array.from(e.target.files ?? []))} />
      <Botao variante="secundario" icone="folder_open" onClick={() => input.current?.click()}>
        Escolher arquivos
      </Botao>
    </div>
  );
}

function Conferencia({ resultados, total, conferindo }: { resultados: ResultadoImagem[]; total: number; conferindo: boolean }) {
  const sem2x1 = resultados.filter((r) => r.equirretangular === false || r.erro);
  const semGps = resultados.filter((r) => r.temGps === false);
  return (
    <div className="rounded-card border border-borda bg-superficie-alt p-4">
      <p className="flex items-center gap-2 font-semibold text-navy">
        <Icone nome={conferindo ? "progress_activity" : "fact_check"} className={conferindo ? "animate-spin" : undefined} />
        Conferência das imagens {conferindo && <span className="font-normal text-texto-fraco">({resultados.length} de {total})</span>}
      </p>
      <ul className="mt-2 space-y-1 text-[0.88rem]">
        <Checagem ok={sem2x1.length === 0} texto={sem2x1.length ? `${sem2x1.length} imagem(ns) fora do formato 360° (2:1)` : "Todas no formato 360° equirretangular (2:1)"} />
        <Checagem ok={semGps.length === 0} texto={semGps.length ? `${semGps.length} imagem(ns) sem GPS no EXIF: vão precisar da trajetória` : "Todas com posição GPS gravada"} />
      </ul>
      {(sem2x1.length > 0 || semGps.length > 0) && (
        <details className="mt-2 text-[0.82rem] text-texto-fraco">
          <summary className="cursor-pointer font-medium text-acao-texto">Ver arquivos com problema</summary>
          <ul className="mt-1 max-h-40 overflow-y-auto">
            {[...new Set([...sem2x1, ...semGps])].map((r) => (
              <li key={r.nome}>
                {r.nome} — {r.erro ?? (r.largura ? `${r.largura}×${r.altura}` : "")}
                {r.temGps === false ? " · sem GPS" : ""}
              </li>
            ))}
          </ul>
        </details>
      )}
    </div>
  );
}

function Checagem({ ok, texto }: { ok: boolean; texto: string }) {
  return (
    <li className={cn("flex items-center gap-2", ok ? "text-sucesso-texto" : "text-atencao-texto")}>
      <Icone nome={ok ? "check_circle" : "warning"} tamanho={18} cheio /> {texto}
    </li>
  );
}

function Resumo({ dados, panoramas, trajetoria, cadastro, conferidas }: {
  dados: Dados; panoramas: File[]; trajetoria: File[]; cadastro: File[]; conferidas: ResultadoImagem[];
}) {
  const total = [...panoramas, ...trajetoria, ...cadastro].reduce((s, f) => s + f.size, 0);
  const minutos = Math.ceil((panoramas.length * SEG_POR_PANORAMA) / 60);
  const problemas = conferidas.filter((r) => r.equirretangular === false || r.temGps === false || r.erro).length;
  const etapas = [
    { icone: "cloud_upload", t: "Envio e registro", d: "Arquivos imutáveis no armazenamento, com hash." },
    { icone: "location_on", t: "Posição de cada foto", d: dados.gnss.startsWith("GNSS") ? "Pela trajetória RTK." : "Pelo GPS do EXIF." },
    { icone: "crop_free", t: "Vistas planas", d: "16 vistas por panorama (horizonte e +35°)." },
    { icone: "center_focus_strong", t: "Detecção", d: "Poste, braço e luminária, juntados em ângulos." },
    { icone: "straighten", t: "Altura e posição", d: `Plano do chão, câmera a ${dados.alturaCamera} m.` },
    { icone: "compare_arrows", t: "Confronto com o cadastro", d: cadastro.length ? "Ponto a ponto, por proximidade." : "Sem cadastro: etapa pulada." },
  ];
  return (
    <div className="space-y-5">
      <dl className="grid gap-x-6 gap-y-2 text-[0.9rem] sm:grid-cols-2">
        <Item rotulo="Inspeção" valor={dados.nome} />
        <Item rotulo="Município" valor={dados.municipio} />
        <Item rotulo="Projeto" valor={dados.projeto || "—"} />
        <Item rotulo="Equipamento" valor={`${dados.camera} · ${dados.montagem} · ${dados.alturaCamera} m`} />
        <Item rotulo="Arquivos" valor={`${panoramas.length} panoramas, ${trajetoria.length} trajetória, ${cadastro.length} cadastro · ${tamanhoLegivel(total)}`} />
        <Item rotulo="Tempo estimado" valor={`~${minutos} min de processamento`} />
      </dl>
      {problemas > 0 && (
        <p className="flex items-center gap-2 rounded-pi bg-atencao-suave px-3 py-2 text-[0.88rem] text-atencao-texto">
          <Icone nome="warning" tamanho={18} cheio /> {problemas} imagem(ns) com pendência na conferência. Dá para seguir; elas ficam marcadas.
        </p>
      )}
      <div>
        <p className="rotulo-secao mb-2">O que acontece depois do envio</p>
        <ol className="grid gap-2 sm:grid-cols-2">
          {etapas.map((e) => (
            <li key={e.t} className="flex gap-3 rounded-pi border border-borda p-3">
              <Icone nome={e.icone} className="text-acao-texto" />
              <span>
                <span className="block text-[0.88rem] font-semibold text-navy">{e.t}</span>
                <span className="block text-[0.8rem] text-texto-fraco">{e.d}</span>
              </span>
            </li>
          ))}
        </ol>
      </div>
      <p className="flex flex-wrap items-center gap-2 text-[0.84rem] text-texto-fraco">
        <Selo tom="atencao" icone="construction">Em desenvolvimento</Selo>
        O envio ao servidor entra junto com a API de ingestão. Enquanto isso, veja o resultado do processamento em
        <Link href="/inspecao/panoramax-br-v0" className="font-semibold text-acao-texto hover:underline">uma inspeção de exemplo</Link>.
      </p>
    </div>
  );
}

function Item({ rotulo, valor }: { rotulo: string; valor: string }) {
  return (
    <div>
      <dt className="text-[0.78rem] text-texto-fraco">{rotulo}</dt>
      <dd className="font-medium text-texto">{valor}</dd>
    </div>
  );
}
