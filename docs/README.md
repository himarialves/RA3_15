# Analisador Semântico — RA3_15

**Aluna:** Mariana Alves da Silva — @himarialves  
**Grupo:** RA3_15  
**Disciplina:** Linguagens Formais e Compiladores — PUC/PR 2026-1  
**Professor:** Frank Coelho de Alcantara

---

## Descrição

Analisador semântico para uma linguagem de expressões em notação polonesa (pós-fixada), com geração de código Assembly ARMv7 para execução no simulador [CPUlator](https://cpulator.01xz.net/?sys=arm-de1soc) (DEC1-SOC v16.1).

O pipeline completo é:

```
arquivo.txt
    │
    ▼  lexer + parser          (lexer.py, parser.py)
    │  → list[Token], No
    │
    ▼  tabela de símbolos      (tabela_simbolos.py)
    │  → TabelaSimbolos, list[ErroSemantico]
    │
    ▼  verificação de tipos    (verificar_tipos.py)
    │  → dict[int, str], list[ErroSemantico]
    │
    ▼  geração de Assembly     (gerador.py)
       → str (arquivo .asm)
```

---

## Requisitos

```bash
pip install pytest
```

Python 3.10+.

---

## Como Usar

### Compilar um programa

```bash
python AnalisadorSemantico.py <arquivo.txt>
```

O assembly gerado é salvo em `output/<nome>.asm`.

**Exemplos:**

```bash
python AnalisadorSemantico.py teste1.txt
python AnalisadorSemantico.py tests/fixtures/prog_valido.txt
```

### Validar o assembly antes de colar no CPUlator

```bash
python validar_assembly.py output/<nome>.asm
```

Verifica: seções `.data`/`.text`, labels duplicados, referências indefinidas, alinhamento, inicializações obrigatórias.

### Rodar os testes

```bash
pytest -v                          # todos os testes
pytest tests/test_04_assembly.py   # só os testes de assembly
pytest --tb=short                  # saída resumida
```

---

## Programas de Teste

| Arquivo | Descrição | Resultado esperado |
|---|---|---|
| `teste1.txt` | Todas as operações e estruturas | Assembly válido |
| `teste2.txt` | Erros semânticos intencionais (6 erros) | Rejeita com lista de erros |
| `teste3.txt` | Mistura complexa: aritméticas, IF aninhado, reais | Assembly válido |
| `tests/fixtures/prog_valido.txt` | Demonstra todos os operadores | Assembly válido |
| `tests/fixtures/prog_complexo.txt` | Loop de acumulação + reais | Assembly válido |
| `tests/fixtures/prog_erros_semanticos.txt` | Erros semânticos | Rejeita com lista de erros |

---

## Linguagem Suportada

```
START
  (operando1 operando2 operador)   @ expressão em notação polonesa
  (valor VARIAVEL)                 @ atribuição
  (N RES)                          @ salva N-ésimo resultado no histórico
  IF (cond) THEN ... ELSE ... END IF
  WHILE (cond) DO ... END WHILE
END
```

**Operadores inteiros:** `+` `-` `*` `|` `%` `^` `<` `>` `=` `<=` `>=`  
**Operadores reais:** `+` `-` `*` `/`  
**Operadores lógicos:** `AND` `OR` `NOT`  
**Tipagem:** estática e forte — `int + real` é erro semântico.

---

## Estrutura do Projeto

```
.
├── AnalisadorSemantico.py       # entry point
├── CONTRACTS.py                 # tipos compartilhados (fonte única de verdade)
├── lexer.py                     # análise léxica
├── tabela_simbolos.py           # tabela de símbolos
├── verificar_tipos.py           # verificação de tipos
├── gerador.py                   # geração de Assembly ARMv7
├── validar_assembly.py          # validação estática do .asm gerado
├── tests/
│   ├── test_01_lexer.py
│   ├── test_02_tabela_simbolos.py
│   ├── test_03_assembly.py
│   ├── test_04_tipos.py
│   ├── test_05_integracao.py
│   └── fixtures/
│       ├── prog_valido.txt
│       ├── prog_complexo.txt
│       └── prog_erros_semanticos.txt
└── output/                      # .asm gerados (criado automaticamente)
```
