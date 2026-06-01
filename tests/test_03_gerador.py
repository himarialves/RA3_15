# Integrante do grupo:
# Mariana Alves da Silva - @himarialves
#
# Nome do grupo no Canvas: RA3_15
#
# Professor Frank Coelho de Alcantara
# Projeto acadêmico para a disciplina Linguagens Formais e Compiladores (2026-1).
# Instituição: Pontifícia Universidade Católica do Paraná - PUC/PR — 2026-1

'''
test_03_gerador.py — Testes do gerador de Assembly (Módulo 4).

Valida o texto do Assembly gerado *sem* abrir o CPulator.
Estratégia F64 unificada: todos os valores em registradores D (VFP double 64 bits).

Filosofia dos testes:
#   Não verificamos a semântica de execução (isso é trabalho do CPulator).
#   Verificamos se as instruções e estruturas certas estão presentes no texto
#   gerado — se o VFP está habilitado, se as variáveis estão em .data, se os
#   labels são únicos, se os operadores geram as instruções esperadas.

'''

from __future__ import annotations
import os
import re
import tempfile

import pytest

from lexer import prepararEntradaSemantica
from tabela_simbolos import construirTabelaSimbolos
from verificar_tipos import verificarTipos
from gerador import gerarArvoreAtribuida, gerarAssembly

##
#  Helper 
def _pipeline(codigo: str) -> dict:
    # Executa o pipeline completo e retorna dict com erros e assembly.
    # assembly é None quando há erros semânticos — isso é testado explicitamente
    # na seção "Ausência de assembly com erros semânticos".
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt",
                                     delete=False, encoding="utf-8") as f:
        f.write(codigo)
        path = f.name
    try:
        tokens, arvore = prepararEntradaSemantica(path)
        tabela, erros_decl = construirTabelaSimbolos(arvore)
        tipos, erros_tipo = verificarTipos(arvore, tabela)
        erros = erros_decl + erros_tipo
        arvore_atrib = gerarArvoreAtribuida(arvore, tabela, tipos)
        assembly = gerarAssembly(arvore_atrib) if not erros else None
        return {"erros": erros, "assembly": assembly, "arvore_atrib": arvore_atrib}
    finally:
        os.unlink(path)


def _asm(codigo: str) -> str:
    # Atalho para testes que precisam do Assembly sem erros.
    # Falha o teste imediatamente se houver erros semânticos inesperados.
    r = _pipeline(codigo)
    assert not r["erros"], f"Erros inesperados: {[e['mensagem'] for e in r['erros']]}"
    assert r["assembly"] is not None
    return r["assembly"]


##
# Estrutura obrigatória
# Todo Assembly gerado deve ter essas seções e inicializações.
# O CPulator não inicializa SP nem VFP automaticamente — sem esses blocos
# qualquer instrução de pilha ou ponto flutuante causaria crash.
def test_assembly_tem_secao_data():
    a = _asm("START\n(3 4 +)\nEND\n")
    assert ".data" in a

def test_assembly_tem_secao_text():
    a = _asm("START\n(3 4 +)\nEND\n")
    assert ".text" in a

def test_data_antes_de_text():
    a = _asm("START\n(3 4 +)\nEND\n")
    assert a.index(".data") < a.index(".text")

def test_assembly_tem_start():
    a = _asm("START\n(3 4 +)\nEND\n")
    assert "_start:" in a

def test_assembly_tem_halt():
    a = _asm("START\n(3 4 +)\nEND\n")
    assert "_end:" in a and "B _end" in a

def test_inicializa_stack_pointer():
    a = _asm("START\n(3 4 +)\nEND\n")
    assert "LDR SP, =STACK_TOP" in a

def test_habilita_vfp():
    # VMSR é a sintaxe UAL correta para ARMv7 — FMXR é pré-UAL e causa exceção no CPulator
    a = _asm("START\n(3 4 +)\nEND\n")
    assert "VMSR FPEXC" in a

def test_inicializa_res_idx():
    a = _asm("START\n(3 4 +)\nEND\n")
    assert "RES_IDX" in a
    assert "RES_HIST" in a

def test_stack_top_declarado_em_data():
    a = _asm("START\n(3 4 +)\nEND\n")
    assert "STACK_TOP" in a
    assert "STACK: .space" in a

def test_const_zero_e_const_one_em_data():
    a = _asm("START\n(3 4 +)\nEND\n")
    assert "CONST_ZERO: .double 0.0" in a
    assert "CONST_ONE:  .double 1.0" in a

## 
# Operadores aritméticos (estratégia F64 unificada)
# + → VADD.F64, - → VSUB.F64, * → VMUL.F64 (instruções VFP nativas).
# / | % ^ → loops de subtração/multiplicação (VDIV não suportado no CPulator).
# VPUSH/VPOP
def test_soma_int_gera_vadd_f64():
    a = _asm("START\n(3 4 +)\nEND\n")
    assert "VADD.F64" in a

def test_subtracao_int_gera_vsub_f64():
    a = _asm("START\n(10 3 -)\nEND\n")
    assert "VSUB.F64" in a

def test_multiplicacao_int_gera_vmul_f64():
    a = _asm("START\n(3 4 *)\nEND\n")
    assert "VMUL.F64" in a

def test_divisao_real_usa_loop_subtracao():
    # / usa loop de subtração F64 (VDIV não suportado no CPulator DEC1-SOC)
    a = _asm("START\n(3.0 2.0 /)\nEND\n")
    assert "DIV_LOOP" in a
    assert "DIV_FIM" in a
    assert "VSUB.F64" in a

def test_divisao_inteira_usa_loop_subtracao():
    # | usa mesmo loop de subtração F64 que /
    a = _asm("START\n(10 3 |)\nEND\n")
    assert "DIV_LOOP" in a
    assert "VSUB.F64" in a

def test_resto_usa_loop_subtracao():
    # % usa loop de subtração F64 — o resultado é o que sobrou em D2
    a = _asm("START\n(10 3 %)\nEND\n")
    assert "MOD_LOOP" in a
    assert "MOD_FIM" in a
    assert "VSUB.F64" in a

def test_potencia_usa_loop_multiplicacao():
    # ^ usa loop de multiplicação F64 — decrementa expoente a cada iteração
    a = _asm("START\n(2 3 ^)\nEND\n")
    assert "POT_LOOP" in a
    assert "POT_FIM" in a
    assert "VMUL.F64" in a

def test_soma_real_gera_vadd_f64():
    a = _asm("START\n(1.5 2.5 +)\nEND\n")
    assert "VADD.F64" in a

def test_operacao_usa_vpush_vpop_para_pilha():
    # Operandos intermediários são preservados via VPUSH/VPOP na pilha ARM
    a = _asm("START\n(3 4 +)\nEND\n")
    assert "VPUSH {D0}" in a
    assert "VPOP {D1}" in a


##
# Operadores relacionais
# Relacionais comparam D1 (esq) e D0 (dir) via VCMP.F64.
# VMRS copia as flags VFP para APSR para que as instruções B* possam lê-las.
# Resultado: D0 = CONST_ONE (true) ou CONST_ZERO (false) via VLDR.
def test_menor_gera_vcmp_e_blt():
    a = _asm("START\n(1 2 <)\nEND\n")
    assert "VCMP.F64 D1, D0" in a
    assert "BLT" in a

def test_maior_gera_bgt():
    a = _asm("START\n(2 1 >)\nEND\n")
    assert "BGT" in a

def test_igual_gera_beq():
    a = _asm("START\n(1 1 =)\nEND\n")
    assert "BEQ" in a

def test_diferente_gera_bne():
    a = _asm("START\n(1 2 !=)\nEND\n")
    assert "BNE" in a

def test_relacional_carrega_const_zero_ou_const_one():
    # Resultado bool armazenado como 0.0 ou 1.0 — mesma representação que o resto da linguagem
    a = _asm("START\n(1 2 <)\nEND\n")
    assert "CONST_ZERO" in a
    assert "CONST_ONE" in a
    assert "VMRS APSR_nzcv, FPSCR" in a


##
# Operadores lógicos
def test_and_verifica_dois_operandos():
    a = _asm("START\n((1 2 <) (3 4 <) AND)\nEND\n")
    assert "AND" in a
    assert "CONST_ZERO" in a
    assert "CONST_ONE" in a

def test_or_usa_bne():
    a = _asm("START\n((1 1 =) (2 2 =) OR)\nEND\n")
    assert "BNE" in a

def test_not_usa_beq():
    a = _asm("START\n((1 2 <) NOT)\nEND\n")
    assert "NOT" in a
    assert "VCMP.F64 D0, #0.0" in a


##
# Variáveis: declaração, leitura e escrita
# Cada variável vira uma entrada .double 0.0 em .data — inicializada em zero
# e sobrescrita pela primeira atribuição (V MEM).
# Leitura (MEM) usa VLDR; escrita (V MEM) usa VSTR.
def test_variavel_declarada_em_data_como_double():
    a = _asm("START\n(3 X)\nEND\n")
    assert "X: .double 0.0" in a

def test_atribuicao_usa_vstr():
    # (V MEM) deve usar VSTR para salvar F64 na posição de memória
    a = _asm("START\n(42 X)\nEND\n")
    assert "VSTR D0, [R1]" in a

def test_leitura_variavel_usa_vldr():
    # (MEM) deve usar VLDR para carregar F64 da posição de memória
    a = _asm("START\n(3 X)\n(X)\nEND\n")
    assert "VLDR D0, [R1]" in a

def test_multiplas_variaveis_declaradas_em_data():
    a = _asm("START\n(1 A)\n(2 B)\n(3 C)\nEND\n")
    assert "A: .double 0.0" in a
    assert "B: .double 0.0" in a
    assert "C: .double 0.0" in a

def test_variaveis_ordenadas_alfabeticamente_em_data():
    # Variáveis são listadas em ordem alfabética — garante saída reprodutível
    a = _asm("START\n(1 Z)\n(2 A)\nEND\n")
    idx_a = a.index("A: .double")
    idx_z = a.index("Z: .double")
    assert idx_a < idx_z


##
# Literais
# Inteiros pequenos (0–255) usam MOV imediato; maiores usam LDR pseudo-instrução.
# Todo inteiro passa por VMOV S0 + VCVT.F64.S32 para chegar em D0 como F64.
# Floats geram labels FC_* em .data e são carregados com VLDR.
def test_literal_int_pequeno_usa_mov():
    # Inteiros 0–255 usam MOV R0, #n (instrução mais curta, sem acesso a .data)
    a = _asm("START\n(7 X)\nEND\n")
    assert "MOV R0, #7" in a

def test_literal_int_grande_usa_ldr():
    # Inteiros > 255 usam LDR R0, =n (pseudo-instrução, assembler cria literal pool)
    a = _asm("START\n(1000 X)\nEND\n")
    assert "LDR R0, =1000" in a

def test_literal_int_promovido_para_f64():
    # Todo inteiro passa por VMOV S0 + VCVT para chegar em D0 como F64
    a = _asm("START\n(5 X)\nEND\n")
    assert "VMOV S0, R0" in a
    assert "VCVT.F64.S32 D0, S0" in a

def test_literal_real_declarado_em_data():
    # Floats geram label FC_* em .data como .double
    a = _asm("START\n(3.14 X)\nEND\n")
    assert ".double 3.14" in a

def test_literal_real_carregado_com_vldr():
    # Floats são carregados com LDR R6, =FC_...; VLDR D0, [R6]
    a = _asm("START\n(3.14 X)\nEND\n")
    assert "VLDR D0, [R6]" in a
    assert "FC_3_14" in a or "FC_3" in a

def test_literal_bool_true_carrega_const_one():
    a = _asm("START\n(TRUE X)\nEND\n")
    assert "CONST_ONE" in a

def test_literal_bool_false_carrega_const_zero():
    a = _asm("START\n(FALSE X)\nEND\n")
    assert "CONST_ZERO" in a


##
# (N RES) — histórico de resultados
# RES_IDX aponta para o próximo slot livre. (N RES) acessa RES_HIST[RES_IDX - N].
# O shift LSL #3 converte índice em offset de bytes (× 8, pois cada entrada é F64).
def test_n_res_usa_res_hist():
    a = _asm("START\n(3 4 +)\n(1 RES)\nEND\n")
    assert "RES_HIST" in a
    assert "RES_IDX" in a

def test_n_res_subtrai_n_do_indice():
    # (1 RES) deve gerar SUB R2, R2, #1 para acessar o último resultado
    a = _asm("START\n(3 4 +)\n(1 RES)\nEND\n")
    assert "SUB R2, R2, #1" in a

def test_n_res_2_subtrai_2():
    a = _asm("START\n(1 2 +)\n(3 4 +)\n(2 RES)\nEND\n")
    assert "SUB R2, R2, #2" in a

def test_expressoes_salvas_em_res_hist():
    # Expressões de topo salvam resultado em RES_HIST via VSTR e incrementam RES_IDX
    a = _asm("START\n(3 4 +)\nEND\n")
    assert "VSTR D0, [R6]" in a
    assert "ADD R2, R2, #1" in a


##
# IF — estrutura de desvio condicional
# Condição em D0 como F64: 0.0 = false, qualquer outro = true.
# BEQ pula o THEN quando D0 == 0.0 (comparado via VCMP.F64 D0, #0.0).
# IF com ELSE tem branch incondicional B label_fim após o THEN para pular o ELSE.
def test_if_simples_tem_label_fim():
    a = _asm("START\nIF (1 1 =) THEN\n(1 X)\nEND IF\nEND\n")
    assert re.search(r"IF_FIM_\d+:", a)

def test_if_usa_beq_para_pular_then():
    # Condição falsa (D0 == 0.0) → BEQ pula o bloco THEN
    a = _asm("START\nIF (1 1 =) THEN\n(1 X)\nEND IF\nEND\n")
    assert "VCMP.F64 D0, #0.0" in a
    assert re.search(r"BEQ\s+IF_FIM_\d+|BEQ\s+ELSE_\d+", a)

def test_if_else_tem_branch_incondicional():
    # Após o bloco THEN, deve ter B label_fim para pular o bloco ELSE
    a = _asm("START\nIF (1 2 <) THEN\n(1 X)\nELSE\n(0 X)\nEND IF\nEND\n")
    assert re.search(r"ELSE_\d+:", a)
    assert re.search(r"IF_FIM_\d+:", a)
    assert re.search(r"\bB\s+IF_FIM_\d+", a)

def test_if_aninhado_labels_unicos():
    # Dois IFs aninhados não podem compartilhar labels — o contador global evita isso
    codigo = (
        "START\n"
        "IF (1 1 =) THEN\n"
        "  IF (2 2 =) THEN\n"
        "    (1 X)\n"
        "  END IF\n"
        "END IF\n"
        "END\n"
    )
    a = _asm(codigo)
    labels = re.findall(r"(\w+_\d+):", a)
    duplicados = [l for l in labels if labels.count(l) > 1]
    assert not duplicados, f"Labels duplicados: {duplicados}"


##
# WHILE — estrutura de repetição
# Loop: avalia condição → BEQ sai se false → executa corpo → B volta ao início.
# Dois WHILEs independentes devem ter labels distintos.
def test_while_tem_label_loop_e_saida():
    codigo = "START\n(0 C)\nWHILE (C 10 <) DO\n(1 C)\nEND WHILE\nEND\n"
    a = _asm(codigo)
    assert re.search(r"WHILE_\d+:", a)
    assert re.search(r"WHILE_FIM_\d+:", a)

def test_while_avalia_condicao_com_vcmp():
    codigo = "START\n(0 C)\nWHILE (C 5 <) DO\n(1 C)\nEND WHILE\nEND\n"
    a = _asm(codigo)
    assert "VCMP.F64 D0, #0.0" in a

def test_while_tem_branch_de_volta():
    # Loop WHILE deve ter B incondicional de volta ao rótulo de início
    codigo = "START\n(0 C)\nWHILE (C 3 <) DO\n(1 C)\nEND WHILE\nEND\n"
    a = _asm(codigo)
    assert re.search(r"\bB\s+WHILE_\d+", a)

def test_while_sai_com_beq():
    # WHILE sai quando condição é falsa (D0 == 0.0) via BEQ para WHILE_FIM
    codigo = "START\n(0 C)\nWHILE (C 3 <) DO\n(1 C)\nEND WHILE\nEND\n"
    a = _asm(codigo)
    assert re.search(r"BEQ\s+WHILE_FIM_\d+", a)

def test_dois_whiles_labels_unicos():
    codigo = (
        "START\n"
        "(0 A)\n(0 B)\n"
        "WHILE (A 3 <) DO\n(1 A)\nEND WHILE\n"
        "WHILE (B 5 <) DO\n(1 B)\nEND WHILE\n"
        "END\n"
    )
    a = _asm(codigo)
    labels = re.findall(r"(\w+_\d+):", a)
    duplicados = [l for l in labels if labels.count(l) > 1]
    assert not duplicados, f"Labels duplicados: {duplicados}"


##
# Aninhamento e expressões compostas
##
def test_expressao_aninhada_gera_todas_operacoes():
    # ((3 4 +) (2 5 *) -) deve gerar VADD, VMUL e VSUB
    a = _asm("START\n((3 4 +) (2 5 *) -)\nEND\n")
    assert "VADD.F64" in a
    assert "VMUL.F64" in a
    assert "VSUB.F64" in a

def test_condicao_aninhada_em_if():
    # IF ((A B =) (C D =) AND) — condição lógica composta deve funcionar
    a = _asm(
        "START\n(1 A)\n(1 B)\n(2 C)\n(2 D)\n"
        "IF ((A B =) (C D =) AND) THEN\n(1 R)\nEND IF\nEND\n"
    )
    assert "AND" in a
    assert "VCMP.F64 D0, #0.0" in a


##
# Ausência de assembly com erros semânticos
# Assembly não deve ser gerado quando há erros — código incorreto é pior que nenhum.
def test_erro_semantico_nao_gera_assembly():
    r = _pipeline("START\n(3 3.14 +)\nEND\n")
    assert r["erros"], "Deve haver erros"
    assert r["assembly"] is None

def test_tipo_incompativel_nao_gera_assembly():
    r = _pipeline("START\n(3.0 2.0 |)\nEND\n")
    assert r["assembly"] is None

def test_condicao_nao_bool_nao_gera_assembly():
    r = _pipeline("START\nIF (3 4 +) THEN\n(1 X)\nEND IF\nEND\n")
    assert r["assembly"] is None


##
# Reinicialização do contador de labels entre compilações
# gerarAssembly() reseta _label_count em cada chamada.
# Sem isso, testes que dependem de IFs geram labels com números crescentes
# e quebram quando rodados em sequência diferente.
def test_labels_resetam_entre_compilacoes():
    # Dois IFs compilados separadamente devem começar com IF_FIM_1
    a1 = _asm("START\nIF (1 1 =) THEN\n(1 X)\nEND IF\nEND\n")
    a2 = _asm("START\nIF (2 2 =) THEN\n(1 Y)\nEND IF\nEND\n")
    label1 = re.search(r"IF_FIM_(\d+):", a1)
    label2 = re.search(r"IF_FIM_(\d+):", a2)
    assert label1 and label2
    assert label1.group(1) == label2.group(1), \
        "Contador deve reiniciar a cada gerarAssembly()"


##
# Programa completo com todos os recursos
##
def test_programa_completo_sem_erros():
    # Programa usando todos os operadores e estruturas deve compilar sem erros
    codigo = (
        "START\n"
        "*{ programa de teste completo }*\n"
        "(10 A)\n(3 B)\n"
        "(A B +)\n(A B -)\n(A B *)\n"
        "(10 3 |)\n(10 3 %)\n(2 3 ^)\n"
        "(3.0 2.0 /)\n"
        "(1 RES)\n"
        "IF (A B >) THEN\n(1 OK)\nELSE\n(0 OK)\nEND IF\n"
        "(0 I)\n"
        "WHILE (I 2 <) DO\n(1 I)\nEND WHILE\n"
        "((A B =) (B B =) OR)\n"
        "END\n"
    )
    r = _pipeline(codigo)
    assert not r["erros"], f"Erros inesperados: {[e['mensagem'] for e in r['erros']]}"
    assert r["assembly"] is not None
    a = r["assembly"]
    assert ".data" in a
    assert ".text" in a
    assert "_start:" in a
    assert "_end:" in a
