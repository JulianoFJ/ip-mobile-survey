/**
 * Contrato de dados do módulo de inspeção de campo.
 *
 * Hoje vem dos JSON de demonstração gerados por `scripts/export_web_demo.py`; depois, da
 * API FastAPI (`ipsurvey.api`). Ângulos em radianos, no referencial do panorama:
 * azimute 0 no centro da imagem, positivo para a direita; elevação positiva para cima.
 */

export type Classe = "poste" | "braco" | "luminaria";

export type StatusCampanha = "rascunho" | "processando" | "em_revisao" | "concluida";

/** Decisão de quem revisa uma detecção. */
export type Revisao = "confirmada" | "rejeitada";

export interface Deteccao {
  id: string;
  classe: Classe;
  /** Confiança do detector, 0 a 1. */
  score: number;
  az: number;
  azMeia: number;
  elMin: number;
  elMax: number;
  /** O pé (ou o topo) encostava na borda da vista: medida incompleta. */
  cortadoBase: boolean;
  cortadoTopo: boolean;
  /** Estimativa pelo plano do chão (só postes com o pé visível). */
  alturaM: number | null;
  /** A altura é um limite inferior (topo cortado). */
  alturaMinima: boolean;
  distanciaM: number | null;
  /** Posição estimada do poste (rumo da câmera + azimute + distância). */
  lat: number | null;
  lon: number | null;
  /** Posição no chão em relação à câmera (x à direita, y à frente do deslocamento). */
  planta: { x: number; y: number; lado: "esquerda" | "direita" | "centro" } | null;
}

/** Situação de um campo da planilha de simulação. */
export type EstadoCampo = "estimado" | "pendente";

/** De onde veio um valor. */
export type Fonte = "imagem" | "cadastro" | "mapa" | "revisao";

export interface Candidato {
  fonte: Fonte;
  valor: number | string;
  detalhe: string;
}

export interface CampoVia {
  /** Letra da coluna na planilha de simulação (contrato B–AW). */
  coluna: string;
  rotulo: string;
  valor: number | string | null;
  unidade: string;
  estado: EstadoCampo;
  /** Fonte do valor escolhido (a preferida para o campo, entre as disponíveis). */
  fonte: Fonte | null;
  /** Como o valor foi obtido, ou o que falta para obtê-lo. */
  metodo: string;
  /** Duas fontes discordam (mais de 25% ou textos diferentes). */
  divergente: boolean;
  /** Todos os valores propostos, na ordem de preferência. */
  candidatos: Candidato[];
}

/** Poste do cadastro (BDGD) no entorno das capturas. */
export interface PosteCadastro {
  id: string;
  lat: number;
  lon: number;
  luminarias: number;
  tecnologia: string | null;
  potenciaW: number | null;
}

/** Atributos de via e malha estimados num panorama. */
export interface ViaMalha {
  postesNoPlano: number;
  /** Via do mapa em que a câmera está (OSM). */
  logradouro: string | null;
  classeOsm: string | null;
  maoUnica: boolean | null;
  /** Postes do cadastro atribuídos a essa via, e o que o cadastro diz deles. */
  postesCadastroNaVia: number;
  /** Corte transversal medido na segmentação do chão (distâncias laterais ao eixo do carro). */
  corte: {
    meioFioEsquerdaM: number | null;
    meioFioDireitaM: number | null;
    passeioEsquerdaM: number | null;
    passeioDireitaM: number | null;
    canteiroM: number | null;
    canteiroLado: "esquerda" | "direita" | null;
    pista2M: number | null;
    fatias: number;
    fatiasTotal: number;
    anisotropiaEixo: number | null;
  } | null;
  tecnologia: string | null;
  potenciaW: number | null;
  /** Distância lateral entre os alinhamentos de postes (limite superior de passeio + via + passeio). */
  larguraAlinhamentosM: number | null;
  campos: CampoVia[];
}

export interface Captura {
  id: string;
  arquivo: string;
  /** Caminho relativo da imagem equirretangular reduzida. */
  imagem: string;
  cidade: string;
  lat: number;
  lon: number;
  /** Rumo (graus a partir do norte, sentido horário) do centro do panorama. */
  rumo: number;
  /** Rumo de deslocamento (da foto anterior para a seguinte), se conhecido. */
  rumoDeslocamento: number | null;
  /** Para que lado do panorama está a frente do veículo, e como isso foi decidido. */
  frente: { deg: number; fonte: string };
  data: string;
  camera: string;
  autor: string;
  licenca: string;
  /** Link para a imagem original na fonte. */
  origem: string;
  deteccoes: Deteccao[];
  via: ViaMalha;
}

export interface ParametrosProcessamento {
  alturaCameraM: number;
  alturaMinimaPosteM: number;
  limiares: Record<Classe, number>;
  descricoes: Record<Classe, string[]>;
}

export interface Campanha {
  id: string;
  nome: string;
  municipio: string;
  status: StatusCampanha;
  criadaEm: string;
  fonte: string;
  licenca: string;
  modelo: string;
  fontesCadastro: string | null;
  parametros: ParametrosProcessamento;
  cadastro: PosteCadastro[];
  capturas: Captura[];
}

export interface ResumoCampanha {
  id: string;
  nome: string;
  municipio: string;
  status: StatusCampanha;
  criadaEm: string;
  modelo: string;
  capturas: number;
  postes: number;
}

export const CLASSES: Record<Classe, { rotulo: string; plural: string; icone: string; cor: string }> = {
  poste: { rotulo: "Poste", plural: "Postes", icone: "vertical_align_top", cor: "#E8A24D" },
  braco: { rotulo: "Braço", plural: "Braços", icone: "turn_right", cor: "#0EA5E9" },
  luminaria: { rotulo: "Luminária", plural: "Luminárias", icone: "lightbulb", cor: "#17A672" },
};

export const FONTES: Record<Fonte, { rotulo: string; icone: string; tom: "marca" | "sucesso" | "neutro" }> = {
  imagem: { rotulo: "Imagem 360°", icone: "panorama_photosphere", tom: "marca" },
  cadastro: { rotulo: "Cadastro BDGD", icone: "table_view", tom: "sucesso" },
  mapa: { rotulo: "Mapa (OSM)", icone: "map", tom: "neutro" },
  revisao: { rotulo: "Revisão", icone: "edit_square", tom: "marca" },
};

export const STATUS: Record<StatusCampanha, { rotulo: string; tom: "neutro" | "marca" | "atencao" | "sucesso"; icone: string }> = {
  rascunho: { rotulo: "Rascunho", tom: "neutro", icone: "edit_note" },
  processando: { rotulo: "Processando", tom: "marca", icone: "progress_activity" },
  em_revisao: { rotulo: "Em revisão", tom: "atencao", icone: "rule" },
  concluida: { rotulo: "Concluída", tom: "sucesso", icone: "task_alt" },
};
