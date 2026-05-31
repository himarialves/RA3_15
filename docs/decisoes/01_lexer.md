# Resumo de Decisões — Módulo 01: Lexer + Parser

**Última atualização**: 2026-05-31
**Iteração atual**: v1

## Decisões Vigentes

| ADR | Título | Status | Iteração |
|---|---|---|---|
| — | Nenhuma ADR de módulo criada ainda | — | — |

## Linha do Tempo de Decisões

### v1 — 2026-05-20
- Módulo reaproveitado da Fase 2 (lexer + parser pré-existentes)
- Adicionada função `prepararEntradaSemantica(arquivo: str)` como wrapper que integra lexer, parser e filtragem de comentários
- Comentários `*{ }*` reconhecidos como tokens `COMENTARIO` e filtrados antes do parser

## Decisões que Afetam Este Módulo de Outros Módulos

| ADR | Módulo de Origem | Impacto Aqui |
|---|---|---|
| ADR-001 | 00_arquitetura | Token e No devem ser importados de CONTRACTS.py |
| ADR-002 | 00_arquitetura | Token usa TypedDict — compatível com dict puro da Fase 2 |
| ADR-005 | 00_arquitetura | `from __future__ import annotations` necessário em lexer.py |
