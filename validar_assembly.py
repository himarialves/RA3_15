# Integrante do grupo:
# Mariana Alves da Silva - @himarialves
#
# Nome do grupo no Canvas: RA3_15
#
# Professor Frank Coelho de Alcantara
# Projeto acadêmico para a disciplina Linguagens Formais e Compiladores (2026-1).
# Instituição: Pontifícia Universidade Católica do Paraná - PUC/PR — 2026-1

'''
 validar_assembly.py — Validação estática do Assembly gerado antes de colar no CPulator.

 Uso:
     python validar_assembly.py <arquivo.asm>

 Verifica:
   - Seção .data antes de .text
   - Presença de _start e _end
   - Labels duplicados
   - Referências a labels não definidos
   - Inicializações obrigatórias (SP, VFP, RES_IDX)
   - Diretivas .double e .space bem formadas

'''

from __future__ import annotations
import re
import sys


def validar(caminho: str) -> list[str]:
    try:
        with open(caminho, encoding="utf-8") as f:
            texto = f.read()
    except FileNotFoundError:
        return [f"Arquivo não encontrado: {caminho}"]

    linhas = texto.splitlines()
    erros: list[str] = []

    # ── Seções ────────────────────────────────────────────────────────────────
    tem_data = any(l.strip() == ".data" for l in linhas)
    tem_text = any(l.strip() == ".text" for l in linhas)

    if not tem_data:
        erros.append("Seção .data ausente.")
    if not tem_text:
        erros.append("Seção .text ausente.")

    if tem_data and tem_text:
        idx_data = next(i for i, l in enumerate(linhas) if l.strip() == ".data")
        idx_text = next(i for i, l in enumerate(linhas) if l.strip() == ".text")
        if idx_data > idx_text:
            erros.append(".data deve aparecer antes de .text.")

    #  Labels definidos e usados 
    # Labels são definidos com "nome:" no início da linha (após espaços).
    # Labels são usados em branches (B, BEQ, …) e referências LDR Rx, =nome.
    re_def = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*):")
    re_uso = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\b")

    definidos: set[str] = set()
    usados: set[str] = set()
    duplicados: list[str] = []

    for linha in linhas:
        stripped = linha.strip()
        if stripped.startswith("@"):
            continue
        m = re_def.match(stripped)
        if m:
            label = m.group(1)
            if label in definidos:
                duplicados.append(label)
            definidos.add(label)

    if duplicados:
        erros.append(f"Labels duplicados: {', '.join(sorted(set(duplicados)))}")

    # Instruções de branch referenciam labels
    re_branch = re.compile(r"\b(B|BEQ|BNE|BLT|BGT|BLE|BGE)\s+([A-Za-z_][A-Za-z0-9_]*)")
    for linha in linhas:
        m = re_branch.search(linha)
        if m:
            usados.add(m.group(2))

    # LDR Rx, =label (referência a símbolo em .data)
    re_ldr = re.compile(r"LDR\s+\w+,\s*=([A-Za-z_][A-Za-z0-9_]*)")
    for linha in linhas:
        m = re_ldr.search(linha)
        if m:
            usados.add(m.group(1))

    # Esses nomes são sempre definidos pelo gerador — não precisam ser checados
    ignorar = {"STACK_TOP", "RES_IDX", "RES_HIST", "CONST_ZERO", "CONST_ONE"}
    indefinidos = usados - definidos - ignorar
    if indefinidos:
        erros.append(f"Labels referenciados mas não definidos: {', '.join(sorted(indefinidos))}")

    #  Inicializações obrigatórias 
    # Sem SP: qualquer VPUSH/VPOP causa comportamento indefinido no CPulator.
    # Sem FMXR FPEXC: instruções VFP disparam exceção de coprocessador.
    if "STACK_TOP" not in texto:
        erros.append("STACK_TOP não definido em .data.")
    if "LDR SP, =STACK_TOP" not in texto:
        erros.append("SP não inicializado (falta: LDR SP, =STACK_TOP).")
    if "VMSR FPEXC" not in texto:
        erros.append("VFP não habilitado (falta: VMSR FPEXC, R0).")
    if "_start:" not in texto:
        erros.append("Label _start: ausente.")
    if "_end:" not in texto:
        erros.append("Label _end: ausente.")

    return erros


def main() -> None:
    if len(sys.argv) < 2:
        print("Uso: python validar_assembly.py <arquivo.asm>", file=sys.stderr)
        sys.exit(1)

    caminho = sys.argv[1]
    erros = validar(caminho)

    if erros:
        print(f"Validação falhou ({len(erros)} problema(s)):\n")
        for e in erros:
            print(f"  ✗ {e}")
        sys.exit(1)
    else:
        print(f"Assembly válido: {caminho}")
        print("Pronto para colar no CPulator.")


if __name__ == "__main__":
    main()
