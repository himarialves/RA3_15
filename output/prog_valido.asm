.data

@ Historico de resultados (max 256 entradas x 8 bytes = F64)
RES_IDX: .word 0
.align 3              @ alinha a 8 bytes para VLDR/VSTR D (F64 exige alinhamento duplo)
RES_HIST: .space 2048

@ Constantes auxiliares para loops e operadores relacionais
CONST_ZERO: .double 0.0
CONST_ONE:  .double 1.0

@ Variaveis de memoria (F64, 8 bytes cada)
A: .double 0.0
B: .double 0.0
C: .double 0.0
D: .double 0.0
I: .double 0.0

@ Constantes de ponto flutuante (F64)
FC_2_0: .double 2.0
FC_3_0: .double 3.0

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

    @ atribuicao A
    @ int 10
    MOV R0, #10
    VMOV S0, R0
    VCVT.F64.S32 D0, S0
    LDR R1, =A
    VSTR D0, [R1]  @ salva F64 em A
    @ salva em RES_HIST
    LDR R3, =RES_IDX
    LDR R2, [R3]
    LDR R4, =RES_HIST
    ADD R6, R4, R2, LSL #3
    VSTR D0, [R6]
    ADD R2, R2, #1
    STR R2, [R3]

    @ atribuicao B
    @ int 3
    MOV R0, #3
    VMOV S0, R0
    VCVT.F64.S32 D0, S0
    LDR R1, =B
    VSTR D0, [R1]  @ salva F64 em B
    @ salva em RES_HIST
    LDR R3, =RES_IDX
    LDR R2, [R3]
    LDR R4, =RES_HIST
    ADD R6, R4, R2, LSL #3
    VSTR D0, [R6]
    ADD R2, R2, #1
    STR R2, [R3]

    @ expressao +
    @ var A
    LDR R1, =A
    VLDR D0, [R1]
    VPUSH {D0}  @ empilha esq (8 bytes)
    @ var B
    LDR R1, =B
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

    @ expressao -
    @ var A
    LDR R1, =A
    VLDR D0, [R1]
    VPUSH {D0}  @ empilha esq (8 bytes)
    @ var B
    LDR R1, =B
    VLDR D0, [R1]
    VPOP {D1}   @ desempilha esq em D1
    VSUB.F64 D0, D1, D0
    @ salva em RES_HIST
    LDR R3, =RES_IDX
    LDR R2, [R3]
    LDR R4, =RES_HIST
    ADD R6, R4, R2, LSL #3
    VSTR D0, [R6]
    ADD R2, R2, #1
    STR R2, [R3]

    @ expressao *
    @ var A
    LDR R1, =A
    VLDR D0, [R1]
    VPUSH {D0}  @ empilha esq (8 bytes)
    @ var B
    LDR R1, =B
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

    @ expressao |
    @ int 10
    MOV R0, #10
    VMOV S0, R0
    VCVT.F64.S32 D0, S0
    VPUSH {D0}  @ empilha esq (8 bytes)
    @ int 3
    MOV R0, #3
    VMOV S0, R0
    VCVT.F64.S32 D0, S0
    VPOP {D1}   @ desempilha esq em D1
    @ divisao via loop de subtracao F64 (VDIV nao suportado)
    VMOV.F64 D2, D1         @ D2 = dividendo
    VMOV.F64 D3, D0         @ D3 = divisor
    LDR R6, =CONST_ZERO
    VLDR D4, [R6]           @ D4 = contador
    LDR R6, =CONST_ONE
    VLDR D5, [R6]           @ D5 = incremento
DIV_LOOP_1:
    VCMP.F64 D2, D3
    VMRS APSR_nzcv, FPSCR
    BLT DIV_FIM_2
    VSUB.F64 D2, D2, D3
    VADD.F64 D4, D4, D5
    B DIV_LOOP_1
DIV_FIM_2:
    VMOV.F64 D0, D4         @ quociente -> D0
    @ salva em RES_HIST
    LDR R3, =RES_IDX
    LDR R2, [R3]
    LDR R4, =RES_HIST
    ADD R6, R4, R2, LSL #3
    VSTR D0, [R6]
    ADD R2, R2, #1
    STR R2, [R3]

    @ expressao %
    @ int 10
    MOV R0, #10
    VMOV S0, R0
    VCVT.F64.S32 D0, S0
    VPUSH {D0}  @ empilha esq (8 bytes)
    @ int 3
    MOV R0, #3
    VMOV S0, R0
    VCVT.F64.S32 D0, S0
    VPOP {D1}   @ desempilha esq em D1
    @ modulo via loop de subtracao F64
    VMOV.F64 D2, D1         @ D2 = dividendo
    VMOV.F64 D3, D0         @ D3 = divisor
MOD_LOOP_3:
    VCMP.F64 D2, D3
    VMRS APSR_nzcv, FPSCR
    BLT MOD_FIM_4
    VSUB.F64 D2, D2, D3
    B MOD_LOOP_3
MOD_FIM_4:
    VMOV.F64 D0, D2         @ resto -> D0
    @ salva em RES_HIST
    LDR R3, =RES_IDX
    LDR R2, [R3]
    LDR R4, =RES_HIST
    ADD R6, R4, R2, LSL #3
    VSTR D0, [R6]
    ADD R2, R2, #1
    STR R2, [R3]

    @ expressao ^
    @ int 2
    MOV R0, #2
    VMOV S0, R0
    VCVT.F64.S32 D0, S0
    VPUSH {D0}  @ empilha esq (8 bytes)
    @ int 3
    MOV R0, #3
    VMOV S0, R0
    VCVT.F64.S32 D0, S0
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

    @ expressao *
    @ real 3.0
    LDR R6, =FC_3_0
    VLDR D0, [R6]
    VPUSH {D0}  @ empilha esq (8 bytes)
    @ real 2.0
    LDR R6, =FC_2_0
    VLDR D0, [R6]
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

    @ expressao /
    @ real 3.0
    LDR R6, =FC_3_0
    VLDR D0, [R6]
    VPUSH {D0}  @ empilha esq (8 bytes)
    @ real 2.0
    LDR R6, =FC_2_0
    VLDR D0, [R6]
    VPOP {D1}   @ desempilha esq em D1
    @ divisao via loop de subtracao F64 (VDIV nao suportado)
    VMOV.F64 D2, D1         @ D2 = dividendo
    VMOV.F64 D3, D0         @ D3 = divisor
    LDR R6, =CONST_ZERO
    VLDR D4, [R6]           @ D4 = contador
    LDR R6, =CONST_ONE
    VLDR D5, [R6]           @ D5 = incremento
DIV_LOOP_7:
    VCMP.F64 D2, D3
    VMRS APSR_nzcv, FPSCR
    BLT DIV_FIM_8
    VSUB.F64 D2, D2, D3
    VADD.F64 D4, D4, D5
    B DIV_LOOP_7
DIV_FIM_8:
    VMOV.F64 D0, D4         @ quociente -> D0
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

    @ expressao <
    @ var A
    LDR R1, =A
    VLDR D0, [R1]
    VPUSH {D0}  @ empilha esq (8 bytes)
    @ var B
    LDR R1, =B
    VLDR D0, [R1]
    VPOP {D1}   @ desempilha esq em D1
    @ relacional <
    VCMP.F64 D1, D0
    VMRS APSR_nzcv, FPSCR
    BLT REL_T_9
    LDR R6, =CONST_ZERO
    VLDR D0, [R6]
    B REL_E_10
REL_T_9:
    LDR R6, =CONST_ONE
    VLDR D0, [R6]
REL_E_10:
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
    @ var A
    LDR R1, =A
    VLDR D0, [R1]
    VPUSH {D0}  @ empilha esq (8 bytes)
    @ var B
    LDR R1, =B
    VLDR D0, [R1]
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
    @ atribuicao C
    @ int 100
    MOV R0, #100
    VMOV S0, R0
    VCVT.F64.S32 D0, S0
    LDR R1, =C
    VSTR D0, [R1]  @ salva F64 em C
    B IF_FIM_11
ELSE_14:
    @ atribuicao C
    @ int 0
    MOV R0, #0
    VMOV S0, R0
    VCVT.F64.S32 D0, S0
    LDR R1, =C
    VSTR D0, [R1]  @ salva F64 em C
IF_FIM_11:

    @ atribuicao I
    @ int 0
    MOV R0, #0
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

    @ WHILE
WHILE_15:
    @ expressao <
    @ var I
    LDR R1, =I
    VLDR D0, [R1]
    VPUSH {D0}  @ empilha esq (8 bytes)
    @ int 3
    MOV R0, #3
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
    VCMP.F64 D0, #0.0
    VMRS APSR_nzcv, FPSCR
    BEQ WHILE_FIM_16  @ sai se falso
    @ atribuicao D
    @ int 1
    MOV R0, #1
    VMOV S0, R0
    VCVT.F64.S32 D0, S0
    LDR R1, =D
    VSTR D0, [R1]  @ salva F64 em D
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
    B WHILE_15
WHILE_FIM_16:

    @ expressao OR
    @ expressao =
    @ var A
    LDR R1, =A
    VLDR D0, [R1]
    VPUSH {D0}  @ empilha esq (8 bytes)
    @ var B
    LDR R1, =B
    VLDR D0, [R1]
    VPOP {D1}   @ desempilha esq em D1
    @ relacional =
    VCMP.F64 D1, D0
    VMRS APSR_nzcv, FPSCR
    BEQ REL_T_19
    LDR R6, =CONST_ZERO
    VLDR D0, [R6]
    B REL_E_20
REL_T_19:
    LDR R6, =CONST_ONE
    VLDR D0, [R6]
REL_E_20:
    VPUSH {D0}  @ empilha esq (8 bytes)
    @ expressao =
    @ var B
    LDR R1, =B
    VLDR D0, [R1]
    VPUSH {D0}  @ empilha esq (8 bytes)
    @ var B
    LDR R1, =B
    VLDR D0, [R1]
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
    VPOP {D1}   @ desempilha esq em D1
    @ OR (ao menos um deve ser != 0.0)
    VCMP.F64 D1, #0.0
    VMRS APSR_nzcv, FPSCR
    BNE OR_T_23
    VCMP.F64 D0, #0.0
    VMRS APSR_nzcv, FPSCR
    BNE OR_T_23
    LDR R6, =CONST_ZERO
    VLDR D0, [R6]
    B OR_E_24
OR_T_23:
    LDR R6, =CONST_ONE
    VLDR D0, [R6]
OR_E_24:
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
