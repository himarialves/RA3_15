# Regras de Tipos — Linguagem RPN Customizada

**Fase 3: Analisador Semântico**
**Tipagem:** estática e forte (nenhuma coerção implícita)
**Tipos:** `int`, `real`, `bool`

---

## Notação

```
Γ  — contexto (tabela de símbolos)
⊢  — dedução
:  — tem tipo
```

---

## 1. Literais

```
[T-INT]
  ──────────────────────
  Γ ⊢ <inteiro> : int


[T-REAL]
  ──────────────────────
  Γ ⊢ <real> : real


[T-BOOL]
  ──────────────────────────────
  Γ ⊢ TRUE : bool   Γ ⊢ FALSE : bool
```

---

## 2. Variáveis

```
[T-VAR-READ]
  Γ(MEM) = τ
  ────────────────────
  Γ ⊢ (MEM) : τ


[T-VAR-WRITE]
  Γ ⊢ V : τ    Γ(MEM) = τ
  ─────────────────────────────
  Γ ⊢ (V MEM) : τ
```

---

## 3. Resultado Anterior

```
[T-N-RES]
  resultados[−N] = τ    N ≥ 1    N ≤ |resultados|
  ──────────────────────────────────────────────────
  Γ ⊢ (N RES) : τ
```

---

## 4. Operadores Aritméticos

```
[T-INT-ADD]   [T-INT-SUB]   [T-INT-MUL]
  Γ ⊢ e1 : int    Γ ⊢ e2 : int
  ──────────────────────────────────────
       Γ ⊢ (e1 e2 +) : int
       Γ ⊢ (e1 e2 -) : int
       Γ ⊢ (e1 e2 *) : int


[T-REAL-ADD]   [T-REAL-SUB]   [T-REAL-MUL]
  Γ ⊢ e1 : real    Γ ⊢ e2 : real
  ──────────────────────────────────────────
       Γ ⊢ (e1 e2 +) : real
       Γ ⊢ (e1 e2 -) : real
       Γ ⊢ (e1 e2 *) : real


[T-REAL-DIV]
  Γ ⊢ e1 : real    Γ ⊢ e2 : real
  ─────────────────────────────────
       Γ ⊢ (e1 e2 /) : real


[T-INT-IDIV]                        (divisão inteira)
  Γ ⊢ e1 : int    Γ ⊢ e2 : int
  ────────────────────────────────
       Γ ⊢ (e1 e2 |) : int


[T-INT-MOD]                         (resto)
  Γ ⊢ e1 : int    Γ ⊢ e2 : int
  ────────────────────────────────
       Γ ⊢ (e1 e2 %) : int


[T-INT-POW]
  Γ ⊢ e1 : int    Γ ⊢ e2 : int
  ────────────────────────────────
       Γ ⊢ (e1 e2 ^) : int


[T-REAL-POW]
  Γ ⊢ e1 : real    Γ ⊢ e2 : real
  ─────────────────────────────────
       Γ ⊢ (e1 e2 ^) : real
```

**Proibições:**
- `int + real`, `real + int` → ERRO (e analogamente para `-`, `*`, `^`)
- `int / int`, `int / real`, `real / int` → ERRO (divisão real exige real/real)
- `real | real`, `real % real` → ERRO (divisão inteira e resto exigem int/int)

---

## 5. Operadores Relacionais

```
[T-INT-REL]   (op ∈ {<, >, =, <=, >=, !=})
  Γ ⊢ e1 : int    Γ ⊢ e2 : int
  ──────────────────────────────────
       Γ ⊢ (e1 e2 op) : bool


[T-REAL-REL]
  Γ ⊢ e1 : real    Γ ⊢ e2 : real
  ─────────────────────────────────
       Γ ⊢ (e1 e2 op) : bool


[T-BOOL-EQ]   (op ∈ {=, !=})
  Γ ⊢ e1 : bool    Γ ⊢ e2 : bool
  ─────────────────────────────────
       Γ ⊢ (e1 e2 op) : bool
```

**Proibição:** `int < real`, `real = int` → ERRO (tipagem forte)

---

## 6. Operadores Lógicos

```
[T-AND]
  Γ ⊢ e1 : bool    Γ ⊢ e2 : bool
  ─────────────────────────────────
       Γ ⊢ (e1 e2 AND) : bool


[T-OR]
  Γ ⊢ e1 : bool    Γ ⊢ e2 : bool
  ─────────────────────────────────
       Γ ⊢ (e1 e2 OR) : bool


[T-NOT]
  Γ ⊢ e : bool
  ─────────────────────
  Γ ⊢ (e NOT) : bool
```

**Proibição:** `int AND int`, `real OR real` → ERRO

---

## 7. Estruturas de Controle

```
[T-IF]
  Γ ⊢ cond : bool    Γ ⊢ bloco_then    Γ ⊢ bloco_else
  ──────────────────────────────────────────────────────
       Γ ⊢ IF cond THEN bloco_then [ELSE bloco_else] END


[T-WHILE]
  Γ ⊢ cond : bool    Γ ⊢ corpo
  ─────────────────────────────────────────
       Γ ⊢ WHILE cond DO corpo END
```

**Regra:** condições de IF e WHILE devem ser obrigatoriamente `bool`.
Qualquer outro tipo (int, real) é erro semântico.
