# Resumo de Decisões — Módulo 03: Verificação de Tipos

**Última atualização**: 2026-05-31
**Iteração atual**: v1

## Decisões Vigentes

| ADR | Título | Status | Iteração |
|---|---|---|---|
| — | Nenhuma ADR de módulo criada ainda | — | — |

## Linha do Tempo de Decisões

### v1 — 2026-05-20
- `verificarTipos(arvore: No, tabela: TabelaSimbolos)` retorna `tuple[dict[int, str], list[ErroSemantico]]`
- `dict[int, str]` mapeia `id(no)` → tipo semântico (`"int"`, `"real"`, `"bool"`)
- Tipagem estática e forte: `int + real` é erro; não há coerção implícita
- Condições de IF/WHILE devem ser `bool`; qualquer outro tipo é `tipo_invalido_condicao`
- `tipo_resultado_operacao()` de CONTRACTS.py é usado para todas as verificações
- Regras formais documentadas em cálculo de sequentes em `docs/regras_tipos.md`

## Decisões que Afetam Este Módulo de Outros Módulos

| ADR | Módulo de Origem | Impacto Aqui |
|---|---|---|
| ADR-001 | fase_00_arquitetura | RESULTADO_TIPO_OPERACAO e tipo_resultado_operacao() de CONTRACTS.py |
| ADR-004 | fase_00_arquitetura | int+real é erro semântico mesmo que assembly use F64 para ambos |
