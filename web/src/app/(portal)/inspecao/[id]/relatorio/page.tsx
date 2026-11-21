"use client";

import { useParams } from "next/navigation";
import type { ReactNode } from "react";
import { CabecalhoCampanha, ComCampanha } from "@/componentes/Campanha";
import { contarPorClasse, fmt, histogramaAlturas, mediana } from "@/dados/geometria";
import { useRevisoes } from "@/dados/revisao";
import { CLASSES, type Campanha, type Classe } from "@/dados/tipos";
import { TabelaVias } from "@/componentes/TabelaVias";
import { Botao } from "@/ui/Botao";

export default function PaginaRelatorio() {
  const { id } = useParams<{ id: string }>();
  return <ComCampanha id={decodeURIComponent(id)}>{(c) => <Relatorio campanha={c} />}</ComCampanha>;
}

function Relatorio({ campanha }: { campanha: Campanha }) {
  const { mapa: revisoes } = useRevisoes(campanha.id);
  const todas = campanha.capturas.flatMap((c) => c.deteccoes);
  const n = contarPorClasse(todas);
  const postes = campanha.capturas.flatMap((c) =>
    c.deteccoes.filter((d) => d.classe === "poste" && revisoes[d.id] !== "rejeitada").map((d) => ({ c, d })),
  );
  const alturas = postes.filter(({ d }) => d.alturaM != null && !d.alturaMinima).map(({ d }) => d.alturaM as number);
  const hist = histogramaAlturas(alturas);
  const maxHist = Math.max(1, ...hist.map((h) => h.n));
  const revisadas = todas.filter((d) => revisoes[d.id]).length;
  const rejeitadas = todas.filter((d) => revisoes[d.id] === "rejeitada").length;
  const cidades = [...new Set(campanha.capturas.map((c) => c.cidade))].sort();
  const datas = campanha.capturas.map((c) => c.data).sort();
  const autores = [...new Set(campanha.capturas.map((c) => c.autor))];
  const p = campanha.parametros;

  const baixarCsv = () => {
    const linhas = [
      ["id", "captura", "cidade", "latitude", "longitude", "altura_m", "altura_e_minimo", "distancia_m", "confianca", "revisao"].join(";"),
      ...postes.map(({ c, d }) =>
        [d.id, c.id, c.cidade, d.lat ?? "", d.lon ?? "", d.alturaM ?? "", d.alturaMinima ? "sim" : "nao", d.distanciaM ?? "", d.score, revisoes[d.id] ?? "pendente"]
          .map(String)
          .map((s) => s.replace(".", ","))
          .join(";"),
      ),
    ];
    const blob = new Blob(["﻿" + linhas.join("\n")], { type: "text/csv;charset=utf-8" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `postes-${campanha.id}.csv`;
    a.click();
    URL.revokeObjectURL(a.href);
  };

  return (
    <>
      <div className="print:hidden">
        <CabecalhoCampanha
          campanha={campanha}
          acoes={
            <>
              <Botao variante="download" onClick={baixarCsv}>Postes (.csv)</Botao>
              <Botao variante="download" disabled title="Gerada pelo exportador Python; entra com a API">Planilha de inspeção (.xlsx)</Botao>
              <Botao variante="primario" icone="print" onClick={() => window.print()}>Imprimir ou salvar PDF</Botao>
            </>
          }
        />
      </div>
      <article className="mx-auto my-6 max-w-[210mm] bg-superficie p-10 shadow-card print:my-0 print:max-w-none print:p-0 print:shadow-none">
        <header className="border-b-2 border-navy pb-4">
          <p className="rotulo-secao">Relatório de inspeção de campo · iluminação pública</p>
          <h1 className="mt-1 text-[1.6rem] font-semibold text-navy">{campanha.nome}</h1>
          <p className="mt-1 text-[0.9rem] text-texto-fraco">
            {campanha.municipio} · levantamento de {fmt.data(datas[0] ?? campanha.criadaEm)} a {fmt.data(datas.at(-1) ?? campanha.criadaEm)} · emitido em{" "}
            {new Date().toLocaleDateString("pt-BR")}
          </p>
          {revisadas < todas.length && (
            <p className="mt-3 rounded-pi bg-atencao-suave px-3 py-2 text-[0.84rem] text-atencao-texto">
              Relatório preliminar: {fmt.n(todas.length - revisadas)} de {fmt.n(todas.length)} detecções ainda não foram revisadas. Os números abaixo
              incluem as pendentes e excluem só as rejeitadas.
            </p>
          )}
        </header>

        <Secao n={1} titulo="Resumo">
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <Numero rotulo="Panoramas analisados" valor={fmt.n(campanha.capturas.length)} />
            <Numero rotulo="Postes levantados" valor={fmt.n(postes.length)} />
            <Numero rotulo="Altura mediana" valor={fmt.m(mediana(alturas))} />
            <Numero rotulo="Detecções revisadas" valor={todas.length ? fmt.pct(revisadas / todas.length) : "—"} />
          </div>
          <p className="mt-3 text-[0.9rem]">
            Foram analisados {fmt.n(campanha.capturas.length)} panoramas 360° em {cidades.length} cidade(s). O detector encontrou {fmt.n(n.poste)} postes,{" "}
            {fmt.n(n.braco)} braços e {fmt.n(n.luminaria)} luminárias. Na revisão, {fmt.n(rejeitadas)} detecções foram rejeitadas.
          </p>
        </Secao>

        <Secao n={2} titulo="Distribuição das alturas dos postes">
          <p className="mb-3 text-[0.84rem] text-texto-fraco">
            {fmt.n(alturas.length)} postes com pé e topo visíveis. Os demais não têm altura estimada nesta versão.
          </p>
          <div className="flex h-40 items-end gap-2" role="img" aria-label="Histograma das alturas dos postes">
            {hist.map((h) => (
              <div key={h.faixa} className="flex flex-1 flex-col items-center gap-1">
                <span className="text-[0.75rem] font-semibold num">{h.n}</span>
                <div className="w-full rounded-t bg-teal print:bg-[#E8A24D]" style={{ height: `${(100 * h.n) / maxHist}%`, minHeight: h.n ? 2 : 0 }} />
                <span className="text-[0.72rem] text-texto-fraco">{h.faixa} m</span>
              </div>
            ))}
          </div>
        </Secao>

        <Secao n={3} titulo="Resultados por cidade">
          <table className="w-full text-[0.86rem]">
            <thead>
              <tr className="border-b border-borda-forte text-left text-[0.78rem] text-texto-fraco">
                <th className="py-1.5 font-medium">Cidade</th>
                <th className="py-1.5 text-right font-medium">Panoramas</th>
                {(Object.keys(CLASSES) as Classe[]).map((k) => <th key={k} className="py-1.5 text-right font-medium">{CLASSES[k].plural}</th>)}
                <th className="py-1.5 text-right font-medium">Altura mediana</th>
              </tr>
            </thead>
            <tbody>
              {cidades.map((cid) => {
                const cs = campanha.capturas.filter((c) => c.cidade === cid);
                const ds = cs.flatMap((c) => c.deteccoes).filter((d) => revisoes[d.id] !== "rejeitada");
                const k = contarPorClasse(ds);
                const hs = ds.filter((d) => d.classe === "poste" && d.alturaM != null && !d.alturaMinima).map((d) => d.alturaM as number);
                return (
                  <tr key={cid} className="border-b border-borda">
                    <td className="py-1.5">{cid}</td>
                    <td className="py-1.5 text-right num">{cs.length}</td>
                    {(Object.keys(CLASSES) as Classe[]).map((c) => <td key={c} className="py-1.5 text-right num">{k[c]}</td>)}
                    <td className="py-1.5 text-right num">{fmt.m(mediana(hs))}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </Secao>

        <Secao n={4} titulo="Medidas de via e malha para a simulação" quebra>
          <p className="mb-3 text-[0.86rem] text-texto-fraco">
            Campos de levantamento da planilha de simulação, por captura. Cada valor vem da fonte que mede melhor o campo: a imagem 360° para altura e
            braço, o cadastro {campanha.fontesCadastro ? `(${campanha.fontesCadastro})` : ""} para vão, posteação e lâmpadas por ponto, e o mapa
            (OpenStreetMap) para faixas e logradouro. Larguras ainda pendentes.
          </p>
          <TabelaVias capturas={campanha.capturas} impressao />
        </Secao>

        <Secao n={5} titulo="Método">
          <ul className="list-disc space-y-1.5 pl-5 text-[0.88rem]">
            <li>Cada panorama é fatiado em 16 vistas planas (8 direções, no horizonte e inclinadas 35° para cima), para o detector não sofrer com a distorção da imagem 360°.</li>
            <li>
              Detector: {campanha.modelo}, procurando por descrição em texto. Limiares de confiança: poste {p.limiares.poste}, braço {p.limiares.braco}, luminária{" "}
              {p.limiares.luminaria}.
            </li>
            <li>As detecções de cada vista voltam para ângulos do panorama e são juntadas. Um poste alto, visto em pedaços por duas vistas, vira um só.</li>
            <li>
              Altura e distância saem do plano do chão, com a câmera a {p.alturaCameraM} m. Postes com menos de {p.alturaMinimaPosteM} m são descartados, porque
              costumam ser placas e hastes.
            </li>
            <li>A posição no mapa combina a posição da foto, o rumo da câmera, o ângulo da detecção e a distância estimada.</li>
            <li>
              Vão e posteação pelo cadastro: cada poste é projetado no eixo da via do mapa; a posição ao longo do eixo dá os vãos de cada lado
              (mediana) e o lado dá a posteação.
            </li>
          </ul>
        </Secao>

        <Secao n={6} titulo="Limitações">
          <ul className="list-disc space-y-1.5 pl-5 text-[0.88rem]">
            <li>A estimativa é de um quadro só. Erra em rua com rampa, com meio-fio alto ou quando o pé do poste está atrás de um veículo. A triangulação entre quadros consecutivos vai substituí-la.</li>
            <li>A posição herda o erro do GPS da câmera, de alguns metros. Com GNSS RTK, cai para decímetros.</li>
            <li>Braços e luminárias pequenas e distantes passam despercebidos com frequência. O detector ainda não foi treinado com postes brasileiros.</li>
            <li>
              O casamento poste a poste entre a foto e o cadastro ainda não supera o acaso: os erros somados (GPS da câmera, estimativa de um quadro
              e coordenada esquemática da BDGD) passam do espaçamento entre postes. A comparação é feita por via, não por poste.
            </li>
            <li>Larguras de pista, passeio e canteiro ainda não são medidas: o mapa não as tem, e a medição por satélite e imagem é a próxima etapa.</li>
          </ul>
        </Secao>

        <Secao n={7} titulo="Postes levantados" quebra>
          <table className="w-full text-[0.78rem]">
            <thead>
              <tr className="border-b border-borda-forte text-left text-texto-fraco">
                <th className="py-1 font-medium">Id</th>
                <th className="py-1 font-medium">Cidade</th>
                <th className="py-1 text-right font-medium">Latitude</th>
                <th className="py-1 text-right font-medium">Longitude</th>
                <th className="py-1 text-right font-medium">Altura</th>
                <th className="py-1 text-right font-medium">Distância</th>
                <th className="py-1 text-right font-medium">Confiança</th>
                <th className="py-1 font-medium">Revisão</th>
              </tr>
            </thead>
            <tbody>
              {postes.map(({ c, d }) => (
                <tr key={d.id} className="border-b border-borda/70 [break-inside:avoid]">
                  <td className="py-0.5 font-mono">{d.id}</td>
                  <td className="py-0.5">{c.cidade}</td>
                  <td className="py-0.5 text-right num">{d.lat?.toFixed(6) ?? "—"}</td>
                  <td className="py-0.5 text-right num">{d.lon?.toFixed(6) ?? "—"}</td>
                  <td className="py-0.5 text-right num">{d.alturaM != null ? `${d.alturaMinima ? "≥ " : ""}${fmt.m(d.alturaM)}` : "—"}</td>
                  <td className="py-0.5 text-right num">{fmt.m(d.distanciaM, 0)}</td>
                  <td className="py-0.5 text-right num">{fmt.score(d.score)}</td>
                  <td className="py-0.5">{revisoes[d.id] === "confirmada" ? "confirmada" : "pendente"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Secao>

        <footer className="mt-8 border-t border-borda pt-3 text-[0.75rem] text-texto-fraco">
          Imagens: {campanha.licenca}. Autores: {autores.join(", ")}. Fonte: {campanha.fonte}.
        </footer>
      </article>
    </>
  );
}

function Secao({ n, titulo, quebra, children }: { n: number; titulo: string; quebra?: boolean; children: ReactNode }) {
  return (
    <section className={quebra ? "mt-8 print:break-before-page" : "mt-8 [break-inside:avoid]"}>
      <h2 className="mb-3 text-[1.1rem] font-semibold text-navy">
        <span className="mr-2 text-teal num">{n}.</span>
        {titulo}
      </h2>
      {children}
    </section>
  );
}

function Numero({ rotulo, valor }: { rotulo: string; valor: string }) {
  return (
    <div className="rounded-pi border border-borda p-3">
      <p className="text-[0.75rem] text-texto-fraco">{rotulo}</p>
      <p className="text-[1.25rem] font-semibold text-navy num">{valor}</p>
    </div>
  );
}
