"use client";

import { useCallback, useMemo, useSyncExternalStore } from "react";
import type { Captura, CampoVia, Revisao } from "./tipos";

/**
 * Revisão humana: decisões sobre detecções (confirmar ou rejeitar) e correções do corte
 * transversal (larguras).
 *
 * Provisório: fica no navegador de quem revisa. Quando a API existir, cada gravação vira
 * um POST e passa a ser rótulo de treino. Por isso há `exportar()`: o JSON baixado já tem
 * o formato que a API vai receber.
 */

/** Corte transversal corrigido por quem revisa (distâncias laterais ao eixo do carro, m). */
export interface CorrecaoLargura {
  meioFioEsquerdaM: number | null;
  meioFioDireitaM: number | null;
  passeioEsquerdaM: number | null;
  passeioDireitaM: number | null;
  canteiroM: number | null;
  pista2M: number | null;
  revisadoEm: string;
}

// ---------------------------------------------------------------- armazenamento genérico
function criarArmazem<T>(prefixo: string) {
  const ouvintes = new Set<() => void>();
  const cache = new Map<string, Record<string, T>>();
  const VAZIO: Record<string, T> = {};
  const chave = (campanha: string) => `${prefixo}-${campanha}`;
  const ler = (campanha: string): Record<string, T> => {
    const c = cache.get(campanha);
    if (c) return c;
    let m: Record<string, T> = {};
    try {
      m = JSON.parse(localStorage.getItem(chave(campanha)) ?? "{}") as Record<string, T>;
    } catch {
      m = {};
    }
    cache.set(campanha, m);
    return m;
  };
  const gravar = (campanha: string, m: Record<string, T>) => {
    cache.set(campanha, m);
    try {
      localStorage.setItem(chave(campanha), JSON.stringify(m));
    } catch {
      /* navegação privada: vale só nesta aba */
    }
    ouvintes.forEach((f) => f());
  };
  const assinar = (f: () => void) => {
    ouvintes.add(f);
    return () => ouvintes.delete(f);
  };
  const usar = (campanha: string) => {
    const mapa = useSyncExternalStore(assinar, () => ler(campanha), () => VAZIO);
    const definir = useCallback(
      (id: string, v: T | null) => {
        const novo = { ...ler(campanha) };
        if (v == null) delete novo[id];
        else novo[id] = v;
        gravar(campanha, novo);
      },
      [campanha],
    );
    return { mapa, definir };
  };
  return { usar, ler };
}

const decisoes = criarArmazem<Revisao>("ipsurvey-revisao");
const larguras = criarArmazem<CorrecaoLargura>("ipsurvey-larguras");

function baixarJson(nome: string, dados: unknown) {
  const blob = new Blob([JSON.stringify(dados, null, 2)], { type: "application/json" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = nome;
  a.click();
  URL.revokeObjectURL(a.href);
}

export function useRevisoes(campanha: string) {
  const { mapa, definir } = decisoes.usar(campanha);
  const exportar = useCallback(() => {
    baixarJson(`revisoes-${campanha}.json`, {
      campanha,
      exportadoEm: new Date().toISOString(),
      revisoes: decisoes.ler(campanha),
      larguras: larguras.ler(campanha),
    });
  }, [campanha]);
  return { mapa, decidir: definir, exportar };
}

export function useCorrecoesLargura(campanha: string) {
  const { mapa, definir } = larguras.usar(campanha);
  return { correcoes: mapa, corrigir: definir };
}

// ---------------------------------------------------------------- aplicação nos campos
const R1 = (x: number | null) => (x == null ? null : Math.round(x * 10) / 10);

/**
 * Campos da captura com a correção de largura aplicada: o valor revisado vira o usado
 * (fonte "revisao") e o valor medido continua como candidato, para ver quanto mudou.
 */
export function aplicarCorrecao(c: Captura, cor: CorrecaoLargura | undefined): Captura {
  if (!cor) return c;
  const L = cor.meioFioEsquerdaM;
  const R = cor.meioFioDireitaM;
  const novos: Record<string, number | null> = {
    T: L != null && R != null ? R1(L + R) : null,
    S: R1(cor.passeioEsquerdaM),
    X: R1(cor.passeioDireitaM),
    Y: R1(cor.canteiroM),
    W: R1(cor.pista2M),
  };
  const campos: CampoVia[] = c.via.campos.map((f) => {
    if (!(f.coluna in novos)) return f;
    const v = novos[f.coluna];
    if (v == null) return f.fonte === "imagem" ? { ...f, valor: null, estado: "pendente", fonte: null, metodo: "Removido na revisão" } : f;
    return {
      ...f,
      valor: v,
      unidade: "m",
      estado: "estimado",
      fonte: "revisao",
      metodo: `Corrigido na revisão em ${new Date(cor.revisadoEm).toLocaleDateString("pt-BR")}`,
      divergente: false,
      candidatos: [{ fonte: "revisao", valor: v, detalhe: "Corrigido por quem revisou" }, ...f.candidatos.filter((x) => x.fonte !== "revisao")],
    };
  });
  return {
    ...c,
    via: {
      ...c.via,
      campos,
      corte: {
        meioFioEsquerdaM: L,
        meioFioDireitaM: R,
        passeioEsquerdaM: cor.passeioEsquerdaM,
        passeioDireitaM: cor.passeioDireitaM,
        canteiroM: cor.canteiroM,
        canteiroLado: c.via.corte?.canteiroLado ?? (cor.canteiroM ? "esquerda" : null),
        pista2M: cor.pista2M,
        fatias: c.via.corte?.fatias ?? 0,
        fatiasTotal: c.via.corte?.fatiasTotal ?? 0,
        anisotropiaEixo: c.via.corte?.anisotropiaEixo ?? null,
      },
    },
  };
}

/** Capturas com as correções de largura aplicadas (para tabela, indicadores e relatório). */
export function useCapturasRevisadas(campanha: string, capturas: Captura[]): Captura[] {
  const { correcoes } = useCorrecoesLargura(campanha);
  return useMemo(() => capturas.map((c) => aplicarCorrecao(c, correcoes[c.id])), [capturas, correcoes]);
}
