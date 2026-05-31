# Integrante do grupo:
# Mariana Alves da Silva - @himarialves

# Nome do grupo no Canvas: RA3_15

# Professor Frank Coelho de Alcantara 
# Projeto acadêmico para a disciplina Linguagens Formais e Compiladores (2026-1).
# Instituição:  Pontifícia Universidade Católica do Paraná - PUC/PR — 2026-1

from __future__ import annotations
import os
import subprocess
import sys
import tempfile

import pytest

from lexer import prepararEntradaSemantica, _tokenizar

# Helpers 
# _compilar  ->  caminho feliz: compila e devolve (tokens, arvore)
# _tipos     ->  atalho pra comparar só os tipos sem ruído
# _roda_erro -> caminho de erro: precisa de subprocess por causa do sys.exit

def _compilar(codigo: str):
    # Escreve o código num arquivo temporário e chama o pipeline real.
    # O finally garante limpeza do arquivo mesmo se prepararEntradaSemantica explodir.
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt",
                                     delete=False, encoding="utf-8") as f:
        f.write(codigo)
        path = f.name
    try:
        return prepararEntradaSemantica(path)
    finally:
        os.unlink(path)

def _tipos(tokens) -> list[str]:
    # utilitário de teste — extrai só os tipos para comparações mais legíveis
    return [t["tipo"] for t in tokens]


def _roda_erro(codigo: str) -> str:
    # Roda o compilador num subprocesso separado porque prepararEntradaSemantica()
    # chama sys.exit(1) em erro.
    # Subprocess isola completamente e nos deixa checar returncode + stderr.
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt",
                                     delete=False, encoding="utf-8") as f:
        f.write(codigo)
        path = f.name
    result = subprocess.run(
        [sys.executable, "-c",
         f'from lexer import prepararEntradaSemantica; '
         f'prepararEntradaSemantica(r"{path}")'],
        capture_output=True, text=True,
    )
    os.unlink(path)
    assert result.returncode != 0, "Esperava falha, mas compilador saiu com sucesso"
    assert result.stderr, "Compilador falhou mas não escreveu nada no stderr"
    return result.stderr

#  Comentários 
# Comentários *{ }* são reconhecidos como tokens COMENTARIO pelo lexer mas
# descartados por prepararEntradaSemantica antes do parser.
# Essa separação foi uma decisão deliberada: se ignorássemos direto na regex,
# não teria como testar o reconhecimento de *{ }* sem rodar o pipeline inteiro.
# test_comentario_incluido_antes_de_filtrar testa _tokenizar() diretamente
# pra documentar esse comportamento de duas fases.

def test_comentario_linha_inteira_descartado():
    tokens, _ = _compilar("START\n*{ isto é um comentário }*\n(3 4 +)\nEND\n")
    assert "COMENTARIO" not in _tipos(tokens), \
        "Token COMENTARIO não deve aparecer na lista filtrada"

def test_comentario_apos_expressao_descartado():
    tokens, _ = _compilar("START\n(3 4 +) *{ resultado }*\nEND\n")
    assert "COMENTARIO" not in _tipos(tokens)

def test_comentario_multilinhas_descartado():
    tokens, _ = _compilar("START\n*{ linha 1\nlinha 2\nlinha 3 }*\n(1 2 +)\nEND\n")
    assert "COMENTARIO" not in _tipos(tokens)

def test_comentario_incluido_antes_de_filtrar():
    # Chama _tokenizar() diretamente — não prepararEntradaSemantica() — pra
    # verificar que o COMENTARIO existe na lista bruta antes da filtragem.
    # Esse teste documenta a separação de responsabilidades entre as duas funções.
    todos, erros = _tokenizar("START\n*{ comentário }*\n(3 4 +)\nEND\n")
    assert erros == []
    assert any(t["tipo"] == "COMENTARIO" for t in todos)

def test_comentario_nao_afeta_contagem_de_tokens():
    tokens_com, _ = _compilar("START\n*{ x }*\n(3 4 +)\nEND\n")
    tokens_sem, _ = _compilar("START\n(3 4 +)\nEND\n")
    assert len(tokens_com) == len(tokens_sem)
    
# # 
# Detecção de erros léxicos 
# Qualquer caractere que não case com nenhum padrão vira DESCONHECIDO e gera erro.
# O lexer coleta todos os erros antes de parar (não falha no primeiro símbolo
# inválido) e cada mensagem cita linha + símbolo — os dois testes abaixo
# verificam exatamente isso.

def test_token_invalido_reporta_linha():
    stderr = _roda_erro("START\n@ invalido\nEND\n")
    assert "2" in stderr, "Mensagem de erro deve mencionar a linha 2"
    assert "@" in stderr or "inválido" in stderr.lower()

def test_token_invalido_cifrao():
    stderr = _roda_erro("START\n(3 $ 4 +)\nEND\n")
    assert "$" in stderr or "inválido" in stderr.lower()

##

# Validação de estrutura (START / END) 
# START e END são obrigatórios. A checagem acontece em prepararEntradaSemantica,
# depois da tokenização mas antes do parser — falha rápida com mensagem clara,
# sem tentar parsear um programa que já sabemos que está incompleto.

def test_programa_sem_start_gera_erro():
    stderr = _roda_erro("(3 4 +)\nEND\n")
    assert "START" in stderr

def test_programa_sem_end_gera_erro():
    stderr = _roda_erro("START\n(3 4 +)\n")
    assert "END" in stderr or "fim" in stderr.lower()

##

# Reconhecimento de tokens 

# Cobrimos todos os tipos definidos em CONTRACTS.py: inteiros, reais, bools,
# keywords, os 7 operadores aritméticos, os 6 relacionais, os lógicos,
# identificadores e RES.
#
# Literais negativos são testados explicitamente porque -3.14 poderia ser
# tokenizado como INTEIRO(-3) + REAL(.14) se a ordem dos padrões no lexer
# estivesse errada. 

def test_literais_inteiros_reconhecidos():
    tokens, _ = _compilar("START\n(3 42 +)\nEND\n")
    assert _tipos(tokens).count("INTEIRO") >= 2

def test_literal_inteiro_negativo():
    tokens, _ = _compilar("START\n(-1 5 +)\nEND\n")
    assert any(t["tipo"] == "INTEIRO" and t["valor"] == "-1" for t in tokens)

def test_literais_reais_reconhecidos():
    tokens, _ = _compilar("START\n(3.14 2.0 +)\nEND\n")
    assert "REAL" in _tipos(tokens)

def test_literal_real_negativo():
    tokens, _ = _compilar("START\n(-3.14 2.0 +)\nEND\n")
    assert any(t["tipo"] == "REAL" and t["valor"] == "-3.14" for t in tokens)

def test_keywords_reconhecidas():
    tokens, _ = _compilar("START\nIF (1 1 =) THEN\n(1 X)\nEND IF\nEND\n")
    tipos = _tipos(tokens)
    assert "IF" in tipos
    assert "THEN" in tipos
    assert "END" in tipos

def test_while_do_reconhecidos():
    tokens, _ = _compilar("START\n(0 C)\nWHILE (C 5 <) DO\n(1 C)\nEND WHILE\nEND\n")
    tipos = _tipos(tokens)
    assert "WHILE" in tipos
    assert "DO" in tipos

def test_operadores_aritmeticos_reconhecidos():
    # Um operador por linha pra cobrir todos de uma vez.
    # A mensagem de erro mostra exatamente qual operador falta ou sobra.
    tokens, _ = _compilar("START\n(3 4 +)\n(3 4 -)\n(3 4 *)\n(3.0 4.0 /)\n(3 4 |)\n(3 4 %)\n(2 3 ^)\nEND\n")
    valores_op = {t["valor"] for t in tokens if t["tipo"] == "OP_ARIT"}
    assert valores_op == {"+", "-", "*", "/", "|", "%", "^"}, \
        f"Operadores faltando ou extras — esperado: {{+,-,*,/,|,%,^}}, encontrado: {valores_op}"

def test_operadores_relacionais_reconhecidos():
    # OP_REL multi-char (<=, >=, !=) devem ser tokenizados como um único token,
    # não como dois. Isso depende da ordem dos padrões na regex (multi antes de single).
    tokens, _ = _compilar("START\n(1 2 <)\n(1 2 >)\n(1 1 =)\n(1 2 <=)\n(2 1 >=)\n(1 2 !=)\nEND\n")
    valores_op = {t["valor"] for t in tokens if t["tipo"] == "OP_REL"}
    assert valores_op == {"<", ">", "=", "<=", ">=", "!="}, \
        f"Operadores relacionais faltando ou extras — esperado: {{<,>,=,<=,>=,!=}}, encontrado: {valores_op}"

def test_operadores_logicos_reconhecidos():
    tokens, _ = _compilar("START\n(1 1 = 2 2 = AND)\n(1 1 = 2 3 = OR)\nEND\n")
    tipos = _tipos(tokens)
    assert "OP_LOG" in tipos

def test_res_reconhecido_como_keyword():
    tokens, _ = _compilar("START\n(3 4 +)\n(1 RES)\nEND\n")
    assert any(t["tipo"] == "RES" for t in tokens)

def test_ident_maiusculo_reconhecido():
    tokens, _ = _compilar("START\n(3 MEU_VAR)\nEND\n")
    assert any(t["tipo"] == "IDENT" and t["valor"] == "MEU_VAR" for t in tokens)

##
# Numeração de linhas 
# O campo "linha" do Token é fundamental para mensagens de erro úteis nos
# módulos 2 e 3. Testamos o caso normal e o caso com comentário multilinhas
# porque o lexer precisa contar os \n dentro de *{ }*.

def test_numero_linha_correto():
    tokens, _ = _compilar("START\n(3 4 +)\n(10 X)\nEND\n")
    tok_10 = next(t for t in tokens if t["valor"] == "10")
    assert tok_10["linha"] == 3, f"Esperado linha 3, got {tok_10['linha']}"

def test_numero_linha_apos_comentario():
    # Comentário ocupa uma linha mas não pode "engolir" a numeração das seguintes.
    # O lexer precisa contar os \n dentro de *{...}* corretamente.
    tokens, _ = _compilar("START\n*{ comentario }*\n(5 X)\nEND\n")
    tok_5 = next(t for t in tokens if t["valor"] == "5")
    assert tok_5["linha"] == 3, f"Esperado linha 3, got {tok_5['linha']}"

# Estrutura da árvore sintática 
# Aqui testamos o contrato do parser: que tipo de nó ele produz, quantos filhos
# tem cada estrutura, e que o valor do nó carrega o lexema correto.

def test_arvore_raiz_e_programa():
    _, arvore = _compilar("START\n(3 4 +)\nEND\n")
    assert arvore["tipo"] == "programa"

def test_expressao_simples_gera_expressao_rpn():
    _, arvore = _compilar("START\n(3 4 +)\nEND\n")
    filho = arvore["filhos"][0]
    assert filho["tipo"] == "expressao_rpn"
    assert filho["valor"] == "+"

def test_atribuicao_gera_no_correto():
    _, arvore = _compilar("START\n(3 X)\nEND\n")
    filho = arvore["filhos"][0]
    assert filho["tipo"] == "atribuicao"
    assert filho["valor"] == "X"

def test_leitura_variavel_gera_no_correto():
    _, arvore = _compilar("START\n(3 X)\n(X)\nEND\n")
    assert arvore["filhos"][1]["tipo"] == "variavel"
    assert arvore["filhos"][1]["valor"] == "X"

def test_n_res_gera_no_correto():
    _, arvore = _compilar("START\n(3 4 +)\n(1 RES)\nEND\n")
    no_res = arvore["filhos"][1]
    assert no_res["tipo"] == "n_res"
    assert no_res["valor"] == "1"

def test_if_tem_tres_filhos():
    # A estrutura do nó IF é sempre [condicao, bloco_then, bloco_else].
    # O bloco_else existe mesmo quando não há ELSE — fica com filhos=[].
    _, arvore = _compilar("START\nIF (1 1 =) THEN\n(1 X)\nEND IF\nEND\n")
    no_if = arvore["filhos"][0]
    assert no_if["tipo"] == "if"
    assert len(no_if["filhos"]) == 3

def test_if_condicao_e_expressao_rpn():
    _, arvore = _compilar("START\nIF (1 1 =) THEN\n(1 X)\nEND IF\nEND\n")
    condicao = arvore["filhos"][0]["filhos"][0]
    assert condicao["tipo"] == "expressao_rpn"
    assert condicao["valor"] == "="

def test_while_tem_dois_filhos():
    # WHILE só tem dois filhos: [condicao, bloco_corpo].
    # Simétrico ao IF, mas sem o bloco_else.
    _, arvore = _compilar("START\n(0 C)\nWHILE (C 5 <) DO\n(1 C)\nEND WHILE\nEND\n")
    no_while = arvore["filhos"][1]
    assert no_while["tipo"] == "while"
    assert len(no_while["filhos"]) == 2

def test_expressao_aninhada_3_niveis():
    # ((3 4 +) (2 5 *) -) — duas subexpressões como operandos de outro operador.
    # Testa que o parser recursivo monta a árvore corretamente em 3 níveis.
    _, arvore = _compilar("START\n((3 4 +) (2 5 *) -)\nEND\n")
    raiz = arvore["filhos"][0]
    assert raiz["tipo"] == "expressao_rpn"
    assert raiz["valor"] == "-"
    assert raiz["filhos"][0]["tipo"] == "expressao_rpn"
    assert raiz["filhos"][0]["valor"] == "+"
    assert raiz["filhos"][1]["tipo"] == "expressao_rpn"
    assert raiz["filhos"][1]["valor"] == "*"

def test_if_aninhado():
    # IF dentro de THEN — verifica que o parser não confunde os END IF de cada nível.
    codigo = "START\nIF (1 1 =) THEN\n  IF (2 2 =) THEN\n    (1 X)\n  END IF\nEND IF\nEND\n"
    _, arvore = _compilar(codigo)
    no_if_externo = arvore["filhos"][0]
    assert no_if_externo["tipo"] == "if"
    bloco_then = no_if_externo["filhos"][1]
    no_if_interno = bloco_then["filhos"][0]
    assert no_if_interno["tipo"] == "if"