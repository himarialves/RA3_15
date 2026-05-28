# Integrante do grupo:
# Mariana Alves da Silva - @himarialves

# Nome do grupo no Canvas: RA3_15

# Professor Frank Coelho de Alcantara 
# Projeto acadêmico para a disciplina Linguagens Formais e Compiladores (2026-1).
# Instituição:  Pontifícia Universidade Católica do Paraná - PUC/PR — 2026-1

# lexer.py — lê o arquivo .txt, transforma em tokens e monta a árvore sintática.
# Os módulos seguintes assumem que a entrada já foi validada.

from __future__ import annotations
import re
import sys
from CONTRACTS import (
    Token, No,
    fazer_token, fazer_no,
    KEYWORDS, OPS_ARITMETICOS, OPS_RELACIONAIS, OPS_LOGICOS,
    validar_token, validar_no,
)

##
# Exceções internas  - usadas só dentro do módulo — 
# quem chama prepararEntradaSemantica() não precisa capturar essas exceções, 
# são convertidas em sys.exit(1) antes de sair.

class ErroLexico(Exception):
    def __init__(self, linha: int, msg: str):
        super().__init__(f"Erro léxico na linha {linha}: {msg}")
        self.linha = linha


class ErroSintatico(Exception):
    def __init__(self, linha: int, msg: str):
        super().__init__(f"Erro sintático na linha {linha}: {msg}")
        self.linha = linha

##

# Lexer 
# Arq: regex master com grupos nomeados: 
#  - cada grupo captura um tipo de token e re.finditer percorre o texto uma só vez 
#  — sem backtracking entre padrões, muito mais rápido do que tentar cada regex separada.

# ordem dos padrões:
#   COMENTARIO primeiro — *{ }* pode conter operadores e palavras que seriam
#     tokenizados se o comentário não "ganhar" antes deles.
#   REAL antes de INTEIRO — sem isso, -3.14 viraria INTEIRO(-3) + erro(.14).
#   OP_REL multi-char (<=, >=, !=) antes dos single-char (<, >, =) — o alternador
#     da regex tenta da esquerda pra direita; se = viesse primeiro, <= nunca casaria.
#   PALAVRA captura tudo maiúsculo e a reclassificação fica em _tokenizar —
#     mais simples do que listar cada keyword como padrão separado.
#   DESCONHECIDO é o catch-all no fim — qualquer char que não casou chega aqui.

_PADROES: list[tuple[str, str]] = [
    ("COMENTARIO", r"\*\{.*?\}\*"),   # *{ ... }* — consome o bloco inteiro (DOTALL)
    ("REAL",       r"-?\d+\.\d+"),    # 3.14, -2.0 — antes de INTEIRO por causa do ponto
    ("INTEIRO",    r"-?\d+"),         # 3, 42, -1
    ("OP_REL",     r"<=|>=|!=|<|>|="),# multi-char antes de single-char (ver acima)
    ("OP_ARIT",    r"[+\-*/|%^]"),
    ("LPAREN",     r"\("),
    ("RPAREN",     r"\)"),
    ("PALAVRA",    r"[A-Z][A-Z0-9_]*"),# keywords + idents — reclassificados em _tokenizar
    ("IGNORAR",    r"[ \t\r]+"),
    ("NEWLINE",    r"\n"),
    ("DESCONHECIDO", r"."),            # catch-all — gera erro léxico
]

# re.DOTALL faz o . dentro de COMENTARIO cruzar \n — necessário pra *{ bloco
# multilinhas }* ser consumido como um token único em vez de parar na primeira quebra.
_RE_MASTER = re.compile(
    "|".join(f"(?P<{nome}>{padrao})" for nome, padrao in _PADROES),
    re.DOTALL,
)


def _tokenizar(texto: str) -> tuple[list[Token], list[str]]:
    # Varre o texto inteiro e devolve todos os tokens — inclusive COMENTARIO.
    
    # Decisão: não filtrar comentários aqui. 
    # prepararEntradaSemantica() faz isso DEPOIS.
    # Separar as duas responsabilidades nos deixa testar o reconhecimento de *{ }* 
    # diretamente via _tokenizar() sem precisar de um programa completo.
    tokens: list[Token] = []
    erros: list[str] = []
    linha = 1

    for m in _RE_MASTER.finditer(texto):
        tipo = m.lastgroup
        assert tipo is not None  # regex sempre tem grupo ativo — nunca é None
        valor = m.group()

        if tipo == "NEWLINE":
            linha += 1
            continue
        if tipo == "IGNORAR":
            continue
        if tipo == "COMENTARIO":
            # Avança a contagem de linhas pelo conteúdo do comentário.
            # Sem isso, todos os tokens depois de um comentário multilinhas
            # teriam número de linha errado.
            tokens.append(fazer_token("COMENTARIO", valor, linha))
            linha += valor.count("\n")
            continue
        if tipo == "DESCONHECIDO":
            erros.append(f"Linha {linha}: token inválido '{valor}'")
            continue
        if tipo == "PALAVRA":
            # Reclassifica: AND/OR/NOT verificados antes de KEYWORDS porque
            # estão em maiúsculo e cairiam em IDENT se não forem checados primeiro.
            if valor in ("AND", "OR", "NOT"):
                tipo = "OP_LOG"
            elif valor in ("TRUE", "FALSE"):
                tipo = "BOOL"
            elif valor in KEYWORDS:
                tipo = valor          # START, END, IF, THEN, ELSE, WHILE, DO, RES
            else:
                tipo = "IDENT"

        tokens.append(fazer_token(tipo, valor, linha))

    return tokens, erros


# #

# Token Stream 
class _TokenStream:
    # Encapsula a lista de tokens com peek e consumo tipado.
    # Sem isso, cada função do parser teria que passar o índice atual como parâmetro
    # Com peek() dá pra olhar o próximo token sem consumir,
    def __init__(self, tokens: list[Token]):
        self._tokens = tokens
        self._pos = 0

    def peek(self, offset: int = 0) -> Token | None:
        idx = self._pos + offset
        return self._tokens[idx] if idx < len(self._tokens) else None

    def consumir(self) -> Token:
        if self._pos >= len(self._tokens):
            ultima_linha = self._tokens[-1]["linha"] if self._tokens else 1
            raise ErroSintatico(ultima_linha, "fim inesperado do arquivo")
        t = self._tokens[self._pos]
        self._pos += 1
        return t

    def consumir_tipo(self, tipo_esperado: str) -> Token:
        t = self.consumir()
        if t["tipo"] != tipo_esperado:
            raise ErroSintatico(
                t["linha"],
                f"esperado '{tipo_esperado}', encontrado '{t['tipo']}' ('{t['valor']}')",
            )
        return t

    def fim(self) -> bool:
        return self._pos >= len(self._tokens)

    @property
    def linha_atual(self) -> int:
        t = self.peek()
        return t["linha"] if t else -1


##

# Parser

def _parse_programa(stream: _TokenStream) -> No:
    linha = stream.linha_atual
    stream.consumir_tipo("START")
    filhos = _parse_bloco(stream)
    stream.consumir_tipo("END")
    return fazer_no("programa", "", filhos, linha)


def _parse_bloco(stream: _TokenStream) -> list[No]:
    # Consome statements até encontrar END ou ELSE, sem consumir o terminador.
    nos: list[No] = []
    while not stream.fim():
        prox = stream.peek()
        assert prox is not None  # garantido pelo while not fim()
        if prox["tipo"] in ("END", "ELSE"):
            break
        if prox["tipo"] == "IF":
            nos.append(_parse_if(stream))
        elif prox["tipo"] == "WHILE":
            nos.append(_parse_while(stream))
        elif prox["tipo"] == "LPAREN":
            nos.append(_parse_expressao_paren(stream))
        else:
            raise ErroSintatico(
                prox["linha"],
                f"token inesperado '{prox['valor']}' (tipo '{prox['tipo']}')",
            )
    return nos


def _parse_if(stream: _TokenStream) -> No:
    linha = stream.linha_atual
    stream.consumir_tipo("IF")

    condicao = _parse_expressao_paren(stream)
    stream.consumir_tipo("THEN")

    nos_then = _parse_bloco(stream)
    bloco_then = fazer_no("bloco", "then", nos_then, condicao["linha"])

    nos_else: list[No] = []
    prox = stream.peek()
    if prox and prox["tipo"] == "ELSE":
        stream.consumir()
        nos_else = _parse_bloco(stream)

    bloco_else = fazer_no("bloco", "else", nos_else, linha)

    stream.consumir_tipo("END")
    prox = stream.peek()
    if prox and prox["tipo"] == "IF":
        stream.consumir()   # "END IF" — consome IF opcional

    return fazer_no("if", "", [condicao, bloco_then, bloco_else], linha)


def _parse_while(stream: _TokenStream) -> No:
    linha = stream.linha_atual
    stream.consumir_tipo("WHILE")

    condicao = _parse_expressao_paren(stream)
    stream.consumir_tipo("DO")

    nos_corpo = _parse_bloco(stream)
    bloco_corpo = fazer_no("bloco", "corpo", nos_corpo, condicao["linha"])

    stream.consumir_tipo("END")
    prox = stream.peek()
    if prox and prox["tipo"] == "WHILE":
        stream.consumir()   # "END WHILE" — consome WHILE opcional

    return fazer_no("while", "", [condicao, bloco_corpo], linha)


def _parse_expressao_paren(stream: _TokenStream) -> No:
    # Coleta tudo dentro de (...) e passa pra _classificar decidir o tipo do nó.
    # A forma exata só fica clara depois de ver todos os elementos — não dá pra
    # saber se é atribuição ou expressão só pelo primeiro token.
    # Expressões aninhadas funcionam porque a função chama a si mesma ao encontrar '('.
    linha = stream.linha_atual
    stream.consumir_tipo("LPAREN")

    elementos: list[No] = []
    while not stream.fim():
        prox = stream.peek()
        assert prox is not None  # garantido pelo while not fim()
        if prox["tipo"] == "RPAREN":
            break
        if prox["tipo"] == "LPAREN":
            elementos.append(_parse_expressao_paren(stream))
        else:
            elementos.append(_token_para_no(stream))

    stream.consumir_tipo("RPAREN")
    return _classificar(elementos, linha)


def _token_para_no(stream: _TokenStream) -> No:
    # Consome o próximo token e transforma num nó folha da árvore.
    t = stream.consumir()
    tipo = t["tipo"]
    linha = t["linha"]

    if tipo == "INTEIRO":
        return fazer_no("literal_int", t["valor"], [], linha)
    if tipo == "REAL":
        return fazer_no("literal_real", t["valor"], [], linha)
    if tipo == "BOOL":
        return fazer_no("literal_bool", t["valor"], [], linha)
    if tipo in ("OP_ARIT", "OP_REL", "OP_LOG"):
        # Nó temporário para operador — tipo "expressao_rpn" com filhos vazios
        return fazer_no("expressao_rpn", t["valor"], [], linha)
    if tipo == "IDENT":
        return fazer_no("variavel", t["valor"], [], linha)
    if tipo == "RES":
        return fazer_no("variavel", "RES", [], linha)
    raise ErroSintatico(linha, f"elemento inesperado '{t['valor']}' (tipo '{tipo}')")


def _classificar(elementos: list[No], linha: int) -> No:
    # Decide o tipo do nó olhando quantos elementos tem e o que é o último.
    # A lógica é: se o último é identificador -> atribuição (V MEM).
    # Se o último é operador -> expressão RPN. Caso especial: (N RES) e (MEM).
    if not elementos:
        raise ErroSintatico(linha, "expressão vazia '()'")

    # (MEM) — leitura de variável: elemento único que é um identificador
    if len(elementos) == 1:
        el = elementos[0]
        if el["tipo"] == "variavel":
            return fazer_no("variavel", el["valor"], [], el["linha"])
        raise ErroSintatico(linha, f"expressão com um único elemento inválido: '{el['valor']}'")

    ultimo = elementos[-1]

    # (N RES) — resultado anterior
    if (len(elementos) == 2
            and elementos[0]["tipo"] == "literal_int"
            and elementos[1]["tipo"] == "variavel"
            and elementos[1]["valor"] == "RES"):
        return fazer_no("n_res", elementos[0]["valor"], [], linha)

    # (V MEM) — atribuição: último elemento é identificador (não operador)
    # Inclui (V RES) — sintaticamente aceito aqui; erro semântico gerado no Módulo 2
    if ultimo["tipo"] == "variavel":
        # o valor pode ser literal, variável ou expressão aninhada
        if len(elementos) == 2:
            valor_no = elementos[0]
        else:
            # expressão composta como valor (ex: múltiplos elementos antes do MEM)
            valor_no = fazer_no("bloco", "", elementos[:-1], linha)
        return fazer_no("atribuicao", ultimo["valor"], [valor_no], linha)

    # (e1 e2 OP) — operação: último elemento é operador
    if ultimo["tipo"] == "expressao_rpn" and not ultimo["filhos"]:
        operandos = elementos[:-1]
        return fazer_no("expressao_rpn", ultimo["valor"], operandos, linha)

    raise ErroSintatico(
        linha,
        f"não foi possível classificar expressão com {len(elementos)} elemento(s); "
        f"último: tipo='{ultimo['tipo']}' valor='{ultimo['valor']}'",
    )


## 
# interface pública 
#

def prepararEntradaSemantica(arquivo: str) -> tuple[list[Token], No]:
    # Função pública do módulo — é isso que AnalisadorSemantico.py chama.
    # Faz tudo: lê arquivo -> tokeniza -> filtra comentários -> parseia -> valida contratos.
    
    # 1. Leitura
    try:
        with open(arquivo, encoding="utf-8") as f:
            texto = f.read()
    except FileNotFoundError:
        print(f"Erro: arquivo '{arquivo}' não encontrado.", file=sys.stderr)
        sys.exit(1)

    # 2. Tokenização
    todos_tokens, erros_lexicos = _tokenizar(texto)

    if erros_lexicos:
        for e in erros_lexicos:
            print(e, file=sys.stderr)
        sys.exit(1)

    # 3. Filtrar comentários (mantém a lista sem comentários para as fases seguintes)
    tokens = [t for t in todos_tokens if t["tipo"] != "COMENTARIO"]

    # 4. Validar presença de START / END
    tipos_seq = [t["tipo"] for t in tokens]
    if not tipos_seq or tipos_seq[0] != "START":
        print("Erro sintático: programa deve começar com START.", file=sys.stderr)
        sys.exit(1)
    if "END" not in tipos_seq:
        print("Erro sintático: programa deve terminar com END.", file=sys.stderr)
        sys.exit(1)

    # 5. Parsing + validação de contratos
    try:
        stream = _TokenStream(tokens)
        arvore = _parse_programa(stream)
        if not stream.fim():
            prox = stream.peek()
            assert prox is not None  # garantido pelo if not fim()
            raise ErroSintatico(
                prox["linha"],
                f"tokens inesperados após END: '{prox['valor']}'",
            )
        # 6. Validação dos contratos (detecta bugs internos do parser)
        violacoes = validar_no(arvore)
        if violacoes:
            print("Erro interno: árvore sintática viola contratos:", file=sys.stderr)
            for v in violacoes:
                print(f"  {v}", file=sys.stderr)
            sys.exit(1)
        return tokens, arvore
    except ErroSintatico as e:
        print(e, file=sys.stderr)
        sys.exit(1)
