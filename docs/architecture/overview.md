# Visão geral da arquitetura

Ver §3 da [especificação](../especificacao.md).

```mermaid
flowchart LR
  domain --> application
  application --> adapters
  adapters --> entry[api / cli / flows]
  entry --> bootstrap
```

As setas indicam "é usado por". Contratos verificados por `make arch`.

## Referência do domínio

::: ipsurvey.domain.models.core
