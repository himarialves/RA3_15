# Integrante do grupo:
# Mariana Alves da Silva - @himarialves
#
# Nome do grupo no Canvas: RA3_15
#
# Professor Frank Coelho de Alcantara
# Projeto acadêmico para a disciplina Linguagens Formais e Compiladores (2026-1).
# Instituição: Pontifícia Universidade Católica do Paraná - PUC/PR — 2026-1

'''
tabela_simbolos.py — Módulo 2: construirTabelaSimbolos

Percorre a árvore sintática e registra cada variável com tipo, linha de
declaração, linhas de uso e escopo.

Decisões de design que ficam evidentes aqui:
#   Variável declarada dentro de um IF é visível fora dele. 
#   Tipo inferido no ponto de declaração.
#   Erros coletados em lista — nunca lançamos exceção. 
'''

from __future__ import annotations
from CONTRACTS import (
    No, TabelaSimbolos, EntradaTabela, ErroSemantico,
    fazer_erro_semantico,
    tipo_resultado_operacao,
)

##
# Inferência de tipo 
# _inferir_tipo  desce pela árvore até encontrar um literal ou uma variável já conhecida na tabela.
# Retorna None quando não é possível determinar (n_res, variável não declarada).
def _inferir_tipo(no: No, tabela: TabelaSimbolos) -> str | None:
    tipo_no = no["tipo"]

    if tipo_no == "literal_int":
        return "int"
    if tipo_no == "literal_real":
        return "real"
    if tipo_no == "literal_bool":
        return "bool"

    if tipo_no == "variavel":
        entrada = tabela.get(no["valor"])
        return entrada["tipo"] if entrada else None

    if tipo_no == "expressao_rpn":
        op = no["valor"]
        filhos = no["filhos"]
        if len(filhos) == 1:                        # NOT (único operador unário)
            t = _inferir_tipo(filhos[0], tabela)
            return tipo_resultado_operacao(op, t) if t else None
        if len(filhos) >= 2:                        # operadores binários
            t1 = _inferir_tipo(filhos[0], tabela)
            t2 = _inferir_tipo(filhos[1], tabela)
            if t1 and t2:
                return tipo_resultado_operacao(op, t1, t2)

    if tipo_no == "atribuicao":
        # Tipo da atribuição é o tipo do seu valor
        return _inferir_tipo(no["filhos"][0], tabela)

    if tipo_no == "bloco":
        # Bloco como valor inline de uma atribuição: ex. (1 1 = FLAG)
        # O parser gera um nó bloco com [literal, literal, expressao_rpn(=)].
        # O tipo é determinado pelo operador no último filho.
        filhos = no["filhos"]
        if not filhos:
            return None
        ultimo = filhos[-1]
        if ultimo["tipo"] == "expressao_rpn" and not ultimo["filhos"]:
            op = ultimo["valor"]
            operandos = filhos[:-1]
            if len(operandos) == 1:
                t = _inferir_tipo(operandos[0], tabela)
                return tipo_resultado_operacao(op, t) if t else None
            if len(operandos) == 2:
                t1 = _inferir_tipo(operandos[0], tabela)
                t2 = _inferir_tipo(operandos[1], tabela)
                if t1 and t2:
                    return tipo_resultado_operacao(op, t1, t2)
        return _inferir_tipo(filhos[-1], tabela)

    # n_res — o tipo depende de qual resultado anterior estamos acessando,
    return None

##

# Travessia da árvore 
# _percorrer desce a árvore inteira.
# Só atribuicao e variavel têm tratamento especial
def _percorrer(no: No, tabela: TabelaSimbolos,
               erros: list[ErroSemantico], escopo: str) -> None:
    tipo_no = no["tipo"]

    if tipo_no == "atribuicao":
        _processar_atribuicao(no, tabela, erros, escopo)

    elif tipo_no == "variavel":
        _processar_leitura(no, tabela, erros)

    elif tipo_no in ("literal_int", "literal_real", "literal_bool", "n_res"):
        pass  # folhas sem variáveis — nada a registrar

    else:
        # programa, bloco, if, while, expressao_rpn — desce nos filhos
        for filho in no["filhos"]:
            _percorrer(filho, tabela, erros, escopo)


def _processar_atribuicao(no: No, tabela: TabelaSimbolos,
                           erros: list[ErroSemantico], escopo: str) -> None:
    # Processa (V MEM): registra ou valida a variável na tabela de símbolos.
    # Ordem importa: percorremos o sub-nó de valor ANTES de registrar MEM.
    nome = no["valor"]
    linha = no["linha"]
    valor_no = no["filhos"][0]

    # RES é keyword reservada — não pode ser usado como destino de atribuição
    if nome == "RES":
        erros.append(fazer_erro_semantico(
            linha, "res_como_variavel",
            f"'RES' é keyword reservada e não pode ser nome de variável",
        ))
        return

    # Percorre a expressão do valor antes de registrar (pré-ordem intencional)
    _percorrer(valor_no, tabela, erros, escopo)

    tipo_inferido = _inferir_tipo(valor_no, tabela)

    if nome in tabela:
        # Redefinição — verifica compatibilidade de tipo
        tipo_atual = tabela[nome]["tipo"]
        if tipo_inferido and tipo_atual != "desconhecido" and tipo_atual != tipo_inferido:
            erros.append(fazer_erro_semantico(
                linha, "tipo_incompativel",
                f"variável '{nome}' redefinida com tipo '{tipo_inferido}', "
                f"mas foi declarada como '{tipo_atual}'",
            ))
        else:
            # Se o tipo era desconhecido (declaração anterior com tipo não inferível),
            # aproveita a redefinição para resolver o tipo agora que temos mais contexto.
            if tipo_inferido and tabela[nome]["tipo"] == "desconhecido":
                tabela[nome]["tipo"] = tipo_inferido
            tabela[nome]["linhas_uso"].append(linha)
    else: 
        # Primeira declaração da variável.
        # "desconhecido" quando o tipo não é inferível agora
        # linhas_uso começa vazio: a própria declaração não conta como uso, só as leituras (MEM) contam.
        tabela[nome] = EntradaTabela(
            tipo=tipo_inferido or "desconhecido",
            linha_decl=linha,
            linhas_uso=[],
            escopo=escopo,
        )


def _processar_leitura(no: No, tabela: TabelaSimbolos,
                        erros: list[ErroSemantico]) -> None:
    # Processa (MEM): verifica declaração prévia e registra o uso.
    # Uso antes de declaração é erro semântico, não erro de tipo —
    nome = no["valor"]
    linha = no["linha"]

    if nome not in tabela:
        erros.append(fazer_erro_semantico(
            linha, "variavel_nao_declarada",
            f"variável '{nome}' usada antes de ser declarada",
        ))
    else:
        tabela[nome]["linhas_uso"].append(linha)

##
# API pública 
def construirTabelaSimbolos(
    arvore: No,
    escopo: str = "<programa>",
) -> tuple[TabelaSimbolos, list[ErroSemantico]]:
    # Entrada:  arvore — árvore produzida por prepararEntradaSemantica()
    #           escopo — nome do arquivo fonte (padrão "<programa>")
    # Saída:    (tabela_de_simbolos, lista_de_erros_semanticos)
    tabela: TabelaSimbolos = {}
    erros: list[ErroSemantico] = []
    _percorrer(arvore, tabela, erros, escopo)
    return tabela, erros

    # Erros detectados:
    #   variavel_nao_declarada  — uso de (MEM) antes de (V MEM)
    #   tipo_incompativel       — redefinição com tipo diferente do original
    #   res_como_variavel       — tentativa de usar RES como destino de atribuição