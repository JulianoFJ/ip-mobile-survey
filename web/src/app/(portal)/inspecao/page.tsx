"use client";

import Link from "next/link";
import { Cabecalho } from "@/componentes/Casca";
import { Carregando, EstadoVazio } from "@/componentes/Campanha";
import { useCampanhas } from "@/dados/api";
import { fmt } from "@/dados/geometria";
import { STATUS } from "@/dados/tipos";
import { Botao } from "@/ui/Botao";
import { Icone } from "@/ui/Icone";
import { Selo } from "@/ui/Selo";

export default function Inspecoes() {
  const q = useCampanhas();
  const novaInspecao = (
    <Botao asChild variante="primario">
      <Link href="/inspecao/nova">
        <Icone nome="add_a_photo" tamanho={18} /> Nova inspeção
      </Link>
    </Botao>
  );
  return (
    <>
      <Cabecalho
        titulo="Inspeção de campo"
        descricao="Envie as imagens 360° do levantamento, acompanhe o processamento, revise as estruturas detectadas no mapa e gere o relatório e a planilha de inspeção."
        acoes={novaInspecao}
      />
      <div className="mx-auto max-w-6xl space-y-6 p-6">
        <Fluxo />
        <section aria-labelledby="t-lista">
          <h2 id="t-lista" className="rotulo-secao mb-2">Inspeções</h2>
          {q.isPending && <Carregando />}
          {q.isError && (
            <EstadoVazio icone="photo_camera" titulo="Nenhuma inspeção ainda" descricao="Comece enviando as imagens de um levantamento." acao={novaInspecao} />
          )}
          {q.data && (
            <ul className="grid gap-3">
              {q.data.map((c) => {
                const st = STATUS[c.status];
                return (
                  <li key={c.id}>
                    <Link href={`/inspecao/${encodeURIComponent(c.id)}`} className="cartao group flex flex-wrap items-center gap-x-6 gap-y-3 p-4 transition-colors hover:border-acao">
                      <span className="grid h-11 w-11 shrink-0 place-items-center rounded-pi bg-acao-suave text-acao-texto">
                        <Icone nome="panorama_photosphere" tamanho={24} />
                      </span>
                      <span className="min-w-0 flex-1">
                        <span className="flex flex-wrap items-center gap-2">
                          <span className="font-semibold text-navy group-hover:text-acao-texto">{c.nome}</span>
                          <Selo tom={st.tom} icone={st.icone}>{st.rotulo}</Selo>
                        </span>
                        <span className="mt-0.5 block text-[0.85rem] text-texto-fraco">
                          {c.municipio} · criada em {fmt.data(c.criadaEm)} · {c.modelo}
                        </span>
                      </span>
                      <Numero rotulo="Panoramas" valor={c.capturas} />
                      <Numero rotulo="Postes detectados" valor={c.postes} />
                      <Icone nome="chevron_right" className="text-texto-suave group-hover:text-acao-texto" />
                    </Link>
                  </li>
                );
              })}
            </ul>
          )}
        </section>
      </div>
    </>
  );
}

function Numero({ rotulo, valor }: { rotulo: string; valor: number }) {
  return (
    <span className="text-right">
      <span className="block text-[1.15rem] font-semibold text-texto num">{fmt.n(valor)}</span>
      <span className="block text-[0.75rem] text-texto-fraco">{rotulo}</span>
    </span>
  );
}

/** As etapas do módulo, para quem chega pela primeira vez. */
function Fluxo() {
  const passos = [
    { icone: "upload", titulo: "Enviar", texto: "Panoramas 360°, trajetória e cadastro do município." },
    { icone: "memory", titulo: "Processar", texto: "Vistas planas, detecção de poste, braço e luminária, altura e posição." },
    { icone: "rule", titulo: "Revisar", texto: "Confirmar ou rejeitar cada estrutura no panorama e no mapa." },
    { icone: "description", titulo: "Entregar", texto: "Relatório, planilha de inspeção e confronto com o cadastro." },
  ];
  return (
    <ol className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
      {passos.map((p, i) => (
        <li key={p.titulo} className="cartao flex gap-3 p-4">
          <span className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-superficie-alt font-semibold text-navy num">{i + 1}</span>
          <span>
            <span className="flex items-center gap-1.5 font-semibold text-navy">
              <Icone nome={p.icone} tamanho={18} className="text-acao-texto" /> {p.titulo}
            </span>
            <span className="mt-0.5 block text-[0.84rem] text-texto-fraco">{p.texto}</span>
          </span>
        </li>
      ))}
    </ol>
  );
}
