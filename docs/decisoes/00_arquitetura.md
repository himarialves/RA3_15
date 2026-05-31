# [Fase 0] - Decisões Arquiteturais do Projeto

**Última atualização**: 2026-05-31
**Iteração atual**: v1 — Fase 0 (arquitetura inicial, antes de qualquer implementação)

## Decisões Vigentes

| ADR | Título | Status | Iteração |
|---|---|---|---|
| ADR-001 | CONTRACTS.py como fonte única de verdade | Aceita | v1 |
| ADR-002 | TypedDict em vez de dataclass ou dict puro | Aceita | v1 |
| ADR-003 | Pipeline linear de 4 módulos sem feedback | Aceita | v1 |
| ADR-004 | Estratégia F64 unificada para assembly | Aceita | v1 |
| ADR-005 | Compatibilidade com Python 3.9 via `from __future__ import annotations` | Aceita | v1 |
| ADR-006 | Pasta `output/` separada para artefatos gerados | Aceita | v1 |

## Linha do Tempo de Decisões

### Fase 0 — 2026-05-20 (antes de qualquer código)

- **ADR-001**: Centralizar todos os tipos de interface em `CONTRACTS.py` para
  garantir compatibilidade entre os 4 módulos implementados independentemente.

- **ADR-002**: Escolher `TypedDict` como representação de tipos porque é compatível
  com `dict` (sem migração da Fase 2), permite `json.dump` nativo e adiciona
  type hints sem overhead de runtime.

- **ADR-003**: Pipeline linear estrito — cada módulo recebe a saída do anterior.
  A linguagem RPN não exige múltiplas passagens (sem forward references entre funções).

- **ADR-004**: Todos os valores (int e real) em registradores VFP D-regs (F64),
  simplificando o gerador a um único conjunto de instruções ao custo de conversão
  explícita de inteiros.

- **ADR-005**: `from __future__ import annotations` em todos os arquivos para usar
  sintaxe moderna de type hints no Python 3.9 do ambiente de desenvolvimento.

- **ADR-006**: Artefatos gerados em `output/` (subdiretório fixo) para não poluir
  a raiz do projeto e dar às testes de integração um caminho previsível.

## Decisões que Afetam Este Módulo de Outros Módulos

Nenhuma — Fase 0 é a origem de todas as decisões arquiteturais do projeto.

## Princípios Arquiteturais Adotados

1. **Contrato explícito antes de código**: CONTRACTS.py foi gerado antes de qualquer módulo
2. **Tipagem estática e forte**: int+real é erro semântico em todos os contextos
3. **Falha rápida em erros estruturais**: erros léxicos/sintáticos interrompem o pipeline; erros semânticos são coletados por completo
4. **Testabilidade por design**: cada módulo pode ser testado isoladamente com os tipos de CONTRACTS.py
5. **Sem dependências externas**: apenas `pytest` para testes; sem bibliotecas de terceiros no código de produção
