// Cópia de @apphouer/ui (HouerIgnis, packages/ui). Na integração ao Ignis, importar do pacote.
// Gerado por scripts/tokens_web.py a partir de tema/tokens.py — não editar à mão.
import type { Config } from "tailwindcss";

/**
 * Cores só por papel, lidas das variáveis de `src/tokens.css`.
 * `rgb(var(--pi-x-rgb) / <alpha-value>)` deixa usar opacidade: `bg-acao/10`.
 */
const preset = {
  darkMode: ["selector", '[data-tema="escuro"]'],
  theme: {
    extend: {
      colors: {
    "navy": "rgb(var(--pi-navy-rgb) / <alpha-value>)",
    "teal": "rgb(var(--pi-teal-rgb) / <alpha-value>)",
    "acao": "rgb(var(--pi-acao-rgb) / <alpha-value>)",
    "acao-hover": "rgb(var(--pi-acao-hover-rgb) / <alpha-value>)",
    "acao-suave": "rgb(var(--pi-acao-suave-rgb) / <alpha-value>)",
    "texto": "rgb(var(--pi-texto-rgb) / <alpha-value>)",
    "texto-fraco": "rgb(var(--pi-texto-fraco-rgb) / <alpha-value>)",
    "texto-suave": "rgb(var(--pi-texto-suave-rgb) / <alpha-value>)",
    "fundo": "rgb(var(--pi-fundo-rgb) / <alpha-value>)",
    "superficie": "rgb(var(--pi-superficie-rgb) / <alpha-value>)",
    "superficie-alt": "rgb(var(--pi-superficie-alt-rgb) / <alpha-value>)",
    "borda": "rgb(var(--pi-borda-rgb) / <alpha-value>)",
    "borda-campo": "rgb(var(--pi-borda-campo-rgb) / <alpha-value>)",
    "borda-forte": "rgb(var(--pi-borda-forte-rgb) / <alpha-value>)",
    "sucesso": "rgb(var(--pi-sucesso-rgb) / <alpha-value>)",
    "sucesso-suave": "rgb(var(--pi-sucesso-suave-rgb) / <alpha-value>)",
    "atencao": "rgb(var(--pi-atencao-rgb) / <alpha-value>)",
    "atencao-suave": "rgb(var(--pi-atencao-suave-rgb) / <alpha-value>)",
    "erro": "rgb(var(--pi-erro-rgb) / <alpha-value>)",
    "erro-suave": "rgb(var(--pi-erro-suave-rgb) / <alpha-value>)",
    "destaque": "rgb(var(--pi-destaque-rgb) / <alpha-value>)",
    "acao-texto": "rgb(var(--pi-acao-texto-rgb) / <alpha-value>)",
    "sobre-acao": "rgb(var(--pi-sobre-acao-rgb) / <alpha-value>)",
    "navy-fixo": "rgb(var(--pi-navy-fixo-rgb) / <alpha-value>)",
    "sucesso-texto": "rgb(var(--pi-sucesso-texto-rgb) / <alpha-value>)",
    "atencao-texto": "rgb(var(--pi-atencao-texto-rgb) / <alpha-value>)",
    "erro-texto": "rgb(var(--pi-erro-texto-rgb) / <alpha-value>)",
    "acao-fundo": "rgb(var(--pi-acao-fundo-rgb) / <alpha-value>)",
    "acao-fundo-hover": "rgb(var(--pi-acao-fundo-hover-rgb) / <alpha-value>)",
      },
      fontFamily: { sans: ["var(--pi-fonte)"], display: ["var(--pi-fonte-display)"] },
      borderRadius: { pi: "var(--pi-raio)", card: "var(--pi-raio-card)", chip: "var(--pi-raio-chip)" },
      boxShadow: { card: "var(--pi-sombra-card)", botao: "var(--pi-sombra-botao)" },
      height: { botao: "var(--pi-altura-botao)" },
      minHeight: { botao: "var(--pi-altura-botao)" },
      keyframes: {
        "entra-baixo": { from: { opacity: "0", transform: "translateY(6px)" }, to: { opacity: "1", transform: "none" } },
        pulso: { "0%,100%": { opacity: "1" }, "50%": { opacity: ".45" } },
      },
      animation: { "entra-baixo": "entra-baixo .18s ease-out", pulso: "pulso 1.4s ease-in-out infinite" },
    },
  },
} satisfies Partial<Config>;

export default preset;
