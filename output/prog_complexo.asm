.data

@ Historico de resultados (max 256 entradas x 8 bytes = F64)
RES_IDX: .word 0
.align 3              @ alinha a 8 bytes para VLDR/VSTR D (F64 exige alinhamento duplo)
RES_HIST: .space 2048

@ Constantes auxiliares para loops e operadores relacionais
CONST_ZERO: .double 0.0
CONST_ONE:  .double 1.0

@ Variaveis de memoria (F64, 8 bytes cada)
BASE: .double 0.0
EXP: .double 0.0
FLAG: .double 0.0
I: .double 0.0
N: .double 0.0
SOMA: .double 0.0
X: .double 0.0
Y: .double 0.0

@ Constantes de ponto flutuante (F64)
FC_1_5: .double 1.5
FC_2_5: .double 2.5

@ Pilha de software (1 KB)
STACK: .space 1024
STACK_TOP:

.text
@ Assembly ARMv7 gerado automaticamente -- RA3-15
@ Plataforma: CPulator ARMv7 DEC1-SOC v16.1

.global _start
_start:

    @ Inicializa stack pointer (CPulator nao inicializa SP automaticamente)
    LDR SP, =STACK_TOP

    @ Habilita coprocessador VFP (bit EN do FPEXC) — VMSR é a sintaxe UAL correta para ARMv7
    LDR R0, =0x40000000
    VMSR FPEXC, R0

    @ Inicializa indice do historico RES em zero
    LDR R4, =RES_IDX
    MOV R5, #0
    STR R5, [R4]

    @ atribuicao N
    @ int 5
    MOV R0, #5
    VMOV S0, R0
    VCVT.F64.S32 D0, S0
    LDR R1, =N
    VSTR D0, [R1]  @ salva F64 em N
    @ salva em RES_HIST
    LDR R3, =RES_IDX
    LDR R2, [R3]
    LDR R4, =RES_HIST
    ADD R6, R4, R2, LSL #3
    VSTR D0, [R6]
    ADD R2, R2, #1
    STR R2, [R3]

    @ atribuicao I
    @ int 1
    MOV R0, #1
    VMOV S0, R0
    VCVT.F64.S32 D0, S0
    LDR R1, =I
    VSTR D0, [R1]  @ salva F64 em I
    @ salva em RES_HIST
    LDR R3, =RES_IDX
    LDR R2, [R3]
    LDR R4, =RES_HIST
    ADD R6, R4, R2, LSL #3
    VSTR D0, [R6]
    ADD R2, R2, #1
    STR R2, [R3]

    @ atribuicao SOMA
    @ int 0
    MOV R0, #0
    VMOV S0, R0
    VCVT.F64.S32 D0, S0
    LDR R1, =SOMA
    VSTR D0, [R1]  @ salva F64 em SOMA
    @ salva em RES_HIST
    LDR R3, =RES_IDX
    LDR R2, [R3]
    LDR R4, =RES_HIST
    ADD R6, R4, R2, LSL #3
    VSTR D0, [R6]
    ADD R2, R2, #1
    STR R2, [R3]

    @ WHILE
WHILE_1:
    @ expressao <=
    @ var I
    LDR R1, =I
    VLDR D0, [R1]
    VPUSH {D0}  @ empilha esq (8 bytes)
    @ var N
    LDR R1, =N
    VLDR D0, [R1]
    VPOP {D1}   @ desempilha esq em D1
    @ relacional <=
    VCMP.F64 D1, D0
    VMRS APSR_nzcv, FPSCR
    BLE REL_T_3
    LDR R6, =CONST_ZERO
    VLDR D0, [R6]
    B REL_E_4
REL_T_3:
    LDR R6, =CONST_ONE
    VLDR D0, [R6]
REL_E_4:
    VCMP.F64 D0, #0.0
    VMRS APSR_nzcv, FPSCR
    BEQ WHILE_FIM_2  @ sai se falso
    @ atribuicao SOMA
    @ expressao +
    @ var SOMA
    LDR R1, =SOMA
    VLDR D0, [R1]
    VPUSH {D0}  @ empilha esq (8 bytes)
    @ var I
    LDR R1, =I
    VLDR D0, [R1]
    VPOP {D1}   @ desempilha esq em D1
    VADD.F64 D0, D1, D0
    LDR R1, =SOMA
    VSTR D0, [R1]  @ salva F64 em SOMA
    @ atribuicao I
    @ expressao +
    @ var I
    LDR R1, =I
    VLDR D0, [R1]
    VPUSH {D0}  @ empilha esq (8 bytes)
    @ int 1
    MOV R0, #1
    VMOV S0, R0
    VCVT.F64.S32 D0, S0
    VPOP {D1}   @ desempilha esq em D1
    VADD.F64 D0, D1, D0
    LDR R1, =I
    VSTR D0, [R1]  @ salva F64 em I
    B WHILE_1
WHILE_FIM_2:

    @ atribuicao BASE
    @ int 2
    MOV R0, #2
    VMOV S0, R0
    VCVT.F64.S32 D0, S0
    LDR R1, =BASE
    VSTR D0, [R1]  @ salva F64 em BASE
    @ salva em RES_HIST
    LDR R3, =RES_IDX
    LDR R2, [R3]
    LDR R4, =RES_HIST
    ADD R6, R4, R2, LSL #3
    VSTR D0, [R6]
    ADD R2, R2, #1
    STR R2, [R3]

    @ atribuicao EXP
    @ int 8
    MOV R0, #8
    VMOV S0, R0
    VCVT.F64.S32 D0, S0
    LDR R1, =EXP
    VSTR D0, [R1]  @ salva F64 em EXP
    @ salva em RES_HIST
    LDR R3, =RES_IDX
    LDR R2, [R3]
    LDR R4, =RES_HIST
    ADD R6, R4, R2, LSL #3
    VSTR D0, [R6]
    ADD R2, R2, #1
    STR R2, [R3]

    @ expressao ^
    @ var BASE
    LDR R1, =BASE
    VLDR D0, [R1]
    VPUSH {D0}  @ empilha esq (8 bytes)
    @ var EXP
    LDR R1, =EXP
    VLDR D0, [R1]
    VPOP {D1}   @ desempilha esq em D1
    @ potencia via loop de multiplicacao F64
    VMOV.F64 D2, D1         @ D2 = base
    VMOV.F64 D3, D0         @ D3 = expoente (contador)
    LDR R6, =CONST_ONE
    VLDR D4, [R6]           @ D4 = acumulador
    LDR R6, =CONST_ONE
    VLDR D5, [R6]           @ D5 = decremento
POT_LOOP_5:
    VCMP.F64 D3, #0.0
    VMRS APSR_nzcv, FPSCR
    BLE POT_FIM_6
    VMUL.F64 D4, D4, D2
    VSUB.F64 D3, D3, D5
    B POT_LOOP_5
POT_FIM_6:
    VMOV.F64 D0, D4         @ resultado -> D0
    @ salva em RES_HIST
    LDR R3, =RES_IDX
    LDR R2, [R3]
    LDR R4, =RES_HIST
    ADD R6, R4, R2, LSL #3
    VSTR D0, [R6]
    ADD R2, R2, #1
    STR R2, [R3]

    @ (1 RES)
    LDR R3, =RES_IDX
    LDR R2, [R3]
    SUB R2, R2, #1
    LDR R4, =RES_HIST
    ADD R6, R4, R2, LSL #3
    VLDR D0, [R6]
    @ salva em RES_HIST
    LDR R3, =RES_IDX
    LDR R2, [R3]
    LDR R4, =RES_HIST
    ADD R6, R4, R2, LSL #3
    VSTR D0, [R6]
    ADD R2, R2, #1
    STR R2, [R3]

    @ IF
    @ expressao >
    @ var SOMA
    LDR R1, =SOMA
    VLDR D0, [R1]
    VPUSH {D0}  @ empilha esq (8 bytes)
    @ var N
    LDR R1, =N
    VLDR D0, [R1]
    VPOP {D1}   @ desempilha esq em D1
    @ relacional >
    VCMP.F64 D1, D0
    VMRS APSR_nzcv, FPSCR
    BGT REL_T_8
    LDR R6, =CONST_ZERO
    VLDR D0, [R6]
    B REL_E_9
REL_T_8:
    LDR R6, =CONST_ONE
    VLDR D0, [R6]
REL_E_9:
    VCMP.F64 D0, #0.0
    VMRS APSR_nzcv, FPSCR
    BEQ ELSE_10  @ pula para ELSE se falso
    @ IF
    @ expressao >
    @ var N
    LDR R1, =N
    VLDR D0, [R1]
    VPUSH {D0}  @ empilha esq (8 bytes)
    @ int 3
    MOV R0, #3
    VMOV S0, R0
    VCVT.F64.S32 D0, S0
    VPOP {D1}   @ desempilha esq em D1
    @ relacional >
    VCMP.F64 D1, D0
    VMRS APSR_nzcv, FPSCR
    BGT REL_T_12
    LDR R6, =CONST_ZERO
    VLDR D0, [R6]
    B REL_E_13
REL_T_12:
    LDR R6, =CONST_ONE
    VLDR D0, [R6]
REL_E_13:
    VCMP.F64 D0, #0.0
    VMRS APSR_nzcv, FPSCR
    BEQ ELSE_14  @ pula para ELSE se falso
    @ atribuicao FLAG
    @ int 1
    MOV R0, #1
    VMOV S0, R0
    VCVT.F64.S32 D0, S0
    LDR R1, =FLAG
    VSTR D0, [R1]  @ salva F64 em FLAG
    B IF_FIM_11
ELSE_14:
    @ atribuicao FLAG
    @ int 0
    MOV R0, #0
    VMOV S0, R0
    VCVT.F64.S32 D0, S0
    LDR R1, =FLAG
    VSTR D0, [R1]  @ salva F64 em FLAG
IF_FIM_11:
    B IF_FIM_7
ELSE_10:
    @ atribuicao FLAG
    @ int 0
    MOV R0, #0
    VMOV S0, R0
    VCVT.F64.S32 D0, S0
    LDR R1, =FLAG
    VSTR D0, [R1]  @ salva F64 em FLAG
IF_FIM_7:

    @ atribuicao X
    @ real 1.5
    LDR R6, =FC_1_5
    VLDR D0, [R6]
    LDR R1, =X
    VSTR D0, [R1]  @ salva F64 em X
    @ salva em RES_HIST
    LDR R3, =RES_IDX
    LDR R2, [R3]
    LDR R4, =RES_HIST
    ADD R6, R4, R2, LSL #3
    VSTR D0, [R6]
    ADD R2, R2, #1
    STR R2, [R3]

    @ atribuicao Y
    @ real 2.5
    LDR R6, =FC_2_5
    VLDR D0, [R6]
    LDR R1, =Y
    VSTR D0, [R1]  @ salva F64 em Y
    @ salva em RES_HIST
    LDR R3, =RES_IDX
    LDR R2, [R3]
    LDR R4, =RES_HIST
    ADD R6, R4, R2, LSL #3
    VSTR D0, [R6]
    ADD R2, R2, #1
    STR R2, [R3]

    @ expressao +
    @ var X
    LDR R1, =X
    VLDR D0, [R1]
    VPUSH {D0}  @ empilha esq (8 bytes)
    @ var Y
    LDR R1, =Y
    VLDR D0, [R1]
    VPOP {D1}   @ desempilha esq em D1
    VADD.F64 D0, D1, D0
    @ salva em RES_HIST
    LDR R3, =RES_IDX
    LDR R2, [R3]
    LDR R4, =RES_HIST
    ADD R6, R4, R2, LSL #3
    VSTR D0, [R6]
    ADD R2, R2, #1
    STR R2, [R3]

    @ expressao *
    @ var X
    LDR R1, =X
    VLDR D0, [R1]
    VPUSH {D0}  @ empilha esq (8 bytes)
    @ var Y
    LDR R1, =Y
    VLDR D0, [R1]
    VPOP {D1}   @ desempilha esq em D1
    VMUL.F64 D0, D1, D0
    @ salva em RES_HIST
    LDR R3, =RES_IDX
    LDR R2, [R3]
    LDR R4, =RES_HIST
    ADD R6, R4, R2, LSL #3
    VSTR D0, [R6]
    ADD R2, R2, #1
    STR R2, [R3]

    @ expressao AND
    @ expressao <
    @ int 1
    MOV R0, #1
    VMOV S0, R0
    VCVT.F64.S32 D0, S0
    VPUSH {D0}  @ empilha esq (8 bytes)
    @ int 2
    MOV R0, #2
    VMOV S0, R0
    VCVT.F64.S32 D0, S0
    VPOP {D1}   @ desempilha esq em D1
    @ relacional <
    VCMP.F64 D1, D0
    VMRS APSR_nzcv, FPSCR
    BLT REL_T_15
    LDR R6, =CONST_ZERO
    VLDR D0, [R6]
    B REL_E_16
REL_T_15:
    LDR R6, =CONST_ONE
    VLDR D0, [R6]
REL_E_16:
    VPUSH {D0}  @ empilha esq (8 bytes)
    @ expressao <
    @ int 3
    MOV R0, #3
    VMOV S0, R0
    VCVT.F64.S32 D0, S0
    VPUSH {D0}  @ empilha esq (8 bytes)
    @ int 4
    MOV R0, #4
    VMOV S0, R0
    VCVT.F64.S32 D0, S0
    VPOP {D1}   @ desempilha esq em D1
    @ relacional <
    VCMP.F64 D1, D0
    VMRS APSR_nzcv, FPSCR
    BLT REL_T_17
    LDR R6, =CONST_ZERO
    VLDR D0, [R6]
    B REL_E_18
REL_T_17:
    LDR R6, =CONST_ONE
    VLDR D0, [R6]
REL_E_18:
    VPOP {D1}   @ desempilha esq em D1
    @ AND (ambos devem ser != 0.0)
    VCMP.F64 D1, #0.0
    VMRS APSR_nzcv, FPSCR
    BEQ AND_F_19
    VCMP.F64 D0, #0.0
    VMRS APSR_nzcv, FPSCR
    BEQ AND_F_19
    LDR R6, =CONST_ONE
    VLDR D0, [R6]
    B AND_E_20
AND_F_19:
    LDR R6, =CONST_ZERO
    VLDR D0, [R6]
AND_E_20:
    @ salva em RES_HIST
    LDR R3, =RES_IDX
    LDR R2, [R3]
    LDR R4, =RES_HIST
    ADD R6, R4, R2, LSL #3
    VSTR D0, [R6]
    ADD R2, R2, #1
    STR R2, [R3]

    @ expressao OR
    @ expressao =
    @ int 1
    MOV R0, #1
    VMOV S0, R0
    VCVT.F64.S32 D0, S0
    VPUSH {D0}  @ empilha esq (8 bytes)
    @ int 2
    MOV R0, #2
    VMOV S0, R0
    VCVT.F64.S32 D0, S0
    VPOP {D1}   @ desempilha esq em D1
    @ relacional =
    VCMP.F64 D1, D0
    VMRS APSR_nzcv, FPSCR
    BEQ REL_T_21
    LDR R6, =CONST_ZERO
    VLDR D0, [R6]
    B REL_E_22
REL_T_21:
    LDR R6, =CONST_ONE
    VLDR D0, [R6]
REL_E_22:
    VPUSH {D0}  @ empilha esq (8 bytes)
    @ expressao =
    @ int 3
    MOV R0, #3
    VMOV S0, R0
    VCVT.F64.S32 D0, S0
    VPUSH {D0}  @ empilha esq (8 bytes)
    @ int 3
    MOV R0, #3
    VMOV S0, R0
    VCVT.F64.S32 D0, S0
    VPOP {D1}   @ desempilha esq em D1
    @ relacional =
    VCMP.F64 D1, D0
    VMRS APSR_nzcv, FPSCR
    BEQ REL_T_23
    LDR R6, =CONST_ZERO
    VLDR D0, [R6]
    B REL_E_24
REL_T_23:
    LDR R6, =CONST_ONE
    VLDR D0, [R6]
REL_E_24:
    VPOP {D1}   @ desempilha esq em D1
    @ OR (ao menos um deve ser != 0.0)
    VCMP.F64 D1, #0.0
    VMRS APSR_nzcv, FPSCR
    BNE OR_T_25
    VCMP.F64 D0, #0.0
    VMRS APSR_nzcv, FPSCR
    BNE OR_T_25
    LDR R6, =CONST_ZERO
    VLDR D0, [R6]
    B OR_E_26
OR_T_25:
    LDR R6, =CONST_ONE
    VLDR D0, [R6]
OR_E_26:
    @ salva em RES_HIST
    LDR R3, =RES_IDX
    LDR R2, [R3]
    LDR R4, =RES_HIST
    ADD R6, R4, R2, LSL #3
    VSTR D0, [R6]
    ADD R2, R2, #1
    STR R2, [R3]

    @ (2 RES)
    LDR R3, =RES_IDX
    LDR R2, [R3]
    SUB R2, R2, #2
    LDR R4, =RES_HIST
    ADD R6, R4, R2, LSL #3
    VLDR D0, [R6]
    @ salva em RES_HIST
    LDR R3, =RES_IDX
    LDR R2, [R3]
    LDR R4, =RES_HIST
    ADD R6, R4, R2, LSL #3
    VSTR D0, [R6]
    ADD R2, R2, #1
    STR R2, [R3]

_end:
    B _end
