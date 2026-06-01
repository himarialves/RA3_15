# Integrante do grupo:
# Mariana Alves da Silva - @himarialves
#
# Nome do grupo no Canvas: RA3_15
#
# Professor Frank Coelho de Alcantara
# Projeto acadêmico para a disciplina Linguagens Formais e Compiladores (2026-1).
# Instituição: Pontifícia Universidade Católica do Paraná - PUC/PR — 2026-1
'''
 test_03_tipos.py — Testes de verificarTipos (Módulo 3).

Cobre: todos os operadores aritméticos, relacionais e lógicos,
       condições de IF/WHILE, (N RES), variáveis, erros de tipo.

'''

from __future__ import annotations
import os
import tempfile

import pytest

from lexer import prepararEntradaSemantica
from tabela_simbolos import construirTabelaSimbolos
from verificar_tipos import verificarTipos

##
#  Helpers 
def _pipeline(codigo: str):
    # Roda os três módulos em sequência e retorna (tipos, erros_totais).
    # Os erros de declaração (Módulo 2) e de tipo (Módulo 3) são mergeados
    # numa lista única — reflete como o AnalisadorSemantico.py reporta ao usuário.
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt",
                                     delete=False, encoding="utf-8") as f:
        f.write(codigo)
        path = f.name
    try:
        tokens, arvore = prepararEntradaSemantica(path)
        tabela, erros_decl = construirTabelaSimbolos(arvore)
        tipos, erros_tipo = verificarTipos(arvore, tabela)
        return tipos, erros_decl + erros_tipo
    finally:
        os.unlink(path)

def _sem_erros(codigo: str):
    # Atalho para casos que devem ser semanticamente válidos.
    # A mensagem de falha lista todos os erros.
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
# Operadores aritméticos 
def test_int_mais_int_valido():
    _sem_erros("START\n(3 4 +)\nEND\n")

def test_real_mais_real_valido():
    _sem_erros("START\n(3.0 4.0 +)\nEND\n")

def test_int_mais_real_gera_erro():
    _com_erro("START\n(3 3.14 +)\nEND\n", tipo_erro="tipo_incompativel")

def test_real_mais_int_gera_erro():
    _com_erro("START\n(3.14 3 +)\nEND\n", tipo_erro="tipo_incompativel")

def test_int_menos_int_valido():
    _sem_erros("START\n(10 3 -)\nEND\n")

def test_int_vezes_int_valido():
    _sem_erros("START\n(3 4 *)\nEND\n")

def test_real_vezes_real_valido():
    _sem_erros("START\n(3.0 4.0 *)\nEND\n")

def test_real_vezes_int_gera_erro():
    _com_erro("START\n(3.0 4 *)\nEND\n", tipo_erro="tipo_incompativel")

##
#  Divisão 
# / e | são operadores distintos com regras distintas:
#   /  — divisão real: exige real×real, retorna real (IEEE 754 puro)
#   |  — divisão inteira: exige int×int, retorna int (equivale ao // do Python)
#   %  — resto: exige int×int, retorna int (módulo inteiro)
def test_divisao_real_real_valida():
    _sem_erros("START\n(3.0 2.0 /)\nEND\n")

def test_divisao_int_int_gera_erro():
    # / exige real×real — int/int é erro porque não há coerção implícita
    _com_erro("START\n(3 2 /)\nEND\n", tipo_erro="tipo_incompativel")

def test_divisao_int_real_gera_erro():
    _com_erro("START\n(3 2.0 /)\nEND\n", tipo_erro="tipo_incompativel")

def test_divisao_inteira_int_int_valida():
    _sem_erros("START\n(10 3 |)\nEND\n")

def test_divisao_inteira_real_gera_erro():
    _com_erro("START\n(3.0 2.0 |)\nEND\n", tipo_erro="tipo_incompativel")

def test_divisao_inteira_int_real_gera_erro():
    _com_erro("START\n(3 2.0 |)\nEND\n", tipo_erro="tipo_incompativel")

##
#  Resto 
def test_resto_int_int_valido():
    _sem_erros("START\n(10 3 %)\nEND\n")

def test_resto_real_gera_erro():
    _com_erro("START\n(3.0 2.0 %)\nEND\n", tipo_erro="tipo_incompativel")

def test_resto_int_real_gera_erro():
    _com_erro("START\n(3 2.0 %)\nEND\n", tipo_erro="tipo_incompativel")

##
#  Potenciação 
def test_potencia_int_int_valido():
    _sem_erros("START\n(2 3 ^)\nEND\n")

def test_potencia_real_real_valido():
    _sem_erros("START\n(2.0 3.0 ^)\nEND\n")

def test_potencia_int_real_gera_erro():
    _com_erro("START\n(2 3.0 ^)\nEND\n", tipo_erro="tipo_incompativel")

##
#  Operadores relacionais 
# Relacionais (<, >, =, <=, >=, !=) sempre retornam bool.
# Os dois operandos precisam ser do mesmo tipo — comparar int com real é erro
# pela mesma razão que soma: sem coerção implícita.
def test_int_menor_int_retorna_bool():
    _sem_erros("START\n(1 2 <)\nEND\n")

def test_real_menor_real_retorna_bool():
    _sem_erros("START\n(1.0 2.0 <)\nEND\n")

def test_int_igual_int_retorna_bool():
    _sem_erros("START\n(1 1 =)\nEND\n")

def test_int_diferente_int():
    _sem_erros("START\n(1 2 !=)\nEND\n")

def test_todos_relacionais_int():
    # Todos os seis operadores relacionais devem aceitar int×int sem erro
    for op in ["<", ">", "=", "<=", ">=", "!="]:
        _sem_erros(f"START\n(1 2 {op})\nEND\n")

def test_relacional_int_real_gera_erro():
    _com_erro("START\n(1 2.0 <)\nEND\n", tipo_erro="tipo_incompativel")

##
#  Operadores lógicos 
# AND, OR exigem bool×bool. NOT exige bool.
# Passar int ou real para AND/OR é erro de tipo — booleano não é int nesta linguagem.
def test_bool_and_bool_valido():
    _sem_erros("START\n((1 2 <) (3 4 <) AND)\nEND\n")

def test_bool_or_bool_valido():
    _sem_erros("START\n((1 1 =) (2 2 =) OR)\nEND\n")

def test_int_and_int_gera_erro():
    _com_erro("START\n(3 4 AND)\nEND\n", tipo_erro="tipo_incompativel")

def test_real_or_real_gera_erro():
    _com_erro("START\n(3.0 4.0 OR)\nEND\n", tipo_erro="tipo_incompativel")

##
#  Estruturas de controle 
# A condição de IF e WHILE deve ser bool — qualquer outro tipo é erro semântico.
# Isso garante que o branch ARM gerado é sempre baseado em uma comparação booleana.
def test_if_condicao_bool_valido():
    _sem_erros("START\nIF (1 1 =) THEN\n(1 X)\nEND IF\nEND\n")

def test_if_condicao_int_gera_erro():
    _com_erro(
        "START\nIF (3 4 +) THEN\n(1 X)\nEND IF\nEND\n",
        tipo_erro="condicao_nao_bool",
        trecho="bool",
    )

def test_if_condicao_real_gera_erro():
    _com_erro(
        "START\nIF (3.0 4.0 +) THEN\n(1 X)\nEND IF\nEND\n",
        tipo_erro="condicao_nao_bool",
    )

def test_if_else_valido():
    _sem_erros(
        "START\nIF (1 2 <) THEN\n(1 X)\nELSE\n(2 X)\nEND IF\nEND\n"
    )

def test_while_condicao_bool_valido():
    _sem_erros("START\n(0 C)\nWHILE (C 10 <) DO\n(1 C)\nEND WHILE\nEND\n")

def test_while_condicao_int_gera_erro():
    _com_erro(
        "START\nWHILE (3 4 +) DO\n(1 X)\nEND WHILE\nEND\n",
        tipo_erro="condicao_nao_bool",
    )

def test_if_aninhado_valido():
    _sem_erros(
        "START\n"
        "IF (1 1 =) THEN\n"
        "  IF (2 2 =) THEN\n"
        "    (1 X)\n"
        "  END IF\n"
        "END IF\n"
        "END\n"
    )

#  (N RES) 
# (N RES) acessa o N-ésimo resultado anterior na sequência atual.
# O tipo inferido é o tipo do resultado que foi produzido naquele passo.
def test_n_res_1_tipo_int():
    _sem_erros("START\n(3 4 +)\n(1 RES)\nEND\n")

def test_n_res_1_tipo_real():
    _sem_erros("START\n(3.0 4.0 +)\n(1 RES)\nEND\n")

def test_n_res_usado_em_expressao():
    _sem_erros("START\n(3 4 +)\n((1 RES) 2 +)\nEND\n")

def test_n_res_n_zero_gera_erro():
    _com_erro("START\n(0 RES)\nEND\n", tipo_erro="n_res_invalido")

def test_n_res_fora_de_alcance_gera_erro():
    _com_erro("START\n(3 4 +)\n(5 RES)\nEND\n", tipo_erro="n_res_fora_de_alcance")

def test_n_res_2_com_dois_anteriores():
    _sem_erros("START\n(1 2 +)\n(3 4 +)\n(2 RES)\nEND\n")

##
#  Variáveis 
# O tipo da variável é fixado na primeira declaração — reatribuição com tipo
def test_var_int_em_expressao():
    _sem_erros("START\n(3 X)\n(X 2 +)\nEND\n")

def test_var_real_em_expressao():
    _sem_erros("START\n(3.14 PI)\n(PI 2.0 *)\nEND\n")

def test_redef_tipo_incompativel_gera_erro():
    _com_erro("START\n(3 X)\n(3.14 X)\nEND\n", tipo_erro="tipo_incompativel")

def test_multiplos_erros_coletados():
    _, erros = _pipeline("START\n(3 3.14 +)\n(3.0 2.0 |)\nEND\n")
    assert len(erros) >= 2, f"Esperava ≥2 erros, got {len(erros)}"

def test_erros_incluem_numero_de_linha():
    _, erros = _pipeline("START\n(3 3.14 +)\nEND\n")
    assert erros[0]["linha"] == 2

def test_mensagem_erro_inclui_tipos():
    _, erros = _pipeline("START\n(3 3.14 +)\nEND\n")
    msg = erros[0]["mensagem"]
    assert "int" in msg and "real" in msg, f"Mensagem deve mencionar tipos: '{msg}'"
