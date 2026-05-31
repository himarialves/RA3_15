# Integrante do grupo:
# Mariana Alves da Silva - @himarialves
#
# Nome do grupo no Canvas: RA3_15
#
# Professor Frank Coelho de Alcantara
# Projeto acadêmico para a disciplina Linguagens Formais e Compiladores (2026-1).
# Instituição: Pontifícia Universidade Católica do Paraná - PUC/PR — 2026-1

'''
test_02_tabela_simbolos.py — Testes de construirTabelaSimbolos (Módulo 2).

Cobre: declaração de variáveis, inferência de tipo, erros semânticos
(uso antes de declaração, redefinição com tipo incompatível, RES como variável).

'''

from __future__ import annotations
import os
import tempfile

import pytest

from lexer import prepararEntradaSemantica
from tabela_simbolos import construirTabelaSimbolos

##
# Helpers
# construirTabelaSimbolos() retorna erros em lista.
def _pipeline(codigo: str):
    # Compila o código e roda o Módulo 2. Retorna (tabela, erros).
    # O finally garante limpeza do arquivo temporário mesmo em caso de exceção.
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt",
                                     delete=False, encoding="utf-8") as f:
        f.write(codigo)
        path = f.name
    try:
        _, arvore = prepararEntradaSemantica(path)
        tabela, erros = construirTabelaSimbolos(arvore)
        return tabela, erros
    finally:
        os.unlink(path)


def _sem_erros(codigo: str):
    # Atalho para casos que devem ser semanticamente válidos.
    # A mensagem de falha lista todos os erros encontrados.
    _, erros = _pipeline(codigo)
    assert erros == [], f"Erros inesperados: {[e['mensagem'] for e in erros]}"


def _com_erro(codigo: str, tipo_erro: str | None = None, trecho: str | None = None):
    # Atalho para casos que devem gerar pelo menos um erro semântico.
    # tipo_erro verifica o campo "tipo_erro" do ErroSemantico.
    _, erros = _pipeline(codigo)
    assert erros, "Esperava erro semântico, mas não houve nenhum"
    if tipo_erro:
        assert any(e["tipo_erro"] == tipo_erro for e in erros), \
            f"Esperava tipo_erro='{tipo_erro}', got: {[e['tipo_erro'] for e in erros]}"
    if trecho:
        assert any(trecho in e["mensagem"] for e in erros), \
            f"Esperava '{trecho}' na mensagem, got: {[e['mensagem'] for e in erros]}"

##
# Declaração e tipo 
# O tipo de uma variável é inferido do valor usado em (V MEM).
# Literal inteiro → int, literal real → real, expressão → tipo do resultado.
# Isso está definido em CONTRACTS.py (RESULTADO_TIPO_OPERACAO).

def test_variavel_int_registrada():
    tabela, _ = _pipeline("START\n(3 X)\nEND\n")
    assert "X" in tabela
    assert tabela["X"]["tipo"] == "int"

def test_variavel_real_registrada():
    tabela, _ = _pipeline("START\n(3.14 PI)\nEND\n")
    assert "PI" in tabela
    assert tabela["PI"]["tipo"] == "real"

def test_multiplas_variaveis():
    tabela, _ = _pipeline("START\n(1 A)\n(2.0 B)\nEND\n")
    assert tabela["A"]["tipo"] == "int"
    assert tabela["B"]["tipo"] == "real"

def test_linha_declaracao_registrada():
    tabela, _ = _pipeline("START\n(3 X)\nEND\n")
    assert tabela["X"]["linha_decl"] == 2

def test_linha_uso_registrada():
    tabela, _ = _pipeline("START\n(3 X)\n(X)\nEND\n")
    assert 3 in tabela["X"]["linhas_uso"]

def test_variavel_sem_uso_linhas_uso_vazio():
    # A declaração (V MEM) não conta como "uso" — só leituras (MEM) contam.
    # Isso facilita detectar variáveis declaradas mas nunca lidas.
    tabela, _ = _pipeline("START\n(3 X)\nEND\n")
    assert tabela["X"]["linhas_uso"] == []

def test_variavel_usada_multiplas_vezes():
    tabela, _ = _pipeline("START\n(3 X)\n(X)\n(X)\nEND\n")
    assert len(tabela["X"]["linhas_uso"]) == 2

def test_variavel_reatribuida_mesmo_tipo_valida():
    _sem_erros("START\n(3 X)\n(5 X)\nEND\n")

def test_variavel_tipo_resultado_de_expressao():
    # (3 4 +) resulta em int — X deve ser registrado como int
    tabela, _ = _pipeline("START\n((3 4 +) X)\nEND\n")
    assert tabela["X"]["tipo"] == "int"

##
#  Erros: uso antes de declaração 
# O módulo percorre a expressão de valor ANTES de registrar a variável destino.
# Isso garante que (X) detecta o erro mesmo que X apareça logo depois como MEM.
def test_uso_antes_de_declaracao_gera_erro():
    _com_erro("START\n(X)\n(3 X)\nEND\n", tipo_erro="variavel_nao_declarada")

def test_uso_em_expressao_antes_de_declaracao():
    _com_erro("START\n(X 2 +)\n(3 X)\nEND\n", tipo_erro="variavel_nao_declarada")

def test_variavel_nao_declarada_nunca():
    _com_erro("START\n(Y)\nEND\n", tipo_erro="variavel_nao_declarada")

##
# Erros: redefinição com tipo incompatível 
# Tipagem forte: int -> real ou real -> int são sempre erros.
def test_redef_int_para_real_gera_erro():
    _com_erro("START\n(3 X)\n(3.14 X)\nEND\n", tipo_erro="tipo_incompativel")

def test_redef_real_para_int_gera_erro():
    _com_erro("START\n(3.14 X)\n(3 X)\nEND\n", tipo_erro="tipo_incompativel")

##
# Erros: RES como variável 
def test_res_como_destino_de_atribuicao_gera_erro():
    # (3 RES) é interpretado como n_res válido (inteiro + keyword RES).
    # (3.14 RES) não é n_res (literal_real, não int) -> vira atribuição para RES -> erro.
    _com_erro("START\n(3.14 RES)\nEND\n", tipo_erro="res_como_variavel")

def test_res_na_mensagem():
    _com_erro("START\n(3.14 RES)\nEND\n", trecho="RES")

##
# Erros: linha correta no erro
# O campo "linha" do ErroSemantico deve apontar exatamente onde o problema está.
def test_erro_inclui_numero_de_linha():
    _, erros = _pipeline("START\n\n(Z)\nEND\n")
    assert erros[0]["linha"] == 3

def test_multiplos_erros_coletados():
    # Decisão de design: coleta todos os erros antes de retornar.
    _, erros = _pipeline("START\n(Y)\n(Z)\nEND\n")
    assert len(erros) >= 2

##
# Variáveis em estruturas de controle 
# Escopo plano: variáveis declaradas dentro de IF ou WHILE ficam na tabela global. 
def test_variavel_declarada_dentro_de_if():
    # Variável declarada em IF deve aparecer na tabela global.
    tabela, _ = _pipeline(
        "START\nIF (1 1 =) THEN\n(5 X)\nEND IF\nEND\n"
    )
    assert "X" in tabela

def test_variavel_usada_dentro_de_while():
    _sem_erros("START\n(0 I)\nWHILE (I 3 <) DO\n(1 I)\nEND WHILE\nEND\n")
