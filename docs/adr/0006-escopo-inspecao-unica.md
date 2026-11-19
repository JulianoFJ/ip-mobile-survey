# 0006: Inspeção única por ponto de IP, com saída na planilha de inspeção

- **Status:** aceita
- **Data:** 2026-11-19

## Contexto

A especificação v0.1 descreve uma plataforma genérica de levantamento de ativos, com atributos por
poste e por vão. Na prática, o uso na Houer é outro:

- a equipe mapeia a rede de um município **uma vez** (inspeção de campo);
- os resultados são confrontados com o **cadastro atual** do município;
- o produto final é a **planilha de inspeção de campo** que alimenta as planilhas de simulação
  (Plataforma_IP, `simulacao_nbr`).

## Decisão

1. **Unidade de registro: ponto de IP** (um poste com suas luminárias), não componentes separados.
2. **Saída canônica: colunas B–AW da aba "Simulações"**, com as mesmas letras e cabeçalhos do
   `modelo_planilha_simulacao.json` da Plataforma_IP, uma linha por ponto. Contrato em
   `ipsurvey.domain.inspection.columns`.
3. Cada campo registra a **origem** (medido no levantamento, cadastro, escritório) e, quando
   medido, a **confiança**. A exportação mostra isso numa aba à parte e destaca os campos de baixa
   confiança.
4. Colunas calculadas pela planilha (Q, AK, AO, AV) **não** são preenchidas pelo ipsurvey.
5. Sem histórico de levantamentos nem ciclo de vida do ativo: cada campanha é independente.

## Alternativas consideradas

- Componentes separados (poste, braço, luminária): mais flexível, mas não é o que a planilha de
  simulação consome. Pode vir depois, sem quebrar o contrato.
- Gestão de ativos com ciclo de vida e ordens de serviço: fora do uso real.

## Consequências

- O esquema do banco (#4) modela `inspection_point` no lugar de `pole_observation` como entidade de
  saída. As observações por segmento continuam como dado intermediário do pipeline.
- A malha NBR 5101 (`domain/nbr5101`) fica para o módulo fotométrico. O ipsurvey não simula.
- Mudança no layout da planilha de simulação exige atualizar o contrato e o teste de contrato.
