// Cópia de @apphouer/ui (HouerIgnis, packages/ui). Na integração ao Ignis, importar do pacote.
// Gerado por scripts/tokens_web.py a partir de tema/tokens.py — não editar à mão.

/** Cores por papel em hex, para o que não lê variável CSS (deck.gl, canvas). */
export const COR = {
  "navy": "#1B3664",
  "teal": "#E8A24D",
  "acao": "#A05A16",
  "acao-hover": "#844A10",
  "acao-suave": "#FBF2E6",
  "texto": "#1B2434",
  "texto-fraco": "#5B6579",
  "texto-suave": "#94A3B8",
  "fundo": "#F4F6FA",
  "superficie": "#FFFFFF",
  "superficie-alt": "#F8FAFC",
  "borda": "#E2E8F0",
  "borda-campo": "#CBD5E1",
  "borda-forte": "#94A3B8",
  "sucesso": "#17A672",
  "sucesso-suave": "#E8F7F0",
  "atencao": "#C08420",
  "atencao-suave": "#FFF6E5",
  "erro": "#DC5B52",
  "erro-suave": "#FDECEA",
  "destaque": "#8B5CF6",
  "acao-texto": "#844A10",
  "sobre-acao": "#231504",
  "navy-fixo": "#1B3664",
  "sucesso-texto": "#0F7A53",
  "atencao-texto": "#8A5A0B",
  "erro-texto": "#B42F27",
  "acao-fundo": "#E8A24D",
  "acao-fundo-hover": "#D4913B"
} as const;

export const COR_ESCURO = {
  "navy": "#A9C1EA",
  "teal": "#F0B868",
  "acao": "#E8A24D",
  "acao-hover": "#F0B868",
  "acao-suave": "#2A2012",
  "texto": "#E7EBF3",
  "texto-fraco": "#A7B1C5",
  "texto-suave": "#76829A",
  "fundo": "#0D131E",
  "superficie": "#151C29",
  "superficie-alt": "#1B2333",
  "borda": "#273145",
  "borda-campo": "#36425A",
  "borda-forte": "#55627D",
  "sucesso": "#3CC793",
  "sucesso-suave": "#11291F",
  "atencao": "#E6AA45",
  "atencao-suave": "#2C2212",
  "erro": "#F2837A",
  "erro-suave": "#331A1A",
  "destaque": "#A78BFA",
  "acao-texto": "#F0B868",
  "sobre-acao": "#231504",
  "navy-fixo": "#14294D",
  "sucesso-texto": "#3CC793",
  "atencao-texto": "#E6AA45",
  "erro-texto": "#F2837A",
  "acao-fundo": "#E8A24D",
  "acao-fundo-hover": "#D4913B"
} as const;

export type Papel = keyof typeof COR;

export const SERIES = [
  "#A05A16",
  "#1B3664",
  "#17A672",
  "#F59E0B",
  "#8B5CF6",
  "#94A3B8"
] as const;

export const FORNECEDORES = {
  "LEDSTAR": "#A05A16",
  "SX LIGHTING": "#8B5CF6",
  "TECNOWATT": "#D55181"
} as const;

export const USO_EDIFICACAO = {
  "Residencial": "#A9B8CC",
  "Misto (moradia e comércio)": "#F2C46D",
  "Comércio e serviços": "#F59E0B",
  "Prédio público": "#1B3664",
  "Ensino": "#A05A16",
  "Saúde": "#D55181",
  "Religioso": "#8B5CF6",
  "Em construção": "#2BB3A3",
  "Sem endereço no Censo": "#DDE3EA"
} as const;

export const EQUIPAMENTO = {
  "camera": "#DC2626",
  "wifi": "#0891B2",
  "totem": "#EA580C",
  "ar": "#65A30D",
  "ruido": "#C026D3",
  "meteorologia": "#4F46E5",
  "alagamento": "#0F766E",
  "sirene": "#F43F5E",
  "gateway": "#475569",
  "carregador": "#A16207"
} as const;

export const CAMADA_GEMEO = {
  "poste": "#FACC15",
  "ponto_interesse": "#111827",
  "risco": "#DC5B52",
  "estacao": "#38BDF8",
  "predio": "#1B3664"
} as const;

export const PAISAGEM = {
  "Parque e praça": "#7BC67E",
  "Campo de esporte": "#4CAF7A",
  "Parquinho": "#B5E3A1",
  "Mata": "#2F7D46",
  "Campo e gramado": "#A8D08D",
  "Banhado": "#8FB9A8",
  "Água": "#7FB8E6",
  "Areia e praia": "#F1E2B8",
  "Estacionamento": "#D5D9E0",
  "Quadra residencial": "#EEE8DF",
  "Quadra comercial": "#F3DCD2",
  "Quadra industrial": "#DAD3E8"
} as const;

export const RUA_TIPO = {
  "Rodovia": "#3F4652",
  "Avenida": "#59616E",
  "Coletora": "#767E8B",
  "Rua local": "#959CA8",
  "Acesso e serviço": "#B1B7C1"
} as const;

export const RUA_PISO = {
  "Asfalto": "#4B5563",
  "Paralelepípedo ou bloco": "#A0785A",
  "Terra, cascalho ou areia": "#C9A66B",
  "Não informado": "#A7AEB9"
} as const;

export const LUZ_LAMPADA = {
  "LED": "#E8F1FF",
  "Sódio": "#FFB347",
  "Mercúrio": "#B9D3FF",
  "Metálico": "#FFF1C9",
  "Outra": "#FFE08A"
} as const;

export const LUX_ESCALA = [
  "#1E1B4B",
  "#6D28D9",
  "#C026D3",
  "#F97316",
  "#FACC15",
  "#FEF08A"
] as const;

/** tom → (fundo, texto, borda) de selo/chip, no tema claro. */
export const TOM = {
  "marca": {
    "fundo": "#FBF2E6",
    "texto": "#A05A16",
    "borda": "#E8A24D"
  },
  "sucesso": {
    "fundo": "#E8F7F0",
    "texto": "#17A672",
    "borda": "#17A672"
  },
  "atencao": {
    "fundo": "#FFF6E5",
    "texto": "#C08420",
    "borda": "#F59E0B"
  },
  "erro": {
    "fundo": "#FDECEA",
    "texto": "#DC5B52",
    "borda": "#DC5B52"
  },
  "neutro": {
    "fundo": "#F8FAFC",
    "texto": "#5B6579",
    "borda": "#CBD5E1"
  }
} as const;

export type Tom = keyof typeof TOM;
