# Integrante do grupo:
# Mariana Alves da Silva - @himarialves
#
# Nome do grupo no Canvas: RA3_15
#
# Professor Frank Coelho de Alcantara
# Projeto acadêmico para a disciplina Linguagens Formais e Compiladores (2026-1).
# Instituição: Pontifícia Universidade Católica do Paraná - PUC/PR — 2026-1
'''
 CONTRACTS.py — Fonte única de verdade para tipos e interfaces do compilador.

Estrutura do arquivo:
   Seção 1 — Constantes (frozensets de operadores, Literals de tipos)
   Seção 2 — Tipos (Token, No, EntradaTabela, ErroSemantico, NoAtribuido)
   Seção 3 — Fábricas (construtores canônicos — use sempre estes)
   Seção 4 — Validadores (detectam bugs internos em desenvolvimento)
   Seção 5 — Tabela de compatibilidade de tipos (regras de tipo da linguagem)
'''

# Por que TypedDict em vez de dataclass?
# TypedDict gera dicts normais em runtime, então os módulos da Fase 2 (que já
# usavam dicts) não precisaram mudar. O Pylance entende os campos e dá
# autocomplete e verificação de tipo sem overhead de classe em runtime.

from __future__ import annotations
from typing import TypedDict, Literal

###
# SEÇÃO 1 — CONSTANTES GLOBAIS
###

# frozenset para keywords e operadores: imutável, O(1) no `in`, e hashável.
# Literal para tipos de tokens e nós: o Pylance usa esses para checar que
# nenhum módulo invente um tipo fora do contrato.

# Os três tipos semânticos da linguagem — tipagem forte, sem coerção implícita
TIPOS_VALIDOS = Literal["int", "real", "bool"]

# Keywords reservadas — não podem ser nomes de variáveis
KEYWORDS: frozenset[str] = frozenset({"START", "END", "RES", "IF", "THEN",
                                       "ELSE", "WHILE", "DO"})

# Tipos de tokens reconhecidos pelo lexer
TIPOS_TOKEN = Literal[
    "START",       # keyword START
    "END",         # keyword END
    "RES",         # keyword RES (reservada)
    "IF",          # estrutura de controle
    "THEN",
    "ELSE",
    "WHILE",
    "DO",
    "INTEIRO",     # literal inteiro: 3, 42, -1
    "REAL",        # literal real: 3.14, 2.0
    "BOOL",        # literal bool: TRUE, FALSE (se suportado)
    "IDENT",       # identificador de variável: X, MEM, VAR
    "OP_ARIT",     # operadores: + - * / | % ^
    "OP_REL",      # operadores relacionais: < > = <= >= !=
    "OP_LOG",      # operadores lógicos: AND OR NOT
    "LPAREN",      # (
    "RPAREN",      # )
    "COMENTARIO",  # *{ ... }* — descartado antes do parser
    "DESCONHECIDO" # token inválido — gera erro léxico
]

# Operadores aritméticos válidos
OPS_ARITMETICOS: frozenset[str] = frozenset({"+", "-", "*", "/", "|", "%", "^"})

# | e % são exclusivos de int — divisão real usa /, não |
# Isso está explícito aqui pra que verificar_tipos e o gerador não precisem
# repetir essa regra — basta checar OPS_APENAS_INT.
OPS_APENAS_INT: frozenset[str] = frozenset({"|", "%"})

# Operadores relacionais
OPS_RELACIONAIS: frozenset[str] = frozenset({"<", ">", "=", "<=", ">=", "!="})

# Operadores lógicos
OPS_LOGICOS: frozenset[str] = frozenset({"AND", "OR", "NOT"})

# Tipos de nós da árvore sintática
TIPOS_NO = Literal[
    "programa",       # nó raiz: START ... END
    "bloco",          # sequência de statements
    "expressao_rpn",  # (operando operando operador)
    "literal_int",    # número inteiro
    "literal_real",   # número real
    "literal_bool",   # TRUE / FALSE
    "variavel",       # (MEM) — leitura
    "atribuicao",     # (V MEM) — escrita
    "n_res",          # (N RES) — resultado anterior
    "if",             # estrutura IF THEN ELSE END
    "while",          # estrutura WHILE DO END
    "erro",           # nó marcado como inválido
]

# Categorias semânticas para nós atribuídos
CATEGORIAS_SEMANTICAS = Literal[
    "literal",
    "variavel_leitura",
    "variavel_escrita",
    "operacao_aritmetica",
    "operacao_relacional",
    "operacao_logica",
    "resultado_anterior",
    "controle_fluxo",
]

# Registradores ARM para o Cpulator-ARMv7 DEC1-SOC(v16.1)
# R0–R3: temporários, usados livremente pelo gerador
# R4–R7: callee-saved, precisam ser salvos/restaurados se o gerador os usar
# R12 (IP): scratch register — disponível pra cálculos intermediários como %
REGS_TEMPORARIOS: list[str] = ["R0", "R1", "R2", "R3"]
REGS_CALLEE_SAVED: list[str] = ["R4", "R5", "R6", "R7"]
REG_SCRATCH = "R12"  # IP — uso temporário, não preservar

###
# # SEÇÃO 2 — TIPOS (TypedDict)
###
# # Cada TypedDict define o contrato de uma fronteira entre módulos.
# A regra: se você produz um desses tipos, use a função fazer_*() da Seção 3 —
# nunca monte o dict manualmente, ou uma mudança de campo vai quebrar em runtime.

class Token(TypedDict):
    # Produzido por: prepararEntradaSemantica() — Módulo 1
    # Consumido por: parser interno do Módulo 1, construirTabelaSimbolos()
    #
    # COMENTARIO é tokenizado mas nunca chega ao parser (filtrado antes).
    # DESCONHECIDO dispara erro léxico antes de qualquer análise prosseguir.
    # linha começa em 1, não em 0.
    tipo:  str   # um dos valores de TIPOS_TOKEN
    valor: str   # lexema original do código-fonte
    linha: int   # linha no arquivo fonte (base 1)


class No(TypedDict):
    # Produzido por: parser do Módulo 1
    # Consumido por: construirTabelaSimbolos(), verificarTipos(), gerarArvoreAtribuida()
    #
    # valor é "" para nós compostos (programa, bloco) que não têm lexema próprio.
    # filhos é sempre uma lista — nunca None — mesmo que vazia (folhas da árvore).
    tipo:    str        # um dos valores de TIPOS_NO
    valor:   str        # lexema original ou "" para nós compostos
    filhos:  list[No]   # filhos diretos na árvore (vazio = nó folha)
    linha:   int        # linha no arquivo fonte (base 1)


class EntradaTabela(TypedDict):
    # Uma entrada da tabela de símbolos para uma variável.
    # linhas_uso é lista porque a mesma variável pode ser lida em vários lugares —
    # útil para relatório de erros ("X declarado na linha 3, usado nas linhas 7, 12").
    tipo:        str        # "int" | "real" | "bool"
    linha_decl:  int        # linha onde (V MEM) foi encontrado pela primeira vez
    linhas_uso:  list[int]  # linhas onde (MEM) aparece como leitura
    escopo:      str        # nome do arquivo fonte (base para futuras extensões)


# A tabela de símbolos completa: nome_variavel → EntradaTabela
# dict normal em vez de TypedDict porque as chaves são dinâmicas (nomes de variáveis).
TabelaSimbolos = dict[str, EntradaTabela]


class ErroSemantico(TypedDict):
    # Produzido por: construirTabelaSimbolos() e verificarTipos()
    # Consumido por: main() para relatório final e decisão de gerar Assembly
    #
    # Decisão: erros são coletados em lista, não lançados imediatamente.
    # Isso nos deixa mostrar todos os erros de uma vez em vez de parar no primeiro,
    # o que é muito mais útil pra quem está escrevendo o código-fonte.
    linha:     int
    tipo_erro: str   # snake_case descritivo, ex: "uso_antes_declaracao"
    mensagem:  str   # human-readable com linha + elemento + causa


class NoAtribuido(TypedDict):
    # Produzido por: gerarArvoreAtribuida() — Módulo 4A
    # Consumido por: gerarAssembly() — Módulo 4B
    #
    # É um No enriquecido com o que o gerador precisa: tipo semântico, registrador
    # onde o resultado vai ficar, e label ARM para desvios (IF/WHILE).
    #
    # Por que não herdar de No com class NoAtribuido(No)?
    # TypedDict suporta herança, mas `filhos` precisaria ser list[NoAtribuido] —
    # e TypedDict não permite redefinir um campo herdado com tipo diferente.
    # Solução: redefinir filhos: list (sem parâmetro) e documentar aqui.

    # Campos herdados de No
    tipo:    str
    valor:   str
    filhos:  list  # em runtime: list[NoAtribuido] — ver nota acima
    linha:   int
    # Campos semânticos adicionados pelo Módulo 4A
    tipo_semantico:      str   # "int" | "real" | "bool"
    categoria_semantica: str   # um dos valores de CATEGORIAS_SEMANTICAS
    reg_resultado:       str   # ex: "R0", "R1", "[SP, #4]" se usou pilha
    label:               str   # ex: "if_3", "end_while_1" — "" se não é desvio


###
# # SEÇÃO 3 — FUNÇÕES DE FÁBRICA (construtores canônicos)
###
# # Por que não criar Token/No diretamente com dict()?
# Porque se um dia adicionarmos um campo obrigatório ao contrato, todos os
# lugares que chamam fazer_token() ficam com erro de tipo imediatamente —
# em vez de um KeyError silencioso em runtime num caso de borda.

def fazer_token(tipo: str, valor: str, linha: int) -> Token:
    # Constructor canônico — use sempre este, nunca Token({...}) direto.
    return Token(tipo=tipo, valor=valor, linha=linha)


def fazer_no(tipo: str, valor: str, filhos: list, linha: int) -> No:
    # Constructor canônico de No.
    return No(tipo=tipo, valor=valor, filhos=filhos, linha=linha)


def fazer_erro_semantico(linha: int, tipo_erro: str, mensagem: str) -> ErroSemantico:
    # Constructor canônico de ErroSemantico.
    # Prepend automático de "Linha X:" — garante consistência nas mensagens
    # sem depender de cada módulo lembrar de incluir o número de linha.
    # Se a mensagem já começa com "Linha X:", não duplica.
    if not mensagem.startswith(f"Linha {linha}"):
        mensagem = f"Linha {linha}: {mensagem}"
    return ErroSemantico(linha=linha, tipo_erro=tipo_erro, mensagem=mensagem)


def fazer_no_atribuido(no: No, tipo_semantico: str,
                        categoria_semantica: str,
                        reg_resultado: str,
                        label: str = "",
                        filhos_atribuidos: list | None = None) -> NoAtribuido:
    # Constructor canônico de NoAtribuido a partir de um No existente.
    # filhos_atribuidos substitui no["filhos"] — deve ser list[NoAtribuido].
    # Se None, copia os filhos originais (útil para nós folha sem filhos atribuídos).
    return NoAtribuido(
        tipo=no["tipo"],
        valor=no["valor"],
        filhos=filhos_atribuidos if filhos_atribuidos is not None else no["filhos"],
        linha=no["linha"],
        tipo_semantico=tipo_semantico,
        categoria_semantica=categoria_semantica,
        reg_resultado=reg_resultado,
        label=label,
    )


###
# SEÇÃO 4 — FUNÇÕES DE VALIDAÇÃO (para uso durante desenvolvimento)
###
# # Essas funções não são chamadas em produção — são para detectar bugs internos
# do compilador durante desenvolvimento. Cada uma retorna lista de violações
# (vazia = OK) em vez de lançar exceção, pra poder reportar tudo de uma vez.

def validar_token(token: Token) -> list[str]:
    # Verifica que um Token tem os três campos obrigatórios e que linha >= 1.
    # Chamada por prepararEntradaSemantica() como sanity check após tokenização.
    erros = []
    for campo in ("tipo", "valor", "linha"):
        if campo not in token:
            erros.append(f"Token sem campo obrigatório: '{campo}'")
    if "linha" in token and (not isinstance(token["linha"], int) or token["linha"] < 1):
        erros.append(f"Token.linha deve ser int >= 1, got: {token.get('linha')}")
    return erros


def validar_no(no: No, profundidade: int = 0) -> list[str]:
    # Valida um No recursivamente, descendo por todos os filhos.
    # profundidade é só para mensagens de erro mais úteis ("filho[2]: ...").
    # Chamada por prepararEntradaSemantica() após o parser pra pegar árvores malformadas.
    erros = []
    for campo in ("tipo", "valor", "filhos", "linha"):
        if campo not in no:
            erros.append(f"No (prof={profundidade}) sem campo: '{campo}'")
    if "filhos" in no and not isinstance(no["filhos"], list):
        erros.append(f"No.filhos deve ser list, got: {type(no['filhos'])}")
    if "filhos" in no:
        for i, filho in enumerate(no["filhos"]):
            erros += [f"filho[{i}]: {e}" for e in validar_no(filho, profundidade + 1)]
    return erros


def validar_tabela(tabela: dict) -> list[str]:
    # Verifica que a tabela de símbolos está bem formada.
    # Nomes de variável são sempre maiúsculos na linguagem — qualquer coisa
    # minúscula indica um bug no construirTabelaSimbolos().
    erros = []
    for nome, entrada in tabela.items():
        if not nome.isupper():
            erros.append(f"Nome de variável deve ser maiúsculo: '{nome}'")
        if nome in KEYWORDS:
            erros.append(f"Variável usa keyword reservada: '{nome}'")
        for campo in ("tipo", "linha_decl", "linhas_uso", "escopo"):
            if campo not in entrada:
                erros.append(f"EntradaTabela['{nome}'] sem campo: '{campo}'")
        if "tipo" in entrada and entrada["tipo"] not in ("int", "real", "bool"):
            erros.append(f"Tipo inválido para '{nome}': '{entrada['tipo']}'")
    return erros


def validar_no_atribuido(no: NoAtribuido) -> list[str]:
    # Verifica os campos semânticos adicionados pelo Módulo 4A.
    # Reutiliza validar_no() para os campos base (tipo, valor, filhos, linha).
    erros = validar_no(no)
    for campo in ("tipo_semantico", "categoria_semantica", "reg_resultado", "label"):
        if campo not in no:
            erros.append(f"NoAtribuido sem campo semântico: '{campo}'")
    if "tipo_semantico" in no and no["tipo_semantico"] not in ("int", "real", "bool"):
        erros.append(f"tipo_semantico inválido: '{no['tipo_semantico']}'")
    return erros


###
# SEÇÃO 5 — TABELA DE COMPATIBILIDADE DE TIPOS
###
# Implementa a tipagem estática e forte da linguagem.
# Cada operador mapeia pares de tipos para o tipo resultado, ou None (= inválido).
#
# Decisões que ficam explícitas aqui:
#   "/"  só aceita real×real — divisão inteira tem operador próprio ("|")
#   "|"  e "%" só aceitam int×int — exclusivos de inteiros, sem coerção
#   "="  e "!=" aceitam bool×bool — permite comparar resultados de condições
#   "NOT" usa tupla de 1 elemento como chave — único operador unário da linguagem
#   int+real → None — tipagem forte, zero coerção implícita
#
# None como resultado (não exceção): verificar_tipos coleta o erro junto com
# outros em vez de parar imediatamente — mais útil para o programador.

# operador → {(tipo_esq, tipo_dir) → tipo_resultado}  (None = combinação inválida)
RESULTADO_TIPO_OPERACAO: dict[str, dict[tuple[str, ...], str | None]] = {
    "+":  {("int", "int"): "int",  ("real", "real"): "real",
           ("int", "real"): None,  ("real", "int"): None},
    "-":  {("int", "int"): "int",  ("real", "real"): "real",
           ("int", "real"): None,  ("real", "int"): None},
    "*":  {("int", "int"): "int",  ("real", "real"): "real",
           ("int", "real"): None,  ("real", "int"): None},
    "/":  {("real", "real"): "real",
           ("int", "int"): None,   ("int", "real"): None, ("real", "int"): None},
    "|":  {("int", "int"): "int"},   # divisão inteira — APENAS int×int
    "%":  {("int", "int"): "int"},   # resto — APENAS int×int
    "^":  {("int", "int"): "int",  ("real", "real"): "real",
           ("int", "real"): None,  ("real", "int"): None},
    "<":  {("int", "int"): "bool", ("real", "real"): "bool"},
    ">":  {("int", "int"): "bool", ("real", "real"): "bool"},
    "=":  {("int", "int"): "bool", ("real", "real"): "bool", ("bool", "bool"): "bool"},
    "<=": {("int", "int"): "bool", ("real", "real"): "bool"},
    ">=": {("int", "int"): "bool", ("real", "real"): "bool"},
    "!=": {("int", "int"): "bool", ("real", "real"): "bool", ("bool", "bool"): "bool"},
    "AND": {("bool", "bool"): "bool"},
    "OR":  {("bool", "bool"): "bool"},
    "NOT": {("bool",): "bool"},   # unário — tupla de 1 elemento
}


def tipo_resultado_operacao(op: str, tipo_esq: str,
                             tipo_dir: str | None = None) -> str | None:
    """
    Retorna o tipo resultante de uma operação, ou None se incompatível.

    Para operadores unários (NOT), passe tipo_dir=None.

    Exemplos:
        tipo_resultado_operacao("+", "int", "int")   → "int"
        tipo_resultado_operacao("+", "int", "real")  → None  (erro)
        tipo_resultado_operacao("|", "int", "int")   → "int"
        tipo_resultado_operacao("|", "real", "real") → None  (erro)
        tipo_resultado_operacao("NOT", "bool")       → "bool"
    """
    if op not in RESULTADO_TIPO_OPERACAO:
        return None
    tabela = RESULTADO_TIPO_OPERACAO[op]
    chave = (tipo_esq,) if tipo_dir is None else (tipo_esq, tipo_dir)
    return tabela.get(chave)   # None se par não existe na tabela
