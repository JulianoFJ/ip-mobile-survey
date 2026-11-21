import { describe, expect, it } from "vitest";
import { anguloParaPixel, histogramaAlturas, mediana, retangulosDaDeteccao, rumoDaDeteccao } from "./geometria";
import type { Captura, Deteccao } from "./tipos";

const det = (az: number, azMeia: number, elMin = -0.1, elMax = 0.3): Deteccao => ({
  id: "x", classe: "poste", score: 0.5, az, azMeia, elMin, elMax, cortadoBase: false, cortadoTopo: false,
  alturaM: null, alturaMinima: false, distanciaM: null, lat: null, lon: null, planta: null,
});

describe("anguloParaPixel (mesma convenção de ipsurvey.domain.geometry.equirect)", () => {
  it("frente no centro, horizonte no meio", () => {
    expect(anguloParaPixel(0, 0, 2048, 1024)).toEqual([1024, 512]);
  });
  it("direita a +90°, zênite no topo", () => {
    expect(anguloParaPixel(Math.PI / 2, Math.PI / 2, 2048, 1024)).toEqual([1536, 0]);
  });
  it("normaliza azimute fora de [-π, π)", () => {
    const [u] = anguloParaPixel(Math.PI / 2 + 2 * Math.PI, 0, 2048, 1024);
    expect(u).toBeCloseTo(1536);
  });
});

describe("retangulosDaDeteccao", () => {
  it("um retângulo longe da costura", () => {
    const r = retangulosDaDeteccao(det(0, 0.05), 2048, 1024);
    expect(r).toHaveLength(1);
    expect(r[0]!.x).toBeLessThan(1024);
    expect(r[0]!.x + r[0]!.w).toBeGreaterThan(1024);
    expect(r[0]!.h).toBeGreaterThan(0);
  });
  it("dois retângulos quando atravessa ±180°", () => {
    const r = retangulosDaDeteccao(det(Math.PI - 0.01, 0.05), 2048, 1024);
    expect(r).toHaveLength(2);
    expect(r[1]!.x).toBe(0);
  });
});

describe("rumo, histograma, mediana", () => {
  it("rumo soma o rumo da câmera ao azimute", () => {
    const c = { rumo: 350 } as Captura;
    expect(rumoDaDeteccao(c, det(Math.PI / 9, 0.01))).toBeCloseTo(10);
  });
  it("histograma conta todas as alturas", () => {
    const h = histogramaAlturas([4.5, 7, 9.9, 12, 20]);
    expect(h.reduce((s, f) => s + f.n, 0)).toBe(5);
    expect(h.at(-1)!.n).toBe(1);
  });
  it("mediana", () => {
    expect(mediana([])).toBeNull();
    expect(mediana([3, 1, 2])).toBe(2);
    expect(mediana([1, 2, 3, 4])).toBe(2.5);
  });
});
