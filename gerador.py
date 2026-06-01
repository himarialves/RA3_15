# Integrante do grupo:
# Mariana Alves da Silva - @himarialves
#
# Nome do grupo no Canvas: RA3_15
#
# Professor Frank Coelho de Alcantara
# Projeto acadêmico para a disciplina Linguagens Formais e Compiladores (2026-1).
# Instituição: Pontifícia Universidade Católica do Paraná - PUC/PR — 2026-1

'''
gerador.py — Módulo 4: gerarArvoreAtribuida + gerarAssembly

 Estratégia F64 unificada:
   -Todos os valores (int e real) vivem em registradores D (VFP double 64 bits).
   -Inteiros são promovidos: MOV/LDR R0 → VMOV S0 → VCVT.F64.S32 D0, S0.
   -Floats vêm de labels .double em .data: LDR R6, =label; VLDR D0, [R6].
   -Resultado de toda expressão fica em D0; pilha (VPUSH/VPOP) para sub-exprs.

 Decisões:
   -F64 unificado — em vez de separar registradores S (float) e D (double),
   -VPUSH/VPOP para sub-expressões — a convenção é: operando esquerdo vai para
   -D1 (via VPUSH + VPOP), operando direito fica em D0. 
   -Labels com contador global 
   -RES_HIST como array F64 — (N RES) 
'''
from __future__ import annotations
from CONTRACTS import (
    No, NoAtribuido, TabelaSimbolos,
    fazer_no_atribuido,
    OPS_RELACIONAIS, OPS_LOGICOS,
)

##
#  Estado global (resetado a cada chamada de gerarAssembly) 
_label_count = 0

def _novo_label(prefixo: str = "L") -> str:
    global _label_count
    _label_count += 1
    return f"{prefixo}_{_label_count}"

def _label_para_float(val: str) -> str:
    # Labels ARM não aceitam '.' ou '-' — convertemos para '_' e 'N'
    return f"FC_{val.replace('.', '_').replace('-', 'N')}"


##
# PARTE A — gerarArvoreAtribuida
def gerarArvoreAtribuida(
    arvore: No,
    tabela: TabelaSimbolos,
    tipos: dict[int, str],
) -> NoAtribuido:
    # Anota cada nó com tipo_semantico, categoria_semantica, reg_resultado e label.
    # Recebe a árvore sintática, a tabela de símbolos e o mapa id(no)→tipo do
    # verificador de tipos. Retorna a árvore completa como NoAtribuido.
    return _anotar(arvore, tabela, tipos)

def _categoria(no: No) -> str:
    tipo = no["tipo"]
    if tipo in ("literal_int", "literal_real", "literal_bool"):
        return "literal"
    if tipo == "variavel":
        return "variavel_leitura"
    if tipo == "atribuicao":
        return "variavel_escrita"
    if tipo == "n_res":
        return "resultado_anterior"
    if tipo == "expressao_rpn":
        op = no["valor"]
        if op in OPS_RELACIONAIS:
            return "operacao_relacional"
        if op in OPS_LOGICOS:
            return "operacao_logica"
        return "operacao_aritmetica"
    return "controle_fluxo"

def _tipo_fallback(no: No, tabela: TabelaSimbolos) -> str:
    # Usado quando o Módulo 3 não conseguiu inferir o tipo (ex: variável com
    # tipo "desconhecido"). Evita que gerarArvoreAtribuida quebre com None.
    tipo = no["tipo"]
    if tipo == "literal_int":
        return "int"
    if tipo == "literal_real":
        return "real"
    if tipo == "literal_bool":
        return "bool"
    if tipo == "variavel":
        entrada = tabela.get(no["valor"])
        return entrada["tipo"] if entrada else "int"
    return "int"

def _anotar(no: No, tabela: TabelaSimbolos, tipos: dict[int, str]) -> NoAtribuido:
    tipo_sem = tipos.get(id(no)) or _tipo_fallback(no, tabela)
    filhos_atrib = [_anotar(f, tabela, tipos) for f in no["filhos"]]
    return fazer_no_atribuido(
        no,
        tipo_semantico=tipo_sem,
        categoria_semantica=_categoria(no),
        reg_resultado="D0",
        label="",
        filhos_atribuidos=filhos_atrib,
    )

##
# PARTE B — gerarAssembly
#  Pré-passos (coleta de declarações para .data) 
def _coletar_mem_ids(no: NoAtribuido, vistos: set[str]) -> None:
    if no["tipo"] in ("variavel", "atribuicao"):
        nome = no["valor"]
        if nome and nome != "RES":
            vistos.add(nome)
    for filho in no["filhos"]:
        _coletar_mem_ids(filho, vistos)


def _coletar_floats(no: NoAtribuido, floats: dict[str, str]) -> None:
    if no["tipo"] == "literal_real":
        val = no["valor"]
        floats[_label_para_float(val)] = val
    for filho in no["filhos"]:
        _coletar_floats(filho, floats)


#  Geração de literais / variáveis em D0 

def _gerar_literal_int(no: NoAtribuido) -> str:
    val = no["valor"]
    ival = int(val)
    # MOV aceita imediato de 8 bits (0–255); valores maiores exigem LDR pseudo-instrução
    load = f"    MOV R0, #{ival}" if 0 <= ival <= 255 else f"    LDR R0, ={ival}"
    return (
        f"    @ int {val}\n"
        f"{load}\n"
        f"    VMOV S0, R0\n"
        f"    VCVT.F64.S32 D0, S0"
    )


def _gerar_literal_real(no: NoAtribuido) -> str:
    val = no["valor"]
    label = _label_para_float(val)
    return f"    @ real {val}\n    LDR R6, ={label}\n    VLDR D0, [R6]"


def _gerar_literal_bool(no: NoAtribuido) -> str:
    val = no["valor"]
    # Booleans são representados como F64: TRUE=1.0, FALSE=0.0
    const = "CONST_ONE" if val == "TRUE" else "CONST_ZERO"
    return f"    @ bool {val}\n    LDR R6, ={const}\n    VLDR D0, [R6]"


def _gerar_variavel_leitura(no: NoAtribuido) -> str:
    nome = no["valor"]
    return f"    @ var {nome}\n    LDR R1, ={nome}\n    VLDR D0, [R1]"


def _gerar_n_res(no: NoAtribuido) -> str:
    # Acessa RES_HIST[RES_IDX - N].
    # RES_IDX aponta para o próximo slot livre (não o último salvo),
    # então (RES_IDX - N) dá o índice do N-ésimo resultado anterior.
    # LSL #3 converte o índice de entradas para offset em bytes (× 8, pois F64).
    n = int(no["valor"])
    return "\n".join([
        f"    @ ({n} RES)",
        "    LDR R3, =RES_IDX",
        "    LDR R2, [R3]",
        f"    SUB R2, R2, #{n}",
        "    LDR R4, =RES_HIST",
        "    ADD R6, R4, R2, LSL #3",
        "    VLDR D0, [R6]",
    ])


def _gerar_valor_em_d0(no: NoAtribuido) -> str:
    # Despacha para a função de geração correta segundo o tipo de nó.
    # O contrato é: após executar o código retornado, D0 contém o valor.
    tipo = no["tipo"]
    if tipo == "literal_int":
        return _gerar_literal_int(no)
    if tipo == "literal_real":
        return _gerar_literal_real(no)
    if tipo == "literal_bool":
        return _gerar_literal_bool(no)
    if tipo == "variavel":
        return _gerar_variavel_leitura(no)
    if tipo == "n_res":
        return _gerar_n_res(no)
    if tipo == "expressao_rpn":
        return _gerar_expressao_rpn(no, salvar_res=False)
    if tipo == "bloco" and no["valor"] == "":
        return _gerar_bloco_inline(no)
    if tipo == "atribuicao":
        return _gerar_atribuicao(no, salvar_res=False)
    return f"    @ valor desconhecido: {tipo}"


def _gerar_bloco_inline(no: NoAtribuido) -> str:
    # Bloco inline (valor=="") usado como valor de atribuição composta.
    # Ex: (1 1 = FLAG) → o parser gera bloco com filhos=[lit_int(1), lit_int(1), expr_rpn("=")].
    # O operador fica no último filho (expressao_rpn sem filhos próprios) e
    # os operandos nos filhos anteriores — espelhando o que o Módulo 3 espera.
    filhos = no["filhos"]
    if not filhos:
        return "    @ bloco inline vazio"
    ultimo = filhos[-1]
    if ultimo["tipo"] == "expressao_rpn" and not ultimo["filhos"]:
        op = ultimo["valor"]
        operands = filhos[:-1]
        linhas = [f"    @ bloco inline {op}"]
        if len(operands) == 1:
            linhas.append(_gerar_valor_em_d0(operands[0]))
            if op == "NOT":
                linhas.append(_gerar_op_not())
            else:
                linhas.append(_gerar_op(op))
        elif len(operands) >= 2:
            linhas.append(_gerar_valor_em_d0(operands[0]))
            linhas.append("    VPUSH {D0}  @ empilha esq (8 bytes)")
            linhas.append(_gerar_valor_em_d0(operands[1]))
            linhas.append("    VPOP {D1}   @ desempilha esq em D1")
            linhas.append(_gerar_op(op))
        return "\n".join(linhas)
    return _gerar_valor_em_d0(filhos[-1])


#  Histórico de resultados 

def _gerar_salvar_res() -> str:
    # Salva D0 (F64) na posição RES_HIST[RES_IDX] e incrementa RES_IDX.
    # Chamado após qualquer statement de topo que produz resultado (expressão,
    # atribuição, leitura de variável, n_res) — a mesma lógica do Módulo 3.
    return "\n".join([
        "    @ salva em RES_HIST",
        "    LDR R3, =RES_IDX",
        "    LDR R2, [R3]",
        "    LDR R4, =RES_HIST",
        "    ADD R6, R4, R2, LSL #3",
        "    VSTR D0, [R6]",
        "    ADD R2, R2, #1",
        "    STR R2, [R3]",
    ])


#  Geração de operadores 

def _gerar_op(op: str) -> str:
    # Gera código ARM para operador binário.
    # Convenção de entrada: D1=operando esquerdo, D0=operando direito.
    # Resultado sempre em D0 ao retornar.
    if op == "+":
        return "    VADD.F64 D0, D1, D0"
    if op == "-":
        return "    VSUB.F64 D0, D1, D0"
    if op == "*":
        return "    VMUL.F64 D0, D1, D0"

    if op in ("/", "|"):
        # VDIV não suportado no CPulator DEC1-SOC — implementamos via loop de
        # subtração repetida em F64. D2=dividendo, D3=divisor, D4=contador.
        # O resultado é o número de vezes que D3 cabe em D2.
        lp = _novo_label("DIV_LOOP")
        lf = _novo_label("DIV_FIM")
        return "\n".join([
            "    @ divisao via loop de subtracao F64 (VDIV nao suportado)",
            "    VMOV.F64 D2, D1         @ D2 = dividendo",
            "    VMOV.F64 D3, D0         @ D3 = divisor",
            "    LDR R6, =CONST_ZERO",
            "    VLDR D4, [R6]           @ D4 = contador",
            "    LDR R6, =CONST_ONE",
            "    VLDR D5, [R6]           @ D5 = incremento",
            f"{lp}:",
            "    VCMP.F64 D2, D3",
            "    VMRS APSR_nzcv, FPSCR",
            f"    BLT {lf}",
            "    VSUB.F64 D2, D2, D3",
            "    VADD.F64 D4, D4, D5",
            f"    B {lp}",
            f"{lf}:",
            "    VMOV.F64 D0, D4         @ quociente -> D0",
        ])

    if op == "%":
        lp = _novo_label("MOD_LOOP")
        lf = _novo_label("MOD_FIM")
        return "\n".join([
            "    @ modulo via loop de subtracao F64",
            "    VMOV.F64 D2, D1         @ D2 = dividendo",
            "    VMOV.F64 D3, D0         @ D3 = divisor",
            f"{lp}:",
            "    VCMP.F64 D2, D3",
            "    VMRS APSR_nzcv, FPSCR",
            f"    BLT {lf}",
            "    VSUB.F64 D2, D2, D3",
            f"    B {lp}",
            f"{lf}:",
            "    VMOV.F64 D0, D2         @ resto -> D0",
        ])

    if op == "^":
        lp = _novo_label("POT_LOOP")
        lf = _novo_label("POT_FIM")
        return "\n".join([
            "    @ potencia via loop de multiplicacao F64",
            "    VMOV.F64 D2, D1         @ D2 = base",
            "    VMOV.F64 D3, D0         @ D3 = expoente (contador)",
            "    LDR R6, =CONST_ONE",
            "    VLDR D4, [R6]           @ D4 = acumulador",
            "    LDR R6, =CONST_ONE",
            "    VLDR D5, [R6]           @ D5 = decremento",
            f"{lp}:",
            "    VCMP.F64 D3, #0.0",
            "    VMRS APSR_nzcv, FPSCR",
            f"    BLE {lf}",
            "    VMUL.F64 D4, D4, D2",
            "    VSUB.F64 D3, D3, D5",
            f"    B {lp}",
            f"{lf}:",
            "    VMOV.F64 D0, D4         @ resultado -> D0",
        ])

    # Relacionais: VCMP.F64 D1, D0 compara D1 (esq) com D0 (dir).
    # VMRS copia as flags VFP para APSR para que BLT/BGT/BEQ possam lê-las.
    # Resultado final: D0 = 1.0 (verdadeiro) ou 0.0 (falso), via VLDR.
    _branch_map = {
        "<": "BLT", ">": "BGT", "=": "BEQ",
        "<=": "BLE", ">=": "BGE", "!=": "BNE",
    }
    if op in _branch_map:
        branch = _branch_map[op]
        lt = _novo_label("REL_T")
        le = _novo_label("REL_E")
        return "\n".join([
            f"    @ relacional {op}",
            "    VCMP.F64 D1, D0",
            "    VMRS APSR_nzcv, FPSCR",
            f"    {branch} {lt}",
            "    LDR R6, =CONST_ZERO",
            "    VLDR D0, [R6]",
            f"    B {le}",
            f"{lt}:",
            "    LDR R6, =CONST_ONE",
            "    VLDR D0, [R6]",
            f"{le}:",
        ])

    if op == "AND":
        lf = _novo_label("AND_F")
        le = _novo_label("AND_E")
        return "\n".join([
            "    @ AND (ambos devem ser != 0.0)",
            "    VCMP.F64 D1, #0.0",
            "    VMRS APSR_nzcv, FPSCR",
            f"    BEQ {lf}",
            "    VCMP.F64 D0, #0.0",
            "    VMRS APSR_nzcv, FPSCR",
            f"    BEQ {lf}",
            "    LDR R6, =CONST_ONE",
            "    VLDR D0, [R6]",
            f"    B {le}",
            f"{lf}:",
            "    LDR R6, =CONST_ZERO",
            "    VLDR D0, [R6]",
            f"{le}:",
        ])

    if op == "OR":
        lt = _novo_label("OR_T")
        le = _novo_label("OR_E")
        return "\n".join([
            "    @ OR (ao menos um deve ser != 0.0)",
            "    VCMP.F64 D1, #0.0",
            "    VMRS APSR_nzcv, FPSCR",
            f"    BNE {lt}",
            "    VCMP.F64 D0, #0.0",
            "    VMRS APSR_nzcv, FPSCR",
            f"    BNE {lt}",
            "    LDR R6, =CONST_ZERO",
            "    VLDR D0, [R6]",
            f"    B {le}",
            f"{lt}:",
            "    LDR R6, =CONST_ONE",
            "    VLDR D0, [R6]",
            f"{le}:",
        ])

    return f"    @ operador desconhecido: {op}"


def _gerar_op_not() -> str:
    # NOT unário: inverte o valor booleano em D0.
    # D0==0.0 (false) → D0=1.0 (true); qualquer outro valor → D0=0.0 (false).
    lt = _novo_label("NOT_T")
    le = _novo_label("NOT_E")
    return "\n".join([
        "    @ NOT",
        "    VCMP.F64 D0, #0.0",
        "    VMRS APSR_nzcv, FPSCR",
        f"    BEQ {lt}",
        "    LDR R6, =CONST_ZERO",
        "    VLDR D0, [R6]",
        f"    B {le}",
        f"{lt}:",
        "    LDR R6, =CONST_ONE",
        "    VLDR D0, [R6]",
        f"{le}:",
    ])


#  Expressão RPN 

def _gerar_expressao_rpn(no: NoAtribuido, salvar_res: bool) -> str:
    op = no["valor"]
    filhos = no["filhos"]

    # Nó "bare" (sem filhos) acontece em blocos inline — o operador é filho
    # do bloco, não da expressão. Já tratado por _gerar_bloco_inline.
    if not filhos:
        return f"    @ operador bare {op}"

    linhas = [f"    @ expressao {op}"]

    if op == "NOT":
        linhas.append(_gerar_valor_em_d0(filhos[0]))
        linhas.append(_gerar_op_not())
    else:
        # Esquerdo em D1, direito em D0 — convenção estabelecida em _gerar_op.
        linhas.append(_gerar_valor_em_d0(filhos[0]))
        linhas.append("    VPUSH {D0}  @ empilha esq (8 bytes)")
        linhas.append(_gerar_valor_em_d0(filhos[1]))
        linhas.append("    VPOP {D1}   @ desempilha esq em D1")
        linhas.append(_gerar_op(op))

    if salvar_res:
        linhas.append(_gerar_salvar_res())

    return "\n".join(linhas)


#  Atribuição (V MEM) 

def _gerar_atribuicao(no: NoAtribuido, salvar_res: bool) -> str:
    nome = no["valor"]
    valor_no = no["filhos"][0]
    linhas = [f"    @ atribuicao {nome}"]
    linhas.append(_gerar_valor_em_d0(valor_no))
    linhas.append(f"    LDR R1, ={nome}")
    linhas.append(f"    VSTR D0, [R1]  @ salva F64 em {nome}")
    if salvar_res:
        linhas.append(_gerar_salvar_res())
    return "\n".join(linhas)


#  IF 

def _gerar_if(no: NoAtribuido) -> str:
    filhos = no["filhos"]
    cond, bloco_then, bloco_else = filhos[0], filhos[1], filhos[2]
    tem_else = bool(bloco_else["filhos"])

    label_fim = _novo_label("IF_FIM")
    linhas = ["    @ IF"]
    linhas.append(_gerar_valor_em_d0(cond))
    # Condição está em D0 como F64: 0.0 = false, qualquer outro valor = true
    linhas.append("    VCMP.F64 D0, #0.0")
    linhas.append("    VMRS APSR_nzcv, FPSCR")

    if tem_else:
        label_else = _novo_label("ELSE")
        linhas.append(f"    BEQ {label_else}  @ pula para ELSE se falso")
        linhas.append(_gerar_bloco_stmts(bloco_then["filhos"]))
        linhas.append(f"    B {label_fim}")
        linhas.append(f"{label_else}:")
        linhas.append(_gerar_bloco_stmts(bloco_else["filhos"]))
    else:
        linhas.append(f"    BEQ {label_fim}  @ pula se falso")
        linhas.append(_gerar_bloco_stmts(bloco_then["filhos"]))

    linhas.append(f"{label_fim}:")
    return "\n".join(linhas)


#  WHILE 

def _gerar_while(no: NoAtribuido) -> str:
    filhos = no["filhos"]
    cond, bloco_corpo = filhos[0], filhos[1]
    lp = _novo_label("WHILE")
    lf = _novo_label("WHILE_FIM")

    linhas = ["    @ WHILE"]
    linhas.append(f"{lp}:")
    linhas.append(_gerar_valor_em_d0(cond))
    linhas.append("    VCMP.F64 D0, #0.0")
    linhas.append("    VMRS APSR_nzcv, FPSCR")
    linhas.append(f"    BEQ {lf}  @ sai se falso")
    linhas.append(_gerar_bloco_stmts(bloco_corpo["filhos"]))
    linhas.append(f"    B {lp}")
    linhas.append(f"{lf}:")
    return "\n".join(linhas)


#  Statement (despacho) 

def _stmt_produz_resultado(no: NoAtribuido) -> bool:
    # True se o statement deve ser salvo em RES_HIST — a mesma lógica do
    # verificador de tipos ao decidir o que entra em `resultados`.
    return no["tipo"] in ("expressao_rpn", "atribuicao", "variavel", "n_res")

def _gerar_stmt(no: NoAtribuido, salvar_res: bool) -> str:
    tipo = no["tipo"]

    if tipo == "expressao_rpn":
        return _gerar_expressao_rpn(no, salvar_res)
    if tipo == "atribuicao":
        return _gerar_atribuicao(no, salvar_res)
    if tipo == "variavel":
        code = _gerar_variavel_leitura(no)
        if salvar_res:
            code += "\n" + _gerar_salvar_res()
        return code
    if tipo == "n_res":
        code = _gerar_n_res(no)
        if salvar_res:
            code += "\n" + _gerar_salvar_res()
        return code
    if tipo == "if":
        return _gerar_if(no)
    if tipo == "while":
        return _gerar_while(no)
    return f"    @ stmt desconhecido: {tipo}"


def _gerar_bloco_stmts(nos: list) -> str:
    # Gera statements de um bloco interno (corpo de IF/WHILE) sem salvar em
    # RES_HIST — (N RES) dentro de IF/WHILE não acessa resultados de fora.
    if not nos:
        return "    @ bloco vazio"
    return "\n".join(_gerar_stmt(no, salvar_res=False) for no in nos)


#  Seção .data 

def _gerar_secao_dados(mem_ids: list[str], floats: dict[str, str]) -> str:
    linhas = [
        ".data",
        "",
        "@ Historico de resultados (max 256 entradas x 8 bytes = F64)",
        "RES_IDX: .word 0",
        ".align 3              @ alinha a 8 bytes para VLDR/VSTR D (F64 exige alinhamento duplo)",
        "RES_HIST: .space 2048",
        "",
        "@ Constantes auxiliares para loops e operadores relacionais",
        "CONST_ZERO: .double 0.0",
        "CONST_ONE:  .double 1.0",
        "",
    ]
    if mem_ids:
        linhas.append("@ Variaveis de memoria (F64, 8 bytes cada)")
        for nome in mem_ids:
            linhas.append(f"{nome}: .double 0.0")
        linhas.append("")
    if floats:
        linhas.append("@ Constantes de ponto flutuante (F64)")
        for label, val in sorted(floats.items()):
            linhas.append(f"{label}: .double {val}")
        linhas.append("")
    linhas += [
        "@ Pilha de software (1 KB)",
        "STACK: .space 1024",
        "STACK_TOP:",
        "",
    ]
    return "\n".join(linhas)


#  Seção .text 

def _gerar_secao_texto(arvore: NoAtribuido) -> str:
    linhas = [
        ".text",
        "@ Assembly ARMv7 gerado automaticamente -- RA3-15",
        "@ Plataforma: CPulator ARMv7 DEC1-SOC v16.1",
        "",
        ".global _start",
        "_start:",
        "",
        "    @ Inicializa stack pointer (CPulator nao inicializa SP automaticamente)",
        "    LDR SP, =STACK_TOP",
        "",
        "    @ Habilita coprocessador VFP (bit EN do FPEXC) — VMSR é a sintaxe UAL correta para ARMv7",
        "    LDR R0, =0x40000000",
        "    VMSR FPEXC, R0",
        "",
        "    @ Inicializa indice do historico RES em zero",
        "    LDR R4, =RES_IDX",
        "    MOV R5, #0",
        "    STR R5, [R4]",
        "",
    ]
    for filho in arvore["filhos"]:
        linhas.append(_gerar_stmt(filho, salvar_res=_stmt_produz_resultado(filho)))
        linhas.append("")
    linhas += [
        "_end:",
        "    B _end",
        "",
    ]
    return "\n".join(linhas)


#  API pública 

def gerarAssembly(arvore_atrib: NoAtribuido) -> str:
    # Gera código Assembly ARMv7 a partir da árvore atribuída.
    # Deve ser chamado apenas para programas sem erros semânticos.
    # Saída: string com seções .data e .text prontas para o CPulator.
    global _label_count
    _label_count = 0   # reset garante que cada compilação começa em L_1

    mem_ids: set[str] = set()
    _coletar_mem_ids(arvore_atrib, mem_ids)

    floats: dict[str, str] = {}
    _coletar_floats(arvore_atrib, floats)

    secao_dados = _gerar_secao_dados(sorted(mem_ids), floats)
    secao_texto = _gerar_secao_texto(arvore_atrib)
    return secao_dados + "\n" + secao_texto
