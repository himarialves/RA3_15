# Integrante do grupo:
# Mariana Alves da Silva - @himarialves
#
# Nome do grupo no Canvas: RA3_15
#
# Professor Frank Coelho de Alcantara
# Projeto acadêmico para a disciplina Linguagens Formais e Compiladores (2026-1).
# Instituição: Pontifícia Universidade Católica do Paraná - PUC/PR — 2026-1
'''
verificar_tipos.py — Módulo 3: verificarTipos

Infere e valida tipos semânticos em toda a árvore sintática.
Recebe a árvore do Módulo 1 e a tabela de símbolos do Módulo 2.

Decisões de design que ficam evidentes aqui:
   dict[id(no) -> tipo] — anotamos cada nó pelo seu id() Python em vez de modificar o nó. 

   resultados: list[str] — passado em _verificar_lista para resolver (N RES).
   É o histórico dos tipos das expressões anteriores na sequência atual.

   Erros coletados em lista — nunca lança exceção.
'''

from __future__ import annotations
from CONTRACTS import (
    No, TabelaSimbolos, ErroSemantico,
    fazer_erro_semantico,
    tipo_resultado_operacao,
)

##
#  Inferência e validação por nó 
def _verificar_no(
    no: No,
    tabela: TabelaSimbolos,
    tipos: dict[int, str],
    erros: list[ErroSemantico],
    resultados: list[str],          # histórico de tipos para resolver (N RES)
) -> str | None:
    # Infere o tipo semântico do nó, registra em `tipos` e coleta erros.
    # Retorna o tipo inferido, ou None para nós sem valor (if, while, bloco-stmt).
    tipo_no = no["tipo"]

    ##
    # Literais 
    if tipo_no == "literal_int":
        return _registrar(no, "int", tipos)

    if tipo_no == "literal_real":
        return _registrar(no, "real", tipos)

    if tipo_no == "literal_bool":
        return _registrar(no, "bool", tipos)

    #  Variável (leitura) 
    if tipo_no == "variavel":
        entrada = tabela.get(no["valor"])
        if entrada is None or entrada["tipo"] == "desconhecido":
            return None   # erro já emitido pelo Módulo 2
        return _registrar(no, entrada["tipo"], tipos)

    #  (N RES) — resultado anterior 
    if tipo_no == "n_res":
        n = int(no["valor"])
        if n <= 0:
            erros.append(fazer_erro_semantico(
                no["linha"], "n_res_invalido",
                f"(N RES): N deve ser inteiro positivo, recebido {n}",
            ))
            return None
        if n > len(resultados):
            erros.append(fazer_erro_semantico(
                no["linha"], "n_res_fora_de_alcance",
                f"(N RES): N={n} mas há apenas {len(resultados)} resultado(s) anterior(es)",
            ))
            return None
        t = resultados[-n]
        return _registrar(no, t, tipos)

    #  Expressão RPN 
    if tipo_no == "expressao_rpn":
        return _verificar_expressao_rpn(no, tabela, tipos, erros, resultados)

    #  Bloco como valor inline (ex: (1 1 = FLAG)) 
    if tipo_no == "bloco" and no["valor"] == "":
        return _verificar_bloco_valor(no, tabela, tipos, erros, resultados)

    # Atribuição (V MEM) 
    if tipo_no == "atribuicao":
        return _verificar_atribuicao(no, tabela, tipos, erros, resultados)

    #  IF 
    if tipo_no == "if":
        _verificar_if(no, tabela, tipos, erros)
        return None

    #  WHILE 
    if tipo_no == "while":
        _verificar_while(no, tabela, tipos, erros)
        return None

    #  Programa / Bloco-statement (then, else, corpo) 
    if tipo_no in ("programa", "bloco"):
        _verificar_lista(no["filhos"], tabela, tipos, erros)
        return None

    return None


def _registrar(no: No, tipo: str, tipos: dict[int, str]) -> str:
    # Centraliza o mapeamento id(no) → tipo para garantir consistência.
    # Usar id() em vez de modificar o nó mantém a árvore imutável.
    tipos[id(no)] = tipo
    return tipo

##
#  Expressão RPN (operadores binários e unário NOT) 
def _verificar_expressao_rpn(
    no: No,
    tabela: TabelaSimbolos,
    tipos: dict[int, str],
    erros: list[ErroSemantico],
    resultados: list[str],
) -> str | None:
    op = no["valor"]
    filhos = no["filhos"]

    tipos_operandos: list[str | None] = [
        _verificar_no(f, tabela, tipos, erros, resultados)
        for f in filhos
    ]

    # Nó operador "bare" sem filhos — parte de um bloco-valor, sem tipo próprio
    if not filhos:
        return None

    if len(tipos_operandos) == 1:           # NOT (único operador unário)
        t1 = tipos_operandos[0]
        resultado = tipo_resultado_operacao(op, t1) if t1 else None
        if t1 and resultado is None:
            erros.append(fazer_erro_semantico(
                no["linha"], "tipo_incompativel",
                f"operação '{op}' não aceita operando do tipo '{t1}'",
            ))
        return _registrar(no, resultado, tipos) if resultado else None

    if len(tipos_operandos) >= 2:           # operadores binários
        t1, t2 = tipos_operandos[0], tipos_operandos[1]
        resultado = tipo_resultado_operacao(op, t1, t2) if (t1 and t2) else None
        if t1 and t2 and resultado is None:
            erros.append(fazer_erro_semantico(
                no["linha"], "tipo_incompativel",
                f"operação '{op}' entre '{t1}' e '{t2}' não é permitida",
            ))
        return _registrar(no, resultado, tipos) if resultado else None

    return None

##
#  Bloco como valor inline (ex: (1 1 = FLAG)) 

def _verificar_bloco_valor(
    no: No,
    tabela: TabelaSimbolos,
    tipos: dict[int, str],
    erros: list[ErroSemantico],
    resultados: list[str],
) -> str | None:
    # Caso especial gerado pelo parser para atribuições sem parênteses extras.
    # Ex: (1 1 = FLAG) -> o parser cria atribuição cujo valor é um nó bloco
    # com filhos [literal_int(1), literal_int(1), expressao_rpn(=)].
    # O operador fica no último filho e os operandos nos filhos anteriores.
    filhos = no["filhos"]
    if not filhos:
        return None

    ultimo = filhos[-1]
    if ultimo["tipo"] == "expressao_rpn" and not ultimo["filhos"]:
        op = ultimo["valor"]
        operandos = filhos[:-1]
        tipos_ops = [
            _verificar_no(f, tabela, tipos, erros, resultados)
            for f in operandos
        ]
        if len(tipos_ops) == 1:
            t1 = tipos_ops[0]
            resultado = tipo_resultado_operacao(op, t1) if t1 else None
            if t1 and resultado is None:
                erros.append(fazer_erro_semantico(
                    no["linha"], "tipo_incompativel",
                    f"operação '{op}' não aceita tipo '{t1}'",
                ))
            return _registrar(no, resultado, tipos) if resultado else None
        if len(tipos_ops) == 2:
            t1, t2 = tipos_ops[0], tipos_ops[1]
            resultado = tipo_resultado_operacao(op, t1, t2) if (t1 and t2) else None
            if t1 and t2 and resultado is None:
                erros.append(fazer_erro_semantico(
                    no["linha"], "tipo_incompativel",
                    f"operação '{op}' entre '{t1}' e '{t2}' não é permitida",
                ))
            return _registrar(no, resultado, tipos) if resultado else None

    # Fallback: bloco sem operador reconhecível — infere tipo do último filho
    return _verificar_no(filhos[-1], tabela, tipos, erros, resultados)

##
#  Atribuição (V MEM) 
def _verificar_atribuicao(
    no: No,
    tabela: TabelaSimbolos,
    tipos: dict[int, str],
    erros: list[ErroSemantico],
    resultados: list[str],
) -> str | None:
    nome = no["valor"]
    valor_no = no["filhos"][0]

    t_valor = _verificar_no(valor_no, tabela, tipos, erros, resultados)

    entrada = tabela.get(nome)
    if entrada and t_valor:
        t_declarado = entrada["tipo"]
        # "desconhecido" significa que o Módulo 2 não conseguiu inferir o tipo
        # na declaração — não é erro aqui, o Módulo 3 resolve agora
        if t_declarado not in ("desconhecido",) and t_declarado != t_valor:
            erros.append(fazer_erro_semantico(
                no["linha"], "tipo_incompativel",
                f"variável '{nome}' tem tipo '{t_declarado}' mas recebe valor do tipo '{t_valor}'",
            ))

    if t_valor:
        return _registrar(no, t_valor, tipos)
    return None

##
#  IF 
def _verificar_if(
    no: No,
    tabela: TabelaSimbolos,
    tipos: dict[int, str],
    erros: list[ErroSemantico],
) -> None:
    filhos = no["filhos"]
    condicao, bloco_then, bloco_else = filhos[0], filhos[1], filhos[2]

    # A condição deve ser bool — qualquer outro tipo é erro
    t_cond = _verificar_no(condicao, tabela, tipos, erros, [])
    if t_cond is not None and t_cond != "bool":
        erros.append(fazer_erro_semantico(
            condicao["linha"], "condicao_nao_bool",
            f"condição do IF deve ser bool, encontrado '{t_cond}'",
        ))

    # Blocos then/else têm seu próprio histórico de resultados (lista vazia)
    # — (N RES) dentro de um IF não pode referenciar resultados de fora
    _verificar_lista(bloco_then["filhos"], tabela, tipos, erros)
    _verificar_lista(bloco_else["filhos"], tabela, tipos, erros)

##
#  WHILE 
def _verificar_while(
    no: No,
    tabela: TabelaSimbolos,
    tipos: dict[int, str],
    erros: list[ErroSemantico],
) -> None:
    filhos = no["filhos"]
    condicao, bloco_corpo = filhos[0], filhos[1]

    t_cond = _verificar_no(condicao, tabela, tipos, erros, [])
    if t_cond is not None and t_cond != "bool":
        erros.append(fazer_erro_semantico(
            condicao["linha"], "condicao_nao_bool",
            f"condição do WHILE deve ser bool, encontrado '{t_cond}'",
        ))

    _verificar_lista(bloco_corpo["filhos"], tabela, tipos, erros)

##
#  Processamento de lista de statements 
def _verificar_lista(
    nos: list[No],
    tabela: TabelaSimbolos,
    tipos: dict[int, str],
    erros: list[ErroSemantico],
) -> None:
    # Processa uma sequência de statements mantendo o histórico de tipos
    # para resolução de (N RES). Cada statement que produz um tipo (expressão,
    # atribuição) vai para `resultados`, e (N RES) indexa esse histórico.
    resultados: list[str] = []
    for no in nos:
        t = _verificar_no(no, tabela, tipos, erros, resultados)
        if t is not None:
            resultados.append(t)

##
#  API pública 
def verificarTipos(
    arvore: No,
    tabela: TabelaSimbolos,
) -> tuple[dict[int, str], list[ErroSemantico]]:
    # Percorre a árvore sintática e verifica compatibilidade de tipos.
    # Entrada:  arvore  — árvore produzida por prepararEntradaSemantica()
    #           tabela  — tabela produzida por construirTabelaSimbolos()
    # Saída:    (tipos, erros)
    #           tipos  — dict[id(no) → tipo_semantico] para cada nó tipado
    #           erros  — list[ErroSemantico] com todos os erros de tipo encontrados
    tipos: dict[int, str] = {}
    erros: list[ErroSemantico] = []
    _verificar_lista(arvore["filhos"], tabela, tipos, erros)
    return tipos, erros

    # Erros detectados:
    #   tipo_incompativel      — operação entre tipos incompatíveis
    #   condicao_nao_bool      — condição de IF/WHILE não é bool
    #   n_res_invalido         — N <= 0 em (N RES)
    #   n_res_fora_de_alcance  — N maior que o número de resultados anteriores