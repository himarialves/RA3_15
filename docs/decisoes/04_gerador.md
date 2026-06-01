# Índice de ADRs — Fase 3: Analisador Semântico

**Projeto**: Compilador RPN — Fase 3 (Analisador Semântico + Gerador de Assembly)
**Linguagem**: Python 3.9+
**Alvo**: CPulator-ARMv7 DEC1-SOC(v16.1)
**Aluna**: Mariana Alves

## Todas as ADRs

| ID | Título | Módulo | Status | Data |
|---|---|---|---|---|
| ADR-001 | CONTRACTS.py como fonte única de verdade | fase_00 | Aceita | 2026-05-30 |
| ADR-002 | TypedDict em vez de dataclass ou dict puro | fase_00 | Aceita | 2026-05-30 |
| ADR-003 | Pipeline linear de 4 módulos sem feedback | fase_00 | Aceita | 2026-05-30 |
| ADR-004 | Estratégia F64 unificada para assembly | fase_00 | Aceita | 2026-05-30 |
| ADR-005 | Compatibilidade com Python 3.9 via `from __future__` | fase_00 | Aceita | 2026-05-30 |
| ADR-006 | Pasta `output/` separada para artefatos gerados | fase_00 | Aceita | 2026-05-30 |

## Decisões Cross-Module (afetam mais de um módulo)

| ADR | Título | Módulos Afetados |
|---|---|---|
| ADR-001 | CONTRACTS.py como fonte única de verdade | todos (01, 02, 03, 04) |
| ADR-002 | TypedDict em vez de dataclass ou dict puro | todos (01, 02, 03, 04) |
| ADR-003 | Pipeline linear de 4 módulos | todos (01, 02, 03, 04) |
| ADR-005 | Compatibilidade Python 3.9 | todos (01, 02, 03, 04) |
| ADR-004 | Estratégia F64 unificada | 03 (verificar_tipos), 04 (gerador) |
| ADR-006 | Pasta `output/` separada | 04 (gerador), AnalisadorSemantico.py |

