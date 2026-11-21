import type { Captura, Classe, Deteccao } from "./tipos";

/**
 * Converte ângulos do panorama para pixels da imagem equirretangular (mesma convenção de
 * `ipsurvey.domain.geometry.equirect`): u = (az + π) / 2π · L, v = (π/2 − el) / π · A.
 */
export function anguloParaPixel(az: number, el: number, largura: number, altura: number): [number, number] {
  const azN = ((((az + Math.PI) % (2 * Math.PI)) + 2 * Math.PI) % (2 * Math.PI)) - Math.PI;
  return [((azN + Math.PI) / (2 * Math.PI)) * largura, ((Math.PI / 2 - el) / Math.PI) * altura];
}

export interface Retangulo { x: number; y: number; w: number; h: number }

/**
 * Retângulos (em pixels) de uma detecção no panorama. Dois quando a caixa atravessa a
 * costura de ±180°.
 */
export function retangulosDaDeteccao(d: Deteccao, largura: number, altura: number): Retangulo[] {
  const [u0, v0] = anguloParaPixel(d.az - d.azMeia, d.elMax, largura, altura);
  const [u1, v1] = anguloParaPixel(d.az + d.azMeia, d.elMin, largura, altura);
  const h = Math.max(v1 - v0, 1);
  const minW = 2;
  if (u1 >= u0) return [{ x: u0, y: v0, w: Math.max(u1 - u0, minW), h }];
  return [
    { x: u0, y: v0, w: Math.max(largura - u0, minW), h },
    { x: 0, y: v0, w: Math.max(u1, minW), h },
  ];
}

/** Rumo (graus a partir do norte) para onde a detecção aponta. */
export function rumoDaDeteccao(c: Captura, d: Deteccao): number {
  return (((c.rumo + (d.az * 180) / Math.PI) % 360) + 360) % 360;
}

export function contarPorClasse(deteccoes: Deteccao[]): Record<Classe, number> {
  const n: Record<Classe, number> = { poste: 0, braco: 0, luminaria: 0 };
  for (const d of deteccoes) n[d.classe] += 1;
  return n;
}

/** Histograma de alturas em faixas de `passo` metros (só alturas completas). */
export function histogramaAlturas(alturas: number[], passo = 2, max = 16): { faixa: string; n: number }[] {
  const faixas: { faixa: string; n: number }[] = [];
  for (let a = 4; a < max; a += passo) faixas.push({ faixa: `${a}–${a + passo}`, n: 0 });
  faixas.push({ faixa: `≥ ${max}`, n: 0 });
  for (const h of alturas) {
    const i = h >= max ? faixas.length - 1 : Math.max(0, Math.floor((h - 4) / passo));
    const f = faixas[i];
    if (f) f.n += 1;
  }
  return faixas;
}

export function mediana(xs: number[]): number | null {
  if (!xs.length) return null;
  const s = [...xs].sort((a, b) => a - b);
  const m = Math.floor(s.length / 2);
  return s.length % 2 ? (s[m] ?? null) : ((s[m - 1] ?? 0) + (s[m] ?? 0)) / 2;
}

export const fmt = {
  n: (x: number) => x.toLocaleString("pt-BR"),
  m: (x: number | null, casas = 1) => (x == null ? "—" : `${x.toLocaleString("pt-BR", { maximumFractionDigits: casas, minimumFractionDigits: casas })} m`),
  pct: (x: number) => `${(x * 100).toLocaleString("pt-BR", { maximumFractionDigits: 0 })}%`,
  score: (x: number) => x.toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 }),
  data: (iso: string) => new Date(`${iso.slice(0, 10)}T12:00:00`).toLocaleDateString("pt-BR"),
};
