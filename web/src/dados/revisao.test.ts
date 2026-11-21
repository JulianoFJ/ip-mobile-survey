import { describe, expect, it } from "vitest";
import { aplicarCorrecao, type CorrecaoLargura } from "./revisao";
import type { Captura, CampoVia } from "./tipos";

const campo = (coluna: string, valor: number | null, fonte: CampoVia["fonte"] = "imagem"): CampoVia => ({
  coluna, rotulo: coluna, valor, unidade: "m", estado: valor == null ? "pendente" : "estimado", fonte,
  metodo: "", divergente: false, candidatos: valor == null || !fonte ? [] : [{ fonte, valor, detalhe: "medido" }],
});

const captura = {
  id: "c1",
  via: {
    corte: null,
    campos: [campo("T", 12.5), campo("S", 7.8), campo("X", 2.4), campo("Y", null, null), campo("AF", 30, "cadastro")],
  },
} as unknown as Captura;

const cor: CorrecaoLargura = {
  meioFioEsquerdaM: 3.2, meioFioDireitaM: 4.1, passeioEsquerdaM: 2.5, passeioDireitaM: null,
  canteiroM: null, pista2M: null, revisadoEm: "2026-11-21T12:00:00Z",
};

describe("aplicarCorrecao", () => {
  it("sem correção devolve a captura como está", () => {
    expect(aplicarCorrecao(captura, undefined)).toBe(captura);
  });
  it("a largura revisada vira a usada e a medida fica como candidata", () => {
    const c = aplicarCorrecao(captura, cor);
    const t = c.via.campos.find((f) => f.coluna === "T")!;
    expect(t.valor).toBe(7.3);
    expect(t.fonte).toBe("revisao");
    expect(t.candidatos.map((x) => x.fonte)).toEqual(["revisao", "imagem"]);
    expect(c.via.campos.find((f) => f.coluna === "S")!.valor).toBe(2.5);
    expect(c.via.corte?.meioFioDireitaM).toBe(4.1);
  });
  it("campo zerado na revisão sai da imagem, mas não mexe no cadastro", () => {
    const c = aplicarCorrecao(captura, cor);
    expect(c.via.campos.find((f) => f.coluna === "X")!.valor).toBeNull();
    expect(c.via.campos.find((f) => f.coluna === "AF")!.valor).toBe(30);
  });
});
